# SL-V2-EFF-01 — the AFCI efficiency pilot

Status: **Study-Lead decision, PRE-DATA and NON-CONFIRMATORY**. It authorises a
36-observation efficiency pilot, freezes everything that pilot will run under,
and freezes how its output will be read. **Zero efficiency observations exist at
the moment it is written.**

It passes no gate. `G1` is not passed, `G2` is not passed, and `TD-B01`,
`TD-B11`, `TD-B34`, `TD-B32`, `TD-B12`/`G6`, `TD-B03` and `TD-B39` all remain
**OPEN**. The suite is **not** frozen.

Authority: `SL-V2-EFF-01`
Budget authority: [`SL-V2-EFF-RESET-01`](AFCI_EFFICIENCY_PILOT_RESET_BUDGET_DECISION.md)
Checkpoint authority: `SL-V2-EFF-CHK-01` (private evaluator repository)
Committed schedule: [`AFCI_EFFICIENCY_PILOT_RUN_PLAN.json`](AFCI_EFFICIENCY_PILOT_RUN_PLAN.json)

---

## 1. What this pilot asks

**Does supplying the architecture context change what a run costs?**

Not whether it changes what a run *achieves*. The confirmatory construct — does
explicit architecture guidance reduce dependency-direction violations — is `E1`,
it is gated on `G1`/`TD-B34`, and **none of it is touched here.** This pilot
measures tokens, wall-clock, tool calls and exploration, and it measures them on
instruments whose hidden functional acceptance is validated so that a broken run
can be told from an expensive one.

It is a **pilot**: it is powered for nothing, it estimates no effect, and its
output is a GO / QUALIFIED GO / STOP judgement about whether a full-suite
efficiency measurement is worth building. Sections 10–12 freeze that judgement
in advance so it cannot be assembled afterwards from whatever the data happened
to show.

---

## 2. Scope, and the exact matrix

| axis | values | count |
|---|---|---|
| task | `PT01`, `PT04`, `PT07` | 3 |
| condition | `C1`, `C4` | 2 |
| reset state | `NON_RESET`, `RESET` | 2 |
| repetition | `R1`, `R2`, `R3` | 3 |

**3 × 2 × 2 × 3 = 36 substantive observations, maximum.**

The three instruments are the three whose hidden functional acceptance runtimes
are recorded `validated` in
[`TASK_ACCEPTANCE_MATRIX.csv`](TASK_ACCEPTANCE_MATRIX.csv). Validation of the
hidden acceptance is **not** a freeze, is **not** an independent review, and
confers no E1 run-eligibility; it is required here only so that "did the run
work?" is answerable, which is what makes a cost number interpretable.

This is the **first** purpose in the repository to authorise `C4`, and it
authorises it for **cost measurement only**. No architecture score, violation
value, success value, outcome value or treatment-effect estimate is produced,
read or implied by any observation in this pilot.

---

## 3. The run-purpose firewall

### 3.1 The run-purpose firewall table

| field | value |
|---|---|
| `run_purpose` | `AFCI_EFFICIENCY_PILOT` |
| `decision_id` | `SL-V2-EFF-01` |
| `confirmatory` | `false` |
| `confirmatory_eligible` | `false` |
| `enters_confirmatory_dataset` | `false` |
| `enters_confirmatory_e1_analysis` | `false` |
| `enters_treatment_effect_analysis` | `false` |
| `enters_power_estimation` | `false` |
| `is_result` | `false` |
| `scored` | `false` |

The runner derives these five eligibility flags from the purpose and re-checks
them against this table before it writes a record. A record whose flags disagree
is refused rather than written, so a pilot artifact cannot be promoted by editing
it.

### 3.2 Artifact quarantine

Every artifact is written to a scratch root **outside** the canonical
repository, and `experiments/v2/results/` and `experiments/v2/analysis/` are
refused as artifact roots for this purpose. Those two directories contain a
`README.md` each and nothing else, and this decision does not change that.

---

## 4. Repetitions

### 4.1 The repetition table

| field | value |
|---|---|
| `decision_id` | `SL-V2-EFF-01` |
| `diagnostic_repetitions` | `3` |
| `condition` | `C1, C4` |
| `tasks` | `PT01, PT04, PT07` |
| `reset_states` | `NON_RESET, RESET` |
| `process_per_repetition` | `fresh` |
| `session_per_repetition` | `fresh` |
| `resume_permitted` | `false` |
| `continuation_permitted` | `false` |
| `session_reuse_permitted` | `false` |
| `power_claim` | `none` |
| `precision_claim` | `none` |
| `treatment_effect_claim` | `none` |

Three repetitions per cell. **No power calculation justifies the count and none
is implied.** Three is enough to see whether a difference is large and
consistent, and far too few to estimate one.

---

## 5. The frozen execution configuration, and why it changed

### 5.1 The permission finding

Every AFCI-Bench v2 live run executed before this decision — the three `PT08`
difficulty repetitions and the six `PT09`/`PT10` qualification repetitions — ran
with `--permission-mode acceptEdits`, the tool set
`Read,Edit,Write,Glob,Grep,Bash`, and **no permission allowlist**.

Under that configuration, Claude Code 2.1.229 refuses `npm run ci:agent` with
*"This command requires approval"*. Measured across all nine saved artifacts:

