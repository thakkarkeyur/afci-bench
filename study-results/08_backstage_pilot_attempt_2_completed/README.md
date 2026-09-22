# 08 — Backstage pilot, attempt 2: COMPLETE

`V2_BACKSTAGE_PILOT_ATTEMPT_2`, execution attempt 2. **All 18 scheduled
observations executed.** Governing records:
[`SL-V2-BACKSTAGE-PILOT-01`](../../docs/v2/AFCI_BACKSTAGE_PILOT_DECISION.md)
(science, endpoints and continuation rule, frozen before any data) and
[`SL-V2-BACKSTAGE-PILOT-03`](../../docs/v2/AFCI_BACKSTAGE_PILOT_ATTEMPT_2_DECISION.md)
(execution controls, frozen pre-data).

Attempt 1 remains **HALTED / EXCLUDED WHOLESALE**
([`07_backstage_pilot_attempt_1_halted/`](../07_backstage_pilot_attempt_1_halted/)).
Its rows are never pooled with, replaced by or re-run under this attempt.

## Decision

> **NO ARCHITECTURE SIGNAL — DO NOT AUTOMATICALLY EXPAND**

The frozen §11.1 rule requires **all three** criteria. Two hold, one fails.

| Clause | Statement | Observed | Verdict |
| --- | --- | --- | --- |
| §11.1.1 | C4 has **fewer** target-violation runs than C1 overall | C1 2/9, C4 1/9 | **PASS** |
| §11.1.2 | C4 has **fewer** target violations in **≥2 of 3** tasks | fewer in **1** of 3 (T5 only) | **FAIL** |
| §11.1.3 | C4 `FUNCTIONAL_VALID` no more than 1 below C1 | C1 4, C4 4 — difference 0 | **PASS** |

Criterion §11.1.2 fails on **ties at zero, not on C4 being worse.** T1 and T2
produced **zero** target violations in *both* arms, so neither task can show C4
as "fewer". Only T5 discriminated at all.

## Primary endpoint — architectural placement / ownership

Exactly 1 applicable opportunity per run, 18 across the set, as frozen.

| Scope | C1 target-violation runs | C4 target-violation runs |
| --- | ---: | ---: |
| **Overall** | **2 / 9** | **1 / 9** |
| T1 | 0 / 3 | 0 / 3 |
| T2 | 0 / 3 | 0 / 3 |
| T5 | 2 / 3 | 1 / 3 |

Applicable opportunities 9 per arm, 18 total; violated 2 (C1) + 1 (C4) = 3.

**Two of three tasks are at an architecture floor.** This is the same failure
mode the lower-model pilot hit, here partial rather than total: where nobody
violates, the instrument cannot separate the arms, and a rule that asks for
"fewer" cannot be satisfied by a tie.

## Functional endpoint

`FUNCTIONAL_VALID` iff every semantic case executes and passes (§7.2);
restraint cases are recorded separately and do not enter it.

| Scope | C1 valid | C4 valid | paired-valid blocks |
| --- | ---: | ---: | ---: |
| **Overall** | **4 / 9** | **4 / 9** | **3 / 9** |
| T1 | 0 / 3 | 0 / 3 | 0 / 3 |
| T2 | 2 / 3 | 3 / 3 | 2 / 3 |
| T5 | 2 / 3 | 1 / 3 | 1 / 3 |

### T1 is a task-instrument failure, not a model result

All six T1 runs — **both arms, all three repetitions** — passed exactly 3 of 4
semantic cases, failing **the same single case every time**. Both controlled
T1 references pass that case in the frozen reference matrix, so the oracle is
satisfiable; what no candidate reproduced is a behaviour the model-facing task
statement does not ask for. T1 therefore contributes 0 functionally valid runs
to either arm *and* 0 target violations to either arm: it is inert on both
endpoints.

**Nothing was changed in response.** The task bytes, the oracle, the scorer and
the rule are exactly as frozen. This is recorded as a finding for any future
amendment, and it is the single most important thing this attempt learned.

