/**
 * END-TO-END SCORING MUTATION CORPUS — scope-based opportunity attribution.
 *
 * These tests run `evaluateSnapshot` all the way THROUGH the scoring path (not
 * merely to a fail-closed lifecycle refusal) against synthetic FROZEN manifests
 * built inside the test process. No repository manifest is altered or frozen.
 *
 * The corpus is the regression proof for the attribution defect: a frozen
 * opportunity used to be located by one exact historical `importer_path`, so a
 * model that put its forbidden edge in a DIFFERENT file of the same frozen
 * architectural scope scored SATISFIED while the edge sat in `raw_violation_count`
 * only, and deleting the anchor scored NOT_APPLICABLE. Attribution is now anchored
 * on the frozen `locator.scope` (a dependency-policy layer), so:
 *
 *   M0  base snapshot, no prohibited edge                      -> SATISFIED
 *   M1  forbidden api->core edge in the historical anchor       -> VIOLATION
 *   M2  same edge in a NEW apps/api/src/*.ts file               -> VIOLATION (same opportunity)
 *   M3  handler moved to a new api file, edge moved with it     -> VIOLATION
 *   M4  features->api edge in a NEW libs/features/src/*.ts file -> VIOLATION (scope-level opportunity)
 *   M4A same features->api edge in the historical anchor        -> VIOLATION
 *   M5  anchor deleted, scope alive, edge in another file       -> VIOLATION (never NOT_APPLICABLE)
 *   M6  new conforming file using an allowed dependency         -> SATISFIED
 *   M7  several prohibited edges in several files, one decision -> exactly ONE violated opportunity
 *
 * The frozen denominator is identical across every mutant: it is the manifest's
 * opportunity count and never depends on what the model created, edited, or how
 * many imports matched.
 *
 * ---------------------------------------------------------------------------
 * M8 — PRODUCTION-SOURCE SCORING (docs/v2/ORACLE_VALIDATION_REQUIREMENTS.md §1b)
 *
 * The second defect: the frozen source globs and the frozen LAYER globs both
 * match test and tooling TypeScript sitting inside an architectural scope, so a
 * dependency written only to wire up a test could violate a PRODUCTION
 * opportunity. E1 measures production architectural dependencies, so the engine
 * partitions the scanned source before building any edge:
 *
 *   M8-A  new PRODUCTION features file imports forbidden infra -> VIOLATION
 *   M8-B  same import in a features-layer *.spec.ts            -> NOT a violation
 *   M8-C  same import under __tests__/                         -> NOT a violation
 *   M8-D  same import in jest.config.ts (tooling config)       -> NOT a violation
 *   M8-E  conforming production file, forbidden dep only in a test -> SATISFIED
 *   M8-F  forbidden production dep + harmless test deps        -> VIOLATION exactly once
 *
 * M0–M7 are unchanged by M8: the base snapshot carries no test or config file, so
 * the partition holds out nothing there.
 */

import {
  ArchitectureFinding,
  BASELINE_PRODUCTION_SOURCE_POLICY_ID,
  EvaluateOptions,
  OracleError,
  classifySourceFile,
  evaluateSnapshot,
  isProductionSource,
  partitionProductionSources,
  resolveProductionSourcePolicy,
} from '../src';
import {
  baseDependencyPolicy,
  baseManifest,
  cleanup,
  makeTmpRoot,
  writeManifest,
  writeSnapshot,
} from './helpers';

// --------------------------------------------------------------------------- //
// Synthetic source substrate (a miniature of the real layered repository)
// --------------------------------------------------------------------------- //
const TSCONFIG = `{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@afci-bench/contracts": ["libs/contracts/src/index.ts"],
      "@afci-bench/core": ["libs/core/src/index.ts"],
      "@afci-bench/features": ["libs/features/src/index.ts"],
      "@afci-bench/infra": ["libs/infra/src/index.ts"],
      "@afci-bench/observability": ["libs/observability/src/index.ts"]
    }
  }
}
`;

/** The historical anchor of the api opportunity (provenance in the manifest). */
const API_ANCHOR = 'apps/api/src/handlers/order.ts';
/** The historical anchor of the features opportunity. */
const FEATURES_ANCHOR = 'libs/features/src/index.ts';

const BASE: Record<string, string> = {
  'tsconfig.json': TSCONFIG,
  'libs/contracts/src/index.ts': `export interface OrderDto {
  id: string;
}
`,
  'libs/observability/src/index.ts': `export const log = (m: string): string => m;
`,
  'libs/core/src/index.ts': `import { OrderDto } from '@afci-bench/contracts';
export const idOf = (o: OrderDto): string => o.id;
`,
  'libs/infra/src/index.ts': `import { OrderDto } from '@afci-bench/contracts';
import { log } from '@afci-bench/observability';
export const load = (o: OrderDto): string => log(o.id);
`,
  [FEATURES_ANCHOR]: `import { idOf } from '@afci-bench/core';
import { OrderDto } from '@afci-bench/contracts';
import { log } from '@afci-bench/observability';
export const describe = (o: OrderDto): string => log(idOf(o));
`,
  'apps/api/src/app.ts': `import { describe } from '@afci-bench/features';
import { load } from '@afci-bench/infra';
import { OrderDto } from '@afci-bench/contracts';
export const handle = (o: OrderDto): string => describe(o) + load(o);
`,
  [API_ANCHOR]: `import { describe } from '@afci-bench/features';
export const order = (): string => describe({ id: 'x' });
`,
};

/** A file that reaches api -> core directly (forbidden; AR-DEP-005). */
const API_TO_CORE = `import { idOf } from '@afci-bench/core';
export const peek = (): string => idOf({ id: 'x' });
`;

/** A file that reaches features -> api directly (forbidden; AR-DEP-006). */
const FEATURES_TO_API = `import { handle } from '../../../apps/api/src/app';
export const call = (): string => handle({ id: 'x' });
`;

/** A file that reaches core -> infra directly (forbidden; AR-DEP-003). */
const CORE_TO_INFRA = `import { load } from '@afci-bench/infra';
export const grab = (): string => load({ id: 'x' });
`;

/** A conforming api file (api -> infra is an allowed dependency). */
const API_TO_INFRA = `import { load } from '@afci-bench/infra';
export const report = (): string => load({ id: 'x' });
`;

/** Build a snapshot file map from BASE; `null` deletes a file. */
function snapshotWith(overrides: Record<string, string | null> = {}): Record<string, string> {
  const files: Record<string, string> = { ...BASE };
  for (const [rel, contents] of Object.entries(overrides)) {
    if (contents === null) {
      delete files[rel];
    } else {
      files[rel] = contents;
    }
  }
  return files;
}

