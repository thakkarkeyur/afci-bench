# docs/v2 — `PT08-PUB-P2-2` public accounting synchronization (CLOSED)

Status: **governance record for study v2**. The protocol remains **PRE-FREEZE**.

This record closes one finding and nothing else. It authors **no** task body,
changes **no** task body or hash, creates **no** private evaluator material, runs
**no** model, benchmark or power simulation, freezes **nothing**, passes **no**
gate, selects **no** model and **no** sample size, and produces **no** result.

---

## 1. The finding

**`PT08-PUB-P2-2` — stale public accounting after `PT08`'s admission.**

The external independent read-only review of the `PT08` public-authoring package
returned **APPROVE** with **P0 = 0**, **P1 = 0** and **P2 = 2**. `PT08-PUB-P2-2`
recorded that several public surfaces still described the **pre-admission** state
and would have to be reconciled to the admitted state **before `PT08`'s manifest
freeze** ([`PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md`](PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md)
§7.15, §11).

The stale assertions were, in substance. Each left-hand cell **describes** the
superseded claim rather than restating it, so this table cannot itself be quoted as
a live assertion of the pre-admission state:

| Superseded claim, described | Corrected to |
|---|---|
| active `E1` opportunity count given as **5** | **6** |
| cluster observation depths given as **3 / 1 / 1** | **3 / 2 / 1** |
| priority-A cluster depth given as **one** observation | **two** |
| singleton clusters counted as **two** | **one** |
| `PT08`'s private evaluator package described as absent | it is **authored** |
| `PT08`'s private manifest described as absent | one exists at `status=review` |
| `PT08`'s hidden evaluator manifest given as `not_yet_authored` | `stored_in_private_evaluator_repo` |
| `PT08`'s independent public-authoring review described as pending | it **passed** |
| `PT08` described as adding **zero** active observations | it adds **one** |
| the scored active set enumerated without `PT08` | it **includes** `PT08` |

---

## 2. `PT08-PUB-P2-2` is CLOSED

**Closure basis.** Every public surface that describes **current** accounting or
**current** `PT08` lifecycle state has been reconciled to the admitted state, and
every genuinely **historical** statement has been preserved under an explicit
historical framing (*as recorded then* / *superseded on this point only*) rather
than rewritten or deleted.

**Current active accounting, authoritative in
[`DEPENDENCY_TASK_FEASIBILITY.md`](DEPENDENCY_TASK_FEASIBILITY.md) §3:**

| Quantity | Value |
|---|---|
| Active `E1` opportunities | **6** |
| Active decision clusters | **3** |
| Cluster observation depths | **3 / 2 / 1** |
| Active scored tasks | `PT01`, `PT02`, `PT03`, `PT04`, `PT07`, `PT08` |
| Priority-A cluster observations | **2** |
| Remaining singleton clusters | **1** |

**`E1` is unchanged.** The numerator stays
`opportunity_accounting.violated_opportunity_count` and the
denominator/offset stays `opportunity_accounting.applicable_opportunity_count`.
`applicable_rule_count`, `rules_satisfied_count`, `satisfaction_proportion` and
`raw_violation_count` remain **inadmissible**. Synchronization changed the
**value** of the active register and **nothing** about the endpoint's definition,
the estimands, the cluster-robust strategy or the confirmatory hypotheses.

---

## 3. What closure does NOT imply

Stated first so it cannot be quoted without it. Closing `PT08-PUB-P2-2`:

- **freezes nothing** — every manifest, `PT08`'s included, stays `status=review`;
- **passes no gate**, `G1` included, and `G2`/`G6` stay blocking;
- **makes `PT08` no more run-eligible** — the public oracle still refuses a
  non-frozen manifest;
- **validates no hidden acceptance** — `PT08`'s hidden functional acceptance
  scaffold stays **`draft_unvalidated`** and has never been runtime-validated
  (`TD-B32`);
- **creates no result**, no violation value, no success value and no
  treatment-effect estimate;
- **runs no power simulation** and freezes no power value (`TD-B37`, `TD-B41`);
- **selects no model** (`primary_model` stays null, `TD-B03` open) and **no sample
  size**;
