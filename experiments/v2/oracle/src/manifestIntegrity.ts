/**
 * Manifest integrity gates the engine applies BEFORE scoring (fail-closed).
 *
 * These guards exist so a mis-authored or lifecycle-invalid frozen manifest can
 * never silently mis-score or silently drop a scoring opportunity — the risks
 * that bite exactly when task-specific manifests are first authored:
 *
 *  - assertManifestScorable      (P1-3): refuse to score anything that is not an
 *                                exactly-`frozen`, non-invalidated manifest.
 *  - assertOpportunityRulesValid (P1-2 + scope attribution): every frozen
 *                                opportunity must reference a rule that is
 *                                registered, in force for this manifest (directly
 *                                applicable or covered by the AR-DEP-001
 *                                umbrella), and actually scored by the active
 *                                checker — otherwise the opportunity would be
 *                                dropped from accounting instead of counted. It
 *                                must also carry a WELL-FORMED FROZEN SCOPE: a
 *                                known dependency-policy layer, known and truly
 *                                forbidden target layers, the correct implemented
 *                                LEAF rule for that relationship (never the
 *                                AR-DEP-001 umbrella), and no other opportunity
 *                                claiming the same decision.
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
import { ApprovedEligibilityIndex, EvaluatorManifest, Opportunity } from './types';
import { descriptorFor, isKnownRule } from './checkers/registry';
import {
  DEP_FAMILY_RULE_IDS,
  DEP_UMBRELLA_RULE_ID,
  isForbiddenDirection,
  leafRuleFor,
} from './checkers/dependencyDirection';

const UMBRELLA = DEP_UMBRELLA_RULE_ID;

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

/** Deterministic key for one frozen (scope -> forbidden target) decision. */
function decisionKey(scope: string, target: string): string {
  return `${scope}->${target}`;
}

/**
 * Scope-integrity gate for one dependency opportunity (locator anchoring).
 *
 * Scoring is anchored on the frozen ARCHITECTURAL SCOPE, so the scope must be
 * well-formed or the opportunity would silently score against nothing:
 *
 *   1. `locator.scope` names a layer of the frozen `dependency_policy.layers`.
 *   2. `locator.forbidden_target_layers` is non-empty, every entry is a known
 *      layer, and every entry is genuinely forbidden for the scope by the frozen
 *      allowed matrix (a "forbidden" target that is actually permitted could
 *      never be violated, so it would pad the denominator with zero exposure).
 *   3. `rule_id` is the implemented LEAF rule for that scope -> target
 *      relationship, and is the SAME leaf for every declared target.
 *
 * `locator.importer_path` is deliberately NOT checked: it is provenance only and
 * must never become the scoring anchor again.
 */
function assertOpportunityScopeValid(opp: Opportunity, manifest: EvaluatorManifest): void {
  const layerIds = new Set(manifest.dependency_policy.layers.map((l) => l.id));
  const allowed = manifest.dependency_policy.allowed;
  const scope = opp.locator.scope;

  // 1. Known frozen dependency-policy layer.
  if (scope === null || !layerIds.has(scope)) {
    throw new OracleError(
      'INVALID_OPPORTUNITY_SCOPE',
      `opportunity '${opp.opportunity_id}' declares locator.scope '${scope ?? '(null)'}', which is not a layer id of the frozen dependency policy (known layers: ${[...layerIds].join(', ')}); scope is the scoring anchor and must resolve to frozen layer path globs`,
    );
  }

  // 2. Known, genuinely forbidden targets.
  const targets = opp.locator.forbidden_target_layers ?? [];
  if (targets.length === 0) {
    throw new OracleError(
      'INVALID_OPPORTUNITY_SCOPE',
      `opportunity '${opp.opportunity_id}' declares no locator.forbidden_target_layers; a dependency opportunity must name the target layers its frozen decision forbids`,
    );
  }
  for (const target of targets) {
    if (!layerIds.has(target)) {
      throw new OracleError(
        'INVALID_OPPORTUNITY_SCOPE',
        `opportunity '${opp.opportunity_id}' declares forbidden target layer '${target}', which is not a layer id of the frozen dependency policy`,
      );
    }
    if (!isForbiddenDirection(scope, target, allowed)) {
      throw new OracleError(
        'INVALID_OPPORTUNITY_SCOPE',
        `opportunity '${opp.opportunity_id}' declares '${scope}' -> '${target}' as forbidden, but the frozen allowed-dependency matrix permits it; such an opportunity could never be violated and would pad the E1 denominator with zero exposure`,
      );
    }
  }

  // 3. The rule must be THE implemented leaf clause for this relationship.
  for (const target of targets) {
    const leaf = leafRuleFor(scope, target);
    if (leaf === null) {
      throw new OracleError(
        'OPPORTUNITY_RULE_SCOPE_MISMATCH',
        `opportunity '${opp.opportunity_id}' declares '${scope}' -> '${target}', for which the dependency family implements no leaf rule (only the ${UMBRELLA} umbrella covers it); an umbrella-only relationship cannot back a scored opportunity`,
      );
    }
    if (leaf !== opp.rule_id) {
      throw new OracleError(
        'OPPORTUNITY_RULE_SCOPE_MISMATCH',
        `opportunity '${opp.opportunity_id}' declares rule '${opp.rule_id}' for '${scope}' -> '${target}', but the implemented leaf rule for that relationship is '${leaf}'`,
      );
    }
  }
}

