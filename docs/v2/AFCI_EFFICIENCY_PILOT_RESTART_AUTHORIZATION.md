# SL-V2-EFF-RESTART-01 — a fresh 36-observation efficiency pilot execution

**Decision id:** `SL-V2-EFF-RESTART-01`
**Decided by:** Study Lead
**Status:** decided — **PRE-RESTART**
**Scope:** the `AFCI_EFFICIENCY_PILOT` run purpose only
**Depends on:** `SL-V2-EFF-ABORT-01` (the abort), `SL-V2-EFF-01` (the pilot),
`SL-V2-EFF-RESET-01` (the budget), `SL-V2-EFF-CHK-01` (the checkpoints),
`SL-V2-EFF-ELIG-01` (the eligibility narrowing), `SL-V2-EFF-FUNC-01` (functional
validity)

**Observations existing under this authority when it was written: 0.**

---

## 1. The decision

A **completely fresh 36-observation execution** of the frozen
`AFCI_EFFICIENCY_PILOT` schedule is authorised, as **execution attempt 2**,
following repair of the deterministic run-id / artifact collision recorded in
`SL-V2-EFF-ABORT-01`.

### 1.1 The authorisation table

| key | value |
| --- | --- |
| `decision_id` | `SL-V2-EFF-RESTART-01` |
| `run_purpose` | `AFCI_EFFICIENCY_PILOT` |
| `execution_attempt` | 2 |
| `supersedes_execution_attempt` | 1 |
| `abort_authority` | `SL-V2-EFF-ABORT-01` |
| `authorised_observations` | 36 |
| `begins_at_scientific_sequence` | 1 |
| `attempt_1_excluded_wholesale` | true |
| `attempt_1_observations_reused` | 0 |
| `attempt_1_comparative_analysis_used` | false |
| `attempt_1_comparative_analysis_exists` | false |
| `decided_before_any_attempt_2_observation` | true |
| `additional_repetitions` | false |
| `selective_rerun` | false |
| `replaces_unfavourable_outcomes` | false |
| `full_protocol_restart` | true |
| `scientific_design_changed` | false |
| `metrics_or_thresholds_changed` | false |
| `is_result` | false |
| `scored` | false |
| `enters_confirmatory_dataset` | false |

---

## 2. Why an authorisation exists at all

Because Attempt 1 was aborted for infrastructure corruption — not because
anything about the pilot's design, its instruments or its plausibility changed.

`SL-V2-EFF-ABORT-01` §5 records, and this decision relies on, the fact that **no
comparative analysis of Attempt 1 was ever computed**: no `TOKEN_RATIO`, no
C1-vs-C4 comparison, no pilot outcome, no continuation-threshold evaluation. So
nothing about what Attempt 1's seven intact rows *showed* could have informed
this authorisation, because nobody has established what they showed.

That ordering is the whole basis on which a restart is legitimate. A restart
decided after seeing a disappointing comparison is a different act wearing the
same words.

---

## 3. What "fresh" means, item by item

The replacement:

* **begins again at scientific sequence 1** and executes all 36 rows;
* uses **new worktrees** — every row prepares its own from the canonical
  substrate, and none is inherited;
* uses **new sessions** — every process mints a fresh session identity, no
  `--resume`, no `--continue`, no reuse across rows or across phases;
* uses **new run ids**, derived by the reset-aware, attempt-scoped algorithm;
* writes under the **Attempt-2 artifact namespace** (§5), which is provably
  disjoint from Attempt 1's;
* **reuses no Attempt-1 result, record, worktree, evidence stream or measurement.**

### 3.1 What this is NOT

It is **not** additional repetitions: the count stays at three per cell, and the
replacement's R1/R2/R3 are its own, not a continuation of Attempt 1's.

It is **not** selective rerunning: all 36 rows run, including the 7 that
completed intact in Attempt 1 and the 27 that never started.

It is **not** replacement of unfavourable outcomes: no outcome has been computed
to be favourable or otherwise (§2).

It **is** a full protocol restart.

---

## 4. Scientific invariance

Nothing about the experiment moves. The replacement is required to be
byte-identical or value-identical to the aborted execution on every one of:

| held invariant | value / authority |
| --- | --- |
| `PT01` task body | `6c938822fe19cd6e87942a6ee24ec8f604c0883da1b7f80d45216be35d7c9c39` |
| `PT04` task body | `f349b150b1d8fe5676fed8460b1840b988ee2bb0a78b1966ef82ae9ce9c8a9b5` |
| `PT07` task body | `557caed09420354efbc823c8b72e54b0760ac72847aba0d9c07d99e37ff7d2d7` |
| architecture payload (MAD) | `bf6f32b162a23b851596d8b489d938bef10d0b8616a50dcc039873d12ffa7a4d` |
| `C1` definition | `docs/v2/CONDITIONS.md`, delivery `none` |
| `C4` definition | `docs/v2/CONDITIONS.md`, delivery `prompt_injection` |
| checkpoint predicates | `SL-V2-EFF-CHK-01`, `docs/v2/RESET_CHECKPOINT_MATRIX.csv` |
| permission mode, tool set, Bash allowlist | `SL-V2-EFF-01` §5, re-derived per run |
| `NON_RESET` max turns | 64 |
| `RESET` phase A max turns | 32 |
| `RESET` phase B max turns | 32 |
| model | `claude-sonnet-5` |
| runtime | `2.1.229` |
| `FUNCTIONAL_VALID` | `SL-V2-EFF-FUNC-01` |
| `TOTAL_INPUT_TOKENS` | `SL-V2-EFF-01`, `efficiency_metrics` |
| secondary efficiency metrics | `SL-V2-EFF-01` |
| reset-overhead metrics | `SL-V2-EFF-01`, `SL-V2-EFF-RESET-01` |
| continuation thresholds | `SL-V2-EFF-01` |
| tasks / conditions / reset states / repetitions | `PT01,PT04,PT07` × `C1,C4` × `NON_RESET,RESET` × `R1,R2,R3` |
| paired scientific blocks | 18 |
| observations | 36 |

