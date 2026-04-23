TASK=T03, CONDITION=afci_reset, BASE=paper-v0-runner, MODEL=Opus 7
CRITICAL: PRIMARY CONTEXT (MAD) BELOW. FOLLOW IT STRICTLY.
# AFCI-Bench: Master Architecture Document (MAD) v0

## 1) System Overview
A small but realistic service-oriented codebase designed to test repo-level code changes
under architectural constraints and CI quality gates.

## 2) Canonical Folder Structure
/apps
  /api          # entry service (HTTP API)
/libs
  /contracts    # API contracts + shared DTOs/schemas (single source of truth)
  /core         # domain logic, pure functions, no IO
  /features     # feature modules (orchestrate core)
  /infra        # IO (db/http clients), adapters, persistence
  /observability# logging/tracing helpers

## 3) Dependency Rules (Must Hold)
MUST NOT violate these:
- features MUST NOT import other features directly.
- core MUST NOT import infra.
- contracts MUST NOT import anything.
- infra MUST NOT import features or core (adapters only; direction is inward).
- apps/api may import features, infra, observability, contracts (but not core directly).

## 4) API Contract Rules
- All externally visible request/response shapes live in libs/contracts.
- Contract changes require: update contract + update consumers + update tests.
- No ad-hoc JSON shapes inside features/apps.

## 5) Observability Rules
- Every request handler MUST log: correlationId, operation, status, latencyMs.
- Errors MUST include: correlationId + errorType + message.

## 6) Coding Rules (Strict)
- MUST keep functions small: avoid mega-functions; split by responsibility.
- MUST NOT duplicate business logic across layers.
- MUST add/adjust tests for any behavior change.
- MUST keep changes local: do not refactor unrelated modules.

## 7) MAD Evolution
MAD is mostly immutable. Changes require:
- A dedicated “MAD change” task
- Updated CI rules (if applicable)
- 1 human review + reason for change
---
TASK SPEC BELOW

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
- Prefer minimal refactor: extract only what’s needed.