| run | `ci:agent` attempts | **executed** |
|---|---|---|
| `PT09` R1 / R2 / R3 | 10 / 3 / 5 | **0 / 0 / 0** |
| `PT10` R1 / R2 / R3 | 3 / 5 / 3 | **0 / 0 / 0** |
| `PT08` R1 / R2 / R3 | 7 / 5 / 3 | **0 / 0 / 0** |

**44 attempts, 0 executions.** The mechanism, read from the installed runtime:
`acceptEdits` auto-approves *edits* and leaves `Bash` to rule evaluation, which
with no matching allow rule returns `behavior: "passthrough"` with the reason
*"This command requires approval"*; in headless mode there is nobody to ask, so
the call is refused. Simple read commands (`ls`, `find`) pass a built-in safe
list, which is why some `Bash` calls did succeed.

### 5.2 What follows from it, for this pilot

The public task bodies name `npm run ci:agent` as the one CI surface the coding
model may see (`TD-B16`). A benchmark that tells a model to validate its work
with a command it is then refused is measuring the refusal. It also makes the
selected reset checkpoint — *the first agent-initiated `npm run ci:agent`
invocation after at least one implementation edit* — fire on a denial rather
than on a validation.

This pilot therefore freezes a **permission allowlist** for exactly that one
command, and for nothing else:

```
--allowed-tools "Bash(npm run ci:agent)" "Bash(npm run ci:agent:*)"
```

Two rules because the runtime matches exact and prefix rules separately. Neither
admits a different command, and neither admits a compound such as
`cd X && npm run ci:agent`, whose parts are each evaluated on their own.

Verified by a quarantined, synthetic infrastructure probe
(`RESET_STREAM_INTERRUPTION_PROBE`, §14): with these rules the command executed
and left its marker file on disk.

### 5.3 What this does NOT do

It does **not** change the `PT08` or `PT09`/`PT10` configurations, which keep
exactly what they ran under. It does **not** re-interpret their outcomes. The
bearing of the finding on those already-executed packages is recorded as an
open decision (`TD-B42`, [`OPEN_DECISIONS.md`](OPEN_DECISIONS.md)) and is
**UNRESOLVED**.

### 5.4 The configuration, stated once

| field | value |
|---|---|
| model | `claude-sonnet-5` (exact id; never the alias) |
| runtime | Claude Code `2.1.229` |
| authentication | subscription OAuth; no API key |
| fallback model | none; `--fallback-model` is refused by the launcher |
| permission mode | `acceptEdits` |
| tools | `Read, Edit, Write, Glob, Grep, Bash` |
| permission allowlist | `Bash(npm run ci:agent)`, `Bash(npm run ci:agent:*)` |
| turn ceiling | `SL-V2-EFF-RESET-01`: 32 / 32 / 64 |
| process per repetition | fresh |
| session per repetition | fresh |
| sterile profile | required, per process |
| context audit | required for **every** process, including reset phase B |

---

## 6. Applicability of the diagnostic-scoped freeze

Six tables, one per (task, condition). They are **not** collapsed to three: `C1`
and `C4` differ in `architecture_delivery`, which is the value a freeze table
exists to pin, and one shared table would certify a delivery that one of the two
arms never received.

Each narrows the **applicability** of the suite-wide `G1` freeze prerequisite
for its own triple and passes no gate.

### 6.1 Applicability table - PT01 / C1

| field | value |
|---|---|
| `decision_id` | `SL-V2-EFF-01` |
| `diagnostic_freeze_authority` | `SL-V2-EFF-01` |
| `run_purpose` | `AFCI_EFFICIENCY_PILOT` |
| `diagnostic_freeze_task` | `PT01` |
| `diagnostic_freeze_condition` | `C1` |
| `diagnostic_freeze_frozen` | `true` |
| `diagnostic_freeze_task_sha256` | `6c938822fe19cd6e87942a6ee24ec8f604c0883da1b7f80d45216be35d7c9c39` |
| `diagnostic_freeze_exact_model_id` | `claude-sonnet-5` |
| `diagnostic_freeze_cli_version` | `2.1.229` |
| `diagnostic_freeze_repetitions` | `3` |
| `diagnostic_freeze_permission_mode` | `acceptEdits` |
| `diagnostic_freeze_authentication` | `claude-code-subscription-oauth` |
| `diagnostic_freeze_model_selector_is_alias` | `false` |
| `diagnostic_freeze_api_key_used` | `false` |
| `diagnostic_freeze_fallback_model_permitted` | `false` |
| `diagnostic_freeze_process_per_repetition` | `fresh` |
| `diagnostic_freeze_session_per_repetition` | `fresh` |
| `diagnostic_freeze_resume_permitted` | `false` |
| `diagnostic_freeze_continuation_permitted` | `false` |
| `diagnostic_freeze_session_reuse_permitted` | `false` |
| `diagnostic_freeze_sterile_context_required` | `true` |
| `diagnostic_freeze_context_audit_required_every_repetition` | `true` |
| `diagnostic_freeze_architecture_delivery` | `none` |
| `diagnostic_freeze_is_result` | `false` |
| `diagnostic_freeze_scored` | `false` |
| `global_g1` | `false` |
| `global_g1_passed_by_this_record` | `false` |
| `suite_frozen` | `false` |
| `global_manifest_frozen` | `false` |
| `global_td_b32_status` | `open` |
| `td_b12_g6_status` | `open` |
| `td_b34_status` | `open` |
| `td_b01_status` | `open` |
| `td_b11_status` | `open` |
| `priority_b_state` | `started; not complete` |
| `td_b03_status` | `open` |

