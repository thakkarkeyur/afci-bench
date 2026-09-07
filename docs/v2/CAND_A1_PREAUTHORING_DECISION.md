# docs/v2 — `CAND-A1` pre-authoring candidate decision record

Status: **development record for study v2**, now carrying the recorded lifecycle
transition in §2a. **As originally issued** this was a pre-authoring record only:
`CAND-A1` was a **provisional candidate identifier**, not a task, and the record
itself authors **no** public task body, creates **no** private evaluator package,
creates **no** manifest, assigns **no** `PT08` identifier, creates **no**
architecture opportunity, enters **no** `E1` denominator, activates **no** reserve,
authorizes **no** paid model run, freezes **no** benchmark configuration, changes
**no** task body or hash, touches **no** file under `apps/` or `libs/`, runs **no**
power simulation and **produces no power value**. The protocol remains
**PRE-FREEZE**.

**`CAND-A1` has since been publicly authored, by a separate public-authoring
package, as the public task body `PT08` (§2a).** That package — not this record —
is what assigned the identifier. Everything else in the list above still holds of
**this record and of that package alike**: neither created a private evaluator
package, a manifest, an architecture opportunity, an `E1` denominator row, an
activated reserve, a paid model run, a freeze or a power value.

**Current post-admission state, reached by later separate packages and recorded in
§2a.** `PT08`'s public authoring was **independently reviewed and approved**; its
**private evaluator package has since been authored** and **approved on a
discharged conditional independent review**; and a **separately recorded governance
admission step** admitted its single fixed architecture opportunity to the active
`E1` denominator and the active decision-cluster register. **None of that was done by this record**, and
none of it confers a freeze, a gate pass, run eligibility, a result or a power
value: nothing is frozen, `G1` is **not** passed, `PT08` is **not** run-eligible,
its hidden functional acceptance is still **`draft_unvalidated`**, no reserve is
activated, no model is selected, and the protocol remains **PRE-FREEZE**.

Decision: **`TD-B34`** (re-scoped to replication depth), priority **A**.
Feasibility and forcing strength:
[`DEPENDENCY_TASK_FEASIBILITY.md`](DEPENDENCY_TASK_FEASIBILITY.md) §2a, §3.
Authoring bar: [`TASK_AUTHORING_POLICY.md`](TASK_AUTHORING_POLICY.md) §12.
Observation boundary:
[`HIDDEN_EVALUATOR_BOUNDARY.md`](HIDDEN_EVALUATOR_BOUNDARY.md) §9–§14.

---

## 1. What this record is, and what it is not

The independent Priority-A pre-authoring review of `CAND-A1` returned **`DECISION
B` — REPAIR CANDIDATE BEFORE AUTHORING**, with **P0 = 0** and **four P1
findings**. This record carries the Study Lead's approved adjudications and pins
the contract decisions the review required **before** any prose is written, so
authoring cannot later drift toward whatever is convenient.

**It is not an approval.** All four P1 findings are closed here (§8). The
candidate itself is **not** finally approved, and **one focused independent
remediation re-review is still required before authoring may begin.**

> **Disclosed consequence, recorded rather than hidden.** This record names
> `CAND-A1`'s target cluster, and therefore its source scope, forbidden target and
> leaf rule. That is a deliberate continuation of the disclosure already made in
> [`DEPENDENCY_TASK_FEASIBILITY.md`](DEPENDENCY_TASK_FEASIBILITY.md) §1 and
> [`TASK_AUTHORING_POLICY.md`](TASK_AUTHORING_POLICY.md) §12.2c, which publish the
> cluster inventory and name `DC-FEATURES-API-AR-DEP-006` as the priority-A
> replication target: the candidate's expected area was already inferable, and the
> pre-authoring adjudications cannot be reviewed without it. **Nothing here changes
> what the coding model sees** — `docs/v2/` is excluded from every condition's
> worktree by
> [`MODEL_VISIBLE_WORKTREE_POLICY.md`](MODEL_VISIBLE_WORKTREE_POLICY.md) — so the
> cost is to reviewer-facing blinding of one candidate's expected area, not to the
> experiment's baseline. **The expected violating implementation shape is not
> published here** and must not appear in the eventual public task prose.

---

## 2. Candidate identity and lifecycle state