## MAX_TURNS

Ceiling 96, identical in both arms and every row.

| Scope | Overall | C1 | C4 |
| --- | ---: | ---: | ---: |
| All | 2 / 18 | 1 / 9 | 1 / 9 |
| T1 | 0 / 6 | 0 / 3 | 0 / 3 |
| T2 | 0 / 6 | 0 / 3 | 0 / 3 |
| T5 | 2 / 6 | 1 / 3 | 1 / 3 |

The 64→96 raise worked: attempt 1 hit its ceiling on 4 of 5 valid rows, attempt
2 on 2 of 18, one in each arm. The other 16 finished naturally at 49–89 turns.
`MAX_TURNS` is a scientific outcome and was never a retry reason.

## Secondary — efficiency (§11.2, cannot override §11.1)

Medians of C4/C1 over **functionally valid paired blocks only**. Coverage is
**3 of 9 blocks** (T2|R2, T2|R3, T5|R2) — T1 contributes none, because no T1
run is functionally valid.

| Endpoint | Median C4/C1 | Coverage | C4 lower |
| --- | ---: | ---: | ---: |
| `TOKEN_RATIO` (`TOTAL_INPUT_TOKENS`) | 0.9672 | 3/3 | 2/3 |
| `WALL_RATIO` | 1.0551 | 3/3 | 0/3 |
| `EXPLORATION_RATIO` | 0.8750 | 3/3 | 2/3 |
| `TOTAL_TOOL_RATIO` | 1.0159 | 3/3 | 0/3 |
| `COST_RATIO` | 0.9497 | 3/3 | 2/3 |
| `UNIQUE_FILES_READ` ratio | 0.9231 | 3/3 | 2/3 |
| `EDIT_WRITE` ratio | 0.9286 | 3/3 | 2/3 |

**Three pairs is not an efficiency result.** These medians are published for
completeness and are descriptive only; at n=3 a single block moves every one of
them. Efficiency is secondary by §11.2 and could not have rescued §11.1 in any
case.

## Cost

| | |
| --- | ---: |
| C1 total | $15.91 |
| C4 total | $16.28 |
| **Attempt-2 total** | **$32.19** |
| C1 median per run | $1.6969 |
| C4 median per run | $1.7275 |
| Paired median `COST_RATIO` | 0.9497 (3/3) |
| Coverage | 18/18 runs have provider cost |

Attempt 1's **$10.93** is retained separately and is **never** pooled with
attempt-2 treatment estimates.

## Execution integrity — all 18 rows

Read from each run's own record, not asserted: model `claude-sonnet-5`
requested **and** resolved 18/18; effort `high` validated 18/18 from two
independent channels (hook payload `effort.level` and `CLAUDE_EFFORT`) over
2,479 hook firings; runtime context `CLEAN` 18/18 with loaded context empty on
skills, slash commands, plugins and MCP servers; runtime 2.1.229 18/18;
`apiKeySource: none` 18/18; model-visible export tree
`4dfadc101db1c9f29b82934db25def67a93a2563` 18/18 with export proof passed;
dependency verification passed 18/18; tracked tree unchanged after pre-warm
18/18; `--max-turns 96` 18/18; candidate workspace preserved 18/18; **18 unique
sessions**, no resume or reuse; **0 scientific modifications**.

**0 infrastructure-invalid attempts. 0 retries. All 18 pre-authorised
`execution_attempt=2` identities remain unactivated.**

### The network preflight paid for itself

20 preflight refusals occurred (19 on sequence 10, 1 on sequence 11), every one
`VPN_ADAPTER_UP` — the same adapter state that severed two attempt-1
observations. Each refusal happened **before the task was delivered**: no
artifact directory, no workspace, no provider call, no observation consumed,
$0. The cost was wall-clock only. That is the control working exactly as
§3 of `SL-V2-BACKSTAGE-PILOT-03` intended.

## Per-run results

