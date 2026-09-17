# AFCI-Bench — results summary

**Compiled 2026-09-18** from `study-v2`.
Every figure below was recomputed from raw evidence; see
[`AFCI_EVIDENCE_INDEX.md`](AFCI_EVIDENCE_INDEX.md) for the trace.

Throughout, claims are tagged:

- **[FACT]** — a measured value, reproducible from the artifacts.
- **[INTERPRETATION]** — a reading of those facts.
- **[LIMITATION]** — a bound on what the facts can support.

---

## 1. Executive summary

Seven experiments have been executed: one v1 study (48 runs) and six v2 experiment
sets (73 attempted runs). **None of them is confirmatory.** The v2 programme has
so far produced instrument-validation evidence, one completed cost pilot and one
completed lower-model pilot; both pilots' pre-registered decision rules returned a
negative verdict.

The single most consequential result to date:

> **[FACT]** On the clean synthetic substrate, with `claude-sonnet-5`, giving the
> model an explicit Machine-readable Architecture Document (condition **C4**)
> did **not** make it cheaper than giving it the task alone (condition **C1**).
> Median C4/C1 input-token ratio **1.4014** over 16 paired blocks; C4 was cheaper
> in only **4 of 16** pairs. Wall time, exploration, tool calls, edit/write effort
> and provider cost all moved the same way. Functional quality was essentially
> equal: **17/18** functionally valid runs in each condition.

> **[FACT]** One signal ran the other way. Under context reset, C4's *recovery
> overhead* was lower than C1's in **2 of 3** tasks for tokens and **3 of 3**
> tasks for wall time.

**[INTERPRETATION]** Explicit architecture context is not a general efficiency
win for a strong model on an architecturally legible codebase. It is a cost. The
reset-recovery signal is the one place the mechanism the study is about — cheaper
re-establishment of architectural intent — appears to show up, and it is
descriptive only.

> **[FACT]** The lower-model pilot then tested the most obvious explanation for
> that null — that a strong model already knows what the MAD says — by re-running
> the same three tasks on `claude-haiku-4-5-20251001` (18 runs, non-reset, 8
> paired blocks). The weaker model made C4 **relatively more** expensive, not
> less: median C4/C1 input tokens **2.0372** against Sonnet's non-reset
> **1.5582**. Functionally C4 was the better arm (**9/9** vs **8/9**). On
> architecture, **both** arms violated the target in **0 of 9** runs.

**[INTERPRETATION]** Explicit architecture context was not a general efficiency
win on either model, and weakening the model did not rescue it. The
**strong-model ceiling** explanation is therefore **not supported**. The rival
**substrate legibility** explanation (a 49-file synthetic monorepo whose
architecture is inferable from the code) remains untested and is now the primary
open explanation.

**[LIMITATION]** The lower-model pilot's architecture channel answered nothing:
both arms sat at zero violations, so it could not have detected a quality effect
even had one existed. A tie at the floor is **not** evidence that the MAD fails to
improve architecture. The two pilots are two separate experiments on two separate
models and are **never pooled**; no cross-model causal effect is estimated.

---

## 2. Study timeline

| when | what | outcome |
| --- | --- | --- |
| 2026-04-20 → 04-23 | v1 execution, 48 runs, "Opus 7" | published; ASE 2026 artifact; Zenodo DOI `10.5281/zenodo.19757261` |
| 2026-04-25 | v1 artifact package released | tag `ase2026-artifacts-v1` |
| 2026-07-18 | reproducibility review of v1 | v1 limitations L1–L7 recorded; v2 designed to remedy them |
| 2026-09-13 | PT08 C1 difficulty diagnostic, 3 runs | PT08 = REVISE; benchmark = CONTINUE |
| 2026-09-14 | efficiency pilot design frozen (36 runs) | pre-registered endpoints and decision rule |
| ~2026-09-15 | PT09/PT10 qualification, 6 runs | both STOP / REASSESS |
| 2026-09-16 (early) | efficiency pilot Attempt 1 | ABORTED at sequence 9 — run-id collision |
| 2026-09-16 14:28–20:02 UTC | efficiency pilot Attempt 2, 36 runs | STOP — no efficiency signal |
| 2026-09-17 (early) | lower-model pilot design frozen (18 runs) | pre-registered endpoints, two independent channels, continuation rule |
| 2026-09-17 21:08–21:52 UTC | lower-model pilot, 18 runs, `claude-haiku-4-5-20251001` | NO SIGNAL — do not expand |
| 2026-09-18 | this evidence package | reporting only |

