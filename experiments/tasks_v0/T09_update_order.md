# Task T09: Update Order endpoint

## Goal
Add an endpoint to update an existing order (e.g., update quantity or status).
Return 404 if not found.

## Constraints
- DTOs in contracts.
- Use feature use-case orchestration.
- Use infra repo update method.
- Keep business logic out of api.

## Acceptance Criteria
- `npm run ci` passes.
- Integration tests cover: update success, update not-found, invalid input.