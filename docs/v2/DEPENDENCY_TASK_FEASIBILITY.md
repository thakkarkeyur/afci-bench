# docs/v2 — Dependency-Decision Task Feasibility (canonical substrate)

Status: **development record for study v2**. It records which
dependency-direction decisions the **canonical source substrate** can actually be
made to *create* through a public functional task, and which it cannot. It is a
governance record only: it authorizes **no** paid model run, freezes **no**
benchmark configuration, authors **no** task, changes **no** task body or hash,
touches **no** file under `apps/` or `libs/`, activates **no** reserve, accesses
**no** private evaluator material, runs **no** power simulation and **produces no
power value**. The protocol remains **PRE-FREEZE**.

Substrate: [`SOURCE_SUBSTRATE_IDENTITY.md`](SOURCE_SUBSTRATE_IDENTITY.md).
Rules: [`ARCHITECTURE_RULE_CATALOG.yml`](ARCHITECTURE_RULE_CATALOG.yml).
Authoring bar: [`TASK_AUTHORING_POLICY.md`](TASK_AUTHORING_POLICY.md) §12.
Blocker: **`TD-B34`**. Test:
`experiments/v2/harness/tests/test_dependency_feasibility.py`.

---

## 1. Two different questions, deliberately not conflated

| Question | Answered by | What a "yes" means |
|---|---|---|
| **Is the edge mechanically detectable?** | the frozen dependency matrix + the implemented leaf clauses in `experiments/v2/oracle/` | if such an edge existed in a patch, the oracle would find and attribute it |
| **Is the decision task-creatable?** | this document | a **public, functional-only** task can force a model to *make* that decision, and a **black-box functional acceptance** test can grade the task without seeing where the code was placed |

**A mechanically detectable relationship is not automatically an experimentally
usable one.** The oracle's coverage of the dependency matrix is a property of the
*checker*; whether a scored opportunity can be *created* is a property of the
*substrate plus the observation boundary*
([`HIDDEN_EVALUATOR_BOUNDARY.md`](HIDDEN_EVALUATOR_BOUNDARY.md) §9–§14). Nothing
in this document may be read as claiming that a detectable pair is a feasible
benchmark decision, and nothing in the boundary-space inventories
([`TASK_AUTHORING_POLICY.md`](TASK_AUTHORING_POLICY.md) §12.2;
[`TASK_AUTHORING_REPORT.md`](../../experiments/v2/tasks/public/TASK_AUTHORING_REPORT.md))
may be either.

**What this document publishes, and what it does not.** It publishes
**suite-level** counts: which leaf rules and source scopes are task-creatable, how
many decision clusters exist, and how many active observations each cluster
currently carries. It maps **no task** to a leaf rule, a source scope, a forbidden
target or a cluster; those mappings, and every per-task opportunity, stay in the
private evaluator repository exactly as before.

> **Disclosed consequence, recorded rather than hidden.** Publishing the cluster
> inventory of §3 is a deliberate Study Lead choice: it is the evidence `TD-B34`'s
> re-scope rests on, and coverage cannot be adjudicated without it. It does carry
> an **inference cost**. The public record already states that the pre-`PT07`
> active set sat under one source scope and one leaf rule, and that `PT07`
> introduced a new source scope and a new leaf rule; against §3 a reader can
> therefore infer which cluster `PT07`'s decision occupies. Which of the earlier
> scored candidates share a cluster remains **not** inferable, and no public
> artifact states it. Nothing here changes what the coding model sees — `docs/v2/`
> is excluded from every condition's worktree by
> [`MODEL_VISIBLE_WORKTREE_POLICY.md`](MODEL_VISIBLE_WORKTREE_POLICY.md) — so the
> cost is to reviewer-facing blinding of one candidate's expected area, not to the
> experiment's baseline.

---

## 2. Remaining-leaf feasibility result (normative)

Assessed independently against the canonical substrate, **before any benchmark or
model execution**, from the public task bodies, the unchanged substrate and the
observation boundary only.

### `AR-DEP-002` — source scope `contracts`

**Classification: THEORETICALLY DETECTABLE BUT NOT TASK-CREATABLE ON CURRENT
SUBSTRATE.**

- `contracts` is **type/interface-only** and is **erased at runtime**, so no
  externally observable behaviour depends on what it imports;
- **black-box functional acceptance cannot force production work there** — no HTTP
  observation distinguishes a solution that edits `contracts` from one that does
  not;