---

## 3. V1 original findings

**Design.** 12 tasks × {baseline, AFCI} × {non-reset, reset} = **48 runs**, one
run per cell, model labelled "Opus 7", base tag `paper-v0`.

### 3.1 What was measured [FACT]

| metric | baseline | AFCI | change | per-task |
| --- | ---: | ---: | ---: | --- |
| non-reset code churn (mean) | 576.58 | 955.42 | **+65.7%** | AFCI higher in **12/12** |
| non-reset test churn (mean) | 172.67 | 244.00 | **+41.3%** | AFCI higher in **12/12** |
| reset true drift, ΔCodeLOC (mean) | 307.7 | 670.5 | **+117.9%** | AFCI **lower** in **1/12** |
| CI pass | 100% | 100% | — | 48/48 |

All four recompute exactly from `results_v1.csv` and `drift_true_v1_codeonly.csv`.
Code churn = `code_additions + code_deletions`; test churn is the test-file
equivalent; true reset drift is
`|CodeChurn_reset − CodeChurn_nonreset|` per task and condition family.

A separate v1 table reports **condition-level** reset churn — baseline-reset mean
576.6→268.9, AFCI-reset 286.2 — which is a different construct from the ΔCodeLOC
drift figure above. Both are reproduced in
[`01_v1_original_study/`](01_v1_original_study/) so they are not confused.

### 3.2 What this means [INTERPRETATION]

In v1, AFCI **increased** churn on every task and was **more** reset-inconsistent
on 11 of 12. Read at face value this contradicts the hypothesis. It should not be
read at face value, for the reasons in §3.3.

### 3.3 Why v1 is historical, not confirmatory [LIMITATION]

Seven recorded limitations, each of which independently undermines inference:

1. **L1 — non-independent runs.** The harness captured `git diff paper-v0` over
   the whole working tree and never reset it between tasks, so edits accumulate
   monotonically across T01→T12. The rising churn across task index is largely
   this accumulation, not a treatment effect.
2. **L2 — no model invocation.** `run_one_v1.sh` did not invoke a model; it
   snapshotted the tree. Generation and diff capture were never coupled.
3. **L3 — AFCI-Guard non-functional.** The guard matched literal `libs/core`
   import paths while the codebase uses `@afci-bench/*` aliases, so its regexes
   never fired. `conformance_summary_v1.csv` is all zeros and the guard has no
   tests. **These zeros are not measurements.**
4. **L4 — empty architecture rules.** `docs/ARCH_RULES.yml` is 0 bytes on `main`.
5. **L5 — degenerate metric.** `layer_jaccard` is a constant 1.0
   (self-comparison, `expected_layers=None`) yet was reported as a metric.
6. **L6 — indirect metrics only.** There is no per-task acceptance oracle beyond
   `npm run ci`, and `ci_pass` is saturated `True` across all 48 cells, so the
   gate does not discriminate task success at all.
7. **L7 — lockfile desync on the base.** `npm ci` fails on the clean v1 base.

Also relevant: **baseline architecture leakage** — the v1 baseline ran against a
repository whose architecture was visible in the tree, so the "no architecture
context" arm was not architecture-free.

> **v1 is historical / exploratory evidence. It is not confirmatory v2 evidence,
> and no v1 number may be pooled with, or compared against, a v2 number.**

---

## 4. V2 diagnostic and qualification findings

These three experiments measure **instruments**, not treatments. None may enter a
confirmatory dataset, a treatment-effect estimate or a power calculation. Each
carries a run-purpose firewall enforced by the record schema.

### 4.1 PT08 difficulty diagnostic — 3 runs [FACT]

