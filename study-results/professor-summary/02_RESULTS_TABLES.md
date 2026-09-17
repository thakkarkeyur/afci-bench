# AFCI-Bench — results tables

All figures recomputed from raw evidence on 2026-09-17. Traces in
[`../AFCI_EVIDENCE_INDEX.md`](../AFCI_EVIDENCE_INDEX.md).

---

## A. v1 original study (48 runs, model "Opus 7", 2026-04-20 → 04-23)

### A.1 Headline

| metric | baseline | AFCI | relative | per-task direction |
| --- | ---: | ---: | ---: | --- |
| non-reset code churn, mean | 576.58 | 955.42 | **+65.7%** | AFCI higher in **12/12** |
| non-reset test churn, mean | 172.67 | 244.00 | **+41.3%** | AFCI higher in **12/12** |
| reset true drift ΔCodeLOC, mean | 307.7 | 670.5 | **+117.9%** | AFCI **lower** in **1/12** |
| CI pass | 100% | 100% | — | 48/48 (saturated) |

Code churn = `code_additions + code_deletions`. True reset drift =
`|CodeChurn_reset − CodeChurn_nonreset|` per task.

### A.2 Per-task code churn, non-reset

| task | baseline | AFCI | AFCI/baseline | higher |
| --- | ---: | ---: | ---: | --- |
| T01 | 321 | 346 | 1.078 | AFCI |
| T02 | 437 | 517 | 1.183 | AFCI |
| T03 | 497 | 569 | 1.145 | AFCI |
| T04 | 512 | 743 | 1.451 | AFCI |
| T05 | 518 | 805 | 1.554 | AFCI |
| T06 | 534 | 875 | 1.639 | AFCI |
| T07 | 542 | 938 | 1.731 | AFCI |
| T08 | 549 | 994 | 1.810 | AFCI |
| T09 | 678 | 1235 | 1.821 | AFCI |
| T10 | 713 | 1327 | 1.861 | AFCI |
| T11 | 804 | 1523 | 1.894 | AFCI |
| T12 | 814 | 1593 | 1.957 | AFCI |

The monotone rise in both arms is the **L1 accumulation artefact**: the working
tree was never reset between tasks, so later tasks inherit earlier edits. Read the
trend as an artefact, not a finding.

### A.3 Condition-level churn (a different construct from A.1 row 3)

| condition | n | mean code churn | mean test churn | mean files changed | CI pass |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 12 | 576.58 | 172.67 | 9.25 | 100% |
| afci | 12 | 955.42 | 244.00 | 13.58 | 100% |
| baseline_reset | 12 | 268.92 | 104.92 | 5.83 | 100% |
| afci_reset | 12 | 286.25 | 97.00 | 5.83 | 100% |

### A.4 Architecture in v1

| | |
| --- | --- |
| AFCI-Guard reported | 0 violations in all 48 runs |
| status | **INVALID FOR INFERENCE** |
| why | the guard matches literal `libs/core` paths; the codebase uses `@afci-bench/*` aliases, so the regexes never fire (L3) |
| `layer_jaccard` | constant 1.0 by construction — degenerate (L5) |

**These zeros are not measurements.** They are blank in the master run results.

---

## B. PT08 / PT09 / PT10 — diagnostics and qualification

All `claude-sonnet-5`, CLI 2.1.229, condition C1, sterile execution, model
identity VALIDATED and context audit CLEAN on every run.

### B.1 Summary

| task | runs | functional | acceptance cases | applicable opportunities | target violations | classification |
| --- | ---: | ---: | --- | ---: | ---: | --- |
| PT08 | 3 | **3/3** | 15/15 per run | 1 per run (3 total) | **0/3** | diagnostic: architecture FLOOR |
| PT09 | 3 | **3/3** | 14/14 per run | 1 per run (3 total) | **0/3** | **FAIL / ARCHITECTURE FLOOR** |
| PT10 | 3 | **3/3** | 8/8 per run | 1 per run (3 total) | **1/3** | **REVISE / WEAK PRESSURE** |

