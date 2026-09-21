# 07 — Backstage pilot, attempt 1: HALTED

`V2_BACKSTAGE_PILOT`, execution attempt 1. **Halted after 7 of 18 scheduled
observations.** Governing record:
[`SL-V2-BACKSTAGE-PILOT-02`](../../docs/v2/AFCI_BACKSTAGE_PILOT_ATTEMPT_1_HALT_DECISION.md).

## Nothing here is an analysis set

**No `C1`-vs-`C4` comparison, arm total, ratio, median or continuation
criterion was computed for this attempt, and none may be.** Four independent
reasons, each sufficient on its own:

1. the schedule is **11 rows short** of 18;
2. the arms are **unbalanced** — 3 valid `C1`, 2 valid `C4`;
3. **none** of the 9 paired blocks the frozen continuation rule depends on is
   complete in both arms *and* usable;
4. `SL-V2-BACKSTAGE-PILOT-01` §11.3 forbids a confirmatory claim from this
   pilot even when it **is** complete.

Every row carries `eligible_for_analysis = false`.

## What was attempted

| Seq | Task | Cond | Rep | Status | Turns | Completion |
| ---: | --- | --- | ---: | --- | --- | --- |
| 1 | T2 | C4 | 2 | INTACT_GOVERNED_OBSERVATION | 58/64 | COMPLETED_NATURALLY |
| 2 | T2 | C1 | 2 | INTACT_GOVERNED_OBSERVATION | 64/64 | MAX_TURNS_REACHED |
| 3 | T5 | C4 | 2 | INTACT_GOVERNED_OBSERVATION | 64/64 | MAX_TURNS_REACHED |
| 4 | T5 | C1 | 2 | INTACT_GOVERNED_OBSERVATION | 64/64 | MAX_TURNS_REACHED |
| 5 | T1 | C1 | 2 | INTACT_GOVERNED_OBSERVATION | 64/64 | MAX_TURNS_REACHED |
| 6 | T1 | C4 | 2 | **INFRASTRUCTURE_INVALID_NON_OBSERVATION** | 56/64 | PROCESS_FAILED |
| 7 | T5 | C4 | 3 | **INFRASTRUCTURE_INVALID_NON_OBSERVATION** | 54/64 | PROCESS_FAILED |

Rows 6 and 7 were severed mid-task by a local network failure
(`INFRA_API_TRANSPORT`, [`FAILURE_RERUN_POLICY.md`](../../docs/v2/FAILURE_RERUN_POLICY.md)
§2), **below** the turn ceiling. Their functional and architecture cells are
deliberately empty: a truncated candidate has no scorable outcome, and
publishing one would present a network event as model behaviour.

## Execution integrity, all seven rows

Read from each run's own record, not asserted: model `claude-sonnet-5`
requested **and** resolved 7/7; effort `high` validated 7/7 from two
independent channels; runtime context `CLEAN` 7/7; runtime 2.1.229 7/7;
model-visible substrate tree `4dfadc101db1c9f29b82934db25def67a93a2563` 7/7;
7 unique sessions, no resume or reuse; **0 scientific modifications**.

## Consumed

7 model runs, **$10.93** captured provider cost (\$8.17 across the five valid
observations, \$2.75 lost to the two infrastructure failures), ~5.3 hours of
model wall time.

## Two execution findings

Neither is a treatment result; both bear on any amendment.

* **The 64-turn budget was binding.** 4 of the 5 valid observations reached
  64/64; only one finished naturally. One of those four never ran the visible
  gate at all before exhausting its turns, and consequently left non-compiling
  code — its hidden functional result is "all semantic cases missing" because
  the candidate ran out of budget, not because the oracle failed.
* **28 tool calls were refused** across the seven rows under the frozen §8.1
  command allowlist, every one a compound shell construct it does not admit.
  Refused attempts consume turns.

Neither the ceiling nor the allowlist was changed during execution.

## Files

| File | What it is |
| --- | --- |
| `attempt1_attempted_rows.csv` | all 7 attempted rows, same schema as [`AFCI_MASTER_RUN_RESULTS.csv`](../AFCI_MASTER_RUN_RESULTS.csv), where they also appear |

Aggregate change counts (files changed, lines added/removed) are published; the
changed-file **lists** are not, because they name the solution package.
