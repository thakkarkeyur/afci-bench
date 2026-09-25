# AFCI-Bench - results delivery

**Compiled 2026-09-25** from `study-results/` on branch `study-v2`, pinned to evidence
commit `b98cc65af4c2` (*study(backstage): execute task qualification V1 in full and record the result*) - the last change to the
evidence this package reports.

Reporting and export only. No benchmark observation was executed to produce this
package, no model was invoked, and no task definition, architecture document,
scorer, threshold, run plan, condition, raw run artifact or prior analysis was
changed. Every figure below was recomputed from the 164 run/attempt
rows and then checked against the frozen per-experiment analysis artifacts:
**146 checks, 0 mismatches**. The full check list is in
the workbook sheet `20_RECOMPUTATION_AUDIT`.

Claims are tagged **[FACT]** (a measured value, reproducible from the artifacts),
**[INTERPRETATION]** (a reading of those facts) and **[LIMITATION]** (a bound on
what the facts can support).

---

## 1. Study objective

AFCI asks a narrow question. If you hand a coding agent an explicit,
machine-readable description of a repository's architecture - the MAD - does it
build better, or more cheaply, than an agent given the task alone?

The programme operationalises that as two conditions held identical in every
other respect:

- **C1** - the task, and nothing else.
- **C4** - the same task, plus the explicit Machine-readable Architecture Document.

Two constructs are measured, and they are never combined into one score:

- **architectural conformance** - does the run violate the architecture
  opportunities its own changes made relevant? This is the study's actual
  construct.
- **efficiency** - tokens, wall time, exploration, tool effort and provider cost.
  This is the secondary construct, and it is the one with a clean pilot.

---

## 2. Experiments conducted

| # | experiment | model | runs | status | decision |
| --- | --- | --- | ---: | --- | --- |
| 1 | V1 original study | "Opus 7" | 48 | COMPLETE, PUBLISHED, superseded | published, then superseded by v1 limitations L1-L7 |
| 2 | PT08 C1 difficulty diagnostic | claude-sonnet-5 | 3 | COMPLETE | PT08 = REVISE; benchmark investment = CONTINUE |
| 3 | PT09 instrument qualification | claude-sonnet-5 | 3 (+1 infra-invalid) | COMPLETE | FAIL / ARCHITECTURE FLOOR -> STOP / REASSESS |
| 4 | PT10 instrument qualification | claude-sonnet-5 | 3 | COMPLETE | REVISE / WEAK PRESSURE -> STOP / REASSESS |
| 5 | Efficiency pilot, Attempt 1 | claude-sonnet-5 | 9 attempted of 36 | ABORTED | excluded wholesale; no analysis was ever performed |
| 6 | Efficiency pilot, Attempt 2 | claude-sonnet-5 | 36 | COMPLETE | STOP - NO EFFICIENCY SIGNAL JUSTIFIES FULL-SUITE EXPANSION |
| 7 | Lower-capability model pilot | claude-haiku-4-5-20251001 | 18 | COMPLETE | NO LOWER-MODEL SIGNAL - DO NOT EXPAND THE SYNTHETIC LOWER-MODEL MATRIX |
| 8 | Backstage real-repository pilot, Attempt 1 | claude-sonnet-5 | 7 attempted of 18 | HALTED | excluded wholesale; no analysis was ever performed |
| 9 | Backstage real-repository pilot, Attempt 2 | claude-sonnet-5 | 18 | COMPLETE | NO ARCHITECTURE SIGNAL - DO NOT AUTOMATICALLY EXPAND |
| 10 | Backstage task qualification V1 (*instrument qualification / C1-only / pre-treatment / not AFCI treatment evidence*) | claude-sonnet-5 | 15 C1 (+1 pre-delivery infra-invalid) | COMPLETE | INSUFFICIENT QUALIFIED TASKS - 1 of 5 qualified |
| 11 | Open-source complexity study | TBD | 0 | **NOT STARTED** | none - no runs exist and no result is pre-populated |

All three completed pilots were judged by a decision rule frozen **before** the
data they judge existed, and all three rules returned a negative verdict. None
was changed afterwards. The task qualification (row 10) is not a pilot and
judges no treatment: it applied a frozen **instrument** rule to C1 runs only, to
decide which tasks a future study may use.

---

## 3. Evidence and run inventory

**[FACT]** Mechanically counted from `AFCI_MASTER_RUN_RESULTS.csv`.

| measure | count |
| --- | ---: |
| total run/attempt records | 164 |
| distinct run identities | 161 |
| completed observations | 144 |
| functionally valid observations | 85 |
| explicitly functionally invalid | 16 |
| no functional verdict captured at all | 63 |
| diagnostic / qualification observations | 28 |
| infrastructure-invalid or damaged records | 7 |
| refused | 1 |
| excluded from every analysis | 108 |
| eligible for any analysis | 56 |
| **confirmatory observations** | **0** |

The three "missing" run identities are not a bookkeeping error: the PT08
diagnostic minted one run id for all three of its repetitions, and one Attempt-1
collision pair shares a single id. Both are recorded defects, kept as found.

