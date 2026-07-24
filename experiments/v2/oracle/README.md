# experiments/v2/oracle — Architecture-Conformance Oracle (+ future acceptance oracle)

The out-of-band **oracle**: the code and fixtures that decide, after model
generation has ended, whether a produced change conforms to the repository's
architecture rules. Development scaffolding for study v2; it produces **no** paid
run and invokes **no** model.

## What is implemented (this package)

- **Framework** (`src/`): deterministic, blind (takes no condition/model), and
  fail-closed. `evaluateSnapshot({ snapshotDir, manifestPath })` scores a complete
  final repository snapshot against a frozen, externally mounted evaluator
  manifest and returns a raw `architecture_finding` (see
  `../schemas/architecture_finding.schema.json`).
- **AST resolution** (`src/resolver.ts`): uses the TypeScript compiler API
  (`ts.resolveModuleName` + AST specifier extraction), **not** regex import
  matching. Resolves path aliases, relative imports, index/barrel imports, and
  re-exports; attributes moved/deleted targets by path; evaluates the **whole
  repository**, not added lines only. Specifiers inside comments/strings are
  ignored.
- **Reference checker** (`src/checkers/dependencyDirection.ts`): dependency-
  direction conformance for the `AR-DEP-001` family, applying the frozen
  allowed-dependency matrix from the manifest. It understands the repository's real
  `@afci-bench/*` aliases and `src/index.ts` barrels; a real-repository run reports
  `CONFORMANT` and does not false-flag the sanctioned api→features→core re-export.
- **Fail-closed** on: evaluator mount inside the coding worktree
  (`INFRA_EVALUATOR_MOUNT`), missing/malformed/unresolved manifest, unknown rule
  id, malformed/missing alias config, and incomplete scoring.
- **Explicit unimplemented stubs**: the contract/observability/coding-discipline/
  change-footprint rules are registered but report `UNIMPLEMENTED` — they can never
  report PASS until built.
- **CLI** (`src/cli.ts`): out-of-band runner; `npm run oracle:test` runs the Jest
  suite; `npm run oracle:typecheck` type-checks the oracle in isolation.

## Fixtures and tests

`fixtures/` holds synthetic `.ts.fixture` snapshots (materialized to a temp dir at
test time so the repo-wide `tsc` never compiles deliberately-broken code); `tests/`
holds the Jest suites. See `fixtures/README.md`.

## What is NOT built here

The **task-acceptance oracle** (per-task behavioural checks / hidden acceptance
tests), the labelled/mutation validation corpus, and the manual inter-rater
validation are future work — see `docs/v2/ORACLE_VALIDATION_REQUIREMENTS.md` (gates
G1/G6; `TD-B04`, `TD-B05`, `TD-B12`). Do not commit run outputs or task-specific
answers here.
