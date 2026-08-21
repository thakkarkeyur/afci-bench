/**
 * Architecture-conformance oracle engine (deterministic, blind, fail-closed).
 *
 * evaluateSnapshot scores a complete final repository snapshot against a frozen,
 * externally mounted evaluator manifest. It takes NO condition and NO model
 * parameter, so scoring is blind. It fails closed (throws OracleError) on an
 * evaluator mount inside the worktree, a missing/malformed/unresolved manifest,
 * a manifest that is not lifecycle-valid for evidentiary use (status not exactly
 * 'frozen', or invalidated, or missing lifecycle fields), a duplicate
 * opportunity_id, an opportunity referencing an unknown/non-applicable/non-scoring
 * rule, an opportunity backed by the AR-DEP-001 umbrella instead of an
 * implemented leaf clause, an opportunity whose frozen scope is malformed or
 * whose rule is not the leaf for its scope -> forbidden-target relationship, two
 * opportunities claiming the same frozen decision, an unknown applicable rule id,
 * a malformed/missing alias config, or an incomplete scoring pass (an opportunity
 * dropped from accounting). Unimplemented rules report UNIMPLEMENTED and never PASS.
 *
 * Frozen opportunities are attributed by ARCHITECTURAL SCOPE, not by an exact
 * historical importer path: see checkers/dependencyDirection.ts.
 *
 * Scoring runs over the PRODUCTION dependency graph only. Test specs, test
 * support material and tooling/build configuration TypeScript are partitioned out
 * before any import edge is built (see productionSource.ts), so a dependency
 * introduced solely for a test or a tool can never violate a production
 * architectural opportunity. The frozen layer scopes are unchanged by that
 * partition, and the E1 denominator remains the frozen manifest opportunity
 * count, so the number of test files in the snapshot moves neither side of E1.
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
import { partitionProductionSources } from './productionSource';
import {
  ApprovedEligibilityIndex,
  ArchitectureFinding,
  CheckerContext,
  Finding,
  RuleEvaluated,
  Verdict,
} from './types';
import { descriptorFor, isKnownRule } from './checkers/registry';
import { DEP_FAMILY_RULE_IDS, runDependencyDirection } from './checkers/dependencyDirection';
import {
  EligibilityOptions,
  assertEligibilityConsistent,
  assertManifestScorable,
  assertOpportunityAccountingComplete,
  assertOpportunityRulesValid,
} from './manifestIntegrity';

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
  /**
   * Approved public eligibility per task id, read from
   * experiments/v2/tasks/public/TASK_INDEX.csv. REQUIRED whenever the manifest
   * binds a real task id — the engine fails closed rather than trusting a
   * manifest's self-declared classification.
   */
  approvedEligibility?: ApprovedEligibilityIndex;
  /**
   * A separately recorded pre-run decision activating an inactive reserve. Absent
   * by default, so an `inactive-reserve` manifest is refused.
   */
  reserveActivation?: EligibilityOptions['reserveActivation'];
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

  // 3. Load + structurally validate the manifest (fail closed on issues:
  //    malformed JSON, unresolved id/version, missing lifecycle fields, and
  //    duplicate opportunity_id values are all rejected by the loader).
  const manifest = loadManifest(opts.manifestPath);

  // 3b. Lifecycle gate (P1-3): score ONLY a frozen, non-invalidated manifest.
  assertManifestScorable(manifest);

  // 4. Every applicable rule id must be known (registered).
  for (const ruleId of manifest.applicable_rule_ids) {
    if (!isKnownRule(ruleId)) {
      throw new OracleError('UNKNOWN_RULE_ID', `applicable rule id '${ruleId}' is not registered`);
    }
  }

  // 4b. Every frozen opportunity must reference a rule that is known, in force,
  //     and scored by the active checker (P1-2). This is what stops an
  //     opportunity from being silently dropped from accounting below.
  assertOpportunityRulesValid(manifest);

  // 4c. Analysis-eligibility gates (suite-classification decision D). The
  //     manifest's declared e1_analysis_eligibility must agree with the approved
  //     public task index and with its own frozen opportunity set, so a
  //     functional-only task can never acquire an E1 denominator, an inactive
  //     reserve can never enter an E1 run without a recorded activation, and a
  //     scored task can never be entered with zero exposure.
  assertEligibilityConsistent(manifest, {
    approvedEligibility: opts.approvedEligibility,
    reserveActivation: opts.reserveActivation,
  });

  // 5. Frozen layer map + snapshot alias config (fail closed if malformed/missing).
  const layerMap = new LayerMap(manifest.dependency_policy.layers);
  const options = parseCompilerOptions(opts.snapshotDir, manifest.dependency_policy.alias_config_path);

  // 6. Source files (full repository), filtered by the frozen source globs, then
  //    partitioned into the PRODUCTION dependency graph and the excluded
  //    test/config/support graph. E1 measures production architectural
  //    dependencies, so a dependency written only to wire up a test or a tool
  //    must not be able to violate a production opportunity. The partition
  //    happens BEFORE any edge is built and leaves the frozen layer scopes
  //    untouched; the denominator stays the frozen opportunity count, so adding
  //    or deleting test files cannot move either side of the rate.
  const allFiles = listSourceFiles(opts.snapshotDir);
  const scannedFiles = allFiles.filter((f) => matchAnyGlob(f, manifest.dependency_policy.source_globs));
  const partition = partitionProductionSources(
    scannedFiles,
    manifest.dependency_policy.production_source_policy,
  );
  const sourceFiles = partition.production;
  const excludedSourceFiles = partition.excluded.slice().sort();

  // 7. Resolve the import graph (AST + compiler resolution) over PRODUCTION
  //    source only. Excluded files are never read for edges, so no excluded edge
  //    can reach a finding, the raw series, or the opportunity accounting.
  const resolver = new ImportGraphResolver(opts.snapshotDir, options, layerMap);
  const edges = resolver.buildEdges(sourceFiles);

  const ctx: CheckerContext = {
    snapshotDir: opts.snapshotDir,
    manifest,
    edges,
    sourceFiles,
    nonProductionSourceFiles: excludedSourceFiles,
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

  // 10b. Reconcile the accounting (fail closed rather than under-count). The two
  // invariants and the reasoning behind them live with the unit that owns them,
  // manifestIntegrity.assertOpportunityAccountingComplete: no frozen opportunity
  // may be dropped by the dep-family filter, and each must be bucketed exactly
  // once. Both branches are defensive — the loader's DUPLICATE_OPPORTUNITY_ID
  // check and assertOpportunityRulesValid refuse first — which is why the guard is
  // a separately callable unit with its own direct tests rather than inline code
  // nothing can exercise.
  assertOpportunityAccountingComplete(
    depOpportunities.length,
    manifest.opportunities.length,
    oppAccounting,
  );

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
      // Lifecycle provenance (P1-3). A scored finding is only ever produced from
      // a frozen, non-invalidated manifest; recorded so a consumer can confirm it.
      status: manifest.status,
      invalidated: manifest.invalidation.invalidated,
    },
    base_sha: manifest.base_sha,
    snapshot_ref: { id: opts.snapshotId ?? path.basename(path.resolve(opts.snapshotDir)), sha256: null },
    scored_at: opts.scoredAt ?? null,
    rules_evaluated: rulesEvaluated,
    findings,
    raw_violation_count: rawViolationCount,
    opportunity_accounting: oppAccounting,
    // Descriptive provenance of the production/test partition. Records which
    // files were held out of the E1 dependency graph so the exclusion is
    // auditable per result; it is NEVER an E1 numerator or denominator.
    production_source: {
      policy_id: manifest.dependency_policy.production_source_policy.policy_id,
      production_file_count: sourceFiles.length,
      excluded_file_count: excludedSourceFiles.length,
      excluded_paths: excludedSourceFiles,
    },
    deterministic_order: true,
    verdict,
  };
}