- **resolves no blocker** — `TD-B34` stays **OPEN and BLOCKING**;
- **starts no priority-B work**;
- **activates no reserve** and opens or closes no other blocker;
- **builds no runner** — none exists in this repository.

One **applicable opportunity** is an **instrument count**. It is never a
violation, a success, an outcome or a result.

---

## 4. `TD-B34` and priority B

- **Priority-A replication: complete and active.** The instrument is authored,
  its public authoring independently reviewed and approved, its private evaluator
  package authored and approved on a discharged conditional independent review,
  and its architecture opportunity admitted by a separately recorded governance
  step.
- **Priority-B candidate review: NOT STARTED.** `DC-API-CORE-AR-DEP-005` has had
  **no** candidate review at all and remains a **singleton**.
- **Priority B is therefore incomplete**, and **`TD-B34` stays OPEN and BLOCKING**
  for the normal staged path: Stage 0, normal Stage 1, final pilot progression,
  confirmatory execution and the power simulation where applicable.
- **Depth 2 is replication depth over one shared boundary decision.** The two
  observations in the priority-A cluster are **pseudo-replicates**; they are never
  two independent architecture constructs, and admission created **no new decision
  cluster**. The demonstrated ceiling of **3 decision clusters / 2 leaf rules /
  2 source scopes / 3 forbidden targets** is untouched.

---

## 5. `SL-PT08-01` is untouched

The bounded diagnostic exception recorded in
[`PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md`](PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md)
is neither widened nor withdrawn here.

- **Normal path:** `TD-B34` blocks Stage 0 and Stage 1.
- **Diagnostic exception:** `SL-PT08-01` permits **one** pre-registered,
  pre-Stage-0, `PT08`-only, `C1`-only, **non-confirmatory** difficulty diagnostic
  before `TD-B34` closure.
- **The diagnostic is not Stage 1**, is not Stage 0, is not part of the core grid,
  and **advances no stage**. Its observations are **analytically quarantined**:
  they never enter the confirmatory dataset, confirmatory `E1` effect estimation,
  treatment-effect analysis or power estimation, and are never pooled with Stage-1
  or core-grid observations.
- **The diagnostic remains mechanically NO-GO.** Closing `PT08-PUB-P2-2` discharges
  exactly one item on that record's §7 prerequisite list and **no other**.

---

## 6. Scope of the synchronization

**Changed:** public governance and registry surfaces carrying **current**
accounting or **current** `PT08` lifecycle state.

**Deliberately preserved as history:** the pre-authoring `CAND-A1` record's
adjudications and prohibitions; the pre-admission counts wherever a passage is
recording what was true at the time; the withdrawn `TD-B34` breadth objective and
every supersession note attached to it; the `TD-B40` reserve-reconciliation
statements, which `TD-B40` neither caused nor governs.

**Untouched:** `PT08.md` and every other public task body and hash; `apps/`;
`libs/`; the oracle; the canonical model-visible substrate
(`630d3180…` / `0198d76c…`); the public evaluator schemas; the architecture-context
payload; the architecture-rule catalog.

**No disclosure was widened.** No public task-facing artifact maps `PT08` to a
rule id, an opportunity identifier, a cluster, or an expected or prohibited area.
`PT08`'s opportunity identifier is **not** published anywhere in this repository:
the single bare identifier the public record is licensed to name is the one
`TD-B29` concerns, named there **as an identifier only**, and this record adds no
second one. The suite-level cluster inventory this record relies on was already
published, with its inference cost recorded, in
[`DEPENDENCY_TASK_FEASIBILITY.md`](DEPENDENCY_TASK_FEASIBILITY.md) §1.

---

## 7. Private repository

**No private byte was modified by this package**, and no private commit
accompanies it. The private repository was inspected **read-only**.

The changed public paths lie entirely **outside** the private linkage pin set —
they are public governance prose and public registry matrices, which that linkage
records as deliberately unpinned — so the private package's public-linkage
integrity is **unaffected** and **no re-link is required**. The reviewed public
evaluation baseline is **not** advanced by this record.