Consequence for PT09 and PT10: **STOP / REASSESS** for each instrument.
Consequence for PT08: **PT08 = REVISE; benchmark investment = CONTINUE**.

The classification rule was frozen before the first observation
(`SL-V2-QUAL-01` §7): QUALIFY needs ≥2 functional-valid runs *and* the target
violation in ≥2 of them; exactly 1 gives REVISE / WEAK PRESSURE; 0 gives FAIL /
ARCHITECTURE FLOOR.

### B.2 PT10's single violation

| | |
| --- | --- |
| repetition | 3 |
| what was violated | the **target architecture opportunity** |
| applicable / violated | 1 / 1 |
| form | one forbidden import, one line, one already-existing file, no new file |
| severity | blocker |
| confidence | certain (automated) |

One import, one line, no new file — the intended shortcut.

The opportunity id, the rule id, the forbidden source and target scopes and the
anchor path are withheld: they are hidden evaluator semantics, and publishing them
would disclose PT10's architecture answer to any future participant. They are
retained in the private evaluator repository. **No numeric result is withheld** —
the counts above are the complete finding. `04_EVIDENCE_MAP.md` gives the pointer
chain from this claim to the private evidence.

### B.3 What these three runs did **not** produce

No treatment effect, no condition contrast, no effect size, no power estimate.
Every artifact carries `is_result: false` and `scored: false`.

---

## C. Sonnet efficiency pilot — Attempt 2 (36 runs, 2026-09-16)

3 tasks × {C1 task-only, C4 explicit MAD} × {non-reset, reset} × 3 repetitions,
block-paired, randomised within-block condition order.

### C.1 Execution

| | |
| --- | ---: |
| scheduled / executed | 36 / 36 |
| completed | 35 |
| refused | 1 (sequence 12, `MODEL_PROCESS_FAILED`) |
| functionally valid | 34 — C1 **17/18**, C4 **17/18** |
| paired-eligible blocks | **16 of 18** (12 required) |
| runs in the paired analysis | 32 |
| valid but unpaired | 2 |

### C.2 Primary endpoint — TOTAL_INPUT_TOKENS (lower is better for C4)

| cut | n | median C4/C1 | C4 cheaper |
| --- | ---: | ---: | ---: |
| **overall** | 16 | **1.4014** | **4/16** |
| PT01 | 5 | 1.3372 | |
| PT04 | 5 | **0.9325** | |
| PT07 | 6 | 1.5419 | |
| NON_RESET arm | 9 | 1.5582 | |
| RESET arm | 7 | 1.3776 | |

PT04 is the only task where C4 was cheaper on median.

### C.3 Secondary endpoints

| endpoint | n | median C4/C1 | C4 lower | note |
| --- | ---: | ---: | ---: | --- |
| MODEL_WALL_SECONDS | 16 | 1.2660 | 4/16 | |
| EXPLORATION_CALLS | 16 | 1.3939 | 3/16 | |
| TOTAL_TOOL_CALLS | 16 | 1.1864 | 5/16 | |
| UNIQUE_FILES_READ | 16 | 1.2111 | 0/16 | |
| EDIT_AND_WRITE_CALLS | 16 | 1.9167 | 0/16 | largest gap |
| TOTAL_OUTPUT_TOKENS | 9 | 1.4671 | 1/9 | non-reset only |
| provider cost USD | 9 | 1.4928 | 2/9 | non-reset only |
| CI_COMMAND_RUNS | 16 | 1.0000 | 1/16 | the only parity |
| TEST_COMMAND_RUNS | 0 | **not captured** | — | no paired observation |

Output tokens and cost are non-reset only: a reset run's phase A is interrupted
before its terminal result event, so those totals are **withheld, not estimated**.

