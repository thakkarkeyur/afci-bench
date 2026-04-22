TASK=T01, CONDITION=baseline_reset, BASE=paper-v0-runner, MODEL=Opus 7
BASELINE PROMPT (task-only)
# Task T01: Get Order by ID (end-to-end)

## Goal
Add a new API endpoint to fetch an order by ID using the existing architecture pattern.

## Constraints
- MUST follow MAD dependency rules (no api -> core; no infra -> core; contracts is pure).
- MUST define/extend request/response DTOs in libs/contracts.
- MUST implement use-case orchestration in libs/features.
- MUST implement data access in libs/infra (in-memory is fine).
- SHOULD use observability utilities for correlationId + required fields.

## Acceptance Criteria
- `npm run ci` passes.
- Endpoint returns 200 with order payload for existing IDs, and 404 for unknown IDs.
- Tests added/updated (API integration test + any unit tests needed).
- No boundary violations.

## Notes
- Follow existing create-order patterns and naming conventions.
- If repo already has a repository interface, reuse it; otherwise add a minimal one (as a port in libs/contracts).