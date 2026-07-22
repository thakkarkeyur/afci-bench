# docs/v2 — Experimental Agent-Visible CI Policy

Status: **development policy for study v2**. Defines the **two distinct CI
surfaces** the study uses and why they differ. Development artifact only: it does
**not** freeze the final benchmark configuration and authorizes **no** paid model
run.

Mechanism: [`.eslintrc.agent.json`](../../.eslintrc.agent.json) (experimental
config), the `lint:agent` / `ci:agent` scripts in
[`package.json`](../../package.json), and the separation tests in
[`experiments/v2/harness/tests/test_experimental_ci_separation.py`](../../experiments/v2/harness/tests/test_experimental_ci_separation.py).
Binding decision context: [`CRITICAL_DESIGN_DECISIONS.md`](CRITICAL_DESIGN_DECISIONS.md)
(CI row / `TD-B16`).

---

## 1. Why two CI surfaces

The study measures whether a coding model, working under a given context
condition (C1–C4), produces architecture-conformant code. If the model could run
the repository's **architecture enforcement** (`@nx/enforce-module-boundaries`)
as part of its own edit-verify loop, it would receive the architecture answer as
tool feedback — collapsing the very outcome the oracle is meant to measure. The
same is true of the **hidden acceptance tests** and the **architecture-oracle
checks**: they are the measurement, so they must be invisible to the subject.

Therefore the study defines two CI surfaces:

| Surface | Command | Who sees it | Includes architecture enforcement? | Includes hidden checks? |
|---|---|---|---|---|
| **Repository validation** | `npm run ci` | maintainers / repo CI (`.github/workflows/ci.yml`) | **Yes** (`@nx/enforce-module-boundaries` = error) | n/a (hidden checks live outside the repo) |
| **Agent-visible CI** | `npm run ci:agent` | **the coding model only** | **No** | **No** |

- **`npm run ci:agent` is the only CI command exposed to the coding model.**
- **`npm run ci` is repository validation**, run by maintainers and repository
  CI — it is **not** agent feedback and is never part of a run's edit-verify loop.
- **Hidden acceptance tests and hidden architecture-oracle checks never run
  inside the coding model's workspace or feedback loop.** They are evaluated
  **after** the run, by the (future) evaluator, from a separate hidden location
  (see [`ORACLE_VALIDATION_REQUIREMENTS.md`](ORACLE_VALIDATION_REQUIREMENTS.md)).

## 2. What `npm run ci:agent` does and does not do

`ci:agent = lint:agent && typecheck && test`.

- **Type checking** — `tsc -p tsconfig.base.json --noEmit` (identical to normal CI).
- **Visible functional / unit tests** — `nx run-many --target=test --all`
  (the repository's own jest suites; these are legitimate, non-hidden tests the
  model is allowed to run).
- **Ordinary non-architecture lint** — `lint:agent` runs ESLint with
  `.eslintrc.agent.json`, which retains the ordinary TypeScript rules
  (`no-explicit-any`, `explicit-function-return-type`, `no-unused-vars`) and
  **only** turns off `@nx/enforce-module-boundaries`.
- **Excludes** `@nx/enforce-module-boundaries` (the architecture rule).
- **Excludes** all hidden acceptance and architecture-oracle checks (these are
  not npm scripts and are not present in the model's workspace).

`.eslintrc.agent.json` disables **only** the architecture rule; it is **not** a
blanket lint disable. The separation test proves an ordinary `no-explicit-any`
failure is still caught by `ci:agent`.

## 3. Normal CI is unchanged

`npm run ci`, the root `.eslintrc.json` (with `@nx/enforce-module-boundaries` at
`error`), every per-project `.eslintrc.json`, and `.github/workflows/ci.yml` are
**untouched**. Repository architecture enforcement is neither removed nor
weakened.

## 4. The controlled boundary-violating fixture

`experiments/v2/ci_fixtures/boundary_violation.ts.fixture` is a single
architecture-boundary violation (`scope:observability` importing
`@afci-bench/contracts`, forbidden by the root `depConstraints`). It is stored
with a `.ts.fixture` extension so **no** normal tool touches it, which is why it
does not break `npm run ci`. The separation test materializes it into a tagged
library source directory, runs ESLint under both configs, and removes it again.

## 5. Validation (all automated in the separation test)

1. `npm run ci` continues to include architecture enforcement — the root config
   has `@nx/enforce-module-boundaries` at `error`; the `ci` script is unchanged.
2. `npm run ci:agent` excludes architecture enforcement — it runs `lint:agent`
   against `.eslintrc.agent.json`, where the rule is `off`.
3. The boundary-violating fixture is **not** rejected by `ci:agent` for
   architectural reasons (no `@nx/enforce-module-boundaries` finding under the
   agent config).
4. The same fixture **is** detectable by the normal architecture configuration
   (a `@nx/enforce-module-boundaries` finding under the normal config) — the
   dedicated validation test asserts this.
5. Normal type/test/lint failures are still caught by `ci:agent` — the agent
   config still reports `@typescript-eslint/no-explicit-any`.

## 6. This is a measurement choice, not a recommendation

**Disabling architecture enforcement in `ci:agent` is a benchmark-measurement
choice: it prevents the subject from reading the outcome we are measuring.** It
is **not** a recommendation that production teams disable architecture
enforcement. In production, `@nx/enforce-module-boundaries` (and the equivalent
in any repository) should stay **on** — that is exactly the value the study is
investigating. Repository CI (`npm run ci`) keeps it on for this repository.

## 7. Open blocker

The **mechanism** here (two CI surfaces, agent config, fixture, tests) is
delivered and tested. What remains open is the **runner-time guarantee**: when
the future experimental runner exists, it must expose **only** `ci:agent` to the
coding model and ensure no hidden acceptance/oracle check ever enters the model's
workspace or feedback loop. That runner-time enforcement is blocking decision
**`TD-B16`** (depends on the runner, `TD-B02`).