### C.4 Reset recovery (reset ÷ non-reset; lower overhead is better)

| endpoint | tasks where C4's overhead is lower |
| --- | --- |
| TOTAL_INPUT_TOKENS | **2 of 3** — PT01, PT07 |
| MODEL_WALL_SECONDS | **3 of 3** — PT01, PT04, PT07 |
| EXPLORATION_CALLS | 2 of 3 — PT01, PT07 |
| TOTAL_TOOL_CALLS | 2 of 3 — PT01, PT07 |

### C.5 The pre-registered decision

| branch | clause | result |
| --- | --- | --- |
| gate 11.0 | ≥12 of 18 blocks paired-valid | **PASS** (16) |
| STRONG GO 11.1.2 | functional guardrail | **PASS** |
| STRONG GO 11.1.3 | median token ratio ≤ 0.90 | FAIL (1.4014) |
| STRONG GO 11.1.4 | C4 cheaper in ≥60% of pairs | FAIL (4/16) |
| STRONG GO 11.1.5 | ≥2 of 3 tasks with median < 1 | FAIL (PT04 only) |
| QUALIFIED GO 11.2.3 | median token ratio ≤ 1.10 | FAIL (1.4014) |
| QUALIFIED GO 11.2.4 | ≥1 secondary endpoint meets its ceiling | FAIL (none) |
| QUALIFIED GO 11.2.5 | qualifying endpoint improves in ≥2 of 3 tasks | FAIL (none) |
| RESET-SPECIFIC 11.3.2 | overall token ratio ≤ 1.10 | FAIL (1.4014) |
| RESET-SPECIFIC 11.3.3 | C4 token reset-overhead lower in ≥2 of 3 tasks | **PASS** |
| RESET-SPECIFIC 11.3.4 | C4 time-or-exploration reset-overhead lower in ≥2 of 3 | **PASS** |

> **Outcome (rule 11.4): `STOP — NO EFFICIENCY SIGNAL JUSTIFIES FULL-SUITE
> EXPANSION`.** `efficiency_claim_made = false`.

The RESET-SPECIFIC branch failed **only** on its overall token clause. Both of its
reset-overhead clauses passed. That is the whole basis of the reset-recovery
signal, and it is why the signal is reported as motivating, not as a result.

### C.6 Not produced

**No architecture endpoint.** `AFCI_EFFICIENCY_PILOT` is cost-only by frozen
governance, `thresholds_depending_on_architecture` is empty, and no architecture
claim may be derived from it.

---

## CC. Lower-model pilot — Haiku 4.5 (18 runs, 2026-09-17)

Authority `SL-V2-LOWER-MODEL-01`. Model `claude-haiku-4-5-20251001`, CLI
`2.1.229`, non-reset only, 64 turns, 3 tasks × 2 conditions × 3 repetitions.
Quality and efficiency are two **independent** channels and are combined into no
single score.

### CC.1 Execution

| | |
| --- | ---: |
| scheduled / executed | 18 / 18 |
| completed | 18 |
| refused | 0 |
| infrastructure-invalid attempts | 0 |
| functionally valid | 17 (C1 **8/9**, C4 **9/9**) |
| paired-eligible blocks | **8 of 9** |
| runs in the paired analysis | 16 |
| valid but unpaired | 1 |
| runs hitting the turn ceiling | 0 |

One block was lost: **`PT04|R2`** — the C1 run failed all 4 semantic acceptance
cases, stranding an otherwise-valid C4 partner.

### CC.2 Architecture quality (all 18 runs)

| arm | runs | applicable opportunities | violated | target-violation runs |
| --- | ---: | ---: | ---: | ---: |
| C1 | 9 | 9 | 0 | **0** |
| C4 | 9 | 9 | 0 | **0** |

By task, every cell is identical: 3 applicable, 0 violated, 0 target-violation
runs, in **both** arms, for PT01, PT04 and PT07 alike.

