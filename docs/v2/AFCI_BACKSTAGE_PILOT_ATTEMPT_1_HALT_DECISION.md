# SL-V2-BACKSTAGE-PILOT-02 — Attempt 1 of the Backstage pilot is halted

Status: **execution halted after 7 of 18 scheduled observations.** Escalation
record, raised under [`FAILURE_RERUN_POLICY.md`](FAILURE_RERUN_POLICY.md) §5,
which requires that repeated infrastructure failure be **escalated, not silently
re-attempted**, and whose escalation policy `TD-N06` is an **open decision**.

This record authorizes **no** further model run. It changes **no** frozen
artifact of [`SL-V2-BACKSTAGE-PILOT-01`](AFCI_BACKSTAGE_PILOT_DECISION.md).

---

## 1. The halt, in one line

Two scheduled observations were destroyed mid-run by a **local network
failure**, the launcher has **no replacement mechanism** and refuses any run id
absent from the frozen plan, so continuing would have required either an
unrecorded protocol change or a run-id reuse of exactly the kind that has
previously destroyed data in this study. Execution stopped.

---

## 2. What was executed

Seven rows of the frozen 18-row schedule were attempted, in the frozen order.
**Five are valid observations. Two are infrastructure-invalid.** Eleven were
never started and their destinations remain unoccupied.

| Seq | Task | Cond | Rep | Valid | Turns | Completion | All semantic cases passed | Arch appl / viol / target | Input tokens | Cost USD | Model wall s |
| ---: | --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| 1 | T2 | C4 | 2 | yes | 58/64 | COMPLETED_NATURALLY | yes | 1 / 0 / false | 2,817,125 | 1.514 | 861.8 |
| 2 | T2 | C1 | 2 | yes | 64/64 | MAX_TURNS_REACHED | no | 1 / 0 / false | 3,585,944 | 1.798 | 1,789.4 |
| 3 | T5 | C4 | 2 | yes | 64/64 | MAX_TURNS_REACHED | no | 1 / 1 / true | 3,002,072 | 1.614 | 341.0 |
| 4 | T5 | C1 | 2 | yes | 64/64 | MAX_TURNS_REACHED | yes | 1 / 1 / true | 2,919,281 | 1.564 | 565.7 |
| 5 | T1 | C1 | 2 | yes | 64/64 | MAX_TURNS_REACHED | no | 1 / 0 / false | 3,289,224 | 1.684 | 1,335.5 |
| 6 | T1 | C4 | 2 | **no** | 56/64 | **PROCESS_FAILED** | — | — | 2,482,292 | 1.275 | 2,692.8 |
| 7 | T5 | C4 | 3 | **no** | 54/64 | **PROCESS_FAILED** | — | — | 2,747,021 | 1.478 | 952.8 |

Rows 6 and 7 carry no functional or architecture result in this record. Hidden
scoring did run against their preserved workspaces, but a candidate truncated
mid-task by a transport failure has no scorable outcome, and publishing those
numbers would misrepresent a network event as model behaviour.

### 2.1 Execution integrity, all seven rows

Verified per row from each run's own record, not asserted:

| Property | Result |
| --- | --- |
| Model readback | `claude-sonnet-5` requested **and** resolved, 7/7 |
| Effort readback | `high`, validated 7/7, from both the hook payload's `effort.level` and the hook process's `CLAUDE_EFFORT` |
| Runtime context verdict | `CLEAN` 7/7 — empty skills, plugins, MCP servers and slash commands; `apiKeySource: none` |
| Runtime version | 2.1.229, 7/7 |
| Substrate tree in the model-visible workspace | `4dfadc101db1c9f29b82934db25def67a93a2563`, 7/7 |
| Unique sessions | 7/7, no resume, no continue, no session reuse |
| Scientific modifications | none |

---

## 3. The two infrastructure failures

Both rows died the same way: the runtime exhausted its API retry budget and the
process exited 1.