// --------------------------------------------------------------------------- //
// The FROZEN opportunity set — identical for every mutant
// --------------------------------------------------------------------------- //
const OPP_API_CORE = 'OPP-API-CORE';
const OPP_FEATURES_API = 'OPP-FEAT-API';

/** Two frozen architectural decisions; the denominator is therefore always 2. */
function frozenOpportunities(): Record<string, unknown>[] {
  return [
    {
      opportunity_id: OPP_API_CORE,
      rule_id: 'AR-DEP-005',
      locator: {
        // provenance only: where the decision was authored, never the anchor
        importer_path: API_ANCHOR,
        scope: 'api',
        forbidden_target_layers: ['core'],
      },
      description: null,
    },
    {
      opportunity_id: OPP_FEATURES_API,
      rule_id: 'AR-DEP-006',
      locator: {
        importer_path: FEATURES_ANCHOR,
        scope: 'features',
        forbidden_target_layers: ['api'],
      },
      description: null,
    },
  ];
}

const FROZEN_DENOMINATOR = frozenOpportunities().length;

function score(
  files: Record<string, string>,
  manifest: Record<string, unknown> = baseManifest({ opportunities: frozenOpportunities() }),
  extra: Partial<EvaluateOptions> = {},
): ArchitectureFinding {
  const tmp = makeTmpRoot();
  try {
    const snapshotDir = writeSnapshot(tmp, files);
    const manifestPath = writeManifest(tmp, manifest);
    return evaluateSnapshot({ snapshotDir, manifestPath, snapshotId: 'mutant', scoredAt: null, ...extra });
  } finally {
    cleanup(tmp);
  }
}

function expectFailClosed(
  files: Record<string, string>,
  manifest: Record<string, unknown>,
  reason: RegExp,
  extra: Partial<EvaluateOptions> = {},
): OracleError {
  const tmp = makeTmpRoot();
  try {
    const snapshotDir = writeSnapshot(tmp, files);
    const manifestPath = writeManifest(tmp, manifest);
    let thrown: unknown;
    try {
      evaluateSnapshot({ snapshotDir, manifestPath, snapshotId: 'mutant', ...extra });
    } catch (e) {
      thrown = e;
    }
    expect(thrown).toBeInstanceOf(OracleError);
    expect((thrown as OracleError).reason).toMatch(reason);
    return thrown as OracleError;
  } finally {
    cleanup(tmp);
  }
}

type OppStatus = 'VIOLATION' | 'SATISFIED' | 'NOT_APPLICABLE';

/** The single status the frozen opportunity resolves to across all its findings. */
function oppStatus(r: ArchitectureFinding, opportunityId: string): OppStatus {
  const linked = r.findings.filter((f) => f.opportunity_id === opportunityId);
  expect(linked.length).toBeGreaterThan(0);
  if (linked.some((f) => f.violation)) {
    expect(linked.every((f) => f.status === 'VIOLATION')).toBe(true);
    return 'VIOLATION';
  }
  expect(linked).toHaveLength(1);
  return linked[0].status as OppStatus;
}

// --------------------------------------------------------------------------- //
// The mutation corpus
// --------------------------------------------------------------------------- //
interface Mutant {
  id: string;
  what: string;
  files: Record<string, string>;
  apiOpp: OppStatus;
  featuresOpp: OppStatus;
  rawViolations: number;
}

const MUTANTS: Mutant[] = [
  {
    id: 'M0',
    what: 'base snapshot, no prohibited edge',
    files: snapshotWith(),
    apiOpp: 'SATISFIED',
    featuresOpp: 'SATISFIED',
    rawViolations: 0,
  },
  {
    id: 'M1',
    what: 'forbidden api->core edge in the historical anchor file',
    files: snapshotWith({ [API_ANCHOR]: API_TO_CORE }),
    apiOpp: 'VIOLATION',
    featuresOpp: 'SATISFIED',
    rawViolations: 1,
  },
  {
    id: 'M2',
    what: 'same forbidden api->core edge in a NEW apps/api/src file (anchor untouched)',
    files: snapshotWith({ 'apps/api/src/lookup.ts': API_TO_CORE }),
    apiOpp: 'VIOLATION',
    featuresOpp: 'SATISFIED',
    rawViolations: 1,
  },
  {
    id: 'M3',
    what: 'handler MOVED to a new api file, carrying the prohibited edge',
    files: snapshotWith({ [API_ANCHOR]: null, 'apps/api/src/orders/handler.ts': API_TO_CORE }),
    apiOpp: 'VIOLATION',
    featuresOpp: 'SATISFIED',
    rawViolations: 1,
  },
  {
    id: 'M4',
    what: 'features->api violation in a NEW libs/features/src file',
    files: snapshotWith({ 'libs/features/src/gateway.ts': FEATURES_TO_API }),
    apiOpp: 'SATISFIED',
    featuresOpp: 'VIOLATION',
    rawViolations: 1,
  },
  {
    id: 'M4A',
    what: 'the same features->api edge in the historical anchor',
    files: snapshotWith({
      [FEATURES_ANCHOR]: `${BASE[FEATURES_ANCHOR]}${FEATURES_TO_API}`,
    }),
    apiOpp: 'SATISFIED',
    featuresOpp: 'VIOLATION',
    rawViolations: 1,
  },
  {
    id: 'M5',
    what: 'historical anchor deleted, scope still alive, prohibited edge in another file',
    files: snapshotWith({ [API_ANCHOR]: null, 'apps/api/src/reports.ts': API_TO_CORE }),
    apiOpp: 'VIOLATION',
    featuresOpp: 'SATISFIED',
    rawViolations: 1,
  },
  {
    id: 'M6',
    what: 'new conforming source file using an allowed dependency',
    files: snapshotWith({ 'apps/api/src/report.ts': API_TO_INFRA }),
    apiOpp: 'SATISFIED',
    featuresOpp: 'SATISFIED',
    rawViolations: 0,
  },
  {
    id: 'M7',
    what: 'multiple prohibited edges in several files within the same frozen decision',
    files: snapshotWith({
      [API_ANCHOR]: API_TO_CORE,
      'apps/api/src/one.ts': API_TO_CORE,
      'apps/api/src/two.ts': API_TO_CORE,
      'apps/api/src/nested/three.ts': API_TO_CORE,
    }),
    apiOpp: 'VIOLATION',
    featuresOpp: 'SATISFIED',
    rawViolations: 4,
  },
];