**This is an architecture floor.** C4 did not fail to beat C1; neither arm ever
violated the opportunity, so the comparison had nothing to discriminate. The same
floor was recorded for PT08 and PT09. No conclusion about the architecture
document's effect on placement can be drawn from it in either direction.

### CC.3 Efficiency endpoints (8 paired blocks; C4/C1, lower is better for C4)

| endpoint | n | median | PT01 | PT04 | PT07 | C4 lower |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **TOTAL_INPUT_TOKENS** (primary) | 8 | **2.0372** | 2.9214 | 1.7502 | 0.9038 | 2/8 |
| TOTAL_OUTPUT_TOKENS | 8 | 1.7804 | 2.5067 | 1.4358 | 0.7171 | 3/8 |
| MODEL_WALL_SECONDS | 8 | 1.5268 | 2.3801 | 1.2307 | 0.8427 | 3/8 |
| TOTAL_TOOL_CALLS | 8 | 1.5023 | 2.0000 | 1.4174 | 0.9412 | 2/8 |
| EXPLORATION_CALLS | 8 | 1.7308 | 2.0000 | 2.1683 | 1.0769 | 1/8 |
| UNIQUE_FILES_READ | 8 | 1.2500 | 1.0000 | 1.0833 | 1.5000 | 2/8 |
| EDIT_AND_WRITE_CALLS | 8 | 1.1741 | 2.0000 | 1.1741 | 0.8750 | 2/8 |
| CI_COMMAND_RUNS | 8 | 1.0000 | 1.0000 | 0.7500 | 0.5000 | 3/8 |
| provider cost USD | 8 | 1.8865 | 2.5232 | 1.5777 | 0.8078 | 2/8 |
| TEST_COMMAND_RUNS | 1 | 0.0000 | — | — | 0.0000 | 1/1 |

Provider cost is complete for **all 8 pairs** here, unlike the Sonnet pilot, because
every non-reset run emits a terminal result event. C1 total $1.3862, C4 total
$2.0068 over the paired blocks; $3.80 for all 18 runs.

**PT07 is the one task where C4 is directionally cheaper** on tokens, time, output
and cost. PT01 is the most expensive for C4 on every endpoint. This is descriptive
and rests on 2–3 blocks per task.

### CC.4 Rework and change size (8 paired blocks)

| | C1 | C4 |
| --- | ---: | ---: |
| EDIT_CALLS | 54 | 66 |
| WRITE_CALLS | 2 | 0 |
| FILES_REEDITED | 16 | 20 |
| REPEATED_FILE_READS | 16 | 43 |
| FAILED_TEST_OR_CI_CYCLES | 13 | 9 |
| TURNS_USED | 229 | 309 |
| files changed | 25 | 30 |
| lines added / removed | 1755 / 134 | 1932 / 186 |
| net lines | +1621 | +1746 |

C4 wrote more and re-read more, but needed **fewer** failed CI cycles (9 vs 13).

### CC.5 The pre-registered decision

Frozen in `SL-V2-LOWER-MODEL-01` §12 before any observation existed.

| signal | criterion | observed | verdict |
| --- | --- | --- | --- |
| QUALITY | C4 fewer target-violation runs overall | 0 vs 0 | **FAIL** (tie at the floor) |
| QUALITY | improvement in ≥ 2 of 3 tasks | 0 of 3 | **FAIL** |
| QUALITY | C4 valid no more than 1 below C1 | 9 vs 8 (deficit −1) | PASS |
| EFFICIENCY | C4 valid no more than 1 below C1 | 9 vs 8 (deficit −1) | PASS |
| EFFICIENCY | median TOKEN_RATIO < 1.00 | 2.0372 | **FAIL** |
| EFFICIENCY | median EXPLORATION_RATIO ≤ 0.80 | 1.7308 | **FAIL** |
| EFFICIENCY | median TOTAL_TOOL_RATIO ≤ 0.85 | 1.5023 | **FAIL** |

