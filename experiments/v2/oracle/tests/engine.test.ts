/**
 * Engine-level validation: unknown rules fail closed; unimplemented stubs never
 * PASS; scoring is deterministic and blind to condition/model labels; manifest
 * problems fail closed.
 */

import * as fs from 'fs';
import * as path from 'path';

import { evaluateSnapshot } from '../src';
import {
  baseManifest,
  cleanup,
  makeTmpRoot,
  materializeSnapshot,
  writeManifest,
} from './helpers';

describe('oracle engine', () => {
  it('fails closed on an unknown (unregistered) rule id', () => {
    const tmp = makeTmpRoot();
    try {
      const snapshotDir = materializeSnapshot(tmp, 'clean_alias');
      const manifestPath = writeManifest(
        tmp,
        baseManifest({ applicable_rule_ids: ['AR-DEP-001', 'AR-DOES-NOT-EXIST'] }),
      );
      expect(() => evaluateSnapshot({ snapshotDir, manifestPath })).toThrow(/UNKNOWN_RULE_ID/);
    } finally {
      cleanup(tmp);
    }
  });

  it('reports a registered-but-unimplemented rule as UNIMPLEMENTED and never PASS', () => {
    const tmp = makeTmpRoot();
    try {
      const snapshotDir = materializeSnapshot(tmp, 'clean_alias');
      const manifestPath = writeManifest(
        tmp,
        baseManifest({ applicable_rule_ids: ['AR-DEP-001', 'AR-CONTRACT-001'] }),
      );
      const r = evaluateSnapshot({ snapshotDir, manifestPath });
      const stub = r.rules_evaluated.find((x) => x.rule_id === 'AR-CONTRACT-001');
      expect(stub?.status).toBe('unimplemented');
      const stubFinding = r.findings.find((f) => f.rule_id === 'AR-CONTRACT-001');
      expect(stubFinding?.status).toBe('UNIMPLEMENTED');
      expect(stubFinding?.violation).toBe(false);
      // A clean snapshot with an unimplemented applicable rule must NOT be CONFORMANT.
      expect(r.verdict).toBe('PENDING');
    } finally {
      cleanup(tmp);
    }
  });

  it('produces deterministic (byte-identical) output across runs', () => {
    const runOnce = (): string => {
      const tmp = makeTmpRoot();
      try {
        const snapshotDir = materializeSnapshot(tmp, 'violating_barrel');
        const manifestPath = writeManifest(tmp, baseManifest());
        const r = evaluateSnapshot({ snapshotDir, manifestPath, snapshotId: 'violating_barrel', scoredAt: null });
        return JSON.stringify(r);
      } finally {
        cleanup(tmp);
      }
    };
    expect(runOnce()).toEqual(runOnce());
  });

  it('is blind to condition/model labels added to the snapshot', () => {
    const tmp = makeTmpRoot();
    try {
      const snapshotDir = materializeSnapshot(tmp, 'violating_alias');
      const manifestPath = writeManifest(tmp, baseManifest());
      const before = evaluateSnapshot({ snapshotDir, manifestPath, snapshotId: 'x' });

      // Inject a condition/model marker file; it must not change the findings.
      fs.writeFileSync(
        path.join(snapshotDir, 'libs', 'core', 'src', '_afci_meta.ts'),
        "// MODEL=claude-opus-4-8 CONDITION=C4\nexport const meta = 'x';\n",
        'utf-8',
      );
      const after = evaluateSnapshot({ snapshotDir, manifestPath, snapshotId: 'x' });

      expect(after.findings).toEqual(before.findings);
      expect(after.raw_violation_count).toBe(before.raw_violation_count);
      // The record carries no condition/model field at all.
      const json = JSON.stringify(after);
      expect(json.includes('"condition"')).toBe(false);
      expect(json.includes('"model"')).toBe(false);
      expect(json.includes('C4')).toBe(false);
    } finally {
      cleanup(tmp);
    }
  });

  it('fails closed on a missing manifest', () => {
    const tmp = makeTmpRoot();
    try {
      const snapshotDir = materializeSnapshot(tmp, 'clean_alias');
      const manifestPath = path.join(tmp, 'evaluator', 'does_not_exist.json');
      expect(() => evaluateSnapshot({ snapshotDir, manifestPath })).toThrow(/MANIFEST_MISSING/);
    } finally {
      cleanup(tmp);
    }
  });

  it('fails closed on an unresolved manifest version', () => {
    const tmp = makeTmpRoot();
    try {
      const snapshotDir = materializeSnapshot(tmp, 'clean_alias');
      const manifestPath = writeManifest(tmp, baseManifest({ manifest_version: 'unresolved' }));
      expect(() => evaluateSnapshot({ snapshotDir, manifestPath })).toThrow(/MANIFEST_VERSION_UNRESOLVED/);
    } finally {
      cleanup(tmp);
    }
  });

  it('records evaluator provenance without any condition/model identity', () => {
    const tmp = makeTmpRoot();
    try {
      const snapshotDir = materializeSnapshot(tmp, 'clean_alias');
      const manifestPath = writeManifest(tmp, baseManifest());
      const r = evaluateSnapshot({ snapshotDir, manifestPath, snapshotId: 'clean_alias' });
      expect(r.evaluator.name).toBe('afci-arch-oracle');
      expect(r.evaluator.deterministic).toBe(true);
      expect(r.evaluator.alias_aware).toBe(true);
      expect(r.manifest_ref.manifest_sha256).toMatch(/^[0-9a-f]{64}$/);
      expect(Object.keys(r)).not.toContain('condition');
      expect(Object.keys(r)).not.toContain('model');
    } finally {
      cleanup(tmp);
    }
  });
});
