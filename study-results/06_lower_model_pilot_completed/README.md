# 06 — lower-capability-model AFCI pilot (COMPLETED)

**18 of 18 rows executed · `claude-haiku-4-5-20251001` · CLI 2.1.229 ·
2026-09-17T21:08:23Z → 21:52:09Z · authority `SL-V2-LOWER-MODEL-01`**

> **Classification: completed non-confirmatory pilot with TWO independent
> endpoints.** Eligible for its own analysis; **not** confirmatory. Its
> architecture endpoint is **descriptive** and enters no `E1`, treatment-effect or
> power analysis. Its records are **never** pooled with the `claude-sonnet-5`
> efficiency pilot.

## Files here

| file | what it is |
| --- | --- |
| `lower_model_pilot_frozen_analysis_report.json` | **the analysis artifact** — output of the repository's frozen analysis, unmodified |
| `lower_model_runs_raw_metrics.csv` | **derived** — all 18 runs, every captured metric |
| `lower_model_endpoint_ratios.csv` | **derived** — every endpoint's paired median, n, task medians and C4-lower count |
| `lower_model_primary_pairs.csv` | **derived** — the 8 paired blocks behind every median |
| `lower_model_architecture_summary.csv` | **derived** — architecture aggregates, overall and by task |
| `lower_model_decision_clauses.csv` | **derived** — every frozen decision clause and its verdict |

Raw evidence stays at `D:\afci-runs\lower-model-pilot`; operator logs at
`D:\afci-runs\lower-model-pilot-logs`.

## Design

3 tasks (PT01, PT04, PT07) × {**C1** task only, **C4** explicit MAD} ×
**NON_RESET only** × 3 repetitions = 18 runs, 9 paired blocks. Block-paired on
(task, repetition); condition order and block order both randomised from a fixed
seed (`AFCI_LOWER_MODEL_PILOT_V1_20260917`, SHA-256 ordering, no language RNG).
Turn budget 64, identical in both arms.

The reset arm is **deliberately excluded** so that model capability is the single
moderator varied. Adding context-loss at the same time would leave any difference
attributable to either.

## The question it asked

> Does explicit architecture guidance become more useful when the coding model has
> less ability to infer the architecture from the repository on its own?

Two **independent** channels, combined into no single score: **quality** (does C4
reduce architecture violations without materially reducing functional
correctness?) and **efficiency** (does C4 reduce tokens, time, exploration or tool
effort?).

## Execution

| | |
| --- | ---: |
| scheduled / executed | 18 / 18 |
| completed | 18 |
| refused | 0 |
| infrastructure-invalid attempts | **0** |
| functionally valid | 17 (C1 **8/9**, C4 **9/9**) |
| paired-eligible blocks | **8 of 9** |
| runs in the paired analysis | 16 |
| valid but unpaired | 1 |
| runs at the turn ceiling | 0 |

One block was lost: **`PT04|R2`** — the C1 run failed all 4 semantic acceptance
cases, stranding an otherwise-valid C4 partner.

## Architecture quality (all 18 runs)

| arm | runs | applicable | violated | target-violation runs |
| --- | ---: | ---: | ---: | ---: |
| C1 | 9 | 9 | 0 | **0** |
| C4 | 9 | 9 | 0 | **0** |

Identical by task: 3 applicable, 0 violated in both arms for PT01, PT04, PT07.

**This is an architecture floor.** C4 did not fail to beat C1 — neither arm
violated anything. The frozen rule scores it FAIL because it requires *strictly
fewer* violations, and a tie at zero is not an improvement. Read it as **no
information**, not as evidence that the architecture document does nothing.

## Efficiency (8 paired blocks; C4/C1, lower is better for C4)

