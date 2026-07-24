/**
 * Reference-checker validation over the synthetic fixture cases (PART D).
 * Proves: known violations are detected; known-good/legitimate solutions are not
 * flagged; comments/strings do not create import violations; alias, relative, and
 * barrel/re-export resolution work; moved/deleted code is handled; malformed
 * alias config fails closed.
 */

import { evaluateSnapshot, ArchitectureFinding } from '../src';
import {
  baseManifest,
  cleanup,
  makeTmpRoot,
  materializeSnapshot,
  writeManifest,
  ManifestOverrides,
} from './helpers';

function run(caseName: string, overrides: ManifestOverrides = {}): ArchitectureFinding {
  const tmp = makeTmpRoot();
  try {
    const snapshotDir = materializeSnapshot(tmp, caseName);
    const manifestPath = writeManifest(tmp, baseManifest(overrides));
    return evaluateSnapshot({ snapshotDir, manifestPath, snapshotId: caseName });
  } finally {
    cleanup(tmp);
  }
}

describe('dependency-direction reference checker', () => {
  it('does not flag a clean alias import', () => {
    const r = run('clean_alias');
    expect(r.raw_violation_count).toBe(0);
    expect(r.verdict).toBe('CONFORMANT');
  });

  it('detects a violating alias import (core -> infra)', () => {
    const r = run('violating_alias');
    expect(r.raw_violation_count).toBe(1);
    const v = r.findings.find((f) => f.violation);
    expect(v?.rule_id).toBe('AR-DEP-003');
    expect(v?.importer_layer).toBe('core');
    expect(v?.target_layer).toBe('infra');
    expect(v?.evidence_paths[0]).toBe('libs/core/src/index.ts');
    expect(r.verdict).toBe('VIOLATIONS');
  });

  it('does not flag a clean relative import', () => {
    const r = run('clean_relative');
    expect(r.raw_violation_count).toBe(0);
    expect(r.verdict).toBe('CONFORMANT');
  });

  it('detects a violating relative import (alias bypass)', () => {
    const r = run('violating_relative');
    expect(r.raw_violation_count).toBe(1);
    const v = r.findings.find((f) => f.violation);
    expect(v?.evidence_paths[0]).toBe('libs/core/src/bad.ts');
    expect(v?.target_layer).toBe('infra');
  });

  it('does not flag the sanctioned api -> features -> core re-export (clean barrel)', () => {
    const r = run('clean_barrel');
    expect(r.raw_violation_count).toBe(0);
    // The engine must NOT synthesize a direct api -> core edge from the re-export.
    expect(r.findings.some((f) => f.importer_layer === 'api' && f.target_layer === 'core')).toBe(false);
    expect(r.verdict).toBe('CONFORMANT');
  });

  it('detects a forbidden dependency laundered through a barrel export *', () => {
    const r = run('violating_barrel');
    expect(r.raw_violation_count).toBe(1);
    const v = r.findings.find((f) => f.violation);
    expect(v?.evidence_paths[0]).toBe('libs/core/src/index.ts');
    expect(v?.target_layer).toBe('infra');
    // features -> core (importing from the laundering barrel) is allowed, not flagged.
    expect(r.findings.some((f) => f.importer_layer === 'features' && f.violation)).toBe(false);
  });

  it('does not treat import-like text in comments or strings as imports', () => {
    const r = run('deceptive_negative');
    expect(r.raw_violation_count).toBe(0);
    expect(r.verdict).toBe('CONFORMANT');
  });

  it('detects a violation in a moved file (full-repository evaluation)', () => {
    const r = run('moved_violation');
    expect(r.raw_violation_count).toBe(1);
    const v = r.findings.find((f) => f.violation);
    expect(v?.evidence_paths[0]).toBe('libs/core/nested/deep/moved.ts');
    expect(v?.importer_layer).toBe('core');
    expect(v?.target_layer).toBe('infra');
  });

  it('records a deleted opportunity as absent, not as an invented violation', () => {
    const r = run('deleted_violation', {
      opportunities: [
        {
          opportunity_id: 'OPP-DEL',
          rule_id: 'AR-DEP-003',
          locator: { importer_path: 'libs/core/src/removed.ts', scope: 'core', forbidden_target_layers: ['infra'] },
          description: null,
        },
      ],
    });
    expect(r.raw_violation_count).toBe(0);
    expect(r.opportunity_accounting.applicable_opportunity_count).toBe(1);
    expect(r.opportunity_accounting.absent_opportunity_count).toBe(1);
    expect(r.opportunity_accounting.violated_opportunity_count).toBe(0);
    const opp = r.findings.find((f) => f.opportunity_id === 'OPP-DEL');
    expect(opp?.status).toBe('NOT_APPLICABLE');
    expect(r.verdict).toBe('CONFORMANT');
  });

  it('fails closed on a malformed alias configuration', () => {
    expect(() => run('malformed_alias')).toThrow(/MALFORMED_ALIAS_CONFIG/);
  });

  it('does not flag a legitimate alternative solution (specificity)', () => {
    const r = run('legitimate_alternative');
    expect(r.raw_violation_count).toBe(0);
    expect(r.verdict).toBe('CONFORMANT');
  });

  it('accounts a satisfied frozen opportunity separately from raw violations', () => {
    const r = run('clean_alias', {
      opportunities: [
        {
          opportunity_id: 'OPP-OK',
          rule_id: 'AR-DEP-001',
          locator: { importer_path: 'libs/features/src/index.ts', scope: 'features', forbidden_target_layers: [] },
          description: null,
        },
      ],
    });
    expect(r.raw_violation_count).toBe(0);
    expect(r.opportunity_accounting.applicable_opportunity_count).toBe(1);
    expect(r.opportunity_accounting.fixed_opportunity_count).toBe(1);
    const opp = r.findings.find((f) => f.opportunity_id === 'OPP-OK');
    expect(opp?.status).toBe('SATISFIED');
  });

  it('links a violated frozen opportunity to its raw violation finding', () => {
    const r = run('violating_alias', {
      opportunities: [
        {
          opportunity_id: 'OPP-BAD',
          rule_id: 'AR-DEP-001',
          locator: { importer_path: 'libs/core/src/index.ts', scope: 'core', forbidden_target_layers: ['infra'] },
          description: null,
        },
      ],
    });
    expect(r.opportunity_accounting.violated_opportunity_count).toBe(1);
    const v = r.findings.find((f) => f.violation);
    expect(v?.opportunity_id).toBe('OPP-BAD');
  });

  it('detects a forbidden dependency laundered via a backtick dynamic import / require', () => {
    const r = run('dynamic_import_launder');
    expect(r.raw_violation_count).toBe(2);
    const v = r.findings.filter((f) => f.violation);
    expect(v.every((f) => f.importer_layer === 'core' && f.target_layer === 'infra')).toBe(true);
    const snippets = v.map((f) => f.evidence_locations[0]?.snippet ?? '');
    expect(snippets.some((s) => s.includes('dynamic-import'))).toBe(true);
    expect(snippets.some((s) => s.includes('require'))).toBe(true);
    expect(r.verdict).toBe('VIOLATIONS');
  });

  it('keeps the opportunity-accounting invariant when a violation targets a layer the opportunity does not scope', () => {
    // core->infra is the real violation; this opportunity scopes 'observability',
    // so it is not linked to that violation. It must still be accounted (as fixed),
    // never dropped, so applicable == violated + fixed + absent.
    const r = run('violating_alias', {
      opportunities: [
        {
          opportunity_id: 'OPP-OBS',
          rule_id: 'AR-DEP-001',
          locator: { importer_path: 'libs/core/src/index.ts', scope: 'core', forbidden_target_layers: ['observability'] },
          description: null,
        },
      ],
    });
    expect(r.raw_violation_count).toBe(1);
    const acc = r.opportunity_accounting;
    expect(acc.applicable_opportunity_count).toBe(1);
    expect(
      acc.violated_opportunity_count + acc.fixed_opportunity_count + acc.absent_opportunity_count,
    ).toBe(acc.applicable_opportunity_count);
    expect(acc.fixed_opportunity_count).toBe(1);
  });
});