| Field | Value |
|---|---|
| **Provisional candidate** | **`CAND-A1`** |
| **Concept** | caller-declared order-value ceiling on order creation |
| **Target cluster** | `DC-FEATURES-API-AR-DEP-006` |
| **Source scope** | `features` |
| **Forbidden target** | `api` |
| **Leaf rule** | `AR-DEP-006` |
| **Priority** | **A** (`TD-B34` §12.2c) |
| **Authoring state** | **PUBLICLY AUTHORED** as `PT08` (§2a); public-authoring review **passed**; private evaluator package **authored and approved**; opportunity **admitted** |
| **Review state** | `DECISION B` remediation completed / focused remediation re-review **APPROVED — public authoring may begin** / **independent public-authoring review of the authored body PASSED** / private evaluator package **APPROVED on a discharged conditional independent review** |
| **Approved carrier** | **publicly specified query parameter** `maxTotal` |
| **Forcing class** | **natural-path / opportunity-creating** |
| **Study Lead acceptance** | **recorded** (`SL-CA1-01`, `SL-CA1-02`) |
| **Difficulty-diagnostic adjudication** | **`SL-PT08-01`** — pre-Stage-0, `PT08`-only, `C1`-only, non-confirmatory (§4) |
| **Task identifier assigned** | **`PT08`**, assigned at public authoring only (§2a) |

**No `PT08` identifier is assigned by this record**; the separate public-authoring
package assigned it, and *as originally recorded* here none existed anywhere in the
repository. *As recorded then*, `CAND-A1` had **no** private evaluator package,
**no** manifest, **no** denominator row and **no** active opportunity. **Superseded
on those four points only** (§2a): a private evaluator package, a manifest, an
admitted denominator row and an active opportunity now exist for its authored body
`PT08`. Its public `PT08` row in
[`TASK_INDEX.csv`](../../experiments/v2/tasks/public/TASK_INDEX.csv) carries the
public eligibility value `scored`, which **still** records **intent only** and is
never a demonstrated denominator: the manifest is `status=review`, `G1` is not
passed, and `PT08` is not run-eligible.

---

## 2a. Lifecycle transition — publicly authored as `PT08`, then admitted

Recorded so the transition is legible and bounded. **This section changes no pin
and no adjudication in the rest of this record**; §3–§9 stand as written, and the
pre-authoring history above them is preserved rather than rewritten. The counts it
carries are the one thing that has moved, and both readings are kept below.

| Lifecycle fact | State |
|---|---|
| **Focused independent remediation re-review** | **PASSED — APPROVE: public authoring may begin** |
| **Public task body** | **authored** |
| **Public task identifier** | **`PT08`** (assigned at public authoring; §2, §9) |
| **Independent public-authoring review of `PT08`** | **PASSED** (*as recorded then*: **pending**) |
| **Private evaluator package** | **authored** (*as recorded then*: absent) |
| **Private evaluator package review** | **APPROVED on a discharged conditional independent review** |
| **Private manifest** | **authored, `status=review`, not frozen** (*as recorded then*: absent) |
| **Private architecture opportunity** | **authored and ADMITTED** — one fixed opportunity, identifier withheld (*as recorded then*: absent) |
| **Hidden functional acceptance** | **`draft_unvalidated`** — authored, **not** runtime-validated |
| **Frozen** | **no** |
| **Gate `G1`** | **not passed** |
| **`E1` run eligible** | **no** |
| **Benchmark run** | **no** |
| **Result / power value** | **none** |
| **Active `E1` contribution** | **one applicable opportunity instrument** (*as recorded then*: none) — an instrument count, **never** a violation, a success or a result |

- **`CAND-A1` → `PT08` occurs only at public authoring.** The mapping is created by
  the public-authoring package and by nothing earlier: no pre-authoring record, no
  feasibility review and no registry row assigned an identifier before that package
  existed.
- **The final independent authoring-readiness confirmation passed.** The focused
  remediation re-review that §8 required has happened and returned **APPROVE —
  public authoring may begin**. Provenance is recorded exactly as supplied: the
  review was an external read-only confirmation supplied to the governance process,
  **no reviewer identity, external URL or timestamp was supplied and none is
  claimed**, and the review **precedes** the commit that records it — this record
  and the authoring package **propagate** that result and **neither performs it**.
