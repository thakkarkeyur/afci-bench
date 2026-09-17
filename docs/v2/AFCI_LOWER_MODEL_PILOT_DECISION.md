# SL-V2-LOWER-MODEL-01 — the lower-capability-model AFCI pilot

Status: **Study-Lead decision, PRE-DATA and NON-CONFIRMATORY**. It authorises an
18-observation pilot under a lower-capability coding model, freezes everything
that pilot will run under, and freezes how its output will be read. **Zero
lower-model observations exist at the moment it is written.**

It passes no gate. `G1` is not passed, `G2` is not passed, and `TD-B01`,
`TD-B11`, `TD-B34`, `TD-B32`, `TD-B12`/`G6`, `TD-B03`, `TD-B39` and `TD-B42` all
remain **OPEN**. The suite is **not** frozen.

Authority: `SL-V2-LOWER-MODEL-01`
Committed schedule: [`AFCI_LOWER_MODEL_PILOT_RUN_PLAN.json`](AFCI_LOWER_MODEL_PILOT_RUN_PLAN.json)
Committed execution plan: [`AFCI_LOWER_MODEL_PILOT_EXECUTION_PLAN.json`](AFCI_LOWER_MODEL_PILOT_EXECUTION_PLAN.json)

---

## 1. What this pilot asks

The completed `AFCI_EFFICIENCY_PILOT` measured, on `claude-sonnet-5`, what a run
COSTS with and without the architecture payload. Its frozen decision rule
returned **STOP**: on that substrate, under that model, `C4` was not cheaper.

This pilot asks a **different, new** question:

> **Does explicit architecture guidance become more useful when the coding model
> has less ability to infer the architecture from the repository on its own?**

The hypothesis is that a lower-capability model is less able to reconstruct the
intended layering accurately and cheaply from the code alone, and therefore has
more to gain from being told it. That is a claim about a **moderator**, and this
pilot is the smallest honest look at it.

Two things follow, and both are frozen below.

**It asks TWO independent questions, and never collapses them.**

* **Quality.** Does `C4`/MAD reduce architecture violations under the lower
  model without materially reducing functional correctness?
* **Efficiency.** Does `C4`/MAD reduce tokens, time, repository exploration or
  tool effort under the lower model?

They are reported separately and combined into no single score. AFCI may be
useful when architecture quality improves and token cost rises modestly, and a
composite would hide exactly that case.

**It does not reinterpret the Sonnet result.** The Sonnet pilot's records,
outcome and `STOP` verdict stand exactly as written. Nothing here re-reads them,
amends them or pools with them (§13).

---

## 2. Scope, and the exact matrix

| axis | values | count |
|---|---|---|
| task | `PT01`, `PT04`, `PT07` | 3 |
| condition | `C1`, `C4` | 2 |
| reset state | `NON_RESET` only | 1 |
| repetition | `R1`, `R2`, `R3` | 3 |

**3 × 2 × 1 × 3 = 18 substantive observations, maximum. 9 paired blocks.**

The reset arm is **deliberately excluded**. This pilot isolates MODEL CAPABILITY
as the moderator; adding context-loss as a second factor at the same time would
leave a difference attributable to either. The reset arm remains available as a
separate future factor and is not authorised here, so a `RESET` run under this
purpose is refused rather than scheduled.

The three instruments are the three whose hidden functional acceptance runtimes
are recorded `validated` in
[`TASK_ACCEPTANCE_MATRIX.csv`](TASK_ACCEPTANCE_MATRIX.csv), and they are the same
three the Sonnet pilot ran, deliberately: holding the instrument set fixed is
what makes the descriptive comparison in §13 meaningful at all.

Validation of the hidden acceptance is **not** a freeze, is **not** an
independent review, and confers no `E1` run eligibility.

---

## 3. The run-purpose firewall

### 3.1 The run-purpose firewall table

| field | value |
|---|---|
| `run_purpose` | `AFCI_LOWER_MODEL_PILOT` |
| `decision_id` | `SL-V2-LOWER-MODEL-01` |
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
is refused rather than written.

This purpose is **new**. It deliberately does not reuse `AFCI_EFFICIENCY_PILOT`:
a second model under the same purpose marker would make two different
experiments indistinguishable in every artifact that carries only the purpose.