| experiment | rows | status COMPLETE | functionally valid | eligible | token coverage | cost coverage | architecture coverage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `V1_ORIGINAL` | 48 | 48 | not captured | 0 | 0/48 | 0/48 | 0/48 |
| `V2_PT08_DIAGNOSTIC` | 3 | 3 | 3 | 0 | 0/3 | 0/3 | 3/3 |
| `V2_PT09_QUALIFICATION` | 4 | 3 | 3 | 0 | 0/4 | 0/4 | 3/4 |
| `V2_PT10_QUALIFICATION` | 3 | 3 | 3 | 0 | 0/3 | 0/3 | 3/3 |
| `V2_EFF_ATTEMPT1` | 9 | 0 | not captured | 0 | 0/9 | 0/9 | 0/9 |
| `V2_EFF_ATTEMPT2` | 36 | 35 | 34 | 34 | 35/36 | 19/36 | 0/36 |
| `V2_LOWER_MODEL_PILOT` | 18 | 18 | 17 | 16 | 18/18 | 18/18 | 18/18 |
| `V2_BACKSTAGE_PILOT` | 7 | 0 | 2 | 0 | 7/7 | 7/7 | 5/7 |
| `V2_BACKSTAGE_PILOT_ATTEMPT_2` | 18 | 18 | 8 | 6 | 18/18 | 18/18 | 18/18 |
| `V2_BACKSTAGE_TASK_QUALIFICATION_V1` | 16 | 15 | 15 | 0 | 15/16 | 16/16 | 15/16 |
| `V2_BACKSTAGE_TASK_QUALIFICATION_V2` | 2 | 1 | 0 | 0 | 1/2 | 2/2 | 1/2 |

`V2_EFF_ATTEMPT1` shows 0 under *status COMPLETE* because its rows carry
`INTACT_GOVERNED_OBSERVATION` (7 rows) and `DAMAGED_*` (2 rows) instead - a
deliberately distinct status, because those runs were never admitted as
observations. The experiment registry counts the same 7 rows as "completed runs";
both readings are shown rather than reconciled away.

**[LIMITATION]** All 56 eligible rows belong to three
**non-confirmatory** pilots. No p-value, confidence interval, effect size or
power estimate exists anywhere in this programme, and none would be defensible
from 16, 8 and 3 paired blocks at 3 repetitions.

---

## 4. V1 historical results

**Design.** 12 tasks x {baseline, AFCI} x {non-reset, reset} = 48 runs, one run
per cell, model labelled "Opus 7". Published as the ASE 2026 artifact; Zenodo DOI
`10.5281/zenodo.19757261`.

**[FACT]**

| metric | baseline | AFCI | change | per-task direction |
| --- | ---: | ---: | ---: | --- |
| non-reset code churn (mean) | 576.58 | 955.42 | +65.7% | AFCI higher in 12/12 |
| non-reset test churn (mean) | 172.67 | 244.00 | +41.3% | AFCI higher in 12/12 |
| reset true drift, delta CodeLOC (mean) | 307.7 | 670.5 | +117.9% | AFCI **lower** in 1/12 |
| CI pass | 100% | 100% | 0.0 pp | 48/48 |

**[INTERPRETATION]** Read at face value, v1 contradicts the hypothesis: AFCI
increased churn on every task and was more reset-inconsistent on 11 of 12. It
should not be read at face value.

**[LIMITATION]** Seven recorded limitations, each of which independently
undermines inference:

| id | limitation | consequence |
| --- | --- | --- |
| L1 | the tree was never reset between tasks, so edits accumulate across T01-T12 | runs are **non-independent**; the churn trend is confounded with accumulation |
| L2 | `run_one_v1.sh` does not invoke a model - it snapshots the working tree | generation and diff capture are not coupled |
| L3 | AFCI-Guard matched literal `libs/core` paths while the code uses `@afci-bench/*` aliases | the guard's regexes never fired; its zeros are **not measurements** |
| L4 | `docs/ARCH_RULES.yml` is 0 bytes | the machine-checkable architecture rules did not exist |
| L5 | `layer_jaccard` is a constant 1.0 | the metric cannot vary, so it measures nothing |
| L6 | no per-task acceptance oracle beyond `npm run ci`, which is saturated `True` | the success gate does not discriminate |
| L7 | `npm ci` fails on the clean v1 base | deterministic install is broken at the base tag |

Also: the v1 baseline ran against a repository whose architecture was visible in
the tree, so the "no architecture context" arm was not architecture-free.

> v1 is historical / exploratory evidence. No v1 number may be pooled with, or
> contrasted against, a v2 number.

---

## 5. Architecture diagnostic results

These three experiments measure **instruments**, not treatments. A run-purpose
firewall enforced by the record schema keeps them out of every confirmatory
dataset, treatment-effect estimate and power calculation.

**[FACT]**

| task | runs | functional | applicable opportunities | target violations | classification | consequence |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| PT08 | 3 | 3/3 (15/15 acceptance cases each) | 3 | **0/3** | functional ceiling + architecture floor | PT08 = REVISE; benchmark = CONTINUE |
| PT09 | 3 | 3/3 (14/14 each) | 3 | **0/3** | FAIL / ARCHITECTURE FLOOR | STOP / REASSESS |
| PT10 | 3 | 3/3 (8/8 each) | 3 | **1/3** | REVISE / WEAK PRESSURE | STOP / REASSESS |

PT10's single violation is the only target architecture violation recorded
anywhere in the programme: one forbidden import, on one line, in one
already-existing file, severity blocker, confidence certain, automated. The
opportunity id, rule id, forbidden scopes and anchor path are hidden evaluator
semantics and stay in the private evaluator repository. **No numeric result is
withheld.**

**[INTERPRETATION]** Three independent instruments at or near the architecture
floor on this substrate is evidence about the **substrate**, not only about the
tasks. A baseline at the floor has no room beneath it, so no treatment however
good can be discriminated.

**[LIMITATION]** Three observations per instrument. No power calculation
justifies that count and none is implied.

---

## 6. Sonnet efficiency pilot (Attempt 2)

**Design.** 3 tasks (PT01, PT04, PT07) x {C1, C4} x {non-reset, reset} x 3
repetitions = 36 runs, `claude-sonnet-5`, CLI 2.1.229, block-paired with
randomised within-block condition order.

**[FACT]** Execution and validity:

| | value |
| --- | ---: |
| scheduled / executed | 36 / 36 |
| completed | 35 |
| refused | 1 (sequence 12) |
| functionally valid | 34 - C1 **17/18**, C4 **17/18** |
| paired-eligible blocks | **16 of 18** (minimum required 12) |
| runs entering the paired analysis | 32 |
| valid but unpaired | 2 |

