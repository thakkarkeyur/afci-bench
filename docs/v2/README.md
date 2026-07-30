# docs/v2 — Study v2 Design Documentation

Design and methodology documents for **AFCI-Bench study v2**.

This directory holds the v2 study design as it is written: the research
questions, the measurement model, threats-to-validity analysis, the v2 protocol,
and the architecture-conformance rule specification. It is the v2 counterpart to
the v0 documents on `main` (`docs/MAD_v0.md`, `docs/PROMPT_PACK_v0.md`,
`docs/ARCH_RULES.yml`), which remain immutable.

## Status: PRE-FREEZE DRAFT (not scientifically frozen)

The previous commit (`b23409f`) described this protocol as "frozen". That was
premature. Following the external **pre-execution scientific-design review**, the
protocol is reclassified:

- The existing protocol is a **pre-freeze draft**.
- It is **structurally complete but NOT scientifically frozen**: mandatory
  scientific decisions remain unresolved (see
  [`CRITICAL_DESIGN_DECISIONS.md`](CRITICAL_DESIGN_DECISIONS.md) and
  [`OPEN_DECISIONS.md`](OPEN_DECISIONS.md)).
- **Scientific freeze occurs only after** this reconciliation is **independently
  approved** *and* the relevant **blocking decisions are closed**.
- **No `protocol-freeze` tag currently exists**, and none is created by this work
  package.

It authorizes **no** paid model run, freezes **no** final benchmark /
model-execution configuration and **no** task / repetition / run count, and uses
**no** v1 result to choose any threshold, power input, or effect size. Unresolved
decisions are tracked as explicit blockers in
[`OPEN_DECISIONS.md`](OPEN_DECISIONS.md); binding design decisions are recorded in
[`CRITICAL_DESIGN_DECISIONS.md`](CRITICAL_DESIGN_DECISIONS.md).

### Pre-execution design-review reconciliation (this work package)

- [`CRITICAL_DESIGN_DECISIONS.md`](CRITICAL_DESIGN_DECISIONS.md) — binding design
  decisions D1–D13 (v1 use, task wording, C3≈C4, content parity, reset, primary
  endpoint, hypothesis hierarchy, model screening, environment, study size).
- [`EXPERIMENTAL_CI_POLICY.md`](EXPERIMENTAL_CI_POLICY.md) — the agent-visible CI
  (`npm run ci:agent`) vs repository validation (`npm run ci`).
- [`TASK_AUTHORING_POLICY.md`](TASK_AUTHORING_POLICY.md) +
  [`TASK_LEAKAGE_TERMS.yml`](TASK_LEAKAGE_TERMS.yml) — public-task leakage policy.
- [`CONDITION_PARITY_POLICY.md`](CONDITION_PARITY_POLICY.md) +
  [`CONDITION_CONTENT_MATRIX.csv`](CONDITION_CONTENT_MATRIX.csv) — condition parity.
- [`ORACLE_VALIDATION_REQUIREMENTS.md`](ORACLE_VALIDATION_REQUIREMENTS.md) — oracle
  validity bar.
- [`PILOT_AND_POWER_POLICY.md`](PILOT_AND_POWER_POLICY.md) — staged pilot and
  mandatory interaction-focused power simulation.

### Pilot task candidates (repaired after independent public review)

- [`experiments/v2/tasks/public/`](../../experiments/v2/tasks/public/) — six
  primary (`PT01`–`PT06`) and two reserve (`PR01`–`PR02`) **public functional
  task bodies**, plus `TASK_INDEX.csv`, `TASK_SCHEMA.yml`,
  `TASK_AUTHORING_REPORT.md`, and the front-matter schema
  [`public_task.schema.json`](../../experiments/v2/schemas/public_task.schema.json).
  Each body states functional requirements and observable behaviour only; the
  public-task leakage validator reports OK for all (partial advance on `TD-B17`).
- **Repairs.** An independent review found four task defects that would have
  invalidated the evidence — `PT06` was impossible against the frozen base, `PT04`
  was partly unsatisfiable, and `PT02`/`PT03` left their JSON wire formats
  undefined — plus two fairness gaps (unpinned `error` values; `PR01`'s worked
  example already satisfied at the base). All are repaired; `PT04` and `PT06` were
  rewritten onto behaviour that exists at the base. **Seven of the eight task
  hashes changed** (only `PT05` is unchanged). Every response key, request key,
  status code and pinned `error` value is now stated publicly, so no hidden test
  can enforce an unstated string. Details:
  [`TASK_AUTHORING_REPORT.md`](../../experiments/v2/tasks/public/TASK_AUTHORING_REPORT.md).