### 3.2 Artifact quarantine

Every artifact is written to a scratch root **outside** the canonical
repository, and `experiments/v2/results/` and `experiments/v2/analysis/` are
refused as artifact roots for this purpose.

---

## 4. Repetitions

### 4.1 The repetition table

| field | value |
|---|---|
| `decision_id` | `SL-V2-LOWER-MODEL-01` |
| `diagnostic_repetitions` | `3` |
| `condition` | `C1, C4` |
| `tasks` | `PT01, PT04, PT07` |
| `reset_states` | `NON_RESET` |
| `process_per_repetition` | `fresh` |
| `session_per_repetition` | `fresh` |
| `resume_permitted` | `false` |
| `continuation_permitted` | `false` |
| `session_reuse_permitted` | `false` |
| `power_claim` | `none` |
| `precision_claim` | `none` |
| `treatment_effect_claim` | `none` |

Three repetitions per (task, condition) cell. **No power calculation justifies
the count and none is implied.**

---

## 5. The model, and how it was chosen

### 5.1 The model discovery record

The lower model was **not guessed**. It was established in two steps, both
recorded, and the second is the only live call this package made.

**Step 1 — local enumeration, no model invoked.** The installed Claude Code
runtime at `C:\Users\<operator>\.local\share\claude\versions\2.1.229` was read
as bytes and every model identifier string it carries was enumerated. The
Haiku-family identifiers present are `claude-haiku-4-5` and
`claude-haiku-4-5-20251001` (plus the legacy `claude-3-5-haiku` and
`claude-3-haiku` families and their dated forms). **No Haiku 5 or any newer
Haiku identifier exists in this runtime**, so Haiku 4.5 is the strongest
Haiku-family model this runtime can address, and nothing newer can have been
missed by selecting it.

**Step 2 — one infrastructure-only identity probe.** Subscription accessibility
and the exact readback cannot be established from a binary, so exactly one probe
was executed (§16). It requested the **exact dated identifier** rather than the
`haiku` alias — so the identifier this record pins is the identifier that was
actually exercised, not one inferred from an alias resolution.

| field | value |
|---|---|
| requested selector | `claude-haiku-4-5-20251001` (exact id, never the alias) |
| resolved model id | `claude-haiku-4-5-20251001` |
| readback sources | `system.init.model`, `modelUsage` |
| readback unambiguous | `true` |
| exit status | `0` |
| `apiKeySource` | `none` (subscription OAuth) |
| runtime reported | `2.1.229` |
| verdict | `PASS` |

The four selection criteria, each answered by the evidence above rather than
asserted: it is **accessible** through the authenticated subscription (exit 0,
no API key); it is **pinnable by an exact identifier** (the exact dated id was
what was requested); it **returns an exact model readback** (one identifier,
from both sources); and it is **clearly lower-capability than
`claude-sonnet-5`** — a small-tier model of the preceding generation, which is
the property the hypothesis is about. It supports the same
`Read`/`Edit`/`Write`/`Glob`/`Grep`/`Bash` workflow, which is the workflow every
prior live run in this study used.

`Q8` (invalid-model-id rejection) is **cited, not re-performed**, exactly as
`SL-V2-QUAL-01` and `SL-V2-EFF-01` cite it. It is a property of the RUNTIME —
does an unrecognised identifier get rejected with no substitution — and the
runtime, the machine and the CLI version are the ones `SL-PT08-05` validated it
on. Re-performing it would have been a second live call establishing a fact
already on record.

Like every prior diagnostic pin, this confers **no primary-model selection**:
`TD-B03` stays open and `primary_model` stays `null`.

### 5.2 The frozen configuration, stated once

| field | value |
|---|---|
| model | `claude-haiku-4-5-20251001` (exact id; never the alias) |
| runtime | Claude Code `2.1.229` |
| authentication | subscription OAuth; no API key |
| fallback model | none; `--fallback-model` is refused by the launcher |
| permission mode | `acceptEdits` |
| tools | `Read, Edit, Write, Glob, Grep, Bash` |
| permission allowlist | `Bash(npm run ci:agent)`, `Bash(npm run ci:agent:*)` |
| turn ceiling | 64, `NON_RESET`, identical in `C1` and `C4` |
| process per repetition | fresh |
| session per repetition | fresh |
| sterile profile | required, per process |
| context audit | required for **every** process |