| Seq | Task | Cond | Rep | Functional valid | Semantic | Target violation | Turns | Completion |
| ---: | --- | --- | ---: | --- | ---: | --- | ---: | --- |
| 1 | T1 | C1 | 3 | no | 3/4 | no | 70/96 | natural |
| 2 | T1 | C4 | 3 | no | 3/4 | no | 57/96 | natural |
| 3 | T5 | C4 | 3 | no | 0/5 | **yes** | 77/96 | natural |
| 4 | T5 | C1 | 3 | no | 0/5 | no | 96/96 | MAX_TURNS |
| 5 | T5 | C1 | 2 | yes | 5/5 | **yes** | 87/96 | natural |
| 6 | T5 | C4 | 2 | yes | 5/5 | no | 89/96 | natural |
| 7 | T2 | C1 | 2 | yes | 4/4 | no | 62/96 | natural |
| 8 | T2 | C4 | 2 | yes | 4/4 | no | 64/96 | natural |
| 9 | T1 | C1 | 2 | no | 3/4 | no | 64/96 | natural |
| 10 | T1 | C4 | 2 | no | 3/4 | no | 63/96 | natural |
| 11 | T5 | C4 | 1 | no | 0/5 | no | 96/96 | MAX_TURNS |
| 12 | T5 | C1 | 1 | yes | 5/5 | **yes** | 49/96 | natural |
| 13 | T2 | C4 | 1 | yes | 4/4 | no | 61/96 | natural |
| 14 | T2 | C1 | 1 | no | 3/4 | no | 62/96 | natural |
| 15 | T1 | C1 | 1 | no | 3/4 | no | 52/96 | natural |
| 16 | T1 | C4 | 1 | no | 3/4 | no | 60/96 | natural |
| 17 | T2 | C4 | 3 | yes | 4/4 | no | 56/96 | natural |
| 18 | T2 | C1 | 3 | yes | 4/4 | no | 59/96 | natural |

Architecture placement is scored **independently** of functional validity, so
every row enters the primary endpoint whether or not it is efficiency-eligible.
Sequences 3, 5 and 12 demonstrate the independence directly: 5 and 12 are
functionally valid *and* target-violating; 3 is functionally invalid *and*
target-violating.

`eligible_for_analysis = true` marks the 6 rows in the 3 functionally valid
paired blocks — the rows that enter the **efficiency** analysis. All 18 enter
the architecture endpoint.

## Permission denials

63 across 18 runs (C1 26, C4 37), recorded descriptively. A denied command is
part of run behaviour; none authorised a retry, and the allowlist was not
widened during execution.

## What this does NOT license

Per §11.3: no p-values, no confidence intervals, no confirmatory causal claim.
Never pooled with `V2_EFF_ATTEMPT2` or `V2_LOWER_MODEL_PILOT` treatment
estimates — a descriptive side-by-side is permitted and must be labelled
descriptive. Enters no E1, treatment-effect or power analysis. Confers no
primary-model selection and no confirmatory eligibility.

## Files

| File | What it is |
| --- | --- |
| `attempt2_run_rows.csv` | all 18 rows, same schema as [`AFCI_MASTER_RUN_RESULTS.csv`](../AFCI_MASTER_RUN_RESULTS.csv), where they also appear |
| `attempt2_runs_raw_metrics.csv` | per-run captured metrics, counts only |
| `attempt2_architecture_summary.csv` | primary endpoint, overall and per task |
| `attempt2_functional_summary.csv` | functional endpoint and MAX_TURNS, overall and per task |
| `attempt2_endpoint_ratios.csv` | secondary efficiency medians and coverage |
| `attempt2_primary_pairs.csv` | the 3 functionally valid paired blocks used |
| `attempt2_decision_clauses.csv` | the three §11.1 clauses and the decision |
| `attempt2_frozen_analysis_report.json` | the full analysis, case ids stripped |

Aggregate change counts (files changed, lines added/removed) are published; the
changed-file **lists** are not, because they name the solution package. Hidden
oracle case identifiers, architecture rule and opportunity ids, expected
packages and evidence strings are private and appear nowhere here.