```
{"subtype": "api_retry", "attempt": 10, "max_retries": 10, ...}
"API Error: Can't reach the API server — check your internet or DNS (ENOTFOUND)"
```

Row 6 recorded 10 exhausted retries, row 7 recorded 8 retry events before the
same terminal error. Independently confirmed at the machine afterwards: DNS
resolution was dead (`nslookup` timed out against both the configured resolver
and a public one) and ICMP to `1.1.1.1` showed **100% loss**. After a reboot,
raw connectivity and the API both recovered — `HTTP 401` at ~5 ms name lookup,
stable across repeated probes — while the local VPN adapter remained up with an
**unresponsive DNS server**, which is the most probable cause.

### 3.1 Classification

[`FAILURE_RERUN_POLICY.md`](FAILURE_RERUN_POLICY.md) §2 lists
**`INFRA_API_TRANSPORT` — API transport failure (network / 5xx / dropped
stream)** as rerun-eligible, with both the original and the replacement retained
and linked under §5.

This is **not** a §3 valid model outcome. It is specifically not
`BUDGET_TURNS_EXHAUSTED`: both runs stopped **below** the 64-turn ceiling, at 56
and 54, because the API became unreachable. Nothing about the model's own
behaviour ended them.

It is also **not** the situation of
[`AFCI_EFFICIENCY_PILOT_ATTEMPT_1_ABORT_DECISION.md`](AFCI_EFFICIENCY_PILOT_ATTEMPT_1_ABORT_DECISION.md)
§4.2, where the task was delivered, the model ran **to completion**, the turns
were spent, and only the capture afterwards failed. Here the run itself was
severed part-way.

---

## 4. Why this halted instead of re-running

The policy permits a replacement. The infrastructure does not currently express
one.

1. **The launcher has no replacement mechanism.** It refuses any run id absent
   from the frozen plan (`RUN_ID_NOT_IN_FROZEN_PLAN`, checked against the frozen
   plan digest) and fail-closes on an occupied destination.
2. **Each run id maps to exactly one artifact and one workspace destination.**
   Re-running in place would give the original and the replacement the **same**
   run id, so the §5 linkage (`replaces_run_id` / `replaced_by_run_id`) cannot
   be expressed — and run-id reuse is the precise defect that previously
   destroyed 18 runs in this study and that the current identity guards exist to
   prevent.
3. **The clean path is an amendment, not a workaround.** Run identity already
   includes an `execution_attempt` component, and the plan generator already
   takes it as a parameter, so attempt-2 rows would produce distinct ids and
   distinct destinations. But the launcher validates against the **frozen plan**,
   so the two replacement rows must be added to the plan — which changes
   `plan_sha256`. That is a protocol amendment and is recorded as one, never
   applied silently.
4. **`TD-N06` is open.** §5 ends: "repeated infrastructure failure on the same
   cell is escalated, not silently re-attempted (escalation policy = open
   decision `TD-N06`)." Two failures in consecutive rows is the trigger for that
   sentence, and the policy it points at does not yet exist.

---

## 5. No analysis preceded this halt

Recorded explicitly, because a halt issued *after* a comparative result would be
a different and far less defensible act:

* **no `C1`-vs-`C4` comparison was computed**, for any task, arm or repetition;
* **no target-violation arm total was formed**;
* **no `TOKEN_RATIO`, `WALL_RATIO`, `EXPLORATION_RATIO`, `TOOL_RATIO` or
  `COST_RATIO` was calculated**;
* **no continuation criterion was evaluated** and **no continuation decision was
  taken**;
* no pilot outcome was emitted.

**The five valid rows in §2 are not an analysis set and must not be used as
one.** They are recorded for provenance and cost accounting. The schedule is
11 rows short, the arms are unbalanced (3 `C1`, 2 `C4`), the nine paired blocks
the continuation rule depends on do not exist, and `SL-V2-BACKSTAGE-PILOT-01`
§11.3 forbids a confirmatory claim from this pilot even when complete. Deriving
an arm comparison from these rows would be invalid on every one of those grounds
independently.

