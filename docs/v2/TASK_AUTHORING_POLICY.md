# docs/v2 — Public Task Authoring & Leakage Policy

Status: **development policy for study v2**. Governs how **public** v2 task files
are written so that no hidden design detail — architecture, hidden acceptance,
reset predicates, evaluator machinery — leaks into the task the coding model
sees. Development artifact only: it does **not** freeze the final benchmark
configuration, authorizes **no** paid model run, and freezes **no** task count
(see [`CRITICAL_DESIGN_DECISIONS.md`](CRITICAL_DESIGN_DECISIONS.md) D13).

Binding decisions: [`CRITICAL_DESIGN_DECISIONS.md`](CRITICAL_DESIGN_DECISIONS.md)
D2 (public task wording), D3 (implicit repository architecture). Enforced by
[`TASK_LEAKAGE_TERMS.yml`](TASK_LEAKAGE_TERMS.yml) +
`experiments/v2/tasks/validate_public_tasks.py` +
`experiments/v2/tasks/tests/test_public_task_leakage.py` +
`experiments/v2/harness/tests/test_public_task_integrity.py`. Blocker for the
authored suite: **`TD-B17`**.

---

## 1. The separation

Every v2 task has **two** parts:

| Part | Location | Visible to model? | Contains hidden design? |
|---|---|---|---|
| **Public task** | `experiments/v2/tasks/public/<id>.md` | **Yes** | **Never** |
| **Hidden evaluator package** | separate private evaluator repository (`TD-B04`/`TD-B05`) | **No** | **Yes** (rules, layer expectations, hidden acceptance, reset predicates, legitimate alternatives) |

The public task states **functional requirements and observable behaviour
only**. All architecture criteria — MAD rules, layer placement, dependency
directions, contract/port locations, boundary rules, architecture-specific
acceptance — and all evaluation machinery live **only** in the private evaluator
package.

## 2. Where public tasks live, and what counts as one

- Public task bodies live under **`experiments/v2/tasks/public/`**.
- **`TASK_INDEX.csv`** (in that directory) is the authoritative definition of the
  expected task set. A task file that is not indexed, and an indexed task with no
  file, are both failures.
- Discovery is **recursive** over `experiments/v2/tasks/`, so a task body nested
  in a subdirectory cannot escape scanning.
- The only supported task-body extension is **`.md`**. A task-like file (stem
  `PT01`, `PR02`, `T07`, …) with any other extension is **rejected**, never
  silently skipped.
- `README.md` and `TASK_AUTHORING_REPORT.md` are documented **non-task** files.
  The authoring report is a public handoff document, not a benchmark task, and is
  never counted as one.
- Nine **draft candidates** currently exist: seven primary (`PT01`–`PT07`, of
  which `PT07` was authored later under `DECISION B`) and two reserve
  (`PR01`–`PR02`). They are **candidates**: authored, **not approved and not
  frozen**. Current public eligibility: `PT01`–`PT04` and `PT07` `scored`,
  `PT05`/`PT06` `functional-only`, `PR01`/`PR02` `inactive-reserve`.

## 3. What is scanned

Validation covers **both** the task body and its front matter:

- **Front matter** — every string value and mapping key, at any nesting depth, in
  any list or mapping. YAML metadata is **not** safe merely because it is
  metadata: a leaky `title`, `notes`, or nested `hint` is leakage. Only the
  `leakage_exceptions` subtree is excluded, because a justification must be able
  to quote the term it excepts.
- **Body physical lines** — for precise line numbers.
- **Body logical text** — hard-wrapped prose joined within a paragraph or list
  item, so a phrase split across adjacent lines (`must not` / `import …`) is
  still detected. Headings, blank lines, list-item starts, table rows and fenced
  code blocks are unit boundaries, so unrelated paragraphs are never glued
  together and the normaliser cannot invent a phrase nobody wrote.

## 4. What a public task MUST NOT contain (fail closed)

The validator's **hard-leak** tier rejects, and no exception can permit, any of
these families (pattern ids in [`TASK_LEAKAGE_TERMS.yml`](TASK_LEAKAGE_TERMS.yml)):

