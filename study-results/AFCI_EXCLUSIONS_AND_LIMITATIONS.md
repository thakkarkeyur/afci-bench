# AFCI-Bench — exclusions and limitations

Everything here weakens, bounds or disqualifies some piece of evidence. Nothing
unfavourable is omitted. Where a limitation was discovered the expensive way, that
is said plainly.

---

## 0. The one-line version

Of 121 recorded run/attempt rows, **50 are eligible for any analysis at all**, all
50 belong to two non-confirmatory pilots, and **0 are confirmatory**.

| experiment | rows | eligible | why not |
| --- | ---: | ---: | --- |
| `V1_ORIGINAL` | 48 | 0 | historical/exploratory; L1–L7 |
| `V2_PT08_DIAGNOSTIC` | 3 | 0 | diagnostic only |
| `V2_PT09_QUALIFICATION` | 4 | 0 | qualification only (+1 infra-invalid) |
| `V2_PT10_QUALIFICATION` | 3 | 0 | qualification only |
| `V2_EFF_ATTEMPT1` | 9 | 0 | attempt aborted wholesale |
| `V2_EFF_ATTEMPT2` | 36 | 34 | eligible, but **non-confirmatory** |
| `V2_LOWER_MODEL_PILOT` | 18 | 16 | eligible, but **non-confirmatory**; 1 functionally invalid, 1 stranded partner |

---

## 1. V1 methodological limitations

Recorded verbatim in `archive/v1/REFERENCE_MANIFEST.yml`. These describe the v1
**design as executed**; they are not allegations about artifact integrity, and no
v1 artifact was altered.

| id | limitation | consequence |
| --- | --- | --- |
| **L1** | The harness captured `patch.diff` as `git diff paper-v0` over the whole working tree and **never reset the tree between tasks**, so edits accumulate monotonically across T01→T12. | Runs are **non-independent**. The churn trend across task index is confounded with accumulation. This is the single most serious v1 limitation. |
| **L2** | `run_one_v1.sh` **does not invoke a model**; it snapshots the working tree. | Generation and diff capture are not coupled; the generation step is not reproducible from the harness. |
| **L3** | AFCI-Guard matches literal `libs/core` import paths, but the codebase uses `@afci-bench/*` aliases, so **the guard regexes never fire**. The guard has no tests. | `conformance_summary_v1.csv` is all zeros. **Those zeros are not measurements.** In this package the v1 architecture columns are left **blank**, never 0. |
| **L4** | `docs/ARCH_RULES.yml` is **0 bytes** on `main`. | The documented machine-checkable architecture rules did not exist. |
| **L5** | `layer_jaccard` evaluates to a constant **1.0** (self-comparison; `expected_layers=None`) yet was reported as a metric. | Architecture **self-comparison weakness**: the metric cannot vary, so it measures nothing. |
| **L6** | Primary metrics are churn/drift proxies. There is **no per-task acceptance oracle** beyond `npm run ci`, and `ci_pass` is saturated `True` across all 48 cells. | The success gate **does not discriminate**. v1 has no validated hidden task-acceptance oracle. |
| **L7** | `package-lock.json` on the v1 base is out of sync with `package.json`; `npm ci` fails on the clean base. | Deterministic install is broken at `paper-v0` (fixed only at `paper-v0-runner`). |

**Additionally — baseline architecture leakage.** The v1 baseline arm ran against
a repository whose architecture was visible in the tree, so "no architecture
context" was not architecture-free. v2 addresses this with an allowlisted
model-visible worktree that excludes `docs/`, `experiments/`, `paper/`, `archive/`
and the architecture-enforcing `.eslintrc.json`.

> **Therefore: v1 results are historical / exploratory evidence, not confirmatory
> v2 evidence.** No v1 number may be pooled with, or contrasted against, a v2
> number.

---

## 2. PT08 — diagnostic-only status

`PT08_DIFFICULTY_DIAGNOSTIC` carries a run-purpose firewall enforced by
`run_record.schema.json`: `confirmatory_eligible`, `enters_confirmatory_dataset`,
`enters_confirmatory_e1_analysis`, `enters_treatment_effect_analysis` and
`enters_power_estimation` are **all false**, plus `is_result: false` and
`scored: false`. An artifact that dropped the firewall could not validate.

- Its observations are **exploratory observations about an instrument**, never an
  outcome value for PT08 and never evidence about any experimental condition.
