# Task T12: Add order status enum and propagate (reset candidate)

## Goal
Introduce an enum-like status (e.g., CREATED, UPDATED, CANCELLED) in contracts, and ensure responses use it consistently.

## Constraints
- Status definition belongs in contracts.
- Update all affected layers (features, infra, api) and tests.
- No ad-hoc status strings scattered across code.

## Acceptance Criteria
- `npm run ci` passes.
- Tests assert status values for create/update/cancel flows.
- Minimal changes; no unrelated refactoring.

## Notes
- Intended for reset testing: ensure MAD reinjection keeps the implementation consistent.