| Family | Examples |
|---|---|
| MAD references | "MAD", "minimum architecture document" |
| Boundary instructions | module/layer boundaries, "enforce-module-boundaries", "cross-layer" |
| Follow-the-architecture language | "follow the architecture", "match the repository architecture" |
| Dependency directions | "must not import", "may only depend", "point inward" |
| Prescriptive layer names | "put X in the core layer" |
| Contract/port placement | "the port must live in …" |
| Architecture-specific acceptance | "must not violate the layering", "no boundary violation" |
| Prescribed repository paths | `libs/core/src/…`, `apps/api/…`, `docs/v2/…`, `@afci-bench/…` |
| Source filenames as instructions | "wire it in `app.ts`", "export it from `index.ts`" |
| Required/prohibited placement | "required areas", "must be placed under …" |
| Hidden-test / withheld-grading clues | "the withheld grading suite asserts …", "the graders check …" |
| Reset / checkpoint / restart clues | "checkpoint CK-…", "your session is restarted", `--continue` |
| Condition names | `C1`, `C2`, `C3`, `C4`, "token-matched", "placebo", "AFCI" |
| Opportunity and rule ids | `OPP-…`, `AR-…`, "fixed opportunity set", "rule id" |
| Evaluator / oracle clues | "oracle", "evaluator", `oracle_result.json`, "scored" |
| Expected implementation | "the expected implementation adds …", "reference solution" |
| Legitimate-alternative disclosures | "a legitimate alternative is …" |

## 5. Ambiguous terms → review, not blanket rejection