- **TypeScript structural typing allows local declarations**, so a conforming
  solution may declare the shape it needs wherever it likes;
- consequently any scored `contracts`-source opportunity would be
  **preservation-only** — it would re-pass a boundary the base already satisfies,
  which requirement 2 of the authoring bar rejects.

### `AR-DEP-003` — source scope `core`

**Classification: THEORETICALLY DETECTABLE BUT NOT TASK-CREATABLE ON CURRENT
SUBSTRATE.**

- **architecture-neutral functionality cannot force placement in `core`** — a
  public task may not name a layer, so nothing in its text can require the
  computation to live there;
- `core` is **pure and self-sufficient over plain data and `contracts`**, so a
  computation placed there needs no outward import in the first place;
- **callers may legally implement or wrap the functionality in `features` or
  `api`**, and such a solution is fully conforming;
- **persistence and logging are already served through ports/injection**, so the
  usual pressure that would drag `core` outward does not arise;
- **hidden acceptance cannot distinguish where the computation lives** without
  inspecting implementation-specific structure, which the observation boundary
  forbids.

### `AR-DEP-004` — source scope `infra`

**Classification: THEORETICALLY DETECTABLE BUT NOT TASK-CREATABLE ON CURRENT
SUBSTRATE.**

- **persistence-shaped requirements can be satisfied at `api` level** under the
  current observation topology, so the functional work need never enter `infra`;
- **`infra` entities structurally mirror the `core` domain shapes**, so an adapter
  can carry its own representation without importing `core`;
- **`infra` may legally use `contracts` and `observability`**, which covers the
  shapes and the cross-cutting concerns it would otherwise reach for;
- **no functional contract can force a forbidden `infra` → `core`/`features`/`api`
  edge** without implementation-specific wording, which a public task body may not
  contain.

### `AR-DEP-005` — source scope `api`, forbidden target `core`

**Classification: TASK-CREATABLE.** Currently represented by **one** decision
cluster in the active set: `api → core`.

### `AR-DEP-006` — source scope `features`

**Classification: TASK-CREATABLE.** Currently represented by **two** decision
clusters in the active set: `features → infra` and `features → api`. The two are
**equally task-creatable** and **not equally forced** — see §2a, which is
normative and must be read with this classification.

---

## 2a. Task-createdness is not forcing strength (normative)

§2 answers exactly one question per `(source scope, forbidden target)` pair: **can
a public functional task CREATE the decision at all?** That is a binary, and it is
the only question §2 ever settled. It is **not** the same question as: **must every
externally equivalent conforming implementation CONFRONT the decision?**

An independent Priority-A pre-authoring review established that the two
represented `AR-DEP-006` decision families answer the second question
**differently**, and that the difference was recorded nowhere. It is recorded here,
in the authoritative feasibility record, so no later reader can take
*task-creatable* to mean *strictly forced*.

**`AR-DEP-006` is task-creatable for both represented forbidden targets. The two
existing decision families have different forcing strength on the canonical
substrate.**

| Decision family | Task-creatable? | Forcing strength | Boundary-only conforming solution? |
|---|---|---|---|
| `features → infra` (`DC-FEATURES-INFRA-AR-DEP-006`) | **yes** | **STRONG / STRICT task-created forcing** | **no** |
| `features → api` (`DC-FEATURES-API-AR-DEP-006`) | **yes** | **NATURAL-PATH / OPPORTUNITY-CREATING forcing** | **yes** |

**`features → infra` — strong/strict task-created forcing.** In the retained
instruments the functional contract requires **persistence/query behaviour that
cannot be satisfied without confronting the dependency decision**. A conforming
implementation must resolve the source-to-target choice; it cannot route around it
and still pass.

**`features → api` — natural-path / opportunity-creating forcing.** A public
functional task **can** make an `api`-owned boundary datum relevant to feature
computation and **can** create a plausible forbidden reach-back. But `api` is the
**editable composition/boundary layer**, so **some externally equivalent conforming
implementations may solve the required behaviour entirely at the boundary without
touching `features` at all**. The decision is genuinely *created*; it is not
*compelled*.

**Consequences, stated so none can be paraphrased away:**

- **Task-creatable does NOT mean every valid implementation must encounter the
  forbidden decision.** The two properties are independent and only the first was
  ever demonstrated by §2.
