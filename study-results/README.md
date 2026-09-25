# AFCI-Bench — consolidated study evidence package

**Compiled:** 2026-09-18
**Repository:** `afci-bench`, branch `study-v2`
**Scope:** every AFCI experiment executed to date, v1 and v2.
**Status of the benchmark:** study v2 remains **PRE-FREEZE**. Gate `G1` is not
passed, `primary_model` is still `null`, and **no confirmatory evidence has been
collected**.

This package is **reporting only**. It was produced by reading existing
artifacts and re-executing the already-frozen analysis over them. It creates no
run, invokes no model, and changes no task body, evaluator, metric, threshold,
governance state or raw artifact.

---

## Read this first

Four facts frame everything below, and each is verifiable from the files here.

1. **Nothing in this package is a confirmatory result.** Every experiment run so
   far is exploratory (v1), diagnostic (PT08), instrument qualification
   (PT09/PT10) or a non-confirmatory pilot (efficiency Attempt 2, lower-model
   pilot). No experiment has produced a treatment-effect estimate, and none is
   eligible to.
2. **No p-values, confidence intervals or effect sizes appear anywhere**, by
   design. The largest v2 experiment is a 3-repetition pilot, which supports
   none of them.
3. **Efficiency Attempt 1 is excluded wholesale**, including the seven rows that
   are individually intact. It is listed in full so the record is complete, never
   so a number can be taken from it.
4. **The headline v1 and Attempt-2 numbers in this package were recomputed from
   the raw evidence**, not copied from prior reports. Where a recomputation
   disagreed with a prior statement, the recomputation is reported and the
   discrepancy is named.

---

## What is in this package

| File | What it answers |
| --- | --- |
| [`AFCI_RESULTS_SUMMARY.md`](AFCI_RESULTS_SUMMARY.md) | What we found, what it supports, what it does not |
| [`AFCI_MASTER_EXPERIMENT_REGISTRY.csv`](AFCI_MASTER_EXPERIMENT_REGISTRY.csv) | One row per experiment set: counts, status, decision |
| [`AFCI_MASTER_RUN_RESULTS.csv`](AFCI_MASTER_RUN_RESULTS.csv) | One row per actual run/attempt (128 rows) |
| [`AFCI_METRICS_MATRIX.csv`](AFCI_METRICS_MATRIX.csv) | Which metric exists in which experiment, and at what status |
| [`AFCI_EVIDENCE_INDEX.md`](AFCI_EVIDENCE_INDEX.md) | Summary number → analysis artifact → run record → raw evidence |
| [`AFCI_EXCLUSIONS_AND_LIMITATIONS.md`](AFCI_EXCLUSIONS_AND_LIMITATIONS.md) | Everything that weakens or bounds the evidence |
| [`professor-summary/`](professor-summary/) | Five short documents suitable to share directly |

Per-experiment folders hold derived tables and pointers, not bulk artifacts:

- [`01_v1_original_study/`](01_v1_original_study/)
- [`02_pt08_diagnostic/`](02_pt08_diagnostic/)
- [`03_pt09_pt10_qualification/`](03_pt09_pt10_qualification/)
- [`04_efficiency_attempt_1_aborted/`](04_efficiency_attempt_1_aborted/)
- [`05_efficiency_attempt_2_completed/`](05_efficiency_attempt_2_completed/)
- [`06_lower_model_pilot_completed/`](06_lower_model_pilot_completed/)
- [`07_backstage_pilot_attempt_1_halted/`](07_backstage_pilot_attempt_1_halted/)
- [`08_backstage_pilot_attempt_2_completed/`](08_backstage_pilot_attempt_2_completed/)
- [`09_backstage_task_qualification_v1/`](09_backstage_task_qualification_v1/)

---

## The ten experiments at a glance

| id | what | runs (attempted → usable) | class | decision |
| --- | --- | --- | --- | --- |
| `V1_ORIGINAL` | 12 tasks × baseline/AFCI × reset/non-reset | 48 → 0 | exploratory | published, superseded |
| `V2_PT08_DIAGNOSTIC` | PT08 C1 difficulty diagnostic | 3 → 0 | diagnostic | PT08 = REVISE; benchmark = CONTINUE |
| `V2_PT09_QUALIFICATION` | PT09 C1 instrument qualification | 4 → 0 | qualification | FAIL / ARCHITECTURE FLOOR → STOP |
| `V2_PT10_QUALIFICATION` | PT10 C1 instrument qualification | 3 → 0 | qualification | REVISE / WEAK PRESSURE → STOP |
| `V2_EFF_ATTEMPT1` | efficiency pilot, first execution | 9 → 0 | aborted | excluded wholesale |
| `V2_EFF_ATTEMPT2` | efficiency pilot, second execution | 36 → 34 | cost pilot | STOP — no efficiency signal |
| `V2_LOWER_MODEL_PILOT` | lower-capability model pilot (Haiku 4.5) | 18 → 17 | quality + cost pilot | NO SIGNAL — do not expand |
| `V2_BACKSTAGE_PILOT` | Backstage real-repository pilot, attempt 1 | 7 → 0 | halted | excluded wholesale |
| `V2_BACKSTAGE_PILOT_ATTEMPT_2` | Backstage real-repository pilot, attempt 2 | 18 → 6 | architecture + cost pilot | NO ARCHITECTURE SIGNAL — do not expand |
| `V2_BACKSTAGE_TASK_QUALIFICATION_V1` | Backstage task qualification, C1 only | 16 → 0 | instrument qualification (pre-treatment, not treatment evidence) | INSUFFICIENT QUALIFIED TASKS — 1 of 5 qualified; stop |

