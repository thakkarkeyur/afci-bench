/**
 * PRODUCTION-SOURCE POLICY — which scanned TypeScript may contribute a
 * dependency edge to the E1 production dependency graph.
 *
 * The frozen `dependency_policy.source_globs` (all TypeScript under `apps` and
 * `libs`) and the frozen layer path globs (`apps/api/**`, `libs/features/**`, …)
 * both match test and tooling TypeScript that happens to sit inside an
 * architectural scope — `apps/api/src/app.spec.ts` is assigned layer `api`, and
 * each lib's `jest.config.ts` is assigned that lib's layer. Before this policy
 * existed, a dependency written ONLY to wire up a test could therefore violate a
 * production architectural opportunity, which is not what E1 claims to measure.
 *
 * E1 measures PRODUCTION architectural dependencies. This module partitions the
 * scanned source into two disjoint graphs:
 *
 *   - the PRODUCTION dependency graph — the only graph the dependency-direction
 *     checker builds edges over, and therefore the only graph that can reach
 *     E1's numerator;
 *   - the EXCLUDED test/config/support graph — recorded descriptively (the
 *     finding lists exactly which paths were excluded, so the partition is
 *     auditable per result) and never scored.
 *
 * THE FROZEN ARCHITECTURAL LAYER SCOPES ARE NOT TOUCHED. The partition happens at
 * source selection, before any edge is built, so no layer path glob and no frozen
 * opportunity locator moves. The E1 denominator stays the frozen manifest
 * opportunity count, so adding or deleting test files cannot change either side
 * of the rate.
 *
 * WHY EXPLICIT LISTS RATHER THAN SUBSTRING CHECKS. Classification is by exact
 * basename (tooling config), by basename-only glob (test specs), and by exact
 * path-segment name (test-support directories). Three consequences matter:
 *
 *   - `*.config.ts` is deliberately NOT a wildcard. `app.config.ts` is genuine
 *     production source in common frameworks, so tooling config is named
 *     exhaustively instead.
 *   - Production source is never excluded because its name incidentally contains
 *     a word like "test": `latest.ts`, `contest.ts`, `testUtils.ts` and
 *     `libs/core/src/protest/index.ts` are all production. `*.test.ts` requires a
 *     literal `.` before `test`, and directory matching is on the WHOLE segment.
 *   - Nothing depends on the glob engine's `**` semantics, so an over-greedy
 *     pattern cannot silently swallow a production file.
 *
 * A manifest may EXTEND the baseline through `dependency_policy.production_source_policy`.
 * The extension is ADDITIVE ONLY: a manifest can declare further test/config
 * material, never re-admit an excluded class, so the P0 this module fixes cannot
 * be reintroduced by editing a manifest.
 */

import { OracleError } from './errors';
import { matchAnyGlob } from './glob';

/** Identity of the baseline policy, recorded on every finding. */
export const BASELINE_PRODUCTION_SOURCE_POLICY_ID = 'PSP-V1';

/**
 * How a scanned source file is classified. Only `production` contributes edges
 * to the E1 dependency graph; the other three are the excluded
 * test/config/support graph.
 */
export type SourceClass = 'production' | 'test-spec' | 'test-support' | 'tool-config';

export interface ProductionSourcePolicy {
  policy_id: string;
  /**
   * Exact file basenames that are build/test TOOLING configuration, never
   * production architecture. Exhaustive by design (see the header note on
   * `*.config.ts`).
   */
  excluded_config_basenames: string[];
  /**
   * Globs matched against the BASENAME ONLY (a basename contains no separator,
   * so `*` here is unambiguous). These mark test specs.
   */
  excluded_spec_basename_globs: string[];
  /**
   * Exact path-SEGMENT names whose entire subtree is test-only support material.
   * Matched whole-segment, so `protest/` is not `test/`.
   */
  excluded_directory_names: string[];
}

/**
 * The baseline, always in force. Every entry is a conventional test/tooling
 * designation whose only purpose is testing or build configuration.
 *
 * Deliberately NOT excluded, and recorded so the omission is a decision rather
 * than an oversight:
 *   - `testing/` — an Nx/Angular library may publish a `testing/` entry point,
 *     but `testing` is also an ordinary production word; whole-subtree exclusion
 *     on it would risk dropping production source. Use the additive manifest
 *     extension if a specific repository needs it.
 *   - `*.config.ts` as a wildcard — see the header note.
 */
export const BASELINE_PRODUCTION_SOURCE_POLICY: ProductionSourcePolicy = {
  policy_id: BASELINE_PRODUCTION_SOURCE_POLICY_ID,
  excluded_config_basenames: [
    'babel.config.ts',
    'cypress.config.ts',
    'eslint.config.ts',
    'jest.config.ts',
    'jest.preset.ts',
    'jest.setup.ts',
    'karma.conf.ts',
    'playwright.config.ts',
    'rollup.config.ts',
    'vite.config.ts',
    'vitest.config.ts',
    'webpack.config.ts',
  ],
  excluded_spec_basename_globs: ['*.spec.ts', '*.spec.tsx', '*.test.ts', '*.test.tsx'],
  excluded_directory_names: [
    '__fixtures__',
    '__mocks__',
    '__tests__',
    'test-fixtures',
    'test-helpers',
    'test-utils',
  ],
};

function basenameOf(relPath: string): string {
  const segments = relPath.split('/');
  return segments[segments.length - 1];
}