> **`NO LOWER-MODEL SIGNAL — DO NOT EXPAND THE SYNTHETIC LOWER-MODEL MATRIX`**

Both functional guardrails passed — and C4 was in fact *better* functionally
(9/9 vs 8/9). Every quality and efficiency trigger failed.

### CC.6 Descriptive comparison with Sonnet (never pooled)

| C4 / C1, **non-reset only** | Sonnet (`AFCI_EFFICIENCY_PILOT`) | Haiku 4.5 (`AFCI_LOWER_MODEL_PILOT`) |
| --- | ---: | ---: |
| median TOTAL_INPUT_TOKENS | 1.5582 (n=9) | **2.0372** (n=8) |
| architecture endpoint | **not produced** (cost-only governance) | produced, at the floor |
| functional validity | 17/18 vs 17/18 (all reset states) | C1 8/9, C4 9/9 |

Difference in token ratio: **+0.479**, the lower model showing the *higher* C4/C1
ratio. Two separate experiments on two separate models, reported side by side. No
test, no interaction estimate, no pooled model. The Sonnet row is read from
[`../05_efficiency_attempt_2_completed/`](../05_efficiency_attempt_2_completed/).

### CC.7 Not produced

No p-values, no confidence intervals, no effect estimate, no power estimate. The
architecture endpoint is descriptive and enters no `E1`, treatment-effect or power
analysis. No private opportunity or rule identifier appears in this package.

---

## D. All experiments — status and run counts

| experiment | planned | attempted | completed | usable | paired blocks | status | analysis eligible | confirmatory |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| `V1_ORIGINAL` | 48 | 48 | 48 | 0 | 24 | COMPLETE_PUBLISHED | no | no |
| `V2_PT08_DIAGNOSTIC` | 3 | 3 | 3 | 0 | 0 | COMPLETE | no | no |
| `V2_PT09_QUALIFICATION` | 3 | 4 | 3 | 0 | 0 | COMPLETE | no | no |
| `V2_PT10_QUALIFICATION` | 3 | 3 | 3 | 0 | 0 | COMPLETE | no | no |
| `V2_EFF_ATTEMPT1` | 36 | 9 | 7 | 0 | 0 | ABORTED_INFRASTRUCTURE_ATTEMPT | no | no |
| `V2_EFF_ATTEMPT2` | 36 | 36 | 35 | 34 | 16 | COMPLETE | **yes** | no |
| `V2_LOWER_MODEL_PILOT` | 18 | 18 | 18 | 17 | 8 | COMPLETE | **yes** | no |
| `OPEN_SOURCE_COMPLEXITY_STUDY` | — | 0 | 0 | 0 | 0 | **NOT STARTED** | no | no |

**Totals: 121 run/attempt rows; 50 eligible; 0 confirmatory.**

### D.1 Efficiency Attempt 1, in detail

| | |
| --- | ---: |
| scheduled | 36 |
| attempted | 9 |
| never started | 27 |
| intact governed observations | 7 |
| damaged | 2 |
| collision pairs in the schedule | 18 |
| analyses performed | **0** |

Cause: `derive_run_id` omitted the reset state, so 36 rows derived only 18 ids.
Excluded wholesale — including the 7 intact rows, because which rows survived is a
selection mechanism nobody designed.

---

## E. Metric availability matrix

`AVAILABLE` = measured and usable · `PARTIAL` = measured with a stated restriction
· `NOT CAPTURED` = never instrumented (blank, **not** zero) · `INVALID` = recorded
but not usable for inference · `EXCLUDED` = attempt aborted.