- **`features → api` instruments may have weaker forcing than `features → infra`
  instruments.** Where they do, the difference must be reported, not smoothed over.
- **This does not invalidate `PT04`, and it does not invalidate the `CAND-A1`
  candidate** ([`CAND_A1_PREAUTHORING_DECISION.md`](CAND_A1_PREAUTHORING_DECISION.md)).
  Both remain task-created decisions under requirement 1 of the authoring bar.
- **It is a construct-validity limitation of the study**, carried as such
  ([`RESEARCH_QUESTIONS.md`](RESEARCH_QUESTIONS.md) CON-AC;
  [`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md) §2.2), not a
  defect to be engineered away and not a reason to withdraw an instrument.
- **Replication inside `DC-FEATURES-API-AR-DEP-006` estimates behaviour under this
  naturally induced decision pressure**, not under a strictly forced architecture
  fork. An effect observed there must be reported against that description of the
  instrument.
- **Baseline-only Stage-1 difficulty checks remain required** for any instrument in
  this family: discriminative difficulty is evaluated on **C1 baseline** behaviour
  only ([`PILOT_AND_POWER_POLICY.md`](PILOT_AND_POWER_POLICY.md), D3).
- **No treatment-dependent task tuning is permitted.** Difficulty is never tuned on
  `C4`, on an observed AFCI advantage, or on any treatment-effect estimate.
- **Within-cluster observations remain pseudo-replicates** — statistically
  clustered exposures of one instrument — and are never entered as independent
  architecture decisions (`TD-B30`, `TD-B37`).

**What §2a does NOT do.** It does **not** redefine `E1`; it does **not** change the
feasibility ceiling of §3; it adds **no** decision cluster; and it reopens **none**
of `AR-DEP-002`, `AR-DEP-003` or `AR-DEP-004`, which stay classified **not
task-creatable** on this substrate. `api → core` / `AR-DEP-005` is **deliberately
not adjudicated** for forcing strength: the review assessed the two `AR-DEP-006`
families only, no adjudication of that family was supplied, and none is invented
here. The private cluster register carries the same fields per cluster, including
the explicit *not adjudicated* marker, so the distinction is machine-checkable
rather than a matter of reading prose.

This closes pre-authoring finding **`P1-3`**.

---

## 3. The demonstrated feasibility ceiling

On canonical substrate
`630d3180af0d02a86330dfb599f559e78df65e94`, content hash
`0198d76c189f38589e872cab4305527c08e86ef736e1550e428e05f9178060f3`, the
**demonstrated maximum task-creatable dependency-direction decision space** is:

| Dimension | Ceiling |
|---|---|
| **decision clusters** (`source_scope + forbidden_target + leaf_rule`) | **3** |
| **leaf rules** | **2** |
| **source scopes** | **2** |
| **forbidden targets** | **3** |

**Current occupancy is already 3 / 3 clusters.** The three achievable clusters are
each represented in the active set:

| `decision_cluster_id` | Source scope | Forbidden target | Leaf rule | Active observations |
|---|---|---|---|---|
| `DC-FEATURES-INFRA-AR-DEP-006` | `features` | `infra` | `AR-DEP-006` | **3** |
| `DC-FEATURES-API-AR-DEP-006` | `features` | `api` | `AR-DEP-006` | **1** |
| `DC-API-CORE-AR-DEP-005` | `api` | `core` | `AR-DEP-005` | **1** |

Active E1 opportunities: **5**. Decision clusters: **3**. Leaf rules: **2**.
Source scopes: **2**. Forbidden targets: **3**.

> These are the **independently adjudicated active** counts — the
> preservation-only rows `TD-B40` ordered removed are excluded, and that removal
> has since been **performed** under separate authorised private work: no such row
> appears in any manifest opportunity set or any E1 denominator, and each survives
> only as a **superseded, detection-only historical record**. `TD-B40` is now
> **resolved and closed**: its residual **inactive-reserve** reconciliation and its
> outstanding **independent re-approval** are both complete, the complete migration
> having been **independently re-approved** in an external read-only re-review.
> **Closure changes none of these counts and freezes nothing** — no manifest is
> frozen, gate `G1` is not passed, and no reserve is activated. No task-to-cluster
> mapping is published.

**Therefore the remaining actionable deficiency is cluster replication depth and
balance, not additional source-scope or leaf-rule breadth.** Two of the three
achievable clusters are **singletons**, and a singleton cluster is one boundary
decision observed once. Breadth beyond the ceiling above is **structurally
impossible on this substrate** — it is not a matter of authoring effort, review
effort or task count.

---

## 3a. Inactive-reserve draft rows do not contradict the ceiling

The two inactive reserves, `PR01` and `PR02`, historically carried **draft**
architecture-opportunity rows in the private evaluator repository, and one of those
rows named the `infra → core` / `AR-DEP-004` relationship that §2 classifies **not
task-creatable**. A reader comparing the two could conclude that the ceiling is
wrong, or that a fourth decision cluster is available in reserve. **Neither is the
case, and the reason is not merely that the reserves are inactive.**

- **Reserve draft rows are historical, pre-reassessment material.** They were
  authored *before* the repaired scope-based oracle and *before* the independent
  pre-authoring opportunity reassessment. They were never adjudicated against the
  current task-created-decision standard, so their mere existence is evidence about
  what was once drafted, not about what the substrate can support.
- **They enter no active endpoint.** An inactive reserve contributes to **no**
  endpoint: its draft rows are analytically inactive, enter **no** active cluster
  register, count toward **no** E1 denominator, and are reported as a **zero**
  denominator rather than deleted. The adjudicated **active** counts in §3 are
  therefore unaffected by them in either direction.
- **Being inactive was never a licence to leave an invalid row standing.**
  Authorised private work has since **reconciled every one of those rows** under
  the current governance — the task-created-decision standard, scope attribution,
  this feasibility ceiling, the preservation-only rule and the production-source
  policy — and each now carries an explicit recorded disposition. Four rows were
  **demoted** to superseded, detection-only, non-scoring records; one survives as a
  task-created reserve candidate. **No reserve was activated**, the active set did
  not move, and the reserve denominator is **0**.
- **The legacy `infra → core` / `AR-DEP-004` reserve row is permanently barred, not
  merely dormant.** Because `infra` is **not task-creatable** on this substrate, that
  row is recorded as *detectable but not task-creatable* and **cannot enter an E1
  denominator on any future activation**. Stated once, exactly, so it cannot be
  paraphrased into its opposite: **the legacy `infra → core` / `AR-DEP-004` reserve
  row is not evidence of a fourth task-creatable decision cluster, and it is
  permanently barred from E1.** It is therefore **not** a task-creatable fourth
  cluster, and no coverage claim, power calculation or novelty assessment may treat
  it as one. Nothing mechanically valid is lost: a forbidden `infra → core` edge is
  still detected and attributed as a raw violation if it ever appears.
- **One reserve now carries no architecture opportunity at all.** After the
  reconciliation, one of the two reserves holds **no** dependency-direction row, so
  on any future activation it could be a **functional** candidate only — never an
  E1-scored one — unless a genuinely task-created decision is authored for it first
  and independently approved.
- **Machine-readable, not only narrative.** Each reserve row's disposition, its
  reserve denominator of `0`, its exclusion from the active cluster register and the
  permanent bar on the infeasible row are recorded as fields in the private
  migration register and per-task linkage records, so the distinction is checkable
  rather than a matter of reading prose. No private identifier and no
  rule id is published here, and **no task-to-cluster mapping is published**
  either - this section is suite-level only.
- **Now re-approved, and still not activated.** The reconciliation has been
  **independently re-approved** in an external read-only re-review whose recorded
  scope expressly includes it, so `TD-B40` residual (A) is discharged and `TD-B40`
  is **closed** (§8). **Re-approval is not activation and not a freeze:** both
  reserves stay `inactive-reserve`, the reserve denominator stays **0**, no
  manifest is frozen, gate `G1` is not passed, and activation still requires a
  **separately recorded, independently approved pre-run activation decision** that
  does not exist. `PR02` is additionally blocked by `TD-B26` for a reason unrelated
  to its rows — its terminal-state criterion is not externally reachable, and a
  defensible architecture row does not unblock an ungradeable functional contract.

---

## 4. The theoretical pair space, annotated

The dependency matrix admits **15** theoretical `(source scope, forbidden target)`
pairs under the implemented leaf clauses. **They are not 15 feasible benchmark
decisions.** Feasibility status is stated per pair so no later reader can mistake
mechanical detectability for experimental usability.

| Leaf rule | Source scope | Forbidden targets it can back | Feasibility on the canonical substrate |
|---|---|---|---|
| `AR-DEP-002` | `contracts` | `core`, `features`, `infra`, `observability`, `api` (5 pairs) | **NOT TASK-CREATABLE ON CURRENT SUBSTRATE** — mechanically detectable only (§2) |
| `AR-DEP-003` | `core` | `features`, `infra`, `observability`, `api` (4 pairs) | **NOT TASK-CREATABLE ON CURRENT SUBSTRATE** — mechanically detectable only (§2) |
| `AR-DEP-004` | `infra` | `core`, `features`, `api` (3 pairs) | **NOT TASK-CREATABLE ON CURRENT SUBSTRATE** — mechanically detectable only (§2) |
| `AR-DEP-005` | `api` | `core` (1 pair) | **TASK-CREATABLE / REPRESENTED** — `DC-API-CORE-AR-DEP-005` |
| `AR-DEP-006` | `features` | `infra`, `api` (2 pairs) | **TASK-CREATABLE / REPRESENTED** — `DC-FEATURES-INFRA-AR-DEP-006`, `DC-FEATURES-API-AR-DEP-006` |
| *(none)* | `observability` | — | **UMBRELLA-ONLY / NO SCORED LEAF** (§5) |

Source-scope summary: `contracts` **not task-creatable**; `core` **not
task-creatable**; `infra` **not task-creatable**; `api → core` **task-creatable /
represented**; `features → infra` **task-creatable / represented**;
`features → api` **task-creatable / represented**; `observability` source
**umbrella-only, no scored leaf**.

Nothing mechanically valid is deleted by this annotation: every pair above remains
a real forbidden relationship, and the oracle continues to detect and attribute it
if it ever appears in a patch. What the annotation removes is only the reading
that each pair is an available benchmark decision.

---

## 5. `observability` as a source scope (documentation gap closed)

`observability` **has no leaf rule**. `leafRuleFor('observability', target)`
returns `null` for every target
(`experiments/v2/oracle/src/checkers/dependencyDirection.ts`), and
`assertOpportunityRulesValid` refuses such an opportunity with
`OPPORTUNITY_RULE_SCOPE_MISMATCH`. Therefore an `observability`-sourced dependency
edge is:

- **umbrella-only under `AR-DEP-001`** — it can enter raw exposure through
  `applicable_rule_ids` and appear in the descriptive raw-violation series;
- **never eligible as a scored opportunity** — it can contribute to neither side
  of E1, regardless of how a task is written.

**No oracle behaviour changes here.** This is documentation of behaviour that is
already implemented and already regression-tested; it is recorded because the
public boundary-space inventories previously named `observability` as a forbidden
*target* without stating its status as a *source*.

---

## 6. Disposition of the earlier provisional coverage targets

Numeric breadth targets of the shape below were discussed **pre-freeze** while
`TD-B34` was being scoped. They were **provisional design targets**, never pinned
in a public artifact, never pre-registered as an acceptance bar and never used to
justify any authored task. They are recorded and adjudicated here rather than
silently dropped.

| Provisional pre-freeze target | Adjudication on the canonical substrate |
|---|---|
| ≥ 3 leaf rules | **NOT ACHIEVABLE** — hard ceiling **2** |
| ≥ 3 source scopes | **NOT ACHIEVABLE** — hard ceiling **2** |
| ≥ 3 forbidden targets | **ACHIEVED** — currently **3** |
| ≥ 4 independent decision clusters | **NOT ACHIEVABLE** — hard ceiling **3** |
| ≥ 2 observations per cluster | **REPLICATION-DEPTH OBJECTIVE — NOT CURRENTLY ACHIEVED UNIVERSALLY** (two of the three clusters are singletons); **potentially achievable** through carefully reviewed replication (`TD-B34`) |
| ≥ 8 E1-scored tasks | **not a scientifically meaningful standalone target** |

**Task count must not substitute for decision diversity or independence.** A task
total is not evidence of architectural coverage: several tasks over one boundary
are one instrument observed repeatedly (`TD-B30`, `TD-B37`). **The suite must not
be optimised toward a task count**, and in particular not toward eight.

---

## 7. Substrate expansion — declared alternative, not selected

**DECLARED ALTERNATIVE — NOT SELECTED BY THIS GOVERNANCE PACKAGE.**

A **substrate redesign or expansion is the only path** to increasing:

- **leaf-rule diversity beyond 2**;
- **source-scope diversity beyond 2**;
- **decision-cluster count beyond 3**.

That path is recorded, not rejected. What it would require, all of it before any
run could be counted against it:

- a **new canonical substrate identity** (`SOURCE_SUBSTRATE_IDENTITY.md` §8);
- a **renewed model-visible leakage review** (the `TD-B23`/`TD-B38` threat classes
  both re-open against new bytes);
- **re-validation of C1/C2/C3/C4 substrate equivalence** and condition parity;
- **re-validation of every existing task's feasibility** against the new
  substrate;
- a **public task linkage review** (each public body re-checked against the
  changed base);
- **private evaluator relink/migration** for every affected package;
- a **renewed architecture-opportunity review** of the whole active set.

This package performs **none** of it. Recording it as an explicit alternative
keeps the choice with the **Study Lead**: nothing here forecloses a later decision
to expand the substrate, and nothing here authorizes one.

---

## 8. Consequences carried elsewhere

- **`TD-B34` is re-scoped** from breadth expansion to **replication depth** over
  the three demonstrated clusters, and stays **open and blocking**
  ([`OPEN_DECISIONS.md`](OPEN_DECISIONS.md);
  [`TASK_AUTHORING_POLICY.md`](TASK_AUTHORING_POLICY.md) §12).
- **The breadth ceiling is a construct-validity limitation of the study**, not a
  defect to be engineered away, and is carried as such in
  [`RESEARCH_QUESTIONS.md`](RESEARCH_QUESTIONS.md) (CON-AC) and
  [`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md) §2.2: observed
  E1 effects generalise directly to the **represented** dependency-decision
  families, not automatically to all architecture rules or all layer pairs.
- **The analysis must treat the cluster count as fixed and small (G = 3)**
  ([`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md) §4b; `TD-B41`),
  and the power simulation stays blocked (`TD-B37`).
- **The inactive-reserve draft rows have been reconciled against this ceiling and
  cannot be read as extra coverage** (§3a; `TD-B40` residual (A)). Four legacy rows
  are demoted to superseded, non-scoring records, one survives as a task-created
  reserve candidate, and the legacy `infra → core` / `AR-DEP-004` row is
  **permanently barred** from any E1 denominator because that relationship is not
  task-creatable here. **No reserve was activated**, the active counts in §3 are
  unchanged, and the reserve denominator is **0**.
- **`TD-B40` is RESOLVED and CLOSED, and closure confers nothing.** Its two
  residuals — (A) inactive-reserve re-authoring/reconciliation and (B) independent
  re-approval of the complete migration — are **both complete**: (A) was performed
  under authorised private work and is independently re-adjudicated, and (B) was
  **independently re-approved** in an external **read-only** re-review of the
  complete migration (the active-set supersessions, the current active
  opportunities, the `PR01`/`PR02` reserve reconciliation, the active cluster
  register and the repaired cross-repository linkage), which closed both
  outstanding linkage findings, raised **no new P0 and no new P1**, and confirmed
  the migration state unchanged. The re-review event **precedes** the record of it;
  the repositories **propagate** that result rather than perform it, and no reviewer
  identity, URL, timestamp or external evidence identifier was supplied or is
  claimed. **Closing `TD-B40` freezes no manifest, passes no gate (`G1` included),
  makes no experiment run-ready, activates no reserve, and resolves neither
  `TD-B34` nor `TD-B39`.** Freeze and `G1` are governed by
  `TD-B05`/`TD-B14`/`TD-B32` and, for the legacy hidden-acceptance packages, by
  `TD-B39`; `TD-B40` never governed freeze, so a still-pending freeze is not a
  `TD-B40` residual. Every historical record it carried is preserved.
- **Forcing strength is recorded separately from task-createdness** (§2a; `P1-3`).
  `features → infra` is strictly forced in the retained instruments; `features →
  api` is natural-path / opportunity-creating. The asymmetry is a
  **construct-validity limitation**, changes no count in §3, and adds no cluster.
- **The Priority-A replication candidate is pinned before authoring, and is not
  authored** ([`CAND_A1_PREAUTHORING_DECISION.md`](CAND_A1_PREAUTHORING_DECISION.md)).
  `DC-FEATURES-API-AR-DEP-006` therefore stays at **one** active observation in §3
  until a body is authored, independently reviewed, privately packaged and admitted
  by eligibility governance.
