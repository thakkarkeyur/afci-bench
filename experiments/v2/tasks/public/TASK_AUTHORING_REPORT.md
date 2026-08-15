# AFCI-Bench v2 - Public Task Authoring Report

Status: **candidate** pilot task materials - authored, repaired, amended (PT06), clarified (PT06's rejection contract), and now **classified for analysis eligibility**, NOT approved, NOT frozen. The scientific protocol remains **PRE-FREEZE**. No benchmark run, paid model call, or task-count freeze accompanies this report.

The confirmatory construct is **narrow**: endpoint E1 is the **dependency-direction violation rate per applicable frozen opportunity** and measures **layered dependency-direction conformance only**. See *Coverage* below for the four distinct coverage categories and which single one E1 scores, and *Suite classification* for per-task eligibility.

## What was authored

- Six primary pilot task candidates (PT01-PT06) and two pre-declared reserve candidates (PR01-PR02).
- Each public task body states functional requirements and observable behaviour only; the single visible validation command is `npm run ci:agent`.
- Every hidden evaluator package for these candidates is stored **only** in a separate local private evaluator repository and is absent from this public repository.

## Coverage

The six primary candidates were selected, before any model outcome existed, to collectively span the pre-declared coverage areas recorded in the private selection policy and coverage matrix. The per-candidate coverage mapping is a hidden design detail and is withheld from this public report.

### Four coverage categories, only one of which E1 measures

"Coverage" was previously written as if it were a single property. It is not, and conflating the four categories below would over-state what the confirmatory endpoint measures. **Each category is distinct, and only category 4 is directly scored by E1.**

| # | Coverage category | What it means | Measured by |
| --- | --- | --- | --- |
| 1 | **Task subject-matter coverage** | the functional spread of the candidate suite (read endpoint, list endpoint, write endpoint, logging, calculation, error handling) | nothing automated - a selection property of the suite, asserted in the index/matrix and reviewable from the public bodies |
| 2 | **Hidden functional coverage** | which required behaviours the hidden acceptance tests exercise per task | E3, the hidden acceptance-test pass proportion (`CON-TC`) - **not** E1 |
| 3 | **Manual-rubric coverage** | which broader architecture dimensions a blinded rater adjudicates (contract ownership, port/interface placement, observability completeness, duplicated logic, general business-logic placement) | manual rubric under `CON-ACB`, secondary evidence only, confirmatory **only** at Cohen's kappa >= 0.70 - **not** E1 |
| 4 | **Directly scored E1 coverage** | which frozen dependency-direction opportunities the architecture oracle scores | **E1** - the dependency-direction violation rate per applicable frozen opportunity |

Correcting the record, since the earlier single-notion wording could be read as claiming that every category is directly measured by the primary endpoint:

- **Four of the six primary candidates currently remain E1-scored candidates.** `PT01`-`PT04` are `scored`; `PT05` and `PT06` are `functional-only` - valid primary functional candidates that are structurally excluded from E1 while still contributing to hidden functional acceptance, cost, reset-related functional outcomes and pre-registered exploratory analyses. `PR01` and `PR02` are `inactive-reserve` and contribute to no endpoint. **No reserve was activated** to restore the scored count.
- **All current scored E1 opportunities use dependency-direction rules** (the `AR-DEP-001..006` family). No contract-boundary, observability, coding-discipline or change-footprint rule is scored into E1: each is an unimplemented oracle stub that reports `UNIMPLEMENTED` and can never report PASS.
- **The opportunity instances reduce to a small number of repeated boundary decisions.** They are not independent observations; the same few layer-boundary judgements recur across tasks, so the power simulation must model that pseudo-replication (`TD-B30`).
- **The surviving active task set does not sample enough distinct dependency-direction decisions for confirmatory inference.** Repeated task exposures to the same source/target boundary are one architectural instrument observed several times, not several independent architecture constructs. Further public task authoring is required before Stage 0 (**DECISION B**, `TD-B34`); see *Opportunity reassessment* below.
- **Task count and final opportunity count remain unfrozen** (`TD-B10`/`TD-B14`/`TD-B20`, and `TD-B05`/`TD-B14` for the per-task opportunity sets). The eight candidates are candidates.
- **No statement here implies that categories 1-3 are directly measured by E1.** Subject-matter breadth, hidden functional coverage and manual-rubric coverage are separate evidence types with separate endpoints or no endpoint at all. **E1 must not be described as broad or general architectural conformance** (gate **G8**).

Per-candidate E1 eligibility is recorded publicly in `TASK_INDEX.csv` and `docs/v2/PILOT_PUBLIC_TASK_MATRIX.csv` (`e1_analysis_eligibility`). Which specific opportunities exist per task, and their contents, remain private: nothing in this section discloses a private opportunity answer or any exact private evaluator content.

## Repairs applied after independent public review

An independent review of the first authored suite found four task defects that would have invalidated the resulting evidence, plus two fairness gaps. All are repaired here. **Every repaired task body has a new SHA-256** (see the inventory below).

| Task | Defect found | Repair |
| --- | --- | --- |
| PT06 | **Impossible at the frozen base.** It asked to standardise not-found handling "across order endpoints" while forbidding new endpoints - but the base substrate has no endpoint that addresses an order by identifier and no 404 path at all, so no conforming solution existed. | **Rewritten** against the endpoint that does exist: `POST /orders`. Superseded by the PT06 amendment below, which removed the remaining externally untestable part of that rewrite. |
| PT04 | **Partly unsatisfiable.** It required log records for "any order-read endpoint" and for "a failing read", but the only read endpoint at the base is `GET /health`, which has no failure path. | **Rewritten** onto traffic that exists. New title: *Emit structured request and error logs for order creation*. It now targets `POST /orders` and names every asserted key: `correlationId`, `method`, `path`, `statusCode`, `status`, `operation`, `latencyMs` on the request record, and `correlationId`, `errorType`, `message` on the error record, which must carry no `stack` key. |
| PT02 | **Undefined response wire format.** "a JSON body containing the customer identifier, the array of matching orders, and the number of orders returned" named no keys, so a correct implementation could still fail on a guessed name. | Response body pinned to exactly `{ "customerId", "orders", "count" }`, with `count` equal to the number of elements in `orders`, the empty case pinned, and array order explicitly **not** part of the required behaviour (validation must be order-independent). |
| PT03 | **Undefined request wire format.** "a target status in its JSON body" named no key, so the grader could not even drive the endpoint. Its observability criterion ("visible on a later read") also had no read endpoint at the base. | Request body pinned to exactly `{ "status": "<value>" }`; the five accepted values are listed explicitly; every status code and `error` value is pinned; persistence is now observed by repeating the request, which needs no endpoint the task does not create. |
| PR01 | **Demonstrating example already passed.** Its only worked example (three items at 15.33 summing to 45.99) is already exact at the base and is already asserted by an existing visible test, so a model would see nothing to fix. | Example replaced with one that exposes the real defect: unit prices `0.10`, `0.10`, `0.70` return `0.8999999999999999` today and must return exactly `0.90`. |
| PR02 | Same unobservable "later fetch" criterion as PT03. | Persistence is now observed by repeating the (idempotent) cancel request. Error values pinned. |

## Error-contract values (binding on private evaluator packages)

Public tasks now state every response key, request key, status code and asserted `error` value, so no hidden test can enforce an unstated string. The pinned vocabulary is:

| Situation | HTTP status | `error` value |
| --- | --- | --- |
| Order not found | 404 | `NotFoundError` |
| Malformed or unknown input (including unparseable JSON) | 400 | `ValidationError` |
| Forbidden state transition | 409 | `ConflictError` |

No candidate pins an unexpected-server-failure status or `error` value any more: the
PT06 amendment below removed the only such requirement, because no external caller
can provoke that failure at the base substrate without an injection seam. A hidden
test may therefore not assert a 500 response for any candidate in this suite.

Binding constraints on every private evaluator package built for these candidates:

1. Where a task pins an `error` value, the hidden acceptance test asserts that exact string.
2. Where a task explicitly does **not** pin a value - the `errorType` of PT04's error-log record is the only such case in this suite - the hidden acceptance test may assert **only** that the value is a non-empty string. It may assert the HTTP status, the presence of a non-empty `error`, and the presence of a non-empty `message`, and nothing more.
3. `message` is free text everywhere; no hidden test may assert its wording.
4. `correlationId` remains present on every error body, exactly as the base substrate already returns it. A visible test in the repository asserts it, so removing it would break `npm run ci:agent`; the two documented failure keys are `error` and `message`.
5. Where a task states that ordering is not part of the required behaviour (PT02's `orders` array), hidden validation **must** be order-independent.
6. No hidden test may assert a key, string, status code or ordering that the public task body does not state.
7. No hidden test may assert a **response header** - its presence, its absence or its value - that the public task body does not state. Response headers were not enumerated in constraint 6, and a header is exactly as unstated-assertable as a body key; PT06's rejection-contract clarification below is the first task to state one explicitly.

## PT06 amendment: every required behaviour is externally testable

A further review of the repaired suite found that PT06 still required one behaviour
that **no external caller can provoke** against the unchanged source substrate: a
failure that is not caused by invalid input, answered with HTTP 500 and `error`
`InternalServerError`. At the base substrate the create-order path has no such
externally reachable failure. Validating it would have required a failure-injection
hook, a test-only route, a special header, an environment flag or another
implementation-specific seam in the source substrate - none of which exists, and
none of which may be introduced, because a seam authored for validation is itself a
design answer and would contaminate the substrate every condition shares.

PT06 is therefore re-scoped to behaviour that is reachable through the public
interface only. New title: *Return a consistent validation-error envelope for order
creation*. It still targets `POST /orders` and still asks for **one** rejection
envelope, but both of its failure kinds are now externally triggerable:

| Required behaviour | How an external caller triggers it | Status at the base |
| --- | --- | --- |
| HTTP 400 + `error` `ValidationError` + non-empty `message` + non-empty `correlationId` for input that fails the existing validation | send a create-order request with an empty `customerId`, an empty `items` array, or an `items` entry whose `quantity` is not positive | already the behaviour; must be preserved |
| The same HTTP 400 body for a body that cannot be parsed as JSON | send an unparseable body with `Content-Type: application/json` | answered 400, but as an HTML error page with none of the three keys - this is the change the task requires |
| HTTP 201 and the existing response body on success | send a valid create-order request | already the behaviour; must be preserved |

The removed HTTP 500 requirement is **not** replaced by an internal-failure
requirement of any other kind. No private test may induce a storage, logging or
other internal failure to grade PT06, and no private test may assert a 500 response.

Three concrete semantic-invalid cases are named publicly, all of them existing
validation rules of the current create-order input - no new domain rule was invented
to create a test case:

1. `customerId` present but empty (`""`), with an otherwise valid `items` entry.
2. `items` present but empty (`[]`), with an otherwise valid `customerId`.
3. An `items` entry whose `quantity` is not a positive number (for example `0`).

Feasibility was verified against the unchanged substrate rather than assumed, in two
ways.

**A committed static contract test**,
`experiments/v2/harness/tests/test_pt06_feasibility.py`, asserts the substrate
preconditions that make each required behaviour externally reachable: `POST /orders`
is registered; JSON body parsing is enabled for it, so an unparseable body is
externally submittable; the three semantic-invalid cases above are existing
validation rules, each reachable from the create-order input; the create-order
rejection path builds the three-key envelope with `error` `ValidationError` and HTTP
400; the success path answers HTTP 201; **no** JSON-parse-failure branch and **no**
response-shaping error handler exist yet, so the unparseable-JSON body cannot yet
receive that envelope and the task therefore requires a genuine implementation
change; and neither PT06's text nor the substrate contains a failure-injection hook,
test-only route, special header or environment flag seam. The test also pins that
PT06 requires no unprovokable failure (no 500 requirement, no
`InternalServerError`, no induced internal failure) and no new endpoint. It is pure
file inspection; no model and no benchmark run is involved.

**An out-of-tree runtime probe** (run against the unchanged substrate from a scratch
directory, committed nowhere, changing no repository file) confirmed the observed
behaviour the static test reasons about: empty `customerId`, empty `items` and
`quantity: 0` each answer HTTP 400 `application/json` with
`{"error":"ValidationError","message":<non-empty>,"correlationId":<non-empty>}`; an
unparseable body sent as `application/json` answers HTTP 400 with
`Content-Type: text/html`, an HTML error page, none of the three keys and no
correlation-id response header; and a valid request answers HTTP 201 with the
existing response body. The two failure kinds are therefore **not** already
identical in every required respect.

The task's scope classification (`medium`) and its single visible validation command
(`npm run ci:agent`) are unchanged.

## PT06 rejection-contract clarification

An independent review of the amendment above accepted its feasibility work and found
no defect that invalidated it, but identified two places where PT06's public text did
not fully determine the behaviour a conforming solution must produce. Either could
have let a solution satisfy every stated criterion and still fail acceptance, which
is precisely the failure mode the public task body exists to prevent. Both are now
closed in PT06's text.

**1. The response media type is now stated, not implied.** The amendment said only
that the rejection body "is JSON - never HTML, never empty". That constrains the body
payload, not the media type the response declares: a solution that serialises the
envelope and sends it as a string produces a parseable JSON body under a `text/html`
media type, satisfying the old sentence and every completion criterion while failing
any check that reads the response as JSON. The observed base behaviour shows the two
paths already differ on exactly this axis - the semantic rejection declares
`application/json; charset=utf-8`, the parse failure declares `text/html;
charset=utf-8`. PT06 now requires, for both covered rejections, a `Content-Type`
response header whose media type begins with `application/json`, and states that no
other response header is part of its required behaviour.

**2. The covered rejections are now bounded to exactly two kinds.** The amendment
opened with an unqualified "a rejected `POST /orders` request answers with HTTP 400"
and closed with "nothing beyond the rejection response of `POST /orders` has to
change", while its completion criteria pinned only two kinds. That gap is reachable
from outside: at the base an over-large body is answered HTTP 413 and an unsupported
charset HTTP 415, both as HTML. Under the broad reading a solution must remap those
to the envelope; under the narrow reading it must not - and the most natural
implementation of the broad reading silently rewrites them. PT06 now names its two
covered kinds in a **Scope** section, states that every other transport-level or
body-parsing rejection (HTTP 413, HTTP 415, an aborted request, and any other) is
outside its scope and keeps its current status code and body, and uses that same
bounded wording in its completion criteria.

Neither clarification adds a requirement that is not externally observable, and
neither prescribes how the behaviour is produced.

### PT06 acceptance scope (binding on PT06's private evaluator package)

Recorded here so the re-authored package cannot drift from the public text:

1. PT06 acceptance **may** assert that the rejection response carries a
   `Content-Type` header whose media type begins with `application/json`. Parameters
   after the media type are not constrained, so an assertion must not require an
   exact header string.
2. PT06 acceptance **must not** assert any other response header - not its presence,
   not its absence, not its value. `x-correlation-id` in particular is not part of
   PT06's required behaviour, even though the base sets it on the paths that already
   build the envelope.
3. PT06 covers **only** the two kinds its **Scope** section names: a semantic
   input-validation failure of a body that was parsed as JSON, and a JSON parse
   failure of a request sent with `Content-Type: application/json`.
4. HTTP 413, HTTP 415, aborted requests and every other transport-level or
   body-parsing rejection are **outside** PT06's acceptance scope. No PT06 acceptance
   test may require them to answer HTTP 400, to carry `error` `ValidationError`, or to
   carry PT06's envelope; and none may be used to fail a solution that leaves them as
   they are today.
5. `message` wording remains unconstrained: acceptance may assert only that it is a
   non-empty string.

As before, no PT06 acceptance test may assert a 500 response or induce an internal
failure.

### Architecture-opportunity adequacy for the amended PT06 (private, deferred)

The amendment reduced PT06's novel work from two required changes to one, and the
feasibility evidence for it is **functional only** - by design, since a public task
body and its public feasibility test must stay architecture-neutral. Whether the
amended PT06 still carries a non-empty fixed opportunity set is therefore **not**
settled by this public package, and deliberately cannot be: settling it publicly
would mean publishing the very material that must stay private.

Classification: a **future private-evaluator blocker** under **TD-B05** / **TD-B14**,
gated by **G1**. It is **not** a defect in PT06's public text, and no opportunity,
applicable rule or expected area has been added to any public artifact to address it.
It must be demonstrated during the substantive private re-authoring of PT06's package,
before that package may be approved or frozen.

PT06's SHA-256 has now changed twice: once with the amendment
(`3994a158ad39f629...` -> `ae87303c6be53fe1...`) and once with this clarification
(`ae87303c6be53fe1...` -> `3e0f84cfef1f9fbf...`). The current pinned value is
`3e0f84cfef1f9fbf...`; the two earlier values are recorded so a private package
pinned to either is identifiable. **No other task body changed** in either step, so
every other pinned public-task hash recorded at public commit `0e77d49` still holds.

## Feasibility against the frozen base substrate

Every candidate was re-checked against the base substrate rather than against an assumed one. The base exposes exactly two endpoints (`GET /health`, `POST /orders`), has no 404 handling, and stubs the repository read paths at the composition root. Each task either targets behaviour that exists or creates the endpoint it describes, and no completion criterion depends on an endpoint the task neither has nor creates.

Since the PT06 amendment, a second feasibility bar also holds for every candidate: **no completion criterion depends on a failure that an external caller cannot provoke** through the public interface. PT06 was the only candidate that failed this bar, and it no longer does.

## Leakage validation

The public-task leakage validator (`experiments/v2/tasks/validate_public_tasks.py`, terms in `docs/v2/TASK_LEAKAGE_TERMS.yml`) was run over every authored public task body. Result: **OK for every task** (no hard leak; no uncovered review-required term; no reviewed exceptions were needed), with a hardened validator that now also scans front matter, detects hard-wrapped phrases, covers all twelve prohibited leakage families, discovers task bodies recursively, and reconciles them against `TASK_INDEX.csv`.

A clean result means **no detected leakage**. It is not proof of scientific validity. This advances TD-B17 for the authored draft suite; **TD-B17 remains open** pending independent review at freeze.

## Suite classification (analysis eligibility)

An independently approved suite-level decision narrowed the confirmatory construct to **layered dependency-direction conformance**. Analysis eligibility is now an explicit, machine-checked field (`e1_analysis_eligibility`) in `TASK_INDEX.csv` and `docs/v2/PILOT_PUBLIC_TASK_MATRIX.csv`. The existing primary/reserve classification is **unchanged**; eligibility is a separate axis.

| Value | Meaning | Tasks |
| --- | --- | --- |
| `scored` | carries applicable frozen dependency-direction opportunities; contributes to E1 | PT01, PT02, PT03, PT04 |
| `functional-only` | valid primary functional candidate, **structurally excluded from E1**; still contributes to hidden functional acceptance, cost, reset-related functional outcomes and pre-registered exploratory analyses | PT05, PT06 |
| `inactive-reserve` | pre-declared reserve, **not activated**; contributes to no endpoint | PR01, PR02 |

Binding consequences:

- **`PT05` and `PT06` are excluded from E1 without being a failed run.** Exclusion is a statement about architectural exposure, not about the task's validity or a run's success. Neither is coded as zero violations, entered with a zero numerator, or coded `NO_PATCH`/`REFUSAL`/`INVALID_CODE`.
- **A task with `applicable_opportunity_count = 0` is structurally ineligible for E1**, never entered as zero violations (`docs/v2/STATISTICAL_ANALYSIS_PLAN.md` §2.1).
- **No reserve was activated.** `PR01` and `PR02` enter no endpoint.
- **`PR02` must not be promoted.** Its terminal-state completion criterion (cancelling a `shipped` or `delivered` order answers HTTP 409 `ConflictError`) is **not externally reachable** through the current public interface: no public endpoint can move an order out of its created status and `PR02` creates none. `PR02` cannot be activated until the criterion is repaired **and** the repair is independently re-approved (**TD-B26**). Its public body is **not** modified by this work package.
- **Broader architecture dimensions remain secondary/manual evidence** under `CON-ACB` and are never pooled into E1.
- **`PT03`'s public repeat-request contract is contradictory and is recorded, not fixed.** It permits a change to any of the five accepted values - including `delivered` and `cancelled` - while also requiring that repeating the same request returns the same stored status *and* that a current status of `delivered` or `cancelled` answers HTTP 409 `ConflictError`. A target of `delivered` or `cancelled` cannot satisfy both. This needs a **separate public task amendment** and a **private relink**, tracked as **TD-B25**. `PT03`'s body and hash are unchanged here.
- **Architecture-revealing source comments are recorded, not neutralised.** Model-visible TypeScript comments in the shared substrate explicitly state some scored dependency rules to every condition, including the C1 baseline, and one shows a worked boundary-violation example. That may make C1 partly guided and floor the primary contrast (**TD-B23**), and the worktree leakage sweep does not yet read source content to detect it (**TD-B24**). `apps/` and `libs/` are **unchanged** by this work package. *(**Superseded** by a later remediation - see "Addendum: source substrate re-identified" below. `TD-B23`/`TD-B24` are now resolved and the substrate has a new identity; this bullet remains an accurate record of what **this** package did.)*
- **No task body, task content hash, manifest, endpoint or protocol was frozen.**

## Opportunity reassessment (pre-authoring, pre-run)

An independent reassessment of the active architecture set was carried out **before any
benchmark or model execution**, against the frozen public task bodies and the unchanged
source substrate. It is a **construct and feasibility** judgement about what architectural
decisions the tasks actually create; it is not, and cannot be, a judgement about any
observed result, because **no experimental result exists**.

### PT05 is reclassified `functional-only`

**PT05 is functionally valid but structurally ineligible for E1 because its required
functional work creates no currently scored dependency-direction opportunity.**

This is a **pre-run construct/feasibility reclassification and is not based on a model
outcome.** **No benchmark or model execution occurred** in this package and no result
artifact exists, so no outcome could have informed it. PT05's public body, its SHA-256, and
its `primary` kind are **unchanged**; only its `e1_analysis_eligibility` moves from `scored`
to `functional-only`.

`PT05` must **never** be represented as:

- zero architecture violations;
- a failed task or a failed run;
- a missing task;
- an invalid task;
- a refusal.

`PT05` continues to contribute to **hidden functional acceptance**, the **engineering-cost**
measures, **reset-related functional outcomes**, and **pre-registered exploratory analysis**.
It contributes nothing to E1's numerator or denominator.

**No reserve was activated** to compensate. `PR01` and `PR02` remain `inactive-reserve`;
restoring a scored task count is explicitly *not* a legitimate reason to activate a reserve.

### Aggregate construct coverage (no private content disclosed)

Reported at suite level only. Which specific opportunities exist per task, and their
contents, remain private; nothing below discloses a private opportunity identifier, a
hidden test, a hidden acceptance detail, or an implementation answer.

- **`PT01`-`PT04` currently remain E1-scored candidates.**
- **`PT05` and `PT06` are `functional-only`.**
- **`PR01`/`PR02` remain inactive; no reserve was activated.**
- **The current active task set does not provide enough distinct dependency-direction
  decisions for confirmatory inference.** The active opportunities exercise **too few
  distinct dependency boundaries** - too few distinct (source scope, forbidden target)
  relationships - to support the named confirmatory construct.
- **Repeated tasks over one boundary do not count as independent architecture
  constructs.** Several tasks that each re-expose the same source/target boundary are one
  architectural instrument measured repeatedly; they are clustered observations, not
  independent architecture decisions (`TD-B30`, `TD-B37`).
- **Additional task-created dependency decisions are required**, and therefore **further
  public task authoring is required before Stage 0**.

The deficiency is **task-set coverage**, not an oracle failure: the repaired scope-based
attribution mechanism remains the approved attribution mechanism, and it is strengthened -
not replaced - by the production-source scoring policy recorded below.

## DECISION B - additional architecture tasks required before Stage 0

**DECISION B: author additional public tasks exercising genuinely different existing
dependency-direction leaf rules and source/target boundaries before Stage 0.** Registered as
blocking decision **`TD-B34`**.

The motivation is **construct validity**: the current task set does not sample enough
distinct dependency-direction decisions to support the intended confirmatory endpoint.

Stated explicitly, so the record cannot be misread later:

- **This decision predates any benchmark or model outcome.** It was taken from the task
  bodies and the substrate, before Stage 0.
- **No experimental result exists.** `experiments/v2/results/` holds no result artifact.
- **No reserve is being activated merely to restore task count.** `PR01`/`PR02` stay
  inactive, and `PR02` additionally stays blocked (`TD-B26`).
- **The deficiency is task-set coverage, not an oracle failure.**
- **The repaired scope-based oracle remains the approved attribution mechanism**
  (`TD-B27`, mutation corpus M0-M8).
- **New rule families are not required for this immediate remedy**, because additional
  **unused implemented dependency leaf relationships already exist** in the frozen matrix
  (see the boundary space below). Implementing new rule families stays future work
  (`TD-B33`) and must never be used to readmit an excluded task post hoc.

`TD-B34` is **open and blocking**. Gates **G1**, **G2** and **G6** remain **not passed**, and
the suite is **not** ready.

## Authoring requirements for the NEXT work package (no task is authored here)

**No new or replacement task is authored in this package.** These are the requirements the
next candidates must satisfy; they are recorded now so authoring cannot drift.

Every next candidate task must:

1. **create a genuine dependency decision caused by required functional work** - the
   functional requirement itself must force a source-to-target choice;
2. **not merely preserve an already-satisfied boundary** - re-passing a boundary the base
   already satisfies is a preservation-only opportunity and does not count;
3. **exercise a dependency leaf/source-target decision not already represented** by the
   surviving active set where the substrate permits it;
4. **be feasible through the public interface** of the unchanged source substrate;
5. **avoid implementation-dependent hidden setup** - no failure-injection hook, test-only
   route, special header or environment flag;
6. **have a fixed opportunity before model output** - the decision is frozen at authoring
   time, never inferred from what a model produced;
7. **remain compatible with legitimate implementation alternatives** - more than one
   correct shape must be able to satisfy it;
8. **not depend on which file the model creates** - scoring is anchored on the frozen
   architectural scope, so a candidate whose decision only exists in one particular file is
   not admissible;
9. **avoid task overlap severe enough to duplicate an existing architectural instrument**;
10. **remain functional-only in public wording, with no architecture hint** - the public
    body still states functional requirements and observable behaviour only, and must pass
    the leakage validator unchanged.

Each candidate must pass the **same "task-created decision" test** that removed the
preservation-only opportunities: if the required functional work would leave the boundary
untouched, there is no opportunity.

### Boundary space available under the already-implemented leaf rules

Public information only - derived from the public rule catalog and the public dependency
matrix, not from any private manifest. Priority is given to decisions that broaden currently
absent scored exposure, **subject to actual substrate feasibility**.

| Leaf rule | Source scope | Forbidden targets it can back |
| --- | --- | --- |
| `AR-DEP-002` | contracts | core, features, infra, observability, api |
| `AR-DEP-003` | core | features, infra, observability, api |
| `AR-DEP-004` | infra | core, features, api |
| `AR-DEP-005` | api | core |
| `AR-DEP-006` | features | infra, api |

Candidate decisions to **investigate, not automatically adopt**:

- a genuine **api -> core-only capability** decision backed by `AR-DEP-005`;
- a genuine **infra -> core** decision backed by `AR-DEP-004`;
- a genuine **core -> forbidden layer** decision backed by `AR-DEP-003`;
- a **contracts-source** decision backed by `AR-DEP-002`, where a task can legitimately
  create such a decision.

**Do not create artificial tasks merely to hit rule ids.** A candidate that names a rule
relationship but does not make the functional work create the decision fails requirement 1
and must be rejected. The `observability` scope has **no implemented leaf clause** at all,
so it cannot back a scored opportunity regardless of how a task is written.

## Production-source scoring (E1 measures production dependencies only)

A P0 finding was that test and configuration TypeScript entered the scored dependency
scopes: the frozen `source_globs` (`apps/**/*.ts`, `libs/**/*.ts`) and the frozen layer path
globs both match `*.spec.ts` files and `jest.config.ts`, so a dependency introduced purely
to wire up a test could have produced an E1 violation in a production architectural scope.

The oracle now partitions the scanned TypeScript into two graphs before any edge is built:

- the **production dependency graph** - the only graph E1 is computed from;
- the **excluded test/config/support graph** - recorded descriptively, never scored.

The **frozen architectural layer scopes are unchanged**; the partition happens at source
selection, so no layer glob and no frozen opportunity locator moved. The denominator remains
the **frozen opportunity count**, never a file count, so adding or deleting test files cannot
move either side of E1. The policy, its exclusion classes, and why excluded edges never enter
E1 are specified in
[`../../../../docs/v2/ORACLE_VALIDATION_REQUIREMENTS.md`](../../../../docs/v2/ORACLE_VALIDATION_REQUIREMENTS.md)
§1b, and regression-locked by mutation cases **M8-A**-**M8-F**.

## Public task inventory

| Task | Kind | Category | Scope | Public task SHA-256 | E1 analysis eligibility |
| --- | --- | --- | --- | --- | --- |
| PT01 | primary | read-endpoint | small | `6c938822fe19cd6e...` | scored |
| PT02 | primary | list-endpoint | medium | `ec4b60057708b20c...` | scored |
| PT03 | primary | write-endpoint | medium | `cbfce1ca232cb9b6...` | scored |
| PT04 | primary | logging | medium | `f349b150b1d8fe56...` | scored |
| PT05 | primary | calculation | medium | `f6efc772e76d6c28...` | functional-only |
| PT06 | primary | error-handling | medium | `3e0f84cfef1f9fbf...` | functional-only |
| PR01 | reserve | calculation | small | `0e1527bce4149883...` | inactive-reserve |
| PR02 | reserve | write-endpoint | medium | `e89a4aab236813c0...` | inactive-reserve |

Relative to the suite recorded before the repair package, only PT05 is byte-identical
and the other seven changed. Relative to public commit `0e77d49`, **only PT06
changed**: it carries the amended and clarified body above, and the other seven bodies
are byte-identical to their `0e77d49` bytes.

## Private evaluator package staleness (mandatory)

The private evaluator commit that was created against the **hashes recorded before the
repair package** is **stale** and must be treated as such:

- it **must not** be reviewed, approved, frozen, or used for Stage 0 or any pilot;
- every private per-task manifest, hidden acceptance plan, fixed opportunity set, expected/prohibited area set, legitimate-alternative list and reset predicate must be **re-authored or re-linked** against the new public task hashes above - PT04 and PT06 changed subject matter entirely, so their hidden packages must be re-authored, not merely re-hashed;
- a private manifest hash must **never** be silently accepted against a changed public task: the pinned public-task hash is part of the package's identity, and a mismatch is a hard failure, not a warning;
- re-linking may only happen **after** this public work package is independently approved, so the hashes it pins are the approved ones;
- the oracle continues to refuse to score a non-frozen manifest (`MANIFEST_NOT_FROZEN`).

### Staleness introduced by the PT06 amendment and clarification (scope: PT06 only)

A private evaluator commit was subsequently created against the public task bytes of
public commit `0e77d49`: private commit
`5733ca6151f7739c7105a5c1405fcbc8fb3cb59d` (`5733ca6`). The PT06 amendment and the
PT06 rejection-contract clarification above change **only** PT06's public bytes, so
their combined effect on that private commit is exactly scoped:

- **only PT06's private package becomes stale** because of this amendment and this
  clarification;
- the **seven** packages other than PT06 - PT04 among them - remain linked to the
  public task bytes that were independently reviewed at public commit `0e77d49`, which
  are byte-identical to the bytes recorded here, so they need no re-linking for either
  change;
- PT06's private package must be **substantively re-authored**, not merely re-hashed:
  its subject matter changed again (the unexpected-server-failure requirement is gone,
  the rejection envelope now covers the unparseable-JSON path, the response media type
  is now pinned and the covered rejections are now bounded to two kinds), so its hidden
  acceptance plan, expected/prohibited areas, fixed opportunity set,
  legitimate-alternative list and reset predicate must all be reconsidered against the
  amended and clarified public text, under the PT06 acceptance-scope constraints
  recorded above;
- that re-authoring must also demonstrate a non-empty fixed opportunity set for the
  amended PT06, which this public package deliberately does not and cannot settle
  (TD-B05/TD-B14, gate G1);
- re-authoring may only happen **after** this public amendment and clarification are
  independently approved, so the hash it pins (`3e0f84cfef1f9fbf...`) is the approved
  one. A package pinned to `3994a158ad39f629...` or to `ae87303c6be53fe1...` is pinned
  to superseded public bytes;
- private commit `5733ca6` **must not be reviewed as a complete eight-task package**
  until PT06 is updated. Reviewing it as complete would review a PT06 package built
  against superseded public bytes;
- as before, a private manifest hash must never be silently accepted against a changed
  public task, and every private manifest remains status `review` (not frozen).

The private evaluator repository was **not** accessed, inspected, or modified while producing this report, this amendment, or this clarification. Its filesystem location is deliberately not recorded in any public file, and no private manifest, hidden plan or other private content is reproduced here - the private commit identifier above is an identifier only.

## Model-visible worktree isolation

The review also found that the coding model's worktree was the whole repository, which placed `docs/v2/ARCHITECTURE_CONTEXT.md` and `docs/v2/ARCHITECTURE_RULE_CATALOG.yml` inside every condition's workspace including the C1 baseline. An allowlist-first, fail-closed preparation mechanism now builds the model-visible worktree from the source substrate only (`docs/v2/MODEL_VISIBLE_WORKTREE_POLICY.md`, `experiments/v2/harness/prepare_model_worktree.py`). Runner-time enforcement is the new blocking decision **TD-B22** and is **not** implemented.

## What was deliberately NOT done

- No task was selected, rejected, or difficulty-tuned using any observed or expected AFCI advantage (CRITICAL_DESIGN_DECISIONS D3/D10).
- No candidate task was implemented; no reference or expected solution exists in this repository. PT06 in particular was **not** implemented as part of its amendment or of its rejection-contract clarification.
- **No validation seam was added to the source substrate.** No failure-injection hook, test-only route, special header, environment flag or other implementation-specific seam was introduced to make any requirement observable; `apps/` and `libs/` are byte-identical to their state at public commit `0e77d49`. *(True of this package. A later remediation changed `apps/` and `libs/` - comments only, no seam and no executable change - so the current substrate identity is the one recorded in [`../../../../docs/v2/SOURCE_SUBSTRATE_IDENTITY.md`](../../../../docs/v2/SOURCE_SUBSTRATE_IDENTITY.md), not `0e77d49`.)*
- **No architecture opportunity was added publicly.** The rejection-contract clarification adds no architecture wording, applicable rule, expected or prohibited area, or task-specific opportunity to PT06 or to any other public artifact; PT06 remains architecture-neutral, and the adequacy of its fixed opportunity set stays a private, deferred question (TD-B05/TD-B14, G1).
- No hidden acceptance test or hidden evaluator answer was added publicly.
- **No final task count**, repetition count, run count, model, or numerical budget was selected. The eight candidates are candidates, not a core-study task set.
- No hidden evaluator package was frozen; the oracle continues to refuse to score a review-status package (`MANIFEST_NOT_FROZEN`).
- Task-specific oracle validity, hidden-acceptance validation, reset checkpoint review, and benchmark discrimination remain open (G1/G2 not passed).
- **No task body or task content hash changed for the suite classification, for `PT05`'s reclassification, or for `DECISION B`.** All eight bodies are byte-identical to their state at public commit `fef5987`, and all eight recorded SHA-256 values are unchanged. Classification is metadata, never a task edit.
- **No replacement or additional task was authored.** `DECISION B` records the requirement and the authoring bar; the tasks themselves are the next work package.
- **No reserve was activated to restore the scored task count**, and no reserve opportunity was promoted into E1.
- **No architecture-rule family was implemented or added.** The remedy uses dependency leaf relationships that are **already implemented** (`AR-DEP-002`-`AR-DEP-006`).
- **No power simulation was run and no power value was frozen** (`TD-B20`/`TD-B37`).
- **`PT03`'s repeat-request contradiction was NOT fixed** - it is recorded as blocking decision **TD-B25** and requires a separate public amendment plus a private relink.
- **Architecture-revealing source comments were NOT neutralised** - recorded as **TD-B23** (with the leakage-scanner gap as **TD-B24**); `apps/` and `libs/` are unchanged. *(**Superseded**: a later remediation neutralised them and resolved both blockers - see the addendum below.)*
- **No reserve task was activated**, and `PR02` was **not** promoted (**TD-B26**).
- **No new architecture-rule family was implemented**, and `AR-CONTRACT-001`/`AR-CODE-001` were **not** implemented: broadening E1 is future work (**TD-B33**) and must never readmit an excluded task post hoc. The **only** oracle change in this package is the production-source scoring policy above, which **narrows** what E1 measures to production dependencies and adds no rule, no opportunity and no answer.
- **No blocker was closed.** Eleven were opened by the suite classification (`TD-B23`-`TD-B33`) and four more here (`TD-B34`-`TD-B37`); the registry now holds 37 blocking and 6 non-blocking decisions, all `open`. *(**Superseded on status only**: a later remediation resolved `TD-B23` and `TD-B24`. The registry still holds 37 blocking and 6 non-blocking decisions; 41 of the 43 remain `open`, including every task-authoring blocker.)*
- **No private opportunity answer or exact private evaluator content is disclosed here.** Where a private identifier is named at all it is named as an identifier only.

---

## Addendum: source substrate re-identified (`TD-B23`/`TD-B24` resolved)

Recorded here because the section above states that `apps/` and `libs/` are
byte-identical to public commit `0e77d49`, and that is no longer the current
substrate. This addendum was written by a **later** work package; nothing above it
was rewritten, and no task body, task hash or task classification changed.

**What changed.** Six comment lines in three model-visible source files. They
stated scored dependency rules to every condition, including the no-guidance C1
baseline: the `api` to `core` prohibition together with a worked commented-out
forbidden import and a "would fail CI" consequence; the `infra` avoidance of
`core` justified as a deliberate architectural choice; and the same `api` to
`core` prohibition restated from the `features` side. They are removed, or
rewritten in neutral implementation terms.

**Why it matters to task authoring.** `DECISION B` (`TD-B34`) requires new public
tasks over genuinely different dependency boundaries, and the strongest candidates
sit on exactly the `api` to `core` and `infra` to `core` boundaries the substrate
was teaching. Authoring them against a substrate that states the answer would have
compressed the intended contrast between the unguided baseline and the
architecture-context conditions.

**What did not change.** No executable change: the emitted JavaScript with
comments stripped, the full AST fingerprint and the import/export edge list are
identical in all three files. No alias, dependency rule, layer scope, allowed
relationship, application API or runtime behaviour was touched, and the three
forbidden relationships remain structurally detectable. The eight public task
bodies and all eight recorded SHA-256 values are unchanged, because a task body is
not a substrate file.

**New substrate identity.** Recorded in `docs/v2/SOURCE_SUBSTRATE_IDENTITY.md`,
which carries the superseded and current content hashes, the commit identifiers
and the equivalence proof. Any private evaluator package that pins the substrate
by commit should be re-pinned to the new identity; **no** public task hash changed,
so no package needs re-authoring or re-hashing on account of this remediation.

**Governance.** `TD-B23` is resolved with disposition **neutralise** (not
pre-register), and `TD-B24` is resolved by extending the leakage sweep to read
source content. All other blockers stay open, including every task-authoring
blocker (`TD-B34`, `TD-B26`, `TD-B31`) and runner-time enforcement (`TD-B22`).
No benchmark ran, no model was invoked, the private evaluator repository was not
accessed, and nothing was frozen.