| endpoint | n | median | PT01 | PT04 | PT07 | C4 lower |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **TOTAL_INPUT_TOKENS** | 8 | **2.0372** | 2.9214 | 1.7502 | 0.9038 | 2/8 |
| TOTAL_OUTPUT_TOKENS | 8 | 1.7804 | 2.5067 | 1.4358 | 0.7171 | 3/8 |
| MODEL_WALL_SECONDS | 8 | 1.5268 | 2.3801 | 1.2307 | 0.8427 | 3/8 |
| TOTAL_TOOL_CALLS | 8 | 1.5023 | 2.0000 | 1.4174 | 0.9412 | 2/8 |
| EXPLORATION_CALLS | 8 | 1.7308 | 2.0000 | 2.1683 | 1.0769 | 1/8 |
| UNIQUE_FILES_READ | 8 | 1.2500 | 1.0000 | 1.0833 | 1.5000 | 2/8 |
| EDIT_AND_WRITE_CALLS | 8 | 1.1741 | 2.0000 | 1.1741 | 0.8750 | 2/8 |
| CI_COMMAND_RUNS | 8 | 1.0000 | 1.0000 | 0.7500 | 0.5000 | 3/8 |
| provider cost USD | 8 | 1.8865 | 2.5232 | 1.5777 | 0.8078 | 2/8 |
| TEST_COMMAND_RUNS | 1 | 0.0000 | — | — | 0.0000 | 1/1 |

Provider cost is complete for **all 8 pairs** — unlike the Sonnet pilot — because
every non-reset run emits a terminal `result` event. C1 total $1.3862, C4 total
$2.0068 over the paired blocks; $3.8007 across all 18 runs.

PT07 is the one task where C4 was directionally cheaper on tokens, time, output
and cost.

## The decision

> **`NO LOWER-MODEL SIGNAL — DO NOT EXPAND THE SYNTHETIC LOWER-MODEL MATRIX`**

Both functional guardrails passed — and C4 was the *better* functional arm (9/9
vs 8/9). Every quality and efficiency trigger failed. All clauses are in
`lower_model_decision_clauses.csv`.

## Descriptive comparison with Sonnet — never pooled

| C4 / C1, **non-reset only** | Sonnet | Haiku 4.5 |
| --- | ---: | ---: |
| median TOTAL_INPUT_TOKENS | 1.5582 (n=9) | **2.0372** (n=8) |
| architecture endpoint | **not produced** (cost-only) | produced, at the floor |

Difference **+0.479**, the lower model showing the *higher* ratio — the direction
**opposite** to the moderator hypothesis. Two separate experiments on two separate
models. No test, no interaction estimate, no pooled model, and **no randomised
cross-model causal effect**. The Sonnet pilot produced no architecture
measurement, so only the efficiency channel is comparable at all.

## Four limits that matter

1. **The quality channel answered nothing.** Both arms at zero violations. It
   cannot distinguish "the MAD does not help" from "the instrument cannot see
   help".
2. **The architecture endpoint rests on a pilot-scoped corpus exemption**
   (`SL-V2-LOWER-MODEL-01` §9), **not** a full architecture mutation corpus, and
   must never be described as one.
3. **No inferential statistics.** 8 paired blocks, 3 repetitions, 3 tasks. The
   report asserts `no_p_values`, `no_confidence_intervals`, `no_effect_estimate`.
4. **One lower-capability model, one synthetic 49-file substrate.** `TD-B03` stays
   open and `primary_model` stays `null`.

## Integrity guarantees on this analysis

- The analysis **refuses** a `claude-sonnet-5` record rather than filtering it
  out, so "never pooled" is a property of the code.
- The architecture summary and the efficiency summary share no input beyond the
  block list, neither reads the other's output, and the two continuation signals
  are evaluated independently.
- Functional validity is read from exactly one place —
  `record.functional_evaluation.functional_valid` — never inferred from CI
  success, model prose, exit status, architecture score or files changed.
- The public invocation boundary refuses to write a record naming any private
  opportunity or rule identifier.

## Reproducing it

```sh
python experiments/v2/harness/lower_model_pilot_analysis.py \
    D:\afci-runs\lower-model-pilot\*\run_record.json
```

All 18 directories under that root are substantive runs. Readiness records were
written to a **separate** root (`D:\afci-runs\lower-model-readiness`), so the
Attempt-2 trap — where 12 dry-run readiness records sharing the R1 blocks'
coordinates corrupted pairing — cannot recur here.
