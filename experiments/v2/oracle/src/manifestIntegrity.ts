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
 *  - assertEligibilityConsistent (suite-classification decision D): the manifest's
 *                                declared `e1_analysis_eligibility` must agree with
 *                                the approved public task index AND with its own
 *                                frozen opportunity set, so the public
 *                                classification cannot silently diverge from what
 *                                the evaluator actually scores.
 *
 * The invalidation REASON is deliberately never placed in a thrown error: it is
 * evaluator-authored text that must not leak toward the coding model.
 */

import { OracleError } from './errors';
import { ApprovedEligibilityIndex, EvaluatorManifest } from './types';
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

/**
 * Count the frozen opportunities that would actually enter the E1 denominator:
 * dependency-direction family only, and in force for this manifest. Shared with
 * the engine so the eligibility gates reason about the same number the accounting
 * block reports.
 */
export function e1DenominatorOpportunities(manifest: EvaluatorManifest) {
  const applicable = new Set(manifest.applicable_rule_ids);
  return manifest.opportunities.filter(
    (o) =>
      DEP_FAMILY_RULE_IDS.includes(o.rule_id) &&
      (applicable.has(o.rule_id) || applicable.has(UMBRELLA)),
  );
}

export interface EligibilityOptions {
  /**
   * Approved public eligibility per task id, read from the public task index
   * (experiments/v2/tasks/public/TASK_INDEX.csv). REQUIRED whenever the manifest
   * binds a real task id: without it the manifest's self-declared eligibility
   * could not be checked against the approved classification, so the engine fails
   * closed rather than trusting the manifest.
   */
  approvedEligibility?: ApprovedEligibilityIndex;
  /**
   * A separately recorded pre-run decision that activates an inactive reserve.
   * Absent by default: an `inactive-reserve` manifest is refused. Supplying it
   * records that the activation was decided BEFORE the run, outside the manifest.
   */
  reserveActivation?: { task_id: string; activated_eligibility: 'scored' | 'functional-only'; decision_ref: string };
}

/**
 * Suite-classification decision D — the five fail-closed eligibility gates.
 *
 * These stop the public classification and the private evaluator manifests from
 * silently diverging. They are deliberately enforced in the ENGINE (not merely in
 * JSON Schema) because the schema cannot express a cross-artifact agreement, nor
 * the relationship between eligibility and the frozen opportunity set.
 */
export function assertEligibilityConsistent(
  manifest: EvaluatorManifest,
  opts: EligibilityOptions = {},
): void {
  const eligibility = manifest.e1_analysis_eligibility;
  const taskId = manifest.task_id;
  const denominator = e1DenominatorOpportunities(manifest).length;

  // Gate 1 — the manifest value must match the approved public task index.
  // Applies to any manifest that binds a REAL task id. Templates (task_id null)
  // carry no task classification to agree with and are never scorable anyway
  // (assertManifestScorable requires status === 'frozen').
  if (taskId !== null) {
    const approved = opts.approvedEligibility;
    if (!approved) {
      throw new OracleError(
        'ELIGIBILITY_TASK_INDEX_MISMATCH',
        `manifest binds task '${taskId}' but no approved public eligibility index was supplied; the declared eligibility cannot be verified and the manifest must not be scored`,
        eligibility,
      );
    }
    const expected = approved[taskId];
    if (expected === undefined) {
      throw new OracleError(
        'ELIGIBILITY_TASK_INDEX_MISMATCH',
        `task '${taskId}' does not appear in the approved public task index; an unapproved task must not be scored`,
        eligibility,
      );
    }
    if (expected !== eligibility) {
      throw new OracleError(
        'ELIGIBILITY_TASK_INDEX_MISMATCH',
        `manifest declares e1_analysis_eligibility '${eligibility}' for task '${taskId}' but the approved public task index records '${expected}'`,
        `${eligibility} != ${expected}`,
      );
    }
  }

  // Gate 3 — an inactive reserve enters no E1 run or aggregation unless a
  // separately recorded pre-run activation decision changes its eligibility.
  // Draft opportunities are NOT required to be deleted: while the reserve is
  // inactive nothing about it is ever scored, so those opportunities are
  // analytically inactive by construction.
  let effective = eligibility;
  if (eligibility === 'inactive-reserve') {
    const act = opts.reserveActivation;
    const activatesThisTask =
      !!act && taskId !== null && act.task_id === taskId && !!act.decision_ref;
    if (!activatesThisTask) {
      throw new OracleError(
        'ELIGIBILITY_RESERVE_INACTIVE',
        `manifest is classified 'inactive-reserve' and must not enter an E1 run or aggregation; any draft opportunities it carries remain analytically inactive until a separately recorded pre-run activation decision changes its eligibility`,
        taskId ?? 'no-task-id',
      );
    }
    // Activated: the remaining gates apply to the eligibility the recorded
    // decision confers, never to the stale 'inactive-reserve' label.
    effective = act!.activated_eligibility;
  }

  // Gate 2 — a functional-only task contributes NO E1 opportunity denominator.
  if (effective === 'functional-only' && denominator > 0) {
    throw new OracleError(
      'ELIGIBILITY_DENOMINATOR_CONFLICT',
      `manifest is classified 'functional-only' (structurally excluded from E1) but carries ${denominator} dependency-direction opportunit${denominator === 1 ? 'y' : 'ies'}, which would enter the E1 denominator`,
      `denominator=${denominator}`,
    );
  }

  // Gate 4 — a scored task must have a valid NON-ZERO frozen denominator before
  // it can enter E1. A zero-exposure 'scored' manifest is a classification error,
  // not a zero-violation observation.
  if (effective === 'scored' && denominator === 0) {
    throw new OracleError(
      'ELIGIBILITY_SCORED_WITHOUT_OPPORTUNITIES',
      `manifest is classified 'scored' but has no applicable frozen dependency-direction opportunity, so it has no E1 exposure; a zero denominator must never be entered as zero violations`,
      'denominator=0',
    );
  }
}
