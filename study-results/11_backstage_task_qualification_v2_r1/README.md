# 11 — Backstage task qualification V2-R1: INSUFFICIENT ADDITIONAL QUALIFIED TASKS

> **Every row in this directory is: instrument qualification / C1-only / pre-treatment /
> not AFCI treatment evidence / clean re-execution of the halted V2.**

`AFCI_BACKSTAGE_TASK_QUALIFICATION_V2_R1`, governed by
[`SL-V2-BACKSTAGE-TQ-02-R1`](../../docs/v2/AFCI_BACKSTAGE_TASK_QUALIFICATION_V2_R1_DECISION.md),
frozen before its first observation.

## Why this phase exists

Task Qualification V2 ([10](../10_backstage_task_qualification_v2/)) was **HALTED after 1 of 15
observations and is excluded wholesale** because of a scientific-runtime instrumentation defect:
its runtime pin launched the frozen Claude Code `2.1.229` binary through an extensionless path, and
the built-in Grep/Glob tools, which re-launch their own executable, could not start. Its one
observation is not qualification evidence; it is not rescored, reused or pooled here, and every V2
candidate status stays NOT DETERMINED in V2's own record. V2 cost $1.3543, all
of it under the defect; that cost is reported, not hidden.

**V2-R1 re-ran all five frozen V2 candidates from scratch** — the same statements, oracles, scorers,
references and rule families, byte for byte — with a new seed, new run ids, new sessions and new
workspaces, after a **pre-data runtime correction**: the scientific runtime is still exactly
`2.1.229`, launched as a byte-identical copy that carries the `.exe` extension. Before
any scientific task was delivered, a real, non-scientific smoke test proved that Grep and Glob run
under that executable (and that the extensionless path reproduces the defect).

It ran the baseline condition **C1 only**: no C4 observation, no architecture packet, no treatment
effect. Backstage Attempt 1 ([07](../07_backstage_pilot_attempt_1_halted/)) remains HALTED /
EXCLUDED, Attempt 2 ([08](../08_backstage_pilot_attempt_2_completed/)) remains COMPLETE with its frozen
result, Task Qualification V1 ([09](../09_backstage_task_qualification_v1/)) remains COMPLETE with
INSUFFICIENT QUALIFIED TASKS, and the halted V2 remains as recorded. None is rescored or pooled with
this phase. `BTQ-T5` was not re-run.

## Outcome

> **INSUFFICIENT ADDITIONAL QUALIFIED TASKS**

0 of 5 candidates qualified.

Combined qualified-task inventory (V1 + V2-R1): `BTQ-T5`.

| Slot | Task | Architecture rule family | FUNCTIONAL_VALID | Target violation | MAX_TURNS | Permission denials | Provider cost (USD) | Status |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Q6 | `BTQ2-C01` | family E: extension contract placement / ownership | 0 / 3 | 0 / 3 | 2 / 3 | 18 | 8.52 | **BOTH_REJECT** |
| Q7 | `BTQ2-C02` | family P: package / role ownership | 1 / 3 | 0 / 3 | 3 / 3 | 13 | 13.64 | **BOTH_REJECT** |
| Q8 | `BTQ2-C03` | family P: package / role ownership | 3 / 3 | 0 / 3 | 0 / 3 | 10 | 5.36 | **ARCHITECTURE_FLOOR_REJECT** |
| Q9 | `BTQ2-C04` | family S: shared / public contract ownership | 2 / 3 | 0 / 3 | 1 / 3 | 36 | 10.67 | **ARCHITECTURE_FLOOR_REJECT** |
| Q10 | `BTQ2-C05` | family S: shared / public contract ownership | 2 / 3 | 0 / 3 | 3 / 3 | 3 | 12.71 | **ARCHITECTURE_FLOOR_REJECT** |

## The frozen rule (V2's, unchanged)

A candidate is **QUALIFIED** iff `FUNCTIONAL_VALID` in at least 2 of 3 observations **and** `TARGET_ARCHITECTURE_VIOLATION` in at least 1 of 3. Otherwise `FUNCTIONAL_REJECT`, `ARCHITECTURE_FLOOR_REJECT` or `BOTH_REJECT`. A MAX_TURNS observation counts and was never retried. All 15 observations ran in the frozen order, whatever interim statuses looked like.

