/**
 * Shared types for the architecture-conformance oracle. The finding shapes mirror
 * experiments/v2/schemas/architecture_finding.schema.json. None carries a
 * condition or model identity: scoring is blind (docs/v2/HIDDEN_EVALUATOR_BOUNDARY.md).
 */

import { ProductionSourcePolicy } from './productionSource';

export type Severity = 'blocker' | 'major' | 'minor' | 'n/a';
export type EvaluationMode = 'automated' | 'manual';
export type OracleImplementationStatus = 'implemented' | 'partial' | 'stub' | 'not-implemented';
export type FindingStatus =
  | 'VIOLATION'
  | 'SATISFIED'
  | 'NOT_APPLICABLE'
  | 'UNIMPLEMENTED'
  | 'ERROR';
export type Confidence = 'certain' | 'heuristic' | 'manual-required';
export type Verdict = 'CONFORMANT' | 'VIOLATIONS' | 'PENDING' | 'FAIL_CLOSED';

export interface EvidenceLocation {
  path: string;
  line: number;
  column: number;
  snippet: string | null;
}

export interface Finding {
  finding_id: string;
  rule_id: string;
  opportunity_id: string | null;
  violation: boolean;
  status: FindingStatus;
  severity: Severity;
  evaluation_mode: EvaluationMode;
  automated: boolean;
  confidence: Confidence;
  importer_layer: string | null;
  target_layer: string | null;
  evidence_paths: string[];
  evidence_locations: EvidenceLocation[];
  resolution_chain: string[];
  message: string;
}

export interface RuleEvaluated {
  rule_id: string;
  evaluation_mode: EvaluationMode;
  oracle_implementation_status: OracleImplementationStatus;
  status: 'evaluated' | 'unimplemented' | 'error';
}

export interface OpportunityAccounting {
  applicable_opportunity_count: number;
  fixed_opportunity_count: number;
  violated_opportunity_count: number;
  absent_opportunity_count: number;
}

/**
 * Provenance of the production/test partition for one scored snapshot. Purely
 * descriptive: it records WHICH files were held out of the E1 dependency graph so
 * the partition is auditable per result. Nothing here is an E1 numerator or
 * denominator — the denominator remains the frozen manifest opportunity count.
 */
export interface ProductionSourceAccounting {
  policy_id: string;
  production_file_count: number;
  excluded_file_count: number;
  /** Sorted posix paths held out of the production graph (test/config/support). */
  excluded_paths: string[];
}

export interface ArchitectureFinding {
  schema_version: string;
  evaluator: {
    name: string;
    version: string;
    engine: 'typescript-compiler-api' | 'ast' | 'other';
    alias_aware: boolean;
    deterministic: boolean;
  };
  manifest_ref: {
    manifest_id: string;
    manifest_version: string;
    manifest_sha256: string | null;
    /** Lifecycle provenance: a scored finding is only ever produced from a frozen manifest. */
    status: string;
    /** Invalidation provenance: always false for a scored finding (invalidated manifests fail closed). */
    invalidated: boolean;
  };
  base_sha: string;
  snapshot_ref: { id: string; sha256: string | null };
  scored_at: string | null;
  rules_evaluated: RuleEvaluated[];
  findings: Finding[];
  raw_violation_count: number;
  opportunity_accounting: OpportunityAccounting;
  production_source: ProductionSourceAccounting;
  deterministic_order: boolean;
  verdict: Verdict;
}

// ------------------------------------------------------------------------- //
// Evaluator manifest (mirrors evaluator_manifest.schema.json; the subset the
// engine consumes).
// ------------------------------------------------------------------------- //
export interface OpportunityLocator {
  /**
   * PROVENANCE ONLY — the file the opportunity was authored against. It is
   * recorded as authoring evidence and is NEVER the scoring anchor: deleting,
   * renaming, or moving it cannot change how the opportunity scores.
   */
  importer_path: string | null;
  /**
   * SCORING ANCHOR — the frozen architectural scope, given as the `id` of a layer
   * in `dependency_policy.layers`. The opportunity is evaluated over every source
   * file the frozen layer path globs assign to this layer, wherever the model put
   * its implementation.
   */
  scope: string | null;
  /**
   * SCORING ANCHOR — the target layers this one frozen decision forbids. Required
   * and non-empty for a dependency opportunity; every entry must be a known layer
   * that the frozen allowed-dependency matrix actually forbids for `scope`.
   */
  forbidden_target_layers?: string[];
}