| | value |
| --- | --- |
| functional completion | **3/3** (15/15 hidden acceptance cases per run) |
| architecture opportunities applicable | 1 per run, **3** across the set |
| target violations | **0/3** |
| violation proportion | **0.0** — the architecture floor |

Every repetition enforced the ceiling at the request boundary, so the use-case
scope was never entered and the decision the instrument exists to expose was never
taken.

**Decision (`SL-PT08-07`): PT08 = REVISE. Benchmark investment = CONTINUE.**

**[INTERPRETATION]** PT08 shows a **functional ceiling with an architecture
floor**. `C1` is a baseline, and a baseline at the floor has no room beneath it,
so PT08 unchanged cannot discriminate. This is a task-design finding about one
instrument — the runner, sterile execution, model pinning, hidden acceptance,
the architecture oracle and the artifact firewall all worked end to end.

### 4.2 PT09 / PT10 qualification — 6 runs [FACT]

The classification rule was **frozen before the first observation**
(`SL-V2-QUAL-01` §7) and was not changed afterwards.

| task | functional-valid | target violations | classification | consequence |
| --- | ---: | ---: | --- | --- |
| PT09 | 3/3 | **0/3** | FAIL / ARCHITECTURE FLOOR | STOP / REASSESS |
| PT10 | 3/3 | **1/3** | REVISE / WEAK PRESSURE | STOP / REASSESS |

PT10's single violation (repetition 3) was a violation of its **target
architecture opportunity** (applicable=1, violated=1): one forbidden import, on
one line, in one already-existing file — severity blocker, confidence certain,
automated. The opportunity id, the rule id, the forbidden source and target
scopes and the anchor path are hidden evaluator semantics and are withheld; they
stay in the private evaluator repository. No numeric result is withheld.

A fourth PT09 attempt exists and is **not** an observation: the harness could not
encode the task body to the child process stdin (`UnicodeEncodeError`, cp1252,
U+2192), so the model received an empty prompt and never served the request. It
did not consume one of the three repetitions.

**[INTERPRETATION]** Both replacement instruments also failed to exert reliable
architectural pressure on an unguided baseline. Combined with PT08, this is three
independent instruments at or near the architecture floor on this substrate — which
is evidence about the **substrate**, not only about the tasks.

**[LIMITATION]** Three observations per instrument. No power calculation
justifies that count and none is implied.

---

## 5. V2 Sonnet efficiency pilot findings (Attempt 2)

**Design.** 3 tasks (PT01, PT04, PT07) × {C1 task-only, C4 explicit MAD} ×
{non-reset, reset} × 3 repetitions = **36 runs**, executed
2026-09-16 14:28:58Z → 20:02:54Z, `claude-sonnet-5`, CLI 2.1.229, block-paired
with randomised within-block condition order.

### 5.1 Execution and validity [FACT]

| | value |
| --- | ---: |
| scheduled / executed | 36 / 36 |
| completed | 35 |
| refused | 1 (sequence 12) |
| functionally valid runs | 34 (C1 **17/18**, C4 **17/18**) |
| paired-eligible blocks | **16 of 18** (minimum required: 12) |
| runs entering the paired analysis | 32 |
| valid but unpaired runs | 2 |

The two blocks lost are `PT01|RESET|R1` (its C4 arm was refused) and
`PT04|RESET|R1` (its C1 arm never reached the reset checkpoint). Because pairing
is within-block, each loss removes the block, which is why 34 valid runs yield 16
pairs rather than 17.

### 5.2 Primary endpoint — TOTAL_INPUT_TOKENS [FACT]

| | value |
| --- | ---: |
| **median C4/C1** | **1.4014** |
| C4 cheaper | **4 of 16** pairs (25%) |
| PT01 median | 1.3372 |
| PT04 median | **0.9325** |
| PT07 median | 1.5419 |
| NON_RESET arm median | 1.5582 (n=9) |
| RESET arm median | 1.3776 (n=7) |

PT04 is the only task where C4 was cheaper on median.

### 5.3 Secondary endpoints [FACT]