### 6.2 Applicability table - PT01 / C4

| field | value |
|---|---|
| `decision_id` | `SL-V2-EFF-01` |
| `diagnostic_freeze_authority` | `SL-V2-EFF-01` |
| `run_purpose` | `AFCI_EFFICIENCY_PILOT` |
| `diagnostic_freeze_task` | `PT01` |
| `diagnostic_freeze_condition` | `C4` |
| `diagnostic_freeze_frozen` | `true` |
| `diagnostic_freeze_task_sha256` | `6c938822fe19cd6e87942a6ee24ec8f604c0883da1b7f80d45216be35d7c9c39` |
| `diagnostic_freeze_exact_model_id` | `claude-sonnet-5` |
| `diagnostic_freeze_cli_version` | `2.1.229` |
| `diagnostic_freeze_repetitions` | `3` |
| `diagnostic_freeze_permission_mode` | `acceptEdits` |
| `diagnostic_freeze_authentication` | `claude-code-subscription-oauth` |
| `diagnostic_freeze_model_selector_is_alias` | `false` |
| `diagnostic_freeze_api_key_used` | `false` |
| `diagnostic_freeze_fallback_model_permitted` | `false` |
| `diagnostic_freeze_process_per_repetition` | `fresh` |
| `diagnostic_freeze_session_per_repetition` | `fresh` |
| `diagnostic_freeze_resume_permitted` | `false` |
| `diagnostic_freeze_continuation_permitted` | `false` |
| `diagnostic_freeze_session_reuse_permitted` | `false` |
| `diagnostic_freeze_sterile_context_required` | `true` |
| `diagnostic_freeze_context_audit_required_every_repetition` | `true` |
| `diagnostic_freeze_architecture_delivery` | `prompt_injection` |
| `diagnostic_freeze_is_result` | `false` |
| `diagnostic_freeze_scored` | `false` |
| `global_g1` | `false` |
| `global_g1_passed_by_this_record` | `false` |
| `suite_frozen` | `false` |
| `global_manifest_frozen` | `false` |
| `global_td_b32_status` | `open` |
| `td_b12_g6_status` | `open` |
| `td_b34_status` | `open` |
| `td_b01_status` | `open` |
| `td_b11_status` | `open` |
| `priority_b_state` | `started; not complete` |
| `td_b03_status` | `open` |

### 6.3 Applicability table - PT04 / C1

| field | value |
|---|---|
| `decision_id` | `SL-V2-EFF-01` |
| `diagnostic_freeze_authority` | `SL-V2-EFF-01` |
| `run_purpose` | `AFCI_EFFICIENCY_PILOT` |
| `diagnostic_freeze_task` | `PT04` |
| `diagnostic_freeze_condition` | `C1` |
| `diagnostic_freeze_frozen` | `true` |
| `diagnostic_freeze_task_sha256` | `f349b150b1d8fe5676fed8460b1840b988ee2bb0a78b1966ef82ae9ce9c8a9b5` |
| `diagnostic_freeze_exact_model_id` | `claude-sonnet-5` |
| `diagnostic_freeze_cli_version` | `2.1.229` |
| `diagnostic_freeze_repetitions` | `3` |
| `diagnostic_freeze_permission_mode` | `acceptEdits` |
| `diagnostic_freeze_authentication` | `claude-code-subscription-oauth` |
| `diagnostic_freeze_model_selector_is_alias` | `false` |
| `diagnostic_freeze_api_key_used` | `false` |
| `diagnostic_freeze_fallback_model_permitted` | `false` |
| `diagnostic_freeze_process_per_repetition` | `fresh` |
| `diagnostic_freeze_session_per_repetition` | `fresh` |
| `diagnostic_freeze_resume_permitted` | `false` |
| `diagnostic_freeze_continuation_permitted` | `false` |
| `diagnostic_freeze_session_reuse_permitted` | `false` |
| `diagnostic_freeze_sterile_context_required` | `true` |
| `diagnostic_freeze_context_audit_required_every_repetition` | `true` |
| `diagnostic_freeze_architecture_delivery` | `none` |
| `diagnostic_freeze_is_result` | `false` |
| `diagnostic_freeze_scored` | `false` |
| `global_g1` | `false` |
| `global_g1_passed_by_this_record` | `false` |
| `suite_frozen` | `false` |
| `global_manifest_frozen` | `false` |
| `global_td_b32_status` | `open` |
| `td_b12_g6_status` | `open` |
| `td_b34_status` | `open` |
| `td_b01_status` | `open` |
| `td_b11_status` | `open` |
| `priority_b_state` | `started; not complete` |
| `td_b03_status` | `open` |

### 6.4 Applicability table - PT04 / C4

