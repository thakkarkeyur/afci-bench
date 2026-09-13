# docs/v2 — `SL-PT08-06`: the diagnostic-scoped freeze exception for the `PT08` `C1` difficulty diagnostic

Status: **Study-Lead governance adjudication for study v2.** This record is
governance only. It authors **no** task body, changes **no** task body or hash,
edits **no** pinned public schema, changes **no** evaluator, opportunity or task
semantics, selects **no** confirmatory model, validates **no** hidden acceptance,
passes **no** gate, produces **no** result and **no** power value, and advances
**no** private linkage baseline.

**The suite-wide protocol remains PRE-FREEZE.** Nothing here freezes the
benchmark, the task suite, or any other task.

Decision identifier: **`SL-PT08-06`**, in the repository's existing Study-Lead
convention `SL-<subject>-<nn>`. `SL-PT08-05` is **occupied** by
[`PT08_DIAGNOSTIC_MODEL_RUNTIME_SELECTION.md`](PT08_DIAGNOSTIC_MODEL_RUNTIME_SELECTION.md),
so the next free identifier is used.

Related: [`PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md`](PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md)
§2, §5, §6, §7 item 14, §8, §9;
[`PT08_DIAGNOSTIC_EXECUTION_DECISIONS.md`](PT08_DIAGNOSTIC_EXECUTION_DECISIONS.md)
§2, §3, §4 item 4;
[`PT08_DIAGNOSTIC_ISOLATION_CLARIFICATION.md`](PT08_DIAGNOSTIC_ISOLATION_CLARIFICATION.md);
[`PT08_DIAGNOSTIC_MODEL_RUNTIME_SELECTION.md`](PT08_DIAGNOSTIC_MODEL_RUNTIME_SELECTION.md)
§7; [`PT08_PUBLIC_ACCOUNTING_SYNCHRONIZATION.md`](PT08_PUBLIC_ACCOUNTING_SYNCHRONIZATION.md);
[`TASK_ACCEPTANCE_MATRIX.csv`](TASK_ACCEPTANCE_MATRIX.csv);
[`PILOT_GATE_MATRIX.csv`](PILOT_GATE_MATRIX.csv) `G1`;
[`OPEN_DECISIONS.csv`](OPEN_DECISIONS.csv) `TD-B05`, `TD-B12`, `TD-B14`,
`TD-B32`, `TD-B34`.

---

## 1. The circularity this record resolves

`SL-PT08-01` authorised **one** pre-Stage-0, `PT08`-only, `C1`-only,
**non-confirmatory** difficulty diagnostic **before** `TD-B34` closure and
**before** priority B, precisely so that one instrument's baseline difficulty
could be checked before further benchmark investment was committed to.

Four prerequisites of that authorisation remained. Three have since been
discharged — the sterile isolated execution context and identity
(`SL-PT08-04`), and the live `Q1`/`Q8` runtime controls with the exact model and
runtime pin (`SL-PT08-05`). **One remains: §7 item 14, `PT08`'s manifest
freeze.**

That last item is where the loop closes:

1. `SL-PT08-01` authorised this diagnostic **before** `TD-B34` and **before**
   priority B, and §8 records that neither is a prerequisite for it.
2. The **generic** freeze rule the repository already carries makes a manifest
   freeze conditional on the **suite-wide** gate `G1`
   ([`PILOT_GATE_MATRIX.csv`](PILOT_GATE_MATRIX.csv)).
3. Gate `G1` in turn depends on work that `SL-PT08-01` §8 **expressly does not
   require for this diagnostic** — the re-scoped `TD-B34` replication-depth
   objective, priority-B candidate authoring, and the suite-wide `TD-B32` and
   `TD-B12`/`G6` conjuncts across every other package.
4. So, under the generic rule alone, the earlier authorisation is
   **mechanically non-executable**: a diagnostic explicitly permitted before
   that work could never run until that work was complete.

**The loop is a governance artefact, not a scientific finding.** Resolving it is
a Study-Lead adjudication, and this record carries it.

### 1.1 Why this decision is PRE-DATA

Stated plainly, because it is the only thing that makes the decision
defensible:

- **Zero `PT08` diagnostic observations exist at decision time.** No repetition
  has been executed, here or anywhere in this repository.
- `experiments/v2/results/` and `experiments/v2/analysis/` carry a `README.md`
  each and nothing else. There is no `R1`, no `R2`, no `R3`.
- **No functional-success count exists.** No architecture-violation result
  exists. No treatment-effect result exists. No power value exists.
- Therefore this decision **cannot be outcome-driven**: there is no outcome to
  drive it. It resolves a pre-data governance circularity and nothing else.

