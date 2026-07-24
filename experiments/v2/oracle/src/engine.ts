/**
 * Architecture-conformance oracle engine (deterministic, blind, fail-closed).
 *
 * evaluateSnapshot scores a complete final repository snapshot against a frozen,
 * externally mounted evaluator manifest. It takes NO condition and NO model
 * parameter, so scoring is blind. It fails closed (throws OracleError) on an
 * evaluator mount inside the worktree, a missing/malformed/unresolved manifest,
 * an unknown rule id, a malformed/missing alias config, or an incomplete scoring
 * pass. Unimplemented rules report UNIMPLEMENTED and never PASS.
 */

import * as crypto from 'crypto';
import * as fs from 'fs';
import * as path from 'path';

import { OracleError } from './errors';
import { LayerMap } from './layers';
import { loadManifest } from './manifest';
import { assertEvaluatorMountOutsideWorktree } from './mountPolicy';
import { ImportGraphResolver, listSourceFiles, parseCompilerOptions } from './resolver';
import { matchAnyGlob } from './glob';
import {
  ArchitectureFinding,
  CheckerContext,
  Finding,
  RuleEvaluated,
  Verdict,
} from './types';
import { descriptorFor, isKnownRule } from './checkers/registry';
import { DEP_FAMILY_RULE_IDS, runDependencyDirection } from './checkers/dependencyDirection';

export const EVALUATOR_NAME = 'afci-arch-oracle';
export const EVALUATOR_VERSION = '0.1.0-dev';
export const FINDING_SCHEMA_VERSION = '1.0.0';

export interface EvaluateOptions {
  /** The coding worktree / final repository snapshot to score (read-only). */
  snapshotDir: string;
  /** Path to the frozen evaluator manifest; MUST be outside snapshotDir. */
  manifestPath: string;
  /** Opaque snapshot identity for the record (carries no condition/model). */
  snapshotId?: string;
  /** Caller-supplied timestamp (kept out of the engine for determinism). */
  scoredAt?: string | null;
}

function sha256File(file: string): string | null {
  try {
    return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
  } catch {
    return null;
  }
}