The permission allowlist is **reused unchanged** from `SL-V2-EFF-01` §5, for the
reason that record established: without it the governed CI surface
`npm run ci:agent` is refused in headless mode, and a benchmark that instructs a
model to validate its work with a command it is then refused is measuring the
refusal. `TD-B42` — the bearing of that finding on the runs executed before the
allowlist existed — is **UNRESOLVED** and is not resolved here.

---

## 6. Applicability of the diagnostic-scoped freeze

Six tables, one per (task, condition). They are **not** collapsed to three: `C1`
and `C4` differ in `architecture_delivery`, which is the value a freeze table
exists to pin, and one shared table would certify a delivery that one of the two
arms never received.

Each narrows the **applicability** of the suite-wide `G1` freeze prerequisite for
its own triple and passes no gate.

### 6.1 Applicability table - PT01 / C1

| field | value |
|---|---|
| `decision_id` | `SL-V2-LOWER-MODEL-01` |
| `diagnostic_freeze_authority` | `SL-V2-LOWER-MODEL-01` |
| `run_purpose` | `AFCI_LOWER_MODEL_PILOT` |
| `diagnostic_freeze_task` | `PT01` |
| `diagnostic_freeze_condition` | `C1` |
| `diagnostic_freeze_frozen` | `true` |
| `diagnostic_freeze_task_sha256` | `6c938822fe19cd6e87942a6ee24ec8f604c0883da1b7f80d45216be35d7c9c39` |
| `diagnostic_freeze_exact_model_id` | `claude-haiku-4-5-20251001` |
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
| `td_b42_status` | `open` |
| `priority_b_state` | `started; not complete` |
| `td_b03_status` | `open` |

### 6.2 Applicability table - PT01 / C4

| field | value |
|---|---|
| `decision_id` | `SL-V2-LOWER-MODEL-01` |
| `diagnostic_freeze_authority` | `SL-V2-LOWER-MODEL-01` |
| `run_purpose` | `AFCI_LOWER_MODEL_PILOT` |
| `diagnostic_freeze_task` | `PT01` |
| `diagnostic_freeze_condition` | `C4` |
| `diagnostic_freeze_frozen` | `true` |
| `diagnostic_freeze_task_sha256` | `6c938822fe19cd6e87942a6ee24ec8f604c0883da1b7f80d45216be35d7c9c39` |
| `diagnostic_freeze_exact_model_id` | `claude-haiku-4-5-20251001` |
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
| `td_b42_status` | `open` |
| `priority_b_state` | `started; not complete` |
| `td_b03_status` | `open` |

### 6.3 Applicability table - PT04 / C1

| field | value |
|---|---|
| `decision_id` | `SL-V2-LOWER-MODEL-01` |
| `diagnostic_freeze_authority` | `SL-V2-LOWER-MODEL-01` |
| `run_purpose` | `AFCI_LOWER_MODEL_PILOT` |
| `diagnostic_freeze_task` | `PT04` |
| `diagnostic_freeze_condition` | `C1` |
| `diagnostic_freeze_frozen` | `true` |
| `diagnostic_freeze_task_sha256` | `f349b150b1d8fe5676fed8460b1840b988ee2bb0a78b1966ef82ae9ce9c8a9b5` |
| `diagnostic_freeze_exact_model_id` | `claude-haiku-4-5-20251001` |
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
| `td_b42_status` | `open` |
| `priority_b_state` | `started; not complete` |
| `td_b03_status` | `open` |

### 6.4 Applicability table - PT04 / C4

| field | value |
|---|---|
| `decision_id` | `SL-V2-LOWER-MODEL-01` |
| `diagnostic_freeze_authority` | `SL-V2-LOWER-MODEL-01` |
| `run_purpose` | `AFCI_LOWER_MODEL_PILOT` |
| `diagnostic_freeze_task` | `PT04` |
| `diagnostic_freeze_condition` | `C4` |
| `diagnostic_freeze_frozen` | `true` |
| `diagnostic_freeze_task_sha256` | `f349b150b1d8fe5676fed8460b1840b988ee2bb0a78b1966ef82ae9ce9c8a9b5` |
| `diagnostic_freeze_exact_model_id` | `claude-haiku-4-5-20251001` |
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
| `td_b42_status` | `open` |
| `priority_b_state` | `started; not complete` |
| `td_b03_status` | `open` |

