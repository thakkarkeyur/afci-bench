# AFCI-Bench - professor results delivery package

**Compiled 2026-09-18** from `study-results/` on branch `study-v2`, pinned to evidence
commit `cfdb646b22f4` (*study(backstage): halt AFCI pilot attempt 1 and record the escalation*) - the last change to the
evidence this package reports.

This package is safe to send outside the private evaluator repository. It carries
no private opportunity identifier, rule identifier, evaluator path, hidden
architecture rule, or hidden source/target label.

## Start here

| file | what it is |
| --- | --- |
| `AFCI_Professor_Results_Summary.md` | the 15-section narrative report - read this first |
| `AFCI_Professor_Results_Summary.pdf` | the same report, rendered |
| `AFCI_Professor_Results.xlsx` | 20 sheets: every matrix, every decision clause, every run |
| `AFCI_Professor_Full_Run_Results.csv` | all 128 run/attempt rows, excluded ones included |
| `AFCI_Professor_Metric_Definitions.md` | what each metric means and which way is better |
| `AFCI_Professor_Evidence_Map.md` | summary number -> analysis artifact -> run record -> raw artifact |

## Workbook sheets

| sheet | contents |
| --- | --- |
| `01_EXECUTIVE_SUMMARY` | programme totals, three result cards, the current research conclusion |
| `02_EXPERIMENT_INVENTORY` | one row per experiment set, including the one not started |
| `03_ALL_RUNS` | all 128 run/attempt records, every public-safe column |
| `04_FUNCTIONAL_MATRIX` | functional correctness by experiment, task and condition |
| `05_ARCHITECTURE_MATRIX` | architecture evidence, and what produced none |
| `06_TOKEN_MATRIX` | input and output tokens, by arm and reset state |
| `07_COST_MATRIX` | provider cost, with coverage stated before every figure |
| `08_TIME_MATRIX` | MODEL_WALL_SECONDS |
| `09_EXPLORATION_TOOLS` | exploration, tool calls, unique files, per tool type |
| `10_REWORK_CHANGE_MATRIX` | edits, re-edits, turns, files changed, LOC |
| `11_RESET_RECOVERY` | Sonnet only - reset overhead by task and condition |
| `12_SONNET_VS_HAIKU` | descriptive cross-model matrix, never pooled |
| `13_V1_HISTORICAL` | v1 results and the seven limitations that bound them |
| `14_DIAGNOSTICS` | PT08, PT09, PT10 in per-repetition detail |
| `15_EXCLUSIONS` | every excluded observation and every missing metric |
| `16_DECISION_MATRIX` | each frozen decision clause: criterion, threshold, observed, PASS/FAIL |
| `17_METRIC_AVAILABILITY` | metric x experiment availability grid |
| `18_EVIDENCE_MAP` | traceability, repository anchors, hashes |
| `19_METRIC_DEFINITIONS` | plain-English definitions |
| `20_RECOMPUTATION_AUDIT` | the 124 checks behind every figure in this package |

Five descriptive charts are embedded, on sheets 04, 05, 06, 07 and 12. None
carries a significance marking, because no significance test exists in this
programme. The ratio charts draw a parity line at 1.00 so the direction is
readable without reading the axis.

## Two rules that hold everywhere

1. **A missing metric is a blank, never a zero.** A blank cell means the metric
   was not captured for that run. Reading it as 0 would invent an observation.
2. **Every aggregate is published beside its coverage count.** A median over 8
   pairs and a median over 16 pairs are different claims, and the package says
   which it is every time.

## What this package is not

- It is **not confirmatory**. Of 128 run rows, 50
  are eligible for any analysis, all 50 belong to two
  non-confirmatory pilots, and **0** are confirmatory.
- It contains **no p-value, confidence interval, effect size or power estimate**,
  because none exists in this programme.
- It is a **secondary artifact**. Where it and a primary artifact disagree, the
  primary artifact wins.

## Started, then halted - no results

