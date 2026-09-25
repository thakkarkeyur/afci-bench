# 10 — Backstage task qualification V2: HALTED

`AFCI_BACKSTAGE_TASK_QUALIFICATION_V2`. **Halted after 1 of 15 scheduled
observations.** Pre-registration:
[`SL-V2-BACKSTAGE-TQ-02`](../../docs/v2/AFCI_BACKSTAGE_TASK_QUALIFICATION_V2_DECISION.md);
halt record: [`SL-V2-BACKSTAGE-TQ-02-H1`](../../docs/v2/AFCI_BACKSTAGE_TASK_QUALIFICATION_V2_HALT_DECISION.md).

**Instrument qualification; C1 only; pre-treatment; NOT AFCI treatment evidence.**
No C4 observation, no architecture packet, no treatment effect. Never pooled with
Backstage Attempts 1 or 2 or with Task Qualification V1.

## Nothing here is a qualification result

The frozen rule needs three observations per candidate. One observation exists,
and it was produced under a runtime-launch defect, so **no candidate status is
determined** and **no task newly qualified**. Every row carries
`eligible_for_analysis = false`.

## What happened

The V2 runtime pin launched the frozen Claude Code `2.1.229` binary by an
extensionless path. The version and digest checks passed, but Claude Code's
built-in Grep tool re-spawns its own executable, which Windows cannot resolve
without an executable extension, so the tool could not start. Task Qualification
V1 ran the same version under its usual executable name and never hit this:
93 successful Grep/Glob results, 0 such errors. The defect was new in V2,
independent of task and outcome, and no pre-data gate exercised a built-in tool.

| Seq | Slot | Task | Rep | Attempt | Status | Delivered | Functional | Arch (appl./viol.) | Turns | Files changed | Cost |
| ---: | --- | --- | ---: | ---: | --- | --- | --- | --- | --- | ---: | ---: |
| 1 | Q6 | `BTQ2-C01` | 2 | 1 | valid under the frozen classifier; produced under the defect | yes | FAIL (0/5) | 0/0 | 34/96 | 0 | $1.3543 |
| 2 | Q7 | `BTQ2-C02` | 3 | 1 | stopped during workspace preparation | no | — | — | — | — | $0 |

Cells 3–15 never started. Offered a fix under a recorded deviation, continuing
unchanged, or stopping, the Study Lead stopped the phase.

## The five candidates

| Slot | Task | Architecture rule family | Static qualification | Observations | Status |
| --- | --- | --- | --- | ---: | --- |
| Q6 | `BTQ2-C01` | family E: extension contract placement / ownership | STATIC_PASS | 1 (under the defect) | NOT DETERMINED |
| Q7 | `BTQ2-C02` | family P: package / role ownership | STATIC_PASS | 0 | NOT DETERMINED |
| Q8 | `BTQ2-C03` | family P: package / role ownership | STATIC_PASS | 0 | NOT DETERMINED |
| Q9 | `BTQ2-C04` | family S: shared / public contract ownership | STATIC_PASS | 0 | NOT DETERMINED |
| Q10 | `BTQ2-C05` | family S: shared / public contract ownership | STATIC_PASS | 0 | NOT DETERMINED |

All five remain statically qualified instruments (reference matrix, visible gate,
task/oracle alignment, leakage audit and real preparation all green); any future
use needs a new pre-data decision.

## Outcome and inventory

* New QUALIFIED tasks: **0** — **INSUFFICIENT ADDITIONAL QUALIFIED TASKS**, reached
  by halt, not by measurement.
* Qualified inventory for a future study: **`BTQ-T5`** (Task Qualification V1) only.
* Prior phases re-verified unchanged after the halt; host power settings restored.

## Cost

| Scope | Provider cost |
| --- | ---: |
| V2 (all of it under the runtime-launch defect) | $1.3543 |
| Backstage before V2 (Attempt 1, Attempt 2, V1) | $76.8372 |
| Backstage cumulative | $78.1915 |

**Selection-bias limitation.** This qualification intentionally selects tasks with
measurable baseline architecture pressure. A future treatment study built on its
selection estimates AFCI behaviour on ARCHITECTURE-PRESSURE-QUALIFIED BACKSTAGE
TASKS and must not be presented as an unbiased estimate over arbitrary Backstage
software changes.

Rows: [`qualification_v2_run_rows.csv`](qualification_v2_run_rows.csv).