**[FACT]** Endpoints. Every figure is the median of per-block C4/C1 ratios;
1.0000 is parity and above 1.0000 means C4 cost more.

| endpoint | n | median C4/C1 | C4 lower | PT01 | PT04 | PT07 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **TOTAL_INPUT_TOKENS** (primary) | 16 | 1.4014 | 4/16 | 1.3372 | 0.9325 | 1.5419 |
| MODEL_WALL_SECONDS | 16 | 1.2660 | 4/16 | 1.2815 | 0.9834 | 1.7018 |
| EXPLORATION_CALLS | 16 | 1.3939 | 3/16 | 1.0714 | 1.3333 | 1.5130 |
| TOTAL_TOOL_CALLS | 16 | 1.1864 | 5/16 | 1.1000 | 0.9200 | 1.3867 |
| UNIQUE_FILES_READ | 16 | 1.2111 | 0/16 | 1.1429 | 1.3333 | 1.3571 |
| EDIT_AND_WRITE_CALLS | 16 | 1.9167 | 0/16 | 1.6000 | 1.3333 | 2.0000 |
| CI_COMMAND_RUNS | 16 | 1.0000 | 1/16 | 1.0000 | 1.0000 | 1.0000 |
| TOTAL_OUTPUT_TOKENS (non-reset only) | 9 | 1.4671 | 1/9 | 1.4671 | 1.0423 | 2.5088 |
| provider cost USD (non-reset only) | 9 | 1.4928 | 2/9 | 1.4438 | 0.9511 | 1.8851 |

By arm, on the primary endpoint: **NON_RESET 1.5582**
(n=9) and **RESET 1.3776**
(n=7). PT04 is the only task where C4 was
cheaper on median.

**[FACT]** One signal ran the other way. Reset overhead is a run's metric under
reset divided by the same task and condition without reset; lower is better.

| endpoint | tasks where C4's recovery overhead is lower |
| --- | --- |
| TOTAL_INPUT_TOKENS | **2 of 3** (PT01, PT07) |
| MODEL_WALL_SECONDS | **3 of 3** (PT01, PT04, PT07) |
| EXPLORATION_CALLS | 2 of 3 (PT01, PT07) |
| TOTAL_TOOL_CALLS | 2 of 3 (PT01, PT07) |

**[FACT]** The frozen decision. Both functional guardrails and the minimum-pairs
gate passed; every token and secondary-endpoint threshold failed. The
RESET-SPECIFIC GO branch failed only on its overall token clause - its two
reset-overhead clauses passed.

> **Outcome (rule 11.4): `STOP - NO EFFICIENCY SIGNAL JUSTIFIES FULL-SUITE
> EXPANSION`.** `efficiency_claim_made = false`.

**[LIMITATION]** `AFCI_EFFICIENCY_PILOT` is a **cost-only** purpose under its own
frozen governance. **No architecture endpoint was produced and none may be
inferred from it.** LOC churn was likewise not captured.

---

## 7. Haiku lower-model pilot

**Design.** The same three tasks on `claude-haiku-4-5-20251001`, non-reset only,
3 repetitions, 18 runs. The point was to test the most obvious explanation for
the Sonnet null - that a strong model already knows what the MAD would tell it.
Quality and efficiency are two **independent** channels, combined into no single
score.

**[FACT]** Execution and validity: 18 of 18 executed, 18 COMPLETE, **0 refused,
0 infrastructure-invalid**. 17 of 18 functionally valid - C1 **8/9**, C4 **9/9**.
The single invalid run, `PT04/C1/R2`, failed all four semantic acceptance cases
and strands its valid C4 partner, leaving **8 of 9** paired-eligible blocks.

**[FACT]** Architecture quality:

| arm | runs | applicable opportunities | violated | target-violation runs |
| --- | ---: | ---: | ---: | ---: |
| C1 | 9 | 9 | 0 | **0** |
| C4 | 9 | 9 | 0 | **0** |

Identical by task: 3 applicable, 0 violated in both arms for PT01, PT04 and PT07.

**[FACT]** Efficiency endpoints, 8 paired blocks:

| endpoint | n | median C4/C1 | C4 lower | PT01 | PT04 | PT07 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **TOTAL_INPUT_TOKENS** (primary) | 8 | 2.0372 | 2/8 | 2.9214 | 1.7502 | 0.9038 |
| TOTAL_OUTPUT_TOKENS | 8 | 1.7804 | 3/8 | 2.5067 | 1.4358 | 0.7171 |
| MODEL_WALL_SECONDS | 8 | 1.5268 | 3/8 | 2.3801 | 1.2307 | 0.8427 |
| TOTAL_TOOL_CALLS | 8 | 1.5023 | 2/8 | 2.0000 | 1.4174 | 0.9412 |
| EXPLORATION_CALLS | 8 | 1.7308 | 1/8 | 2.0000 | 2.1683 | 1.0769 |
| UNIQUE_FILES_READ | 8 | 1.2500 | 2/8 | 1.0000 | 1.0833 | 1.5000 |
| EDIT_AND_WRITE_CALLS | 8 | 1.1741 | 2/8 | 2.0000 | 1.1741 | 0.8750 |
| CI_COMMAND_RUNS | 8 | 1.0000 | 3/8 | 1.0000 | 0.7500 | 0.5000 |
| provider cost USD | 8 | 1.8865 | 2/8 | 2.5232 | 1.5777 | 0.8078 |

PT07 is the one task where C4 was directionally cheaper on tokens, time, output
and cost. PT01 was the most expensive for C4 on every endpoint.

