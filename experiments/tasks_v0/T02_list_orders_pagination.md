# Task T02: List Orders with Pagination

## Goal
Add an endpoint to list orders with optional pagination (limit + offset or page + pageSize).

## Constraints
- DTOs in libs/contracts.
- Features orchestrates; infra provides storage access.
- Keep changes minimal; no unrelated refactors.

## Acceptance Criteria
- `npm run ci` passes.
- Endpoint supports default pagination and returns stable ordering.
- Tests: add integration tests covering:
  - default paging
  - custom paging
  - empty result

## Notes
- Reuse existing in-memory store.
- If no store supports multiple orders, extend it minimally.