A test asserts the zero-data precondition mechanically, so this paragraph is a
checked fact rather than a claim.

---

## 2. `SL-PT08-06` — the decision

> **`SL-PT08-06`.** For `run_purpose` = **`PT08_DIFFICULTY_DIAGNOSTIC`**, task
> **`PT08`**, condition **`C1`**, and for that triple **only**, `PT08` may enter
> a **`DIAGNOSTIC-SCOPED FROZEN`** state and may be executed once every
> `PT08`-specific prerequisite authorised by `SL-PT08-01` through `SL-PT08-05`
> is satisfied — **WITHOUT** declaring the suite-wide gate `G1` passed.
>
> This is a **narrow exception to the APPLICABILITY** of the suite-wide `G1`
> freeze prerequisite, for this one diagnostic vehicle. It is **not** a pass of
> that gate, **not** a waiver of it, and **not** a reduction of its scope.
>
> Every other run purpose, every other task, and every other condition continues
> to use the existing gates, unchanged. The runner **fails closed** on anything
> outside the triple.

### 2.1 The applicability table

Machine-readable. The runner re-derives these values from this table, so a drift
between the adjudication and the code is a mechanical failure rather than a
reading.

| Field | Required value |
|---|---|
| `decision_id` | `SL-PT08-06` |
| `run_purpose` | `PT08_DIFFICULTY_DIAGNOSTIC` |
| `diagnostic_freeze_task` | `PT08` |
| `diagnostic_freeze_condition` | `C1` |
| `diagnostic_freeze_frozen` | `true` |
| `diagnostic_freeze_authority` | `SL-PT08-06` |
| `diagnostic_freeze_task_sha256` | `a31bb515b79cc1e211a662de2a8761c97082dd8bf266ee5b4f660981435badf2` |
| `diagnostic_freeze_exact_model_id` | `claude-sonnet-5` |
| `diagnostic_freeze_model_selector_is_alias` | `false` |
| `diagnostic_freeze_cli_version` | `2.1.229` |
| `diagnostic_freeze_repetitions` | `3` |
| `diagnostic_freeze_permission_mode` | `acceptEdits` |
| `diagnostic_freeze_authentication` | `claude-code-subscription-oauth` |
| `diagnostic_freeze_api_key_used` | `false` |
| `diagnostic_freeze_fallback_model_permitted` | `false` |
| `diagnostic_freeze_process_per_repetition` | `fresh` |
| `diagnostic_freeze_session_per_repetition` | `fresh` |
| `diagnostic_freeze_resume_permitted` | `false` |
| `diagnostic_freeze_continuation_permitted` | `false` |
| `diagnostic_freeze_session_reuse_permitted` | `false` |
| `diagnostic_freeze_sterile_context_required` | `true` |
| `diagnostic_freeze_context_audit_required_every_repetition` | `true` |
| `diagnostic_freeze_architecture_delivery` | `none` |
| `diagnostic_freeze_is_result` | `false` |
| `diagnostic_freeze_scored` | `false` |
| `global_g1` | `false` |
| `global_g1_passed_by_this_record` | `false` |
| `suite_frozen` | `false` |
| `global_manifest_frozen` | `false` |
| `public_lifecycle_status_unchanged` | `validated` |
| `global_td_b32_status` | `open` |
| `td_b12_g6_status` | `open` |
| `td_b34_status` | `open` |
| `priority_b_state` | `not started` |
| `td_b03_status` | `open` |
| `private_linkage_baseline_advance_required` | `false` |

### 2.2 The rationale, stated as the rationale

1. **`SL-PT08-01` already authorised this `PT08`-only `C1` diagnostic before
   `TD-B34` closure and before priority B.** §2 grants it; §5 records `TD-B34`
   as the one bounded exception; §8 lists priority-B authoring, `TD-B34`
   closure, `C3`, `C4`, treatment-effect analysis and the power simulation as
   **not** prerequisites.
2. **The existing generic freeze rule still depended on suite-wide `G1`.**
   `SL-PT08-01` §7 item 14 names it, and `SL-PT08-02`/`SL-PT08-03`/`SL-PT08-05`
   each restate that they freeze nothing and pass no gate.
3. **Suite-wide `G1` itself depends on work explicitly not required for this
   diagnostic.** `G1` is a suite gate over `TD-B04`, `TD-B05` and `TD-B12`, and
   `PILOT_GATE_MATRIX.csv` records it as blocking on the re-scoped `TD-B34`
   objective and on packages other than this one.
