# Task T03: Define OrderRepository port and refactor to use it

## Goal
Introduce a shared repository interface (port) to decouple features from infra implementation.

## Constraints
- The port/interface MUST live in libs/contracts (per MAD ports/interfaces rule).
- features may depend on contracts/core/observability.
- infra implements the port but MUST NOT import core.

## Acceptance Criteria
- `npm run ci` passes.
- features depends only on the interface, not concrete infra class.
- infra provides the concrete implementation and wiring is done in api or features entry points (consistent with current pattern).
- Tests remain green.

## Notes
- Prefer minimal refactor: extract only what's needed.