| field | value |
|---|---|
| `decision_id` | `SL-V2-EFF-01` |
| `diagnostic_freeze_authority` | `SL-V2-EFF-01` |
| `run_purpose` | `AFCI_EFFICIENCY_PILOT` |
| `diagnostic_freeze_task` | `PT04` |
| `diagnostic_freeze_condition` | `C4` |
| `diagnostic_freeze_frozen` | `true` |
| `diagnostic_freeze_task_sha256` | `f349b150b1d8fe5676fed8460b1840b988ee2bb0a78b1966ef82ae9ce9c8a9b5` |
| `diagnostic_freeze_exact_model_id` | `claude-sonnet-5` |
| `diagnostic_freeze_cli_version` | `2.1.229` |
| `diagnostic_freeze_repetitions` | `3` |
| `diagnostic_freeze_permission_mode` | `acceptEdits` |
| `diagnostic_freeze_authentication` | `claude-code-subscription-oauth` |
| `diagnostic_freeze_model_selector_is_alias` | `false` |
| `diagnostic_freeze_api_key_used` | `false` |
| `diagnostic_freeze_fallback_model_permitted` | `false` |
| `diagnostic_freeze_process_per_repetition` | `fresh` |
| `diagnostic_freeze_session_per_repetition` | `fresh` |
| `diagnostic_freeze_resume_permitted` | `false` |
| `diagnostic_freeze_continuation_permitted` | `false` |
| `diagnostic_freeze_session_reuse_permitted` | `false` |
| `diagnostic_freeze_sterile_context_required` | `true` |
| `diagnostic_freeze_context_audit_required_every_repetition` | `true` |
| `diagnostic_freeze_architecture_delivery` | `prompt_injection` |
| `diagnostic_freeze_is_result` | `false` |
| `diagnostic_freeze_scored` | `false` |
| `global_g1` | `false` |
| `global_g1_passed_by_this_record` | `false` |
| `suite_frozen` | `false` |
| `global_manifest_frozen` | `false` |
| `global_td_b32_status` | `open` |
| `td_b12_g6_status` | `open` |
| `td_b34_status` | `open` |
| `td_b01_status` | `open` |
| `td_b11_status` | `open` |
| `priority_b_state` | `started; not complete` |
| `td_b03_status` | `open` |

### 6.5 Applicability table - PT07 / C1

| field | value |
|---|---|
| `decision_id` | `SL-V2-EFF-01` |
| `diagnostic_freeze_authority` | `SL-V2-EFF-01` |
| `run_purpose` | `AFCI_EFFICIENCY_PILOT` |
| `diagnostic_freeze_task` | `PT07` |
| `diagnostic_freeze_condition` | `C1` |
| `diagnostic_freeze_frozen` | `true` |
| `diagnostic_freeze_task_sha256` | `557caed09420354efbc823c8b72e54b0760ac72847aba0d9c07d99e37ff7d2d7` |
| `diagnostic_freeze_exact_model_id` | `claude-sonnet-5` |
| `diagnostic_freeze_cli_version` | `2.1.229` |
| `diagnostic_freeze_repetitions` | `3` |
| `diagnostic_freeze_permission_mode` | `acceptEdits` |
| `diagnostic_freeze_authentication` | `claude-code-subscription-oauth` |
| `diagnostic_freeze_model_selector_is_alias` | `false` |
| `diagnostic_freeze_api_key_used` | `false` |
| `diagnostic_freeze_fallback_model_permitted` | `false` |
| `diagnostic_freeze_process_per_repetition` | `fresh` |
| `diagnostic_freeze_session_per_repetition` | `fresh` |
| `diagnostic_freeze_resume_permitted` | `false` |
| `diagnostic_freeze_continuation_permitted` | `false` |
| `diagnostic_freeze_session_reuse_permitted` | `false` |
| `diagnostic_freeze_sterile_context_required` | `true` |
| `diagnostic_freeze_context_audit_required_every_repetition` | `true` |
| `diagnostic_freeze_architecture_delivery` | `none` |
| `diagnostic_freeze_is_result` | `false` |
| `diagnostic_freeze_scored` | `false` |
| `global_g1` | `false` |
| `global_g1_passed_by_this_record` | `false` |
| `suite_frozen` | `false` |
| `global_manifest_frozen` | `false` |
| `global_td_b32_status` | `open` |
| `td_b12_g6_status` | `open` |
| `td_b34_status` | `open` |
| `td_b01_status` | `open` |
| `td_b11_status` | `open` |
| `priority_b_state` | `started; not complete` |
| `td_b03_status` | `open` |

### 6.6 Applicability table - PT07 / C4

| field | value |
|---|---|
| `decision_id` | `SL-V2-EFF-01` |
| `diagnostic_freeze_authority` | `SL-V2-EFF-01` |
| `run_purpose` | `AFCI_EFFICIENCY_PILOT` |
| `diagnostic_freeze_task` | `PT07` |
| `diagnostic_freeze_condition` | `C4` |
| `diagnostic_freeze_frozen` | `true` |
| `diagnostic_freeze_task_sha256` | `557caed09420354efbc823c8b72e54b0760ac72847aba0d9c07d99e37ff7d2d7` |
| `diagnostic_freeze_exact_model_id` | `claude-sonnet-5` |
| `diagnostic_freeze_cli_version` | `2.1.229` |
| `diagnostic_freeze_repetitions` | `3` |
| `diagnostic_freeze_permission_mode` | `acceptEdits` |
| `diagnostic_freeze_authentication` | `claude-code-subscription-oauth` |
| `diagnostic_freeze_model_selector_is_alias` | `false` |
| `diagnostic_freeze_api_key_used` | `false` |
| `diagnostic_freeze_fallback_model_permitted` | `false` |
| `diagnostic_freeze_process_per_repetition` | `fresh` |
| `diagnostic_freeze_session_per_repetition` | `fresh` |
| `diagnostic_freeze_resume_permitted` | `false` |
| `diagnostic_freeze_continuation_permitted` | `false` |
| `diagnostic_freeze_session_reuse_permitted` | `false` |
| `diagnostic_freeze_sterile_context_required` | `true` |
| `diagnostic_freeze_context_audit_required_every_repetition` | `true` |
| `diagnostic_freeze_architecture_delivery` | `prompt_injection` |
| `diagnostic_freeze_is_result` | `false` |
| `diagnostic_freeze_scored` | `false` |
| `global_g1` | `false` |
| `global_g1_passed_by_this_record` | `false` |
| `suite_frozen` | `false` |
| `global_manifest_frozen` | `false` |
| `global_td_b32_status` | `open` |
| `td_b12_g6_status` | `open` |
| `td_b34_status` | `open` |
| `td_b01_status` | `open` |
| `td_b11_status` | `open` |
| `priority_b_state` | `started; not complete` |
| `td_b03_status` | `open` |