- They **must never** be retrospectively promoted to confirmatory status,
  re-labelled as a result, or entered into any numerator, denominator, dataset or
  power estimate.
- `PT08 = REVISE` is **not** `INVALID` and **not** `RETIRED`. PT08 is functionally
  valid; it is unsuitable **unchanged** as a confirmatory
  architecture-discrimination instrument.
- Two registers are deliberately kept apart: the admitted active E1 register is
  **unchanged** at 6 opportunities / 3 clusters / depths 3-2-1, while the
  **confirmatory-candidate set excludes unchanged PT08**. Neither may be read off
  the other.

**Defect exposed.** `run_artifacts.derive_run_id` hashed only content identity, so
all three repetitions minted the **same run id**. They stayed separable only
because each got its own `--artifact-root`. Fixed under `SL-RUNID-01`; the PT08
artifacts keep the ids they were written with and are **not** rewritten.

---

## 3. PT09 / PT10 — qualification-only status

Run purpose `INSTRUMENT_QUALIFICATION_DIAGNOSTIC`, authority `SL-V2-QUAL-01`, same
five-flag firewall plus `is_result: false`, `scored: false`. Artifacts are written
to a scratch root **outside the canonical repository**; the runner refuses
`experiments/v2/results/`, `experiments/v2/analysis/` and anywhere inside the
repository at all.

- **Not treatment-effect results.** The decision explicitly does not authorise
  `C2`, `C3` or `C4`, any condition contrast, any `C1`-versus-`C4` comparison, any
  effect size, any confidence interval or any power calculation.
- **Three observations per instrument.** No power calculation justifies the count
  and none is implied. No fourth observation may be added, for any reason.
- **The rule was frozen before the first observation** and was not changed after
  results were seen. Violation counts are taken over functional-valid observations
  only; raw violations under other rules are descriptive and never counted toward
  the target.
- **PT09 and PT10 are never pooled.** Interleaved execution was an order control
  only.
- The two instruments were **staged and unreviewed** at execution time; neither
  package has been independently reviewed (`TD-B32` open, `TD-B12`/`G6`
  unchanged).
- **A known escape hatch exists by construction.** Both admit a functionally valid
  architecture-neutral implementation. `SL-V2-QUAL-01` decided **before any data**
  that this is not by itself a disqualifier — precisely so the question stayed
  empirical. That decision is a policy choice, and it is fair to challenge it.

**One infrastructure-invalid attempt.** PT09 R1 attempt 1 failed with
`INFRA_RUNNER_CRASH`: the harness could not encode the task body to the child
process stdin (`UnicodeEncodeError`, cp1252, U+2192), so the model received an
empty prompt. `model_served_the_request: false`,
`is_a_substantive_observation: false`. It did **not** consume one of the three
repetitions and was re-run under `FAILURE_RERUN_POLICY.md` §2.

---

## 4. Efficiency Attempt 1 — excluded wholesale

> **No observation from execution attempt 1 may enter any efficiency analysis,
> under any circumstance, in whole or in part.**

**Root cause.** `derive_run_id` omitted the reset state from the identity seed. The
pilot crosses every cell with `NON_RESET` and `RESET`, so 36 scheduled rows
collapsed to **18 run ids = 18 collision pairs**, one artifact directory per pair.

**What the collision destroyed.** Sequence 6 completed and wrote its governed
record. Sequence 9 derived the same directory, overwrote the readiness, prompt,
prepared-manifest, context-audit and launch artifacts, deleted and rebuilt the
prepared worktree, **ran the model to completion**, then refused at
`CAPTURE_WORKTREE` with `PREPARED_WORKTREE_DIRTY` — and the refusal handler wrote
its refusal record over sequence 6's completed `run_record.json`. The failure was
caught by the last control that could have caught it, after the money was spent,
and the detection itself destroyed a record.

**The counts.**

| | |
| --- | ---: |
| scheduled | 36 |
| attempted | 9 |
| never started | 27 |
| intact governed observations | 7 (sequences 1–5, 7, 8) |
| damaged | 2 (sequences 6, 9) |

**Why the 7 intact rows are excluded too** — the tempting move is to keep them and
run 29 more. It is refused for three reasons:

1. **They are not a random seven.** They survived because their collision partners
   happened to be scheduled later. That is a selection mechanism nobody designed
   and nobody can adjust for.
