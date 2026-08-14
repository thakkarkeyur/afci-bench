/**
 * Load and structurally validate the frozen evaluator manifest, fail-closed.
 *
 * The engine consumes JSON (not the YAML catalog) so it needs no YAML dependency.
 * Validation here is a fail-closed structural check of the fields the engine
 * uses; the full JSON-Schema check lives in the Python/Jest schema tests.
 */

import * as fs from 'fs';

import { OracleError } from './errors';
import { resolveProductionSourcePolicy } from './productionSource';
import {
  DependencyPolicy,
  E1_ANALYSIS_ELIGIBILITIES,
  E1AnalysisEligibility,
  EvaluatorManifest,
  LayerDef,
  Opportunity,
} from './types';

function isObject(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null && !Array.isArray(v);
}

function isStringArray(v: unknown): v is string[] {
  return Array.isArray(v) && v.every((x) => typeof x === 'string');
}

const UNRESOLVED_TOKENS = new Set(['', 'unresolved', 'todo', 'tbd', 'null']);

/** Recognized manifest lifecycle states (mirrors evaluator_manifest.schema.json). */
export const VALID_MANIFEST_STATUSES = ['template', 'draft', 'review', 'frozen', 'deprecated'];

function requireResolved(value: unknown, field: string): string {
  if (typeof value !== 'string' || UNRESOLVED_TOKENS.has(value.trim().toLowerCase())) {
    throw new OracleError(
      'MANIFEST_VERSION_UNRESOLVED',
      `manifest field '${field}' is missing or unresolved`,
      String(value),
    );
  }
  return value;
}

function parseDependencyPolicy(raw: unknown): DependencyPolicy {
  if (!isObject(raw)) {
    throw new OracleError('MANIFEST_MALFORMED', 'dependency_policy must be an object');
  }
  const { alias_config_path, source_globs, layers, allowed, production_source_policy } = raw;
  if (typeof alias_config_path !== 'string' || alias_config_path.length === 0) {
    throw new OracleError('MANIFEST_MALFORMED', 'dependency_policy.alias_config_path must be a non-empty string');
  }
  if (!isStringArray(source_globs) || source_globs.length === 0) {
    throw new OracleError('MANIFEST_MALFORMED', 'dependency_policy.source_globs must be a non-empty string array');
  }
  if (!Array.isArray(layers) || layers.length === 0) {
    throw new OracleError('MANIFEST_MALFORMED', 'dependency_policy.layers must be a non-empty array');
  }
  const parsedLayers: LayerDef[] = layers.map((l, i) => {
    if (!isObject(l) || typeof l.id !== 'string' || !isStringArray(l.path_globs)) {
      throw new OracleError('MANIFEST_MALFORMED', `dependency_policy.layers[${i}] is malformed`);
    }
    return { id: l.id, path_globs: l.path_globs };
  });
  if (!isObject(allowed)) {
    throw new OracleError('MANIFEST_MALFORMED', 'dependency_policy.allowed must be an object');
  }
  const parsedAllowed: Record<string, string[]> = {};
  for (const [k, v] of Object.entries(allowed)) {
    if (!isStringArray(v)) {
      throw new OracleError('MANIFEST_MALFORMED', `dependency_policy.allowed['${k}'] must be a string array`);
    }
    parsedAllowed[k] = v;
  }
  // The production-source policy is resolved here so every consumer of a loaded
  // manifest sees the EFFECTIVE policy. Omitting the field is legal and yields the
  // baseline (PSP-V1): the production/test partition is always in force, so a
  // manifest can never opt back into scoring test or tooling dependencies. A
  // malformed declaration fails closed rather than silently reverting.
  return {
    alias_config_path,
    source_globs,
    layers: parsedLayers,
    allowed: parsedAllowed,
    production_source_policy: resolveProductionSourcePolicy(production_source_policy),
  };
}

function parseOpportunities(raw: unknown): Opportunity[] {
  if (!Array.isArray(raw)) {
    throw new OracleError('MANIFEST_MALFORMED', 'opportunities must be an array');
  }
  const opportunities = raw.map((o, i) => {
    if (!isObject(o) || typeof o.opportunity_id !== 'string' || typeof o.rule_id !== 'string' || !isObject(o.locator)) {
      throw new OracleError('MANIFEST_MALFORMED', `opportunities[${i}] is malformed`);
    }
    const loc = o.locator;
    const forbidden = loc.forbidden_target_layers;
    return {
      opportunity_id: o.opportunity_id,
      rule_id: o.rule_id,
      locator: {
        importer_path: typeof loc.importer_path === 'string' ? loc.importer_path : null,
        scope: typeof loc.scope === 'string' ? loc.scope : null,
        forbidden_target_layers: isStringArray(forbidden) ? forbidden : [],
      },
      description: typeof o.description === 'string' ? o.description : null,
    };
  });

  // Fail closed on duplicate opportunity_id values (P1-1). opportunity_id is a
  // UNIQUE KEY: the engine keys id-Sets on it while sizing the denominator by
  // array length, so a repeat would silently mis-score the primary endpoint.
  // JSON Schema cannot express object-property uniqueness, so the loader is the
  // authoritative guard. We reject rather than deduplicate, and the error lists
  // the offending id(s) deterministically (sorted) for reproducibility.
  const seen = new Set<string>();
  const duplicates = new Set<string>();
  for (const o of opportunities) {
    if (seen.has(o.opportunity_id)) {
      duplicates.add(o.opportunity_id);
    }
    seen.add(o.opportunity_id);
  }
  if (duplicates.size > 0) {
    const ids = Array.from(duplicates).sort().join(', ');
    throw new OracleError(
      'DUPLICATE_OPPORTUNITY_ID',
      `evaluator manifest contains duplicate opportunity_id value(s): ${ids}`,
      `${duplicates.size} duplicated id(s)`,
    );
  }
  return opportunities;
}