---

## 7. The frozen execution configuration, per cell

Six tables, matching §6 one for one.

### 7.1 Frozen execution configuration - PT01 / C1

| field | value |
|---|---|
| `exact_model_id` | `claude-sonnet-5` |
| `cli_version` | `2.1.229` |
| `permission_mode` | `acceptEdits` |
| `tools` | `Read, Edit, Write, Glob, Grep, Bash` |
| `allowed_tools` | `Bash(npm run ci:agent)`, `Bash(npm run ci:agent:*)` |
| `architecture_delivery` | `none` |
| `non_reset_max_turns` | `64` |
| `pre_reset_max_turns` | `32` |
| `post_reset_max_turns` | `32` |

### 7.2 Frozen execution configuration - PT01 / C4

| field | value |
|---|---|
| `exact_model_id` | `claude-sonnet-5` |
| `cli_version` | `2.1.229` |
| `permission_mode` | `acceptEdits` |
| `tools` | `Read, Edit, Write, Glob, Grep, Bash` |
| `allowed_tools` | `Bash(npm run ci:agent)`, `Bash(npm run ci:agent:*)` |
| `architecture_delivery` | `prompt_injection` |
| `architecture_sha256` | `bf6f32b162a23b851596d8b489d938bef10d0b8616a50dcc039873d12ffa7a4d` |
| `non_reset_max_turns` | `64` |
| `pre_reset_max_turns` | `32` |
| `post_reset_max_turns` | `32` |

### 7.3 Frozen execution configuration - PT04 / C1

| field | value |
|---|---|
| `exact_model_id` | `claude-sonnet-5` |
| `cli_version` | `2.1.229` |
| `permission_mode` | `acceptEdits` |
| `tools` | `Read, Edit, Write, Glob, Grep, Bash` |
| `allowed_tools` | `Bash(npm run ci:agent)`, `Bash(npm run ci:agent:*)` |
| `architecture_delivery` | `none` |
| `non_reset_max_turns` | `64` |
| `pre_reset_max_turns` | `32` |
| `post_reset_max_turns` | `32` |

### 7.4 Frozen execution configuration - PT04 / C4

| field | value |
|---|---|
| `exact_model_id` | `claude-sonnet-5` |
| `cli_version` | `2.1.229` |
| `permission_mode` | `acceptEdits` |
| `tools` | `Read, Edit, Write, Glob, Grep, Bash` |
| `allowed_tools` | `Bash(npm run ci:agent)`, `Bash(npm run ci:agent:*)` |
| `architecture_delivery` | `prompt_injection` |
| `architecture_sha256` | `bf6f32b162a23b851596d8b489d938bef10d0b8616a50dcc039873d12ffa7a4d` |
| `non_reset_max_turns` | `64` |
| `pre_reset_max_turns` | `32` |
| `post_reset_max_turns` | `32` |

### 7.5 Frozen execution configuration - PT07 / C1

| field | value |
|---|---|
| `exact_model_id` | `claude-sonnet-5` |
| `cli_version` | `2.1.229` |
| `permission_mode` | `acceptEdits` |
| `tools` | `Read, Edit, Write, Glob, Grep, Bash` |
| `allowed_tools` | `Bash(npm run ci:agent)`, `Bash(npm run ci:agent:*)` |
| `architecture_delivery` | `none` |
| `non_reset_max_turns` | `64` |
| `pre_reset_max_turns` | `32` |
| `post_reset_max_turns` | `32` |

### 7.6 Frozen execution configuration - PT07 / C4

| field | value |
|---|---|
| `exact_model_id` | `claude-sonnet-5` |
| `cli_version` | `2.1.229` |
| `permission_mode` | `acceptEdits` |
| `tools` | `Read, Edit, Write, Glob, Grep, Bash` |
| `allowed_tools` | `Bash(npm run ci:agent)`, `Bash(npm run ci:agent:*)` |
| `architecture_delivery` | `prompt_injection` |
| `architecture_sha256` | `bf6f32b162a23b851596d8b489d938bef10d0b8616a50dcc039873d12ffa7a4d` |
| `non_reset_max_turns` | `64` |
| `pre_reset_max_turns` | `32` |
| `post_reset_max_turns` | `32` |

---

## 8. The reset, and the checkpoint

The reset procedure is `RESET_PROTOCOL.md` §2, executed rather than described.
The checkpoint predicate was selected pre-data by `SL-V2-EFF-CHK-01`, which
chose among predicates that **already existed** and authored, rewrote and
relaxed none. All three instruments use the same one:

