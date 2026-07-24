/**
 * Rule registry: maps catalog rule ids to their oracle implementation status.
 *
 * The dependency-direction family (AR-DEP-001..006) is implemented by the
 * reference checker. All other catalog rules are registered as EXPLICIT
 * unimplemented stubs: they are known to the oracle (so an applicable stub is not
 * an unknown-rule fail-closed), but they never report PASS — they report
 * UNIMPLEMENTED, which keeps the verdict out of CONFORMANT until they are built.
 * A rule id absent from this registry is unknown and fails closed.
 */

import { EvaluationMode, OracleImplementationStatus } from '../types';
import { DEP_FAMILY_RULE_IDS } from './dependencyDirection';

export interface RuleDescriptor {
  rule_id: string;
  evaluation_mode: EvaluationMode;
  oracle_implementation_status: OracleImplementationStatus;
  implemented: boolean;
  family: 'dependency-direction' | 'none';
}

const DEP_DESCRIPTORS: Record<string, RuleDescriptor> = Object.fromEntries(
  DEP_FAMILY_RULE_IDS.map((id) => [
    id,
    {
      rule_id: id,
      evaluation_mode: 'automated' as EvaluationMode,
      oracle_implementation_status: 'implemented' as OracleImplementationStatus,
      implemented: true,
      family: 'dependency-direction' as const,
    },
  ]),
);

const STUB_DESCRIPTORS: Record<string, RuleDescriptor> = {
  'AR-CONTRACT-001': {
    rule_id: 'AR-CONTRACT-001',
    evaluation_mode: 'automated',
    oracle_implementation_status: 'stub',
    implemented: false,
    family: 'none',
  },
  'AR-OBSERV-001': {
    rule_id: 'AR-OBSERV-001',
    evaluation_mode: 'automated',
    oracle_implementation_status: 'stub',
    implemented: false,
    family: 'none',
  },
  'AR-CODE-001': {
    rule_id: 'AR-CODE-001',
    evaluation_mode: 'manual',
    oracle_implementation_status: 'stub',
    implemented: false,
    family: 'none',
  },
  'AR-CHANGE-FOOTPRINT-001': {
    rule_id: 'AR-CHANGE-FOOTPRINT-001',
    evaluation_mode: 'automated',
    oracle_implementation_status: 'stub',
    implemented: false,
    family: 'none',
  },
};

export const RULE_REGISTRY: Record<string, RuleDescriptor> = {
  ...DEP_DESCRIPTORS,
  ...STUB_DESCRIPTORS,
};

export function isKnownRule(ruleId: string): boolean {
  return Object.prototype.hasOwnProperty.call(RULE_REGISTRY, ruleId);
}

export function descriptorFor(ruleId: string): RuleDescriptor | undefined {
  return RULE_REGISTRY[ruleId];
}
