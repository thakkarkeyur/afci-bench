# Task T11: Cancel Order endpoint (reset candidate)

## Goal
Add a cancel order capability. This task is intended to be run both in normal and reset conditions.

## Constraints
- You MUST follow existing patterns created in earlier tasks (contracts -> features -> infra -> api).
- Do not invent new layering or file placement.
- Use typed errors and observability patterns already present.

## Acceptance Criteria
- `npm run ci` passes.
- Tests cover cancel success + cancel not-found.
- No boundary violations.

## Notes
- This task is a drift detector: a "reset" run should still implement it consistently by relying on MAD + repo patterns.
