/**
 * Test helpers: materialize a `.ts.fixture` snapshot into an OS temp directory
 * (renaming `*.ts.fixture` -> `*.ts`) and build a frozen evaluator manifest in a
 * sibling `evaluator/` directory OUTSIDE the snapshot, so the mount is legal.
 */

import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';

export const FIXTURES_ROOT = path.resolve(__dirname, '..', 'fixtures');
export const CASES_ROOT = path.resolve(FIXTURES_ROOT, 'cases');

export function makeTmpRoot(): string {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'afci-oracle-'));
}

function copyRename(srcDir: string, destDir: string): void {
  fs.mkdirSync(destDir, { recursive: true });
  for (const e of fs.readdirSync(srcDir, { withFileTypes: true })) {
    const s = path.join(srcDir, e.name);
    if (e.isDirectory()) {
      copyRename(s, path.join(destDir, e.name));
    } else {
      const name = e.name.endsWith('.ts.fixture')
        ? e.name.slice(0, -'.fixture'.length)
        : e.name;
      fs.copyFileSync(s, path.join(destDir, name));
    }
  }
}

/** Materialize `cases/<caseName>/snapshot` into `<tmpRoot>/snapshot`. */
export function materializeSnapshot(tmpRoot: string, caseName: string): string {
  const src = path.join(CASES_ROOT, caseName, 'snapshot');
  const dest = path.join(tmpRoot, 'snapshot');
  copyRename(src, dest);
  return dest;
}

export function cleanup(tmpRoot: string): void {
  fs.rmSync(tmpRoot, { recursive: true, force: true });
}

/**
 * Materialize a snapshot from an in-memory file map (posix relative path ->
 * contents) into `<tmpRoot>/snapshot`. Used by the mutation corpus, where each
 * mutant differs from the base snapshot by a file or two and expressing it as
 * data is clearer (and keeps deliberately-broken code out of the repo tree).
 */
export function writeSnapshot(tmpRoot: string, files: Record<string, string>): string {
  const dest = path.join(tmpRoot, 'snapshot');
  for (const [rel, contents] of Object.entries(files)) {
    const abs = path.join(dest, ...rel.split('/'));
    fs.mkdirSync(path.dirname(abs), { recursive: true });
    fs.writeFileSync(abs, contents, 'utf-8');
  }
  return dest;
}

export interface ManifestOverrides {
  manifest_id?: string;
  manifest_version?: string;
  task_id?: string | null;
  applicable_rule_ids?: string[];
  opportunities?: unknown[];
  status?: string;
  invalidation?: { invalidated: boolean; reason: string | null; superseded_by: string | null };
  answers_populated?: boolean;
  /**
   * Analysis eligibility (suite-classification decision D). Defaults are chosen so
   * the helper always builds a manifest that PASSES the eligibility gates: a
   * manifest with frozen opportunities defaults to `scored` (it has E1 exposure),
   * one without defaults to `functional-only` (zero exposure). Eligibility-failure
   * tests override it explicitly. Pass `null` to omit the field entirely and prove
   * the loader fails closed on a pre-migration manifest.
   */
  e1_analysis_eligibility?: string | null;
}

export function baseDependencyPolicy(): Record<string, unknown> {
  return {
    alias_config_path: 'tsconfig.json',
    source_globs: ['libs/**/*.ts', 'apps/**/*.ts'],
    layers: [
      { id: 'contracts', path_globs: ['libs/contracts/**'] },
      { id: 'core', path_globs: ['libs/core/**'] },
      { id: 'features', path_globs: ['libs/features/**'] },
      { id: 'infra', path_globs: ['libs/infra/**'] },
      { id: 'observability', path_globs: ['libs/observability/**'] },
      { id: 'api', path_globs: ['apps/api/**'] },
    ],
    allowed: {
      contracts: [],
      observability: [],
      core: ['contracts'],
      features: ['core', 'contracts', 'observability'],
      infra: ['contracts', 'observability'],
      api: ['features', 'infra', 'contracts', 'observability'],
    },
  };
}

export function baseManifest(overrides: ManifestOverrides = {}): Record<string, unknown> {
  const opportunities = overrides.opportunities ?? [];
  // Eligibility must be consistent with the frozen opportunity set or the engine
  // fails closed (gates 2 and 4). Default accordingly so existing scoring tests
  // stay valid without restating it.
  const defaultEligibility = opportunities.length > 0 ? 'scored' : 'functional-only';
  const manifest: Record<string, unknown> = {
    schema_version: '1.0.0',
    manifest_id: overrides.manifest_id ?? 'EM-FIXTURE',
    manifest_version: overrides.manifest_version ?? '0.1.0-dev',
    task_id: overrides.task_id ?? null,
    base_sha: '0'.repeat(40),
    // Default to a scorable (frozen, non-invalidated) manifest: these helpers
    // build manifests for SCORING tests. Lifecycle-failure tests override status
    // / invalidation explicitly.
    status: overrides.status ?? 'frozen',
    invalidation: overrides.invalidation ?? { invalidated: false, reason: null, superseded_by: null },
    applicable_rule_ids: overrides.applicable_rule_ids ?? ['AR-DEP-001'],
    e1_analysis_eligibility: overrides.e1_analysis_eligibility ?? defaultEligibility,
    opportunities,
    areas: { required: [], optional: [], prohibited: [] },
    legitimate_alternatives: [],
    manual_rubric_refs: [],
    hidden_test_refs: [],
    checkpoint_ref: null,
    evaluator_hashes: {},
    dependency_policy: baseDependencyPolicy(),
    answers_populated: overrides.answers_populated ?? false,
  };
  // `null` means "omit the field": used to prove the loader fails closed on a
  // manifest authored before the suite-classification decision.
  if (overrides.e1_analysis_eligibility === null) {
    delete manifest.e1_analysis_eligibility;
  }
  return manifest;
}

/** Write a manifest into `<tmpRoot>/<subdir>/manifest.json` and return its path. */
export function writeManifest(
  tmpRoot: string,
  manifest: Record<string, unknown>,
  subdir = 'evaluator',
): string {
  const dir = path.join(tmpRoot, subdir);
  fs.mkdirSync(dir, { recursive: true });
  const p = path.join(dir, 'manifest.json');
  fs.writeFileSync(p, JSON.stringify(manifest, null, 2), 'utf-8');
  return p;
}
