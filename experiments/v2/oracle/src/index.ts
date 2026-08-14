/**
 * AFCI-Bench v2 architecture-conformance oracle — public API.
 *
 * Development scaffolding for study v2. Deterministic, blind (no condition/model),
 * fail-closed. See docs/v2/ORACLE_VALIDATION_REQUIREMENTS.md and
 * docs/v2/HIDDEN_EVALUATOR_BOUNDARY.md. No paid model run is produced by this code.
 */

export { evaluateSnapshot, EVALUATOR_NAME, EVALUATOR_VERSION, FINDING_SCHEMA_VERSION } from './engine';
export type { EvaluateOptions } from './engine';
export { OracleError } from './errors';
export type { OracleFailReason } from './errors';
export { assertEvaluatorMountOutsideWorktree, isInside } from './mountPolicy';
export { loadManifest, VALID_MANIFEST_STATUSES } from './manifest';
export {
  assertManifestScorable,
  assertOpportunityRulesValid,
  assertEligibilityConsistent,
  e1DenominatorOpportunities,
} from './manifestIntegrity';
export type { EligibilityOptions } from './manifestIntegrity';
export { LayerMap } from './layers';
export { ImportGraphResolver, listSourceFiles, parseCompilerOptions, extractSpecifiers } from './resolver';
export { RULE_REGISTRY, isKnownRule, descriptorFor } from './checkers/registry';
export {
  DEP_FAMILY_RULE_IDS,
  DEP_UMBRELLA_RULE_ID,
  edgeInOpportunityScope,
  isForbiddenDirection,
  leafRuleFor,
  runDependencyDirection,
} from './checkers/dependencyDirection';
export * from './types';