2. **Pooling would break the pairing.** The analysis is paired within each of 18
   blocks; pooling would mix blocks measured in different sessions, which is the
   drift within-block randomisation exists to prevent.
3. **A restart that keeps the convenient rows is not a restart.** It is selective
   replacement, and after the fact it is indistinguishable from replacing rows
   because of what they showed — even though here nobody looked.

**No analysis preceded the abort.** No `TOKEN_RATIO` analysis, no C1-vs-C4
comparison for any task/arm/repetition, no pilot outcome, no continuation-threshold
evaluation. The abort rests on the 18 collisions alone, which is fully established
without reading a single measured quantity.

**Evidence preserved exactly as found** — nothing deleted, rewritten, normalised,
repaired, renamed or re-derived; no missing artifact reconstructed. Sequence 6's
surviving phase evidence **must not** be used to rebuild a governed record: a
record assembled from the evidence it is supposed to attest cannot attest it. The
row is recorded as damaged and left damaged.

**Enforced, not merely stated.** `assert_single_execution_attempt` refuses a
record set spanning attempts and refuses any Attempt-1 record even on its own.
Attempt-1 records are recognised by their silence — they declare no execution
attempt because they were written before the repair.

---

## 5. Attempt-2 sequence 12 — the refused observation

`PT01 / C4 / RESET / R1`, run id `…pt01-c4-real-r1-reset-a2-2c255aab1046`.

Recorded facts: `PRECHECK`, `PREPARE_WORKTREE`, `CONTEXT_AUDIT` and
`BUILD_FRESH_LAUNCH` all passed; `MODEL_INVOCATION` returned **REFUSED** with
`MODEL_PROCESS_FAILED` — "the model process exceeded 1800s and was stopped
(`CTRL_BREAK_PROCESS_GROUP`); the repetition is invalid rather than partial". The
operator log shows the sequence starting 2026-09-16T14:49:26Z and ending
18:47:55Z, a wall clock of **14 308.7 s (≈ 3 h 58 m)** against an 1 800 s ceiling,
and execution halted there until it was resumed at sequence 13 at 18:51:14Z.

**What is recorded is the timeout and the termination.** A stalled provider stream
combined with a host sleep over that window is the operational reading, and the
~4-hour wall clock against a 30-minute ceiling is consistent with it — but the
artifacts record the timeout, not its cause, and this package does not assert one.

**Consequences:** no usage, no output tokens, no cost and no functional verdict
exist for this row; `functional_status: MISSING`; its block `PT01|RESET|R1` is not
paired-eligible, which also strands its otherwise-valid C1 partner (sequence 11).

---

## 6. Attempt-2 PT04 checkpoint-not-reached

`PT04 / C1 / RESET / R1`, sequence 15, run id `…pt04-c1-real-r1-reset-a2-62382ec94faa`.

The run completed (`outcome.status = COMPLETE`) but its efficiency status is
`RESET_CHECKPOINT_NOT_REACHED`: the governed checkpoint predicate
(`CK-EFF-FALLBACK-CI-AGENT-AFTER-EDIT` — the first agent-initiated
`npm run ci:agent` after at least one implementation edit) was never satisfied, so
the reset the row exists to carry never happened at the governed point.
`functional_valid: false`.

Its block `PT04|RESET|R1` is therefore not paired-eligible, stranding its
otherwise-valid C4 partner (sequence 16).

**Net effect of §5 and §6 together:** 34 runs are individually functionally valid,
but only **32** enter the **16** paired blocks. Two valid runs are unpaired and
unused.

---

## 7. Architecture was not produced by the efficiency pilot

`AFCI_EFFICIENCY_PILOT` is a **cost-only** purpose under its own frozen
governance. The frozen analysis states this in place of an architecture result:

> "Not produced by `AFCI_EFFICIENCY_PILOT` under its frozen cost-only governance.
> Existing pre-data legal/violating architecture validation was used only for
> eligibility. No live-run architecture treatment inference is made."

`thresholds_depending_on_architecture` is empty, so no continuation threshold
moved. **No architecture claim may be derived from Attempt 2**, and the
architecture columns for its 36 rows in the master run results are blank — not
zero.

Note the asymmetry this creates: the study's *actual* construct (architectural
conformance) has been measured only by three instruments that all sat at or near
the floor, while its *secondary* construct (cost) has one clean pilot. The
evidence base is lopsided, and the cost result should not be allowed to stand in
for an architecture result.