- **`PT06` amendment — every required behaviour is now externally testable.** The
  repaired `PT06` still required one behaviour no external caller can provoke at the
  base: a failure that is *not* caused by invalid input, answered HTTP 500 with
  `error` `InternalServerError`. Validating it would have needed a failure-injection
  hook, test-only route, special header or environment flag in the shared source
  substrate — a seam that is itself a design answer. `PT06` is re-scoped to the
  rejection envelope of `POST /orders` (new title: *Return a consistent
  validation-error envelope for order creation*): the existing semantic-validation
  failures and a body that cannot be parsed as JSON must answer the **same** HTTP 400
  body `{ "error": "ValidationError", "message", "correlationId" }`, and success is
  unchanged. Three existing validation rules are named publicly (empty `customerId`,
  empty `items`, non-positive `quantity`); no new domain rule was invented. The base
  answers an unparseable body 400 **as HTML** with none of those keys, so the task
  needs a genuine change and is not already satisfied — machine-checked by
  [`test_pt06_feasibility.py`](../../experiments/v2/harness/tests/test_pt06_feasibility.py).
  **Only `PT06`'s hash changed** (`3994a158…` → `ae87303c…`); `apps/` and `libs/` are
  byte-identical, and no candidate requires an HTTP 500 response any more.
- **`PT06` rejection-contract clarification — the contract is now fully determined.**
  An independent review of the amendment found two places where `PT06`'s text left a
  conforming solution able to satisfy every stated criterion and still fail
  acceptance. Both are closed. (1) **Response media type stated, not implied:** "the
  body is JSON" constrained the payload, not the declared media type, so a serialised
  envelope sent under `text/html` conformed to the letter while failing any check that
  reads the response as JSON. `PT06` now requires a `Content-Type` response header
  whose media type begins with `application/json` on both covered rejections, and
  states that **no other response header** is part of its required behaviour — which
  also stops a private test asserting `x-correlation-id`. (2) **Covered rejections
  bounded to exactly two kinds:** an unqualified "a rejected `POST /orders` request
  answers HTTP 400" was reachably false — the base answers an over-large body HTTP 413
  and an unsupported charset HTTP 415, both as HTML. `PT06` now names its two covered
  kinds in a **Scope** section (a semantic input-validation failure of a parsed body;
  a JSON parse failure sent as `application/json`) and states that HTTP 413, HTTP 415,
  aborted requests and every other transport-level or body-parsing rejection are
  **outside** its scope and keep their current status codes and bodies. The same
  bounded wording is used in its completion criteria. **Only `PT06`'s hash changed
  again** (`ae87303c…` → `3e0f84cf…`); `apps/` and `libs/` remain byte-identical, and
  no architecture wording, applicable rule, expected area or task-specific opportunity
  was added to any public artifact.
- **Hidden evaluator packages** for these candidates (per-task manifests, hidden
  acceptance plans, fixed opportunity sets, expected/prohibited areas, legitimate
  alternatives, reset predicates, threat reviews) exist **only in a separate
  local private evaluator repository**, never in this repository. Every manifest
  is status `review` (not frozen); the architecture oracle refuses to score it
  (`MANIFEST_NOT_FROZEN`).
- **The private evaluator commit built against the pre-repair hashes is STALE.** It
  **must not** be reviewed, approved, frozen, or used for Stage 0 or any pilot.
  Private manifests and hidden plans must be re-authored or re-linked against the new
  hashes **after** this public package is independently approved, and a private hash
  must never be silently accepted against a changed public task. The private
  repository was not accessed while producing this package, and its filesystem
  location appears in no public file.
- **The `PT06` amendment and clarification make one further private package stale —
  `PT06`'s only.** The private commit created against the public bytes of commit
  `0e77d49` (`5733ca6151f7739c7105a5c1405fcbc8fb3cb59d`) **must not be reviewed as a
  complete eight-task package** until `PT06` is updated; `PT06`'s package must be
  **substantively re-authored** (its subject matter changed again), and only after this
  public amendment and clarification are independently approved, so the hash it pins
  (`3e0f84cf…`) is the approved one. The seven other packages — `PT04` among them —
  remain linked to the public task bytes reviewed at `0e77d49`, which are
  byte-identical here, so neither change forces re-linking for them. They are still
  status `review`, still not frozen. The private repository was not accessed while
  producing this amendment or this clarification.
