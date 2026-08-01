# docs/v2 — Reset Protocol (Controlled Mid-Task Context Interruption)

Status: **development protocol for study v2**. Defines what a *reset* is and how
it is executed identically across conditions, so that RQ2 (reset robustness) is
measured, not confounded. Development artifact only: it does **not** freeze the
final benchmark configuration and authorizes **no** paid model run. **Task-
specific checkpoint values are deliberately NOT finalized here** — they are
open decision `TD-B01`, resolved during pilot task design (see §5 and
[`OPEN_DECISIONS.md`](OPEN_DECISIONS.md)).

Companion table: [`RESET_CHECKPOINT_MATRIX.csv`](RESET_CHECKPOINT_MATRIX.csv)
(two template rows plus one **withheld** row per candidate — eight in total).
**Reset governance is in §6: reset is an experimental factor crossed with tasks,
not a task-content category requiring one special primary task.**
Session-freshness is enforced by the frozen session guard in
[`context_audit.py`](../../experiments/v2/harness/context_audit.py)
(`check_session_flags`, `LaunchCommand`). Per-condition reset context is defined
in [`CONDITIONS.md`](CONDITIONS.md); the construct is defined in
[`RESEARCH_QUESTIONS.md`](RESEARCH_QUESTIONS.md) (CON-RR).

---

## 1. Definition

A **reset** is a *controlled mid-task context interruption*: the first model
process is terminated at a predefined, task-specific checkpoint, and a **new,
context-free** model process is started to finish the same task, under the same
total budget. The interruption removes the model's accumulated **conversational
context** (nothing is restored — see steps 5–7) while preserving the **partially
modified repository** and approved state metadata. A **non-reset** run performs
the identical task end-to-end in a single process under the same total budget.

The reset is the *treatment* in RQ2; it must be applied identically across
C1–C4 so that any condition-specific attenuation is attributable to the context
mechanism, not to how the reset was performed.

---

## 2. The reset procedure (mandatory, in order)

1. **Start from a clean frozen repository SHA.** The task begins on a pinned base
   commit (`base_sha`), recorded in the run manifest.
2. **Begin the task in a fresh process.** A new model process starts the task
   under the condition's context (per [`CONDITIONS.md`](CONDITIONS.md)).
3. **Interrupt at a predefined, task-specific checkpoint.** The checkpoint is
   fixed *before* the run for each task (see §5; value = `TD-B01`), and is
   **externally detectable and condition-neutral** (it must not require a
   canonical layer, file path, or correct architecture — D7). It does not depend
   on what the model does at run time beyond the defined trigger.
4. **Preserve only the partially modified repository and approved state
   metadata.** The working tree as modified up to the checkpoint is kept; the
   approved state metadata (base SHA, condition, task, budget consumed so far,
   approved-context hashes) is kept. **Nothing else** — in particular, no model
   conversation, scratch context, or session transcript — is carried forward.
5. **Terminate the first model process.** The first process is stopped; its
   in-memory context is gone.
6. **Start a completely new model process.** A fresh process resumes the same
   task on the preserved working tree.
7. **Do not use `--continue`, `--resume`, `--from-pr`, or a reused session ID.**
   The new process must be genuinely fresh. Enforced fail-closed by
   `check_session_flags` / the launch-command guard in `context_audit.py`; a
   fresh, previously-unseen `--session-id` plus `--no-session-persistence` is the
   only permitted session handling.
8. **Apply condition-specific reset context.** The second process receives
   exactly the reset context defined for its condition
   ([`CONDITIONS.md`](CONDITIONS.md) → "reset context"):
   - **C1:** the functional task statement only.
   - **C2:** the task statement plus the same token-matched generic guidance.
   - **C3:** the persistent repository-instruction file (which is still in place
     by construction) plus the re-supplied task statement.
   - **C4 (AFCI):** the approved MAD **re-injected** as primary context, plus the
     task as secondary context.
9. **Continue under the frozen post-reset allowance.** The second process runs
   under the **frozen `post_reset_allowance`** — a fixed budget set in advance,
   **equal across all conditions** for the same (task, model). It is **not**
   computed from actual pre-reset consumption, and **unused `pre_reset_allowance`
   does not transfer** into the `post_reset_allowance`.
10. **Keep equal total budgets for reset and non-reset conditions.** For a given
    (task, condition, model), the **`total_budget`** (tokens / turns / wall-clock,
    per [`OPEN_DECISIONS.md`](OPEN_DECISIONS.md) `TD-B11`) is **identical** whether
    or not a reset occurs. A reset run's total is split *in advance* into a frozen
    `pre_reset_allowance` and a frozen `post_reset_allowance` with
    `pre_reset_allowance + post_reset_allowance == total_budget`; the reset never
    grants extra budget.

---

## 3. Budget equality (why step 10 matters)

If reset runs received more total budget, any "robustness" difference could be a
budget artifact. Therefore:

- `total_budget(reset) == total_budget(non-reset)` for the same
  (task, condition, model).
- **The `post_reset_allowance` is frozen and equal across conditions** for the
  same (task, model): the reset never grants one condition more room to recover
  than another.
- **Allowances are frozen; consumption is observational.** A reset run's total is
  split *in advance* into a **frozen `pre_reset_allowance`** and a **frozen
  `post_reset_allowance`**. The `post_reset_allowance` is **not** derived from
  actual pre-reset consumption, and **unused `pre_reset_allowance` does not
  transfer** into the `post_reset_allowance`.
