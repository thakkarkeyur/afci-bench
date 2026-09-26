# AFCI-Bench - metric definitions

Compiled 2026-09-26. Plain-English definitions for every metric that appears in
`AFCI_Professor_Results.xlsx`, `AFCI_Professor_Results_Summary.md` and
`AFCI_Professor_Full_Run_Results.csv`. Direction is stated for every ratio.

Two conventions hold everywhere in this package:

- **a missing metric is a blank, never a zero**; and
- **every aggregate is published beside its coverage count**.

---

## TOTAL_INPUT_TOKENS

*PRIMARY cost endpoint*

Every input token the model was charged for on a run: input_tokens + cache_creation_input_tokens + cache_read_input_tokens. The MAD's own tokens and all cache traffic are INSIDE this number and are never removed - removing them would be measuring a cheaper experiment than the one that was run.

**Direction and caveats.** Lower is better. For reset runs it is still EXACT, reconstructed from the streamed assistant messages.

---

## TOKEN_RATIO

*derived*

Within one block (same task, same reset state, same repetition), the C4 run's TOTAL_INPUT_TOKENS divided by the C1 run's. The headline figure is the MEDIAN of those per-block ratios, not a ratio of totals.

**Direction and caveats.** 1.00 is parity. Below 1.00 means the explicit MAD made the run cheaper; above 1.00 means it made it more expensive.

---

## TOTAL_OUTPUT_TOKENS

*secondary*

Tokens the model produced. Reported only where a terminal result event exists.

**Direction and caveats.** Lower is better. WITHHELD (not zero) for reset runs.

---

## MODEL_WALL_SECONDS

*secondary*

Wall-clock seconds inside the model invocation itself - the governed time endpoint. Distinct from TOTAL_RUN_SECONDS, which is the harness's own wall clock around the invocation and is not an endpoint.

**Direction and caveats.** Lower is better.

---

## EXPLORATION_CALLS

*secondary*

Read + grep + glob tool calls: how much the agent looked around before and while acting. This is the metric that would fall first if an explicit architecture document actually saved the agent from having to discover the architecture.

**Direction and caveats.** Lower is better.

---

## TOTAL_TOOL_CALLS

*secondary*

Every tool call the agent made on the run, of any kind.

**Direction and caveats.** Lower is better.

---

## UNIQUE_FILES_READ

*secondary*

The number of DISTINCT files the agent opened. Reading one file ten times counts once.

**Direction and caveats.** Lower is better.

---

## EDIT_AND_WRITE_CALLS

*secondary*

Edit tool calls plus write tool calls: how much the agent changed things.

**Direction and caveats.** Lower is better, but only weakly - a run that edits more may simply be implementing more.

---

## FILES_REEDITED

*descriptive*

How many distinct files the agent edited MORE THAN ONCE in a single run. A proxy for rework: going back to a file usually means the first attempt was not right.

**Direction and caveats.** Lower is better. No frozen paired endpoint is defined on it.

---

## UNIQUE_FILES_MODIFIED vs FILES_CHANGED

*descriptive*

UNIQUE_FILES_MODIFIED counts files targeted by an edit or write TOOL CALL. FILES_CHANGED counts files that actually DIFFER in the captured worktree at the end. They are different measurements and can disagree - on Haiku PT07/C1/R2 six files were written but only four ended up different.

**Direction and caveats.** Reported separately, never merged.

---

## CI_COMMAND_RUNS / TEST_COMMAND_RUNS

*descriptive*

How many times the agent itself invoked the project's CI or test command. These are TOOL-CALL COUNTS, not pass/fail outcomes, and they are not the v1 'CI success' metric.

**Direction and caveats.** No direction is claimed. A ratio is undefined when the C1 run issued none.

---

## PROVIDER_COST_USD

*secondary*

The provider-reported USD cost of the run, taken exactly as the runtime reported it in the terminal result event. Never modelled, never back-computed from token counts, never estimated.

**Direction and caveats.** Lower is better. A run with no terminal result event has NO cost, and that cell is blank - never 0.

---

## FUNCTIONAL_VALID

*quality gate*

The hidden acceptance oracle's verdict on whether the run actually did the task: record.functional_evaluation.functional_valid, and nowhere else. It is NEVER inferred from CI success, from the model's own prose, from exit status alone, from any architecture score, or from the number of files changed.

**Direction and caveats.** TRUE or FALSE. A blank means no verdict exists for that run at all.

---

## architecture applicable / violated

*quality endpoint*

APPLICABLE counts the architecture opportunities that the run's own changes made relevant - the decision points where the run could have got the architecture right or wrong. VIOLATED counts how many of those it got wrong. TARGET-VIOLATION RUNS counts runs that violated the specific opportunity the task was built to expose.

**Direction and caveats.** Lower violated is better. The identifiers behind these counts are hidden evaluator semantics and stay private; the counts themselves are fully published.

---

## architecture FLOOR

*reading*

Both arms recorded ZERO violations, so there was nothing for the treatment to improve. The frozen rule scores this FAIL because it requires strictly fewer violations and a tie at zero is not an improvement.

**Direction and caveats.** A floor is NO INFORMATION. It is not evidence that the MAD fails to improve architecture.

---

## reset overhead

*derived*

A run's metric under RESET divided by the same task and condition WITHOUT reset. It asks what a mid-task context loss costs, rather than what the task costs.

**Direction and caveats.** Lower overhead is better. C4's overhead being lower than C1's means the explicit MAD made recovery cheaper.

---

## paired block

*unit of analysis*

One task x reset state x repetition cell, holding exactly one C1 run and one C4 run. A block is paired-eligible only when BOTH of its runs are functionally valid - a cost figure from a run that did not work is not a cheaper way of doing the task.

**Direction and caveats.** One invalid run removes the whole block, which is why 34 individually valid Sonnet runs yield 16 pairs, not 17.

---

## C1 / C4

*conditions*

C1 gives the model the task and nothing else. C4 gives it the same task PLUS the explicit Machine-readable Architecture Document. Everything else - substrate, tooling, turn budget, model, runtime - is held identical.

**Direction and caveats.** The whole study is the difference between these two.

---

## How a run becomes a number

1. The runner prepares a sterile worktree from the governed substrate and hands the model the task body
   (C1) or the task body plus the MAD (C4). Nothing else differs.
2. The runtime streams events. The terminal `result` event carries the exact token and cost totals; for a
   reset run, whose phase A is interrupted before that event, input tokens are reconstructed exactly from
   the streamed assistant messages and output tokens and cost are withheld.
3. A hidden acceptance oracle, which the model never sees, decides `FUNCTIONAL_VALID`.
4. An out-of-band architecture oracle scores the captured worktree against the opportunities the run's own
   changes made applicable.
5. The frozen analysis pairs C1 against C4 within each block and takes the median of the per-block ratios.

Steps 3 and 4 are independent of each other and of step 2. A run that violated the architecture is still a
run that violated it, so the architecture channel is reported over *all* runs; a cost figure from a run that
did not work is not a cheaper way of doing the task, so the efficiency channel is restricted to
functionally-valid pairs.