4. **Without this narrow exception the earlier authorisation is mechanically
   non-executable.** Readiness reports `manifest_freeze` as the sole remaining
   blocker, and no existing `SL-PT08` decision opens a diagnostic-scoped route
   around it — `SL-PT08-05` §7 states exactly that and declines to narrow it.
5. **Zero `PT08` diagnostic observations exist at decision time** (§1.1).
6. **Therefore the decision resolves a pre-data governance circularity rather
   than reacting to results.**

---

## 3. What `SL-PT08-06` does NOT do

Stated as an enumerated bound so no later reader can extract a licence this
record does not grant. `SL-PT08-06` does **not**:

- pass the suite-wide gate **`G1`**;
- close the suite-wide gate **`G1`**;
- close **`TD-B34`**;
- start or complete **priority B**;
- close the **global `TD-B32`** row;
- close **`TD-B12`** or pass **`G6`**;
- authorise **`C2`**, **`C3`** or **`C4`**;
- authorise **confirmatory execution**;
- authorise **treatment-effect analysis**;
- authorise **power estimation** or any power calculation;
- make the **benchmark** or the **task suite** frozen;
- freeze, or change the lifecycle of, **any other task**;
- waive **hidden-evaluator validation**;
- waive **public/private linkage**;
- waive **clean isolation** or the per-repetition context audit;
- waive **`Q1`** or **`Q8`**;
- waive **exact model pinning**, or permit the alias in place of the exact id;
- waive the **fresh-process / fresh-session** requirements, or permit
  `--resume`, `--continue` or session reuse;
- select a **primary benchmark model** — **`TD-B03` stays open** and
  `MODEL_REGISTRY.yml` still records `primary_model: null`;
- change any **task**, **evaluator**, **opportunity** or **hidden-acceptance**
  semantics;
- advance a **private linkage baseline**, or require a re-link;
- change any **active accounting** value — this record states no active
  opportunity count, no decision-cluster count and no observation depth, and
  changes none;
- create **precedent** for a second exception. A further scoped freeze would
  need its own Study-Lead adjudication.

**The `PT08` evaluator manifest is not globally frozen by this record.** The
public lifecycle row stays `status=validated`, which records hidden-acceptance
validation only and is not a freeze; the private evaluator manifest stays
`status=review`. What this record creates is a **separate, narrower state** that
sits beside the global one and never replaces it.

---

## 4. The two states, kept apart

The repository's existing lifecycle carries a single global reading of "frozen".
This record does **not** overload it. Two distinct states now exist and are
reported separately:

| State | Value | Meaning |
|---|---|---|
| `global_manifest_frozen` | `false` | the suite-wide lifecycle freeze, gated on `G1`. **Unchanged, and still not granted.** |
| `diagnostic_scoped_frozen` | `true` | the execution configuration pinned by this record, valid **only** for `PT08` / `C1` / `PT08_DIFFICULTY_DIAGNOSTIC`. |

A reader, a report or a later package that wants the suite-wide answer must read
`global_manifest_frozen`, which is **`false`**. A consumer that silently upgraded
the scoped state into the global one would be reading the wrong field, and the
runner refuses to write the global one at all.

**Fail closed.** Anything the scoped state does not cover — another task,
another condition, another run purpose, a different exact model, a different
runtime version, a missing clean context, a `Q1` or `Q8` that is not `PASS`, a
resume, a continuation, a reused session, an absent scoped freeze, or a freeze
claiming a different authority — is **refused**, never defaulted.

---

## 5. The frozen execution configuration

Frozen for this diagnostic, and for nothing else. After the commit that records
it, these bytes are not modified.

| Field | Frozen value |
|---|---|
| `frozen_task_id` | `PT08` |
| `frozen_task_sha256` | `a31bb515b79cc1e211a662de2a8761c97082dd8bf266ee5b4f660981435badf2` |
| `frozen_condition` | `C1` |
| `frozen_run_purpose` | `PT08_DIFFICULTY_DIAGNOSTIC` |
| `frozen_repetitions` | `3` |
| `frozen_exact_model_id` | `claude-sonnet-5` |
| `frozen_cli_version` | `2.1.229` |
| `frozen_authentication` | `claude-code-subscription-oauth` |
| `frozen_api_key` | `none` |
| `frozen_permission_mode` | `acceptEdits` |
| `frozen_substrate_commit` | `630d3180af0d02a86330dfb599f559e78df65e94` |
| `frozen_substrate_content_hash` | `0198d76c189f38589e872cab4305527c08e86ef736e1550e428e05f9178060f3` |
| `frozen_substrate_entry_count` | `49` |
| `frozen_hidden_evaluator` | `the current validated PT08 hidden-acceptance package` |
| `frozen_architecture_scorer` | `the current governed out-of-band architecture oracle` |
| `frozen_opportunity_set` | `the current active PT08 opportunity set, unchanged` |