/**
 * Classify one posix repo-relative source path. Deterministic and total: the
 * checks run in a fixed order (tooling config, then test spec, then test-support
 * directory) and anything left is production.
 */
export function classifySourceFile(
  relPath: string,
  policy: ProductionSourcePolicy = BASELINE_PRODUCTION_SOURCE_POLICY,
): SourceClass {
  const basename = basenameOf(relPath);
  if (policy.excluded_config_basenames.includes(basename)) {
    return 'tool-config';
  }
  if (matchAnyGlob(basename, policy.excluded_spec_basename_globs)) {
    return 'test-spec';
  }
  const directorySegments = relPath.split('/').slice(0, -1);
  if (directorySegments.some((segment) => policy.excluded_directory_names.includes(segment))) {
    return 'test-support';
  }
  return 'production';
}

/** True when the path may contribute a dependency edge to the E1 graph. */
export function isProductionSource(
  relPath: string,
  policy: ProductionSourcePolicy = BASELINE_PRODUCTION_SOURCE_POLICY,
): boolean {
  return classifySourceFile(relPath, policy) === 'production';
}

export interface SourcePartition {
  /** Scored: the production dependency graph's file set (input order preserved). */
  production: string[];
  /** Descriptive only: the excluded test/config/support graph's file set. */
  excluded: string[];
}

/** Split an already-source-glob-filtered file list into the two graphs. */
export function partitionProductionSources(
  sourceFiles: string[],
  policy: ProductionSourcePolicy = BASELINE_PRODUCTION_SOURCE_POLICY,
): SourcePartition {
  const production: string[] = [];
  const excluded: string[] = [];
  for (const rel of sourceFiles) {
    (isProductionSource(rel, policy) ? production : excluded).push(rel);
  }
  return { production, excluded };
}

function readAdditions(raw: Record<string, unknown>, field: string, allowGlob: boolean): string[] {
  const value = raw[field];
  if (value === undefined || value === null) {
    return [];
  }
  if (!Array.isArray(value) || value.some((x) => typeof x !== 'string')) {
    throw new OracleError(
      'INVALID_PRODUCTION_SOURCE_POLICY',
      `dependency_policy.production_source_policy.${field} must be an array of strings`,
    );
  }
  const entries = value as string[];
  for (const entry of entries) {
    if (entry.length === 0) {
      throw new OracleError(
        'INVALID_PRODUCTION_SOURCE_POLICY',
        `dependency_policy.production_source_policy.${field} contains an empty entry`,
      );
    }
    // Every list is matched against a single basename or a single path segment.
    // An entry carrying a separator could never match, so it would silently
    // widen nothing — refuse it rather than accept a dead exclusion.
    if (entry.includes('/')) {
      throw new OracleError(
        'INVALID_PRODUCTION_SOURCE_POLICY',
        `dependency_policy.production_source_policy.${field} entries are basenames or path segments and must not contain '/'`,
        entry,
      );
    }
    if (!allowGlob && (entry.includes('*') || entry.includes('?'))) {
      throw new OracleError(
        'INVALID_PRODUCTION_SOURCE_POLICY',
        `dependency_policy.production_source_policy.${field} entries are exact names and must not contain a glob wildcard`,
        entry,
      );
    }
  }
  return entries;
}

function mergeSorted(baseline: string[], additions: string[]): string[] {
  return Array.from(new Set([...baseline, ...additions])).sort();
}

/**
 * Resolve the effective policy for a manifest. The baseline ALWAYS applies; a
 * manifest may only add to it. Fails closed on a malformed declaration rather
 * than falling back to the baseline, so a typo cannot silently weaken scoring.
 */
export function resolveProductionSourcePolicy(raw: unknown): ProductionSourcePolicy {
  if (raw === undefined || raw === null) {
    return BASELINE_PRODUCTION_SOURCE_POLICY;
  }
  if (typeof raw !== 'object' || Array.isArray(raw)) {
    throw new OracleError(
      'INVALID_PRODUCTION_SOURCE_POLICY',
      'dependency_policy.production_source_policy must be an object when present',
    );
  }
  const declared = raw as Record<string, unknown>;
  const policyId = declared.policy_id;
  if (policyId !== undefined && (typeof policyId !== 'string' || policyId.trim().length === 0)) {
    throw new OracleError(
      'INVALID_PRODUCTION_SOURCE_POLICY',
      'dependency_policy.production_source_policy.policy_id must be a non-empty string when present',
    );
  }
  const configAdditions = readAdditions(declared, 'additional_excluded_config_basenames', false);
  const specAdditions = readAdditions(declared, 'additional_excluded_spec_basename_globs', true);
  const directoryAdditions = readAdditions(declared, 'additional_excluded_directory_names', false);

  const base = BASELINE_PRODUCTION_SOURCE_POLICY;
  const extended =
    configAdditions.length + specAdditions.length + directoryAdditions.length > 0;
  return {
    // The recorded id always identifies the baseline it extends, so a finding can
    // never claim a policy weaker than PSP-V1.
    policy_id: extended
      ? `${BASELINE_PRODUCTION_SOURCE_POLICY_ID}+${(policyId as string | undefined) ?? 'manifest-extension'}`
      : BASELINE_PRODUCTION_SOURCE_POLICY_ID,
    excluded_config_basenames: mergeSorted(base.excluded_config_basenames, configAdditions),
    excluded_spec_basename_globs: mergeSorted(base.excluded_spec_basename_globs, specAdditions),
    excluded_directory_names: mergeSorted(base.excluded_directory_names, directoryAdditions),
  };
}
