# Master Architecture Document (MAD) v0

## Overview

This document defines the authoritative architecture for the `afci-bench` repository. All code changes MUST comply with the rules defined herein. CI enforcement ensures violations are caught before merge.

## Folder Structure

```
/
├── apps/
│   └── api/                 # HTTP API entrypoint (Express)
├── libs/
│   ├── contracts/           # DTOs, schemas, public API types
│   ├── core/                # Pure domain logic, no IO
│   ├── features/            # Use cases, orchestration
│   ├── infra/               # IO adapters (repositories, external services)
│   └── observability/       # Structured logging, metrics helpers
├── docs/                    # Architecture documentation
└── .github/workflows/       # CI configuration
```

## Dependency Rules

Dependencies flow in a strict direction. Violations are enforced by Nx module boundary rules.

| Source Layer    | Allowed Dependencies                          | Forbidden Dependencies          |
|-----------------|-----------------------------------------------|--------------------------------|
| `contracts`     | None (external libs only)                     | All internal libs              |
| `observability` | None (external libs only)                     | All internal libs              |
| `core`          | `contracts`                                   | `infra`, `features`, `apps/*`  |
| `features`      | `core`, `contracts`, `observability`          | `infra`, `apps/*`              |
| `infra`         | `contracts`, `observability`                  | `core`, `features`, `apps/*`   |
| `apps/api`      | `features`, `infra`, `contracts`, `observability` | `core` (use via features)  |

### Rationale

- **contracts**: Must be dependency-free to allow sharing across all layers without cycles. Shared interfaces/ports that need cross-layer visibility belong here.
- **core**: Contains pure business logic; must not have IO dependencies.
- **features**: Orchestrates use cases; receives adapters via dependency injection (ports pattern).
- **infra**: Implements adapters; uses contracts for shared types. Does NOT import core.
- **observability**: Cross-cutting concern, must remain independent.

### Ports and Interfaces

Shared interfaces (ports) that must be visible to multiple layers MUST be placed in `libs/contracts`. This ensures:
- `features` can define dependencies on port interfaces
- `infra` can implement those interfaces without importing `core` or `features`
- `apps/api` can wire adapters to use cases

Domain-internal types (not shared across boundaries) may remain in their respective layer.

## Contract Rules

1. **MUST**: All request/response DTOs live in `libs/contracts`.
2. **MUST**: Apps and features must NOT define ad-hoc DTOs inline.
3. **MUST**: Contract changes require corresponding test updates.
4. **SHOULD**: Use TypeScript interfaces (not classes) for DTOs.
5. **SHOULD**: Version contracts when making breaking changes.

## Observability Rules

> **Note (v0):** Observability rules are evaluated as **P1** (non-blocking) in CI due to limitations of static enforcement. Compliance is verified via integration tests and code review.

1. **MUST**: Every HTTP request handler logs a structured JSON entry with:
   - `correlationId` (from `x-correlation-id` header or generated UUID)
   - `operation` (string describing the operation)
   - `status` (`success` | `fail`)
   - `latencyMs` (number, milliseconds)

2. **MUST**: Error logs include:
   - `correlationId`
   - `errorType` (classification string)
   - `message` (human-readable description)

3. **MUST**: Use the `@afci-bench/observability` library; no direct `console.log`.

4. **SHOULD**: Include `timestamp` in all log entries (handled by Logger).

## Coding Rules

### MUST (P0 - CI blocking)

1. **MUST** pass TypeScript strict mode compilation with no errors.
2. **MUST** pass ESLint with no errors (warnings allowed in dev).
3. **MUST** pass all unit and integration tests.
4. **MUST** respect module boundary rules (enforced by `@nx/enforce-module-boundaries`).
5. **MUST** use strong typing; `any` type is forbidden.
6. **MUST** handle errors explicitly; no unhandled promise rejections.
7. **MUST** include correlationId in all API responses (header) and error bodies.
8. **MUST** keep business logic in `core`; HTTP handlers only orchestrate.

### SHOULD (P1 - Review feedback)

1. **SHOULD** use async/await over raw promises.
2. **SHOULD** prefer composition over inheritance.
3. **SHOULD** keep functions small (<50 lines) and focused.
4. **SHOULD** use descriptive names; avoid abbreviations.
5. **SHOULD** document public APIs with JSDoc comments.
6. **SHOULD** write tests for all new functionality.

### MUST NOT

1. **MUST NOT** import from `core` in `infra` (use contracts for shared types).
2. **MUST NOT** import from `infra` in `features` (use dependency injection).
3. **MUST NOT** bypass the structured logger with console statements.
4. **MUST NOT** store secrets in code; use environment variables.

## CI Enforcement

The following checks run on every PR and push:

| Check          | Command                  | Blocking |
|----------------|--------------------------|----------|
| Lint           | `npm run lint`           | Yes      |
| Type Check     | `npm run typecheck`      | Yes      |
| Unit Tests     | `npm run test`           | Yes      |
| Boundary Check | Included in lint         | Yes      |

All checks must pass for merge.

## MAD Evolution Policy

1. **Versioning**: Increment version in filename (MAD_v1.md, etc.) for breaking changes.
2. **Backward Compatibility**: Non-breaking additions append to existing rules.
3. **Review**: Architecture changes require team review and approval.
4. **Automation**: All MUST rules should have corresponding CI enforcement.
5. **Documentation**: Update this document before implementing architectural changes.

## Quick Reference

```
contracts  ← (nothing)
observability ← (nothing)
core       ← contracts
features   ← core, contracts, observability
infra      ← contracts, observability
apps/api   ← features, infra, contracts, observability
```

---

*Last Updated: v0 - Initial Release*
