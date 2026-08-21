/**
 * Manifest-integrity fail-closed guards (P1 fixes for the Prompt 3A review):
 *   P1-1 duplicate opportunity_id rejection,
 *   P1-2 opportunity rule-reference validation,
 *   P1-3 manifest lifecycle enforcement (score only frozen, non-invalidated).
 *
 * Each guard must FAIL CLOSED (throw OracleError) rather than silently mis-score
 * or drop an opportunity, and must never let a bad manifest reach CONFORMANT /
 * PENDING.
 */

import {
  ArchitectureFinding,
  EvaluateOptions,
  OracleError,
  assertOpportunityAccountingComplete,
  evaluateSnapshot,
} from '../src';
import { baseManifest, cleanup, makeTmpRoot, materializeSnapshot, writeManifest } from './helpers';

function score(caseName: string, manifest: Record<string, unknown>): ArchitectureFinding {
  const tmp = makeTmpRoot();
  try {
    const snapshotDir = materializeSnapshot(tmp, caseName);
    const manifestPath = writeManifest(tmp, manifest);
    return evaluateSnapshot({ snapshotDir, manifestPath, snapshotId: caseName });
  } finally {
    cleanup(tmp);
  }
}

function expectFailClosed(
  caseName: string,
  manifest: Record<string, unknown>,
  reason: RegExp,
): OracleError {
  const tmp = makeTmpRoot();
  try {
    const snapshotDir = materializeSnapshot(tmp, caseName);
    const manifestPath = writeManifest(tmp, manifest);
    let thrown: unknown;
    try {
      evaluateSnapshot({ snapshotDir, manifestPath, snapshotId: caseName });
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

/**
 * A frozen dependency opportunity. `scope` is the SCORING ANCHOR (a
 * dependency-policy layer id) and `forbidden` the target layers the decision
 * forbids; `importer` is provenance only. See scopeAttribution.test.ts for the
 * end-to-end attribution corpus.
 */
const depOpp = (id: string, rule: string, importer: string, scope: string, forbidden: string[]) => ({
  opportunity_id: id,
  rule_id: rule,
  locator: { importer_path: importer, scope, forbidden_target_layers: forbidden },
  description: null,
});

// --------------------------------------------------------------------------- //
// P1-1 — duplicate opportunity IDs
// --------------------------------------------------------------------------- //
describe('P1-1 duplicate opportunity_id rejection', () => {
  it('accepts a manifest whose opportunity IDs are all unique', () => {
    const r = score('clean_alias', baseManifest({
      opportunities: [
        depOpp('OPP-1', 'AR-DEP-006', 'libs/features/src/index.ts', 'features', ['infra']),
        depOpp('OPP-2', 'AR-DEP-003', 'libs/core/src/index.ts', 'core', ['infra']),
      ],
    }));
    expect(r.verdict).toBe('CONFORMANT');
    expect(r.opportunity_accounting.applicable_opportunity_count).toBe(2);
    // Denominator equals the set of uniquely scored opportunity IDs.
    const scoredIds = new Set(r.findings.filter((f) => f.opportunity_id).map((f) => f.opportunity_id));
    expect(scoredIds.size).toBe(2);
  });

  it('fails closed on two identical opportunity IDs (same rule)', () => {
    const err = expectFailClosed('clean_alias', baseManifest({
      opportunities: [
        depOpp('OPP-DUP', 'AR-DEP-003', 'libs/core/src/index.ts', 'core', ['infra']),
        depOpp('OPP-DUP', 'AR-DEP-006', 'libs/features/src/index.ts', 'features', ['infra']),
      ],
    }), /DUPLICATE_OPPORTUNITY_ID/);
    expect(err.message).toContain('OPP-DUP');
  });

  it('fails closed on duplicate IDs across DIFFERENT rule IDs', () => {
    expectFailClosed('clean_alias', baseManifest({
      opportunities: [
        depOpp('OPP-X', 'AR-DEP-006', 'libs/features/src/index.ts', 'features', ['infra']),
        depOpp('OPP-X', 'AR-DEP-003', 'libs/core/src/index.ts', 'core', ['infra']),
      ],
    }), /DUPLICATE_OPPORTUNITY_ID/);
  });

  it('duplicate IDs cannot inflate violation/opportunity counts (throws before scoring)', () => {
    // The exact G-01 scenario: one satisfied importer and one violating importer
    // share an id. Rather than mis-scoring (satisfied counted as violated), the
    // engine refuses to produce any result at all.
    expectFailClosed('violating_alias', baseManifest({
      opportunities: [
        depOpp('OPP-SAME', 'AR-DEP-004', 'libs/infra/src/index.ts', 'infra', ['core']),
        depOpp('OPP-SAME', 'AR-DEP-003', 'libs/core/src/index.ts', 'core', ['infra']),
      ],
    }), /DUPLICATE_OPPORTUNITY_ID/);
  });

  it('duplicate IDs cannot produce a CONFORMANT or PENDING result', () => {
    // clean snapshot (would be CONFORMANT) with a duplicate id:
    expectFailClosed('clean_alias', baseManifest({
      opportunities: [
        depOpp('OPP-D', 'AR-DEP-003', 'libs/core/src/index.ts', 'core', ['infra']),
        depOpp('OPP-D', 'AR-DEP-006', 'libs/features/src/index.ts', 'features', ['infra']),
      ],
    }), /DUPLICATE_OPPORTUNITY_ID/);
    // + an applicable unimplemented rule (would otherwise force PENDING):
    expectFailClosed('clean_alias', baseManifest({
      applicable_rule_ids: ['AR-DEP-001', 'AR-CONTRACT-001'],
      opportunities: [
        depOpp('OPP-D', 'AR-DEP-003', 'libs/core/src/index.ts', 'core', ['infra']),
        depOpp('OPP-D', 'AR-DEP-006', 'libs/features/src/index.ts', 'features', ['infra']),
      ],
    }), /DUPLICATE_OPPORTUNITY_ID/);
  });
});

// --------------------------------------------------------------------------- //
// P1-2 — opportunity rule-reference validation
// --------------------------------------------------------------------------- //
describe('P1-2 opportunity rule-reference validation', () => {
  it('accepts an opportunity for a known, in-force, implemented dependency rule', () => {
    const r = score('clean_alias', baseManifest({
      opportunities: [depOpp('OPP-OK', 'AR-DEP-003', 'libs/core/src/index.ts', 'core', ['infra'])],
    }));
    expect(r.verdict).toBe('CONFORMANT');
    expect(r.opportunity_accounting.applicable_opportunity_count).toBe(1);
    expect(r.opportunity_accounting.fixed_opportunity_count).toBe(1);
  });

  it('fails closed on an opportunity referencing an UNKNOWN rule id', () => {
    expectFailClosed('clean_alias', baseManifest({
      opportunities: [depOpp('OPP-U', 'AR-BOGUS-999', 'libs/core/src/index.ts', 'core', ['infra'])],
    }), /INVALID_OPPORTUNITY_RULE/);
  });

  it('fails closed on a known rule that is NOT in applicable_rule_ids (nor covered by the umbrella)', () => {
    expectFailClosed('clean_alias', baseManifest({
      applicable_rule_ids: ['AR-DEP-002'],
      opportunities: [depOpp('OPP-NA', 'AR-DEP-003', 'libs/core/src/index.ts', 'core', ['infra'])],
    }), /INVALID_OPPORTUNITY_RULE/);
  });

  it('fails closed on a known but UNIMPLEMENTED (stub) rule used as a scored opportunity', () => {
    expectFailClosed('clean_alias', baseManifest({
      applicable_rule_ids: ['AR-DEP-001', 'AR-CONTRACT-001'],
      opportunities: [depOpp('OPP-STUB', 'AR-CONTRACT-001', 'libs/core/src/index.ts', 'core', ['infra'])],
    }), /INVALID_OPPORTUNITY_RULE/);
  });

  it('fails closed on a MIX of valid and invalid opportunities', () => {
    expectFailClosed('clean_alias', baseManifest({
      opportunities: [
        depOpp('OPP-GOOD', 'AR-DEP-003', 'libs/core/src/index.ts', 'core', ['infra']),
        depOpp('OPP-BAD', 'AR-BOGUS-999', 'libs/features/src/index.ts', 'features', ['infra']),
      ],
    }), /INVALID_OPPORTUNITY_RULE/);
  });

  it('does NOT silently drop an opportunity to a zero-denominator CONFORMANT (P1-2)', () => {
    // Before the fix, a stub-rule opportunity was filtered out of accounting,
    // leaving applicable_opportunity_count=0 and a misleading CONFORMANT on a
    // clean snapshot. It must fail closed instead of silently reporting zero.
    expectFailClosed('clean_alias', baseManifest({
      applicable_rule_ids: ['AR-DEP-001', 'AR-CODE-001'],
      opportunities: [depOpp('OPP-DROP', 'AR-CODE-001', 'libs/core/src/index.ts', 'core', ['infra'])],
    }), /INVALID_OPPORTUNITY_RULE/);
  });
});

// --------------------------------------------------------------------------- //
// Umbrella prohibition + locator integrity (scope-based attribution)
// --------------------------------------------------------------------------- //
describe('AR-DEP-001 may expand exposure but can never back a scored opportunity', () => {
  it('fails closed with a DEDICATED reason when the umbrella is used as an opportunity rule', () => {
    const err = expectFailClosed('clean_alias', baseManifest({
      opportunities: [depOpp('OPP-UMB', 'AR-DEP-001', 'libs/core/src/index.ts', 'core', ['infra'])],
    }), /UMBRELLA_OPPORTUNITY_RULE/);
    expect(err.reason).toBe('UMBRELLA_OPPORTUNITY_RULE');
    expect(err.message).toContain('AR-DEP-001');
  });

  it('rejects the umbrella opportunity even in a mixed set of otherwise valid leaves', () => {
    expectFailClosed('clean_alias', baseManifest({
      opportunities: [
        depOpp('OPP-LEAF', 'AR-DEP-003', 'libs/core/src/index.ts', 'core', ['infra']),
        depOpp('OPP-UMB', 'AR-DEP-001', 'libs/features/src/index.ts', 'features', ['infra']),
      ],
    }), /UMBRELLA_OPPORTUNITY_RULE/);
  });

  it('still accepts the umbrella in applicable_rule_ids alongside leaf opportunities', () => {
    const r = score('clean_alias', baseManifest({
      applicable_rule_ids: ['AR-DEP-001'],
      opportunities: [depOpp('OPP-LEAF', 'AR-DEP-003', 'libs/core/src/index.ts', 'core', ['infra'])],
    }));
    expect(r.opportunity_accounting.applicable_opportunity_count).toBe(1);
    expect(r.rules_evaluated.map((x) => x.rule_id)).toContain('AR-DEP-005');
  });
});

describe('locator integrity — the frozen scope must be scoreable', () => {
  it('fails closed on a scope that is not a frozen dependency-policy layer', () => {
    expectFailClosed('clean_alias', baseManifest({
      opportunities: [depOpp('OPP-S', 'AR-DEP-003', 'libs/core/src/index.ts', 'scope:core', ['infra'])],
    }), /INVALID_OPPORTUNITY_SCOPE/);
  });

  it('fails closed on a rule that is not the leaf for the declared relationship', () => {
    expectFailClosed('clean_alias', baseManifest({
      opportunities: [depOpp('OPP-M', 'AR-DEP-006', 'libs/core/src/index.ts', 'core', ['infra'])],
    }), /OPPORTUNITY_RULE_SCOPE_MISMATCH/);
  });

  it('fails closed when two opportunities claim the same frozen decision', () => {
    expectFailClosed('clean_alias', baseManifest({
      opportunities: [
        depOpp('OPP-A', 'AR-DEP-003', 'libs/core/src/index.ts', 'core', ['infra']),
        depOpp('OPP-B', 'AR-DEP-003', 'libs/core/src/other.ts', 'core', ['infra', 'api']),
      ],
    }), /DUPLICATE_OPPORTUNITY_SCOPE/);
  });
});

// --------------------------------------------------------------------------- //
// P1-3 — manifest lifecycle enforcement
// --------------------------------------------------------------------------- //
describe('P1-3 manifest lifecycle enforcement', () => {
  it('scores a frozen, non-invalidated manifest and records lifecycle provenance', () => {
    const r = score('clean_alias', baseManifest({ status: 'frozen' }));
    expect(r.verdict).toBe('CONFORMANT');
    expect(r.manifest_ref.status).toBe('frozen');
    expect(r.manifest_ref.invalidated).toBe(false);
  });

  it('fails closed for template / draft / review / deprecated statuses', () => {
    for (const status of ['template', 'draft', 'review', 'deprecated']) {
      expectFailClosed('clean_alias', baseManifest({ status }), /MANIFEST_NOT_FROZEN/);
    }
  });

  it('fails closed for an invalidated frozen manifest', () => {
    expectFailClosed('clean_alias', baseManifest({
      status: 'frozen',
      invalidation: { invalidated: true, reason: 'superseded by EM-2', superseded_by: 'EM-2' },
    }), /MANIFEST_INVALIDATED/);
  });

  it('fails closed when lifecycle fields are missing', () => {
    const noStatus = baseManifest({ status: 'frozen' });
    delete (noStatus as Record<string, unknown>).status;
    expectFailClosed('clean_alias', noStatus, /MANIFEST_LIFECYCLE_MISSING/);

    const noInvalidation = baseManifest({ status: 'frozen' });
    delete (noInvalidation as Record<string, unknown>).invalidation;
    expectFailClosed('clean_alias', noInvalidation, /MANIFEST_LIFECYCLE_MISSING/);
  });

  it('does NOT expose the invalidation reason toward the coding model', () => {
    const SECRET = 'SECRET-TASK-ANSWER-must-not-leak';
    const err = expectFailClosed('clean_alias', baseManifest({
      status: 'frozen',
      invalidation: { invalidated: true, reason: SECRET, superseded_by: null },
    }), /MANIFEST_INVALIDATED/);
    expect(err.message).not.toContain(SECRET);
    expect(err.detail ?? '').not.toContain(SECRET);
  });

  it('a lifecycle failure can never yield CONFORMANT (clean snapshot, non-frozen manifest)', () => {
    // clean_alias is CONFORMANT when frozen; as a draft it must fail closed.
    expectFailClosed('clean_alias', baseManifest({ status: 'draft' }), /MANIFEST_NOT_FROZEN/);
  });
});

// --------------------------------------------------------------------------- //
// Suite-classification decision D — analysis-eligibility gates
// --------------------------------------------------------------------------- //
function scoreWith(
  caseName: string,
  manifest: Record<string, unknown>,
  extra: Partial<EvaluateOptions>,
): ArchitectureFinding {
  const tmp = makeTmpRoot();
  try {
    const snapshotDir = materializeSnapshot(tmp, caseName);
    const manifestPath = writeManifest(tmp, manifest);
    return evaluateSnapshot({ snapshotDir, manifestPath, snapshotId: caseName, ...extra });
  } finally {
    cleanup(tmp);
  }
}

function expectFailClosedWith(
  caseName: string,
  manifest: Record<string, unknown>,
  extra: Partial<EvaluateOptions>,
  reason: RegExp,
): OracleError {
  const tmp = makeTmpRoot();
  try {
    const snapshotDir = materializeSnapshot(tmp, caseName);
    const manifestPath = writeManifest(tmp, manifest);
    let thrown: unknown;
    try {
      evaluateSnapshot({ snapshotDir, manifestPath, snapshotId: caseName, ...extra });
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

/**
 * A frozen dep-family opportunity covering the violating_alias fixture's decision
 * (the core scope must not reach infra). `scope` is the dependency-policy LAYER
 * ID, not the catalog scope tag.
 */
const VIOLATING_OPP = depOpp(
  'OPP-1',
  'AR-DEP-003',
  'libs/core/src/index.ts',
  'core',
  ['infra'],
);

describe('decision D — e1_analysis_eligibility is required and fails closed', () => {
  it('refuses a pre-migration manifest that carries no eligibility field', () => {
    const err = expectFailClosed(
      'clean_alias',
      baseManifest({ e1_analysis_eligibility: null }),
      /ELIGIBILITY_MISSING/,
    );
    expect(err.message).toMatch(/migrated/);
  });

  it('refuses an unrecognised eligibility value', () => {
    expectFailClosed(
      'clean_alias',
      baseManifest({ e1_analysis_eligibility: 'eligible' }),
      /ELIGIBILITY_MISSING/,
    );
  });

  it('accepts the three approved values when they agree with the opportunity set', () => {
    expect(scoreWith('clean_alias', baseManifest({ e1_analysis_eligibility: 'functional-only' }), {}).verdict)
      .toBe('CONFORMANT');
    expect(
      scoreWith(
        'violating_alias',
        baseManifest({ opportunities: [VIOLATING_OPP], e1_analysis_eligibility: 'scored' }),
        {},
      ).opportunity_accounting.applicable_opportunity_count,
    ).toBe(1);
  });
});

describe('decision D gate 1 — the manifest must match the approved public task index', () => {
  it('refuses a real task id when no approved index is supplied', () => {
    expectFailClosed(
      'clean_alias',
      baseManifest({ task_id: 'PT06', e1_analysis_eligibility: 'functional-only' }),
      /ELIGIBILITY_TASK_INDEX_MISMATCH/,
    );
  });

  it('refuses a task that is absent from the approved index', () => {
    expectFailClosedWith(
      'clean_alias',
      baseManifest({ task_id: 'PT99', e1_analysis_eligibility: 'functional-only' }),
      { approvedEligibility: { PT06: 'functional-only' } },
      /ELIGIBILITY_TASK_INDEX_MISMATCH/,
    );
  });

  it('refuses a manifest whose eligibility disagrees with the approved index', () => {
    // PT06 is functional-only publicly; a manifest claiming `scored` must fail.
    const err = expectFailClosedWith(
      'violating_alias',
      baseManifest({
        task_id: 'PT06',
        opportunities: [VIOLATING_OPP],
        e1_analysis_eligibility: 'scored',
      }),
      { approvedEligibility: { PT06: 'functional-only' } },
      /ELIGIBILITY_TASK_INDEX_MISMATCH/,
    );
    expect(err.message).toMatch(/PT06/);
  });

  it('accepts a manifest that agrees with the approved index', () => {
    const finding = scoreWith(
      'violating_alias',
      baseManifest({ task_id: 'PT01', opportunities: [VIOLATING_OPP], e1_analysis_eligibility: 'scored' }),
      { approvedEligibility: { PT01: 'scored', PT06: 'functional-only' } },
    );
    expect(finding.opportunity_accounting.applicable_opportunity_count).toBe(1);
    expect(finding.opportunity_accounting.violated_opportunity_count).toBe(1);
  });
});

describe('decision D gate 2 — functional-only contributes no E1 denominator', () => {
  it('refuses a functional-only manifest that carries a dependency-direction opportunity', () => {
    const err = expectFailClosed(
      'violating_alias',
      baseManifest({ opportunities: [VIOLATING_OPP], e1_analysis_eligibility: 'functional-only' }),
      /ELIGIBILITY_DENOMINATOR_CONFLICT/,
    );
    expect(err.message).toMatch(/structurally excluded from E1/);
  });

  it('accepts a functional-only manifest with an empty opportunity set', () => {
    const finding = scoreWith('clean_alias', baseManifest({ e1_analysis_eligibility: 'functional-only' }), {});
    expect(finding.opportunity_accounting.applicable_opportunity_count).toBe(0);
  });
});

describe('decision D gate 3 — an inactive reserve enters no E1 run', () => {
  it('refuses an inactive-reserve manifest even when its opportunity set is empty', () => {
    expectFailClosed(
      'clean_alias',
      baseManifest({ task_id: null, e1_analysis_eligibility: 'inactive-reserve' }),
      /ELIGIBILITY_RESERVE_INACTIVE/,
    );
  });

  it('does NOT require a reserve to delete its draft opportunities — they are simply never scored', () => {
    // The reserve keeps draft opportunities; the engine still refuses to score it,
    // so those opportunities are analytically inactive rather than deleted.
    const reserve = baseManifest({
      opportunities: [VIOLATING_OPP],
      e1_analysis_eligibility: 'inactive-reserve',
    });
    expect((reserve.opportunities as unknown[]).length).toBe(1);
    expectFailClosed('violating_alias', reserve, /ELIGIBILITY_RESERVE_INACTIVE/);
  });

  it('scores a reserve only under a separately recorded pre-run activation decision', () => {
    const reserve = baseManifest({
      task_id: 'PR01',
      opportunities: [VIOLATING_OPP],
      e1_analysis_eligibility: 'inactive-reserve',
    });
    const finding = scoreWith('violating_alias', reserve, {
      approvedEligibility: { PR01: 'inactive-reserve' },
      reserveActivation: {
        task_id: 'PR01',
        activated_eligibility: 'scored',
        decision_ref: 'ACTIVATION-2026-08-PR01',
      },
    });
    expect(finding.opportunity_accounting.applicable_opportunity_count).toBe(1);
  });

  it('ignores an activation decision recorded for a different task', () => {
    expectFailClosedWith(
      'violating_alias',
      baseManifest({
        task_id: 'PR01',
        opportunities: [VIOLATING_OPP],
        e1_analysis_eligibility: 'inactive-reserve',
      }),
      {
        approvedEligibility: { PR01: 'inactive-reserve' },
        reserveActivation: {
          task_id: 'PR02',
          activated_eligibility: 'scored',
          decision_ref: 'ACTIVATION-2026-08-PR02',
        },
      },
      /ELIGIBILITY_RESERVE_INACTIVE/,
    );
  });
});

describe('decision D gate 4 — a scored task needs a non-zero frozen denominator', () => {
  it('refuses a scored manifest with no applicable frozen opportunity', () => {
    const err = expectFailClosed(
      'clean_alias',
      baseManifest({ opportunities: [], e1_analysis_eligibility: 'scored' }),
      /ELIGIBILITY_SCORED_WITHOUT_OPPORTUNITIES/,
    );
    expect(err.message).toMatch(/never be entered as zero violations/);
  });

  it('a zero-exposure scored manifest can never yield CONFORMANT', () => {
    // clean_alias would otherwise score CONFORMANT with a zero denominator, which
    // is exactly the zero-violation coding the decision forbids.
    expectFailClosed(
      'clean_alias',
      baseManifest({ opportunities: [], e1_analysis_eligibility: 'scored' }),
      /ELIGIBILITY_SCORED_WITHOUT_OPPORTUNITIES/,
    );
  });
});

// ---------------------------------------------------------------------------
// The frozen-opportunity accounting reconciliation (INCOMPLETE_SCORING).
//
// Both branches of this guard are DEFENSIVE: they cannot be reached through any
// valid manifest, because the loader's DUPLICATE_OPPORTUNITY_ID check and
// assertOpportunityRulesValid refuse first. An independent review accepted that
// ordering as correct but flagged the consequence - the guard itself was never
// exercised, so nothing would notice if it stopped working.
//
// It is therefore driven DIRECTLY here, at the unit that owns the reconciliation,
// with inconsistent accounting inputs. No earlier integrity gate is weakened to
// make the branch reachable through a manifest, and the engine calls this unit at
// exactly the point the inline code used to occupy.
// ---------------------------------------------------------------------------
describe('assertOpportunityAccountingComplete — the INCOMPLETE_SCORING guard', () => {
  const consistent = {
    applicable_opportunity_count: 2,
    fixed_opportunity_count: 1,
    violated_opportunity_count: 1,
    absent_opportunity_count: 0,
  };

  function expectIncompleteScoring(fn: () => void, detail: RegExp): OracleError {
    let thrown: unknown;
    try {
      fn();
    } catch (e) {
      thrown = e;
    }
    expect(thrown).toBeInstanceOf(OracleError);
    const err = thrown as OracleError;
    expect(err.reason).toBe('INCOMPLETE_SCORING');
    expect(`${err.message} ${err.detail ?? ''}`).toMatch(detail);
    return err;
  }

  it('accepts a complete, consistent accounting', () => {
    expect(() =>
      assertOpportunityAccountingComplete(2, 2, consistent),
    ).not.toThrow();
  });

  it('accepts a zero-opportunity accounting (a functional-only manifest)', () => {
    expect(() =>
      assertOpportunityAccountingComplete(0, 0, {
        applicable_opportunity_count: 0,
        fixed_opportunity_count: 0,
        violated_opportunity_count: 0,
        absent_opportunity_count: 0,
      }),
    ).not.toThrow();
  });

  it('BRANCH 1: refuses when a frozen opportunity was dropped from accounting', () => {
    // The denominator would be 1 while the manifest froze 2 - a smaller
    // denominator on the same numerator, i.e. a silently inflated rate.
    const err = expectIncompleteScoring(
      () =>
        assertOpportunityAccountingComplete(1, 2, {
          ...consistent,
          applicable_opportunity_count: 1,
          violated_opportunity_count: 0,
        }),
      /accounted=1 manifest=2/,
    );
    expect(err.message).toMatch(/excluded from accounting/);
    expect(err.message).toMatch(/denominator != scoring-opportunity set/);
  });

  it('BRANCH 1: refuses in the other direction too (more accounted than frozen)', () => {
    expectIncompleteScoring(
      () => assertOpportunityAccountingComplete(3, 2, consistent),
      /accounted=3 manifest=2/,
    );
  });

  it('BRANCH 2: refuses when an opportunity is bucketed under no status', () => {
    // applicable=2 but only one opportunity reached a bucket: one was scored
    // under nothing at all.
    expectIncompleteScoring(
      () =>
        assertOpportunityAccountingComplete(2, 2, {
          applicable_opportunity_count: 2,
          fixed_opportunity_count: 1,
          violated_opportunity_count: 0,
          absent_opportunity_count: 0,
        }),
      /applicable=2 fixed\+violated\+absent=1/,
    );
  });

  it('BRANCH 2: refuses when an opportunity is bucketed twice', () => {
    // The same opportunity counted as both violated and absent would double-count
    // one architectural decision.
    expectIncompleteScoring(
      () =>
        assertOpportunityAccountingComplete(2, 2, {
          applicable_opportunity_count: 2,
          fixed_opportunity_count: 1,
          violated_opportunity_count: 1,
          absent_opportunity_count: 1,
        }),
      /applicable=2 fixed\+violated\+absent=3/,
    );
  });

  it('the guard is the one the engine actually calls', () => {
    // Guard the guard: a real end-to-end score must still pass through a
    // consistent reconciliation, so the extraction did not bypass it.
    const finding = score('clean_alias', baseManifest({}));
    const acc = finding.opportunity_accounting;
    expect(() =>
      assertOpportunityAccountingComplete(
        acc.applicable_opportunity_count,
        acc.applicable_opportunity_count,
        acc,
      ),
    ).not.toThrow();
    expect(
      acc.fixed_opportunity_count +
        acc.violated_opportunity_count +
        acc.absent_opportunity_count,
    ).toBe(acc.applicable_opportunity_count);
  });

  it('remains unreachable through a valid manifest: the earlier gates refuse first', () => {
    // This is the reason the guard needs a direct test at all. The two manifests
    // that would otherwise reach the reconciliation are caught EARLIER - by P1-2
    // (rule not in force, so the dep-family filter would have dropped it) and by
    // the loader (duplicate opportunity_id, so one id would be bucketed twice).
    // That ordering is correct and must not be "fixed" to make the branch
    // reachable through a manifest.
    const dropped = expectFailClosed(
      'clean_alias',
      baseManifest({
        applicable_rule_ids: ['AR-DEP-006'],
        opportunities: [
          depOpp('OPP-1', 'AR-DEP-006', 'libs/features/src/index.ts', 'features', ['infra']),
          depOpp('OPP-2', 'AR-DEP-003', 'libs/core/src/index.ts', 'core', ['infra']),
        ],
      }),
      /INVALID_OPPORTUNITY_RULE/,
    );
    expect(dropped.reason).not.toBe('INCOMPLETE_SCORING');

    const doubled = expectFailClosed(
      'clean_alias',
      baseManifest({
        opportunities: [
          depOpp('OPP-SAME', 'AR-DEP-006', 'libs/features/src/index.ts', 'features', ['infra']),
          depOpp('OPP-SAME', 'AR-DEP-003', 'libs/core/src/index.ts', 'core', ['infra']),
        ],
      }),
      /DUPLICATE_OPPORTUNITY_ID/,
    );
    expect(doubled.reason).not.toBe('INCOMPLETE_SCORING');
  });
});