describe('scope-based attribution — mutation corpus M0..M7', () => {
  it.each(MUTANTS.map((m) => [m.id, m] as [string, Mutant]))(
    '%s produces the intended per-opportunity outcome',
    (_id, m) => {
      const r = score(m.files);
      expect(oppStatus(r, OPP_API_CORE)).toBe(m.apiOpp);
      expect(oppStatus(r, OPP_FEATURES_API)).toBe(m.featuresOpp);
      expect(r.raw_violation_count).toBe(m.rawViolations);

      const expectedViolated =
        (m.apiOpp === 'VIOLATION' ? 1 : 0) + (m.featuresOpp === 'VIOLATION' ? 1 : 0);
      expect(r.opportunity_accounting.violated_opportunity_count).toBe(expectedViolated);
      expect(r.opportunity_accounting.absent_opportunity_count).toBe(0);
    },
  );

  it('a prohibited edge in a NEW file can no longer produce SATISFIED (M2 vs M1)', () => {
    // The exact defect: the anchor file is untouched and still conforms, but the
    // frozen decision is violated elsewhere in the same scope.
    const m2 = score(snapshotWith({ 'apps/api/src/lookup.ts': API_TO_CORE }));
    expect(oppStatus(m2, OPP_API_CORE)).toBe('VIOLATION');
    expect(m2.opportunity_accounting.fixed_opportunity_count).toBe(1); // only the features opp
    // ...and it is scored identically to the same edge in the anchor (M1).
    const m1 = score(snapshotWith({ [API_ANCHOR]: API_TO_CORE }));
    expect(m2.opportunity_accounting).toEqual(m1.opportunity_accounting);
  });

  it('deleting or moving the anchor cannot hide a live violation (M5)', () => {
    const r = score(snapshotWith({ [API_ANCHOR]: null, 'apps/api/src/reports.ts': API_TO_CORE }));
    expect(oppStatus(r, OPP_API_CORE)).toBe('VIOLATION');
    expect(r.opportunity_accounting.absent_opportunity_count).toBe(0);
    expect(r.findings.some((f) => f.status === 'NOT_APPLICABLE')).toBe(false);
  });

  it('one frozen opportunity contributes AT MOST one violation (M7)', () => {
    const m7 = MUTANTS.find((m) => m.id === 'M7') as Mutant;
    const r = score(m7.files);
    expect(r.opportunity_accounting.violated_opportunity_count).toBe(1);
    // Four separate forbidden edges, one frozen decision.
    expect(r.raw_violation_count).toBe(4);
    expect(r.findings.filter((f) => f.opportunity_id === OPP_API_CORE && f.violation)).toHaveLength(4);
  });

  it('raw_violation_count may exceed violated_opportunity_count', () => {
    const r = score((MUTANTS.find((m) => m.id === 'M7') as Mutant).files);
    expect(r.raw_violation_count).toBeGreaterThan(
      r.opportunity_accounting.violated_opportunity_count,
    );
  });

  it('the frozen denominator is identical across every mutant', () => {
    for (const m of MUTANTS) {
      const r = score(m.files);
      expect(r.opportunity_accounting.applicable_opportunity_count).toBe(FROZEN_DENOMINATOR);
      const acc = r.opportunity_accounting;
      expect(
        acc.fixed_opportunity_count + acc.violated_opportunity_count + acc.absent_opportunity_count,
      ).toBe(acc.applicable_opportunity_count);
    }
  });

  it('the denominator does not move when the model adds files, edits files, or adds imports', () => {
    const many: Record<string, string> = {};
    for (let i = 0; i < 12; i += 1) {
      many[`apps/api/src/gen/f${i}.ts`] = API_TO_CORE;
    }
    const r = score(snapshotWith(many));
    expect(r.opportunity_accounting.applicable_opportunity_count).toBe(FROZEN_DENOMINATOR);
    expect(r.opportunity_accounting.violated_opportunity_count).toBe(1);
    expect(r.raw_violation_count).toBe(12);
  });

  it('reports no false positive for any allowed edge (M0, M6)', () => {
    for (const id of ['M0', 'M6']) {
      const r = score((MUTANTS.find((m) => m.id === id) as Mutant).files);
      expect(r.raw_violation_count).toBe(0);
      expect(r.findings.some((f) => f.violation)).toBe(false);
      expect(r.verdict).toBe('CONFORMANT');
    }
  });

  it('records the historical importer path as provenance only, never as the anchor', () => {
    const r = score(snapshotWith());
    const satisfied = r.findings.find((f) => f.opportunity_id === OPP_API_CORE);
    expect(satisfied?.status).toBe('SATISFIED');
    expect(satisfied?.message).toContain('provenance only');
    // Scoring is unchanged when the provenance path is nonsense, because it is
    // never consulted: the scope is what is scored.
    const opportunities = frozenOpportunities();
    (opportunities[0].locator as Record<string, unknown>).importer_path =
      'apps/api/src/this/file/never/existed.ts';
    const withBadProvenance = score(
      snapshotWith({ 'apps/api/src/lookup.ts': API_TO_CORE }),
      baseManifest({ opportunities }),
    );
    expect(oppStatus(withBadProvenance, OPP_API_CORE)).toBe('VIOLATION');
  });
});

// --------------------------------------------------------------------------- //
// NOT_APPLICABLE is reserved for a scope that carries no source material
// --------------------------------------------------------------------------- //
describe('NOT_APPLICABLE semantics', () => {
  it('is reported only when the frozen scope itself no longer exists', () => {
    // The entire features layer is gone; api still imports the (now unresolved)
    // features alias, which remains an ALLOWED direction, so nothing is violated.
    const r = score(snapshotWith({ [FEATURES_ANCHOR]: null }));
    expect(oppStatus(r, OPP_FEATURES_API)).toBe('NOT_APPLICABLE');
    expect(oppStatus(r, OPP_API_CORE)).toBe('SATISFIED');
    expect(r.opportunity_accounting.applicable_opportunity_count).toBe(FROZEN_DENOMINATOR);
    expect(r.opportunity_accounting.absent_opportunity_count).toBe(1);
    expect(r.opportunity_accounting.violated_opportunity_count).toBe(0);
  });

  it('is NOT reported merely because the historical anchor file was deleted', () => {
    // The api scope keeps other files, so the decision stays live and SATISFIED.
    const r = score(snapshotWith({ [API_ANCHOR]: null }));
    expect(oppStatus(r, OPP_API_CORE)).toBe('SATISFIED');
    expect(r.opportunity_accounting.absent_opportunity_count).toBe(0);
  });

  it('an absent scope that reappears with a forbidden edge is VIOLATION, not absent', () => {
    const r = score(
      snapshotWith({ [FEATURES_ANCHOR]: null, 'libs/features/src/gateway.ts': FEATURES_TO_API }),
    );
    expect(oppStatus(r, OPP_FEATURES_API)).toBe('VIOLATION');
    expect(r.opportunity_accounting.absent_opportunity_count).toBe(0);
  });
});

