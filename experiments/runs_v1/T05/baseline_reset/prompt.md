TASK=T05, CONDITION=baseline_reset, BASE=paper-v0-runner, MODEL=Opus 7
BASELINE PROMPT (task-only)
# Task T05: Bugfix - validation edge case

## Goal
Fix an input validation edge case for order creation (e.g., quantity <= 0, missing required field, invalid currency).

## Constraints
- Validation logic should be placed in the appropriate layer:
  - Core: pure validation helper (if needed)
  - Features: orchestrate validation + use-case flow
- API should not re-implement business validation rules.

## Acceptance Criteria
- `npm run ci` passes.
- Add/adjust tests that fail before the fix and pass after.
- Minimal change footprint.

## Notes
- If there’s already validation, extend it rather than rewriting.