- **Public authoring is not private authoring.** *As recorded then*, no private
  evaluator package, hidden acceptance suite, manifest or architecture opportunity
  was created for `PT08` by the authoring package, and none could be inferred from
  its existence; the private package was to be authored only **after** an
  independent review of the public-authored body. **That is exactly the order that
  was followed:** the public-authoring review passed **first**, the private
  evaluator package was authored **after** it, that package was **approved on a
  discharged conditional independent review**, and only then did a **separately
  recorded governance admission step** admit the opportunity.
- **The active experimental inventory moved once, by that admission and by nothing
  earlier.** *As recorded then*, active `E1` opportunities remained **5**, decision
  clusters **3**, cluster observation depths **3 / 1 / 1**, and the priority-A
  cluster stood at **one** active observation — because an authored public body is
  not an observation: it carries no private opportunity, adds nothing to any
  denominator and **must not be pre-counted** (§7). **Current post-admission
  state:** active `E1` opportunities **6**; decision clusters **3**; cluster
  observation depths **3 / 2 / 1**; and the priority-A cluster at **two**
  observations, `PT04` and `PT08`.
- **That depth is replication, not independence.** `PT04` and `PT08` are
  **pseudo-replicates** of one shared boundary decision. Admission created **no new
  decision cluster**, no second architecture construct, and no licence to enter the
  two as independent statistical observations.
- **`TD-B34` is not resolved by this transition** and stays **open and blocking** on
  replication depth. Priority B (`DC-API-CORE-AR-DEP-005`) still has had **no**
  candidate review at all and is **not started**.
- **Nothing is frozen, no gate is passed, and no experiment is run-ready.** `PT08`
  is a `candidate`, exactly like the nine bodies authored before it: its manifest is
  `status=review`, its hidden functional acceptance is `draft_unvalidated`, gate
  `G1` is not passed, it is not `E1` run-eligible, and **no result, violation value
  or treatment-effect estimate exists**.

---

## 3. `SL-CA1-01` — the carrier is a query parameter, not a header (closes `P1-1`)

**Finding `P1-1`.** [`TASK_AUTHORING_POLICY.md`](TASK_AUTHORING_POLICY.md) §12.1
requirement 5 — *"avoids implementation-dependent hidden setup — no
failure-injection hook, test-only route, special header, or environment flag"* —
was **ambiguous** about a candidate that introduces a **new request header** as
the carrier for the caller-declared ceiling.

**Decision, approved by the Study Lead.** **Do not use a new request header.** The
carrier is a **publicly specified query parameter**.

- The query parameter is named **`maxTotal`**.
- It is **ordinary public API input**: part of the documented functional contract,
  not hidden, not test-only, and not implementation-dependent.
- It **must be fully documented in the eventual functional task contract**.
- **No special-header adjudication under requirement 5 is required**, because no
  special header is used. The ambiguity is removed **by construction** rather than
  argued away — see §12.1's requirement-5 note in
  [`TASK_AUTHORING_POLICY.md`](TASK_AUTHORING_POLICY.md).

**`P1-1` is CLOSED.**

---

## 4. `SL-CA1-02` — natural-path forcing accepted (closes `P1-2`)

**Finding `P1-2`.** `CAND-A1` has **natural-path rather than strict forcing**: a
cheap **boundary-only** implementation exists, and it is **cheaper** than the
features-side implementation.

**Decision, approved by the Study Lead.** `CAND-A1` is **accepted as a
scientifically valid independent replication instrument** despite forcing strength
weaker than `PT04`'s. Every one of the following is recorded:

- `CAND-A1` is **not** preservation-only.
- **Doing nothing fails the functional contract.**
- It creates a **real new functional requirement**.
- A `features → api` **violating implementation is compiling, CI-agent-clean and
  evaluator-detectable**.
- **Conforming implementations exist.**
- A **legitimate boundary-only implementation also exists**.
- The boundary-only implementation is **cheaper than both** the intended conforming
  features-side implementation **and** the violating implementation.
- **Therefore the task does not strictly force `features`-scope work.**
- Its forcing class is **natural-path / opportunity-creating, NOT strict**.
- This weaker forcing is **accepted as a construct-validity limitation**.
- **Discriminative difficulty must be evaluated only through the pre-registered
  Stage-1 baseline-only `C1` pilot**
  ([`PILOT_AND_POWER_POLICY.md`](PILOT_AND_POWER_POLICY.md), D3).