### 6.5 Applicability table - PT07 / C1

| field | value |
|---|---|
| `decision_id` | `SL-V2-LOWER-MODEL-01` |
| `diagnostic_freeze_authority` | `SL-V2-LOWER-MODEL-01` |
| `run_purpose` | `AFCI_LOWER_MODEL_PILOT` |
| `diagnostic_freeze_task` | `PT07` |
| `diagnostic_freeze_condition` | `C1` |
| `diagnostic_freeze_frozen` | `true` |
| `diagnostic_freeze_task_sha256` | `557caed09420354efbc823c8b72e54b0760ac72847aba0d9c07d99e37ff7d2d7` |
| `diagnostic_freeze_exact_model_id` | `claude-haiku-4-5-20251001` |
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
| `td_b42_status` | `open` |
| `priority_b_state` | `started; not complete` |
| `td_b03_status` | `open` |

### 6.6 Applicability table - PT07 / C4

| field | value |
|---|---|
| `decision_id` | `SL-V2-LOWER-MODEL-01` |
| `diagnostic_freeze_authority` | `SL-V2-LOWER-MODEL-01` |
| `run_purpose` | `AFCI_LOWER_MODEL_PILOT` |
| `diagnostic_freeze_task` | `PT07` |
| `diagnostic_freeze_condition` | `C4` |
| `diagnostic_freeze_frozen` | `true` |
| `diagnostic_freeze_task_sha256` | `557caed09420354efbc823c8b72e54b0760ac72847aba0d9c07d99e37ff7d2d7` |
| `diagnostic_freeze_exact_model_id` | `claude-haiku-4-5-20251001` |
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
| `td_b42_status` | `open` |
| `priority_b_state` | `started; not complete` |
| `td_b03_status` | `open` |

---

## 7. The frozen execution configuration, per cell

Six tables, matching §6 one for one.

### 7.1 Frozen execution configuration - PT01 / C1

| field | value |
|---|---|
| `exact_model_id` | `claude-haiku-4-5-20251001` |
| `cli_version` | `2.1.229` |
| `permission_mode` | `acceptEdits` |
| `tools` | `Read, Edit, Write, Glob, Grep, Bash` |
| `allowed_tools` | `Bash(npm run ci:agent)`, `Bash(npm run ci:agent:*)` |
| `architecture_delivery` | `none` |
| `reset_state` | `NON_RESET` |
| `non_reset_max_turns` | `64` |

### 7.2 Frozen execution configuration - PT01 / C4

| field | value |
|---|---|
| `exact_model_id` | `claude-haiku-4-5-20251001` |
| `cli_version` | `2.1.229` |
| `permission_mode` | `acceptEdits` |
| `tools` | `Read, Edit, Write, Glob, Grep, Bash` |
| `allowed_tools` | `Bash(npm run ci:agent)`, `Bash(npm run ci:agent:*)` |
| `architecture_delivery` | `prompt_injection` |
| `architecture_sha256` | `bf6f32b162a23b851596d8b489d938bef10d0b8616a50dcc039873d12ffa7a4d` |
| `reset_state` | `NON_RESET` |
| `non_reset_max_turns` | `64` |

### 7.3 Frozen execution configuration - PT04 / C1

| field | value |
|---|---|
| `exact_model_id` | `claude-haiku-4-5-20251001` |
| `cli_version` | `2.1.229` |
| `permission_mode` | `acceptEdits` |
| `tools` | `Read, Edit, Write, Glob, Grep, Bash` |
| `allowed_tools` | `Bash(npm run ci:agent)`, `Bash(npm run ci:agent:*)` |
| `architecture_delivery` | `none` |
| `reset_state` | `NON_RESET` |
| `non_reset_max_turns` | `64` |

### 7.4 Frozen execution configuration - PT04 / C4

| field | value |
|---|---|
| `exact_model_id` | `claude-haiku-4-5-20251001` |
| `cli_version` | `2.1.229` |
| `permission_mode` | `acceptEdits` |
| `tools` | `Read, Edit, Write, Glob, Grep, Bash` |
| `allowed_tools` | `Bash(npm run ci:agent)`, `Bash(npm run ci:agent:*)` |
| `architecture_delivery` | `prompt_injection` |
| `architecture_sha256` | `bf6f32b162a23b851596d8b489d938bef10d0b8616a50dcc039873d12ffa7a4d` |
| `reset_state` | `NON_RESET` |
| `non_reset_max_turns` | `64` |