**[FACT]** Rework over the 8 paired blocks: edit calls
54 vs 66,
files re-edited 16 vs
20, turns used
229 vs 309,
files changed in the worktree diff 25 vs
30, net lines
+1,621 vs +1,746.
Agent-initiated CI command runs went the other way:
13 for C1 against
8 for C4.

**[FACT]** The frozen decision:

| signal | criterion | observed | verdict |
| --- | --- | --- | --- |
| QUALITY | 12.1.1 C4 has fewer target architecture-violation runs overall | C4 0 vs C1 0 | **FAIL** |
| QUALITY | 12.1.2 improvement in at least 2 of 3 tasks | improved: none | **FAIL** |
| QUALITY | 12.1.3 functional guardrail | C4 valid 9 vs C1 valid 8; deficit -1 <= 1 | **PASS** |
| EFFICIENCY | 12.2.1 functional guardrail | C4 valid 9 vs C1 valid 8; deficit -1 <= 1 | **PASS** |
| EFFICIENCY | 12.2.2 at least one endpoint threshold met | median TOTAL_INPUT_TOKENS 2.0372 < 1.00; median EXPLORATION_CALLS 1.7308 <= 0.80; median TOTAL_TOOL_CALLS 1.5023 <= 0.85 | **FAIL** |

> **`NO LOWER-MODEL SIGNAL - DO NOT EXPAND THE SYNTHETIC LOWER-MODEL MATRIX`**

**[LIMITATION]** Criterion 12.1.1 fails on a **tie at zero**, not on C4 being
worse. Neither arm violated anything, so there was nothing to discriminate. The
rule requires *strictly fewer* violations, so a tie scores FAIL. That is a rule
outcome, not a finding about AFCI: the quality channel produced **no
information**.

---

## 8. Backstage real-repository pilot (Attempt 2)

**Design.** The first AFCI experiment on a **real, large, ambiguous** open-source
repository rather than the synthetic substrate: Backstage at
`f285f6e4`, which predates the 2026-02-15 contamination boundary. 3 tasks
(T1, T2, T5) x {C1, C4} x NON_RESET x 3 repetitions = 18 runs, 9 paired
blocks, `claude-sonnet-5` at effort `high`, CLI 2.1.229, 96-turn ceiling.
Attempt 1 was halted at 7 of 18 and is **excluded wholesale**; attempt 2 is a
wholly new execution with new run ids and new destinations.

**[FACT] Execution.** 18/18 executed in the committed order, 18 valid, **0
infrastructure-invalid, 0 retries**, 18 unique sessions, 0 scientific
modifications. Model requested and resolved `claude-sonnet-5` on every row;
effort `high` read back from two independent channels over 2,479 hook firings;
runtime context `CLEAN` with loaded context empty on all four fields; export
tree `4dfadc10...` verified per run. Captured provider cost **$32.19**.

**[FACT] Primary endpoint - architectural placement.** 1 applicable opportunity
per run, 18 across the set.

| scope | C1 target-violation runs | C4 target-violation runs |
| --- | ---: | ---: |
| OVERALL | 2 / 9 | 1 / 9 |
| T1 | 0 / 3 | 0 / 3 |
| T2 | 0 / 3 | 0 / 3 |
| T5 | 2 / 3 | 1 / 3 |

**[FACT] Functional endpoint.**

| scope | C1 valid | C4 valid | paired-valid blocks |
| --- | ---: | ---: | ---: |
| OVERALL | 4 / 9 | 4 / 9 | 3 / 9 |
| T1 | 0 / 3 | 0 / 3 | 0 / 3 |
| T2 | 2 / 3 | 3 / 3 | 2 / 3 |
| T5 | 2 / 3 | 1 / 3 | 1 / 3 |

**[FACT] The frozen decision** (`SL-V2-BACKSTAGE-PILOT-01` S11.1, all three
required):

| clause | statement | observed | verdict |
| --- | --- | --- | --- |
| 11.1.1 | C4 has FEWER target-violation runs than C1 overall | C1=2; C4=1 | **PASS** |
| 11.1.2 | C4 has FEWER target violations in >= 2 of 3 tasks | C4 fewer in 1 of 3 tasks (T5) | **FAIL** |
| 11.1.3 | C4 FUNCTIONAL_VALID no more than 1 below C1 | C1=4; C4=4; difference=0 | **PASS** |
| DECISION | ARCHITECTURE SIGNAL requires all three | NO ARCHITECTURE SIGNAL - DO NOT AUTOMATICALLY EXPAND | **NO SIGNAL** |

> **`NO ARCHITECTURE SIGNAL - DO NOT AUTOMATICALLY EXPAND`**

**[LIMITATION]** Criterion 11.1.2 fails on **ties at zero**, not on C4 being
worse. T1 and T2 produced zero target violations in *both* arms, so neither can
show C4 as "fewer"; only T5 discriminated. Two of three tasks sat at an
architecture floor - the same failure mode the Haiku pilot hit, here partial
rather than total.

**[LIMITATION] T1 is a task-instrument failure, not a model result.** All six
T1 runs - both arms, all three repetitions - passed exactly 3 of 4 semantic
cases and failed the **same single case every time**, while both controlled T1
references pass that case in the frozen reference matrix. The oracle is
satisfiable; the model-facing task statement does not ask for the behaviour it
checks. T1 therefore contributes 0 functionally valid runs *and* 0 target
violations to either arm - inert on both endpoints. Nothing was changed in
response; the task bytes, oracle, scorer and rule stand exactly as frozen.

**[FACT] MAX_TURNS.** 2 of 18 reached the 96-turn ceiling, one per arm, both on
T5. The 64->96 raise worked: attempt 1 hit its ceiling on 4 of its 5 valid rows.
`MAX_TURNS` is a scientific outcome and was never a retry reason.

**[FACT] Secondary efficiency** (S11.2, cannot override S11.1), median C4/C1
over functionally valid paired blocks:

| endpoint | median C4/C1 | coverage | C4 lower |
| --- | ---: | ---: | ---: |
| `TOKEN_RATIO` | 0.9672 | 3/3 | 2/3 |
| `WALL_RATIO` | 1.0551 | 3/3 | 0/3 |
| `EXPLORATION_RATIO` | 0.875 | 3/3 | 2/3 |
| `TOTAL_TOOL_RATIO` | 1.0159 | 3/3 | 0/3 |
| `COST_RATIO` | 0.9497 | 3/3 | 2/3 |
| `UNIQUE_FILES_READ_RATIO` | 0.9231 | 3/3 | 2/3 |
| `EDIT_WRITE_RATIO` | 0.9286 | 3/3 | 2/3 |

**[LIMITATION]** Coverage is **3 of 9** blocks, because no T1 run is
functionally valid. At n=3 a single block moves every median. These figures are
descriptive only and could not have rescued a failed S11.1 in any case.

**[FACT] The network preflight prevented a repeat of the attempt-1 loss.** 20
preflight refusals occurred, every one `VPN_ADAPTER_UP` - the adapter state that
severed two attempt-1 observations. Each refused **before the task was
delivered**: no artifact directory, no workspace, no provider call, no
observation consumed, $0. The cost was wall-clock only.

---

## 9. BACKSTAGE TASK QUALIFICATION V1

> **Every row in this section is: instrument qualification / C1-only / pre-treatment / not AFCI treatment evidence.**

**Design.** `SL-V2-BACKSTAGE-TQ-01`, frozen before its first observation. It
asks which candidate Backstage tasks a **future** AFCI study may use, and runs
the baseline condition **C1 only**: no C4 observation, no architecture packet,
no treatment effect. 5 candidates x 3 C1 observations = 15, `claude-sonnet-5`
at effort `high`, CLI 2.1.229, NON_RESET, 96 turns, on the same frozen
substrate. Backstage Attempts 1 and 2 are unchanged and never pooled with it.

**Why it exists.** Attempt 2 showed that the instrument, not only the model,
limited what could be seen: T1 was functionally underspecified, T2 sat at an
architecture floor, and only T5 discriminated.

* **Q1 `BTQ-T1R` is T1 repaired** under a new identity. All six Attempt-2 T1
  runs failed the same semantic case because the statement never said a
  returned value must be **synchronous**; one sentence now says so, and no
  architecture guidance was added. T1's original bytes are untouched.
* **Q2 `BTQ-T5` is T5**, byte for byte.
* **Q3-Q5** are newly mined, real post-substrate Backstage changes.
* **T2 is RETIRED** (architecture floor in Attempt 2) and was not substituted.

Every candidate passed static qualification before any model run: the untouched
substrate fails the functional check and scores 0/0; a legal reference is
functional PASS with 1 applicable, 0 violated; a violating reference is
functional PASS with 1 applicable, 1 violated; both pass the model-visible gate.

**[FACT] The frozen rule** - QUALIFIED iff `FUNCTIONAL_VALID` >= 2 of 3 **and**
target violation >= 1 of 3:

| slot | task | rule family | FUNCTIONAL_VALID | target violation | MAX_TURNS | status |
| --- | --- | --- | ---: | ---: | ---: | --- |
| Q1 | `BTQ-T1R` | extension-point placement / ownership | 3 / 3 | 0 / 3 | 0 / 3 | **ARCHITECTURE_FLOOR_REJECT** |
| Q2 | `BTQ-T5` | shared contract / permission ownership | 3 / 3 | 3 / 3 | 2 / 3 | **QUALIFIED** |
| Q3 | `BTQ-C02` | shared contract / permission ownership | 3 / 3 | 0 / 3 | 1 / 3 | **ARCHITECTURE_FLOOR_REJECT** |
| Q4 | `BTQ-C04` | package / role ownership | 3 / 3 | 0 / 3 | 0 / 3 | **ARCHITECTURE_FLOOR_REJECT** |
| Q5 | `BTQ-C05` | shared contract / API ownership | 3 / 3 | 0 / 3 | 0 / 3 | **ARCHITECTURE_FLOOR_REJECT** |

> **`INSUFFICIENT QUALIFIED TASKS`** - 1 of 5 qualified
> (BTQ-T5). Fewer than three: the phase stops, with no further mining.

**[FACT] Reading a zero.** Every final observation had exactly one applicable
architecture opportunity, so each 0 means the legal placement was made every
time the decision arose - an architecture floor under C1, not an opportunity
the instrument missed. The T1 repair worked on the functional axis (3/3 valid
against 0/6 for the original T1 in Attempt 2) but exposed no baseline pressure.

**[LIMITATION] Selection.** This qualification intentionally selects tasks with measurable baseline architecture pressure. A future treatment study built on its selection estimates AFCI behaviour on ARCHITECTURE-PRESSURE-QUALIFIED tasks and must not be presented as an unbiased estimate over arbitrary Backstage development tasks. The tasks are
**pressure-qualified** by a rule declared in advance, not cherry-picked; with
fewer than three qualified, no task was selected.

**[FACT] Execution.** 15 valid final
observations, all functionally valid; 1
infrastructure-invalid attempt; captured provider cost
**$33.72**. One attempt
failed **before its task was delivered** (host standby during workspace
preparation, no model invoked, $0): deviation `SL-V2-BACKSTAGE-TQ-01-D1`
re-derived `WORKSPACE_PREPARATION_FAILED` from the attempt's own artifacts and
the cell completed on its pre-authorised attempt-2 identity.

---

## 9B. BACKSTAGE TASK QUALIFICATION V2 - HALTED

> **Every row in this section is: instrument qualification / C1-only / pre-treatment / not AFCI treatment evidence. None is a qualification result.**