/** Read, parse, and structurally validate the manifest at `manifestPath`. */
export function loadManifest(manifestPath: string): EvaluatorManifest {
  let text: string;
  try {
    text = fs.readFileSync(manifestPath, 'utf-8');
  } catch (e) {
    throw new OracleError('MANIFEST_MISSING', `cannot read evaluator manifest`, `${manifestPath}: ${String(e)}`);
  }
  let raw: unknown;
  try {
    raw = JSON.parse(text);
  } catch (e) {
    throw new OracleError('MANIFEST_MALFORMED', 'evaluator manifest is not valid JSON', String(e));
  }
  if (!isObject(raw)) {
    throw new OracleError('MANIFEST_MALFORMED', 'evaluator manifest must be a JSON object');
  }

  const manifest_id = requireResolved(raw.manifest_id, 'manifest_id');
  const manifest_version = requireResolved(raw.manifest_version, 'manifest_version');

  // Lifecycle fields must be present and well-typed (P1-3). The value gate
  // (must be 'frozen' and not invalidated) is enforced at scoring time by the
  // engine (assertManifestScorable); here we only fail closed on missing or
  // malformed lifecycle data so a manifest with no lifecycle can never be scored.
  if (typeof raw.status !== 'string' || !VALID_MANIFEST_STATUSES.includes(raw.status)) {
    throw new OracleError(
      'MANIFEST_LIFECYCLE_MISSING',
      `manifest 'status' is required and must be one of ${VALID_MANIFEST_STATUSES.join('/')}`,
      String(raw.status),
    );
  }
  if (!isObject(raw.invalidation) || typeof raw.invalidation.invalidated !== 'boolean') {
    throw new OracleError(
      'MANIFEST_LIFECYCLE_MISSING',
      "manifest 'invalidation.invalidated' (boolean) is required",
    );
  }

  if (!isStringArray(raw.applicable_rule_ids)) {
    throw new OracleError('MANIFEST_MALFORMED', 'applicable_rule_ids must be a string array');
  }

  // Analysis eligibility is REQUIRED and must be one of the three approved values.
  // A manifest authored before the suite-classification decision carries no such
  // field; it fails closed here rather than being defaulted, so a pre-migration
  // private manifest can never be scored under an assumed eligibility.
  if (
    typeof raw.e1_analysis_eligibility !== 'string' ||
    !E1_ANALYSIS_ELIGIBILITIES.includes(raw.e1_analysis_eligibility as E1AnalysisEligibility)
  ) {
    throw new OracleError(
      'ELIGIBILITY_MISSING',
      `manifest 'e1_analysis_eligibility' is required and must be one of ${E1_ANALYSIS_ELIGIBILITIES.join('/')} (manifests authored before the suite-classification decision must be migrated)`,
      String(raw.e1_analysis_eligibility),
    );
  }

  const dependency_policy = parseDependencyPolicy(raw.dependency_policy);
  const opportunities = parseOpportunities(raw.opportunities);

  return {
    schema_version: typeof raw.schema_version === 'string' ? raw.schema_version : '',
    manifest_id,
    manifest_version,
    task_id: typeof raw.task_id === 'string' ? raw.task_id : null,
    base_sha: typeof raw.base_sha === 'string' ? raw.base_sha : '',
    // status and invalidation.invalidated are validated as present above.
    status: raw.status as EvaluatorManifest['status'],
    invalidation: {
      invalidated: raw.invalidation.invalidated === true,
      reason: typeof raw.invalidation.reason === 'string' ? raw.invalidation.reason : null,
      superseded_by:
        typeof raw.invalidation.superseded_by === 'string' ? raw.invalidation.superseded_by : null,
    },
    applicable_rule_ids: raw.applicable_rule_ids,
    e1_analysis_eligibility: raw.e1_analysis_eligibility as E1AnalysisEligibility,
    opportunities,
    areas: isObject(raw.areas)
      ? {
          required: isStringArray(raw.areas.required) ? raw.areas.required : [],
          optional: isStringArray(raw.areas.optional) ? raw.areas.optional : [],
          prohibited: isStringArray(raw.areas.prohibited) ? raw.areas.prohibited : [],
        }
      : { required: [], optional: [], prohibited: [] },
    legitimate_alternatives: Array.isArray(raw.legitimate_alternatives)
      ? (raw.legitimate_alternatives as EvaluatorManifest['legitimate_alternatives'])
      : [],
    manual_rubric_refs: isStringArray(raw.manual_rubric_refs) ? raw.manual_rubric_refs : [],
    hidden_test_refs: isStringArray(raw.hidden_test_refs) ? raw.hidden_test_refs : [],
    checkpoint_ref: typeof raw.checkpoint_ref === 'string' ? raw.checkpoint_ref : null,
    evaluator_hashes: isObject(raw.evaluator_hashes)
      ? (raw.evaluator_hashes as Record<string, string>)
      : {},
    dependency_policy,
    answers_populated: raw.answers_populated === true,
  };
}