export function evaluateSnapshot(opts: EvaluateOptions): ArchitectureFinding {
  // 1. Fail closed if the evaluator mount is inside the coding worktree.
  assertEvaluatorMountOutsideWorktree(opts.snapshotDir, opts.manifestPath);

  // 2. Snapshot must exist.
  if (!fs.existsSync(opts.snapshotDir) || !fs.statSync(opts.snapshotDir).isDirectory()) {
    throw new OracleError('MISSING_EVALUATOR_FILE', 'snapshot directory does not exist', opts.snapshotDir);
  }

  // 3. Load + structurally validate the manifest (fail closed on issues).
  const manifest = loadManifest(opts.manifestPath);

  // 4. Every applicable rule id must be known (registered).
  for (const ruleId of manifest.applicable_rule_ids) {
    if (!isKnownRule(ruleId)) {
      throw new OracleError('UNKNOWN_RULE_ID', `applicable rule id '${ruleId}' is not registered`);
    }
  }

  // 5. Frozen layer map + snapshot alias config (fail closed if malformed/missing).
  const layerMap = new LayerMap(manifest.dependency_policy.layers);
  const options = parseCompilerOptions(opts.snapshotDir, manifest.dependency_policy.alias_config_path);

  // 6. Source files (full repository), filtered by the frozen source globs.
  const allFiles = listSourceFiles(opts.snapshotDir);
  const sourceFiles = allFiles.filter((f) => matchAnyGlob(f, manifest.dependency_policy.source_globs));

  // 7. Resolve the import graph (AST + compiler resolution).
  const resolver = new ImportGraphResolver(opts.snapshotDir, options, layerMap);
  const edges = resolver.buildEdges(sourceFiles);

  const ctx: CheckerContext = {
    snapshotDir: opts.snapshotDir,
    manifest,
    edges,
    sourceFiles,
    layerOf: (rel) => layerMap.layerOf(rel),
    fileExists: (rel) => fs.existsSync(path.resolve(opts.snapshotDir, rel)),
  };

  // 8. Evaluate applicable rules.
  const findings: Finding[] = [];
  const rulesEvaluated: RuleEvaluated[] = [];
  const applicable = manifest.applicable_rule_ids;
  const applicableDep = applicable.filter((r) => DEP_FAMILY_RULE_IDS.includes(r));
  // The umbrella rule AR-DEP-001 puts the whole matrix in force: every per-layer
  // clause is then evaluated by the one engine and findings carry the specific
  // clause id.
  const effectiveDep = applicableDep.includes('AR-DEP-001')
    ? DEP_FAMILY_RULE_IDS.slice()
    : applicableDep;

  if (effectiveDep.length > 0) {
    try {
      const result = runDependencyDirection(ctx, effectiveDep);
      findings.push(...result.findings);
      for (const ruleId of effectiveDep) {
        rulesEvaluated.push({
          rule_id: ruleId,
          evaluation_mode: 'automated',
          oracle_implementation_status: 'implemented',
          status: result.status,
        });
      }
    } catch (e) {
      if (e instanceof OracleError) {
        throw e;
      }
      throw new OracleError('INCOMPLETE_SCORING', 'dependency-direction checker failed', String(e));
    }
  }

  // Stub (registered-but-unimplemented) rules: report UNIMPLEMENTED, never PASS.
  for (const ruleId of applicable) {
    if (DEP_FAMILY_RULE_IDS.includes(ruleId)) {
      continue;
    }
    const desc = descriptorFor(ruleId);
    if (!desc) {
      // Unreachable (known-rule check above), but fail closed defensively.
      throw new OracleError('UNKNOWN_RULE_ID', `applicable rule id '${ruleId}' is not registered`);
    }
    rulesEvaluated.push({
      rule_id: ruleId,
      evaluation_mode: desc.evaluation_mode,
      oracle_implementation_status: desc.oracle_implementation_status,
      status: 'unimplemented',
    });
    findings.push({
      finding_id: `${ruleId}::unimplemented`,
      rule_id: ruleId,
      opportunity_id: null,
      violation: false,
      status: 'UNIMPLEMENTED',
      severity: 'n/a',
      evaluation_mode: desc.evaluation_mode,
      automated: desc.evaluation_mode === 'automated',
      confidence: 'manual-required',
      importer_layer: null,
      target_layer: null,
      evidence_paths: [],
      evidence_locations: [],
      resolution_chain: [],
      message: `rule ${ruleId} is not implemented as an oracle checker in this package; it cannot report PASS`,
    });
  }

  // 9. Deterministic ordering.
  findings.sort((a, b) => a.rule_id.localeCompare(b.rule_id) || a.finding_id.localeCompare(b.finding_id));
  rulesEvaluated.sort((a, b) => a.rule_id.localeCompare(b.rule_id));

  // 10. Accounting: raw violations vs frozen opportunities (recorded separately).
  const rawViolationCount = findings.filter((f) => f.violation).length;
  const applicableSet = new Set(applicable);
  const depOpportunities = manifest.opportunities.filter(
    (o) => DEP_FAMILY_RULE_IDS.includes(o.rule_id) && (applicableSet.has(o.rule_id) || applicableSet.has('AR-DEP-001')),
  );
  const violatedOppIds = new Set(findings.filter((f) => f.violation && f.opportunity_id).map((f) => f.opportunity_id));
  const absentOppIds = new Set(
    findings.filter((f) => f.status === 'NOT_APPLICABLE' && f.opportunity_id).map((f) => f.opportunity_id),
  );
  const fixedOppIds = new Set(
    findings.filter((f) => f.status === 'SATISFIED' && f.opportunity_id).map((f) => f.opportunity_id),
  );
  const oppAccounting = {
    applicable_opportunity_count: depOpportunities.length,
    fixed_opportunity_count: depOpportunities.filter((o) => fixedOppIds.has(o.opportunity_id)).length,
    violated_opportunity_count: depOpportunities.filter((o) => violatedOppIds.has(o.opportunity_id)).length,
    absent_opportunity_count: depOpportunities.filter((o) => absentOppIds.has(o.opportunity_id)).length,
  };

  // 11. Verdict.
  const anyUnimplemented = rulesEvaluated.some((r) => r.status === 'unimplemented');
  let verdict: Verdict;
  if (rawViolationCount > 0) {
    verdict = 'VIOLATIONS';
  } else if (anyUnimplemented) {
    verdict = 'PENDING';
  } else {
    verdict = 'CONFORMANT';
  }

  return {
    schema_version: FINDING_SCHEMA_VERSION,
    evaluator: {
      name: EVALUATOR_NAME,
      version: EVALUATOR_VERSION,
      engine: 'typescript-compiler-api',
      alias_aware: true,
      deterministic: true,
    },
    manifest_ref: {
      manifest_id: manifest.manifest_id,
      manifest_version: manifest.manifest_version,
      manifest_sha256: sha256File(opts.manifestPath),
    },
    base_sha: manifest.base_sha,
    snapshot_ref: { id: opts.snapshotId ?? path.basename(path.resolve(opts.snapshotDir)), sha256: null },
    scored_at: opts.scoredAt ?? null,
    rules_evaluated: rulesEvaluated,
    findings,
    raw_violation_count: rawViolationCount,
    opportunity_accounting: oppAccounting,
    deterministic_order: true,
    verdict,
  };
}