export interface Opportunity {
  opportunity_id: string;
  rule_id: string;
  locator: OpportunityLocator;
  description?: string | null;
}

export interface LayerDef {
  id: string;
  path_globs: string[];
}

export interface DependencyPolicy {
  alias_config_path: string;
  source_globs: string[];
  layers: LayerDef[];
  allowed: Record<string, string[]>;
  /**
   * The EFFECTIVE production-source policy (baseline PSP-V1, plus any additive
   * manifest extension). Files it classifies as test/config/support are removed
   * before the import graph is built, so they contribute no edge to E1. See
   * productionSource.ts; the frozen layer scopes are unaffected.
   */
  production_source_policy: ProductionSourcePolicy;
}

/**
 * Analysis eligibility for the primary endpoint E1 (suite-classification decision D).
 * Mirrors the `e1_analysis_eligibility` column of the approved public task index.
 */
export type E1AnalysisEligibility = 'scored' | 'functional-only' | 'inactive-reserve';

export const E1_ANALYSIS_ELIGIBILITIES: readonly E1AnalysisEligibility[] = [
  'scored',
  'functional-only',
  'inactive-reserve',
];

/** Approved public eligibility per task id, used to bind a manifest to the index. */
export type ApprovedEligibilityIndex = Record<string, E1AnalysisEligibility>;

export interface EvaluatorManifest {
  schema_version: string;
  manifest_id: string;
  manifest_version: string;
  task_id: string | null;
  base_sha: string;
  status: 'template' | 'draft' | 'review' | 'frozen' | 'deprecated';
  invalidation: { invalidated: boolean; reason: string | null; superseded_by: string | null };
  applicable_rule_ids: string[];
  /**
   * REQUIRED. Binds the manifest to the approved public classification. The engine
   * fails closed on any inconsistency between this value, the approved index, and
   * the frozen opportunity set (see manifestIntegrity.assertEligibilityConsistent).
   */
  e1_analysis_eligibility: E1AnalysisEligibility;
  opportunities: Opportunity[];
  areas: { required: string[]; optional: string[]; prohibited: string[] };
  legitimate_alternatives: Array<{ id: string; ref: string; description?: string | null }>;
  manual_rubric_refs: string[];
  hidden_test_refs: string[];
  checkpoint_ref: string | null;
  evaluator_hashes: Record<string, string>;
  dependency_policy: DependencyPolicy;
  answers_populated: boolean;
}

// ------------------------------------------------------------------------- //
// Import graph (produced by the resolver, consumed by checkers).
// ------------------------------------------------------------------------- //
export type EdgeKind = 'import' | 'export-from' | 'require' | 'dynamic-import';

export interface ImportEdge {
  /** Source file, posix path relative to the snapshot root. */
  importer_path: string;
  /** Layer id of the importer, or null if the importer is not a governed layer. */
  importer_layer: string | null;
  /** The raw module specifier as written. */
  specifier: string;
  kind: EdgeKind;
  type_only: boolean;
  line: number;
  column: number;
  /** Resolved target file (posix, relative to snapshot root) or null if internal-unresolved/external. */
  target_path: string | null;
  /** Layer id of the target, or null when the target is third-party/ungoverned. */
  target_layer: string | null;
  /** True when the specifier is internal (alias or relative) but did not resolve to a file. */
  internal_unresolved: boolean;
  /** Human-readable resolution steps for evidence. */
  resolution_chain: string[];
}

export interface CheckerContext {
  snapshotDir: string;
  manifest: EvaluatorManifest;
  edges: ImportEdge[];
  /**
   * Posix relative paths of every PRODUCTION source file. This is the scored
   * set: the import graph is built from it, and a frozen scope is "live" only if
   * it carries a file here. Test/config/support files are NOT in this list.
   */
  sourceFiles: string[];
  /**
   * Posix relative paths held out of the production graph (test specs, test
   * support material, tooling config). Descriptive only — a checker may examine
   * them for diagnostics, but nothing derived from them may enter E1.
   */
  nonProductionSourceFiles: string[];
  /** Layer id lookup for an arbitrary posix relative path (or null). */
  layerOf: (relPath: string) => string | null;
  /** True when a posix relative path exists in the snapshot. */
  fileExists: (relPath: string) => boolean;
}

export interface CheckerResult {
  findings: Finding[];
  /** How the rule's evaluation concluded (evaluated for a real checker). */
  status: 'evaluated' | 'unimplemented' | 'error';
}
