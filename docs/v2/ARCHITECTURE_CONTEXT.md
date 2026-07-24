# Repository Architecture Reference

Canonical, self-contained description of this repository's architecture: its
module structure, layer identities, dependency-direction rules, import and
resolution conventions, and the contract/observability/change disciplines that
govern changes to it.

This document is **architecture content only**. It is the single canonical
payload of repository architecture information; it contains no functional work
item, no evaluation instruction, no implementation answer, and no statement that
is specific to any one delivery channel. It is intended to be delivered
byte-for-byte identically wherever repository architecture context is provided.

---

## 1. System overview

The repository is a small but realistic service-oriented codebase organized as an
Nx-managed TypeScript monorepo. It implements an order-management domain: an HTTP
API accepts order requests, a use-case layer orchestrates validation and
persistence over pure domain logic, an infrastructure layer provides persistence
adapters, and cross-cutting logging is isolated in an observability layer. Shared
request/response shapes are declared once as contracts.

The architecture exists to keep changes local, keep dependencies pointing inward
toward stable abstractions, and keep externally visible shapes defined in exactly
one place.

## 2. Canonical folder structure

```
/apps
  /api            # entry service: HTTP API (composition root, request handling)
/libs
  /contracts      # externally visible request/response shapes (single source of truth)
  /core           # domain entities, pure functions, ports; no IO
  /features       # use-case modules that orchestrate core; expose application operations
  /infra          # IO and adapters (persistence, external clients)
  /observability  # logging/tracing helpers (cross-cutting)
```

Every library owns a single public surface at `<lib>/src/index.ts` (a barrel).
The application at `apps/api` is the composition root that wires libraries
together behind HTTP endpoints.

## 3. Module identities, aliases, and scope tags

Each internal module has a stable path, a TypeScript path alias (its public
import specifier), and an architecture **scope tag**. Internal code imports other
internal modules through the alias, never through deep internal file paths.

| Module        | Path                    | Public alias                | Scope tag            |
|---------------|-------------------------|-----------------------------|----------------------|
| contracts     | `libs/contracts`        | `@afci-bench/contracts`     | `scope:contracts`    |
| core          | `libs/core`             | `@afci-bench/core`          | `scope:core`         |
| features      | `libs/features`         | `@afci-bench/features`      | `scope:features`     |
| infra         | `libs/infra`            | `@afci-bench/infra`         | `scope:infra`        |
| observability | `libs/observability`    | `@afci-bench/observability` | `scope:observability`|
| api           | `apps/api`              | (application; not imported) | `scope:api`          |

Aliases resolve to each module's barrel (`<module>/src/index.ts`). Resolution of
these aliases is a compile-time fact declared in the workspace TypeScript path
configuration; it is not a textual convention.

## 4. Dependency-direction rules

Dependencies point **inward** toward stable abstractions. A module may import
only from the layers listed for it below; it may also import from itself
(intra-module imports) and from third-party packages. Any internal import outside
the allowed set is an architecture-boundary violation.

| Importing layer (scope) | May import from                                            |
|-------------------------|-----------------------------------------------------------|
| `scope:contracts`       | (nothing internal)                                        |
| `scope:observability`   | (nothing internal)                                        |
| `scope:core`            | `contracts`                                               |
| `scope:features`        | `core`, `contracts`, `observability`                      |
| `scope:infra`           | `contracts`, `observability`                              |
| `scope:api`             | `features`, `infra`, `contracts`, `observability`         |

Equivalent must-not statements:

- **contracts** must not import anything internal; it is the shared source of
  truth for externally visible shapes.
- **core** must not import **infra**, **features**, **observability**, or the
  application. Core is pure domain logic and depends only on contracts.
- **features** must not import **infra** or the application, and must not import
  **another feature module's internals**; features orchestrate core.
- **infra** must not import **core**, **features**, or the application; adapters
  depend inward on contracts (and observability), never on domain or use cases.
- **api** must not import **core directly**; the application reaches domain types
  and operations through **features** (see §5), not by importing core itself.

The direction is the invariant: outer, replaceable layers depend on inner, stable
layers; inner layers never depend on outer ones.

## 5. Import and resolution conventions

- **Alias imports.** Internal modules are imported by their public alias
  (`@afci-bench/<module>`), which resolves to that module's barrel. Prefer the
  alias over a relative path that reaches into another module.
- **Relative imports.** Relative imports are for a module's own internal files.
  A relative path that climbs out of a module into another module's `src` is the
  same dependency as the equivalent alias import and is governed by the same
  direction rules — it does not escape them.
- **Barrels.** Each module's `src/index.ts` is its only public surface. Consumers
  import from the barrel, not from internal files, so a module's internal layout
  can change without breaking consumers.
- **Re-exports and shared types.** A barrel may re-export selected symbols from a
  layer it is permitted to depend on. This is how the application obtains domain
  types it needs without depending on core directly: **features** re-exports the
  domain types the application requires, so the application imports them from
  **features** (an allowed dependency) rather than from **core** (a forbidden
  direct dependency). Re-exporting never launders a forbidden dependency: the
  re-exporting module must itself be permitted to depend on the origin.
- **Boundary adapters.** Where two layers describe the same concept with
  different types (for example, a domain entity versus a persistence entity), the
  application or a use case adapts between them at the boundary rather than
  importing across a forbidden edge.
- **Third-party imports.** Imports of external packages are unconstrained by the
  layer matrix; the matrix governs internal module dependencies only.

## 6. Contract rules

- All externally visible request and response shapes live in **contracts**.
- A change to an externally visible shape updates the contract, updates every
  consumer, and updates the corresponding tests together.
- Ad-hoc externally visible shapes must not be defined inside features or the
  application; they belong in contracts.

## 7. Observability rules

- Every request handler records, for each request: a correlation identifier, the
  operation, the outcome status, and the latency.
- Every error record includes: the correlation identifier, an error type, and a
  message.
- Logging is performed through the observability layer, not by ad-hoc logging
  scattered across other layers.

## 8. Coding and change discipline

- Keep functions small and single-purpose; split by responsibility rather than
  growing one function to cover many concerns.
- Do not duplicate business logic across layers; domain rules live in core.
- Any behavior change is accompanied by added or adjusted tests.
- Keep changes local: address the change at hand without refactoring unrelated
  modules, and keep the changed surface as small as the change requires.

## 9. Architecture evolution governance

The architecture is intended to be stable. A deliberate change to the structure
or the dependency-direction rules is a first-class, reviewed change — with a
stated reason and a corresponding update to any enforcement configuration — not a
side effect of an unrelated change.
