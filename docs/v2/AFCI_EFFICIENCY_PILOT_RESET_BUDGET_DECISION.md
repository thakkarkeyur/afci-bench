# SL-V2-EFF-RESET-01 — the pilot-scoped reset turn budget

Status: **Study-Lead decision, PRE-DATA and PILOT-SCOPED**. It freezes three
numbers for the `AFCI_EFFICIENCY_PILOT` run purpose and nothing else. It passes
no gate, resolves no global open decision, scores nothing, and produces no
result. **Zero efficiency observations exist at the moment it is written, and
that is the point of writing it now.**

Authority: `SL-V2-EFF-RESET-01`
Scope: `AFCI_EFFICIENCY_PILOT` only
Machine-readable companion:
[`experiments/v2/harness/reset_budget.py`](../../experiments/v2/harness/reset_budget.py)
(the harness re-derives §4.1 from this file and refuses on any drift)

---

## 1. What is being decided, and nothing wider

A two-phase reset run cannot be executed at all until somebody says how much
room each phase gets. This record says that, for one non-confirmatory pilot.

It decides **three integers**. It does not decide what a turn is worth, what a
confirmatory run should be allowed, how allowances should be expressed for the
suite, or whether any of this should be reused. Those are `TD-B01`, `TD-B11`
and `G2`, and all three are **OPEN and unchanged** by this record.

The decision is recorded **before** the pilot runs because a budget chosen after
seeing how runs went is a budget chosen to make them look a particular way.

---

## 2. Why the allowance is expressed in agentic turns

Three candidate ceilings exist: wall-clock, USD, and turns.

**Wall-clock is not a budget, it is a symptom.** The same amount of work takes
different times on a loaded machine, and a wall-clock ceiling would therefore
make the measured quantity partly a property of the host. Wall-clock is
recorded as an *observation* (`MODEL_WALL_SECONDS`), never used as a ceiling.

**USD would make the ceiling a function of the thing being measured.** The
pilot's primary endpoint is token consumption. Capping the run on spend caps it
on a monotone function of the endpoint, so a condition that used fewer tokens
would get more room to keep going — which is precisely the confound the pilot
exists to avoid.

**Turns are enforced by construction.** The installed runtime imposes the
ceiling inside its own agent loop and does so deterministically. §3 records
exactly how, from the implementation rather than from the help text.

---

## 3. The `--max-turns` semantics this budget relies on

