# 05 — efficiency pilot, execution attempt 2 (COMPLETED)

**36 of 36 rows executed · `claude-sonnet-5` · CLI 2.1.229 ·
2026-09-16T14:28:58Z → 20:02:54Z · authority `SL-V2-EFF-01` (design) /
`SL-V2-EFF-RESTART-01` (this execution)**

> **Classification: completed non-confirmatory cost pilot.** Eligible for its own
> analysis; **not** confirmatory, and it produces **no architecture result**.

## Files here

| file | what it is |
| --- | --- |
| `efficiency_pilot_frozen_analysis_report.json` | **the analysis artifact** — output of the repository's frozen analysis, unmodified |
| `attempt2_endpoint_ratios.csv` | **derived** — every endpoint's paired median, n and C4-lower count |
| `attempt2_primary_pairs.csv` | **derived** — the 16 pairs behind the primary median |
| `attempt2_reset_overhead.csv` | **derived** — reset ÷ non-reset by task and condition |
| `attempt2_decision_clauses.csv` | **derived** — all 14 pre-registered clauses and their verdicts |
| `attempt2_provider_cost.csv` | **derived** — non-reset provider cost ratios |
| `attempt2_runs_raw_metrics.csv` | **derived** — all 36 runs, every captured metric |

Raw evidence stays at `D:\afci-runs\attempt-2` (≈4 159 files).

## Design

3 tasks (PT01, PT04, PT07) × {**C1** task only, **C4** explicit MAD} ×
{non-reset, reset} × 3 repetitions = 36 runs. Block-paired on
(task, reset state, repetition); condition order randomised within block from a
fixed seed (`AFCI_EFFICIENCY_PILOT_V1_20260914`, SHA-256 ordering, no language
RNG). Turn budgets 64 non-reset, 32 pre-reset, 32 post-reset.

## Execution

| | |
| --- | ---: |
| scheduled / executed | 36 / 36 |
| completed | 35 |
| refused | 1 |
| functionally valid | 34 (C1 **17/18**, C4 **17/18**) |
| paired-eligible blocks | **16 of 18** (12 required) |
| runs in the paired analysis | 32 |
| valid but unpaired | 2 |

Two blocks were lost, each stranding an otherwise-valid partner:

- **`PT01|RESET|R1`** — sequence 12 (C4) REFUSED with `MODEL_PROCESS_FAILED`: the
  model process exceeded 1800 s and was stopped. The operator log records
  14 308.7 s of wall clock (14:49:26Z → 18:47:55Z), and execution halted there
  until it resumed at sequence 13. The artifacts record the timeout, not its
  cause; a stalled stream during a host sleep is the operational reading but is
  not asserted here.
- **`PT04|RESET|R1`** — sequence 15 (C1) completed but never reached the governed
  reset checkpoint (`CK-EFF-FALLBACK-CI-AGENT-AFTER-EDIT`), so
  `functional_valid: false`.

## Primary endpoint — TOTAL_INPUT_TOKENS

| cut | n | median C4/C1 | C4 cheaper |
| --- | ---: | ---: | ---: |
| **overall** | 16 | **1.4014** | **4/16** |
| PT01 | 5 | 1.3372 | |
| PT04 | 5 | **0.9325** | |
| PT07 | 6 | 1.5419 | |
| NON_RESET | 9 | 1.5582 | |
| RESET | 7 | 1.3776 | |

## Secondary endpoints

| endpoint | n | median C4/C1 | C4 lower |
| --- | ---: | ---: | ---: |
| MODEL_WALL_SECONDS | 16 | 1.2660 | 4/16 |
| EXPLORATION_CALLS | 16 | 1.3939 | 3/16 |
| TOTAL_TOOL_CALLS | 16 | 1.1864 | 5/16 |
| UNIQUE_FILES_READ | 16 | 1.2111 | 0/16 |
| EDIT_AND_WRITE_CALLS | 16 | 1.9167 | 0/16 |
| TOTAL_OUTPUT_TOKENS | 9 | 1.4671 | 1/9 |
| provider cost USD | 9 | 1.4928 | 2/9 |
| CI_COMMAND_RUNS | 16 | 1.0000 | 1/16 |
| TEST_COMMAND_RUNS | 0 | not captured | — |

## Reset recovery (reset ÷ non-reset; lower is better)

| endpoint | tasks where C4's overhead is lower |
| --- | --- |
| TOTAL_INPUT_TOKENS | **2 of 3** — PT01, PT07 |
| MODEL_WALL_SECONDS | **3 of 3** — PT01, PT04, PT07 |
| EXPLORATION_CALLS | 2 of 3 — PT01, PT07 |
| TOTAL_TOOL_CALLS | 2 of 3 — PT01, PT07 |

## The decision

> **`STOP — NO EFFICIENCY SIGNAL JUSTIFIES FULL-SUITE EXPANSION`** (rule 11.4).
> `efficiency_claim_made = false`.

The minimum-pairs gate and both functional guardrails passed; every token and
secondary-endpoint threshold failed. The RESET-SPECIFIC GO branch failed **only**
on its overall token clause — its two reset-overhead clauses passed. All 14
clauses are in `attempt2_decision_clauses.csv`.

## Three limits that matter

1. **No architecture result.** `AFCI_EFFICIENCY_PILOT` is cost-only under its own
   frozen governance. `thresholds_depending_on_architecture` is empty and the
   report says so in place of an architecture endpoint. **None may be inferred.**
2. **Output tokens and cost are non-reset only.** A reset run's phase A is
   interrupted before its terminal result event — the only place the runtime
   reports output and cost — so those totals are **withheld, not zero and not
   estimated**. Input tokens are still exact, reconstructed from the streamed
   assistant messages. 17 of 36 rows carry no provider cost.
3. **No inferential statistics.** 16 paired blocks, 3 repetitions, 3 tasks. The
   report asserts `no_p_values`, `no_confidence_intervals`, `no_effect_estimate`.

## Integrity guarantees on this analysis

- `execution_attempt: 2` and `aborted_execution_attempt_excluded: 1` on the face
  of the report.
- `assert_single_execution_attempt` refuses a record set spanning attempts and
  refuses any Attempt-1 record even alone.
- Functional validity is read from exactly one place —
  `record.functional_evaluation.functional_valid` — never inferred from CI
  success, model prose, exit status, architecture score or files changed.

## Reproducing it

```sh
python experiments/v2/harness/efficiency_pilot_analysis.py \
    --records <the 36 afci-efficiency-pilot-* directories under D:\afci-runs\attempt-2> \
    --out report.json
```

**Pass the 36 directories, not the `attempt-2` root.** The root also holds 12
dry-run readiness records under `readiness-context-audit\` that share the R1
blocks' (task, condition, repetition) coordinates. Including them corrupts block
pairing and yields **12** eligible blocks and a median of **1.3895** instead of the
correct **16** and **1.4014**. The report in this folder was generated the correct
way.
