# AFCI-Bench — project status

**As at 2026-09-17.** Repository `afci-bench`, branch `study-v2`, commit `c544cc87`.

---

## Where the project stands

The v1 study is published. The v2 study is **built and working but pre-freeze**:
the harness, oracles and governance all execute end to end, and **no confirmatory
evidence has been collected**. Six experiments have run. One of them — the
efficiency pilot — reached a pre-registered decision, and that decision was
**STOP**.

## What has been run

| # | experiment | runs | class | outcome |
| --- | --- | ---: | --- | --- |
| 1 | v1 original study | 48 | exploratory | published (ASE 2026 artifact, Zenodo DOI) |
| 2 | PT08 C1 difficulty diagnostic | 3 | diagnostic | PT08 = REVISE; benchmark = CONTINUE |
| 3 | PT09 C1 qualification | 3 (+1 invalid) | qualification | FAIL / ARCHITECTURE FLOOR → STOP |
| 4 | PT10 C1 qualification | 3 | qualification | REVISE / WEAK PRESSURE → STOP |
| 5 | efficiency pilot, attempt 1 | 9 of 36 | aborted | infrastructure defect; excluded wholesale |
| 6 | efficiency pilot, attempt 2 | 36 of 36 | cost pilot | **STOP — no efficiency signal** |

**103 run/attempt rows recorded. 34 eligible for any analysis. 0 confirmatory.**

## The headline result

On the synthetic substrate with `claude-sonnet-5`, giving the model an explicit
architecture document (C4) was **more expensive** than giving it the task alone
(C1), with no functional benefit.

| | C4 / C1 |
| --- | ---: |
| input tokens (primary endpoint) | **1.40** |
| wall time | 1.27 |
| exploration calls | 1.39 |
| tool calls | 1.19 |
| unique files read | 1.21 |
| edit/write calls | 1.92 |
| provider cost (non-reset) | 1.49 |
| functional validity | 17/18 vs 17/18 |

One counter-signal: under context reset, C4's **recovery overhead** was lower in
2 of 3 tasks for tokens and 3 of 3 for wall time. Descriptive only.

## What is healthy

- **The instrumentation works.** Sterile execution, model pinning with readback,
  context auditing, hidden functional acceptance, out-of-band architecture
  scoring, the artifact firewall and the frozen analysis all ran end to end.
- **The governance works, including against us.** Two real defects were caught,
  recorded in full and repaired rather than smoothed over: a run-id collision that
  destroyed a paid-for record, and a pre-frozen decision rule that returned an
  unwelcome answer and was honoured anyway.
- **Pre-registration held.** The efficiency pilot's endpoints, thresholds and
  decision rule were frozen before any observation and were not adjusted
  afterwards.

## What is blocked

- **No instrument yet discriminates architecture at baseline.** PT08, PT09 and
  PT10 all sit at or near the architecture floor. Without a discriminating
  instrument, the study's central construct cannot be measured.
- **Gate `G1` is not passed; the suite is not frozen.**
- **`TD-B32`** (independent review of evaluator packages) — open.
- **`TD-B34`** (replication depth) — open and blocking.
- **`TD-B03`** (primary model selection) — open; `primary_model: null`.
- **`TD-B19`** (isolation) — open and blocking.
- No power calculation may run (`TD-B37`).

## The open question

Two rival explanations for the repeated null are **not separable** from current
data:

1. **Strong-model ceiling** — `claude-sonnet-5` already knows what the MAD says.
2. **Substrate legibility** — a 49-file synthetic monorepo advertises its own
   architecture.

The next two experiments vary one factor each.

## What happens next

| experiment | status | tests |
| --- | --- | --- |
| `LOWER_MODEL_PILOT` | **NOT STARTED** | the ceiling explanation |
| `OPEN_SOURCE_COMPLEXITY_STUDY` | **NOT STARTED** | the legibility explanation |

The lower-model pilot reuses the entire existing harness and is much the cheaper
of the two, so it should run first. See
[`05_NEXT_STUDY_PLAN.md`](05_NEXT_STUDY_PLAN.md).

## What this package will not tell you

There are no p-values, confidence intervals, effect sizes or power estimates
anywhere in this programme, by design — a 3-repetition pilot supports none of
them. Every reported ratio is a median of paired ratios, and it is descriptive.