**Design.** `SL-V2-BACKSTAGE-TQ-02`, pre-registered before its first
observation: five **new** mined candidates (Q6-Q10), 3 C1 observations each,
the same model, effort, CLI version, turn ceiling and substrate as V1, looking
for at least two tasks to join `BTQ-T5`. It applied V1's lesson - its floors
followed an obvious nearby precedent - by mining for changes where the nearest
code points away from the documented owner. All five candidates passed static
qualification before data (reference matrix, visible gate, task/oracle
alignment, leakage audit, real preparation). Two of them prepare only under a
pre-registered warm-up report restore, which puts back committed API reports
that the frozen warm-up rewrites on the untouched substrate.

**[FACT] Halted after 1 of 15** (`SL-V2-BACKSTAGE-TQ-02-H1`). The runtime pin
launched the frozen `2.1.229` binary by an extensionless path. The version and
digest checks passed, but Claude Code's built-in Grep tool re-spawns its own
executable, which Windows cannot resolve without an executable extension, so
the tool could not start. V1 ran the same version under its usual executable
name and never hit this (93 successful Grep/Glob results, 0 such errors); no
pre-data gate exercised a built-in tool.

| seq | slot | task | status | delivered | functional | turns | files changed | cost |
| ---: | --- | --- | --- | --- | --- | --- | ---: | ---: |
| 1 | Q6 | `BTQ2-C01` | valid under the frozen classifier; produced under the defect | yes | FAIL (0/5) | 34/96 | 0 | $1.35 |
| 2 | Q7 | `BTQ2-C02` | stopped before task delivery | no | - | - | - | $0.00 |

> **HALTED - no candidate status determined; 0 tasks newly qualified.** The
> frozen rule's first branch applies: **INSUFFICIENT ADDITIONAL QUALIFIED
> TASKS**, reached by halt, not by measurement. `BTQ-T5` remains the only
> qualified task.

**[FACT] Decision.** Offered a fix under a recorded deviation (launch the
byte-identical binary under an executable name, prove the tools, classify every
observation launched by the extensionless path as infrastructure-invalid,
resume on the pre-authorised second attempts), continuing unchanged, or
stopping, the Study Lead stopped the phase. The five candidates remain
statically qualified instruments; using them needs a new pre-data decision.

**[LIMITATION] Selection.** Unchanged from V1: qualification selects tasks with
measurable baseline architecture pressure, so any study built on it estimates
AFCI behaviour on architecture-pressure-qualified Backstage tasks only.

---

## 10. Cost and token findings

**[FACT] Token audit.** `TOTAL_INPUT_TOKENS = input_tokens +
cache_creation_input_tokens + cache_read_input_tokens` on every row that carries
tokens - checked on all 94 such rows, 0 failures. The MAD's
own tokens and all cache traffic stay inside the number.

| scope | paired blocks | C1 total input tokens | C4 total input tokens | C1 median/run | C4 median/run | median C4/C1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Sonnet overall | 16 | 10,988,803 | 14,859,860 | 698,639 | 1,040,459 | 1.4014 |
| Sonnet NON_RESET | 9 | 5,912,725 | 8,339,159 | 664,777 | 1,062,096 | 1.5582 |
| Sonnet RESET | 7 | 5,076,078 | 6,520,701 | 733,633 | 1,028,101 | 1.3776 |
| Haiku NON_RESET | 8 | 5,599,750 | 9,504,643 | 652,919 | 1,271,816 | 2.0372 |

Token coverage: 94 of 164 run rows carry
input-token evidence, 78 carry output tokens. v1, the
aborted Attempt 1 and the three diagnostics predate or do not use the token
instrumentation; their cells are blank, never 0. The one Backstage
task-qualification attempt that failed before delivery invoked no model and has
no token record either.

**[FACT] Cost audit.**

| scope | runs | runs with complete cost | captured total | verdict |
| --- | ---: | ---: | ---: | --- |
| Sonnet Attempt 2 - all rows | 36 | 19 | $11.1919 | PARTIAL COST CAPTURE |
| Sonnet Attempt 2 - NON_RESET | 18 | 18 | $10.9463 | COMPLETE COST COVERAGE |
| Sonnet Attempt 2 - RESET | 17 | 1 | $0.2456 | PARTIAL COST CAPTURE |
| Haiku lower-model pilot - all rows (NON_RESET by design) | 18 | 18 | $3.8007 | COMPLETE COST COVERAGE |

The Sonnet RESET row counts 17, not 18: the refused run (sequence 12) carries no
reset state at all, so it sits outside both arms. 18 + 17 + 1 = 36.

| paired cost ratio | n | C1 total | C4 total | median C4/C1 |
| --- | ---: | ---: | ---: | ---: |
| Sonnet NON_RESET | 9 | $4.5288 | $6.4175 | 1.4928 |
| Sonnet RESET | 0 | n/a | n/a | **no cost comparison exists** |
| Haiku NON_RESET | 8 | $1.3862 | $2.0068 | 1.8865 |

**Total captured provider cost across all runs carrying cost evidence:
$93.18 over 80 runs.**

> **CAPTURED COST, NOT NECESSARILY TOTAL STUDY COST.**
> 84 of 164 run rows carry no
> provider-cost record at all: all 48 v1 rows, all 9 Attempt-1 rows, all 10
> diagnostic rows, 16 of 17 Sonnet RESET rows, and the one refused run. Money was
> spent on those runs; the runtime never reported it in a form the record could
> carry.

**[LIMITATION]** A reset run's phase A is deliberately interrupted at the
checkpoint, **before** its terminal result event - the only place the runtime
reports output tokens and cost. For a reset run, input tokens remain **exact**
(reconstructed from the streamed assistant messages) while output tokens and cost
are **withheld, not zero and not estimated**. The one Sonnet reset run that does
carry a cost is `PT04/C1/RESET/R1`, and it carries one precisely because it never
reached its checkpoint - it is functionally invalid and enters no paired figure.
There are therefore **zero usable Sonnet RESET cost pairs**, and the 1.4928 figure
describes the non-reset arm only.