- **The task must never be tuned based on `C4` or on any treatment-effect result** —
  an observed AFCI advantage, a condition contrast and an interaction estimate are
  all inadmissible inputs to task tuning.
- **`CAND-A1` must not be represented as having forcing strength equal to
  `features → infra` tasks.**
- **Within-cluster observations remain pseudo-replicates** — statistically
  clustered — and are **not** independent architecture decisions (`TD-B30`,
  `TD-B37`).

**`P1-2` is CLOSED.**

### `SL-CA1-02` clarified by `SL-PT08-01` — the authorised baseline vehicle

**Nothing above is edited, withdrawn or rewritten.** The bullet that names the
pre-registered Stage-1 baseline-only `C1` pilot stands exactly as written, and it
still describes the confirmatory path correctly.

**As recorded then**, that pilot was the only vehicle this record named for
`CAND-A1`'s baseline-difficulty evidence, and the pilot sits after Stage 0, which
`TD-B34` gates. **Clarified on this point only, and on no other:** the Study Lead
has since authorised, in **`SL-PT08-01`**
([`PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md`](PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md)),
one pre-registered **pre-Stage-0**, `PT08`-only, `C1`-only, **non-confirmatory**
difficulty diagnostic as an **additional authorised vehicle** for satisfying the
**baseline-difficulty purpose** of `SL-CA1-02`.

The clarification changes the **vehicle**, never the **evidence class**:

- baseline **`C1`** evidence may inform difficulty — unchanged;
- **`C4` and any treatment-effect result may never tune the task** — unchanged,
  and an observed AFCI advantage, a condition contrast and an interaction
  estimate all stay inadmissible;
- every other statement of `SL-CA1-02` — the natural-path forcing class, the
  construct-validity limitation, the forcing-strength representation
  prohibition, and the pseudo-replicate status of within-cluster observations —
  is untouched and remains binding.

`SL-PT08-01` resolves **no** other question: `TD-B34` stays open and blocking on
the normal path, `TD-B12` and `G6` stay open, nothing is frozen, no gate is
passed, no model is selected, no sample size is selected, and no result exists.

---

## 5. Pinned contract decisions, required before authoring

The pre-authoring review required these pinned **before** the body is authored.
They are pinned here, in this record only. **No task prose is created.**

### `P-3` — rejection outcome

| Field | Pin |
|---|---|
| **HTTP status** | **`409`** |
| **`error`** | **`OrderValueLimitExceeded`** |
| **`message`** | required, **non-empty** string; **exact message text NOT pinned** |
| **`correlationId`** | required, **non-empty** string |
| **Response keys** | **exactly** `error`, `message`, `correlationId` |
| **Additional response keys** | **not permitted** |

**Why.** It keeps the **ceiling-policy rejection distinct** from an ordinary
`ValidationError` and from `PT06`'s validation-envelope work. A distinct status and
a distinct error value keep the two observable outcomes separable, so neither
task's acceptance can be satisfied by the other's behaviour. `409` is **not**
interchangeable with `400`: the ceiling rejection is a **policy** outcome, not a
request-validation outcome.

### `P-4` — query parameter and wire determinacy

Query parameter: **`maxTotal`**.

| Case | Outcome |
|---|---|
| **ABSENT** | existing behaviour **unchanged**; no ceiling applied |
| **PRESENT ONCE** | must represent a **finite non-negative base-10 numeric value** |
| **ZERO** | **valid** — a ceiling of zero is legitimate and is not treated as absent |
| **NEGATIVE** | **invalid** → `400` `ValidationError` |
| **EMPTY** | **invalid** → `400` `ValidationError` (an empty value is not an absent parameter) |
| **NON-NUMERIC** | **invalid** → `400` `ValidationError`; no coercion of arbitrary text |
| **`NaN` / `Infinity` spellings** | **invalid** → `400` `ValidationError` |
| **REPEATED `maxTotal` values** | **invalid** → `400` `ValidationError`; ambiguity is rejected, never silently resolved |

| Comparison | Outcome |
|---|---|
| reported order total **<** `maxTotal` | normal creation result |
| reported order total **==** `maxTotal` | **ACCEPTED** — normal creation result |
| reported order total **>** `maxTotal` | `409` `OrderValueLimitExceeded` |

**Equality is accepted.** A reported order total exactly equal to `maxTotal` yields
the normal creation result, never a rejection.