Some words (`layer`, `contract`, `port`, `module`, `architecture`, `boundary`,
`dependency`, `repository`, `use case`, `adapter`, and configuration filenames)
appear in perfectly ordinary functional writing (a "caching layer", a "network
port", a "service contract" in the business sense). Blanket rejection would be
wrong. The validator's **review-required** tier flags these for human review. A
flagged occurrence passes **only** if the task carries a matching **approved,
reviewed exception**.

### Exception format (task front matter)

```markdown
---
leakage_exceptions:
  - id: RR-LAYER                  # the review-required pattern id / category
    location: "body:14"           # exact location: body:<line> or front-matter:<key>
    match: "caching layer"        # optional: scope the exception to this text
    justification: "Functional in-memory caching layer, not a repository layer."
    reviewer: "oracle-designer"
    approved: true                # approval state
---
```

An exception is valid **only** if it targets a review-required id (never a
hard-leak id) **and** carries a non-empty `location`, a non-empty
`justification`, a non-empty `reviewer`, and an affirmative `approved`. A
malformed, unapproved, or mislocated exception **fails closed** — the underlying
finding is treated as un-reviewed leakage. An exception covers only the finding
at its stated location; it never blanket-covers a pattern across the file.

## 6. What a clean validator run does and does not mean

A `[OK]` result means **no detected leakage** by the current term set. It is
**not**:

- proof that the task is scientifically valid;
- proof that the task is well specified, unambiguous, or feasible against the
  frozen base substrate;
- proof that no undetected leakage family exists;
- a substitute for the independent freeze review that closes `TD-B17`.

Functional completeness, ambiguity, wire-format determinacy and base-SHA
feasibility are reviewed **separately** and are recorded in
[`../../experiments/v2/tasks/public/TASK_AUTHORING_REPORT.md`](../../experiments/v2/tasks/public/TASK_AUTHORING_REPORT.md).

## 7. Implicit repository architecture (D3)

The coding model **may inspect the actual repository substrate** it is given;
folder names and existing code are not hidden. Which files the model's worktree
contains is governed by
[`MODEL_VISIBLE_WORKTREE_POLICY.md`](MODEL_VISIBLE_WORKTREE_POLICY.md): the
source substrate (`apps/`, `libs/`, build/test configuration) is present so the
implicit architectural tension is real, while every explicit architecture
document, protocol document, oracle implementation and evaluator artifact is
excluded.

Therefore a good public task deliberately includes a **realistic architectural
decision point** where the locally convenient implementation could conflict with
a global rule — without ever *naming* the rule. The task reads as a normal
engineering request; the architectural tension is real but implicit.

**Task hardening uses baseline-only difficulty criteria** (does the unguided C1
baseline make the mistake often enough to measure?), **never** the size of the
observed C4 advantage.

## 8. Wire-format determinacy (fairness)

A public task must leave **no response key, request key, status code, or asserted
error value** to evaluator guesswork:

- every JSON request body the caller sends is stated with its exact keys;
- every JSON response body is stated with its exact keys;
- every status code is stated;
- where an `error` value is pinned, the task states the exact string; where it is
  **not** pinned, the task says so explicitly, and the private evaluator package
  may then assert only the HTTP status, a non-empty `error`, and a non-empty
  `message`;
- where result ordering is not required, the task says so, and validation must be
  order-independent.

A private hidden test may **never** enforce a string, key, or ordering the public
task did not state.

## 8a. Functional acceptance observation boundary (`TD-B39`)

§8 constrains **what** a hidden test may assert. This constrains **what it may
look at** to decide. The normative statement lives in
[`HIDDEN_EVALUATOR_BOUNDARY.md`](HIDDEN_EVALUATOR_BOUNDARY.md) §9–§14; the rules
an author must satisfy are:

1. **HTTP request/response is the default observation surface.** A task should be
   writable so that its completion criteria are decidable from status codes,
   response headers and response bodies alone.
2. **An explicitly declared application seam is permitted only** when the public
   task requires an **externally emitted behaviour that cannot be faithfully
   observed through HTTP**. Exactly one seam is declared suite-wide — the
   `LogOutput` sink supplied through `createApp({ logOutput })`, grounded in
   `PT04` — and it is registered in `HIDDEN_EVALUATOR_BOUNDARY.md` §12.
3. **A seam must be declared before hidden-test implementation.** A hidden test
   may not create a seam; discovering the need while writing hidden tests means
   amending the public task (§10) or dropping the assertion.
4. **Hidden acceptance may not inspect implementation-specific persistence, module
   state, classes, files, or architecture findings** to decide pass or fail.
5. **Hidden state seeding through implementation modules is prohibited.** A
   precondition that is not reachable through the public interface is an
   unreachable-setup blocker for the task (`TD-B31`), not a licence to reach
   inside.
6. **A conforming implementation with a different internal design must remain
   gradeable.** An assertion that can only pass under one internal design is
   inadmissible.
7. **Test isolation is not an acceptance oracle.** Cases are isolated by a freshly
   constructed application over a freshly evaluated module graph;
   `resetOrderRepository()` is legacy baseline-test infrastructure, not an
   approved evaluator mechanism and never evidence for an assertion.
8. **Architecture scoring and functional acceptance stay channel-separated** —
   neither result is an input to the other.

This boundary is decided **before** any further hidden acceptance is written, so
no task's grading surface can be chosen after its assertions exist.

## 9. v1 reuse boundary

v1 task **concepts** may be reused; v1 task **wording is not reused** (D2). The
validator **never** scans or modifies v1/v0 material (`archive/`,
`experiments/tasks_v0/`); it refuses any such path.

## 10. Private evaluator re-linking (hash coupling)

Each public task's SHA-256 is recorded in `TASK_INDEX.csv` and
[`PILOT_PUBLIC_TASK_MATRIX.csv`](PILOT_PUBLIC_TASK_MATRIX.csv), and is checked
mechanically by `test_public_task_integrity.py`.

**Whenever a public task body changes, its hash changes, and every private
evaluator package pinned to the old hash becomes stale.** A stale private package
must be **re-linked and re-reviewed** before it may be frozen or used; a private
manifest hash must **never** be silently accepted against a changed public task.
See the staleness record in
[`../../experiments/v2/tasks/public/TASK_AUTHORING_REPORT.md`](../../experiments/v2/tasks/public/TASK_AUTHORING_REPORT.md).

## 11. Authoring checklist

1. Write the functional requirement and the observable behaviour only.
2. State every request key, response key, status code and pinned error value
   (§8); say explicitly where a value is not pinned.
3. Verify the task is feasible **against the frozen base substrate** — the
   endpoints, fields and failure paths it refers to must actually exist there, or
   the task must create them.
4. Put every architecture rule and hidden acceptance criterion in the private
   evaluator package (`TD-B04`/`TD-B05`).
5. Run `python experiments/v2/tasks/validate_public_tasks.py` — it must report
   `OK` for every public task and no structural failure.
6. For any review-required flag that is genuinely functional, add an approved,
   located, justified exception; otherwise rewrite the sentence.
7. Update `TASK_INDEX.csv`, `PILOT_PUBLIC_TASK_MATRIX.csv` and the authoring
   report, then run `test_public_task_integrity.py` so the recorded hashes match.
8. Record that the affected private evaluator packages are now stale (§10).
9. Never tune wording or difficulty toward a larger C4 effect (D3).

## 12. Requirements for the NEXT architecture tasks (DECISION B, `TD-B34`)

**No task is authored by the package that records these requirements.** They are
the acceptance bar for the **next** authoring work package, recorded in advance so
authoring cannot drift toward whatever is convenient later.

> **`TD-B34` has been re-scoped (§12.2c).** It no longer directs authoring toward
> additional leaf rules or additional source scopes: an independent remaining-leaf
> feasibility review established that the canonical substrate has a **hard
> task-creatable ceiling of 3 decision clusters, 2 leaf rules, 2 source scopes and
> 3 forbidden targets**, and that all three achievable clusters are **already
> represented** ([`DEPENDENCY_TASK_FEASIBILITY.md`](DEPENDENCY_TASK_FEASIBILITY.md)).
> `TD-B34` now governs **adequate coverage of the complete task-creatable decision
> space** — that is, **replication depth and balance** across the three
> demonstrated clusters. §12.1's requirements are unchanged and still bind;
> requirement 3 is read as §12.2c states.

**Why the decision stays open.** After the pre-authoring opportunity reassessment
(`PT05` reclassified `functional-only`, `TD-B35`) and the authoring of `PT07`, the
active set carries **5** E1 opportunities over **3** decision clusters, **two of
which are singletons**. Several tasks that each re-expose the **same** boundary
are **one** architectural instrument observed repeatedly, not several independent
architecture constructs; and one observation of a boundary is a thin instrument
whichever boundary it is. The motivation is therefore **construct validity**. It
is **not** an oracle failure: the scope-based attribution mechanism (§1a of
[`ORACLE_VALIDATION_REQUIREMENTS.md`](ORACLE_VALIDATION_REQUIREMENTS.md)) remains
the approved mechanism. This decision **predates any benchmark or model outcome**;
**no experimental result exists**; and **no reserve may be activated merely to
restore a task count**.

### 12.1 Requirements every candidate must satisfy

1. **It creates a genuine dependency decision caused by the required functional
   work.** The functional requirement itself must force a source-to-target choice.
2. **It does not merely preserve an already-satisfied boundary.** Re-passing a
   boundary the base already satisfies is a *preservation-only* opportunity and
   does not count — this is the same **task-created decision** test that removed
   the preservation-only opportunities in the reassessment.
3. **It exercises a dependency leaf / source-target decision not already
   represented** by the surviving active set, wherever the substrate permits.
   **On the canonical substrate the substrate no longer permits it**: all three
   task-creatable clusters are represented and the remaining leaves are not
   task-creatable (§12.2, §12.2c). Requirement 3 is therefore satisfied on this
   substrate by an **independent instrument inside an under-replicated cluster**
   — a decision that is functionally distinct from the tasks already occupying it
   — and is **not** satisfied by an artificial task written to reach a
   mechanically implemented leaf that no functional requirement can create.
4. **It is feasible through the public interface** of the unchanged source
   substrate (§11.3, and the suite-wide reachability requirement `TD-B31`).
5. **It avoids implementation-dependent hidden setup** — no failure-injection
   hook, test-only route, special header, or environment flag.
6. **Its opportunity is fixed before model output** — frozen at authoring time,
   never inferred from what a model produced.
7. **It remains compatible with legitimate implementation alternatives** — more
   than one correct shape must be able to satisfy it.
8. **It does not depend on which file the model creates.** Scoring is anchored on
   the frozen architectural **scope**, so a candidate whose decision exists only in
   one particular file is inadmissible.
9. **It avoids task overlap severe enough to duplicate an existing architectural
   instrument.**
10. **Its public wording stays functional-only, with no architecture hint** — §4
    and §5 apply unchanged, and the leakage validator must report `OK`.
11. **Its functional completion criteria are decidable within the observation
    boundary** (§8a). A candidate that would need an undeclared seam, internal
    persistence inspection, or state seeded through implementation modules is
    inadmissible; if it needs a seam, that seam is declared and registered
    **before** its hidden tests are written.

### 12.2 The boundary space available under already-implemented leaf rules

Public information only, derived from
[`ARCHITECTURE_RULE_CATALOG.yml`](ARCHITECTURE_RULE_CATALOG.yml) and the frozen
dependency matrix — **not** from any private manifest.

**The 15 theoretical `(source scope, forbidden target)` pairs below are NOT 15
feasible benchmark decisions.** Mechanical detectability is a property of the
checker; task-creatability is a property of the substrate plus the observation
boundary (§8a). The **feasibility status** column is normative and is derived from
[`DEPENDENCY_TASK_FEASIBILITY.md`](DEPENDENCY_TASK_FEASIBILITY.md) §2.

| Leaf rule | Source scope | Forbidden targets it can back | Feasibility status |
|---|---|---|---|
| `AR-DEP-002` | contracts | core, features, infra, observability, api | **NOT TASK-CREATABLE ON CURRENT SUBSTRATE** — mechanically detectable only |
| `AR-DEP-003` | core | features, infra, observability, api | **NOT TASK-CREATABLE ON CURRENT SUBSTRATE** — mechanically detectable only |
| `AR-DEP-004` | infra | core, features, api | **NOT TASK-CREATABLE ON CURRENT SUBSTRATE** — mechanically detectable only |
| `AR-DEP-005` | api | core | **TASK-CREATABLE / REPRESENTED** (`api → core`) |
| `AR-DEP-006` | features | infra, api | **TASK-CREATABLE / REPRESENTED** (`features → infra`, `features → api`) |
| *(none)* | observability | — | **UMBRELLA-ONLY / NO SCORED LEAF** — see §12.3 |

Source scopes, stated plainly: **`contracts` not task-creatable**; **`core` not
task-creatable**; **`infra` not task-creatable**; **`api → core` task-creatable and
represented**; **`features → infra` task-creatable and represented**;
**`features → api` task-creatable and represented**; **`observability` source
umbrella-only, with no scored leaf**.

The earlier list of decisions to *investigate* — an `infra → core` decision backed
by `AR-DEP-004`, a `core → forbidden layer` decision backed by `AR-DEP-003`, and a
`contracts`-source decision backed by `AR-DEP-002` — has been **investigated and
closed**: each was found **not task-creatable** on this substrate for the reasons
recorded in [`DEPENDENCY_TASK_FEASIBILITY.md`](DEPENDENCY_TASK_FEASIBILITY.md) §2.
The remaining entry, a genuine **`api → core`-only capability** decision backed by
`AR-DEP-005`, was adopted and is represented.

**No new architecture-rule family is required for this remedy**, because these
leaf relationships are **already implemented** — and implementing one would not
help either, since the constraint is substrate feasibility rather than checker
coverage. Implementing further rule families stays future work (`TD-B33`) and must
never readmit an excluded task post hoc.

### 12.2a Coverage of the surviving active set, and one candidate cleared for authoring

Aggregate suite-level statement only. No private opportunity identifier, hidden
test, hidden acceptance detail or implementation answer appears here or anywhere
else in the public repository.

**What the surviving active set covers.** After the reassessment removed the
preservation-only opportunities (requirement 2 above), every retained active
dependency decision sits in **one source scope** and under **one leaf rule**. Using
the conceptual cluster identifier
`decision_cluster_id = source_scope + forbidden_target + leaf_rule`, the active set
spans **two** clusters, both sourced from `features` and both backed by
`AR-DEP-006`. That is precisely the construct-validity deficiency `TD-B34` records:
too few *distinct* boundaries, not too few tasks.

**Consequently `AR-DEP-005` (`api → core`) is currently unrepresented.** No
retained active opportunity uses the `api` source scope, and none uses the
`AR-DEP-005` leaf rule. Preservation-only rows naming that boundary are still
physically present in the stale private manifests and are **pending removal**
(`TD-B40`); they are **analytically inactive** and must not be counted as active
coverage by any later work package.

**One candidate has passed pre-authoring feasibility review.** A candidate whose
dependency decision would use an implemented leaf rule and a source scope that the
surviving active set does not currently represent has been reviewed against
requirements 1–11 and §8a and found feasible:

- its decision would introduce a **new** `decision_cluster_id`, a **new** source
  scope and a **new** leaf rule relative to the surviving active set;
- its functional work **creates** the decision rather than preserving an
  already-satisfied boundary (requirement 2);
- its completion criteria are decidable through **HTTP alone** — no declared seam,
  no internal-state inspection, no seeded state (requirement 11 / §8a).

**No task body has been authored**, no task was added to `TASK_INDEX.csv`, no hash
changed, and no reserve was activated. The candidate's private opportunity details,
its identifier and its hidden acceptance remain private until the normal evaluator
package is created. `TD-B34` stays **open and blocking**: one cleared candidate is
not a suite.

> **Superseded on the coverage counts only** (§12.2b, §12.2c). The candidate above
> was authored as `PT07`, and the independently adjudicated active set now spans
> **three** clusters over **two** source scopes and **two** leaf rules, so
> `AR-DEP-005` and the `api` source scope are **no longer unrepresented**. The
> paragraphs above remain an accurate record of the state they describe; the
> current counts are in
> [`DEPENDENCY_TASK_FEASIBILITY.md`](DEPENDENCY_TASK_FEASIBILITY.md) §3. `TD-B40`
> is **unaffected**: the preservation-only rows are still physically present in
> the stale private manifests and still must be removed.

### 12.2b The cleared candidate is now authored as `PT07` (`TD-B34` still open)

The candidate cleared in §12.2a has since been authored as the public task body
`PT07` — *Price a proposed order before it is placed* (`pricing-endpoint`,
`primary`, `e1_analysis_eligibility` `scored`, `task_status` `candidate`). The
authoring package added **one** task body and nothing else: no other task body or
hash changed, no other eligibility changed, no reserve was activated, no file under
`apps/` or `libs/` was touched, no private evaluator material was authored or
modified, no benchmark or model ran, and nothing was frozen.

- **It was authored before any benchmark or model execution**, and its design and
  public-interface feasibility were **independently reviewed before** authoring
  against requirements 1–11 above and §8a.
- **In aggregate terms it adds a previously unrepresented implemented
  leaf/source-scope candidate.** Which leaf rule, source scope and forbidden target
  its decision uses stay **private**, as for every other candidate: no public
  artifact maps `PT07` to a rule id, an opportunity, or an expected or prohibited
  area.
- **It is decidable through HTTP alone** (requirement 11 / §8a): no declared seam,
  no internal-state inspection, no seeded state, and **no non-persistence
  assertion**. A non-persistence criterion was considered and **rejected as
  externally ungradeable** — the substrate exposes no public way to observe stored
  state, and reaching for it internally is exactly what §8a forbids. What `PT07`
  requires is the observable consequence: its answer carries none of the fields
  that identify a created order.
- **`PT07` cannot enter E1 until a private evaluator package is authored for it**,
  independently validated and approved, and shown to carry a valid non-zero frozen
  opportunity set (`TD-B05`/`TD-B14`, gate `G1`). Its public eligibility of
  `scored` records intent, never a demonstrated denominator.

**`TD-B34` is NOT resolved.** One authored task does not provide the breadth or the
repetition the confirmatory construct needs; the active set plus `PT07` still does
not sample enough distinct dependency-direction decisions for confirmatory
inference. **Further candidate authoring is still required before Stage 0**, **no
power simulation may be run yet** (`TD-B37`), and gates **G1**/**G2**/**G6** remain
**not passed**.

Overlap safeguards for `PT07` against `PT05`, `PR01`, `PT06`, `PT01`/`PT02` and
`PT04` (requirement 9) are recorded in
[`TASK_AUTHORING_REPORT.md`](../../experiments/v2/tasks/public/TASK_AUTHORING_REPORT.md).
They are **governance rationale only** and deliberately appear nowhere in `PT07`'s
public text.

### 12.2c `TD-B34` re-scoped: replication depth over the complete feasible space

An independent remaining-leaf feasibility review has now assessed every remaining
implemented leaf against the canonical substrate and the observation boundary. Its
result is recorded normatively in
[`DEPENDENCY_TASK_FEASIBILITY.md`](DEPENDENCY_TASK_FEASIBILITY.md): `AR-DEP-002`
(`contracts`), `AR-DEP-003` (`core`) and `AR-DEP-004` (`infra`) are **theoretically
detectable but not task-creatable** on this substrate, so the demonstrated ceiling
is **3 decision clusters / 2 leaf rules / 2 source scopes / 3 forbidden targets**,
and **all three achievable clusters are already occupied**.

**Consequently `TD-B34` now governs adequate coverage of the COMPLETE
task-creatable dependency-decision space**, not an expansion of it. Its objective:

1. **Retain all three demonstrated clusters.** None may be dropped, merged or
   traded away.
2. **Add independent functional instruments to the singleton clusters where
   scientifically feasible.** An added instrument must be a genuinely distinct
   functional decision, not a paraphrase of the task already in that cluster.
3. **Do not author artificial tasks merely to hit mechanically implemented
   leaves.** A leaf that no functional requirement can create is not a target
   (§12.3).
4. **Document the substrate breadth ceiling as a construct-validity limitation**
   of the study, reported rather than engineered away
   ([`RESEARCH_QUESTIONS.md`](RESEARCH_QUESTIONS.md) CON-AC;
   [`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md) §2.2).
5. **Defer any broader leaf/source-scope generalisation to a declared substrate
   redesign** ([`DEPENDENCY_TASK_FEASIBILITY.md`](DEPENDENCY_TASK_FEASIBILITY.md)
   §7) rather than pretending the current substrate can support it.

**Priority replication targets**, in order:

| Priority | `decision_cluster_id` | Current observations |
|---|---|---|
| **A** | `DC-FEATURES-API-AR-DEP-006` | **1** |
| **B** | `DC-API-CORE-AR-DEP-005` | **1** |
| — | `DC-FEATURES-INFRA-AR-DEP-006` | **3** — already replicated; **not** the immediate priority |

**No exact new task body is specified here, and it is not asserted that two
suitable new tasks exist.** Whether a candidate for either priority cluster is
functionally distinct from the tasks already occupying it, and whether its
required work genuinely *creates* the decision rather than preserving it
(requirement 2), remain **open questions for a separate pre-authoring review**
under requirements 1–11. `TD-B34` stays **open and blocking** until that review
has happened and its outcome is independently approved.

### 12.3 What is forbidden

- **Do not create artificial tasks merely to hit rule ids.** A candidate that
  names a rule relationship without the functional work creating the decision
  fails requirement 1 and must be rejected. This applies with full force to the
  leaves the feasibility review classified **not task-creatable** (`AR-DEP-002`,
  `AR-DEP-003`, `AR-DEP-004`): they are **mechanically detectable only**, and a
  task written to reach one would either be preservation-only or would need
  implementation-specific wording. Neither is admissible.
- **Do not treat a mechanically detectable pair as an available benchmark
  decision.** The 15 theoretical `(source scope, forbidden target)` pairs in §12.2
  are not 15 feasible decisions; only the three annotated **TASK-CREATABLE /
  REPRESENTED** clusters are, and all three are occupied.
- **Do not target the `observability` scope for a scored opportunity, as source or
  as target.** The dependency family implements **no leaf clause** for
  `observability` as a **source**: `leafRuleFor('observability', target)` returns
  `null` for every target, so such an edge is **umbrella-only under `AR-DEP-001`**
  — visible in raw exposure, never eligible as a scored opportunity — and the
  oracle refuses such an opportunity (`OPPORTUNITY_RULE_SCOPE_MISMATCH`)
  regardless of wording.
- **Do not rely on a test-only or configuration-only dependency.** E1 is computed
  from the **production** dependency graph, so a decision that exists only in a
  `*.spec.ts`, under `__tests__/`, or in `jest.config.ts` carries **no** E1
  exposure (§1b of `ORACLE_VALIDATION_REQUIREMENTS.md`).
- **Do not activate a reserve in place of authoring.** `PR01`/`PR02` remain
  inactive, and `PR02` remains blocked (`TD-B26`).
