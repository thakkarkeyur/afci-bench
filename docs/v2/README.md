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
- [`DEPENDENCY_TASK_FEASIBILITY.md`](DEPENDENCY_TASK_FEASIBILITY.md) — which
  dependency decisions the canonical substrate can actually be made to **create**,
  the demonstrated ceiling, and the declared substrate-expansion alternative.
- [`CONDITION_PARITY_POLICY.md`](CONDITION_PARITY_POLICY.md) +
  [`CONDITION_CONTENT_MATRIX.csv`](CONDITION_CONTENT_MATRIX.csv) — condition parity.
- [`ORACLE_VALIDATION_REQUIREMENTS.md`](ORACLE_VALIDATION_REQUIREMENTS.md) — oracle
  validity bar.
- [`PILOT_AND_POWER_POLICY.md`](PILOT_AND_POWER_POLICY.md) — staged pilot and
  mandatory interaction-focused power simulation.

### Pilot task candidates (repaired after independent public review)

- [`experiments/v2/tasks/public/`](../../experiments/v2/tasks/public/) — seven
  primary (`PT01`–`PT07`, of which `PT07` was authored later under `DECISION B`)
  and two reserve (`PR01`–`PR02`) **public functional
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
- **Status:** candidates authored, repaired, amended, clarified and **classified for
  analysis eligibility**, **not approved and not frozen**.
  Task-specific oracle validity, hidden-acceptance validation, reset-checkpoint
  review, and benchmark discrimination remain open; gates **G1/G2 not passed**;
  the protocol remains **PRE-FREEZE**; **no pilot model execution occurred** and
  **no final task count**, repetition count, run count or numerical budget was
  selected. The **nine** candidates — seven primary `PT01`–`PT07`, two reserve
  `PR01`/`PR02` — are candidates, not a core-study task set.

### Suite classification — the confirmatory construct is NARROW

An independently approved suite-level decision narrowed the confirmatory construct
to **layered dependency-direction conformance**. **No task body, task content
hash, manifest, endpoint or protocol was frozen or edited by that decision**, and
`apps/`/`libs/` are unchanged.