// --------------------------------------------------------------------------- //
// Rule reporting: leaf specificity and no umbrella double-counting
// --------------------------------------------------------------------------- //
describe('rule reporting under the AR-DEP-001 umbrella', () => {
  const coreOpportunity = [
    {
      opportunity_id: 'OPP-CORE-INFRA',
      rule_id: 'AR-DEP-003',
      locator: {
        importer_path: 'libs/core/src/index.ts',
        scope: 'core',
        forbidden_target_layers: ['infra'],
      },
      description: null,
    },
  ];

  it('reports a core->infra edge under the leaf rule AR-DEP-003', () => {
    const r = score(
      snapshotWith({ 'libs/core/src/repo.ts': CORE_TO_INFRA }),
      baseManifest({ opportunities: coreOpportunity }),
    );
    const v = r.findings.filter((f) => f.violation);
    expect(v).toHaveLength(1);
    expect(v[0].rule_id).toBe('AR-DEP-003');
    expect(v[0].importer_layer).toBe('core');
    expect(v[0].target_layer).toBe('infra');
    expect(v[0].opportunity_id).toBe('OPP-CORE-INFRA');
  });

  it('umbrella expansion does not double-count a leaf violation', () => {
    // AR-DEP-001 alone puts the whole matrix in force; one forbidden edge must
    // still yield exactly ONE finding, reported under its leaf clause only.
    const r = score(
      snapshotWith({ 'libs/core/src/repo.ts': CORE_TO_INFRA }),
      baseManifest({ applicable_rule_ids: ['AR-DEP-001'], opportunities: coreOpportunity }),
    );
    expect(r.raw_violation_count).toBe(1);
    expect(r.findings.filter((f) => f.violation && f.rule_id === 'AR-DEP-001')).toHaveLength(0);
    expect(r.opportunity_accounting.violated_opportunity_count).toBe(1);
  });

  it('a forbidden edge outside every frozen decision stays raw-only', () => {
    // core->infra is a real violation, but the frozen set only scopes api->core
    // and features->api, so it must not enter the E1 numerator.
    const r = score(snapshotWith({ 'libs/core/src/repo.ts': CORE_TO_INFRA }));
    expect(r.raw_violation_count).toBe(1);
    expect(r.opportunity_accounting.violated_opportunity_count).toBe(0);
    expect(r.opportunity_accounting.fixed_opportunity_count).toBe(FROZEN_DENOMINATOR);
    expect(r.findings.find((f) => f.violation)?.opportunity_id).toBeNull();
  });
});

// --------------------------------------------------------------------------- //
// AR-DEP-001 is never a scored opportunity rule
// --------------------------------------------------------------------------- //
describe('AR-DEP-001 umbrella prohibition for scored opportunities', () => {
  const umbrellaOpp = [
    {
      opportunity_id: 'OPP-UMBRELLA',
      rule_id: 'AR-DEP-001',
      locator: { importer_path: API_ANCHOR, scope: 'api', forbidden_target_layers: ['core'] },
      description: null,
    },
  ];

  it('refuses the umbrella as a scored opportunity rule', () => {
    const err = expectFailClosed(
      snapshotWith(),
      baseManifest({ opportunities: umbrellaOpp }),
      /UMBRELLA_OPPORTUNITY_RULE/,
    );
    expect(err.message).toContain('AR-DEP-001');
    expect(err.message).toMatch(/leaf clause/);
  });

  it('refuses it even on a violating snapshot (never downgraded to a scored result)', () => {
    expectFailClosed(
      snapshotWith({ 'apps/api/src/lookup.ts': API_TO_CORE }),
      baseManifest({ opportunities: umbrellaOpp }),
      /UMBRELLA_OPPORTUNITY_RULE/,
    );
  });

  it('still allows AR-DEP-001 in applicable_rule_ids to expand raw exposure', () => {
    const r = score(
      snapshotWith({ 'libs/core/src/repo.ts': CORE_TO_INFRA }),
      baseManifest({ applicable_rule_ids: ['AR-DEP-001'], opportunities: frozenOpportunities() }),
    );
    // The core->infra clause was in force only because of the umbrella.
    expect(r.rules_evaluated.map((x) => x.rule_id)).toContain('AR-DEP-003');
    expect(r.raw_violation_count).toBe(1);
  });

  it('refuses a leaf/umbrella pair that would duplicate one frozen decision', () => {
    expectFailClosed(
      snapshotWith(),
      baseManifest({
        opportunities: [
          ...frozenOpportunities(),
          {
            opportunity_id: 'OPP-API-CORE-DUP',
            rule_id: 'AR-DEP-005',
            locator: { importer_path: 'apps/api/src/app.ts', scope: 'api', forbidden_target_layers: ['core'] },
            description: null,
          },
        ],
      }),
      /DUPLICATE_OPPORTUNITY_SCOPE/,
    );
  });
});

// --------------------------------------------------------------------------- //
// Manifest locator integrity
// --------------------------------------------------------------------------- //
describe('manifest locator integrity', () => {
  const withLocator = (locator: Record<string, unknown>, ruleId = 'AR-DEP-005') =>
    baseManifest({
      opportunities: [
        { opportunity_id: 'OPP-X', rule_id: ruleId, locator, description: null },
      ],
    });

  it('refuses a scope that is not a frozen dependency-policy layer', () => {
    // 'scope:api' is the catalog SCOPE TAG, not the policy layer id.
    expectFailClosed(
      snapshotWith(),
      withLocator({ importer_path: API_ANCHOR, scope: 'scope:api', forbidden_target_layers: ['core'] }),
      /INVALID_OPPORTUNITY_SCOPE/,
    );
    expectFailClosed(
      snapshotWith(),
      withLocator({ importer_path: API_ANCHOR, scope: null, forbidden_target_layers: ['core'] }),
      /INVALID_OPPORTUNITY_SCOPE/,
    );
  });

  it('refuses a forbidden target that is not a known layer', () => {
    expectFailClosed(
      snapshotWith(),
      withLocator({ importer_path: API_ANCHOR, scope: 'api', forbidden_target_layers: ['persistence'] }),
      /INVALID_OPPORTUNITY_SCOPE/,
    );
  });

  it('refuses an empty forbidden-target set (an unbounded decision)', () => {
    expectFailClosed(
      snapshotWith(),
      withLocator({ importer_path: API_ANCHOR, scope: 'api', forbidden_target_layers: [] }),
      /INVALID_OPPORTUNITY_SCOPE/,
    );
  });

  it('refuses a "forbidden" target the frozen matrix actually permits', () => {
    // api -> features is allowed, so this opportunity could never be violated and
    // would pad the denominator with zero exposure.
    const err = expectFailClosed(
      snapshotWith(),
      withLocator({ importer_path: API_ANCHOR, scope: 'api', forbidden_target_layers: ['features'] }),
      /INVALID_OPPORTUNITY_SCOPE/,
    );
    expect(err.message).toMatch(/zero exposure/);
  });

  it('refuses a rule that is not the leaf for the declared scope -> target relationship', () => {
    const err = expectFailClosed(
      snapshotWith(),
      withLocator(
        { importer_path: API_ANCHOR, scope: 'api', forbidden_target_layers: ['core'] },
        'AR-DEP-003',
      ),
      /OPPORTUNITY_RULE_SCOPE_MISMATCH/,
    );
    expect(err.message).toContain('AR-DEP-005');
  });

  it('refuses a relationship the family covers only by the umbrella', () => {
    // observability -> core has no implemented leaf clause.
    expectFailClosed(
      snapshotWith(),
      withLocator(
        { importer_path: null, scope: 'observability', forbidden_target_layers: ['core'] },
        'AR-DEP-003',
      ),
      /OPPORTUNITY_RULE_SCOPE_MISMATCH/,
    );
  });

  it('accepts a well-formed leaf opportunity and scores it', () => {
    const r = score(
      snapshotWith(),
      withLocator({ importer_path: API_ANCHOR, scope: 'api', forbidden_target_layers: ['core'] }),
    );
    expect(r.opportunity_accounting.applicable_opportunity_count).toBe(1);
    expect(r.opportunity_accounting.fixed_opportunity_count).toBe(1);
  });

  it('does not require the historical importer path to exist', () => {
    const r = score(
      snapshotWith({ [API_ANCHOR]: null }),
      withLocator({ importer_path: API_ANCHOR, scope: 'api', forbidden_target_layers: ['core'] }),
    );
    expect(r.opportunity_accounting.fixed_opportunity_count).toBe(1);
    expect(r.opportunity_accounting.absent_opportunity_count).toBe(0);
  });
});