### 7.5 Frozen execution configuration - PT07 / C1

| field | value |
|---|---|
| `exact_model_id` | `claude-haiku-4-5-20251001` |
| `cli_version` | `2.1.229` |
| `permission_mode` | `acceptEdits` |
| `tools` | `Read, Edit, Write, Glob, Grep, Bash` |
| `allowed_tools` | `Bash(npm run ci:agent)`, `Bash(npm run ci:agent:*)` |
| `architecture_delivery` | `none` |
| `reset_state` | `NON_RESET` |
| `non_reset_max_turns` | `64` |

### 7.6 Frozen execution configuration - PT07 / C4

| field | value |
|---|---|
| `exact_model_id` | `claude-haiku-4-5-20251001` |
| `cli_version` | `2.1.229` |
| `permission_mode` | `acceptEdits` |
| `tools` | `Read, Edit, Write, Glob, Grep, Bash` |
| `allowed_tools` | `Bash(npm run ci:agent)`, `Bash(npm run ci:agent:*)` |
| `architecture_delivery` | `prompt_injection` |
| `architecture_sha256` | `bf6f32b162a23b851596d8b489d938bef10d0b8616a50dcc039873d12ffa7a4d` |
| `reset_state` | `NON_RESET` |
| `non_reset_max_turns` | `64` |

---

## 8. The turn budget

### 8.1 The frozen turn-budget table

| field | value |
|---|---|
| `decision_id` | `SL-V2-LOWER-MODEL-01` |
| `run_purpose` | `AFCI_LOWER_MODEL_PILOT` |
| `scope` | `AFCI_LOWER_MODEL_PILOT ONLY` |
| `reset_states_authorised` | `NON_RESET` |
| `reset_arm_authorised` | `false` |
| `non_reset_max_turns` | `64` |
| `total_allowance_non_reset` | `64` |
| `pre_reset_max_turns` | `not applicable` |
| `post_reset_max_turns` | `not applicable` |
| `allowances_identical_across_conditions` | `true` |
| `budget_lowered_because_the_model_is_cheaper` | `false` |
| `td_b01_resolved_globally` | `false` |
| `td_b11_resolved_globally` | `false` |
| `g2_passed` | `false` |
| `confirmatory_precedent_created` | `false` |
| `decided_before_any_lower_model_observation` | `true` |

**64 is the Sonnet pilot's `NON_RESET` allowance, unchanged.** It is deliberately
NOT reduced because the model is cheaper: a lower-capability model that needs
more turns to reach the same place is exactly the phenomenon this pilot is
looking at, and capping it lower would convert that phenomenon into a truncation
artifact. `C1` and `C4` receive the identical ceiling; a difference between the
arms in allowance would be indistinguishable from a difference in treatment.

It resolves `TD-B01` and `TD-B11` for nothing, and passes `G2` for nothing.

---

## 9. The architecture-corpus eligibility

`PT01` and `PT04` carry no private per-task architecture mutation corpus;
`PT07` does. `SL-V2-EFF-ELIG-01` adjudicated, for the COST-ONLY efficiency
pilot, that a full corpus is not a run-eligibility prerequisite when eight
pre-data conditions hold. **That decision is scoped to that purpose and is not
inherited.** This section takes the same question for THIS purpose, on its own
facts, and reaches the same answer under the same eight conditions.

The difference this record must be honest about: the efficiency pilot produced
**no** architecture result at all, and this pilot produces one. The architecture
measurement here is still **descriptive and non-confirmatory** — it enters no
`E1` numerator or denominator, no treatment-effect estimate and no power
estimate — but it is a reported endpoint rather than an unreported guardrail, so
the eligibility rule below states that explicitly rather than reusing the
earlier wording.

### 9.1 The eligibility rule table