---

## 8. Cost availability limitation for reset runs

A RESET run executes in two phases; phase A is deliberately interrupted at the
checkpoint, **before its terminal result event**. The result event is the only
place the runtime reports output tokens and cost.

Consequently, for a reset run:

- **`TOTAL_INPUT_TOKENS` is exact** — reconstructed from the streamed assistant
  messages (`source: per_message_partial`), e.g. "input reconstructed exactly from
  11 streamed assistant message(s)".
- **`TOTAL_OUTPUT_TOKENS` and `cost_usd` are `null`** — **withheld, not zero, and
  not estimated.**

So:

- `TOTAL_OUTPUT_TOKENS` has **n = 9** paired blocks (NON_RESET only), against 16
  for the primary endpoint.
- Provider cost has **n = 9** and is reported as **NON_RESET only**. There is **no
  RESET cost comparison at all**, so the 1.4928 figure describes the non-reset arm
  and must not be read as a whole-pilot cost ratio.
- 17 of 36 run rows carry no provider cost.

---

## 8A. Lower-model pilot — what is excluded and what is bounded

**One run is functionally invalid and one valid run is unused.**

| | |
| --- | --- |
| executed | 18 of 18 |
| refused | 0 |
| infrastructure-invalid attempts | 0 |
| functionally valid | 17 (C1 8/9, C4 9/9) |
| paired-eligible blocks | 8 of 9 |
| runs in the paired efficiency analysis | 16 |
| valid but unpaired | 1 |

`PT04/C1/R2` failed all four of its semantic acceptance cases. Under the frozen
`FUNCTIONAL_VALID` definition it is invalid, so block `PT04|R2` cannot be paired
and its **valid** C4 partner is excluded from every efficiency ratio. The C4 run is
not deleted and not counted as a failure — it is a complete observation with no
comparator.

**It was not replaced.** The frozen observation policy consumes a substantive
observation once the real task is delivered, and explicitly forbids replacing one
because it failed functionality. Only a pre-observation infrastructure-invalid
attempt may be re-run, and none occurred.

**Architecture is reported over all 18 runs, efficiency over the 8 paired blocks.**
A run that violated the architecture is still a run that violated it, so the
architecture channel is not restricted to functionally-valid pairs; the
functionally-valid subset is reported alongside so a reader can see both. A cost
figure from a run that did not work is not a cheaper way of doing the task, so the
efficiency channel *is* restricted.

**The architecture endpoint is descriptive.** It enters no `E1` numerator or
denominator, no treatment-effect estimate and no power estimate. It exists under a
pilot-scoped corpus exemption (`SL-V2-LOWER-MODEL-01` §9) which is **not** a full
architecture mutation corpus and must never be described as one. The full corpus
requirement is unchanged and required in full for every confirmatory purpose.

**The quality channel produced no discriminating information.** Both arms recorded
0 target violations across 9 runs each. See §11.

**No private identifiers are published.** Opportunity ids, rule ids, forbidden
scopes and hidden acceptance case semantics stay in the private evaluator
repository; the run record refuses to carry them at all. No numeric result is
withheld.

---

## 9. No p-values, confidence intervals or confirmatory effect estimates

The frozen analysis asserts `no_p_values`, `no_confidence_intervals` and
`no_effect_estimate` on the face of every report, and
`efficiency_claim_made: false`.

- 16 paired blocks, 3 repetitions, 3 tasks. Nothing supports inference.
- No power calculation has ever been run (`TD-B37`), and none is implied by any
  repetition count anywhere in this programme.
- Every reported ratio is a **median of paired ratios**, a descriptive statistic.
- `confirmatory: false` and `is_result: false` on the report itself.

---

## 10. Synthetic-substrate architecture-legibility limitation

Every v2 run to date used one governed substrate: commit `630d3180`, content hash
`0198d76c…`, **49 files**. It is a synthetic Nx monorepo whose layering is
inferable from its own import graph and path aliases.

- A model can often deduce the intended architecture **without** the MAD, which
  directly attacks the MAD's marginal value — the thing the study measures.
- The architecture-enforcing `.eslintrc.json` is excluded from the model-visible
  worktree, but the **structure itself** still signals the architecture.
