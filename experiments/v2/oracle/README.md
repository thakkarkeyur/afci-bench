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
- **Scope-based opportunity attribution**: a frozen opportunity is an
  architectural *decision* — `locator.scope` (a frozen dependency-policy layer)
  plus the target layers that decision forbids — and is scored over **every**
  source file the frozen layer path globs assign to that scope. A forbidden edge
  in a **new** or **moved** file of the scope violates the same one opportunity;
  `locator.importer_path` is **provenance only** and never the scoring anchor;
  `NOT_APPLICABLE` means the *scope* carries no source material, never that a file
  was deleted; and one frozen opportunity contributes **at most one** violation,
  so `raw_violation_count` may exceed `violated_opportunity_count`. The denominator
  is the frozen manifest opportunity count and never depends on what the model
  created or edited. See `docs/v2/ORACLE_VALIDATION_REQUIREMENTS.md` §1a.
- **Production-source scoring** (`src/productionSource.ts`): E1 measures
  **production** architectural dependencies. The frozen `source_globs` and layer
  path globs both match test and tooling TypeScript that sits inside an
  architectural scope, so the engine partitions the scanned source into a
  **production dependency graph** (the only graph edges are built over) and an
  **excluded test/config/support graph** *before* resolving any import. Baseline
  policy **PSP-V1** excludes `*.spec.ts`/`*.test.ts` (and `.tsx`), the
  `__tests__`/`__mocks__`/`__fixtures__`/`test-fixtures`/`test-helpers`/`test-utils`
  subtrees, and an exhaustive list of tooling config basenames (`jest.config.ts`,
  `jest.setup.ts`, `jest.preset.ts`, vite/vitest/webpack/rollup/babel/eslint/
  karma/cypress/playwright configs). Classification is by exact basename,
  basename-only glob, and whole path-segment — never by substring — so
  `latest.ts`, `contest.ts`, `testUtils.ts` and `protest/` stay production, and
  `*.config.ts` is deliberately not a wildcard (`app.config.ts` is production).
  The frozen layer scopes are untouched; a manifest may only **add** exclusions
  (`dependency_policy.production_source_policy`, additive-only), and a malformed
  declaration fails closed (`INVALID_PRODUCTION_SOURCE_POLICY`). Every finding
  records the effective `production_source.policy_id` and the exact
  `excluded_paths`. See `docs/v2/ORACLE_VALIDATION_REQUIREMENTS.md` §1b.
- **Fail-closed** on: evaluator mount inside the coding worktree
  (`INFRA_EVALUATOR_MOUNT`), missing/malformed/unresolved manifest, missing or
  malformed lifecycle fields (`MANIFEST_LIFECYCLE_MISSING`), a manifest that is
  not lifecycle-valid for evidentiary use — status not exactly `frozen`
  (`MANIFEST_NOT_FROZEN`) or invalidated (`MANIFEST_INVALIDATED`) — a duplicate
  `opportunity_id` (`DUPLICATE_OPPORTUNITY_ID`), an opportunity referencing an
  unknown / non-applicable / non-scoring rule (`INVALID_OPPORTUNITY_RULE`), the
  `AR-DEP-001` umbrella used as a **scored** opportunity rule
  (`UMBRELLA_OPPORTUNITY_RULE` — the umbrella may only expand raw exposure through
  `applicable_rule_ids`), a malformed frozen scope or a "forbidden" target the
  matrix actually permits (`INVALID_OPPORTUNITY_SCOPE`), a rule that is not the
  implemented leaf for the declared scope→target relationship
  (`OPPORTUNITY_RULE_SCOPE_MISMATCH`), two opportunities claiming the same frozen
  decision (`DUPLICATE_OPPORTUNITY_SCOPE`), unknown rule id, malformed/missing
  alias config, and incomplete scoring (including any opportunity dropped from
  accounting). A lifecycle/integrity refusal is an `OracleError` (CLI exit 3),
  kept distinct from an ordinary `VIOLATIONS` result (exit 2). The scored finding
  records manifest lifecycle provenance (`manifest_ref.status` /
  `manifest_ref.invalidated`); the invalidation *reason* is never surfaced.
- **Explicit unimplemented stubs**: the contract/observability/coding-discipline/
  change-footprint rules are registered but report `UNIMPLEMENTED` — they can never
  report PASS until built.
- **CLI** (`src/cli.ts`): out-of-band runner; `npm run oracle:test` runs the Jest
  suite; `npm run oracle:typecheck` type-checks the oracle in isolation.

## Fixtures and tests

`fixtures/` holds synthetic `.ts.fixture` snapshots (materialized to a temp dir at
test time so the repo-wide `tsc` never compiles deliberately-broken code); `tests/`
holds the Jest suites. See `fixtures/README.md`.

`tests/scopeAttribution.test.ts` is the end-to-end **scoring mutation corpus**
(**M0–M8**). It builds both the snapshot and a *synthetic frozen manifest* in the
test process — no repository manifest is altered or frozen — and runs
`evaluateSnapshot` all the way through scoring, so the attribution semantics above
are regression-locked rather than only asserted in prose. **M0–M7** cover
scope-based attribution (new/moved files, anchor deletion, one-decision-one-
violation, invariant denominator); **M8-A–M8-F** cover production-source scoring
(a production violation still detected; the same prohibited import in a
`*.spec.ts`, under `__tests__/`, or in `jest.config.ts` never violates the
production opportunity; a conforming production file with a forbidden test-only
dependency stays `SATISFIED`; a forbidden production dependency surrounded by
harmless test dependencies violates exactly once).

## What is NOT built here

The **task-acceptance oracle** (per-task behavioural checks / hidden acceptance
tests), the labelled/mutation validation corpus, and the manual inter-rater
validation are future work — see `docs/v2/ORACLE_VALIDATION_REQUIREMENTS.md` (gates
G1/G6; `TD-B04`, `TD-B05`, `TD-B12`). Do not commit run outputs or task-specific
answers here.