| field | value |
|---|---|
| `decision_id` | `SL-V2-LOWER-MODEL-01` |
| `run_purpose` | `AFCI_LOWER_MODEL_PILOT` |
| `architecture_corpus_required_for_run_eligibility` | `false` |
| `pilot_scoped_conditions_required` | `8` |
| `architecture_measurement_role` | `descriptive non-confirmatory quality endpoint` |
| `architecture_corpus_requirement_waived_globally` | `false` |
| `architecture_corpus_required_for_confirmatory_use` | `true` |
| `private_public_sync_propagation_still_required` | `true` |
| `enters_confirmatory_e1_analysis` | `false` |
| `enters_treatment_effect_analysis` | `false` |
| `enters_power_estimation` | `false` |
| `passes_g1` | `false` |
| `passes_g2` | `false` |
| `closes_td_b32` | `false` |
| `closes_td_b34` | `false` |
| `closes_td_b39` | `false` |
| `changes_e1` | `false` |
| `admits_new_candidates` | `false` |
| `makes_pilot_tasks_confirmatory` | `false` |
| `changes_frozen_pilot_metrics_or_thresholds` | `false` |
| `observations_when_recorded` | `0` |

The eight conditions are the ones `SL-V2-EFF-ELIG-01` enumerated, evaluated
independently here: hidden functional acceptance validated; a legal reference
that passes it and scores `SATISFIED` on the single applicable target
opportunity with zero violations; a **functionally correct** target-violating
reference that ALSO passes hidden functional acceptance; the architecture scorer
reporting the exact declared target violation on that same reference; functional
acceptance not enforcing architecture; and this purpose being non-confirmatory,
non-result-bearing and pinned out of `E1`, treatment-effect and power analysis.

The anti-circularity control is the third of those. If a violating
implementation could not pass functional acceptance, the functional oracle would
be enforcing placement and the architecture measurement would be circular.

This is **NOT** a full architecture mutation corpus and must never be described
as one. The corpus requirement is UNCHANGED and REQUIRED in full everywhere it
already applied, including every confirmatory and result-bearing purpose.

---

## 10. What is measured

### 10.1 Architecture quality

Scored **post hoc**, by the private evaluator, against the **preserved
post-run worktree** — never the live one the model was editing, and never the
canonical repository. Every substantive run records:

* `architecture_applicable_opportunity_count`
* `architecture_violated_opportunity_count`
* `raw_architecture_violation_count`
* `target_opportunity_violated` (yes/no)

Architecture scoring is performed by a **separate channel** from functional
scoring, is derived from counts rather than supplied as a verdict, and is
**never** allowed to influence the functional verdict or vice versa.

**The coding model never sees any of it.** It is not handed the architecture
scorer, its rules, the hidden opportunity definitions, the target rule
identities or any other hidden evaluator material; none of that is present in
its prepared worktree, in its prompt, or in anything it can read. The scorer
runs after the process has ended, against a copy. The run record carries counts
and a boolean, and the public invocation boundary **refuses to write a record**
that names a private opportunity or rule identifier at all.

### 10.2 Functional quality

The validated arbitrary-worktree functional scorer is reused unchanged, and
`FUNCTIONAL_VALID` keeps exactly the definition `SL-V2-EFF-FUNC-01` froze:

> every declared semantic case executed and passed, with no missing, failed,
> errored or indeterminate semantic case.

Non-semantic cases are executed and recorded **separately** and determine
nothing, because a case that issues no request cannot tell a working candidate
from a broken one.

### 10.3 Efficiency

Reused unchanged from the Sonnet pilot, so the descriptive comparison in §13 is
between like and like:

```
TOTAL_INPUT_TOKENS = usage.input_tokens
                   + usage.cache_creation_input_tokens
                   + usage.cache_read_input_tokens
```

The three are non-overlapping. `usage.cache_creation.ephemeral_1h_input_tokens`
and `ephemeral_5m_input_tokens` are a breakdown OF `cache_creation_input_tokens`
and are never added on top.

**MAD tokens count.** Cached MAD tokens count. Excluding the payload would be
excluding the treatment.

Also captured: provider `costUSD`, `TOTAL_OUTPUT_TOKENS`, `MODEL_WALL_SECONDS`,
`TOTAL_TOOL_CALLS`, `EXPLORATION_CALLS` (= `READ_CALLS + GREP_CALLS +
GLOB_CALLS`), `UNIQUE_FILES_READ`, `UNIQUE_FILES_MODIFIED`,
`UNIQUE_DIRECTORIES_EXPLORED`, `REPEATED_FILE_READS`, `EDIT_CALLS`,
`WRITE_CALLS`, `FILES_REEDITED`, `CI_COMMAND_RUNS`, `TEST_COMMAND_RUNS`,
`FAILED_TEST_OR_CI_CYCLES`, `TURNS_USED`, files changed, lines added, lines
removed and net lines.

