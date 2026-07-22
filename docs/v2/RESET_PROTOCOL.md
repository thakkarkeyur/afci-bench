# docs/v2 — Reset Protocol (Controlled Mid-Task Context Interruption)

Status: **development protocol for study v2**. Defines what a *reset* is and how
it is executed identically across conditions, so that RQ2 (reset robustness) is
measured, not confounded. Development artifact only: it does **not** freeze the
final benchmark configuration and authorizes **no** paid model run. **Task-
specific checkpoint values are deliberately NOT finalized here** — they are
open decision `TD-B01`, resolved during pilot task design (see §5 and
[`OPEN_DECISIONS.md`](OPEN_DECISIONS.md)).

Companion table: [`RESET_CHECKPOINT_MATRIX.csv`](RESET_CHECKPOINT_MATRIX.csv).
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
9. **Continue under the remaining fixed budget.** The second process runs with
   the budget **left over** after the pre-reset portion (total minus pre-reset
   consumption).
10. **Keep equal total budgets for reset and non-reset conditions.** For a given
    (task, condition, model), the **total** budget (tokens / turns / wall-clock,
    per [`OPEN_DECISIONS.md`](OPEN_DECISIONS.md) `TD-B11`) is **identical** whether
    or not a reset occurs. The reset merely **splits** that total into a pre-reset
    and a post-reset portion; it never grants extra budget.

---

## 3. Budget equality (why step 10 matters)

If reset runs received more total budget, any "robustness" difference could be a
budget artifact. Therefore:

- `total_budget(reset) == total_budget(non-reset)` for the same
  (task, condition, model).
- **The post-reset budget allowance is equal across conditions** for the same
  (task, model): the reset never grants one condition more room to recover than
  another.
- **Pre-reset consumption and post-reset allowance are logged separately.** The
  run manifest records, distinctly: `budget.pre_reset_consumed` (what process A
  actually used up to the checkpoint) and `budget.post_reset_allowance` (the
  equal-across-conditions room given to process B), alongside the pre/post split
  (`budget.pre_reset` / `budget.post_reset`) and `budget.total`.
- `pre_reset_budget + post_reset_budget == total_budget` for a reset run.

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
with `status = TODO` and no finalized value (`TD-B01`).

Related gates: checkpoint validity feeds **G2** (benchmark discrimination) and
**G1** (oracle validity). See [`PILOT_GATE_MATRIX.csv`](PILOT_GATE_MATRIX.csv).
