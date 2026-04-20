# Task T10: Standardize errors and mapping

## Goal
Introduce a small set of typed errors (e.g., NotFoundError, ValidationError) and ensure:
- features/core throw typed errors
- api maps them to correct HTTP status codes
- errors are logged with errorType + correlationId

## Constraints
- Typed errors should live in the right place:
  - If shared across layers, place in contracts (or core if purely domain)
- Do not introduce circular deps.
- Keep changes minimal.

## Acceptance Criteria
- `npm run ci` passes.
- Integration tests validate correct status codes for each error.