// --------------------------------------------------------------------------- //
// Eligibility and stub gates still hold on the real scoring path
// --------------------------------------------------------------------------- //
describe('gates that must survive the attribution change', () => {
  it('a stub rule cannot contribute a scored opportunity', () => {
    expectFailClosed(
      snapshotWith(),
      baseManifest({
        applicable_rule_ids: ['AR-DEP-001', 'AR-CONTRACT-001'],
        opportunities: [
          {
            opportunity_id: 'OPP-STUB',
            rule_id: 'AR-CONTRACT-001',
            locator: { importer_path: API_ANCHOR, scope: 'api', forbidden_target_layers: ['core'] },
            description: null,
          },
        ],
      }),
      /INVALID_OPPORTUNITY_RULE/,
    );
  });

  it('a PT06-like functional-only task cannot acquire an E1 denominator', () => {
    const err = expectFailClosed(
      snapshotWith(),
      baseManifest({
        opportunities: frozenOpportunities(),
        e1_analysis_eligibility: 'functional-only',
      }),
      /ELIGIBILITY_DENOMINATOR_CONFLICT/,
    );
    expect(err.message).toMatch(/structurally excluded from E1/);
  });

  it('a functional-only task cannot be relabelled scored against the approved index', () => {
    expectFailClosed(
      snapshotWith({ 'apps/api/src/lookup.ts': API_TO_CORE }),
      baseManifest({
        task_id: 'PT06',
        opportunities: frozenOpportunities(),
        e1_analysis_eligibility: 'scored',
      }),
      /ELIGIBILITY_TASK_INDEX_MISMATCH/,
      { approvedEligibility: { PT06: 'functional-only' } },
    );
  });

  it('a reclassified PT05 cannot be scored as E1-eligible against the approved index', () => {
    // PT05 is functionally valid but structurally ineligible: its required work
    // creates no scored dependency-direction opportunity. A private manifest that
    // still declares it 'scored' must fail closed, not quietly enter E1.
    expectFailClosed(
      snapshotWith({ 'apps/api/src/lookup.ts': API_TO_CORE }),
      baseManifest({
        task_id: 'PT05',
        opportunities: frozenOpportunities(),
        e1_analysis_eligibility: 'scored',
      }),
      /ELIGIBILITY_TASK_INDEX_MISMATCH/,
      { approvedEligibility: { PT05: 'functional-only' } },
    );
    // ...and it cannot smuggle a denominator in under the correct label either.
    expectFailClosed(
      snapshotWith(),
      baseManifest({
        task_id: 'PT05',
        opportunities: frozenOpportunities(),
        e1_analysis_eligibility: 'functional-only',
      }),
      /ELIGIBILITY_DENOMINATOR_CONFLICT/,
      { approvedEligibility: { PT05: 'functional-only' } },
    );
  });

  it('a zero-opportunity functional-only task scores with NO E1 exposure', () => {
    // The correct shape: functional-only, zero frozen opportunities. It scores,
    // it is not an error, and it contributes nothing to either side of E1 — so it
    // can never be entered as "zero violations".
    const r = score(
      snapshotWith({ 'apps/api/src/lookup.ts': API_TO_CORE }),
      baseManifest({
        task_id: 'PT05',
        opportunities: [],
        e1_analysis_eligibility: 'functional-only',
      }),
      { approvedEligibility: { PT05: 'functional-only' } },
    );
    expect(r.opportunity_accounting.applicable_opportunity_count).toBe(0);
    expect(r.opportunity_accounting.violated_opportunity_count).toBe(0);
    expect(r.opportunity_accounting.fixed_opportunity_count).toBe(0);
    expect(r.findings.some((f) => f.opportunity_id !== null)).toBe(false);
    // The raw descriptive series still records the forbidden edge; E1 does not.
    expect(r.raw_violation_count).toBe(1);
  });

  it('an inactive reserve is still refused, opportunities and all', () => {
    expectFailClosed(
      snapshotWith({ 'apps/api/src/lookup.ts': API_TO_CORE }),
      baseManifest({
        task_id: 'PR01',
        opportunities: frozenOpportunities(),
        e1_analysis_eligibility: 'inactive-reserve',
      }),
      /ELIGIBILITY_RESERVE_INACTIVE/,
      { approvedEligibility: { PR01: 'inactive-reserve' } },
    );
  });

  it('scoring stays deterministic (byte-identical) under scope attribution', () => {
    const files = snapshotWith({ 'apps/api/src/lookup.ts': API_TO_CORE });
    expect(JSON.stringify(score(files))).toEqual(JSON.stringify(score(files)));
  });
});