| endpoint | n | median C4/C1 | C4 lower |
| --- | ---: | ---: | ---: |
| MODEL_WALL_SECONDS | 16 | **1.2660** | 4/16 |
| EXPLORATION_CALLS | 16 | **1.3939** | 3/16 |
| TOTAL_TOOL_CALLS | 16 | **1.1864** | 5/16 |
| UNIQUE_FILES_READ | 16 | **1.2111** | 0/16 |
| EDIT_AND_WRITE_CALLS | 16 | **1.9167** | 0/16 |
| TOTAL_OUTPUT_TOKENS | 9 | **1.4671** | 1/9 |
| CI_COMMAND_RUNS | 16 | 1.0000 | 1/16 |
| TEST_COMMAND_RUNS | 0 | not captured | — |
| provider cost (USD) | 9 | **1.4928** | 2/9 |

Output tokens and provider cost are **NON_RESET only**. A reset run's phase A is
interrupted before its terminal result event, so its output and cost totals are
*withheld rather than understated* — a deliberate choice recorded in the design.

Every endpoint except CI command runs moves against C4. Nothing is close to the
0.85–0.90 thresholds the pre-registered "GO" branches required.

### 5.4 Reset recovery [FACT]

Reset overhead = the run's metric under reset divided by the same task/condition
without reset. Lower overhead is better.

| endpoint | tasks where C4's overhead is lower |
| --- | --- |
| TOTAL_INPUT_TOKENS | **2 of 3** (PT01, PT07) |
| MODEL_WALL_SECONDS | **3 of 3** (PT01, PT04, PT07) |
| EXPLORATION_CALLS | 2 of 3 (PT01, PT07) |
| TOTAL_TOOL_CALLS | 2 of 3 (PT01, PT07) |

### 5.5 The pre-registered decision [FACT]

All 14 clauses are reproduced in
[`05_efficiency_attempt_2_completed/attempt2_decision_clauses.csv`](05_efficiency_attempt_2_completed/attempt2_decision_clauses.csv).
Both functional guardrails and the minimum-pairs gate passed. Every token and
secondary-endpoint threshold failed. The RESET-SPECIFIC GO branch failed only on
its overall token clause — its two reset-overhead clauses passed.

> **Outcome: `STOP — NO EFFICIENCY SIGNAL JUSTIFIES FULL-SUITE EXPANSION`**
> (rule 11.4). `efficiency_claim_made = false`.

### 5.6 What the pilot did not measure [LIMITATION]

`AFCI_EFFICIENCY_PILOT` is a **cost-only** purpose under its own frozen
governance. **No architecture endpoint was produced and none may be inferred from
it.** No continuation threshold depended on architecture, so none moved. LOC
changed was likewise not captured.

---

## 5A. V2 lower-model pilot findings (Haiku 4.5)

Authority `SL-V2-LOWER-MODEL-01`. `claude-haiku-4-5-20251001`, CLI `2.1.229`,
non-reset only, 64 turns, 3 tasks x 2 conditions x 3 repetitions. Quality and
efficiency are two **independent** channels, combined into no single score.

### 5A.1 Execution and validity [FACT]

18 of 18 scheduled runs executed in the committed order. 18 COMPLETE, 0 refused,
**0 infrastructure-invalid attempts**. Model identity VALIDATED and context audit
CLEAN on every run; no run reached the turn ceiling.

17 of 18 runs were functionally valid — C1 **8/9**, C4 **9/9**. The single invalid
run, `PT04/C1/R2`, failed all four semantic acceptance cases and strands its valid
C4 partner, leaving **8 of 9** paired-eligible blocks and 16 runs in the paired
analysis.

### 5A.2 Architecture quality [FACT]

| arm | runs | applicable opportunities | violated | target-violation runs |
| --- | ---: | ---: | ---: | ---: |
| C1 | 9 | 9 | 0 | **0** |
| C4 | 9 | 9 | 0 | **0** |

Identical by task: 3 applicable, 0 violated in both arms for PT01, PT04 and PT07.

**[LIMITATION]** This is an **architecture floor**. C4 did not fail to beat C1 —
neither arm violated anything, so there was nothing to discriminate. The frozen
rule scores it FAIL because it requires *strictly fewer* violations, and a tie at
zero is not an improvement. It is **no information**, not evidence against AFCI.