- **The run manifest records five distinct budget fields:** `total_budget`, the
  frozen `pre_reset_allowance` and `post_reset_allowance`, and the observational
  `pre_reset_consumed` / `post_reset_consumed` (what each process actually used).
  The consumption fields are recorded for auditing only and never alter an
  allowance.
- `pre_reset_allowance + post_reset_allowance == total_budget` for a reset run.

The total budget value, and the split/allowance policy, are open decisions
(`TD-B11`, `TD-B01`); they are not set from v1 data.

---

## 4. What is and is not preserved

| Preserved across the reset | NOT preserved (removed by the reset) |
|---|---|
| Partially modified repository working tree (as of the checkpoint) | Model conversational context / scratch reasoning |
| Approved state metadata (base SHA, task, condition, budget-consumed, approved-context hashes) | Session transcript / any `--continue`/`--resume` handle |
| The condition's own context mechanism (e.g. C3's persistent file) | Any un-approved context that would fail the audit |

Every reset run still emits a `context_audit.json` for **both** the pre-reset and
post-reset process, and both must be **CLEAN**.

---

## 5. Checkpoints are NOT finalized (open decision `TD-B01`)

Task-specific checkpoint definitions and values are **deliberately unresolved**
and will be set during **pilot task design**, because a valid checkpoint depends
on the chosen task suite (which does not yet exist) and must be:

- **predefined** and **deterministic** (a fixed trigger, not model-behaviour-
  dependent beyond the trigger);
- **externally detectable** (observable by the harness without inspecting model
  reasoning);
- **condition-neutral and non-canonical** — the predicate **must not** require a
  canonical layer, a specific file path, or a correct architecture, because that
  would advantage the guided conditions (C3/C4) and confound the reset with the
  treatment ([`CRITICAL_DESIGN_DECISIONS.md`](CRITICAL_DESIGN_DECISIONS.md) D7);
- placed so that meaningful work remains after the reset (otherwise the reset is
  vacuous);
- **identical** for all conditions of the same task.

**Preferred checkpoint:** task-specific **functional / worktree progress** — an
observable, condition-neutral state (e.g. a required behaviour becomes reachable,
or a defined worktree change exists) that any condition could reach by any
architectural route.

**Fallback checkpoint:** the **first visible validation attempt after at least
one edit** (e.g. the first `npm run ci:agent` invocation after an edit) — also
condition-neutral.

Prohibited predicates: "the file was created in the core layer", "the port was
placed in contracts", or any trigger that presupposes the correct architecture.

Every task **intended for reset analysis must have a frozen checkpoint**. Each
candidate task row in
[`RESET_CHECKPOINT_MATRIX.csv`](RESET_CHECKPOINT_MATRIX.csv) carries these fields
with `status = TODO` and no finalized value (`TD-B01`). All eight candidates
(`PT01`–`PT06`, `PR01`, `PR02`) now have a per-task row whose predicate contents
are **withheld** (`withheld_pending_TD-B01`) so the matrix is complete without
publishing a private checkpoint predicate.

---

## 6. Reset governance: reset is a FACTOR, not a task category

This section exists to prevent a specific bookkeeping error: keeping a task in the
confirmatory analysis because it is the task that "covers reset".

- **Reset is an experimental factor crossed with tasks.** It is a fixed effect in
  the design — every task in the analysed set is run in **both** reset and
  non-reset states, and the RQ2 estimate is the **condition × reset interaction**
  ([`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md) §4).
- **Reset is NOT a task-content category** and does not require one special
  primary task. There is no "reset task", no "reset-continuation coverage" slot to
  fill, and no candidate uniquely supplies reset evidence. A task's subject matter
  (read endpoint, list endpoint, write endpoint, logging, calculation, error
  handling) is orthogonal to whether a reset is applied to it.
- **Multiple retained primary tasks already have condition-neutral checkpoints.**
  Both approved predicate shapes — task-specific functional/worktree progress
  (preferred) and the first visible validation attempt after at least one edit
  (fallback) — are available to every retained primary candidate, because neither
  presupposes a canonical layer, file path, or correct architecture (D7). Reset
  coverage therefore does not depend on any single task being retained.
- **`PT06` must not remain in E1 merely to satisfy a bookkeeping reset label.**
  `PT06` is classified `functional-only`
  ([`PILOT_PUBLIC_TASK_MATRIX.csv`](PILOT_PUBLIC_TASK_MATRIX.csv)): it is a valid
  primary functional candidate, structurally excluded from E1, and it still
  contributes to hidden functional acceptance (E3), cost measures, and
  pre-registered exploratory analyses — **including reset-state comparisons on
  those outcomes**. Retaining it in E1 to preserve a reset label would put a
  zero-exposure task into a rate model, which
  [`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md) §2.1 forbids.
- **No public artifact claims that any one candidate provides reset-continuation
  coverage.** Per-candidate coverage mapping is withheld as a private design
  detail; where reset is discussed publicly it is described as a factor, never as
  a task-content category.

Related gates: checkpoint validity feeds **G2** (benchmark discrimination) and
**G1** (oracle validity). See [`PILOT_GATE_MATRIX.csv`](PILOT_GATE_MATRIX.csv).
