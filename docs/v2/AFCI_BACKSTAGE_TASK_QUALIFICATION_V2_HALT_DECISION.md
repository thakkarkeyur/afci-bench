# SL-V2-BACKSTAGE-TQ-02-H1 — Backstage task qualification V2 HALTED

Status: **HALTED by Study-Lead decision on 2026-09-25, after 1 of 15 scheduled
observations.** No further model run will be made under `SL-V2-BACKSTAGE-TQ-02`.
Instrument qualification; C1 only; pre-treatment; **not AFCI treatment evidence**.

The pre-registration
([`AFCI_BACKSTAGE_TASK_QUALIFICATION_V2_DECISION.md`](AFCI_BACKSTAGE_TASK_QUALIFICATION_V2_DECISION.md))
is unchanged below its halt banner. Backstage Attempts 1 and 2 and Task
Qualification V1 are untouched, were re-verified unchanged after the halt, and
are never pooled with this phase.

## 1. What happened

| Time (IST) | Event |
| --- | --- |
| 19:24 | the frozen schedule starts; runtime `2.1.229` verified; network preflight passed |
| 19:45 | cell 1 workspace prepared; task delivered |
| 19:49 | cell 1 ends: 34 turns, completed naturally, a valid observation under the frozen classifier |
| 19:51 | cell 1 scored post hoc; cell 2 starts workspace preparation |
| 19:55 | inspection of cell 1 finds the runtime-launch defect (§2) |
| 19:57 | the executor is stopped **before cell 2's task delivery**: no model process was started |
| 20:23 | host power settings restored exactly; prior phases re-verified unchanged |

## 2. The defect

The V2 pre-registration pinned the runtime by launching the frozen Claude Code
`2.1.229` binary by its absolute path, so that the host's newer default CLI could
never be used. That file is byte-identical to the frozen release but has no
executable extension. The version and digest checks passed. Claude Code's
built-in **Grep** tool, however, starts its bundled search by re-launching the
running executable, and Windows cannot resolve an executable without an
extension, so the tool failed with *executable not found*. The built-in file-glob
tool uses the same mechanism and is presumed affected.

Task Qualification V1 ran the same version under its usual executable name: over
its 15 observations the Grep and glob tools returned **93 successful results and
no such error**. The defect was therefore new in V2, caused by the launch path,
and independent of task, placement and outcome. The readiness gate verified the
version, the digest and the executable's identity, but no pre-data gate
exercised a built-in tool.

## 3. What was observed

* **Cell 1** (`BTQ2-C01`, repetition 2, attempt 1): a valid observation under the
  frozen classifier — 34 of 96 turns, completed naturally, 0 files changed,
  `FUNCTIONAL_VALID` false (0 of 5 semantic cases), 0 applicable architecture
  opportunities, 4 permission denials, $1.3543. It was produced under the defect,
  so **it is not used as qualification evidence** and no status is derived from it.
* **Cell 2** (`BTQ2-C02`, repetition 3, attempt 1): stopped during workspace
  preparation, before task delivery, on discovering the defect. No model process,
  $0, no attempt 2 activated.
* **Cells 3–15:** never started.

## 4. The decision

Offered, before any further model run: (a) launch the byte-identical binary under
an executable name, prove the built-in tools with a smoke test, record a deviation
that classifies every observation launched by the extensionless path as
infrastructure-invalid (outcome-blind), and resume on the pre-authorised second
attempts; (b) continue unchanged with the tools broken; or (c) stop the phase.
**The Study Lead chose (c).**

## 5. Consequences

* **No candidate status is determined.** The frozen rule needs three observations
  per candidate; none has three valid, defect-free observations.
* **New QUALIFIED tasks: 0** — the frozen selection rule's first branch applies:
  **INSUFFICIENT ADDITIONAL QUALIFIED TASKS**, reached by halt, not by measurement.
  No further mining in this phase.
* **Qualified inventory for a future study:** `BTQ-T5` (Task Qualification V1) only.
* **All five V2 candidates remain statically qualified instruments** — reference
  matrix, visible gate, task/oracle alignment, leakage audit and real preparation
  all passed before data. Using them requires a new pre-data decision, with the
  launch path fixed and a pre-data check that exercises the built-in tools.
* **Cost:** V2 $1.3543, all of it under the defect. Backstage before V2 $76.8372
  (Attempt 1 $10.9275, Attempt 2 $32.1917, V1 $33.7180). Backstage cumulative
  **$78.1915**.
* **Selection-bias limitation** (unchanged): qualification selects tasks with
  measurable baseline architecture pressure; any study built on it estimates AFCI
  behaviour on ARCHITECTURE-PRESSURE-QUALIFIED BACKSTAGE TASKS only.

Rows and the results summary:
[`study-results/10_backstage_task_qualification_v2/`](../../study-results/10_backstage_task_qualification_v2/README.md).