| metric | v1 | PT08 | PT09 | PT10 | Eff 1 | Eff 2 | Lower-Model |
| --- | --- | --- | --- | --- | --- | --- | --- |
| functional correctness | NOT CAPTURED | AVAILABLE 3/3 | AVAILABLE 3/3 | AVAILABLE 3/3 | EXCLUDED | AVAILABLE 17/18 vs 17/18 | AVAILABLE 8/9 vs 9/9 |
| architecture violations | **INVALID** (L3) | AVAILABLE 0/3 | AVAILABLE 0/3 | AVAILABLE 1/3 | EXCLUDED | **NOT PRODUCED** (cost-only) | **AVAILABLE** 0/9 vs 0/9 (floor) |
| code churn | AVAILABLE | NOT CAPTURED | NOT CAPTURED | NOT CAPTURED | EXCLUDED | NOT CAPTURED | NOT CAPTURED |
| test churn | AVAILABLE | NOT CAPTURED | NOT CAPTURED | NOT CAPTURED | EXCLUDED | NOT CAPTURED | NOT CAPTURED |
| CI success | AVAILABLE (saturated) | NOT CAPTURED | NOT CAPTURED | NOT CAPTURED | EXCLUDED | AVAILABLE (as call count) | AVAILABLE (as call count) 1.0000 |
| input tokens | NOT CAPTURED | NOT CAPTURED | NOT CAPTURED | NOT CAPTURED | EXCLUDED | **AVAILABLE** 1.4014 | **AVAILABLE** 2.0372 |
| output tokens | NOT CAPTURED | NOT CAPTURED | NOT CAPTURED | NOT CAPTURED | EXCLUDED | PARTIAL 1.4671 (n=9) | **AVAILABLE** 1.7804 |
| wall time | NOT CAPTURED | PARTIAL (process) | PARTIAL (process) | PARTIAL (process) | EXCLUDED | **AVAILABLE** 1.2660 | **AVAILABLE** 1.5268 |
| provider cost | NOT CAPTURED | NOT CAPTURED | NOT CAPTURED | NOT CAPTURED | EXCLUDED | PARTIAL 1.4928 (n=9) | **AVAILABLE** 1.8865 (n=8) |
| tool calls | NOT CAPTURED | NOT CAPTURED | NOT CAPTURED | NOT CAPTURED | EXCLUDED | **AVAILABLE** 1.1864 | **AVAILABLE** 1.5023 |
| exploration calls | NOT CAPTURED | NOT CAPTURED | NOT CAPTURED | NOT CAPTURED | EXCLUDED | **AVAILABLE** 1.3939 | **AVAILABLE** 1.7308 |
| unique files read | NOT CAPTURED | NOT CAPTURED | NOT CAPTURED | NOT CAPTURED | EXCLUDED | **AVAILABLE** 1.2111 | **AVAILABLE** 1.2500 |
| edit/write effort | NOT CAPTURED | NOT CAPTURED | NOT CAPTURED | NOT CAPTURED | EXCLUDED | **AVAILABLE** 1.9167 | **AVAILABLE** 1.1741 |
| re-edits | NOT CAPTURED | NOT CAPTURED | NOT CAPTURED | NOT CAPTURED | EXCLUDED | AVAILABLE per run (no paired endpoint) | AVAILABLE per run (no paired endpoint) |
| reset recovery | AVAILABLE (ΔCodeLOC) | NOT CAPTURED | NOT CAPTURED | NOT CAPTURED | EXCLUDED | **AVAILABLE** 2/3 tokens, 3/3 time | N/A (non-reset only by design) |
| LOC changed | AVAILABLE | NOT CAPTURED | NOT CAPTURED | NOT CAPTURED | EXCLUDED | NOT CAPTURED | **AVAILABLE** +1621 vs +1746 net |
| test command runs | NOT CAPTURED | NOT CAPTURED | NOT CAPTURED | NOT CAPTURED | EXCLUDED | NOT CAPTURED (n=0) | NEAR-ABSENT (n=1) |

The machine-readable version is
[`../AFCI_METRICS_MATRIX.csv`](../AFCI_METRICS_MATRIX.csv).