---

## 11. Functional and architecture quality

**[FACT]**

| experiment | C1 valid | C4 valid | paired-valid blocks | semantic cases passed (C1 / C4) |
| --- | ---: | ---: | ---: | --- |
| Sonnet Attempt 2 | 17/18 | 17/18 | 16 of 18 | 68 / 68 |
| Haiku lower-model pilot | 8/9 | 9/9 | 8 of 9 | 32 / 36 |

**[FACT]** Architecture, over every run that produced a measurement:

| experiment | arm | runs | applicable | violated | target-violation runs |
| --- | --- | ---: | ---: | ---: | ---: |
| PT08 diagnostic | C1 | 3 | 3 | 0 | 0 |
| PT09 qualification | C1 | 3 | 3 | 0 | 0 |
| PT10 qualification | C1 | 3 | 3 | 1 | 1 |
| Haiku pilot | C1 | 9 | 9 | 0 | 0 |
| Haiku pilot | C4 | 9 | 9 | 0 | 0 |
| **Sonnet Attempt 2** | both | 36 | **NOT MEASURED** | **NOT MEASURED** | **NOT MEASURED** |
| **V1 original** | both | 48 | **INVALID FOR INFERENCE** | **INVALID FOR INFERENCE** | **INVALID FOR INFERENCE** |

**[INTERPRETATION]** Functional acceptance is saturated and architecture sits at
a floor. Six instrument/model combinations now sit at or near that floor on this
substrate: PT08, PT09 and PT10 for an unguided Sonnet baseline, and PT01, PT04
and PT07 for Haiku in **both** arms.

**[LIMITATION]** The evidence base is lopsided. The study's *actual* construct -
architectural conformance - has been measured only by instruments that all sat at
or near the floor, while its *secondary* construct - cost - has one clean pilot.
The cost result must not be allowed to stand in for an architecture result.

---

## 12. Cross-model interpretation

**[FACT]** Both sides below are NON_RESET, so the comparison is like-for-like.

| metric | Sonnet C4/C1 (n=9) | Haiku C4/C1 (n=8) | difference | reading |
| --- | ---: | ---: | ---: | --- |
| TOTAL_INPUT_TOKENS | 1.5582 | 2.0372 | +0.4791 | Haiku ratio higher |
| TOTAL_OUTPUT_TOKENS | 1.4671 | 1.7804 | +0.3133 | Haiku ratio higher |
| MODEL_WALL_SECONDS | 1.4968 | 1.5268 | +0.0300 | Haiku ratio higher |
| EXPLORATION_CALLS | 1.5714 | 1.7308 | +0.1593 | Haiku ratio higher |
| TOTAL_TOOL_CALLS | 1.3333 | 1.5023 | +0.1690 | Haiku ratio higher |
| UNIQUE_FILES_READ | 1.4000 | 1.2500 | -0.1500 | Haiku ratio lower |
| EDIT_AND_WRITE_CALLS | 2.0000 | 1.1741 | -0.8259 | Haiku ratio lower |
| PROVIDER_COST_USD | 1.4928 | 1.8865 | +0.3937 | Haiku ratio higher |

| channel | Sonnet | Haiku | comparable? |
| --- | --- | --- | --- |
| architecture target violations | NOT MEASURED (cost-only purpose) | 0/9 in C1 and 0/9 in C4 | **no** |
| functional validity | 17/18 and 17/18 | 8/9 and 9/9 | descriptively only |

> **This is a descriptive comparison between two separate experiments, not a
> randomised cross-model causal comparison.** The two pilots ran under separate
> purposes, separate schedules and separate frozen analyses and are **never
> pooled**. No interaction was estimated, no test was performed, and no pooled
> model exists.

**[INTERPRETATION]** The moderator hypothesis predicted that a weaker coding
model, having less ability to infer architecture from the repository alone, would
find the explicit MAD *more* useful. The prediction did not come true on the
primary endpoint: C4's median input-token ratio **rose** from
1.5582 to
2.0372, a difference of
0.4791 in the direction opposite to the prediction, and
the quality channel produced nothing at all because both arms sat at zero.

Two of the eight metrics did move the predicted way -
UNIQUE_FILES_READ, EDIT_AND_WRITE_CALLS -
and both are reported above rather than dropped. Neither is the primary endpoint,
both remain **above** 1.0000 on the Haiku side (so C4 still cost more in absolute
terms on both models), and with 8 and 9 paired blocks and no test performed, a
two-of-eight split is not a result. It is recorded so that the six-of-eight
direction is not read as unanimity.

---

## 13. What the evidence supports

1. **[FACT]** On this substrate with `claude-sonnet-5`, explicit MAD injection
   costs more than it saves across every captured cost dimension except CI
   invocations.
2. **[FACT]** It does so without buying functional quality: 17/18 versus 17/18.
3. **[FACT]** Weakening the model did not reduce C4's relative cost; it raised it,
   and produced no quality gain because both arms sat at zero violations.
4. **[FACT]** The reset-recovery direction is the one consistent counter-signal,
   strongest in wall time (3 of 3 tasks).
5. **[INTERPRETATION]** The **strong-model ceiling** explanation for the repeated
   null is **not supported**. Instrument discrimination, not model capability, is
   the binding constraint on the programme.
6. **[INTERPRETATION]** Expanding either pilot, unchanged, is not justified. Both
   frozen rules returned a negative verdict and both were honoured.
7. **[INTERPRETATION]** The benchmark machinery works. Sterile execution, model
   pinning and readback, context auditing, hidden acceptance, the architecture
   oracle, the artifact firewall, run-identity derivation and the frozen analysis
   all executed end to end - and caught their own defects twice, in ways that cost
   real money and were recorded rather than smoothed over.