// --------------------------------------------------------------------------- //
// M8 — production-source scoring
//
// E1 measures PRODUCTION architectural dependencies. The frozen source globs and
// the frozen LAYER globs both match test and tooling TypeScript that physically
// sits inside an architectural scope (`libs/features/src/x.spec.ts` is layer
// `features`; `libs/features/jest.config.ts` is layer `features`), so before this
// policy a dependency written only to wire up a test could violate a production
// opportunity. These cases prove it cannot, while a genuine production dependency
// in a brand-new file still is.
// --------------------------------------------------------------------------- //
const OPP_M8_FEATURES_INFRA = 'OPP-M8-FEAT-INFRA';
const OPP_M8_API_CORE = 'OPP-M8-API-CORE';

/** features->infra (AR-DEP-006) and api->core (AR-DEP-005): denominator 2. */
function m8Opportunities(): Record<string, unknown>[] {
  return [
    {
      opportunity_id: OPP_M8_FEATURES_INFRA,
      rule_id: 'AR-DEP-006',
      locator: {
        importer_path: FEATURES_ANCHOR,
        scope: 'features',
        forbidden_target_layers: ['infra'],
      },
      description: null,
    },
    {
      opportunity_id: OPP_M8_API_CORE,
      rule_id: 'AR-DEP-005',
      locator: { importer_path: API_ANCHOR, scope: 'api', forbidden_target_layers: ['core'] },
      description: null,
    },
  ];
}

const M8_DENOMINATOR = m8Opportunities().length;

/** features -> infra: forbidden (AR-DEP-006). */
const FEATURES_TO_INFRA = `import { load } from '@afci-bench/infra';
export const price = (): string => load({ id: 'x' });
`;

/** features -> core: an ALLOWED dependency, so this file conforms. */
const FEATURES_TO_CORE = `import { idOf } from '@afci-bench/core';
export const discount = (): string => idOf({ id: 'x' });
`;

/** Tooling configuration that pulls in a forbidden target purely to set up tests. */
const JEST_CONFIG_TO_INFRA = `import { load } from '@afci-bench/infra';
export const config = { displayName: 'features', seed: load({ id: 'x' }) };
`;

function scoreM8(
  files: Record<string, string>,
  manifestOverrides: Record<string, unknown> = {},
): ArchitectureFinding {
  return score(files, baseManifest({ opportunities: m8Opportunities(), ...manifestOverrides }));
}

interface ProdMutant {
  id: string;
  what: string;
  files: Record<string, string>;
  featuresInfraOpp: OppStatus;
  apiCoreOpp: OppStatus;
  rawViolations: number;
  /** Files held out of the production dependency graph. */
  excluded: string[];
}

const M8_MUTANTS: ProdMutant[] = [
  {
    id: 'M8-A',
    what: 'a NEW production libs/features/src file imports a forbidden infra target',
    files: snapshotWith({ 'libs/features/src/pricing.ts': FEATURES_TO_INFRA }),
    featuresInfraOpp: 'VIOLATION',
    apiCoreOpp: 'SATISFIED',
    rawViolations: 1,
    excluded: [],
  },
  {
    id: 'M8-B',
    what: 'a new features-layer *.spec.ts imports the same infra target to build a test double',
    files: snapshotWith({ 'libs/features/src/pricing.spec.ts': FEATURES_TO_INFRA }),
    featuresInfraOpp: 'SATISFIED',
    apiCoreOpp: 'SATISFIED',
    rawViolations: 0,
    excluded: ['libs/features/src/pricing.spec.ts'],
  },
  {
    id: 'M8-C',
    what: 'the same prohibited import under __tests__/ (not a *.spec.ts basename)',
    files: snapshotWith({ 'libs/features/src/__tests__/harness.ts': FEATURES_TO_INFRA }),
    featuresInfraOpp: 'SATISFIED',
    apiCoreOpp: 'SATISFIED',
    rawViolations: 0,
    excluded: ['libs/features/src/__tests__/harness.ts'],
  },
  {
    id: 'M8-D',
    what: 'test/config TypeScript (jest.config.ts) imports the forbidden dependency',
    files: snapshotWith({ 'libs/features/jest.config.ts': JEST_CONFIG_TO_INFRA }),
    featuresInfraOpp: 'SATISFIED',
    apiCoreOpp: 'SATISFIED',
    rawViolations: 0,
    excluded: ['libs/features/jest.config.ts'],
  },
  {
    id: 'M8-E',
    what: 'a conforming production file whose TEST carries the forbidden dependency',
    files: snapshotWith({
      'libs/features/src/discount.ts': FEATURES_TO_CORE,
      'libs/features/src/discount.spec.ts': FEATURES_TO_INFRA,
    }),
    featuresInfraOpp: 'SATISFIED',
    apiCoreOpp: 'SATISFIED',
    rawViolations: 0,
    excluded: ['libs/features/src/discount.spec.ts'],
  },
  {
    id: 'M8-F',
    what: 'a forbidden PRODUCTION dependency plus otherwise harmless test dependencies',
    files: snapshotWith({
      'libs/features/src/gateway.ts': FEATURES_TO_INFRA,
      'libs/features/src/gateway.spec.ts': FEATURES_TO_INFRA,
      'libs/features/src/__tests__/support.ts': FEATURES_TO_INFRA,
      'libs/features/jest.config.ts': JEST_CONFIG_TO_INFRA,
    }),
    featuresInfraOpp: 'VIOLATION',
    apiCoreOpp: 'SATISFIED',
    rawViolations: 1,
    excluded: [
      'libs/features/jest.config.ts',
      'libs/features/src/__tests__/support.ts',
      'libs/features/src/gateway.spec.ts',
    ],
  },
];

