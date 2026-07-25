/**
 * Manifest integrity gates the engine applies BEFORE scoring (fail-closed).
 *
 * These guards exist so a mis-authored or lifecycle-invalid frozen manifest can
 * never silently mis-score or silently drop a scoring opportunity — the risks
 * that bite exactly when task-specific manifests are first authored:
 *
 *  - assertManifestScorable      (P1-3): refuse to score anything that is not an
 *                                exactly-`frozen`, non-invalidated manifest.
 *  - assertOpportunityRulesValid (P1-2): every frozen opportunity must reference a
 *                                rule that is registered, in force for this
 *                                manifest (directly applicable or covered by the
 *                                AR-DEP-001 umbrella), and actually scored by the
 *                                active checker — otherwise the opportunity would
 *                                be dropped from accounting instead of counted.
 *
 * The invalidation REASON is deliberately never placed in a thrown error: it is
 * evaluator-authored text that must not leak toward the coding model.
 */

import { OracleError } from './errors';
import { EvaluatorManifest } from './types';
import { descriptorFor, isKnownRule } from './checkers/registry';
import { DEP_FAMILY_RULE_IDS } from './checkers/dependencyDirection';

const UMBRELLA = 'AR-DEP-001';

/**
 * P1-3 — lifecycle gate. The oracle scores only manifests that are valid for
 * evidentiary use: status exactly 'frozen' and not invalidated. Every other
 * state (template/draft/review/deprecated/other) and any invalidated manifest
 * fails closed. Lifecycle failures throw OracleError, so a consumer sees a
 * fail-closed refusal (CLI exit 3), distinct from an ordinary VIOLATIONS result.
 */
export function assertManifestScorable(manifest: EvaluatorManifest): void {
  if (manifest.status !== 'frozen') {
    throw new OracleError(
      'MANIFEST_NOT_FROZEN',
      `evaluator manifest is not scorable: status must be exactly 'frozen', got '${manifest.status}'`,
      manifest.manifest_id,
    );
  }
  if (manifest.invalidation.invalidated === true) {
    // Do NOT include invalidation.reason — it is evaluator-authored and must not
    // leak toward the coding model.
    throw new OracleError(
      'MANIFEST_INVALIDATED',
      'evaluator manifest is invalidated and must not be scored for evidence',
      manifest.manifest_id,
    );
  }
}

/**
 * P1-2 — every frozen opportunity must reference a valid, in-force, scored rule.
 * Fails closed on: unknown rule ids; rules absent from applicable_rule_ids (and
 * not covered by the umbrella); registered-but-unimplemented (stub) rules used as
 * scored opportunities; and rules that are not handled by the active checker.
 * This prevents an opportunity from being silently excluded from accounting.
 */
export function assertOpportunityRulesValid(manifest: EvaluatorManifest): void {
  const applicable = new Set(manifest.applicable_rule_ids);
  const umbrellaInForce = applicable.has(UMBRELLA);

  for (const opp of manifest.opportunities) {
    const ruleId = opp.rule_id;

    // 1. Must exist in the architecture-rule registry.
    if (!isKnownRule(ruleId)) {
      throw new OracleError(
        'INVALID_OPPORTUNITY_RULE',
        `opportunity '${opp.opportunity_id}' references unknown rule id '${ruleId}'`,
      );
    }

    // 2/3. Must be a scoring rule supported by the active evaluator. The only
    // checker that consumes opportunities is the dependency-direction family;
    // registered stubs (unimplemented) and any rule outside that family cannot
    // carry a scored opportunity.
    const desc = descriptorFor(ruleId);
    const scoredByActiveChecker =
      !!desc && desc.implemented && desc.family === 'dependency-direction' && DEP_FAMILY_RULE_IDS.includes(ruleId);
    if (!scoredByActiveChecker) {
      throw new OracleError(
        'INVALID_OPPORTUNITY_RULE',
        `opportunity '${opp.opportunity_id}' references rule '${ruleId}', which is not a scoring rule supported by the active evaluator (only the implemented dependency-direction family can carry scored opportunities)`,
      );
    }

    // 4. Must be in force for this manifest: directly applicable, or covered by
    // the AR-DEP-001 umbrella (which puts every per-layer clause in force).
    const inForce = applicable.has(ruleId) || umbrellaInForce;
    if (!inForce) {
      throw new OracleError(
        'INVALID_OPPORTUNITY_RULE',
        `opportunity '${opp.opportunity_id}' references rule '${ruleId}', which is not in applicable_rule_ids and is not covered by the ${UMBRELLA} umbrella`,
      );
    }
  }
}
