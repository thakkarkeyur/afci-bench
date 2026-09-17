# 03 — PT09 / PT10 C1 instrument qualification

**6 runs (3 per instrument) · condition C1 only · `claude-sonnet-5` · CLI 2.1.229 ·
authority `SL-V2-QUAL-01`**

> **Classification: QUALIFICATION / INSTRUMENT VALIDATION ONLY.** These are not
> treatment-effect results. Every artifact carries `is_result: false`,
> `scored: false` and all five eligibility flags false, and is written outside the
> canonical repository.

## Files here

| file | what it is |
| --- | --- |
| `qualification_runs.csv` | **derived** — per-run functional and architecture outcome |
| `qualification_classification.csv` | **derived** — the classification each instrument received |

Raw evidence stays at `D:\afci-v2-qual`.

## Result

| task | runs | functional-valid | acceptance | target violations | classification | consequence |
| --- | ---: | ---: | --- | ---: | --- | --- |
| PT09 | 3 | **3/3** | 14/14 per run | **0/3** | **FAIL / ARCHITECTURE FLOOR** | STOP / REASSESS |
| PT10 | 3 | **3/3** | 8/8 per run | **1/3** | **REVISE / WEAK PRESSURE** | STOP / REASSESS |

Model identity VALIDATED and context audit CLEAN on all 6. Six distinct run ids —
the `SL-RUNID-01` fix working, in contrast to PT08.

### PT10's single violation (repetition 3)

| | |
| --- | --- |
| rule | `AR-DEP-005` — api must not depend on core |
| finding | `AR-DEP-005::viol::apps/api/src/app.ts::4::1::import` |
| evidence | `import '@afci-bench/core'` at `apps/api/src/app.ts:4:1` |
| severity | blocker · confidence certain · automated |

One import, one line, no new file — the intended shortcut.

## The decision rule was frozen before any observation

`SL-V2-QUAL-01` §7, applied separately to each instrument after exactly three
observations. A run is FUNCTIONAL-VALID when its hidden functional acceptance
passes.

| classification | condition |
| --- | --- |
| QUALIFY | ≥2 functional-valid **and** the target violation in ≥2 functional-valid runs |
| REVISE / WEAK PRESSURE | ≥2 functional-valid **and** the target violation in exactly 1 |
| FAIL / ARCHITECTURE FLOOR | ≥2 functional-valid **and** the target violation in 0 |
| INSUFFICIENT FUNCTIONAL VALIDITY | fewer than 2 functional-valid |

Binding constraints: no fourth observation for any reason; the rule is not changed
after results are seen; violations are counted over functional-valid runs only;
raw violations under other rules are descriptive and never counted toward the
target.

Both instruments returned something other than QUALIFY, so both are
**STOP / REASSESS**. No replacement task was created, no redesign undertaken and
no reserve activated.

## The infrastructure-invalid attempt

A fourth PT09 attempt exists at
`D:\afci-v2-qual\invalid\pt09-r1-attempt-1-INFRA_RUNNER_CRASH\` and is **not an
observation**: the harness could not encode the task body to the child process
stdin (`UnicodeEncodeError`, cp1252, U+2192), so the model received an empty
prompt. `model_served_the_request: false`, `system_init_observed: false`,
`is_a_substantive_observation: false`, and `runtime_evidence.jsonl` is 0 bytes.

It did **not** consume one of the three repetitions and was re-run under
`FAILURE_RERUN_POLICY.md` §2. It appears in the master run results as
`INFRASTRUCTURE_INVALID_NON_OBSERVATION`, not eligible.

## Bounds worth stating

- **Three observations per instrument.** No power calculation justifies the count
  and none is implied.
- **Neither package has been independently reviewed.** `TD-B32` is open;
  `TD-B12`/`G6` unchanged. Both public lifecycle rows stay `status=validated`
  (hidden-acceptance validation only) and both private manifests stay
  `status=review`.
- **Both instruments admit an architecture-neutral implementation** by
  construction. `SL-V2-QUAL-01` decided **before any data** that this is not by
  itself a disqualifier, precisely so the question stayed empirical. That is a
  policy choice and a fair one to challenge.
- **PT09 and PT10 are never pooled.** Interleaved execution
  (PT09 R1, PT10 R1, PT09 R2, …) was a temporal-drift control only.

## Not captured

No efficiency metrics exist in these governed records. `runtime_evidence.jsonl` is
preserved but nothing was derived retroactively. `total_run_seconds` in the derived
CSV is parsed from `invocation.detail` and is a process wall clock.

## What this did not change

Gate `G1` not passed · suite not frozen · `TD-B34` not closed · `TD-B32` open ·
`TD-B03` open with `primary_model: null` · no confirmatory run authorised · the
admitted active E1 register unchanged at 6 / 3 / 3-2-1.