The permission mode, the tool set, the authentication mode and the runtime
version are the ones `SL-PT08-05` **live-validated**, not a fresh choice made
here. The substrate identity is the governed one, unchanged.

### 5.1 The diagnostic-scoped frozen manifest mount

The out-of-band architecture oracle scores only a manifest whose `status` is
exactly `frozen`. The private evaluator manifest **stays `status=review`** and is
never modified.

So the scorer is handed a **derived, diagnostic-scoped mount**, built at scoring
time into a disposable directory outside both repositories, exactly as the
already-approved private validation corpus does for its own labelled cases:

- it is derived from the **shipped** manifest, so it cannot drift from the
  package it scores;
- it differs from the shipped manifest in **exactly two lifecycle fields** —
  `status` and `manifest_version` — and in nothing else. A test asserts the
  difference set mechanically;
- **every semantic field is byte-identical**: the task binding, the opportunity
  set, the dependency policy, the layer map, the evaluator hashes and the
  eligibility classification;
- it is **never committed**, never written into either repository, and never
  written inside the coding worktree.

Deriving a scoped mount changes no evaluator semantics. It is the lifecycle
field, and only the lifecycle field, that this record's authority moves.

---

## 6. What is still required, per repetition

`SL-PT08-06` removes exactly one applicability. Everything else stands, and each
of these is demonstrated per repetition rather than asserted in advance:

1. a **fresh disposable governed worktree**, prepared from the allowlist, with
   `architecture_delivery=none`;
2. a **fresh sterile `HOME` and configuration directory**;
3. **subscription authentication only**, with **no** `ANTHROPIC_API_KEY`;
4. a **context audit verdict of `CLEAN`**, before every repetition;
5. a **fresh process** and a **fresh session id**; no `--resume`, no
   `--continue`, no session reuse;
6. the **exact approved task hash**, verified;
7. the **governed substrate identity**, verified;
8. an **exact model readback** of `claude-sonnet-5`; anything else makes the
   repetition **invalid**;
9. the **same frozen permission and tool configuration** for all three;
10. the **canonical repository unchanged**, verified before and after;
11. the **diagnostic artifact firewall** enforced — `is_result: false`,
    `scored: false`, all five `SL-PT08-01` §9 eligibility flags `false`, and no
    artifact written anywhere inside the canonical repository.

**The failure/rerun policy is unchanged.** A substantive failed attempt is an
observation and is **never** re-run. Only an infrastructure-invalid
non-observation may follow the existing rerun policy, and there are never more
than **three** valid observations.

---

## 7. What the three observations may and may not inform

Unchanged from `SL-PT08-01` §10 and `SL-PT08-03` §3.3–§3.4, restated so this
record cannot be read as widening them.

**Permitted:** functional completion; hidden-acceptance pass/fail; applicable
opportunity count; violated opportunity count; the `C1` violation proportion;
floor/ceiling behaviour; qualitative failure modes; and whether `PT08` should be
retained, revised or retired.

**Prohibited, in any form:** comparison against `C4`; any AFCI effect; any
condition contrast; any treatment-effect estimate; any interaction estimate; any
confidence interval; any power or precision claim; and any pooling with later
Stage-1 or core-grid observations.

**The three repetitions are repeated probes of one instrument under one
condition.** They are not three independent architecture clusters, and the
existing pseudo-replication governance is unchanged in every respect.

---

## 8. Prohibitions attaching to this record

- **Gate `G1` is NOT passed**, and no gate is passed.
- **The suite is NOT frozen** and the protocol remains **PRE-FREEZE**.
- **The global manifest freeze is NOT granted**; the public lifecycle row is
  unchanged at `status=validated` and the private manifest stays `status=review`.
- **`TD-B34` is NOT closed** and is not weakened. *As recorded then* **priority B was NOT started**; the later `SL-QUAL-01` package authored `PT10`, so **priority b is started and is not complete**, and **this freeze neither started nor completed it**.
- **The global `TD-B32` row stays OPEN**; **`TD-B12`/`G6` are unchanged**.
- **`TD-B03` stays OPEN** and `primary_model` stays `null`.
- **No confirmatory run is authorised**, and no result-bearing purpose exists.
- **No result, violation value, success value, outcome value, treatment-effect
  estimate or power value exists** at the time this record is written.
- **No private-linkage baseline is advanced** and **no re-link is performed**.
- **No accounting synchronization is performed here.**