> The first agent-initiated `npm run ci:agent` invocation after at least one
> implementation edit to the working tree.

| field | value |
|---|---|
| `checkpoint_id` | `CK-EFF-FALLBACK-CI-AGENT-AFTER-EDIT` |
| `checkpoint_authority` | `SL-V2-EFF-CHK-01` |
| `checkpoint_hash` | `a48922c9262047e7d2e05c4c6b483b326f21a4d2df8c6d51d59c9d3eed511e46` |
| detected from | structured tool events only |
| identical across `C1`/`C4` | `true` |

**The stop waits for the tool RESULT, not the tool request.** Stopping when the
`Bash` call is merely issued would terminate the process while `npm` and its
children were mid-flight, and the "partially modified repository" the reset
preserves would then be partly the work of an interrupted build. The checkpoint
becomes true when the matching invocation has **completed and returned its
result**.

A *failing* `ci:agent` still closes the checkpoint. The predicate is about the
invocation, not its verdict; making it conditional on success would make the
stop point depend on how well the work was going, which is the treatment.

The detector cannot read the architecture score, the hidden functional result,
model prose, or the condition. It is handed none of them and has nowhere to put
them.

### 8.1 Checkpoint not reached

If phase A exhausts its 32 turns without the predicate becoming true, the
observation is recorded as **`RESET_CHECKPOINT_NOT_REACHED`**. That is a
substantive pilot observation.

**No phase B is fabricated. No rerun is scheduled. No budget is raised. No
alternate checkpoint is substituted.** A pilot that retried until it got a reset
would be reporting its retries.

---

## 9. What is measured

### 9.1 Tokens

```
TOTAL_INPUT_TOKENS = usage.input_tokens
                   + usage.cache_creation_input_tokens
                   + usage.cache_read_input_tokens
```

The three are **non-overlapping**, which is what makes the sum a total.
`usage.cache_creation.ephemeral_1h_input_tokens` and
`ephemeral_5m_input_tokens` are a **breakdown of**
`cache_creation_input_tokens` and are **never added on top** — verified on all
nine live artifacts, where the two subcomponents sum exactly to the parent.

MAD tokens count. Cached MAD tokens count. Task tokens count. Every subsequent
interaction token counts. Excluding the payload would be excluding the treatment.

`TOTAL_OUTPUT_TOKENS` is `usage.output_tokens`. Cost is
`modelUsage["claude-sonnet-5"].costUSD`.

For a `RESET` run the two phases are aggregated, and the per-phase figures are
preserved alongside so the recovery question — what did phase B have to redo? —
stays answerable.

### 9.2 A limitation, recorded rather than smoothed over

A reset's phase A is interrupted at the checkpoint and therefore **never emits a
terminal `result` event**. Measured against the saved artifacts:

* all three **input** categories reconstruct **exactly** from the streamed
  per-message `usage` blocks — delta 0 on every artifact checked;
* `output_tokens` does **not**: the streamed value is the figure at message
  start, and summing it recovers 1–2% of the terminal total.

So a `RESET` run has an exact `TOTAL_INPUT_TOKENS` — the primary endpoint — and
**no** `TOTAL_OUTPUT_TOKENS`. The output figure is recorded as *unavailable*,
never as the partial sum and never as zero. The `TOTAL_OUTPUT_TOKENS` secondary
comparison is therefore available for the nine `NON_RESET` blocks only, and
§11 says so.

### 9.3 Tools and exploration

Derived from structured events only; model prose is never parsed.

`TOTAL_TOOL_CALLS`, `READ_CALLS`, `GREP_CALLS`, `GLOB_CALLS`, `BASH_CALLS`,
`EDIT_CALLS`, `WRITE_CALLS`, and

```
EXPLORATION_CALLS = READ_CALLS + GREP_CALLS + GLOB_CALLS
```

plus `UNIQUE_FILES_READ`, `UNIQUE_FILES_MODIFIED`,
`UNIQUE_DIRECTORIES_EXPLORED`, `REPEATED_FILE_READS`, `FILES_REEDITED`,
`TEST_COMMAND_RUNS`, `CI_COMMAND_RUNS`, `FAILED_TEST_OR_CI_CYCLES`.

Windows paths are normalised to one spelling per file, so the same file typed
three ways counts once.

### 9.4 Timing

Monotonic clocks, taken by the runner.

* `MODEL_WALL_SECONDS` — `NON_RESET`: spawn to termination. `RESET`: phase A
  model duration **plus** phase B model duration.
* `RESET_HANDOFF_SECONDS` — recorded **separately** and **never** inside
  `MODEL_WALL_SECONDS`. The handoff is harness work; charging it to the model
  would make the reset arm look slower by an amount that depends on how fast
  this harness is.
* `TOTAL_RUN_SECONDS`, `EVALUATION_SECONDS`.

### 9.5 Turns

`TURNS_USED` is the count of distinct assistant message ids, **not**
`result.num_turns`. That field means two different things: on a `success` result
it counts user messages, and on an `error_max_turns` result it is
`max_turns + 1` — observed exactly, `num_turns: 2` against a single model
request under `--max-turns 1`. Either would be wrong in one of the two cases.

---

## 10. The frozen analysis

**No p-values. No confidence intervals. No confirmatory effect claim.** A pilot
of three repetitions supports none of them, and producing one would invite
exactly the reading the firewall exists to prevent.

