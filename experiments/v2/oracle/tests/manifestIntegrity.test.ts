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

import { evaluateSnapshot, ArchitectureFinding, OracleError } from '../src';
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

const depOpp = (id: string, rule: string, importer: string, scope: string, forbidden: string[] = []) => ({
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
        depOpp('OPP-1', 'AR-DEP-001', 'libs/features/src/index.ts', 'features'),
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
        depOpp('OPP-DUP', 'AR-DEP-001', 'libs/core/src/index.ts', 'core'),
        depOpp('OPP-DUP', 'AR-DEP-001', 'libs/features/src/index.ts', 'features'),
      ],
    }), /DUPLICATE_OPPORTUNITY_ID/);
    expect(err.message).toContain('OPP-DUP');
  });

  it('fails closed on duplicate IDs across DIFFERENT rule IDs', () => {
    expectFailClosed('clean_alias', baseManifest({
      opportunities: [
        depOpp('OPP-X', 'AR-DEP-001', 'libs/core/src/index.ts', 'core'),
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
        depOpp('OPP-SAME', 'AR-DEP-001', 'libs/infra/src/index.ts', 'infra'),
        depOpp('OPP-SAME', 'AR-DEP-001', 'libs/core/src/index.ts', 'core', ['infra']),
      ],
    }), /DUPLICATE_OPPORTUNITY_ID/);
  });

  it('duplicate IDs cannot produce a CONFORMANT or PENDING result', () => {
    // clean snapshot (would be CONFORMANT) with a duplicate id:
    expectFailClosed('clean_alias', baseManifest({
      opportunities: [
        depOpp('OPP-D', 'AR-DEP-001', 'libs/core/src/index.ts', 'core'),
        depOpp('OPP-D', 'AR-DEP-001', 'libs/features/src/index.ts', 'features'),
      ],
    }), /DUPLICATE_OPPORTUNITY_ID/);
    // + an applicable unimplemented rule (would otherwise force PENDING):
    expectFailClosed('clean_alias', baseManifest({
      applicable_rule_ids: ['AR-DEP-001', 'AR-CONTRACT-001'],
      opportunities: [
        depOpp('OPP-D', 'AR-DEP-001', 'libs/core/src/index.ts', 'core'),
        depOpp('OPP-D', 'AR-DEP-001', 'libs/features/src/index.ts', 'features'),
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
      opportunities: [depOpp('OPP-U', 'AR-BOGUS-999', 'libs/core/src/index.ts', 'core')],
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
      opportunities: [depOpp('OPP-STUB', 'AR-CONTRACT-001', 'libs/core/src/index.ts', 'core')],
    }), /INVALID_OPPORTUNITY_RULE/);
  });

  it('fails closed on a MIX of valid and invalid opportunities', () => {
    expectFailClosed('clean_alias', baseManifest({
      opportunities: [
        depOpp('OPP-GOOD', 'AR-DEP-003', 'libs/core/src/index.ts', 'core', ['infra']),
        depOpp('OPP-BAD', 'AR-BOGUS-999', 'libs/features/src/index.ts', 'features'),
      ],
    }), /INVALID_OPPORTUNITY_RULE/);
  });

  it('does NOT silently drop an opportunity to a zero-denominator CONFORMANT (P1-2)', () => {
    // Before the fix, a stub-rule opportunity was filtered out of accounting,
    // leaving applicable_opportunity_count=0 and a misleading CONFORMANT on a
    // clean snapshot. It must fail closed instead of silently reporting zero.
    expectFailClosed('clean_alias', baseManifest({
      applicable_rule_ids: ['AR-DEP-001', 'AR-CODE-001'],
      opportunities: [depOpp('OPP-DROP', 'AR-CODE-001', 'libs/core/src/index.ts', 'core')],
    }), /INVALID_OPPORTUNITY_RULE/);
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
