TASK=T01, CONDITION=afci_reset, BASE=paper-v0-runner, MODEL=Opus 7
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