**Malformed `maxTotal` reuses the EXISTING `400` envelope** — `error` =
`ValidationError`, `message` non-empty with exact text unpinned, `correlationId`
non-empty. **No new envelope shape is introduced.**

**Prohibitions carried by `P-4`:**

- **No new monetary rounding rule is introduced.**
- **`maxTotal` is not rounded before comparison.**
- **No currency-conversion rule is introduced.**
- **The comparison is against the same total the service itself would report for
  that request under existing behaviour.**

### `P-4` precedence — body validation versus malformed `maxTotal`

Selected pin: **existing body validation wins.**

**Rule.** When the request body fails the existing validation contract **and**
`maxTotal` is malformed, the response is the **existing body-validation outcome,
unchanged**. The malformed ceiling does not alter, replace or suppress it.

**Rationale, in order.**

1. **It preserves an existing outcome.** The existing body-validation result for a
   given malformed body is already governed by the existing task/service contract.
   Changing it merely because a query parameter is also malformed would silently
   re-specify approved behaviour and could collide with `PT06`'s
   validation-envelope work. The pre-authoring instruction explicitly prefers
   preserving existing body-validation semantics.
2. **It follows the substrate's own order.** Request-body validation already runs
   **before** an order total exists, and the ceiling comparison is defined against
   a **reported total**, so a ceiling check cannot meaningfully precede body
   validation.
3. **It is deterministic and single-valued.** Exactly one response is defined for
   the overlap, so no implementation may choose.

**Consequences.** Both failures share the same status (`400`) and the same error
value (`ValidationError`), so the overlap is not externally ambiguous in status
terms; the pin fixes **which** failure the envelope describes. **Existing
request-body validation remains governed by the existing task/service contract and
is not re-specified by `CAND-A1`.** A malformed `maxTotal` on an otherwise valid
body still yields `400` `ValidationError`.

**Rejected alternative.** *Malformed ceiling wins* was rejected: it would change an
existing validation outcome for an already-governed malformed body.

### `P-5` — no new money semantics

- **No new rounding rule.**
- **No new precision rule.**
- **No discount rule.**
- **No currency conversion.**
- **No change to the existing subtotal/total computation.**
- **`maxTotal` is compared against the existing service-computed/reported total.**

**Why.** `PT05` owns order-level discount computation and `PR01` owns cent-exact
totals for fractional unit prices. A new rounding, precision, discount or
conversion rule in `CAND-A1` would overlap those instruments and would breach
authoring requirement 9. The ceiling is a **comparison** against an already-defined
total, never a new way of computing one.

### `P-6` — observation boundary

- **HTTP only.**
- **No `LogOutput` seam.**
- **No new seam of any kind.**
- **No hidden header and no hidden setup.**
- **No persistence inspection.**
- **No seeded repository state.**
- **No direct implementation-module state inspection.**
- **No `resetOrderRepository()`.**
- **A fresh application over a freshly evaluated module graph per hidden case.**
- **No cross-case state dependence.**

**Why.** This is the approved public functional-acceptance observation boundary
(`TD-B39`; [`HIDDEN_EVALUATOR_BOUNDARY.md`](HIDDEN_EVALUATOR_BOUNDARY.md)
§9–§14). `CAND-A1` is authored **after** that boundary, so it conforms from the
start rather than joining the legacy packages awaiting isolation migration.

---

## 6. Pre-declared legitimate implementation families

Recorded **before** authoring so the hidden architecture scorer cannot mistake a
**legal** solution for a violation. **None of these is a recommendation, and
several are deliberately ugly** — recording an alternative is not endorsing it.

| Family | Shape | Legal | Creates a forbidden edge? |
|---|---|---|---|
| **`ALT-A`** | `maxTotal` parsed at `api`; a primitive / options value passed inward to `features`; feature-side comparison | **yes** | no |
| **`ALT-C`** | **boundary-only enforcement** — `api` compares the ceiling against the total after `createOrderUseCase` returns its computed total; `features` untouched | **yes** | no |
| **`ALT-F`** | a **neutral transfer shape declared in `contracts`** | **yes** | no |
| **`ALT-H`** | a **primitive, or a predicate/callback, supplied through composition** | **yes** | no |
| **`ALT-I`** | a **`features`-owned request-scoped holder** populated from `api` | **yes** | no |
| **`ALT-K`** | a **permitted shared facility** (`contracts`, `core` or `observability`) used as a neutral transfer mechanism, **provided no forbidden `features → api` edge exists** | **yes** | no |