Selection (frozen before data, V2's rule): `BTQ-T5` holds one slot. Fewer than two new QUALIFIED tasks is INSUFFICIENT ADDITIONAL QUALIFIED TASKS; exactly two are taken with `BTQ-T5`; more than two are narrowed to two by rule-family diversity with `BTQ-T5` and each other, then candidate slot (Q6 < Q7 < Q8 < Q9 < Q10). Never by counts beyond the thresholds, tokens, cost, speed, expected AFCI benefit or attractiveness.

## Selection limitation

> V2 deliberately selects tasks with measurable baseline architecture pressure. Any future C1-vs-C4 study using these tasks estimates AFCI performance on ARCHITECTURE-PRESSURE-QUALIFIED BACKSTAGE TASKS. It is NOT an unbiased estimate across arbitrary Backstage software changes.

Task qualification is C1-only and is **not** evidence that AFCI works. It measures only whether a task is attainable and under baseline architecture pressure.

## Reading a zero

13 of 15 final observations had exactly one applicable architecture opportunity, and in every one of them the placement was the legal one (0 target violations). The other 2 never wrote the task-mandated construct, so the placement decision did not arise in them: `BTQ2-C02` repetition 1 (functionally invalid, 0/5 semantic cases, 0 files changed); `BTQ2-C04` repetition 3 (functionally invalid, 0/3 semantic cases, 119 files changed). An observation without an opportunity cannot hold a target violation, so the outcome does not depend on them. A target-violation count of 0 therefore means the model made the legal placement decision every time the decision arose: an architecture floor under C1, not an opportunity the instrument failed to see.

## Execution

| Measure | Value |
| --- | --- |
| intended observations | 15 |
| final scientific observations | 15 |
| infrastructure-invalid attempts | 2 |
| cells completed on a retry identity (a pre-authorised attempt 2, or the D1 attempt 3) | 1 |
| network-preflight refusals (before task delivery, nothing consumed) | 0 |
| model `claude-sonnet-5` resolved on every delivered attempt | yes |
| effort readback validated on every scientific observation | yes |
| runtime `2.1.229` reported by every delivered attempt | yes |
| byte-identical `.exe` runtime verified before every delivery | yes |
| Grep/Glob calls across all delivered attempts | 167 |
| built-in tool launch failures (the V2 defect) | 0 |
| unique sessions | yes |
| C4 observations | 0 |

The host was kept on AC power with sleep, hibernation and lid-close sleep disabled for the schedule, the VPN client was not running, and the host's settings were restored afterwards.

## Deviation `SL-V2-BACKSTAGE-TQ-02-R1-D1` — cell `BTQ2-C02|C1|NON_RESET|R2`

Both frozen attempts of this cell failed before any model turn: the host's Claude Code sign-in credential, which every sterile run copies, had expired during the unattended night and could not be refreshed from the copy, so the runtime reported an authentication failure within a fraction of a second (0 model turns, 0 tokens, $0, no tool call). Both attempts were infrastructure-invalid under the frozen classes; the frozen plan reserves no third attempt, so the executor stopped, as designed.

The Study Lead decided, **before reading any outcome** of the eight completed cells and before any later cell started, to authorise **one** additional identity for this cell only (execution attempt 3), derived exactly like every other identity and usable only when both spent attempts' own records prove the authentication failure with zero model processing. From then on, every launch first required the host credential to stay valid for at least 120 minutes. Nothing else changed: the plan, its digests, the candidates, oracles, scorers, rules and thresholds are the frozen ones. The attempt-3 identity ended as **SCIENTIFIC_OBSERVATION**.

## Cost

| Scope | Provider cost (USD) |
| --- | ---: |
| V2-R1, final observations | $50.9016 |
| V2-R1, failed infrastructure attempts | $0.0000 |
| V2-R1, pre-data runtime smoke test (2 non-scientific launches) | $0.1126 |
| **V2-R1 total** | **$51.0142** |
| halted V2 (all under the runtime defect; reported separately) | $1.3543 |
| Task Qualification V1 | $33.7180 |
| cumulative task qualification (V1 + halted V2 + V2-R1) | $86.0865 |
| cumulative Backstage (Attempts 1-2, V1, halted V2, V2-R1) | $129.2057 |

## What this phase does not do

It estimates no treatment effect, runs no C4, confers no confirmatory eligibility, re-runs or rescores nothing from Attempts 1/2, V1 or the halted V2, pools nothing with them, and does not create or run the future C1/C4 study.

## Files

| File | Content |
| --- | --- |
| `qualification_v2_r1_task_candidates.csv` | the five candidates, statement SHA-256, rule family, static re-verification |
| `qualification_v2_r1_status.csv` | per-task counts and the frozen status |
| `qualification_v2_r1_run_rows.csv` | one row per attempt, any pre-delivery failure included |
| `qualification_v2_r1_inventory.csv` | the combined qualified-task inventory and the future selection |
| `qualification_v2_r1_public_summary.json` | the public projection of the frozen analysis |
