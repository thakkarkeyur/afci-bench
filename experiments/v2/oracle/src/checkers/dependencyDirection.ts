/**
 * Reference checker: dependency-direction conformance (AR-DEP-001 family).
 *
 * Evaluates the whole repository snapshot's import graph against the frozen
 * allowed-dependency matrix. A cross-layer import edge whose target layer is not
 * permitted for the importer layer is a violation. Intra-layer and third-party
 * edges are always allowed. Findings are tagged with the most specific applicable
 * AR-DEP rule and linked to frozen opportunities; raw violations and
 * frozen-opportunity accounting are recorded separately.
 */

import { CheckerContext, CheckerResult, Finding, Severity } from '../types';

export const DEP_FAMILY_RULE_IDS = [
  'AR-DEP-001',
  'AR-DEP-002',
  'AR-DEP-003',
  'AR-DEP-004',
  'AR-DEP-005',
  'AR-DEP-006',
];

const UMBRELLA = 'AR-DEP-001';

const SEVERITY_BY_RULE: Record<string, Severity> = {
  'AR-DEP-001': 'blocker',
  'AR-DEP-002': 'blocker',
  'AR-DEP-003': 'blocker',
  'AR-DEP-004': 'blocker',
  'AR-DEP-005': 'blocker',
  'AR-DEP-006': 'major',
};

/** Map a forbidden edge to the most specific AR-DEP rule id. */
function specificRuleFor(importerLayer: string, targetLayer: string): string {
  switch (importerLayer) {
    case 'contracts':
      return 'AR-DEP-002';
    case 'core':
      return 'AR-DEP-003';
    case 'infra':
      return 'AR-DEP-004';
    case 'api':
      return targetLayer === 'core' ? 'AR-DEP-005' : 'AR-DEP-001';
    case 'features':
      return 'AR-DEP-006';
    default:
      return UMBRELLA;
  }
}

function isForbidden(
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

export function runDependencyDirection(
  ctx: CheckerContext,
  applicableRuleIds: string[],
): CheckerResult {
  const applicable = new Set(applicableRuleIds.filter((r) => DEP_FAMILY_RULE_IDS.includes(r)));
  const allowed = ctx.manifest.dependency_policy.allowed;
  const findings: Finding[] = [];

  // ---- Raw violations over the whole snapshot ---------------------------- //
  for (const edge of ctx.edges) {
    if (!isForbidden(edge.importer_layer, edge.target_layer, allowed)) {
      continue;
    }
    const importerLayer = edge.importer_layer as string;
    const targetLayer = edge.target_layer as string;
    const specific = specificRuleFor(importerLayer, targetLayer);
    const ruleId = reportedRuleId(specific, applicable);
    if (ruleId === null) {
      continue; // this edge's rule is not applicable for this manifest
    }
    const opp = ctx.manifest.opportunities.find(
      (o) =>
        o.locator.importer_path === edge.importer_path &&
        (!(o.locator.forbidden_target_layers && o.locator.forbidden_target_layers.length) ||
          o.locator.forbidden_target_layers.includes(targetLayer)),
    );
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

  // ---- Frozen-opportunity accounting ------------------------------------- //
  const depOpportunities = ctx.manifest.opportunities.filter((o) => {
    if (!DEP_FAMILY_RULE_IDS.includes(o.rule_id)) {
      return false;
    }
    return applicable.has(o.rule_id) || applicable.has(UMBRELLA);
  });

  // An opportunity is either represented by its linked raw VIOLATION finding, or
  // emitted here as SATISFIED (importer present, no linked violation) or
  // NOT_APPLICABLE (importer absent). Keying on the linked finding (not on whether
  // the importer has any violation) guarantees applicable == violated + fixed +
  // absent even when an importer violates a target other than the one this
  // opportunity scopes via forbidden_target_layers.
  const linkedOppIds = new Set(
    findings.filter((f) => f.violation && f.opportunity_id).map((f) => f.opportunity_id),
  );
  for (const opp of depOpportunities) {
    if (linkedOppIds.has(opp.opportunity_id)) {
      continue; // represented by its linked raw VIOLATION finding
    }
    const importerPath = opp.locator.importer_path;
    const present = importerPath !== null && ctx.fileExists(importerPath);
    if (!present) {
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
        importer_layer: opp.locator.scope,
        target_layer: null,
        evidence_paths: importerPath ? [importerPath] : [],
        evidence_locations: [],
        resolution_chain: [],
        message: `opportunity ${opp.opportunity_id}: importer ${importerPath ?? '(unspecified)'} is absent (moved/deleted); not counted as a violation`,
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
        importer_layer: opp.locator.scope,
        target_layer: null,
        evidence_paths: [importerPath as string],
        evidence_locations: [],
        resolution_chain: [],
        message: `opportunity ${opp.opportunity_id}: ${importerPath} respects the dependency direction`,
      });
    }
  }

  return { findings, status: 'evaluated' };
}