---

## 6. A pre-execution blocker, resolved before any model ran

Recorded because it changes how preparation must be validated in future, not
because it affected any observation.

The first execution attempt of row 1 was **refused by the launcher before the
model was invoked**, with `SUBSTRATE_IDENTITY_MISMATCH`: the prepared workspace
tree was not the frozen export tree. Cause: the longest substrate-relative path
is 178 characters and the frozen workspace roots are 92, giving 271 — past
Windows' 260-character limit. Two tracked fixture files were therefore missing
from the workspace commit. The operating system had long paths enabled, so the
files were written to disk correctly; **git** was the component that failed,
because `core.longpaths` was unset, and `git add` **warned and exited 0**, so
every guard inside workspace preparation passed. The launcher's substrate
tree-hash comparison was the only check that caught it.

Preparation had been validated end to end on five disposable workspaces, but all
five used a **30-character** root, so real destination path length was never
exercised. Resolved by enabling `core.longpaths` at **system** scope — required
rather than per-user, because the launcher pins a sterile `HOME`, so a per-user
setting would reach preparation but not the model, leaving the model's own `git`
unable to read two tracked files. Verified before resumption: preparation at a
synthetic 92-character root then produced the frozen export tree exactly. No
observation was consumed by the refusal, and nothing frozen was modified.

**Lesson for any amendment:** preparation validation must exercise the *real*
destination path length.

---

## 7. An execution finding, not a result

The 64-turn budget was binding on this substrate: **four of the five valid
observations reached 64/64**, and only one finished naturally. One of those four
never ran the visible gate at all before exhausting its turns, and its hidden
functional result was consequently "all semantic cases missing" — the candidate
left non-compiling code because it ran out of budget, not because the oracle
failed.

Across the seven attempted rows the runtime also refused **28 tool calls** under
the frozen §8.1 command allowlist, every one of them a compound shell
construct the allowlist does not admit. Refused attempts consume turns.

Neither observation is a treatment result and neither is offered as one. Both
bear on whether 64 turns is the right budget for a repository of this size, and
an amendment should consider them. Neither the ceiling nor the allowlist was
changed during execution.

---

## 8. What an amendment must decide

1. Whether rows 6 and 7 are replaced at `execution_attempt = 2`, and if so the
   amended plan digest and the §5 linkage records for both attempts.
2. Whether the remaining 11 rows resume under the existing freeze or a re-issued
   one.
3. `TD-N06`: how many infrastructure failures, on how many cells, end an attempt
   rather than produce a replacement.
4. Whether the 64-turn budget stands for this substrate (§7).
5. That preparation validation must exercise real destination path length (§6).

---

## 9. What is unchanged

| Artifact | Value |
| --- | --- |
| Scientific projection SHA-256 | `e8e8f2a3e141b1911d183f2e963ff2c7cd0e106cb7c31a8981ed053ff21f126e` |
| Plan SHA-256 | `4bc65b6112e603b8fb742b1380de06403d95ae7911ae5aa1102b1df09f30ac98` |
| Substrate commit | `f285f6e46ba57d30c5be8448fd018b960d7d4748` |
| Model-visible export tree | `4dfadc101db1c9f29b82934db25def67a93a2563` |
| T1 / T2 / T5 / architecture packet | all four digests unchanged |
| Continuation rule | unchanged, unevaluated |

Model, effort, runtime, permission surface, turn ceiling, visible gate,
functional oracle, architecture scorer, metric definitions and the analysis plan
were not modified at any point during execution.

**Consumed by attempt 1:** 7 model runs, **$10.93** captured provider cost
(\$8.17 across the five valid observations, \$2.75 lost to the two
infrastructure failures), ~5.3 hours of model wall time.