### 5A.3 Efficiency endpoints [FACT]

8 paired blocks; C4/C1, lower is better for C4.

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

Provider cost is complete for **all 8 pairs**, unlike the Sonnet pilot, because
every non-reset run emits a terminal result event. C1 total $1.3862, C4 total
$2.0068 across the paired blocks; $3.8007 across all 18 runs.

**[FACT]** PT07 is the one task where C4 was directionally cheaper on tokens,
time, output and cost. PT01 was the most expensive for C4 on every endpoint.

**[FACT]** Rework, over the 8 paired blocks: edit calls 54 vs 66, files re-edited
16 vs 20, repeated file reads 16 vs **43**, turns used 229 vs 309, files changed
25 vs 30, net lines +1621 vs +1746. C4 needed **fewer** failed CI cycles (9 vs 13).

### 5A.4 The pre-registered decision [FACT]

| signal | criterion | observed | verdict |
| --- | --- | --- | --- |
| QUALITY | C4 fewer target-violation runs overall | 0 vs 0 | **FAIL** |
| QUALITY | improvement in >= 2 of 3 tasks | 0 of 3 | **FAIL** |
| QUALITY | C4 valid no more than 1 below C1 | 9 vs 8 | PASS |
| EFFICIENCY | C4 valid no more than 1 below C1 | 9 vs 8 | PASS |
| EFFICIENCY | median TOKEN_RATIO < 1.00 | 2.0372 | **FAIL** |
| EFFICIENCY | median EXPLORATION_RATIO <= 0.80 | 1.7308 | **FAIL** |
| EFFICIENCY | median TOTAL_TOOL_RATIO <= 0.85 | 1.5023 | **FAIL** |

> **`NO LOWER-MODEL SIGNAL - DO NOT EXPAND THE SYNTHETIC LOWER-MODEL MATRIX`**

### 5A.5 Descriptive comparison with Sonnet [FACT]

| C4 / C1, **non-reset only** | Sonnet | Haiku 4.5 |
| --- | ---: | ---: |
| median TOTAL_INPUT_TOKENS | 1.5582 (n=9) | **2.0372** (n=8) |
| architecture endpoint | **not produced** (cost-only) | produced, at the floor |

Difference **+0.479**, the lower model showing the *higher* ratio.

**[LIMITATION]** Two separate experiments, never pooled. No test, no interaction
estimate, no pooled model, and **no randomised cross-model causal effect**. The
Sonnet pilot produced no architecture measurement, so only the efficiency channel
is comparable at all.

---

## 6. What we can conclude

1. **[FACT]** On this substrate and this model, explicit MAD injection costs more
   than it saves across every captured cost dimension except CI invocations.
2. **[FACT]** It does so without buying functional quality: 17/18 versus 17/18.
3. **[FACT]** Six instrument/model combinations now sit at or near the
   architecture floor on this substrate: PT08, PT09 and PT10 for an unguided
   Sonnet baseline, and PT01, PT04 and PT07 for Haiku 4.5 in **both** the guided
   and unguided arms.
3a. **[FACT]** Weakening the model did not reduce C4's relative cost; it raised
   it (2.0372 vs 1.5582 on non-reset input tokens), and produced no quality gain
   because both arms sat at zero violations.
4. **[FACT]** The reset-recovery direction is the one consistent counter-signal,
   strongest in wall time (3/3 tasks).
5. **[INTERPRETATION]** The benchmark machinery itself works. Sterile execution,
   model pinning and readback, context auditing, hidden acceptance, the
   architecture oracle, the artifact firewall, run-identity derivation and the
   frozen analysis all executed end to end and caught their own defects — twice,
   in ways that cost real money and were recorded rather than smoothed over.
6. **[INTERPRETATION]** Expanding either pilot, unchanged, is not justified. Both
   frozen rules returned a negative verdict and both were honoured.
7. **[INTERPRETATION]** The **strong-model ceiling** explanation for the repeated
   null is not supported. Instrument discrimination, not model capability, is the
   binding constraint on the programme.

---

## 7. What we cannot conclude