### 10.1 Pairing

A **block** is (task × reset state × repetition): 18 of them, each holding one
`C1` and one `C4` run that differ in the condition and in nothing else.

A pair is **eligible** only if **both** of its runs are functionally valid. A
cost figure from a run that did not work is not a cheaper way of doing the task.

### 10.2 The primary endpoint

```
TOKEN_RATIO = C4 TOTAL_INPUT_TOKENS / C1 TOTAL_INPUT_TOKENS
```

Lower is better for `C4`.

### 10.3 Secondary paired ratios

Same pairing, same direction:

`MODEL_WALL_SECONDS`, `TOTAL_TOOL_CALLS`, `EXPLORATION_CALLS`,
`UNIQUE_FILES_READ`, `TOTAL_OUTPUT_TOKENS` (`NON_RESET` blocks only, §9.2),
`EDIT_CALLS + WRITE_CALLS`, `TEST_COMMAND_RUNS`, `CI_COMMAND_RUNS`.

### 10.4 Reset recovery

For each (task × repetition × condition):

```
RESET_OVERHEAD_RATIO = RESET / NON_RESET
```

for `TOTAL_INPUT_TOKENS`, `MODEL_WALL_SECONDS`, `EXPLORATION_CALLS` and
`TOTAL_TOOL_CALLS`.

---

## 11. The frozen decision rule

Frozen **before** any observation exists. Evaluated in order; the first that
matches is the outcome.

### 11.0 The minimum

**At least 12 of the 18 blocks must have both conditions functionally valid.**

Otherwise the outcome is:

> **PILOT INCONCLUSIVE — INSUFFICIENT PAIRED FUNCTIONAL DATA**

and no efficiency claim of any kind is made.

### 11.1 STRONG GO — all five

1. ≥ 12 eligible pairs;
2. the `C4` functional-valid count is no more than 1 lower than `C1`'s;
3. overall median `TOKEN_RATIO` ≤ **0.90**;
4. `C4` uses fewer tokens in ≥ **60%** of eligible pairs;
5. ≥ **2 of 3** tasks have a task-median `TOKEN_RATIO` < 1.

### 11.2 QUALIFIED GO — STRONG GO fails and all five

1. ≥ 12 eligible pairs;
2. the `C4` functional-valid count is no more than 1 lower than `C1`'s;
3. overall median `TOKEN_RATIO` ≤ **1.10**;
4. at least one of:
   - `MODEL_WALL_SECONDS` ratio ≤ **0.85**
   - `EXPLORATION_CALLS` ratio ≤ **0.75**
   - `TOTAL_TOOL_CALLS` ratio ≤ **0.80**
5. the qualifying endpoint improves directionally in ≥ **2 of 3** tasks.

### 11.3 RESET-SPECIFIC GO — neither above and all four

1. the functional guardrail (11.1 condition 2) holds;
2. overall `TOKEN_RATIO` ≤ **1.10**;
3. `C4` has lower token reset-overhead than `C1` in ≥ **2 of 3** tasks;
4. `C4` has lower reset overhead for `MODEL_WALL_SECONDS` **or**
   `EXPLORATION_CALLS` in ≥ **2 of 3** tasks.

### 11.4 Otherwise

> **STOP — NO EFFICIENCY SIGNAL JUSTIFIES FULL-SUITE EXPANSION**

---

## 12. The run schedule

Deterministic, committed, and generated before any run:

| field | value |
|---|---|
| seed | `AFCI_EFFICIENCY_PILOT_V1_20260914` |
| blocks | 18 |
| runs | 36 |
| ordering | sort by SHA-256 of a seeded string; no language RNG |
| file | [`AFCI_EFFICIENCY_PILOT_RUN_PLAN.json`](AFCI_EFFICIENCY_PILOT_RUN_PLAN.json) |
| sha256 | `0038cd8b563ea804f4887d21cb37ceddb3a8f7632c4dd2315c260d3a9af95767` |

Condition order **within** each block and the order **of** the blocks are both
randomised deterministically, so a drift over the execution session cannot land
systematically on one arm and the tasks are interleaved rather than run in three
homogeneous stretches.

No run in this schedule has been executed.

---

## 12a. The pilot is FROZEN but NOT YET RUN-ELIGIBLE

**This section records the state AT FREEZE TIME and is preserved exactly as
adjudicated. §12b records what has changed since, and the two are read
together.** Nothing in §12b edits a value in this section.

Everything above is frozen. The pilot still **cannot execute**, and the reason
is recorded here rather than discovered by whoever tries.

`check_readiness` reports, for all six (task, condition) cells:

| blocker | PT01 | PT04 | PT07 |
|---|---|---|---|
| `PRIVATE_PUBLIC_SYNC_PROPAGATION_REQUIRED_BEFORE_FREEZE` | **BLOCKED** | **BLOCKED** | **BLOCKED** |
| `ARCHITECTURE_CORPUS_NOT_AVAILABLE` | **BLOCKED** | **BLOCKED** | pass |
| `CONTEXT_AUDIT_UNKNOWN` | see below | see below | see below |

**The public-sync propagation.** The private package record must state that a
public accounting synchronization has been propagated before a task may be
frozen — *scoped or otherwise*, which is exactly what §6 does. `PT08`, `PT09`
and `PT10` carry that record and are `SATISFIED`. `PT01` and `PT04` have **no
package record at all**; `PT07` has one that **carries no
`public_synchronisation_required_before_freeze` entry**.

