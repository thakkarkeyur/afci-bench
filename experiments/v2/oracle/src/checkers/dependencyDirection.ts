/**
 * Reference checker: dependency-direction conformance (AR-DEP-001 family).
 *
 * Evaluates the whole repository snapshot's import graph against the frozen
 * allowed-dependency matrix. A cross-layer import edge whose target layer is not
 * permitted for the importer layer is a violation. Intra-layer and third-party
 * edges are always allowed. Findings are tagged with the most specific applicable
 * AR-DEP rule; raw violations and frozen-opportunity accounting are recorded
 * separately.
 *
 * OPPORTUNITY ATTRIBUTION IS SCOPE-BASED, NOT FILE-BASED. A frozen opportunity
 * names an architectural DECISION — a `locator.scope` layer plus the target
 * layers that decision forbids — and is scored over every source file the frozen
 * layer path globs assign to that scope. A task may legitimately place its new
 * implementation code in a different file of the same frozen scope, so matching a
 * single historical `locator.importer_path` would score such a change SATISFIED
 * while its forbidden edge sat in `raw_violation_count` only. `importer_path` is
 * therefore retained as PROVENANCE (authoring evidence) and never determines
 * scoring.
 *
 * One frozen opportunity stays one opportunity: however many forbidden edges the
 * snapshot contains inside a scope, that opportunity contributes AT MOST ONE
 * violation. The denominator is the frozen manifest opportunity count and never
 * depends on files the model created, edited, or matched.
 *
 * EVERY INPUT HERE IS PRODUCTION SOURCE. `ctx.edges` and `ctx.sourceFiles` carry
 * only files the production-source policy admitted (productionSource.ts); test
 * specs, test support material and tooling config were removed by the engine
 * before the graph was built. A prohibited import that exists only in a test file
 * therefore reaches neither the raw series nor the opportunity accounting, and a
 * frozen scope that retains only test files is NOT_APPLICABLE rather than
 * SATISFIED — the production decision genuinely has no material to evaluate.
 */

import { OracleError } from '../errors';
import { CheckerContext, CheckerResult, Finding, ImportEdge, Opportunity, Severity } from '../types';

export const DEP_FAMILY_RULE_IDS = [
  'AR-DEP-001',
  'AR-DEP-002',
  'AR-DEP-003',
  'AR-DEP-004',
  'AR-DEP-005',
  'AR-DEP-006',
];

/**
 * The umbrella rule. It may appear in `applicable_rule_ids` to put the WHOLE
 * matrix in force (raw exposure), but it may never back a scored opportunity —
 * only implemented leaf clauses may (see manifestIntegrity.assertOpportunityRulesValid).
 */
export const DEP_UMBRELLA_RULE_ID = 'AR-DEP-001';

const UMBRELLA = DEP_UMBRELLA_RULE_ID;

const SEVERITY_BY_RULE: Record<string, Severity> = {
  'AR-DEP-001': 'blocker',
  'AR-DEP-002': 'blocker',
  'AR-DEP-003': 'blocker',
  'AR-DEP-004': 'blocker',
  'AR-DEP-005': 'blocker',
  'AR-DEP-006': 'major',
};

/**
 * The implemented LEAF rule for a source-scope -> forbidden-target relationship,
 * or null when the family has no leaf clause for it (only the umbrella covers it).
 * A relationship with no leaf clause cannot back a scored opportunity.
 */
export function leafRuleFor(importerLayer: string, targetLayer: string): string | null {
  switch (importerLayer) {
    case 'contracts':
      return 'AR-DEP-002';
    case 'core':
      return 'AR-DEP-003';
    case 'infra':
      return 'AR-DEP-004';
    case 'api':
      return targetLayer === 'core' ? 'AR-DEP-005' : null;
    case 'features':
      return 'AR-DEP-006';
    default:
      return null;
  }
}

/** Map a forbidden edge to the most specific AR-DEP rule id (umbrella if no leaf). */
function specificRuleFor(importerLayer: string, targetLayer: string): string {
  return leafRuleFor(importerLayer, targetLayer) ?? UMBRELLA;
}