- Six instrument/model combinations have now sat at or near the architecture
  floor on this substrate: PT08, PT09 and PT10 for an unguided Sonnet baseline,
  and PT01, PT04 and PT07 for Haiku 4.5 in **both** arms. That is as readily
  explained by the substrate as by the tasks.

**This is the primary external-validity threat to every v2 finding, and after the
lower-model pilot it is the leading one** — see §11, where the rival explanation
was tested and not supported.

---

## 11. Ceiling effects, and the one test that has been run

Every Sonnet-era v2 run used `claude-sonnet-5`.

- Functional acceptance was **saturated**: PT08 3/3, PT09 3/3, PT10 3/3, efficiency
  17/18 and 17/18. A saturated outcome cannot show improvement.
- Baseline architecture violations were at or near **zero**, so a treatment that
  reduces violations has no room to act.
- PT08's disposition names this directly: a baseline at the floor has no room
  beneath it.

**The strong-model ceiling explanation has now been tested, and was not
supported.** The lower-model pilot re-ran PT01/PT04/PT07 on
`claude-haiku-4-5-20251001`. A weaker model did **not** escape the architecture
floor — both arms violated the target in 0 of 9 runs — and C4's cost ratio got
*worse*, not better (2.0372 against Sonnet's 1.5582 on non-reset input tokens).

Three limitations bound that test, and none may be dropped when citing it:

1. **The quality channel was uninformative, not negative.** Both arms sat at zero.
   A tie at the floor cannot distinguish "the MAD does not help" from "the
   instrument cannot see help". The frozen rule records FAIL because it demands
   *strictly fewer* violations; that is a rule outcome, not a finding about AFCI.
2. **It is not a randomised cross-model experiment.** Sonnet and Haiku were run
   under separate purposes, separate schedules and separate analyses, and are
   **never pooled**. The comparison is two within-model ratios shown side by side.
   No interaction was estimated and none may be quoted.
3. **One lower-capability model, one substrate, 8 paired blocks, 3 repetitions.**
   Descriptive medians only.

Substrate legibility (§10) remains **untested** and is now the leading explanation
by elimination rather than by evidence.

**`TD-B03` is open and `primary_model` is `null`** — no model has been selected
for the study, so both models used so far are provisional.

---

## 12. Open governance state

Nothing in this package changes any of the following, and all remain open:

| item | state |
| --- | --- |
| suite-wide protocol | **PRE-FREEZE** |
| gate `G1` | not passed |
| `TD-B32` (independent review) | open |
| `TD-B34` (replication depth) | open and blocking |
| `TD-B03` (primary model selection) | open; `primary_model: null` |
| `TD-B19` (isolation) | open and blocking |
| `TD-B12` / `G6` | unchanged |
| `TD-B37` (power simulation) | no power simulation may run |
| reserves `PR01` / `PR02` | inactive; `PR02` blocked under `TD-B26` |
| confirmatory evidence collection | **not begun** |

---

## 13. Limitations of this package itself

1. **It is a secondary artifact.** Where it and a primary artifact disagree, the
   primary artifact wins.
2. **The Attempt-2 analysis was re-executed on 2026-09-17** using the repository's
   frozen analysis over the existing records. The code and the records are
   unchanged; only the report is new.
3. **The analysis is sensitive to what it is handed.** Pointing it at the
   `attempt-2` root instead of the 36 observation directories pulls in 12 dry-run
   readiness records that share R1 coordinates and corrupts block pairing — it then
   reports 12 eligible blocks and a 1.3895 median instead of 16 and 1.4014. The
   correct invocation is documented in the package README.
4. **`total_run_seconds` for PT08/PT09/PT10 is parsed from the free-text
   `invocation.detail`** and is a process wall clock, not the governed
   `MODEL_WALL_SECONDS` endpoint, which those purposes never captured. Those rows'
   `model_wall_seconds` is deliberately blank.
5. **v1 `lines_added` / `lines_removed` are mapped**, not native: `lines_added =
   code_additions + test_additions`, `lines_removed = code_deletions +
   test_deletions`, `net_lines = delta_loc_code + delta_loc_test`.
6. **The `notes` column** was added to the master run results beyond the requested
   schema, to carry per-row provenance that would otherwise be lost.
7. **No v1 run-level token, time or cost metric exists.** v1 predates efficiency
   instrumentation entirely; those cells are blank and were **not** estimated.