describe('production-source scoring — mutation corpus M8-A..M8-F', () => {
  it.each(M8_MUTANTS.map((m) => [m.id, m] as [string, ProdMutant]))(
    '%s produces the intended per-opportunity outcome',
    (_id, m) => {
      const r = scoreM8(m.files);
      expect(oppStatus(r, OPP_M8_FEATURES_INFRA)).toBe(m.featuresInfraOpp);
      expect(oppStatus(r, OPP_M8_API_CORE)).toBe(m.apiCoreOpp);
      expect(r.raw_violation_count).toBe(m.rawViolations);

      // Raw production violations and the frozen accounting stay coherent.
      const expectedViolated =
        (m.featuresInfraOpp === 'VIOLATION' ? 1 : 0) + (m.apiCoreOpp === 'VIOLATION' ? 1 : 0);
      const acc = r.opportunity_accounting;
      expect(acc.violated_opportunity_count).toBe(expectedViolated);
      expect(acc.absent_opportunity_count).toBe(0);
      expect(acc.applicable_opportunity_count).toBe(M8_DENOMINATOR);
      expect(
        acc.fixed_opportunity_count + acc.violated_opportunity_count + acc.absent_opportunity_count,
      ).toBe(acc.applicable_opportunity_count);
      // Every reported violation is a production-file violation.
      expect(r.findings.filter((f) => f.violation)).toHaveLength(m.rawViolations);
    },
  );

  it.each(M8_MUTANTS.map((m) => [m.id, m] as [string, ProdMutant]))(
    '%s partitions exactly the intended files out of the production graph',
    (_id, m) => {
      const r = scoreM8(m.files);
      expect(r.production_source.policy_id).toBe(BASELINE_PRODUCTION_SOURCE_POLICY_ID);
      expect(r.production_source.excluded_paths).toEqual(m.excluded);
      expect(r.production_source.excluded_file_count).toBe(m.excluded.length);
      expect(r.production_source.production_file_count).toBeGreaterThan(0);
      // No excluded file may appear as evidence for any violation.
      for (const finding of r.findings.filter((f) => f.violation)) {
        for (const evidence of finding.evidence_paths) {
          expect(m.excluded).not.toContain(evidence);
        }
      }
    },
  );

  it('M8-A: a production edge in a brand-new file is still detected and attributed', () => {
    const r = scoreM8(snapshotWith({ 'libs/features/src/pricing.ts': FEATURES_TO_INFRA }));
    const violations = r.findings.filter((f) => f.violation);
    expect(violations).toHaveLength(1);
    expect(violations[0].rule_id).toBe('AR-DEP-006');
    expect(violations[0].importer_layer).toBe('features');
    expect(violations[0].target_layer).toBe('infra');
    expect(violations[0].opportunity_id).toBe(OPP_M8_FEATURES_INFRA);
    // Scope attribution (M2) and production-source scoring (M8) compose: the
    // anchor file is untouched and the new file is what carries the decision.
    expect(violations[0].evidence_paths).toEqual(['libs/features/src/pricing.ts']);
  });

  it.each([
    ['M8-B', 'libs/features/src/pricing.spec.ts', FEATURES_TO_INFRA],
    ['M8-C', 'libs/features/src/__tests__/harness.ts', FEATURES_TO_INFRA],
    ['M8-D', 'libs/features/jest.config.ts', JEST_CONFIG_TO_INFRA],
  ])('%s: the excluded file creates no finding of any kind', (_id, rel, contents) => {
    const r = scoreM8(snapshotWith({ [rel]: contents }));
    expect(r.raw_violation_count).toBe(0);
    expect(r.verdict).toBe('CONFORMANT');
    expect(r.findings.some((f) => f.evidence_paths.includes(rel))).toBe(false);
    expect(r.production_source.excluded_paths).toContain(rel);
  });

  it('M8-E: the production opportunity stays SATISFIED when only the test violates', () => {
    const clean = scoreM8(snapshotWith());
    const withTestOnlyDependency = scoreM8(
      snapshotWith({
        'libs/features/src/discount.ts': FEATURES_TO_CORE,
        'libs/features/src/discount.spec.ts': FEATURES_TO_INFRA,
      }),
    );
    expect(oppStatus(withTestOnlyDependency, OPP_M8_FEATURES_INFRA)).toBe('SATISFIED');
    // ...and it scores identically to the snapshot that has no test at all.
    expect(withTestOnlyDependency.opportunity_accounting).toEqual(clean.opportunity_accounting);
    expect(withTestOnlyDependency.raw_violation_count).toBe(clean.raw_violation_count);
  });

  it('M8-F: a forbidden production dependency violates EXACTLY once amid test noise', () => {
    const m8f = M8_MUTANTS.find((m) => m.id === 'M8-F') as ProdMutant;
    const r = scoreM8(m8f.files);
    expect(oppStatus(r, OPP_M8_FEATURES_INFRA)).toBe('VIOLATION');
    expect(r.opportunity_accounting.violated_opportunity_count).toBe(1);
    // Four files carry the prohibited import; only the one production file counts.
    expect(r.raw_violation_count).toBe(1);
    expect(
      r.findings.filter((f) => f.violation && f.opportunity_id === OPP_M8_FEATURES_INFRA),
    ).toHaveLength(1);
    expect(r.findings.find((f) => f.violation)?.evidence_paths).toEqual([
      'libs/features/src/gateway.ts',
    ]);
  });

  it('the frozen denominator is identical across every M8 mutant', () => {
    for (const m of M8_MUTANTS) {
      const r = scoreM8(m.files);
      expect(r.opportunity_accounting.applicable_opportunity_count).toBe(M8_DENOMINATOR);
    }
  });

  it('adding more test/config files cannot change applicable_opportunity_count', () => {
    const many: Record<string, string> = {};
    for (let i = 0; i < 20; i += 1) {
      many[`libs/features/src/gen${i}.spec.ts`] = FEATURES_TO_INFRA;
      many[`libs/features/src/__tests__/gen${i}.ts`] = FEATURES_TO_INFRA;
    }
    many['libs/features/jest.config.ts'] = JEST_CONFIG_TO_INFRA;
    const noisy = scoreM8(snapshotWith(many));
    const clean = scoreM8(snapshotWith());
    expect(noisy.opportunity_accounting.applicable_opportunity_count).toBe(M8_DENOMINATOR);
    // Neither side of E1 moved: same denominator, same numerator.
    expect(noisy.opportunity_accounting).toEqual(clean.opportunity_accounting);
    expect(noisy.raw_violation_count).toBe(0);
    expect(noisy.production_source.excluded_file_count).toBe(41);
    expect(noisy.production_source.production_file_count).toBe(
      clean.production_source.production_file_count,
    );
  });

  it('test/config-only files cannot increase the E1 numerator', () => {
    const clean = scoreM8(snapshotWith());
    const testOnly = scoreM8(
      snapshotWith({
        'libs/features/src/a.spec.ts': FEATURES_TO_INFRA,
        'libs/features/src/__mocks__/infra.ts': FEATURES_TO_INFRA,
        'libs/features/src/test-helpers/build.ts': FEATURES_TO_INFRA,
        'apps/api/src/app.spec.ts': API_TO_CORE,
        'apps/api/jest.config.ts': JEST_CONFIG_TO_INFRA,
      }),
    );
    expect(testOnly.opportunity_accounting.violated_opportunity_count).toBe(0);
    expect(testOnly.opportunity_accounting).toEqual(clean.opportunity_accounting);
    expect(testOnly.raw_violation_count).toBe(0);
  });

  it('a frozen scope left with only test files is NOT_APPLICABLE, never SATISFIED', () => {
    // The production features layer is gone; only a spec remains. The decision
    // has no production material to evaluate, so it must not be scored as fixed.
    const r = scoreM8(
      snapshotWith({ [FEATURES_ANCHOR]: null, 'libs/features/src/left.spec.ts': FEATURES_TO_INFRA }),
    );
    expect(oppStatus(r, OPP_M8_FEATURES_INFRA)).toBe('NOT_APPLICABLE');
    expect(r.opportunity_accounting.applicable_opportunity_count).toBe(M8_DENOMINATOR);
    expect(r.opportunity_accounting.violated_opportunity_count).toBe(0);
  });

  it('scoring stays deterministic under the production-source partition', () => {
    const m8f = M8_MUTANTS.find((m) => m.id === 'M8-F') as ProdMutant;
    expect(JSON.stringify(scoreM8(m8f.files))).toEqual(JSON.stringify(scoreM8(m8f.files)));
  });
});

