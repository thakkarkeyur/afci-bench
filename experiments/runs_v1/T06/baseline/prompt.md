# Task T06: Observability - required log fields in API handlers

## Goal
Ensure API handlers log required fields:
- correlationId
- operation
- status
- latencyMs
and error logs include:
- correlationId
- errorType
- message

## Constraints
- Use libs/observability helpers; do not re-implement logging logic.
- Keep to minimal edits; do not refactor unrelated code.

## Acceptance Criteria
- `npm run ci` passes.
- Add at least one test that asserts correlationId propagation behavior (if feasible).
- Add/update logs in handlers you touch.

## Notes
- This is P1 in ARCH_RULES for v0, but still required by MAD; treat it seriously.
