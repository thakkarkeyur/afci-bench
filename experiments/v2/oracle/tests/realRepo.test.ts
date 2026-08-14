/**
 * Real-repository self-scan (dogfood). Copies the actual repository source
 * (libs, apps, tsconfig.base.json) into a temp snapshot and scores it with the
 * committed evaluator-manifest template. Makes the "the real repository is
 * CONFORMANT and the sanctioned api->features->core re-export is not false-
 * flagged" claim reproducible from committed artifacts (not just a manual run).
 *
 * The manifest is copied to a sibling dir OUTSIDE the snapshot, so the mount is
 * legal; the real source is never modified.
 */

import * as fs from 'fs';
import * as path from 'path';

import { evaluateSnapshot } from '../src';
import { makeTmpRoot, cleanup } from './helpers';

// experiments/v2/oracle/tests -> repo root
const REPO_ROOT = path.resolve(__dirname, '..', '..', '..', '..');
const TEMPLATE_MANIFEST = path.join(
  REPO_ROOT,
  'experiments',
  'v2',
  'manifests',
  'evaluator_manifest.template.json',
);

function copyTree(src: string, dest: string): void {
  fs.mkdirSync(dest, { recursive: true });
  for (const e of fs.readdirSync(src, { withFileTypes: true })) {
    if (e.name === 'node_modules' || e.name === '.git') continue;
    const s = path.join(src, e.name);
    const d = path.join(dest, e.name);
    if (e.isDirectory()) copyTree(s, d);
    else if (e.isFile()) fs.copyFileSync(s, d);
  }
}

describe('real repository self-scan (dogfood)', () => {
  it('scores the real repository source as CONFORMANT with no api->core false positive', () => {
    const tmp = makeTmpRoot();
    try {
      const snapshotDir = path.join(tmp, 'snapshot');
      fs.mkdirSync(snapshotDir, { recursive: true });
      copyTree(path.join(REPO_ROOT, 'libs'), path.join(snapshotDir, 'libs'));
      copyTree(path.join(REPO_ROOT, 'apps'), path.join(snapshotDir, 'apps'));
      fs.copyFileSync(
        path.join(REPO_ROOT, 'tsconfig.base.json'),
        path.join(snapshotDir, 'tsconfig.base.json'),
      );

      // Mount a FROZEN synthetic manifest OUTSIDE the snapshot. The committed
      // template is intentionally status:"template" (and now correctly fails
      // closed for scoring), so we promote a copy of it to a scorable frozen,
      // non-invalidated manifest without touching the committed file.
      const evalDir = path.join(tmp, 'evaluator');
      fs.mkdirSync(evalDir, { recursive: true });
      const manifestPath = path.join(evalDir, 'manifest.json');
      const frozen = JSON.parse(fs.readFileSync(TEMPLATE_MANIFEST, 'utf-8'));
      frozen.manifest_id = 'EM-REALREPO-FROZEN';
      frozen.manifest_version = '0.1.0-dev';
      frozen.status = 'frozen';
      frozen.invalidation = { invalidated: false, reason: null, superseded_by: null };
      fs.writeFileSync(manifestPath, JSON.stringify(frozen, null, 2), 'utf-8');

      const r = evaluateSnapshot({ snapshotDir, manifestPath, snapshotId: 'real-repo' });

      expect(r.verdict).toBe('CONFORMANT');
      expect(r.raw_violation_count).toBe(0);
      // The sanctioned api imports Order from features (which re-exports core):
      // it must NOT be reported as a direct api->core dependency.
      expect(r.findings.some((f) => f.importer_layer === 'api' && f.target_layer === 'core')).toBe(false);
      // Sanity: the whole dependency-direction family was evaluated over real source.
      expect(r.rules_evaluated.map((x) => x.rule_id)).toEqual([
        'AR-DEP-001',
        'AR-DEP-002',
        'AR-DEP-003',
        'AR-DEP-004',
        'AR-DEP-005',
        'AR-DEP-006',
      ]);

      // The REAL substrate's test and tooling TypeScript sits inside the frozen
      // architectural scopes (apps/api/jest.config.ts is layer `api`;
      // libs/features/src/features.spec.ts is layer `features`), so the production
      // partition has to hold it out or a test-only dependency could violate a
      // production opportunity. Assert against the actual repository, not a
      // synthetic snapshot.
      expect(r.production_source.policy_id).toBe('PSP-V1');
      const excluded = r.production_source.excluded_paths;
      expect(excluded.length).toBeGreaterThan(0);
      expect(excluded).toContain('apps/api/jest.config.ts');
      expect(excluded).toContain('apps/api/src/app.spec.ts');
      expect(excluded).toContain('libs/core/src/core.spec.ts');
      expect(excluded).toContain('libs/features/src/features.spec.ts');
      // Every excluded path really is a spec or a tooling config ...
      for (const rel of excluded) {
        expect(/\.spec\.tsx?$|\.test\.tsx?$|(^|\/)jest\.config\.ts$/.test(rel)).toBe(true);
      }
      // ... and no production module was swept up with them.
      expect(excluded).not.toContain('apps/api/src/app.ts');
      expect(excluded).not.toContain('libs/features/src/index.ts');
      expect(r.production_source.production_file_count).toBeGreaterThan(0);
      expect(r.production_source.excluded_file_count).toBe(excluded.length);
    } finally {
      cleanup(tmp);
    }
  });
});