**No parameter is tuned on the basis of Attempt-1 behaviour.** In particular the
turn budgets are unchanged, although Attempt 1 produced nine real runs whose
consumption is on disk and could have been used to argue for different ones.
They are not used, because a budget informed by the aborted attempt's runs would
make the replacement's cost figures partly a function of the attempt it replaces.

---

## 5. The Attempt-2 artifact namespace, and the isolation requirement

### 5.1 Namespace

The replacement writes under a namespace segment `attempt-2`, beneath an
operator-chosen root. Attempt 2's run ids additionally carry the reset state and
the attempt, so **no Attempt-2 identity can equal an Attempt-1 identity** —
proved mechanically by `execution_attempt.overlap_problems` rather than by the
namespace alone.

**Attempt 1's directories are not deleted to obtain uniqueness.** Uniqueness is
obtained by deriving different identities, which is the repair; deleting the
evidence to make room would destroy the very artifacts `SL-V2-EFF-ABORT-01` §7
preserves.

### 5.2 The isolation requirement

Attempt 1 established an infrastructure fact, and it is frozen here as an
**operator-level requirement**:

> The artifact root and the sterile base for a counted `AFCI_EFFICIENCY_PILOT`
> run **must not descend from the active user profile**, and their ancestor
> chains must carry no host `.claude` material.

A root under the operator's profile puts that profile's real configuration on
the ancestor chain the pre-execution context audit walks, so the audit marks the
environment `CONTAMINATED` — **correctly**. The audit is not relaxed, weakened
or exempted in any way. The *root* moves instead.

The requirement is enforced in three places: `run_v2` refuses a counted run
whose roots fail it, `execution_attempt.preflight` refuses the whole execution,
and the pre-execution context audit continues to refuse per run exactly as it
did.

This is **infrastructure isolation, not a treatment change.** It alters where a
run's files live and nothing a run measures.

Recommended concrete roots on the current operator machine — recorded as an
example of the invariant, not as part of it:

```
artifact root : D:\afci-runs\attempt-2
sterile base  : D:\afci-sterile\attempt-2
```

---

## 6. The plan artifacts, and the two hashes

| artifact | hash |
| --- | --- |
| `ORIGINAL_SCIENTIFIC_PLAN_SHA256` (`docs/v2/AFCI_EFFICIENCY_PILOT_RUN_PLAN.json`) | `0038cd8b563ea804f4887d21cb37ceddb3a8f7632c4dd2315c260d3a9af95767` |
| `SCIENTIFIC_PROJECTION_SHA256` (the 36 ordered rows alone) | `417c32d51ae16f09c615db90fd2741155d67d233dddf149cca00bf25fd1386c5` |
| `REPLACEMENT_EXECUTION_PLAN_SHA256` (`docs/v2/AFCI_EFFICIENCY_PILOT_ATTEMPT_2_EXECUTION_PLAN.json`) | `562415031c04b0673c54ac352a4ca35a66e885023aa212cedc284da0c65a087e` |

The scientific schedule is **unchanged and keeps its hash**. It is not
re-randomised, no new seed is chosen, and the previously colliding rows are not
moved — sequences 6 and 9 stay exactly where the frozen order put them.

The replacement execution plan is a **separate artifact** whose physical hash
necessarily differs, because it carries the execution attempt, the run-id
algorithm version and the artifact namespace, none of which the original could
have carried. It **loads** the scientific schedule rather than rebuilding it, so
it cannot silently re-randomise anything.

`SCIENTIFIC_PROJECTION_SHA256` is the hash that makes the two comparable: it
covers the ordered `(sequence, task, condition, reset_state, repetition)` rows
and nothing else. `execution_attempt.projection_problems` proves row-for-row
equality directly, which is the stronger statement and is what the tests assert.

---

## 7. Pre-restart status

At the time this decision was written:

* Attempt-2 substantive observations: **0**
* Attempt-2 model invocations: **0**
* Attempt-2 artifact directories on disk: **0**
* Attempt-1 artifacts modified by this package: **0**

---

## 8. What this decision does not do

It passes no gate, closes no open decision, and admits no candidate. `TD-B32`,
`TD-B34`, `TD-B03`, `TD-B01`, `TD-B11`, `G1` and `G2` are exactly as they were.
The pilot remains **non-confirmatory**: not a result, not scored for confirmatory
`E1`, not treatment-effect eligible, not power eligible, and it estimates no
effect. `SL-V2-EFF-ELIG-01`'s narrowing is unchanged and is not widened by a
restart.

It also authorises no *further* attempt. A third execution, if one were ever
needed, needs its own decision and its own account of why the second failed.