1. **We cannot conclude AFCI does not work.** We can conclude it did not reduce
   cost here. Efficiency is one construct; architectural conformance is the study's
   actual construct, and the cost pilot **did not measure it at all**.
2. **We cannot attach any statistical confidence to anything.** No p-value, no
   confidence interval, no effect size and no power estimate exists in this
   programme. With 16 paired blocks and 3 repetitions, none would be defensible.
3. **We cannot generalise past this substrate.** One synthetic 49-file monorepo
   whose architecture is legible from its own code.
4. **We cannot generalise past `claude-sonnet-5`.** `primary_model` is still
   `null`; no model has been selected for the study.
5. **We cannot use the reset-recovery signal as a finding.** It is descriptive,
   from 3 tasks, and it failed the branch that would have made it a GO.
6. **We cannot say anything about v1's hypothesis test.** L1–L7 make the v1
   comparison uninterpretable as a treatment contrast.
7. **We cannot claim any architecture result from the efficiency pilot.** It
   produced none.
8. **We cannot claim an architecture result from the lower-model pilot either.**
   It produced an endpoint, but at the floor in both arms. A tie at zero
   discriminates nothing and must not be read as AFCI failing to improve
   architecture.
9. **We cannot claim that model capability moderates AFCI's value.** The Sonnet
   and Haiku pilots are separate experiments compared descriptively and never
   pooled. Nothing here is a randomised cross-model causal effect.
10. **We cannot generalise past `claude-sonnet-5` and
    `claude-haiku-4-5-20251001`.** Two models, neither selected as the study
    model; `primary_model` is still `null`.

---

## 8. Why the research direction changed

The chain is short and each link is recorded:

1. **v1 measured the wrong things well enough to notice.** Churn is a proxy;
   the guard did not fire; the oracle did not discriminate; runs were not
   independent. v2 was designed to replace proxies with a hidden functional
   acceptance oracle and an out-of-band architecture oracle.
2. **PT08 showed the instruments, not the theory, were the bottleneck.** A
   baseline at the architecture floor cannot discriminate however good the
   treatment is.
3. **PT09 and PT10 showed it was not specific to PT08.** Two purpose-built
   replacements landed in the same place.
4. **The efficiency pilot asked a cheaper question that could be answered now** —
   does the MAD at least pay for itself? — and answered **no**, decisively, under
   a rule frozen before the data existed.
5. **The lower-model pilot weakened the model, and the null held.** Under a
   rule frozen before the data, a weaker model produced no quality signal (both
   arms at the floor) and a *worse* cost ratio than the stronger one.
6. **[INTERPRETATION]** The common factor across 2–5 is not model strength — that
   has now been varied and did not matter. What remains is that **a legible
   synthetic repository gives an agent little to gain from being told its
   architecture**, whether the agent is strong or weak. That points at one
   remaining change: harden the substrate.

---

## 9. Next experiments

### 9.1 `LOWER_MODEL_PILOT` — **COMPLETE**

Executed 2026-09-17, 18 runs. It tested the strong-model-ceiling explanation
directly: if the ceiling were the cause, a weaker model should have shown both
architecture-floor escape and a better cost profile. It showed **neither**. The
frozen rule returned `NO LOWER-MODEL SIGNAL`. See §5A.

### 9.2 `OPEN_SOURCE_COMPLEXITY_STUDY` — **NOT STARTED**

Re-run against real / open-source repositories with genuine architectural
complexity. Directly tests the substrate-legibility explanation. No runs exist and
no results are pre-populated.

**[INTERPRETATION]** This study **remains scientifically motivated** and is now the
single most informative next experiment, because it tests the only one of the two
rival explanations still standing. Its motivation was never contingent on the
lower-model outcome — repository complexity is an independent moderator, and the
lower-model pilot measured nothing about it — but the removal of the ceiling rival
raises its priority. It is **not** authorised by the lower-model result, needs new
tasks, new hidden acceptance packages and new architecture rule linkage, and
requires its own decision record before any run.

Neither should be treated as confirmatory. Gate `G1` is still not passed, the
suite is still not frozen, and `TD-B32`, `TD-B34`, `TD-B03` and `TD-B19` all
remain open.