Established by reading the **installed Claude Code 2.1.229 implementation** on
the reference machine (`~/.local/share/claude/versions/2.1.229`, a single
307,186,848-byte native binary with the runtime's JavaScript embedded). No live
model call was spent to establish any of it.

| Question | Answer, and where it comes from |
|---|---|
| Is the flag accepted? | Yes. Registered as `--max-turns <turns>`, described as *"Maximum number of agentic turns in non-interactive mode. This will early exit the conversation after the specified number of turns. (only works with --print)"*. Every launch this harness builds carries `-p`. |
| What is one turn? | One iteration of the agent loop: one assistant model request, plus the execution of the tool calls that request made, plus the collection of their results. The loop initialises its counter to `1` and recurses with the completed turn's index. |
| Where is the ceiling checked? | **After** the turn's tools have executed and their results have been gathered, and **before** the next model request is issued. The loop computes `completed = turnCount + 1` and stops when `completed > maxTurns`. |
| So how many model requests does `--max-turns N` permit? | Exactly `N`. The counter starts at 1, so the stop fires on the completion of turn `N`, and request `N+1` is never issued. |
| Does it apply to the autonomous loop? | Yes — it is enforced on the tool-use continuation path, and separately on the stop-hook-blocking and aborted-tools paths, all inside the same loop. It is a **ceiling, not a target**: a run that finishes early returns `success` and never reaches it. |
| What is emitted when it fires? | The loop emits an internal `max_turns_reached` attachment carrying `{turnCount, maxTurns}`. The headless translator **consumes** that attachment rather than forwarding it, and converts it into the terminal `result` event. |
| What does the stream actually carry? | A terminal `result` event with `subtype: "error_max_turns"`, `is_error: true`, `errors: ["Reached maximum number of turns (N)"]`, plus `num_turns`, `duration_ms`, `duration_api_ms`, `stop_reason`, `session_id`, `total_cost_usd`, `usage`, `modelUsage` and `permission_denials`. **There is no `max_turns_reached` event on the wire** and a detector must not look for one. |
| What is `num_turns` on that event? | `maxTurns + 1` — the index of the turn whose *completion* triggered the stop. It is **not** the number of model requests made, which is `maxTurns`. The two are recorded separately and `num_turns` is never used as the turns-used metric. |
| How does the process exit? | Cleanly, with exit status **1**. The headless entry point ends with `exit(result.is_error ? 1 : 0)`, so any `is_error` result — including this one — exits 1 after the complete stream has been written. A reset run must therefore **not** read exit 1 with a terminal `error_max_turns` result as a process failure. |
| Do completed tool effects survive? | Yes. The ceiling is evaluated after tool execution completes; the loop returns, and there is no rollback, revert or discard path on that return. Files written by turns `1..N` are on disk when the process exits. |

**Conclusion recorded as a finding, not an assumption:** `--max-turns`
enforces a deterministic ceiling of exactly N agentic turns, signals it with a
first-class structured event, exits cleanly, and preserves completed work.

---

## 4. The frozen budget

### 4.1 The frozen turn-budget table

| field | value |
|---|---|
| `decision_id` | `SL-V2-EFF-RESET-01` |
| `run_purpose` | `AFCI_EFFICIENCY_PILOT` |
| `scope` | `AFCI_EFFICIENCY_PILOT ONLY` |
| `pre_reset_max_turns` | `32` |
| `post_reset_max_turns` | `32` |
| `non_reset_max_turns` | `64` |
| `total_allowance_reset` | `64` |
| `total_allowance_non_reset` | `64` |
| `allowances_identical_across_conditions` | `true` |
| `unused_pre_reset_transfers` | `false` |
| `post_reset_depends_on_phase_a_consumption` | `false` |
| `td_b01_resolved_globally` | `false` |
| `td_b11_resolved_globally` | `false` |
| `g2_passed` | `false` |
| `confirmatory_precedent_created` | `false` |
| `decided_before_any_efficiency_observation` | `true` |

### 4.2 What the numbers mean

- A `RESET` run's phase A may make at most **32** model requests.
- A `RESET` run's phase B may make at most **32** model requests, **whatever
  phase A consumed**. A phase A that stopped at turn 3 does not hand 29 turns
  forward, and a phase A that exhausted all 32 does not shrink phase B.
- A `NON_RESET` run's single process may make at most **64** model requests.
- `32 + 32 = 64`. A reset run and a non-reset run of the same
  (task, condition, repetition) therefore receive an **identical total
  allowance**, which is what `RESET_PROTOCOL.md` §3 requires so that a
  robustness difference cannot be a budget artifact.
- `C1` and `C4` receive **exactly identical** limits. The reset never grants one
  condition more room to recover than the other.

### 4.3 Why 32, stated as a judgement

32 is a judgement, not a derivation, and nothing in this repository pretends
otherwise. It is large enough that a phase-A run reaches the selected checkpoint
— one `npm run ci:agent` after at least one implementation edit — with room to
spare in every shape of run the executed PT08/PT09/PT10 diagnostics produced,
and small enough that a run which never reaches the checkpoint terminates rather
than consuming a budget on a loop.

**No efficiency observation informed the choice, because none exists.** If the
pilot shows 32 was wrong, that is a finding about the pilot, and correcting it is
a new decision — not a re-reading of this one.

---

## 5. What this record explicitly does NOT do

| Not decided here | Status after this record |
|---|---|
| the confirmatory pre-reset allowance | `TD-B01` **OPEN** |
| the confirmatory total budget | `TD-B11` **OPEN** |
| benchmark discrimination | `G2` **NOT PASSED** |
| oracle validity | `G1` **NOT PASSED** |
| whether the pilot runs at all | `SL-V2-EFF-01`, a separate decision |
| the checkpoint predicate | `SL-V2-EFF-CHK-01`, already recorded, unchanged |
| any suite-wide freeze | `suite_frozen` stays **false** |
| the primary model selection | `TD-B03` **OPEN**, `primary_model: null` |

This record creates **no precedent** for the confirmatory reset protocol. It is
bounded to the `AFCI_EFFICIENCY_PILOT` and expires with it.

---

## 6. Relationship to the already-recorded checkpoint selection

`SL-V2-EFF-CHK-01` selected, pre-data, which already-authored checkpoint
predicate the pilot uses for `PT01`, `PT04` and `PT07`. That record explicitly
stated that **no reset turn budget, pre-reset allowance or post-reset allowance
was selected, frozen or implied** by it, and left them as unresolved
placeholders. This record fills exactly those placeholders, for exactly that
pilot, and changes nothing about the predicate selection itself.