**Recorded explicitly:**

- **`ALT-C` is the strongest task-createdness counterexample, and it is cheaper
  than the feature-side implementation.** This is precisely why `CAND-A1`'s forcing
  class is natural-path rather than strict (§4, §2a of
  [`DEPENDENCY_TASK_FEASIBILITY.md`](DEPENDENCY_TASK_FEASIBILITY.md)).
- **`ALT-K` may also reduce violation frequency.**
- **Both consequences are expected and accepted.**
- **No hidden architecture rule may be designed around eliminating these legal
  alternatives.** A scorer tuned to force one arrangement would convert a
  construct-validity limitation into a measurement artefact.

**The expected violating implementation family is recorded privately and
conceptually only.** It is deliberately absent from this record's detail and must
**not** appear in the eventual public task prose.

---

## 7. What must not move before authoring

*As originally recorded*, `CAND-A1` was **not authored**, so nothing in the
experimental inventory changed. It was then publicly authored as `PT08` (§2a) and
**still nothing in the experimental inventory changed** — a public body carries no
private opportunity — so *as recorded then* every count stood exactly as it had:

- *As recorded then:* **Active `E1` opportunities remain 5.**
- *As recorded then:* **Decision clusters remain 3.**
- *As recorded then:* **Cluster observation depths remain 3 / 1 / 1**
  ([`DEPENDENCY_TASK_FEASIBILITY.md`](DEPENDENCY_TASK_FEASIBILITY.md) §3).
- *As recorded then:* **`DC-FEATURES-API-AR-DEP-006` remains at one observation.**
  No second observation exists in it, and none may be pre-counted.

**The cluster reaches two observations only after all four of these hold:**

1. the **public task is authored**;
2. an **independent public-authoring review passes**;
3. a **private evaluator package is subsequently authored and validated**;
4. **eligibility governance permits inclusion** (`TD-B05`/`TD-B14`/`TD-B32`, gate
   `G1`).

*As recorded then*, **exactly one of those four held: the first** — the public body
existed as `PT08`, its independent public-authoring review was **pending**, no
private evaluator package existed, and eligibility governance had admitted nothing,
so the cluster stood at **one** active observation and the second **could not be
pre-counted** on the strength of an authored public body alone. **That bar was
never waived; it was met.** All four conditions have since been satisfied in order
— the body was authored, its independent public-authoring review **passed**, a
private evaluator package was authored and **approved on a discharged conditional
independent review**, and a separately recorded governance admission step admitted
the opportunity.

**Current post-admission state, which supersedes the four counts above and nothing
else in this record:**

- **Active `E1` opportunities are 6.**
- **Decision clusters remain 3** — admission adds **depth**, never a cluster.
- **Cluster observation depths are 3 / 2 / 1.**
- **`DC-FEATURES-API-AR-DEP-006` carries two observations.** They are
  **pseudo-replicates** of one boundary decision and never two independent
  architecture constructs.

**One applicable opportunity is an instrument count.** It is **not** a violation,
**not** a success, **not** an outcome and **not** a result: nothing is frozen, gate
`G1` is not passed, `PT08` is not run-eligible, and no result, violation value or
treatment-effect estimate exists anywhere in this repository.

---

## 8. Pre-authoring `P1` disposition

| Finding | Disposition |
|---|---|
| **`P1-1`** — §12.1 requirement 5 ambiguity about a new request header | **CLOSED** by choosing the public query parameter `maxTotal`; **no special-header adjudication required**, because no special header is used (`SL-CA1-01`, §3) |
| **`P1-2`** — natural-path rather than strict forcing; a cheap boundary-only implementation exists and is cheaper than the features-side implementation | **CLOSED** by Study Lead acceptance of natural-path forcing as a recorded construct-validity limitation, with **Stage-1 `C1`-only** difficulty evaluation and **no `C4`/effect-based tuning** (`SL-CA1-02`, §4) |
| **`P1-3`** — the feasibility record did not distinguish task-createdness from forcing strength, leaving the `features → infra` versus `features → api` asymmetry unrecorded | **CLOSED** by recording the asymmetry in authoritative governance ([`DEPENDENCY_TASK_FEASIBILITY.md`](DEPENDENCY_TASK_FEASIBILITY.md) §2a) and in the private cluster register |
| **`P1-4`** — the completed `TD-B40`(B) independent re-approval occurred in an external read-only review and was propagated into neither repository | **CLOSED** by propagating that already-completed re-approval into both governance records ([`OPEN_DECISIONS.md`](OPEN_DECISIONS.md) `TD-B40`; [`DEPENDENCY_TASK_FEASIBILITY.md`](DEPENDENCY_TASK_FEASIBILITY.md) §8) |

