# AFCI-Bench — project status

**As at 2026-09-18.** Repository `afci-bench`, branch `study-v2`.

---

## Where the project stands

The v1 study is published. The v2 study is **built and working but pre-freeze**:
the harness, oracles and governance all execute end to end, and **no confirmatory
evidence has been collected**. Seven experiments have run. Two of them — the
efficiency pilot and the lower-model pilot — reached a pre-registered decision,
and both decisions were **negative**.

## What has been run

| # | experiment | runs | class | outcome |
| --- | --- | ---: | --- | --- |
| 1 | v1 original study | 48 | exploratory | published (ASE 2026 artifact, Zenodo DOI) |
| 2 | PT08 C1 difficulty diagnostic | 3 | diagnostic | PT08 = REVISE; benchmark = CONTINUE |
| 3 | PT09 C1 qualification | 3 (+1 invalid) | qualification | FAIL / ARCHITECTURE FLOOR → STOP |
| 4 | PT10 C1 qualification | 3 | qualification | REVISE / WEAK PRESSURE → STOP |
| 5 | efficiency pilot, attempt 1 | 9 of 36 | aborted | infrastructure defect; excluded wholesale |
| 6 | efficiency pilot, attempt 2 | 36 of 36 | cost pilot | **STOP — no efficiency signal** |
| 7 | lower-model pilot (Haiku 4.5) | 18 of 18 | quality + cost pilot | **NO SIGNAL — do not expand** |

**121 run/attempt rows recorded. 50 eligible for any analysis. 0 confirmatory.**

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

## The second headline result — the lower model did not rescue AFCI

The obvious rival explanation for the null above was a **strong-model ceiling**:
`claude-sonnet-5` may already know what the architecture document says. The
lower-model pilot tested that by re-running the same three tasks on
`claude-haiku-4-5-20251001`, non-reset only, 18 runs, with the endpoints and the
continuation rule frozen before any data existed.

The ceiling explanation was **not supported**. C4 was not cheaper on the weaker
model; it was *more* expensive than it had been on the stronger one.

| C4 / C1, non-reset | Sonnet | Haiku 4.5 |
| --- | ---: | ---: |
| input tokens | 1.5582 | **2.0372** |
| wall time | — | 1.5268 |
| exploration calls | — | 1.7308 |
| tool calls | — | 1.5023 |
| provider cost | — | 1.8865 |
| functional validity | 17/18 vs 17/18 | C1 8/9, C4 **9/9** |

The two models are **never pooled**; these are two within-model ratios shown side
by side, and the Sonnet column carries only the endpoint its cost-only governance
produced.

On quality, the pilot hit the same wall as PT08/PT09: **one applicable
architecture opportunity per run, zero violated in both arms**. C4 could not beat
C1 because neither arm ever violated anything. That is an instrument floor, not
evidence that the document does nothing.

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

Two rival explanations for the repeated null were **not separable** from the
Sonnet data alone:

1. **Strong-model ceiling** — `claude-sonnet-5` already knows what the MAD says.
2. **Substrate legibility** — a 49-file synthetic monorepo advertises its own
   architecture.

Explanation 1 has now been **tested and not supported**: weakening the model made
C4 relatively *more* expensive, not less, and produced no quality gain. That
shifts weight onto explanation 2, which remains untested. It does not prove it —
the architecture floor means this pilot could not have detected a quality gain
even had one existed, so the honest reading is that the ceiling story lost
support rather than that legibility won.

## What happens next

| experiment | status | tests |
| --- | --- | --- |
| `LOWER_MODEL_PILOT` | **COMPLETE — no signal** | the ceiling explanation (not supported) |
| `OPEN_SOURCE_COMPLEXITY_STUDY` | **NOT STARTED** | the legibility explanation |

The open-source complexity study remains scientifically motivated and is now the
single most informative next experiment, because it is the only one of the two
rival explanations still standing. It is **not** authorised by the lower-model
result and has not been started. See
[`05_NEXT_STUDY_PLAN.md`](05_NEXT_STUDY_PLAN.md).

A third question the lower-model pilot raised on its own: three of three
instruments now sit at the architecture floor under both arms. Instrument
discrimination, not model capability, is the binding constraint.

## What this package will not tell you

There are no p-values, confidence intervals, effect sizes or power estimates
anywhere in this programme, by design — a 3-repetition pilot supports none of
them. Every reported ratio is a median of paired ratios, and it is descriptive.