Every `NON_RESET` run emits a terminal `result` event, so both the input and the
output totals are exact for every observation in this pilot. The `RESET`
output-token limitation `SL-V2-EFF-01` §9.2 recorded does not arise here,
because there is no reset arm.

---

## 11. The frozen analysis

**No p-values. No confidence intervals. No confirmatory effect claim.**

### 11.1 Pairing

A **block** is (task × repetition): 9 of them, each holding one `C1` and one
`C4` run that differ in the condition and in nothing else.

### 11.2 What is reported, and how

**Functional**, over all 9 blocks:

* `C1` functionally-valid count out of 9;
* `C4` functionally-valid count out of 9.

**Architecture**, by task and overall, over all 18 runs:

* `C1` target-violation run count and `C4` target-violation run count;
* total applicable opportunities and total violated opportunities per arm.

Architecture is reported over **all** runs and not only over functionally-valid
pairs, because a run that violated the architecture is still a run that violated
it. The functionally-valid subset is reported alongside so a reader can see
both, and neither is presented as the other.

**Efficiency**, over **functionally-valid pairs only** — a cost figure from a
run that did not work is not a cheaper way of doing the task:

`TOKEN_RATIO`, `MODEL_WALL_RATIO`, `EXPLORATION_RATIO`, `TOTAL_TOOL_RATIO`,
`COST_RATIO` (where both sides are complete), `UNIQUE_FILES_READ` ratio and
`EDIT+WRITE` ratio — each computed as `C4 / C1` within the block, lower being
better for `C4`.

### 11.3 What is never done

The quality and efficiency channels are **never** combined into one score, and
neither is used to adjust the other.

### 11.4 The analysis is computable, and that was checked before any data

`experiments/v2/harness/lower_model_pilot_analysis.py` implements §11 and §12 and
is committed **while zero lower-model observations exist**. It was executed
against **synthetic records only** — fabricated in memory, never written, and
none of them an observation, an estimate or a prediction — and it produces the
frozen outcome correctly in four directions, including the one this design exists
for: architecture improving while token cost rises yields a **quality signal and
no efficiency signal**, where a composite score would have reported a wash.

This section exists because the efficiency pilot was briefly **executable and not
analysable**: its cost figures would have existed and the gate admitting them
would not have been computable. That is not repeated here.

The separation is structural rather than promised. The architecture summary and
the efficiency summary share no input beyond the block list, neither reads the
other's output, and the two continuation signals are evaluated independently. A
`claude-sonnet-5` record handed to this analysis is **refused**, not filtered out,
so "never pooled" is a property of the code.

---

## 12. The frozen continuation rule

Frozen **before** any observation exists. Expansion to a larger lower-model
study is authorised if **EITHER** signal below holds in full. They are evaluated
independently and either one suffices.

### 12.1 QUALITY SIGNAL — all three

1. `C4` has **fewer** target architecture-violation runs than `C1` **overall**;
2. that improvement occurs in **at least 2 of the 3 tasks**, where a task
   improves when its `C4` target-violation run count is **strictly lower** than
   its `C1` target-violation run count;
3. the `C4` functionally-valid count is **no more than 1 below** `C1`'s.

### 12.2 EFFICIENCY SIGNAL — both

1. the `C4` functionally-valid count is **no more than 1 below** `C1`'s;
2. **and at least one** of:
   * median `TOKEN_RATIO` **< 1.00**
   * median `EXPLORATION_RATIO` **≤ 0.80**
   * median `TOTAL_TOOL_RATIO` **≤ 0.85**

Each median is taken over the functionally-valid pairs.

### 12.3 Otherwise

> **DO NOT EXPAND THE SYNTHETIC LOWER-MODEL MATRIX AUTOMATICALLY**

No automatic expansion follows. A separate **open-source repository complexity**
study may still proceed, because repository complexity is an independent
moderator and this pilot measures nothing about it. That study is a distinct
future experiment and is **not** authorised by this record.

