/**
 * Load and structurally validate the frozen evaluator manifest, fail-closed.
 *
 * The engine consumes JSON (not the YAML catalog) so it needs no YAML dependency.
 * Validation here is a fail-closed structural check of the fields the engine
 * uses; the full JSON-Schema check lives in the Python/Jest schema tests.
 */

import * as fs from 'fs';

import { OracleError } from './errors';
import {
  DependencyPolicy,
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
  const { alias_config_path, source_globs, layers, allowed } = raw;
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
  return { alias_config_path, source_globs, layers: parsedLayers, allowed: parsedAllowed };
}

function parseOpportunities(raw: unknown): Opportunity[] {
  if (!Array.isArray(raw)) {
    throw new OracleError('MANIFEST_MALFORMED', 'opportunities must be an array');
  }
  return raw.map((o, i) => {
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

  if (!isStringArray(raw.applicable_rule_ids)) {
    throw new OracleError('MANIFEST_MALFORMED', 'applicable_rule_ids must be a string array');
  }

  const dependency_policy = parseDependencyPolicy(raw.dependency_policy);
  const opportunities = parseOpportunities(raw.opportunities);

  return {
    schema_version: typeof raw.schema_version === 'string' ? raw.schema_version : '',
    manifest_id,
    manifest_version,
    task_id: typeof raw.task_id === 'string' ? raw.task_id : null,
    base_sha: typeof raw.base_sha === 'string' ? raw.base_sha : '',
    status: (raw.status as EvaluatorManifest['status']) ?? 'template',
    invalidation: isObject(raw.invalidation)
      ? {
          invalidated: raw.invalidation.invalidated === true,
          reason: typeof raw.invalidation.reason === 'string' ? raw.invalidation.reason : null,
          superseded_by:
            typeof raw.invalidation.superseded_by === 'string' ? raw.invalidation.superseded_by : null,
        }
      : { invalidated: false, reason: null, superseded_by: null },
    applicable_rule_ids: raw.applicable_rule_ids,
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