---

## 14. What the evidence does NOT support

1. **We cannot conclude AFCI does not work.** We can conclude it did not reduce
   cost here. Efficiency is one construct; architectural conformance is the
   study's actual construct, and the cost pilot **did not measure it at all**.
2. **We cannot attach any statistical confidence to anything.** No p-value, no
   confidence interval, no effect size, no power estimate.
3. **We cannot generalise past this substrate** - one synthetic 49-file monorepo
   whose architecture is legible from its own code.
4. **We cannot generalise past the two models used.** `primary_model` is still
   `null`; no model has been selected for the study.
5. **We cannot use the reset-recovery signal as a finding.** It is descriptive,
   from 3 tasks, and it failed the branch that would have made it a GO.
6. **We cannot read anything as a v1 hypothesis test.** L1-L7 make the v1
   comparison uninterpretable as a treatment contrast.
7. **We cannot claim any architecture result from the Sonnet pilot.** It produced
   none.
8. **We cannot claim an architecture result from the Haiku pilot either.** It
   produced an endpoint, but at the floor in both arms. A tie at zero
   discriminates nothing and must not be read as AFCI failing to improve
   architecture.
9. **We cannot claim that model capability moderates AFCI's value.** Two separate
   experiments compared descriptively, never pooled.

---

## 15. Limitations

| # | limitation |
| --- | --- |
| 1 | **No confirmatory evidence exists.** Collection has not begun. The suite-wide protocol is PRE-FREEZE, gate `G1` is not passed, and `TD-B32`, `TD-B34`, `TD-B03` and `TD-B19` remain open. |
| 2 | **No statistical inference of any kind.** Every reported figure is a median of paired ratios - a descriptive statistic. No power calculation has ever been run. |
| 3 | **One synthetic substrate**, 49 files, whose layering is inferable from its own import graph and path aliases. A model can often deduce the intended architecture *without* the MAD, which directly attacks the MAD's marginal value. This is the primary external-validity threat to every v2 finding. |
| 4 | **No study model has been selected.** Both models used so far are provisional. |
| 5 | **Architecture is measured only where it sat at a floor.** The evidence base is lopsided toward cost. |
| 6 | **Reset cost and output tokens do not exist for reset runs** - withheld by construction, not missing by accident. |
| 7 | **This package is a secondary artifact.** Where it and a primary artifact disagree, the primary artifact wins. |
| 8 | **Task selection by baseline pressure.** Backstage task qualification V1 selects tasks with measurable C1 architecture pressure; any study built on it estimates AFCI behaviour on **architecture-pressure-qualified** tasks and must not be presented as an unbiased estimate over arbitrary Backstage tasks. It qualified 1 of 5 candidates, so no selection exists yet. |

---

## 16. Current research direction

The chain is short and each link is recorded:

1. **v1 measured the wrong things well enough to notice.** Churn is a proxy, the
   guard did not fire, the oracle did not discriminate, and runs were not
   independent. v2 replaced proxies with a hidden functional acceptance oracle and
   an out-of-band architecture oracle.
2. **PT08 showed the instruments, not the theory, were the bottleneck.** A
   baseline at the architecture floor cannot discriminate however good the
   treatment is.
3. **PT09 and PT10 showed it was not specific to PT08.** Two purpose-built
   replacements landed in the same place.
4. **The efficiency pilot asked a cheaper question that could be answered now** -
   does the MAD at least pay for itself? - and answered **no**, under a rule frozen
   before the data existed.
5. **The lower-model pilot weakened the model, and the null held.** A weaker model
   produced no quality signal and a *worse* cost ratio.
6. **[INTERPRETATION]** The common factor across steps 2-5 is not model strength -
   that has now been varied and did not matter. What remains is that **a legible
   synthetic repository gives an agent little to gain from being told its
   architecture**, whether the agent is strong or weak.

**[INTERPRETATION]** Repository architectural complexity / ambiguity /
context-recovery burden is therefore the next scientifically distinct moderator to
investigate. **This is the next hypothesis to test, not a proven one.** It stands
by elimination rather than by evidence, and nothing in this package tests it.

**[FACT] The first real-repository evidence points the same way.** Backstage
Attempt 2 returned NO ARCHITECTURE SIGNAL with two of three tasks at an
architecture floor, and Backstage task qualification V1 (C1 only, no treatment)
then found the floor again on 4 of 5 candidates: only T5 carries measurable
baseline pressure. **[INTERPRETATION]** On a large, ambiguous real repository
too, `claude-sonnet-5` mostly makes the legal placement decision without being
told the architecture, so finding tasks where a baseline agent actually violates
the architecture is itself the bottleneck for any C1-vs-C4 study.

---

## 17. Next study - open-source architectural complexity

**Status: NOT STARTED.** No runs exist. No results are pre-populated.

Re-run against real / open-source repositories with genuine architectural
complexity, where the architecture is *not* inferable from a 49-file import
graph. That directly tests the substrate-legibility explanation - the only one of
the two rival explanations still standing.

Its motivation was never contingent on the lower-model outcome: repository
complexity is an independent moderator and the lower-model pilot measured nothing
about it. Removing the ceiling rival raises its priority; it does not authorise
it.

Before any run it needs its own decision record, new tasks, new hidden acceptance
packages and new architecture rule linkage. Gate `G1` is still not passed and the
suite is still not frozen.

---

*Sources: `study-results/AFCI_MASTER_RUN_RESULTS.csv`,
`AFCI_MASTER_EXPERIMENT_REGISTRY.csv`, and the frozen per-experiment analysis
artifacts under `01_v1_original_study/` through `06_lower_model_pilot_completed/`.
Traceability from any figure here to its raw artifact is in
`AFCI_Professor_Evidence_Map.md` and workbook sheet `18_EVIDENCE_MAP`.*