---

## 13. Comparison with the Sonnet pilot

After this pilot completes, its results are compared **descriptively** with the
completed `claude-sonnet-5` `NON_RESET` findings.

**Sonnet and lower-model records are NEVER pooled into one treatment estimate.**
They are two separate experiments on two separate models, and one number
covering both would be an estimate of nothing.

What is reported is three things, in this order:

1. **Within Sonnet:** `C4 / C1`, taken from the stored professor evidence
   package (`study-results/05_efficiency_attempt_2_completed/`) and from nowhere
   else. The historical `NON_RESET` `TOKEN_RATIO` reference is **1.5582**; every
   other Sonnet value is read out of the stored package at comparison time
   rather than restated here, so no number in this record can go stale against
   the evidence it names.
2. **Within lower model:** `C4 / C1`, from this pilot.
3. **The direction and magnitude of the difference between them, described in
   words and in a table.** No test, no interaction estimate, no pooled model.

One asymmetry must be stated whenever the comparison is: the Sonnet pilot
produced **no architecture measurement at all**, so the quality channel has no
Sonnet counterpart and the quality comparison is **lower-model only**. Only the
efficiency channel is comparable across the two.

---

## 14. The run schedule

Deterministic, committed, and generated before any run:

| field | value |
|---|---|
| seed | `AFCI_LOWER_MODEL_PILOT_V1_20260917` |
| blocks | 9 |
| runs | 18 |
| ordering | sort by SHA-256 of a seeded string; no language RNG |
| file | [`AFCI_LOWER_MODEL_PILOT_RUN_PLAN.json`](AFCI_LOWER_MODEL_PILOT_RUN_PLAN.json) |

Condition order **within** each block and the order **of** the blocks are both
randomised deterministically, so a drift over the execution session cannot land
systematically on one arm and the tasks are interleaved rather than run in three
homogeneous stretches.

The schedule's own SHA-256, the scientific projection's SHA-256, the 18 run ids
and the 18 artifact directories are recorded in the committed execution plan
[`AFCI_LOWER_MODEL_PILOT_EXECUTION_PLAN.json`](AFCI_LOWER_MODEL_PILOT_EXECUTION_PLAN.json),
which also records the artifact and sterile roots. They are a **new namespace**
with **zero** overlap with any Sonnet artifact: the run purpose is part of the
identity seed, so no lower-model row can derive an identity an efficiency-pilot
row already minted.

No run in this schedule has been executed.

---

## 15. What this decision does NOT do

| | status after this record |
|---|---|
| gate `G1` | **NOT PASSED** |
| gate `G2` | **NOT PASSED** |
| `TD-B01` / `TD-B11` (budgets) | **OPEN** |
| `TD-B34` (qualification) | **OPEN** |
| `TD-B32` (global) | **OPEN** |
| `TD-B12` / `G6` | **OPEN** |
| `TD-B03` (primary model) | **OPEN**; `primary_model: null` |
| `TD-B39` | **OPEN** |
| `TD-B42` (the permission finding) | **OPEN** |
| suite freeze | **false** |
| `E1` register | **UNCHANGED** |
| any task manifest | **NOT FROZEN** |
| independent review | **NOT OBTAINED AND NOT CLAIMED** |
| the Sonnet efficiency pilot's records and `STOP` outcome | **UNCHANGED, NOT RE-READ, NOT RE-INTERPRETED** |
| the open-source complexity study | **NOT AUTHORISED HERE** |

No result, violation value, success value, outcome value or treatment-effect
estimate exists, and none is created by executing this pilot.

---

## 16. The infrastructure probe

**One** quarantined, synthetic, infrastructure-only live probe was executed while
building this package.

| field | value |
|---|---|
| probe | `Q1` resolved-model-id readback |
| purpose | establish subscription accessibility and the exact model readback |
| task used | **none** — the probe prompt asks for a single word |
| MAD used | **none** |
| run purpose carried | **none** |
| directory | a synthetic disposable directory outside both repositories |
| study observation created | **none** |
| result | `PASS`; one unambiguous identifier from two readback sources |

It is **not** a pilot observation, it is not scored, it produced no result, and
it entered no dataset.

Lower-model pilot observations at the time of writing: **ZERO**.