/** True when `importerLayer -> targetLayer` is not permitted by the frozen matrix. */
export function isForbiddenDirection(
  importerLayer: string | null,
  targetLayer: string | null,
  allowed: Record<string, string[]>,
): boolean {
  if (importerLayer === null || targetLayer === null) {
    return false; // ungoverned importer or third-party/ungoverned target
  }
  if (importerLayer === targetLayer) {
    return false; // intra-layer imports are always allowed
  }
  const allowedTargets = allowed[importerLayer] ?? [];
  return !allowedTargets.includes(targetLayer);
}

/** The rule id a finding is reported under, given the applicable set. */
function reportedRuleId(specific: string, applicable: Set<string>): string | null {
  if (applicable.has(specific)) {
    return specific;
  }
  if (applicable.has(UMBRELLA)) {
    return UMBRELLA;
  }
  return null;
}

/**
 * Does this forbidden edge fall inside the opportunity's frozen decision? The
 * edge's IMPORTER LAYER (assigned by the frozen layer path globs, so a model
 * cannot relabel it) must be the frozen scope, and its target must be one of the
 * frozen forbidden targets. The edge's file path is irrelevant — that is exactly
 * what makes a new-file violation attributable.
 */
export function edgeInOpportunityScope(edge: ImportEdge, opp: Opportunity): boolean {
  if (opp.locator.scope === null || edge.importer_layer !== opp.locator.scope) {
    return false;
  }
  if (edge.target_layer === null) {
    return false;
  }
  return (opp.locator.forbidden_target_layers ?? []).includes(edge.target_layer);
}

/**
 * Does the frozen scope still exist as PRODUCTION source material in the
 * snapshot? Only a scope with no production files at all is NOT_APPLICABLE; a
 * scope whose historical anchor file was deleted or moved is still live and still
 * scored. Test/config files in the scope do not keep a decision alive, because
 * they cannot carry a production dependency in the first place.
 */
function scopeHasSourceMaterial(ctx: CheckerContext, scope: string | null): boolean {
  if (scope === null) {
    return false;
  }
  return ctx.sourceFiles.some((f) => ctx.layerOf(f) === scope);
}