"Usable" means *eligible to enter an analysis*. It is 0 for every experiment
except the efficiency Attempt 2, the lower-model pilot and Backstage Attempt 2,
and none of the three is confirmatory.

For Backstage Attempt 2 "usable" counts the **6** rows in the 3 functionally
valid paired blocks, which are the rows that enter the *efficiency* analysis.
All **18** enter the primary architecture endpoint, which is scored
independently of functional validity.

`V2_BACKSTAGE_TASK_QUALIFICATION_V1` is 16 attempts for 15 C1 observations: one
attempt failed before its task was delivered and its cell completed on the
pre-authorised attempt-2 identity. Every row is instrument qualification /
C1-only / pre-treatment / not AFCI treatment evidence, so none is usable by any
analysis.

---

## Evidence that stays where it is

Raw artifacts are large and are **not** copied into this repository. This
package stores pointers and hashes instead.

| Evidence | Location |
| --- | --- |
| v1 run records, prompts, patches | git branch `rerun-v1-opus7-artifacts` (not checked out) |
| PT08 diagnostic artifacts | `D:\pt08-diagnostic` |
| PT09/PT10 qualification artifacts | `D:\afci-v2-qual` |
| Efficiency Attempt 1 artifacts | `D:\afci-runs\obs`, `D:\afci-runs\logs` |
| Efficiency Attempt 2 artifacts | `D:\afci-runs\attempt-2` |
| Lower-model pilot artifacts | `D:\afci-runs\lower-model-pilot`, `D:\afci-runs\lower-model-pilot-logs` |

[`AFCI_EVIDENCE_INDEX.md`](AFCI_EVIDENCE_INDEX.md) maps each of these to the
specific files and hashes behind each summary number.

---

## How the numbers here were produced

- **v1** — recomputed in Python from `experiments/paper/results_v1.csv` and
  `drift_true_v1_codeonly.csv` on the `rerun-v1-opus7-artifacts` branch (read via
  `git show`; the branch is never checked out or merged). All 48 `run_meta.json`
  files were read to confirm model, base tag and CI exit code.
- **PT08 / PT09 / PT10** — read directly from the per-run `scoring_summary.json`
  / score JSON and `run_record.json`. No metric is derived.
- **Attempt 1** — read from the governed evidence inventory, which is itself
  derived from the artifacts rather than from prose.
- **Attempt 2** — produced by running the repository's own frozen analysis,
  `experiments/v2/harness/efficiency_pilot_analysis.py`, over the 36 governed run
  records, unmodified. Its report is included verbatim at
  [`05_efficiency_attempt_2_completed/efficiency_pilot_frozen_analysis_report.json`](05_efficiency_attempt_2_completed/efficiency_pilot_frozen_analysis_report.json).
- **Lower-model pilot** — produced by running the repository's own frozen
  analysis, `experiments/v2/harness/lower_model_pilot_analysis.py`, over the 18
  governed run records, unmodified. Its report is included verbatim at
  [`06_lower_model_pilot_completed/lower_model_pilot_frozen_analysis_report.json`](06_lower_model_pilot_completed/lower_model_pilot_frozen_analysis_report.json).
  Lines added/removed were computed by diffing each preserved post-run worktree
  against a rebuild of the prepared baseline, which reproduces the recorded
  prepared content hash `da7a679552d50857…` exactly.

One methodological note on that last step. The analysis recurses into whatever
directory it is handed. Pointing it at `D:\afci-runs\attempt-2` pulls in the 12
**dry-run readiness records** stored under `attempt-2\readiness-context-audit\`,
which share the task/condition/repetition coordinates of the real R1 blocks and
therefore corrupt block pairing — it then reports 12 eligible blocks instead of
16, and a median token ratio of 1.3895 instead of 1.4014. The report in this
package was generated against the **36 real observation directories only**. The
distinction matters and is recorded here rather than silently resolved.

---

## Reproducing the Attempt-2 analysis

```sh
python experiments/v2/harness/efficiency_pilot_analysis.py \
    --records <the 36 afci-efficiency-pilot-* directories under D:\afci-runs\attempt-2> \
    --out report.json
```

Pass the 36 directories explicitly. Do not pass the `attempt-2` root.