// --------------------------------------------------------------------------- //
// The production-source policy itself: explicit, auditable, additive-only
// --------------------------------------------------------------------------- //
describe('production-source policy classification', () => {
  it.each([
    ['libs/features/src/index.ts', 'production'],
    ['apps/api/src/app.ts', 'production'],
    ['libs/features/src/pricing.spec.ts', 'test-spec'],
    ['libs/features/src/pricing.test.ts', 'test-spec'],
    ['apps/api/src/app.spec.tsx', 'test-spec'],
    ['libs/features/src/__tests__/harness.ts', 'test-support'],
    ['libs/features/src/__mocks__/infra.ts', 'test-support'],
    ['libs/core/src/test-helpers/build.ts', 'test-support'],
    ['libs/features/jest.config.ts', 'tool-config'],
    ['jest.config.ts', 'tool-config'],
    ['webpack.config.ts', 'tool-config'],
  ])('classifies %s as %s', (rel, expected) => {
    expect(classifySourceFile(rel)).toBe(expected);
  });

  it.each([
    'libs/core/src/latest.ts',
    'libs/core/src/contest.ts',
    'libs/core/src/testUtils.ts',
    'libs/core/src/protest/index.ts',
    'apps/api/src/app.config.ts',
    'libs/features/src/manifest.ts',
  ])('does not exclude production source with an incidental word: %s', (rel) => {
    expect(isProductionSource(rel)).toBe(true);
    expect(classifySourceFile(rel)).toBe('production');
  });

  it('partitions a file list without losing or duplicating a path', () => {
    const files = [
      'apps/api/src/app.ts',
      'apps/api/src/app.spec.ts',
      'apps/api/jest.config.ts',
      'libs/core/src/latest.ts',
    ];
    const { production, excluded } = partitionProductionSources(files);
    expect(production).toEqual(['apps/api/src/app.ts', 'libs/core/src/latest.ts']);
    expect(excluded).toEqual(['apps/api/src/app.spec.ts', 'apps/api/jest.config.ts']);
    expect([...production, ...excluded].sort()).toEqual([...files].sort());
  });

  it('applies the baseline when a manifest declares no policy at all', () => {
    const policy = resolveProductionSourcePolicy(undefined);
    expect(policy.policy_id).toBe(BASELINE_PRODUCTION_SOURCE_POLICY_ID);
    expect(policy.excluded_spec_basename_globs).toContain('*.spec.ts');
    expect(policy.excluded_config_basenames).toContain('jest.config.ts');
    expect(policy.excluded_directory_names).toContain('__tests__');
  });

  it('a manifest extension only ADDS exclusions; it cannot re-admit a baseline class', () => {
    const policy = resolveProductionSourcePolicy({
      policy_id: 'repo-extras',
      additional_excluded_directory_names: ['testing'],
      additional_excluded_config_basenames: ['tools.config.ts'],
      additional_excluded_spec_basename_globs: ['*.fixture.ts'],
    });
    // baseline retained ...
    expect(policy.excluded_spec_basename_globs).toContain('*.spec.ts');
    expect(policy.excluded_directory_names).toContain('__tests__');
    // ... plus the additions, and the id still records the baseline it extends
    expect(policy.excluded_directory_names).toContain('testing');
    expect(policy.excluded_config_basenames).toContain('tools.config.ts');
    expect(policy.policy_id.startsWith(BASELINE_PRODUCTION_SOURCE_POLICY_ID)).toBe(true);
    expect(classifySourceFile('libs/core/src/testing/x.ts', policy)).toBe('test-support');
    // and the baseline classes are untouched by the extension
    expect(classifySourceFile('libs/core/src/x.spec.ts', policy)).toBe('test-spec');
  });

  it('an extended policy is reported on the finding and is applied end-to-end', () => {
    const dependencyPolicy = {
      ...baseDependencyPolicy(),
      production_source_policy: {
        policy_id: 'repo-extras',
        additional_excluded_directory_names: ['testing'],
      },
    };
    const r = scoreM8(snapshotWith({ 'libs/features/src/testing/double.ts': FEATURES_TO_INFRA }), {
      dependency_policy: dependencyPolicy,
    });
    expect(r.production_source.policy_id).toBe(
      `${BASELINE_PRODUCTION_SOURCE_POLICY_ID}+repo-extras`,
    );
    expect(r.production_source.excluded_paths).toEqual(['libs/features/src/testing/double.ts']);
    expect(r.raw_violation_count).toBe(0);
    expect(oppStatus(r, OPP_M8_FEATURES_INFRA)).toBe('SATISFIED');
    // Without the extension the very same file IS production and DOES violate.
    const baseline = scoreM8(
      snapshotWith({ 'libs/features/src/testing/double.ts': FEATURES_TO_INFRA }),
    );
    expect(oppStatus(baseline, OPP_M8_FEATURES_INFRA)).toBe('VIOLATION');
  });

  it.each([
    [{ additional_excluded_directory_names: 'nope' }, /must be an array of strings/],
    [{ additional_excluded_config_basenames: ['libs/x.ts'] }, /must not contain/],
    [{ additional_excluded_directory_names: ['__t*__'] }, /glob wildcard/],
    [{ additional_excluded_spec_basename_globs: ['a/b.spec.ts'] }, /must not contain/],
    [{ additional_excluded_spec_basename_globs: [''] }, /empty entry/],
    [{ policy_id: '' }, /non-empty string/],
  ])('fails closed on a malformed production-source policy (%#)', (declared, message) => {
    expect(() => resolveProductionSourcePolicy(declared)).toThrow(OracleError);
    expect(() => resolveProductionSourcePolicy(declared)).toThrow(message as RegExp);
  });

  it('a malformed policy refuses to score rather than reverting to the baseline', () => {
    expectFailClosed(
      snapshotWith({ 'libs/features/src/pricing.ts': FEATURES_TO_INFRA }),
      baseManifest({
        opportunities: m8Opportunities(),
        dependency_policy: {
          ...baseDependencyPolicy(),
          production_source_policy: { additional_excluded_directory_names: ['a/b'] },
        },
      }),
      /INVALID_PRODUCTION_SOURCE_POLICY/,
    );
  });
});
