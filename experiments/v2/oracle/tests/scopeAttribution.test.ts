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
 */

import { ArchitectureFinding, EvaluateOptions, OracleError, evaluateSnapshot } from '../src';
import { baseManifest, cleanup, makeTmpRoot, writeManifest, writeSnapshot } from './helpers';

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