export function runDependencyDirection(
  ctx: CheckerContext,
  applicableRuleIds: string[],
): CheckerResult {
  const applicable = new Set(applicableRuleIds.filter((r) => DEP_FAMILY_RULE_IDS.includes(r)));
  const allowed = ctx.manifest.dependency_policy.allowed;
  const findings: Finding[] = [];

  // The frozen opportunities that this manifest scores. Their COUNT is the E1
  // denominator; it is fixed here and never touched by what the snapshot contains.
  const depOpportunities = ctx.manifest.opportunities.filter((o) => {
    if (!DEP_FAMILY_RULE_IDS.includes(o.rule_id)) {
      return false;
    }
    return applicable.has(o.rule_id) || applicable.has(UMBRELLA);
  });

  const forbiddenEdges = ctx.edges.filter((e) =>
    isForbiddenDirection(e.importer_layer, e.target_layer, allowed),
  );

  // The opportunities the SNAPSHOT violates, decided purely from the frozen scope
  // and target set — before any rule-reporting filter can affect the answer. The
  // raw findings below must reproduce exactly this set, or scoring is incomplete.
  const scopeViolatedOppIds = new Set(
    depOpportunities
      .filter((o) => forbiddenEdges.some((e) => edgeInOpportunityScope(e, o)))
      .map((o) => o.opportunity_id),
  );

  // ---- Raw violations over the whole snapshot ---------------------------- //
  // One finding per forbidden edge (the descriptive raw series). Each is linked
  // to the frozen opportunity whose scope it falls in, if any. Manifest integrity
  // guarantees the (scope, forbidden-target) decisions are pairwise disjoint, so
  // an edge belongs to AT MOST ONE opportunity and the link is unambiguous.
  for (const edge of forbiddenEdges) {
    const importerLayer = edge.importer_layer as string;
    const targetLayer = edge.target_layer as string;
    const specific = specificRuleFor(importerLayer, targetLayer);
    const ruleId = reportedRuleId(specific, applicable);
    if (ruleId === null) {
      continue; // this edge's rule is not applicable for this manifest
    }
    const opp = depOpportunities.find((o) => edgeInOpportunityScope(edge, o));
    findings.push({
      finding_id: `${ruleId}::viol::${edge.importer_path}::${edge.line}::${edge.column}::${edge.kind}`,
      rule_id: ruleId,
      opportunity_id: opp ? opp.opportunity_id : null,
      violation: true,
      status: 'VIOLATION',
      severity: SEVERITY_BY_RULE[ruleId] ?? 'blocker',
      evaluation_mode: 'automated',
      automated: true,
      confidence: 'certain',
      importer_layer: importerLayer,
      target_layer: targetLayer,
      evidence_paths: [edge.importer_path],
      evidence_locations: [
        { path: edge.importer_path, line: edge.line, column: edge.column, snippet: `${edge.kind} '${edge.specifier}'` },
      ],
      resolution_chain: edge.resolution_chain,
      message:
        `${importerLayer} must not depend on ${targetLayer}: ` +
        `${edge.kind} '${edge.specifier}'` +
        (edge.internal_unresolved ? ' (target moved/deleted; layer attributed by path)' : ''),
    });
  }

  // ---- Frozen-opportunity accounting (scope-based) ----------------------- //
  // VIOLATION      — at least one forbidden edge matching the frozen scope and
  //                  target set exists ANYWHERE in the snapshot. Several such
  //                  edges still count as ONE violated opportunity, because the
  //                  raw findings all carry the same opportunity_id.
  // SATISFIED      — the frozen scope exists in the snapshot and contains no such
  //                  edge anywhere.
  // NOT_APPLICABLE — the frozen scope itself carries no source material, so the
  //                  decision cannot be evaluated. Deleting or moving the
  //                  historical anchor file never reaches this branch.
  const linkedOppIds = new Set(
    findings.filter((f) => f.violation && f.opportunity_id).map((f) => f.opportunity_id),
  );

  // Fail closed rather than under-count: every opportunity the frozen scopes say
  // is violated must actually carry a linked raw finding. If a forbidden edge
  // inside a frozen scope were dropped before reporting, the opportunity would
  // fall through to SATISFIED below — exactly the silent miss this change exists
  // to remove — so refuse to emit a result instead.
  const unreported = [...scopeViolatedOppIds].filter((id) => !linkedOppIds.has(id)).sort();
  if (unreported.length > 0) {
    throw new OracleError(
      'INCOMPLETE_SCORING',
      'a frozen opportunity is violated in its scope but carries no reported violation finding',
      unreported.join(', '),
    );
  }

  for (const opp of depOpportunities) {
    if (linkedOppIds.has(opp.opportunity_id)) {
      continue; // represented by its linked raw VIOLATION finding(s)
    }
    const scope = opp.locator.scope;
    const targets = opp.locator.forbidden_target_layers ?? [];
    const provenance = opp.locator.importer_path;
    if (!scopeHasSourceMaterial(ctx, scope)) {
      findings.push({
        finding_id: `${opp.rule_id}::opp-absent::${opp.opportunity_id}`,
        rule_id: opp.rule_id,
        opportunity_id: opp.opportunity_id,
        violation: false,
        status: 'NOT_APPLICABLE',
        severity: SEVERITY_BY_RULE[opp.rule_id] ?? 'blocker',
        evaluation_mode: 'automated',
        automated: true,
        confidence: 'certain',
        importer_layer: scope,
        target_layer: null,
        evidence_paths: [],
        evidence_locations: [],
        resolution_chain: [],
        message:
          `opportunity ${opp.opportunity_id}: the frozen scope '${scope ?? '(unspecified)'}' carries no source ` +
          'material in this snapshot, so the decision cannot be evaluated; not counted as a violation',
      });
    } else {
      findings.push({
        finding_id: `${opp.rule_id}::opp-ok::${opp.opportunity_id}`,
        rule_id: opp.rule_id,
        opportunity_id: opp.opportunity_id,
        violation: false,
        status: 'SATISFIED',
        severity: SEVERITY_BY_RULE[opp.rule_id] ?? 'blocker',
        evaluation_mode: 'automated',
        automated: true,
        confidence: 'certain',
        importer_layer: scope,
        target_layer: null,
        evidence_paths: [],
        evidence_locations: [],
        resolution_chain: [],
        message:
          `opportunity ${opp.opportunity_id}: no forbidden edge from scope '${scope}' to ` +
          `{${targets.join(', ')}} anywhere in the snapshot` +
          (provenance ? ` (authored against ${provenance}; provenance only)` : ''),
      });
    }
  }

  return { findings, status: 'evaluated' };
}