/**
 * P1-2 + scope attribution — every frozen opportunity must reference a valid,
 * in-force, scored LEAF rule and carry a well-formed frozen scope.
 *
 * Fails closed on: unknown rule ids; rules absent from applicable_rule_ids (and
 * not covered by the umbrella); registered-but-unimplemented (stub) rules used as
 * scored opportunities; rules not handled by the active checker; the AR-DEP-001
 * UMBRELLA used as a scored opportunity rule; a malformed frozen scope; a rule
 * that is not the leaf for the declared scope -> target relationship; and two
 * opportunities claiming the same frozen decision. This prevents an opportunity
 * from being silently excluded from accounting, silently double-counted, or
 * silently scored against nothing.
 */
export function assertOpportunityRulesValid(manifest: EvaluatorManifest): void {
  const applicable = new Set(manifest.applicable_rule_ids);
  const umbrellaInForce = applicable.has(UMBRELLA);
  /** decision key -> opportunity_id that already claims it. */
  const claimedDecisions = new Map<string, string>();

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

    // 3b. The UMBRELLA is never a scored opportunity rule. It may sit in
    // applicable_rule_ids to put the whole matrix in force (raw exposure), but a
    // fixed E1 opportunity must name the implemented LEAF clause for its frozen
    // decision, so the denominator cannot be built from an unscoped catch-all.
    if (ruleId === UMBRELLA) {
      throw new OracleError(
        'UMBRELLA_OPPORTUNITY_RULE',
        `opportunity '${opp.opportunity_id}' uses the umbrella rule '${UMBRELLA}' as a scored opportunity; the umbrella may only appear in applicable_rule_ids to expand raw dependency-family exposure, and a fixed E1 opportunity must name the implemented leaf clause (AR-DEP-002..006) for its frozen scope -> forbidden-target decision`,
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

    // 5. The frozen scope must be well-formed and must match the leaf rule.
    assertOpportunityScopeValid(opp, manifest);

    // 6. No two opportunities may claim the same frozen (scope, target) decision.
    // Overlapping decisions would attribute ONE forbidden edge to TWO frozen
    // opportunities, inflating the E1 numerator for a single architectural choice
    // — and an equivalent duplicate record is exactly what an umbrella/leaf pair
    // would produce.
    for (const target of opp.locator.forbidden_target_layers ?? []) {
      const key = decisionKey(opp.locator.scope as string, target);
      const claimedBy = claimedDecisions.get(key);
      if (claimedBy !== undefined) {
        throw new OracleError(
          'DUPLICATE_OPPORTUNITY_SCOPE',
          `opportunities '${claimedBy}' and '${opp.opportunity_id}' both claim the frozen decision '${key}'; one architectural decision is exactly one opportunity, so a duplicated/equivalent record would double-count a single forbidden edge`,
        );
      }
      claimedDecisions.set(key, opp.opportunity_id);
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

/** The four frozen-opportunity accounting buckets the engine reports. */
export interface OpportunityAccounting {
  applicable_opportunity_count: number;
  fixed_opportunity_count: number;
  violated_opportunity_count: number;
  absent_opportunity_count: number;
}

/**
 * Reconcile the frozen-opportunity accounting, or refuse to emit a result.
 *
 * Two invariants, both of which must hold before an E1 rate means anything:
 *
 *   1. NO FROZEN OPPORTUNITY WAS DROPPED. After the P1-2 validation every frozen
 *      opportunity is an in-force dependency-family scoring opportunity, so the
 *      dep-family filter must not have excluded any of them. If it did, the
 *      denominator would silently disagree with the uniquely-scored opportunity
 *      set — a smaller denominator on the same numerator.
 *   2. EACH OPPORTUNITY IS BUCKETED EXACTLY ONCE. Opportunity ids are unique
 *      (P1-1, enforced by the loader), and the checker emits exactly one outcome
 *      per opportunity, so fixed + violated + absent must equal applicable. A
 *      shortfall means an opportunity was scored under no status; an excess means
 *      one was counted under two.
 *
 * WHY THIS IS A SEPARATE, EXPORTED UNIT. Both branches are DEFENSIVE: they are
 * unreachable through any valid manifest, because the loader's
 * DUPLICATE_OPPORTUNITY_ID check and `assertOpportunityRulesValid` refuse first.
 * That is the correct design — the earlier gates should fail first — but it left
 * the guard itself untested, and a defensive guard nobody exercises is a guard
 * that can rot. Extracting it here lets both branches be driven directly with
 * inconsistent inputs WITHOUT weakening any earlier gate to make them reachable
 * through a manifest. The engine calls this at exactly the point the inline code
 * used to occupy, with exactly the same values, so behaviour is unchanged.
 */
export function assertOpportunityAccountingComplete(
  accountedOpportunityCount: number,
  manifestOpportunityCount: number,
  accounting: OpportunityAccounting,
): void {
  if (accountedOpportunityCount !== manifestOpportunityCount) {
    throw new OracleError(
      'INCOMPLETE_SCORING',
      'a frozen opportunity was excluded from accounting (denominator != scoring-opportunity set)',
      `accounted=${accountedOpportunityCount} manifest=${manifestOpportunityCount}`,
    );
  }
  const bucketed =
    accounting.fixed_opportunity_count +
    accounting.violated_opportunity_count +
    accounting.absent_opportunity_count;
  if (bucketed !== accounting.applicable_opportunity_count) {
    throw new OracleError(
      'INCOMPLETE_SCORING',
      'frozen-opportunity accounting is incomplete (applicable != fixed + violated + absent)',
      `applicable=${accounting.applicable_opportunity_count} fixed+violated+absent=${bucketed}`,
    );
  }
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
