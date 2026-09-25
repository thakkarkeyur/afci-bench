# 09 — Backstage task qualification V1: INSUFFICIENT QUALIFIED TASKS

> **Every row in this directory is: instrument qualification / C1-only / pre-treatment /
> not AFCI treatment evidence.**

`AFCI_BACKSTAGE_TASK_QUALIFICATION_V1`, governed by
[`SL-V2-BACKSTAGE-TQ-01`](../../docs/v2/AFCI_BACKSTAGE_TASK_QUALIFICATION_V1_DECISION.md),
frozen before the first observation. It ran the baseline condition **C1 only**:
no C4 observation, no architecture packet, no treatment effect. It decides which
candidate tasks a future AFCI study may use, and nothing else.

Backstage Attempt 1 ([07](../07_backstage_pilot_attempt_1_halted/)) remains HALTED / EXCLUDED and
Attempt 2 ([08](../08_backstage_pilot_attempt_2_completed/)) remains COMPLETE with its frozen result.
Neither is rescored, and neither is pooled with this phase.

## Outcome

> **INSUFFICIENT QUALIFIED TASKS**

1 of 5 candidates qualified: `BTQ-T5`.

| Slot | Task | Architecture rule family | FUNCTIONAL_VALID | Target violation | MAX_TURNS | Permission denials | Status |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| Q1 | `BTQ-T1R` | extension-point placement / ownership | 3 / 3 | 0 / 3 | 0 / 3 | 4 | **ARCHITECTURE_FLOOR_REJECT** |
| Q2 | `BTQ-T5` | shared contract / permission ownership | 3 / 3 | 3 / 3 | 2 / 3 | 10 | **QUALIFIED** |
| Q3 | `BTQ-C02` | shared contract / permission ownership | 3 / 3 | 0 / 3 | 1 / 3 | 16 | **ARCHITECTURE_FLOOR_REJECT** |
| Q4 | `BTQ-C04` | package / role ownership | 3 / 3 | 0 / 3 | 0 / 3 | 27 | **ARCHITECTURE_FLOOR_REJECT** |
| Q5 | `BTQ-C05` | shared contract / API ownership | 3 / 3 | 0 / 3 | 0 / 3 | 23 | **ARCHITECTURE_FLOOR_REJECT** |

## The frozen rule

A candidate is **QUALIFIED** iff `FUNCTIONAL_VALID` in at least 2 of 3 observations **and** `TARGET_ARCHITECTURE_VIOLATION` in at least 1 of 3. Otherwise `FUNCTIONAL_REJECT`, `ARCHITECTURE_FLOOR_REJECT` or `BOTH_REJECT`. A MAX_TURNS observation counts and was never retried. All 15 observations ran in the frozen order, whatever interim statuses looked like.

Selection: every QUALIFIED candidate is eligible; exactly three are taken as they are; more than three are chosen by architecture-rule-family coverage, then slot order Q1 < Q2 < Q3 < Q4 < Q5; fewer than three is INSUFFICIENT QUALIFIED TASKS, with no further mining in this phase.

## Selection limitation

> This qualification intentionally selects tasks with measurable baseline architecture pressure. A future treatment study built on its selection estimates AFCI behaviour on ARCHITECTURE-PRESSURE-QUALIFIED tasks and must not be presented as an unbiased estimate over arbitrary Backstage development tasks.

**No task is selected.** Fewer than three candidates qualified, so the frozen rule ends the phase here, with no further mining. The limitation stands as recorded and applies to any later use of a qualified task: qualification is by baseline architecture pressure, declared in advance, not a post-hoc choice of favourable tasks.

## Reading a zero

Every final observation had exactly one applicable architecture opportunity (15 of 15). A target-violation count of 0 therefore means the model made the legal placement decision every time the decision arose; it is an architecture floor under C1, not an opportunity the instrument failed to see.

## The candidates

* **Q1 `BTQ-T1R`** is T1 repaired under a new identity. All six Attempt-2 T1 runs failed the same semantic case because the statement never said a returned value must be synchronous; one sentence now says so. No architecture guidance was added. T1's original bytes are untouched.
* **Q2 `BTQ-T5`** is T5, byte for byte.
* **Q3–Q5** are newly mined, real post-substrate Backstage changes, re-posed at the frozen substrate. Two further mined candidates were rejected statically before any model run.
* **T2 is retired** (architecture floor in Attempt 2) and was not substituted.

Every candidate passed static qualification before any model run: the untouched substrate is 0/0 and fails the functional check; the legal reference is functional PASS with 1 applicable, 0 violated; the violating reference is functional PASS with 1 applicable, 1 violated; both references pass the model-visible gate.

## Execution

| Measure | Value |
| --- | --- |
| intended observations | 15 |
| final scientific observations | 15 |
| infrastructure-invalid attempts | 1 |
| cells completed on a pre-authorised attempt-2 identity | 1 |
| network-preflight refusals (before task delivery, nothing consumed) | 4 |
| model `claude-sonnet-5` resolved on every delivered attempt | yes |
| effort readback validated on every delivered attempt | yes |
| runtime `2.1.229` on every delivered attempt | yes |
| unique sessions | yes |
| provider cost, final observations (USD) | 33.72 |
| provider cost, infrastructure-invalid attempts (USD) | 0.00 |

Before observation 1 the readiness gate found that the Claude Code runtime on the host had been replaced after the freeze; the frozen `2.1.229` was restored, and the executor now refuses to launch on any other runtime.

## Deviation `SL-V2-BACKSTAGE-TQ-01-D1`

One attempt failed **before its task was delivered**: `BTQ-C02|C1|NON_RESET|R2` (WORKSPACE_PREPARATION_FAILED). The host entered standby during the frozen workspace warm-up, and a warm-up step's wall-clock timeout fired on wake. No model was invoked and nothing was spent. `WORKSPACE_PREPARATION_FAILED` is one of the infrastructure-invalid classes enumerated before data, but the frozen replacement gate reads a run record that a preparation failure never writes, so the pre-registered mechanism could not activate the cell's attempt-2 identity. The Study Lead authorised a narrow path that re-derives the class from the attempt's own artifacts and applies to that cell alone; the cell then completed on its pre-authorised attempt-2 identity. Its scientific coordinates are unchanged and it has no further retry.

## What this phase does not do

It estimates no treatment effect, runs no C4, confers no confirmatory eligibility, rescores nothing from Attempts 1 or 2, pools nothing with them, and does not create or run the future C1/C4 study.

## Files

| File | Content |
| --- | --- |
| `qualification_task_candidates.csv` | the five candidates, statement SHA-256, rule family, static qualification |
| `qualification_status.csv` | per-task counts and the frozen status |
| `qualification_run_rows.csv` | one row per attempt, the pre-delivery failure included |
| `qualification_public_summary.json` | the public projection of the frozen analysis |