**P0 count: 0.** No P0 finding was raised against `CAND-A1`.

*As recorded then:* **the overall `CAND-A1` authoring review was NOT finally
approved.** Closing the four P1 findings is remediation, not approval. **One
focused independent remediation re-review of this record was required, and
authoring could not begin before it passed.**

**That re-review has since happened and it PASSED.** Its verdict was **APPROVE —
PUBLIC AUTHORING MAY BEGIN**, and the sentence above is therefore history rather
than a live bar: the condition it stated is discharged, not waived. Public
authoring proceeded on that basis and produced `PT08` (§2a). Three things the
passed re-review did **not** do: it approved **no** private evaluator package, it
**replaced no** independent review of the authored public body, and it froze
**nothing** and passed **no** gate. *As recorded then*, neither of the first two
had happened at all. **Both have since happened as separate events** — the
independent public-authoring review of the body **passed**, and the private
evaluator package was **separately approved on a discharged conditional independent
review** — and **neither may be read off this re-review**, which remains the
narrow, earlier approval it always was. Nothing here is frozen and no gate is
passed.

---

## 9. Prohibitions attaching to this record

Stated so no later reader can extract a licence this record does not grant.
**Six of these have been amended by later packages recorded in §2a — five
superseded outright and one narrowed — and are kept here, marked, rather than
deleted; every other prohibition below is current and binding.** Three were amended
by the public-authoring package; three more by the separately reviewed private
evaluator package and the separately recorded opportunity admission.

- **No `PT08` identifier is assigned** by this record, here or anywhere — *as
  originally recorded*. **Superseded on this point only:** the separate
  public-authoring package assigned `PT08` (§2a). Nothing else in this list moved
  with it.
- **`CAND-A1` is not an authored public task** — *as originally recorded*.
  **Superseded on this point only:** it is now the authored public task `PT08`
  (§2a), whose independent public-authoring review has **passed**.
- **`CAND-A1` has no private evaluator package** — *as originally recorded*.
  **Superseded on this point only:** a private evaluator package for its authored
  body `PT08` has since been authored and **approved on a discharged conditional
  independent review** (§2a). Approval is **not** a freeze and **not** a gate pass.
- **`CAND-A1` has no manifest** — *as originally recorded*. **Superseded on this
  point only:** a private manifest for `PT08` exists at `status=review`; it is
  **not frozen**.
- **`CAND-A1` has no eligibility status** — *as originally recorded*. **Narrowed on
  this point only:** its authored body `PT08` carries the public
  `e1_analysis_eligibility` value `scored`, which records **intent** and is
  **never** a demonstrated denominator. *As recorded then*, no private eligibility,
  manifest field or denominator row existed for it; a private manifest and an
  admitted denominator row have since been authored and admitted (§2a), and the
  public `scored` value **still** records intent only, because the manifest is not
  frozen and `G1` is not passed.
- **`CAND-A1` enters no `E1` denominator row** — *as originally recorded*.
  **Superseded on this point only:** its authored body's single fixed architecture
  opportunity was admitted to the active `E1` denominator by a separately recorded
  governance step (§2a); the opportunity identifier stays **private**. The
  denominator **definition** is untouched: the numerator stays
  `violated_opportunity_count` and the denominator stays
  `applicable_opportunity_count`.
- **`CAND-A1` is not an active opportunity and is not counted as active** — *as
  originally recorded*. **Superseded on this point only:** its authored body carries
  one **active applicable opportunity**. That is an **instrument count** and encodes **no**
  violation, success, outcome or result.
- **`CAND-A1`'s forcing strength must not be represented as equal to a
  `features → infra` instrument's.**
- **`TD-B34` is not resolved by this record** and stays open and blocking on
  replication depth.
- **Nothing here is frozen**, no gate is passed, and no experiment is run-ready.
- **No benchmark or model result exists**, and none informed any pin above.
