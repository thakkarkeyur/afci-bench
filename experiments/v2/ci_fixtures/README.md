# experiments/v2/ci_fixtures — Controlled CI fixtures

Fixtures used by the **experimental-CI separation** tests
(`experiments/v2/harness/tests/test_experimental_ci_separation.py`) to prove that
the two CI surfaces behave differently on architecture:

- **`npm run ci`** (repository validation) **includes** architecture enforcement
  via `@nx/enforce-module-boundaries` (root `.eslintrc.json`).
- **`npm run ci:agent`** (the only CI visible to the coding model) **excludes**
  `@nx/enforce-module-boundaries` (via `.eslintrc.agent.json`) while retaining
  type checking, visible unit tests, and ordinary non-architecture lint.

See [`docs/v2/EXPERIMENTAL_CI_POLICY.md`](../../../docs/v2/EXPERIMENTAL_CI_POLICY.md).

## `boundary_violation.ts.fixture`

A single architecture-boundary violation: a `scope:observability` source
importing from `@afci-bench/contracts`, which the root `depConstraints` forbid
(`scope:observability` may depend on nothing). It is stored with the
`.ts.fixture` extension so **no** normal tool compiles or lints it (it is outside
every nx project's lint patterns and `tsc` ignores `.ts.fixture`). This is why it
does **not** break `npm run ci`.

The separation test **materializes** it into a tagged library source directory,
runs ESLint under both configurations, asserts:

- normal config → reports `@nx/enforce-module-boundaries` (detectable, per
  requirement 4);
- agent config → reports **no** architecture rule (not rejected for
  architectural reasons, per requirement 3);

and then always removes the materialized file (a `try/finally`), so the working
tree and `npm run ci` stay green.

This is a **benchmark-measurement choice**, not a recommendation that production
teams disable architecture enforcement. See the policy document for the rationale.