- **`PT06`'s architecture-opportunity adequacy is a private, deferred question.** The
  amendment reduced `PT06`'s novel work to a single error path, and its public
  feasibility evidence is functional only — deliberately, because a public task body
  must stay architecture-neutral. Whether the amended `PT06` still carries a non-empty
  fixed opportunity set is a **future private-evaluator blocker** under
  **TD-B05**/**TD-B14**, gated by **G1**. It is **not** a defect in `PT06`'s public
  text, and nothing was added publicly to address it; it must be demonstrated during
  the substantive private re-authoring of `PT06`'s package, before that package may be
  approved or frozen.
- **Status:** candidates authored, repaired, amended and clarified, **not approved and not frozen**.
  Task-specific oracle validity, hidden-acceptance validation, reset-checkpoint
  review, and benchmark discrimination remain open; gates **G1/G2 not passed**;
  the protocol remains **PRE-FREEZE**; **no pilot model execution occurred** and
  **no final task count**, repetition count, run count or numerical budget was
  selected. The eight candidates are candidates, not a core-study task set.

### Model-visible worktree isolation

- [`MODEL_VISIBLE_WORKTREE_POLICY.md`](MODEL_VISIBLE_WORKTREE_POLICY.md) +
  [`prepare_model_worktree.py`](../../experiments/v2/harness/prepare_model_worktree.py)
  — allowlist-first, fail-closed construction of the coding model's worktree. The
  same review found that the worktree was the whole repository, which put
  [`ARCHITECTURE_CONTEXT.md`](ARCHITECTURE_CONTEXT.md) and
  [`ARCHITECTURE_RULE_CATALOG.yml`](ARCHITECTURE_RULE_CATALOG.yml) inside **every**
  condition's workspace including the C1 baseline — a direct confound on the
  primary C4-vs-C1 contrast. The prepared snapshot now contains the source
  substrate only, keeps the implicit architectural clues (folder names, scope
  tags, path aliases, code, visible tests) and excludes every explicit
  architecture, protocol, oracle and evaluator artifact.
- **Runner-time enforcement does not exist** — the live runner does not exist
  (`TD-B02`). It is tracked as the new blocking decision **`TD-B22`**, and no run
  may be counted until it is closed.

Scientific protocol:

- [`RESEARCH_QUESTIONS.md`](RESEARCH_QUESTIONS.md) — RQ1–RQ4 and construct
  definitions (incl. architectural integrity as a broader, not-directly-measured
  construct).
- [`CONDITIONS.md`](CONDITIONS.md) + [`CONDITION_MATRIX.csv`](CONDITION_MATRIX.csv)
  — the four conditions C1–C4.
- [`RESET_PROTOCOL.md`](RESET_PROTOCOL.md) +
  [`RESET_CHECKPOINT_MATRIX.csv`](RESET_CHECKPOINT_MATRIX.csv) — controlled reset.
- [`FAILURE_RERUN_POLICY.md`](FAILURE_RERUN_POLICY.md) — rerun vs data.
- [`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md) — pre-registered
  endpoints (provisional).
- [`INDUSTRIAL_DATA_AUDIT.md`](INDUSTRIAL_DATA_AUDIT.md) — RQ4 feasibility.

Evidence matrices:

- [`CLAIMS_CONSTRUCTS_METRICS.csv`](CLAIMS_CONSTRUCTS_METRICS.csv) — claim ↔
  construct ↔ direct metric.
- [`TASK_RULE_MATRIX.csv`](TASK_RULE_MATRIX.csv),
  [`TASK_ACCEPTANCE_MATRIX.csv`](TASK_ACCEPTANCE_MATRIX.csv),
  [`TASK_LAYER_MATRIX.csv`](TASK_LAYER_MATRIX.csv),
  [`ORACLE_TRACEABILITY.csv`](ORACLE_TRACEABILITY.csv) — task/oracle templates
  plus **redacted** per-candidate rows: every task-specific hidden field is
  `stored_in_private_evaluator_repo`, never a real rule id, expected area, or
  hidden criterion.
- [`PILOT_PUBLIC_TASK_MATRIX.csv`](PILOT_PUBLIC_TASK_MATRIX.csv) — public
  per-candidate view (id, title, functional category, public task hash, visible
  CI command, scope, leakage-validation status); carries no hidden answer.
- [`MODEL_REGISTRY.yml`](MODEL_REGISTRY.yml) /
  [`MODEL_REGISTRY.csv`](MODEL_REGISTRY.csv) — verified model info; no primary
  model selected.
- [`REVIEWER_RESPONSE_MATRIX.csv`](REVIEWER_RESPONSE_MATRIX.csv),
  [`PILOT_GATE_MATRIX.csv`](PILOT_GATE_MATRIX.csv) — reviewer concerns and gates
  G1–G8 (none passed).
- [`RUN_ARTIFACT_MATRIX.csv`](RUN_ARTIFACT_MATRIX.csv) — per-run artifacts and
  their schemas (`experiments/v2/schemas/`).

Direct **architectural-conformance** (v1's guard was non-functional; see
`archive/v1/REFERENCE_MANIFEST.yml`) and **task-acceptance** measurement models
are defined by the oracle/guard schemas in
[`experiments/v2/schemas/`](../../experiments/v2/schemas/) and validated by the
tests in `experiments/v2/harness/tests/`.

Nothing here references or regenerates v1 results. Cross-reference v1 only via the
pointers in [`archive/v1/`](../../archive/v1/README.md).