- **E1 is renamed** *"dependency-direction violation rate per applicable frozen
  opportunity"*. Numerator
  `opportunity_accounting.violated_opportunity_count`; denominator/offset
  `opportunity_accounting.applicable_opportunity_count`. **`applicable_rule_count`
  is not an admissible offset**, **stub rules do not enlarge the denominator**, and
  `raw_violation_count` is a **separate descriptive diagnostic**
  ([`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md) §2.1).
- **E1 does NOT directly measure** contract ownership, port/interface placement,
  observability completeness, duplicated logic, or general business-logic
  placement. Those are **CON-ACB** — pre-registered **secondary / manual**
  evidence whose confirmatory use requires blinded double rating with **Cohen's
  κ ≥ 0.70** ([`MANUAL_RATING_PROTOCOL.md`](MANUAL_RATING_PROTOCOL.md)).
  **The paper must not describe E1 as broad or general architectural
  conformance** (gate **G8**).
- **Analysis eligibility is explicit and machine-checked**
  ([`PILOT_PUBLIC_TASK_MATRIX.csv`](PILOT_PUBLIC_TASK_MATRIX.csv),
  `experiments/v2/tasks/public/TASK_INDEX.csv`, field
  `e1_analysis_eligibility`): **`PT01`–`PT04` `scored`** (joined later by
  **`PT07`**, authored under `DECISION B` — see below), **`PT05` and `PT06`
  `functional-only`** (valid primary functional candidates, structurally excluded
  from E1, still contributing to hidden functional acceptance, cost,
  reset-related functional outcomes and exploratory analyses — **not** failed
  runs), **`PR01`/`PR02` `inactive-reserve`**. Primary/reserve classification is
  unchanged. **No reserve was activated**, and **`PR02` must not be promoted**
  because its terminal-state guard is not externally reachable through the current
  public interface (`TD-B26`).
- **`PT05` was reclassified `scored` → `functional-only` before any run.** An
  independent pre-authoring opportunity reassessment found that its required
  functional work creates **no currently scored dependency-direction
  opportunity**. This is a **construct/feasibility** reclassification, decided
  from the task body and the substrate; it is **not** a model outcome and `PT05`
  is never reported as zero violations, failed, missing, invalid or a refusal. Its
  body, hash and `primary` kind are unchanged.
- A task whose `applicable_opportunity_count` is **0** is **structurally
  ineligible** for E1 — never coded as zero violations.
- **Reset is an experimental factor crossed with tasks, not a task-content
  category** ([`RESET_PROTOCOL.md`](RESET_PROTOCOL.md) §6). No candidate uniquely
  provides "reset-continuation coverage", multiple retained primary tasks already
  admit condition-neutral checkpoints, and `PT06` must not stay in E1 to satisfy a
  bookkeeping reset label. `RESET_CHECKPOINT_MATRIX.csv` now carries a **withheld**
  row for each candidate (eight at the time, nine since `PT07` was authored).
- **Eleven blockers were opened, none closed** — `TD-B23`–`TD-B33`
  ([`OPEN_DECISIONS.md`](OPEN_DECISIONS.md)): architecture-revealing model-visible
  source comments and their floor-effect risk; the leakage sweep not scanning
  source comments; `PT03`'s contradictory repeat-request contract; `PR02`'s
  unreachable terminal state; exact-path opportunity attribution missing
  violations in new files; `AR-DEP-001` coverage across private manifests;
  a private opportunity needing re-justification; pseudo-replication of shared
  boundary decisions; suite-wide public-interface reachability validation;
  `draft_unvalidated` hidden evaluator scaffolds; and broadening E1 as future work.
  *(Status superseded: the first two — `TD-B23` and `TD-B24` — were resolved by the
  later remediation described below. The other nine remain open.)*

### Opportunity reassessment — `PT05` reclassified, DECISION B recorded

An independent **pre-authoring, pre-run** reassessment of the active architecture
set. It changed **no** task body and **no** task hash, activated **no** reserve,
authored **no** task, ran **no** benchmark, and froze **nothing**.

- **`PT05` → `functional-only`** (see above). Functionally valid; structurally
  ineligible for E1 because its required functional work creates no currently
  scored dependency-direction opportunity.
- **Aggregate construct coverage (suite level only; no private content
  published).** `PT01`–`PT04` remain E1-scored candidates; `PT05`/`PT06` are
  `functional-only`; `PR01`/`PR02` remain inactive. **The current active task set
  does not provide enough distinct dependency-direction decisions for confirmatory
  inference** — the active opportunities exercise too few **distinct dependency
  boundaries**, and repeated tasks over one boundary are **not** independent
  architecture constructs.
- **DECISION B — additional public architecture tasks are required before
  Stage 0** (`TD-B34`). New candidates must exercise genuinely different existing
  dependency-direction **leaf rules and source/target boundaries**. The motivation
  is **construct validity**; the deficiency is **task-set coverage, not an oracle
  failure**; the repaired scope-based oracle **remains** the approved attribution
  mechanism; and **no new rule family is required**, because unused implemented
  dependency leaf relationships already exist. `TD-B34` stays **open and
  blocking**; **G1**, **G2** and **G6** remain **not passed** and the suite is
  **not** ready.
- **Production-source scoring (P0 repair).** E1 is computed from the **production
  dependency graph** only: `*.spec.ts` / `*.test.ts`, `__tests__/`, test support
  material and tooling/config TypeScript such as `jest.config.ts` are partitioned
  into a separate **excluded test/config/support graph** before any import edge is
  built. Excluded edges never enter E1's numerator, and because the denominator is
  the **frozen opportunity count**, adding or deleting test files cannot move
  either side. The frozen architectural layer scopes are **unchanged**
  ([`ORACLE_VALIDATION_REQUIREMENTS.md`](ORACLE_VALIDATION_REQUIREMENTS.md) §1b;
  mutation cases **M8-A**–**M8-F**).
- **Statistical governance.** The then-current four-task architecture set
  (`PT01`–`PT04`; now five scored candidates over three decision clusters — see
  the remaining-leaf feasibility section below) is **not**
  confirmatory-ready. Repeated exposures to one boundary are **clustered**; task
  count ≠ independent architecture-decision count; the final power simulation runs
  **only after** additional distinct decisions are authored and approved; the
  analysis artifact will need a **decision/boundary cluster identifier**; and **no
  final power value is frozen now** (`TD-B37`; no power simulation was run here).
- **Four further blockers opened, none closed** — `TD-B34`–`TD-B37`. The registry
  now holds **37 blocking + 6 non-blocking** decisions, **all open**.
  *(Superseded on status only: `TD-B23` and `TD-B24` were subsequently resolved by
  the baseline architecture-coaching remediation below. The other 41 remain open.)*

### Baseline architecture coaching removed — `TD-B23`/`TD-B24` resolved

A **pre-authoring, pre-run** substrate remediation, done because the next public
architecture tasks would score exactly the boundaries the substrate was teaching.
It authored **no** task, changed **no** task body or hash, activated **no**
reserve, ran **no** benchmark or model, and froze **nothing**.

- **The disclosure is gone.** Model-visible source comments stated scored
  dependency rules to **every** condition, including the no-guidance C1 baseline:
  `apps/api/src/app.ts` stated the `api → core` prohibition, named the
  architecture-CI consequence and carried a worked commented-out forbidden import;
  `libs/infra/src/index.ts` justified avoiding `core` as "a deliberate
  architectural choice"; `libs/features/src/index.ts` restated the same
  prohibition from the `features` side. Six comment lines in three files, removed
  or rewritten in neutral implementation terms.
- **Comment-only, and proven so.** Identical emitted JS with comments stripped,
  identical AST fingerprint and an identical import/export edge list in all three
  files. The substrate was **re-identified, not re-designed**:
  [`SOURCE_SUBSTRATE_IDENTITY.md`](SOURCE_SUBSTRATE_IDENTITY.md) records the old
  and new identities and the equivalence proof.
- **Structural signals deliberately remain.** Folder names, `scope:*` tags,
  `@afci-bench/*` aliases, the import edges and every behaviour-describing comment
  stay visible — C1 may still *infer* the architecture from the code, which is the
  D3 signal the design measures. What it may no longer do is **read the answer in
  prose**. C3/C4 still receive the controlled treatment through their own channels.
- **The audit can now see it.** The leakage sweep reads source **content**, not
  just file names, and refuses a snapshot with `ARCHITECTURE_COMMENT_DISCLOSURE`
  when a comment states a rule. It is deliberately narrow: a prohibition counts
  only when paired with a named layer, so ordinary implementation prose passes.
  Positive **and** negative regression cases exist, including the **verbatim**
  pre-remediation bytes ([`../../experiments/v2/leakage_fixtures/`](../../experiments/v2/leakage_fixtures/)).
- **No architecture mechanism was removed.** The root `.eslintrc.json`
  `depConstraints` are untouched, and `api → core`, `infra → core` and
  `features → infra` were each re-probed and are still reported by
  `@nx/enforce-module-boundaries`.
- **Two blockers resolved, 41 still open.** `TD-B23` (disposition: **neutralise**,
  not pre-register) and `TD-B24`. Every task-authoring blocker — `TD-B34`
  (DECISION B), `TD-B26`, `TD-B31` — and runner-time enforcement (`TD-B22`) stay
  **open**, and the suite is **not** ready.

### Functional acceptance observation boundary — `TD-B39`/`TD-B40` opened

A **pre-authoring, pre-run** governance package closing the two conditions that had
to be settled before the next architecture candidate could be authored. It authored
**no** task, changed **no** task body or hash, changed **no** eligibility, touched
**no** file under `apps/`/`libs/`, activated **no** reserve, migrated **no** private
manifest, ran **no** benchmark or model, and froze **nothing**. The private
evaluator repository was inspected read-only and **not modified**; the canonical
substrate is still `630d3180`.

- **What a hidden acceptance test may look at is now fixed suite-wide**
  ([`HIDDEN_EVALUATOR_BOUNDARY.md`](HIDDEN_EVALUATOR_BOUNDARY.md) §9–§14): *externally
  observable functional acceptance through HTTP plus explicitly declared
  task-relevant application seams*. HTTP is the **default** surface; a declared seam
  is exceptional, must be **grounded in the public task** and **declared before**
  hidden tests exist; hidden acceptance may **not** read implementation-specific
  persistence, module state, classes, files or architecture findings, and may **not**
  seed state through implementation modules; a conforming implementation with a
  different internal design must remain **gradeable**; test isolation is **never** an
  acceptance oracle; and the two scoring channels stay **separated**.
- **It is deliberately not called "HTTP-only".** `PT04` requires structured log
  records — an externally *emitted* behaviour no HTTP response carries — so exactly
  **one** seam is declared suite-wide: the `LogOutput` sink on the application's
  publicly declared dependency surface. Internal persistence state is **not** a seam
  and may never be declared as one.
- **`resetOrderRepository()` is reclassified as legacy baseline-test
  infrastructure**, not an approved evaluator mechanism. It couples the evaluator to
  one implementation twice over — the symbol need not survive a conforming change,
  and even where it does its effect depends on when the application was constructed.
  The normative isolation method is a **freshly constructed application over a
  freshly evaluated module graph**. The substrate keeps the helper untouched.
- **Boundary audit of the candidates.** `PT01`–`PT03`, `PT05`, `PT06` and
  `PR01` are gradeable through **HTTP alone** (as is `PT07`, audited when it was
  authored); `PT04` needs HTTP **plus the one
  declared seam**; **`PR02` is blocked** — its terminal-state precondition is
  unreachable through the public interface (`TD-B26`) and the boundary forecloses the
  only workaround, so it makes `TD-B26` **stricter**, not softer. No task contract was
  amended.
- **Active-coverage correction (`TD-B40`).** The preservation-only opportunities the
  reassessment ordered removed are **still physically present** in the stale private
  manifests and are **analytically inactive**; counting them overstates coverage.
  Suite-level consequence, no private identifier disclosed: every retained active
  dependency decision sits in **one source scope** under **one leaf rule**, spanning
  only **two** distinct clusters (`source_scope + forbidden_target + leaf_rule`), so
  the **`api`** source scope and the **`AR-DEP-005`** (`api → core`) leaf rule are
  **currently unrepresented**. Same construct-validity deficiency as `TD-B34`; not an
  oracle failure.
- **One candidate cleared, none authored.** A candidate using a currently
  unrepresented implemented dependency leaf **and** source scope passed pre-authoring
  feasibility review, and is gradeable through HTTP alone. **No task body was
  authored**; its opportunity details stay private until the normal evaluator package
  is created. `TD-B34` stays **open and blocking** — one cleared candidate is not a
  suite — and **G1/G2/G6** remain **not passed**.
- **Two blockers opened, none closed** — `TD-B39` (migrate the hidden acceptance
  packages onto the boundary) and `TD-B40`. The registry now holds **40 blocking +
  6 non-blocking** decisions, **43 open**.

### `PT07` authored under `DECISION B` — one task, `TD-B34` still open

The candidate cleared above is now a public task body. This package authored
**exactly one** task and nothing else: **no** other task body or hash changed,
**no** other eligibility changed, **no** file under `apps/`/`libs/` was touched,
**no** reserve was activated, **no** private evaluator material was authored or
modified, **no** benchmark or model ran, **no** result artifact was produced and
**nothing** was frozen. The private evaluator repository was **not accessed**. The
canonical substrate is still `630d3180` / `0198d76c…`, and the protocol remains
**PRE-FREEZE**.

- **`PT07` — *Price a proposed order before it is placed***
  (`pricing-endpoint`, `primary`, `e1_analysis_eligibility` `scored`,
  `task_status` `candidate`, SHA-256 `557caed09420354e…`). A caller can price a
  proposed set of line items through a new request and get back each item's
  subtotal and the total, agreeing numerically with what the existing
  order-creation operation already reports for the same line items. The body is
  functional-only and the leakage validator reports **OK** for it, unmodified.
- **Authored before any run, from an independently reviewed candidate.** Its
  design and public-interface feasibility were reviewed against the eleven
  authoring requirements and the observation boundary **before** it was written;
  no experimental result exists, so nothing about it could have been chosen from an
  outcome.
- **Aggregate coverage only.** In aggregate terms it adds a **previously
  unrepresented implemented leaf/source-scope candidate**. Which leaf rule, source
  scope and forbidden target its decision uses stay **private** — no public
  artifact maps `PT07` to a rule id, an opportunity, or an expected or prohibited
  area, and `EM-PT07` is a **reserved identifier only**.
- **Gradeable through HTTP alone.** No declared seam (its text states log output is
  not part of its required behaviour), no repository-state observation, no reset
  helper, no seeded state, no implementation-specific import, no architecture
  finding. A **non-persistence criterion was rejected as externally ungradeable**:
  the substrate exposes no public way to observe stored state. `PT07` requires the
  observable consequence instead — its answer carries no `id`, `status`,
  `createdAt` or `customerId`. **The absent response fields are required; a hidden
  persistence side-effect assertion is not.**
- **Overlap safeguards recorded as governance, not as hints.** No new discount rule
  (`PT05`); no cent-exactness requirement and no implicit rounding fix (`PR01`);
  malformed JSON / 413 / 415 / body-parser behaviour explicitly outside it
  (`PT06`); no order read, list or count surface (`PT01`/`PT02`); logging outside it
  (`PT04`). Details in
  [`TASK_AUTHORING_REPORT.md`](../../experiments/v2/tasks/public/TASK_AUTHORING_REPORT.md).
- **`TD-B34` is NOT resolved.** One task is neither the breadth nor the repetition
  the confirmatory construct needs; the active set plus `PT07` still does **not**
  sample enough distinct dependency-direction decisions. **Further candidate
  authoring is still required before Stage 0**, **no power simulation may run yet**
  (`TD-B37`), gates **G1/G2/G6** remain **not passed**, and the suite is **not**
  ready. `PT07` cannot enter E1 until a private evaluator package is authored,
  validated, approved and shown to carry a valid non-zero frozen opportunity set
  (`TD-B05`/`TD-B14`, `G1`); its `scored` eligibility records **intent**, never a
  demonstrated denominator.
- **No blocker was opened or closed.** The registry still holds **40 blocking + 6
  non-blocking** decisions, **43 open**.

### Remaining-leaf feasibility — `TD-B34` re-scoped to replication depth

A **pre-authoring, pre-run** governance package. It authored **no** task, changed
**no** task body, hash or eligibility, touched **no** file under `apps/`/`libs/`,
activated **no** reserve, accessed **no** private evaluator material, ran **no**
benchmark, model or power simulation, and froze **nothing**. The canonical
substrate is still `630d3180` / `0198d76c…` and the protocol remains
**PRE-FREEZE**.

- **The remaining implemented leaves were assessed and are not task-creatable
  here.** `AR-DEP-002` (`contracts`), `AR-DEP-003` (`core`) and `AR-DEP-004`
  (`infra`) are **theoretically detectable but NOT task-creatable on the current
  substrate**: `contracts` is type-only and erased at runtime, `core` is pure and
  self-sufficient so nothing architecture-neutral can force placement there, and
  `infra`-shaped work can be satisfied at `api` level under the current
  observation topology. Reasons are recorded normatively in
  [`DEPENDENCY_TASK_FEASIBILITY.md`](DEPENDENCY_TASK_FEASIBILITY.md).
- **The substrate has a hard ceiling of 3 decision clusters / 2 leaf rules / 2
  source scopes / 3 forbidden targets**, and **all three achievable clusters are
  already represented** — `features → infra` (3 observations), `features → api`
  (1) and `api → core` (1), from **5** adjudicated active E1 opportunities. The
  remaining deficiency is **replication depth and balance**, not breadth.
- **`TD-B34` is re-scoped, not resolved.** It now governs adequate coverage of the
  **complete task-creatable decision space**: retain all three clusters, add
  independent instruments to the two **singletons** where scientifically feasible
  (priority **A** `features → api`, then **B** `api → core`), author **no**
  artificial task merely to reach a mechanically implemented leaf, record the
  ceiling as a **construct-validity limitation**, and defer broader generalisation
  to a declared substrate redesign. **No new task body was specified** and it is
  **not** asserted that two suitable candidates exist. It stays **open and
  blocking**; **G1/G2/G6** remain **not passed**.
- **Substrate redesign is a DECLARED ALTERNATIVE — NOT SELECTED**, with its full
  cost recorded (new substrate identity, renewed leakage review, C1–C4 equivalence
  re-validation, task-feasibility re-validation, public linkage review, private
  relink/migration, renewed opportunity review). The choice stays with the Study
  Lead.
- **The 15 theoretical `(source scope, forbidden target)` pairs are now annotated**
  with feasibility status wherever they are tabulated, so **mechanically detectable
  is never read as task-creatable**; and the **`observability` source scope is
  documented as umbrella-only** — `leafRuleFor('observability', …)` returns `null`,
  so such an edge can never back a scored opportunity. **No oracle behaviour
  changed.**
- **E1's claim is tightened, not broadened.** Observed E1 effects generalise
  directly to the **represented** dependency-decision families, **not**
  automatically to all architecture rules or all layer pairs
  ([`RESEARCH_QUESTIONS.md`](RESEARCH_QUESTIONS.md) CON-AC;
  [`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md) §2.2).
- **The G = 3 analysis problem is settled before any power work.** Because the
  cluster count is fixed at three, `decision_cluster_id` enters as a **FIXED
  factor** and **no cluster random-intercept variance is estimated from three
  clusters**; condition effects stay the inferential target and are identified
  **within** clusters; opportunities and runs stay nested observations; and the
  sensitivity programme is **CR2/CR3 with Satterthwaite df where the tooling
  supports it reliably**, plus **within-block randomisation inference**,
  **leave-one-cluster-out** refits and a pseudo-replication check (§4b). The
  residual specification that needs the runner data shape is the new blocker
  **`TD-B41`**, with its permitted options enumerated.
- **`TD-B37` stays blocked** behind four explicit preconditions, and `TD-B30` now
  names `decision_cluster_id` as the governing identifier. **No power value was
  produced.**
- **One blocker opened, none closed.** The registry now holds **41 blocking + 6
  non-blocking** decisions, **44 open**.

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
  definitions: **CON-AC** (layered dependency-direction conformance — the
  directly measured confirmatory construct), **CON-ACB** (broader architectural
  conformance, **not** directly measured by E1), and **CON-AI** (architectural
  integrity — not directly measured at all).
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
  per-candidate view (id, title, functional category, primary/reserve,
  **`e1_analysis_eligibility`** and its reason, public task hash, visible
  CI command, scope, leakage-validation status); carries no hidden answer.
- [`MODEL_REGISTRY.yml`](MODEL_REGISTRY.yml) /
  [`MODEL_REGISTRY.csv`](MODEL_REGISTRY.csv) — verified model info; no primary
  model selected.
- [`REVIEWER_RESPONSE_MATRIX.csv`](REVIEWER_RESPONSE_MATRIX.csv),
  [`PILOT_GATE_MATRIX.csv`](PILOT_GATE_MATRIX.csv) — reviewer concerns and gates
  G1–G8 (none passed).
- [`RUN_ARTIFACT_MATRIX.csv`](RUN_ARTIFACT_MATRIX.csv) — per-run artifacts and
  their schemas (`experiments/v2/schemas/`).

Direct **dependency-direction-conformance** (v1's guard was non-functional; see
`archive/v1/REFERENCE_MANIFEST.yml`) and **task-acceptance** measurement models
are defined by the oracle/guard schemas in
[`experiments/v2/schemas/`](../../experiments/v2/schemas/) and validated by the
tests in `experiments/v2/harness/tests/`.

Nothing here references or regenerates v1 results. Cross-reference v1 only via the
pointers in [`archive/v1/`](../../archive/v1/README.md).
