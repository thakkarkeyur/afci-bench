TASK=T04, CONDITION=baseline_reset, BASE=paper-v0-runner, MODEL=Opus 7
BASELINE PROMPT (task-only)
# Task T04: Contract evolution - add field and update all consumers

## Goal
Add a new field to the OrderResponse DTO (e.g., `status` or `createdAt`) and ensure the system returns it correctly.

## Constraints
- Contract changes only in libs/contracts.
- Update all dependent code and tests consistently.
- Do not create ad-hoc response shapes in api/features.

## Acceptance Criteria
- `npm run ci` passes.
- API integration tests assert the new field exists and has expected value.
- No contract duplication.

## Notes
- Keep field derivation simple (e.g., createdAt = new Date().toISOString()).