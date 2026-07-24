/**
 * Fail-closed error type for the architecture-conformance oracle.
 *
 * The oracle refuses to score (throws) rather than returning a permissive result
 * whenever an integrity precondition is not met (see PART C item 9 and
 * docs/v2/EVALUATOR_MOUNT_POLICY.md). A refusal is never downgraded to a pass.
 */

export type OracleFailReason =
  | 'INFRA_EVALUATOR_MOUNT' // evaluator mount is inside the coding worktree
  | 'MANIFEST_MISSING' // manifest file absent or unreadable
  | 'MANIFEST_MALFORMED' // manifest is not valid JSON / fails structural validation
  | 'MANIFEST_VERSION_UNRESOLVED' // manifest id/version missing or unresolved
  | 'UNKNOWN_RULE_ID' // an applicable rule id is not registered
  | 'MISSING_EVALUATOR_FILE' // a referenced evaluator/alias file does not exist
  | 'MALFORMED_ALIAS_CONFIG' // the snapshot tsconfig cannot be parsed
  | 'INCOMPLETE_SCORING'; // a rule could not be evaluated to completion

export class OracleError extends Error {
  public readonly reason: OracleFailReason;
  public readonly detail?: string;

  constructor(reason: OracleFailReason, message: string, detail?: string) {
    super(`[${reason}] ${message}`);
    this.name = 'OracleError';
    this.reason = reason;
    this.detail = detail;
    // Preserve the prototype chain under CommonJS transpilation targets.
    Object.setPrototypeOf(this, OracleError.prototype);
  }
}
