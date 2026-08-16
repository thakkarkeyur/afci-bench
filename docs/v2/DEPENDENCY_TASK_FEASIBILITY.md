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
clusters in the active set: `features → infra` and `features → api`.

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
> preservation-only rows `TD-B40` orders removed are excluded, and their physical
> removal from the private manifests is still outstanding. No task-to-cluster
> mapping is published.

**Therefore the remaining actionable deficiency is cluster replication depth and
balance, not additional source-scope or leaf-rule breadth.** Two of the three
achievable clusters are **singletons**, and a singleton cluster is one boundary
decision observed once. Breadth beyond the ceiling above is **structurally
impossible on this substrate** — it is not a matter of authoring effort, review
effort or task count.

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
| ≥ 2 observations per cluster | **potentially achievable** through carefully reviewed replication (`TD-B34`) |
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