`V2_BACKSTAGE_PILOT`, the Backstage real-repository architecture pilot, began
execution and was **halted part-way**. It contributes **no analysable result**.

| field | value |
| --- | --- |
| status | **EXECUTION HALTED - ATTEMPT 1 (INFRASTRUCTURE)** |
| planned runs | 18 (3 tasks x 2 conditions x 3 repetitions, NON_RESET, 9 paired blocks) |
| attempted / valid observations / **usable** | 7 / 5 / **0** |
| run rows here | 7, all `eligible_for_analysis = false` |
| consumed | $10.93 provider cost, ~5.3 h model wall time |
| decisions | `SL-V2-BACKSTAGE-PILOT-01` (freeze), `SL-V2-BACKSTAGE-PILOT-02` (halt) |
| attempt record | `../07_backstage_pilot_attempt_1_halted/` |

Two scheduled observations were severed mid-task by a local network failure
(`INFRA_API_TRANSPORT`), *below* the turn ceiling. That is rerun-eligible under
`FAILURE_RERUN_POLICY.md` S2, but the launcher refuses any run id absent from
the frozen plan, so a replacement needs a recorded protocol amendment - and S5
directs repeated infrastructure failure to be **escalated, not silently
re-attempted** (`TD-N06`, open). Execution stopped rather than improvising.

**No `C1`-vs-`C4` comparison, arm total, ratio, median or continuation criterion
was computed, and none may be derived.** The schedule is 11 rows short, the arms
are unbalanced, no paired block is both complete and usable, and
`SL-V2-BACKSTAGE-PILOT-01` S11.3 forbids a confirmatory claim from this pilot
even when complete. **No matrix cell, chart point or figure in this package
comes from it.**

## Pre-registered, not started

`V2_BACKSTAGE_PILOT_ATTEMPT_2` is a **wholly new** 18-run execution of the same
frozen science, pre-registered by `SL-V2-BACKSTAGE-PILOT-03`. It has **no data**.

| field | value |
| --- | --- |
| status | **PRE-DATA / NOT STARTED** |
| planned runs | 18 (3 tasks x 2 conditions x 3 repetitions, NON_RESET, 9 paired blocks) |
| attempted / completed / **usable** | 0 / 0 / **0** |
| run rows here | 0 |
| decisions | `SL-V2-BACKSTAGE-PILOT-01` (science, unchanged), `SL-V2-BACKSTAGE-PILOT-03` (attempt-2 execution controls) |

It reuses the substrate, the three tasks and their bytes, the architecture
packet, the model, the effort level, the runtime, both conditions, the reset
state, the repetitions, the endpoints, the oracles, the scorer and the
continuation rule **unchanged**, and changes five execution controls: the turn
ceiling 64 -> 96, the Bash allowlist 8 -> 15 rules, a network preflight that
refuses before the task is delivered, 18 pre-authorised infrastructure-retry
identities, and real-destination path validation.

**Attempt 1 is retained above and is never pooled with, replaced by, or re-run
under attempt 2.** No scientific outcome from attempt 1 was used to change any
task, architecture packet, oracle, scorer, threshold, endpoint, metric or
treatment definition - and none could have been, because no `C1`-vs-`C4`
comparison was ever computed from it.

## Provenance

Reporting and export only. Producing this package executed no benchmark
observation, invoked no model, and changed no task definition, architecture
document, scorer, threshold, run plan, condition, raw run artifact or prior
analysis. The private evaluator repository was not modified and nothing was
pushed to it.

Every figure was recomputed from the run/attempt rows and checked against the
frozen per-experiment analysis artifacts: **124 checks,
0 mismatches**. Regenerate with:

```sh
python study-results/professor-delivery/_build/build_professor_delivery.py
```

`_build/` holds that generator. It reads only `study-results/` and writes only
this directory.

The build is **byte-reproducible**: running it twice on unchanged evidence
produces identical files, down to the SHA-256 of the workbook and the PDF. So if
you regenerate the package and `git status` is clean, nothing in it was edited by
hand after generation.