**The architecture corpus.** `PT01` and `PT04` have no private
`<task>_corpus.py`. `PT07`, `PT08` and the qualification pair do. Whether a
COST-ONLY purpose — which produces no architecture score, violation value or
E1 contribution — needs the architecture-oracle validation corpus at all is a
reasonable question, and it is **not answered here**. This record does not
weaken a prerequisite so that its own pilot passes.

**The context verdict is not in this list.** A readiness report has not run the
audit and truthfully reports it as not demonstrated; `CONTEXT_AUDIT` runs it
moments later and refuses on anything but `CLEAN`. A dry run of `PT01`/`C4`
with a governed sterile profile returns **CLEAN** and completes every state.

**The runner now refuses rather than spending.** A real run whose own readiness
report carries any blocker other than the context verdict is refused in
`PRECHECK`, before a process could be created. That closed a fail-OPEN: the
report was computed, written to `readiness.json`, recorded in
`prerequisite_blockers` — and then not acted on. It never mattered, because
every purpose executed so far had its prerequisites met. That was luck, not a
control.

**Operational note.** The artifact root must be **outside the operator's home
directory**. The context audit scans the workspace's ancestors, so a run rooted
under `~` finds the developer's own `~/.claude` and is correctly reported
`CONTAMINATED`. The executed diagnostics used `D:\pt08-diagnostic` and
`D:\afci-v2-qual` for this reason.

---

## 12b. What has changed since §12a, recorded beside it

§12a listed two blockers. Both have since been discharged, each in the way its
own record required, and **zero efficiency observations exist at the moment this
is written** — the same state §12a was written in.

| §12a blocker | state now | how |
|---|---|---|
| `PRIVATE_PUBLIC_SYNC_PROPAGATION_REQUIRED_BEFORE_FREEZE` | **DISCHARGED** | by **propagation**, not by adjudication. The private packages for all three instruments now carry the canonical `<task>_package_record.json` with `public_synchronisation_required_before_freeze` = `SATISFIED`, each citing the exact public commit it verified and each bound to the approved public task hash. The public readiness check independently verifies that the cited commit is an ancestor of public `HEAD`. |
| `ARCHITECTURE_CORPUS_NOT_AVAILABLE` | **NOT APPLICABLE to this purpose** | by [`SL-V2-EFF-ELIG-01`](AFCI_EFFICIENCY_PILOT_ELIGIBILITY_DECISION.md), a separate Study-Lead decision taken on the question §12a explicitly left open. It is reported `N/A` and never `PASS`: the corpus does not exist for two of the three instruments, and the requirement is **UNCHANGED and REQUIRED in full** for every purpose it already applied to, including every confirmatory and result-bearing one. |

The third line of §12a's table — the context verdict — is unchanged and was
never a blocker of this kind: a readiness report has not run the audit, and
`CONTEXT_AUDIT` runs it moments later and refuses on anything but `CLEAN`.

`SL-V2-EFF-ELIG-01` passes no gate, closes no `TD` row, changes no `E1`
admission, makes none of these tasks confirmatory, and changes **nothing** this
record froze: not the task bodies, not the MAD, not the checkpoints, not the
reset budgets, not the permission rules, not the metrics, not the decision
thresholds, not the run schedule and not the model or runtime.

**Nothing in §1–§12 of this record is edited by any of the above.**

---

## 13. What this decision does NOT do

| | status after this record |
|---|---|
| gate `G1` | **NOT PASSED** |
| gate `G2` | **NOT PASSED** |
| `TD-B01` (pre-reset allowance) | **OPEN** |
| `TD-B11` (total budget) | **OPEN** |
| `TD-B34` (qualification) | **OPEN** |
| `TD-B32` (global) | **OPEN** |
| `TD-B12` / `G6` | **OPEN** |
| `TD-B03` (primary model) | **OPEN**; `primary_model: null` |
| `TD-B39` | **OPEN** |
| `TD-B42` (the permission finding, §5) | **OPEN** |
| suite freeze | **false** |
| E1 register | **UNCHANGED** |
| any task manifest | **NOT FROZEN** |
| independent review | **NOT OBTAINED AND NOT CLAIMED** |

No result, violation value, success value, outcome value or treatment-effect
estimate exists, and none is created by executing this pilot.

---

## 14. The infrastructure probes

Two quarantined, synthetic, infrastructure-only live probes were executed while
building this package. **Neither is a pilot observation**, neither used an AFCI
task, neither used the MAD, neither carried a run purpose, and both ran in
disposable directories outside both repositories.

| probe | what it established |
|---|---|
| `RESET_BUDGET_SEMANTICS_PROBE` | `--max-turns 1` permits exactly 1 agentic turn; terminal `result` carries `subtype: error_max_turns`, `is_error: true`, `num_turns: 2`; exit status 1; the turn's file write survives. |
| `RESET_STREAM_INTERRUPTION_PROBE` | `Bash(npm run ci:agent)` allow rules permit the command; events stream incrementally; the checkpoint fires on the tool **result** (index 23) not the tool **use** (index 20); the process stops by `CTRL_BREAK_PROCESS_GROUP` with no escalation; the edit and the completed command's marker file both survive; all 24 events are preserved on disk. |

Efficiency-pilot observations at the time of writing: **ZERO**.
