TASK=T10, CONDITION=afci, BASE=paper-v0-runner, MODEL=Opus 7
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
TASK: T10 - Standardize errors and mapping

Goal: Introduce typed errors (NotFoundError, ValidationError) and ensure correct HTTP status mapping.

Acceptance Criteria:
- npm run ci passes.
- Integration tests validate correct status codes for each error.
- Errors logged with errorType + correlationId.
