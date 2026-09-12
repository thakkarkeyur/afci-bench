# docs/v2 — `SL-PT08-04`: what isolation means for the `PT08` `C1` difficulty diagnostic

Status: **Study-Lead governance adjudication for study v2.** This record is
governance only. It authors **no** task body, changes **no** task body or hash,
edits **no** pinned public schema, runs **no** model, executes **no** benchmark
condition, validates **no** hidden acceptance, freezes **nothing**, passes **no**
gate, produces **no** result and **no** power value, performs **no** power
calculation, selects **no** model, and advances **no** private linkage baseline.
The protocol remains **PRE-FREEZE**.

Decision identifier: **`SL-PT08-04`**, in the repository's existing Study-Lead
convention `SL-<subject>-<nn>` — the convention that numbers `SL-CA1-01` and
`SL-CA1-02` in [`CAND_A1_PREAUTHORING_DECISION.md`](CAND_A1_PREAUTHORING_DECISION.md)
§3–§4, `SL-PT08-01` in
[`PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md`](PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md)
§2, and `SL-PT08-02` / `SL-PT08-03` in
[`PT08_DIAGNOSTIC_EXECUTION_DECISIONS.md`](PT08_DIAGNOSTIC_EXECUTION_DECISIONS.md).
`SL-PT08-04` is unused elsewhere in this repository.

Related: [`PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md`](PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md)
§7 items 5–7; [`PT08_DIAGNOSTIC_EXECUTION_DECISIONS.md`](PT08_DIAGNOSTIC_EXECUTION_DECISIONS.md)
§4 item 2; [`RESET_PROTOCOL.md`](RESET_PROTOCOL.md);
[`MODEL_EXECUTION_CONTROLS.md`](MODEL_EXECUTION_CONTROLS.md) §6–§7;
[`OPEN_DECISIONS.csv`](OPEN_DECISIONS.csv) row `TD-B19`.

---

## 1. The question this record settles

`TD-B19` reads, in full and unchanged:

> Isolated container/dedicated environment + dedicated identity + CLEAN context
> audit with managed policy absent for every counted run

Read literally, three of its clauses were being treated as requiring a **second
billing identity** — a separate Claude account, or an `ANTHROPIC_API_KEY`
belonging to something other than the existing company-billed subscription.
Under that reading the diagnostic could not be prepared at all, because no such
identity exists on the execution machine.

The Study Lead's position is that this reading confuses **two different things**:

* **who pays for, and is permitted to make, the API call** — a billing and
  entitlement fact; and
* **what the model is told** — the effective model-visible execution context.

Only the second can change a benchmark observation. A benchmark result cannot be
biased by which cost centre is invoiced; it can only be biased by instructions,
skills, tools, memories or guidance that reach the model. `TD-B19` exists to
control the second, and the diagnostic's isolation requirement is therefore
restated in those terms.

**This clarification is made BEFORE ANY DIAGNOSTIC RESULT EXISTS.** No
repetition has been executed, no functional outcome is known, no architecture
observation is known, and no result, violation value or success value exists
anywhere in either repository. It is therefore **not outcome-driven**, and it
could not have been: there is no outcome to drive it.

---

## 2. `SL-PT08-04` — the decision

> **`SL-PT08-04`.** For `run_purpose` = **`PT08_DIFFICULTY_DIAGNOSTIC`** and for
> that purpose **only**:
>
> 1. **Isolation is defined by the effective model-visible execution context.**
>    A run is isolated when nothing that could instruct, steer, or inform the
>    model about the task reaches it from the execution machine — and it is
>    *not* isolated merely because some ledger elsewhere records who pays.
> 2. **A separate billing identity is NOT required.** No second Claude account,
>    no dedicated subscription and no distinct billing entity is a prerequisite
>    of this diagnostic.
> 3. **The existing company-billed Claude subscription authentication MAY be
>    reused**, and `ANTHROPIC_API_KEY` is **not** required. The diagnostic
>    authenticates as the installed runtime already does.
> 4. **Company billing membership is not, by itself, experimental context.**
>    Account-level restrictions, policy limits, entitlement flags and billing
>    metadata are **not** contamination merely because they exist.
> 5. **They ARE contamination when they inject experiment-relevant
>    prompt/context, skills, instructions, tools or task-specific guidance into
>    the model-visible execution context.** The test is injection, not presence,
>    and it is decided by **reading the material**, never by exempting a filename.
> 6. **Local user and repository Claude context must not be inherited.** No
>    `CLAUDE.md` from any workspace or ancestor directory; no user or project
>    skills, plugins, hooks, commands, agents, rules or output styles; no
>    settings file that injects instructions or context; no MCP configuration
>    that is not explicitly governed; no memory; no project history.
> 7. **Prior sessions must not be reused.** No `--resume`, no `--continue`, no
>    `--from-pr`, no reused session identifier, and no session state carried
>    from any earlier conversation.
> 8. **Authentication material may be made available without copying any other
>    Claude configuration.** Exactly one file — the credential — may be placed
>    into the run's own configuration directory. Nothing else may be copied from
>    the host profile.
> 9. **Credential contents must never enter an artifact.** They are never read,
>    never hashed into a report, never logged, and never committed. Every stream
>    captured from the process is filtered for credential-shaped material before
>    it is written anywhere.
> 10. **The context audit must return `CLEAN` against the ACTUAL launch
>     environment**, and the launch that is audited must be the launch that is
>     used. An attestation flag is not evidence and never substitutes for the
>     audit.
> 11. **This clarification waives no fresh-process and no fresh-session
>     requirement**, and waives nothing in the reset protocol.

### 2.1 The applicability table

Machine-readable. The runner re-derives these values, so drift between this
adjudication and the code is a mechanical failure rather than a reading.

| Field | Required value |
|---|---|
| `run_purpose` | `PT08_DIFFICULTY_DIAGNOSTIC` |
| `isolation_criterion` | `effective model-visible execution context` |
| `separate_billing_identity_required` | `false` |
| `dedicated_subscription_required` | `false` |
| `anthropic_api_key_required` | `false` |
| `subscription_authentication_permitted` | `true` |
| `company_billing_membership_is_contamination` | `false` |
| `account_policy_metadata_is_contamination_by_presence` | `false` |
| `account_policy_metadata_is_contamination_when_injecting` | `true` |
| `account_policy_decided_by` | `content inspection, never filename exemption` |
| `credential_files_permitted_in_run_config_dir` | `.credentials.json` |
| `other_host_claude_configuration_permitted` | `false` |
| `credential_contents_in_artifacts` | `prohibited` |
| `context_audit_required_verdict` | `CLEAN` |
| `context_audit_target` | `the actual launch environment and the actual launch command` |
| `attestation_flag_sufficient` | `false` |
| `fresh_process_required` | `true` |
| `fresh_session_required` | `true` |
| `resume_permitted` | `false` |
| `continuation_permitted` | `false` |
| `session_reuse_permitted` | `false` |
| `enterprise_managed_settings_permitted` | `false` |
| `td_b19_general_policy_amended` | `false` |

---

## 3. What remains contamination, stated as a closed list

Restated separately so no reader can extract a general relaxation from §2. Each
of the following makes the verdict `CONTAMINATED` for this diagnostic exactly as
it did before:

* a `CLAUDE.md` or `CLAUDE.local.md` in the workspace or any ancestor directory;
* skills, in any scope;
* plugins, in any scope;
* commands and custom agents;
* hooks, and any settings file that injects instructions or context;
* MCP configuration that is not explicitly governed;
* prior-session state, resume or continuation;
* project or user memory, and auto-memory files;
* rules, output styles and model/tool instruction overlays relevant to task
  execution;
* **enterprise managed settings at the operating-system policy path**, which
  stay prohibited outright and are **not** adjudicated on content.

The narrowing in §2 reaches **account-tied metadata the runtime re-creates for
itself after authenticating**, and nothing else.

---

## 4. Why a narrowing here is not a weakening

The requirement that the model-visible execution context be sterile is **not
relaxed**. It is made *stricter* in the one respect that matters, because the
clarification forces the audit to answer a question a filesystem scan alone
cannot:

* **Before.** An audit could report `CLEAN` by observing that nothing had been
  *placed* in the run's configuration directory. It could not report what the
  runtime *loaded*.
* **After.** The audit must additionally read back the runtime's own report of
  what it loaded, and require that the skills, commands, plugins and MCP servers
  it names are **empty**. Absence of placement and absence of loading are now
  both required, and the second is a direct observation rather than an
  inference.

A run that satisfied the old reading by using a second billing identity, while
still inheriting a skills directory, would have been recorded as isolated and
was not. A run that satisfies this reading has been shown, from the runtime's own
output, to have loaded nothing.

---

## 5. What this record does NOT do

* It does **not** amend the general `TD-B19` policy, whose row is unchanged in
  text and unchanged in status, and which continues to govern **every counted
  run** of the confirmatory study in full.
* It does **not** close `TD-B19`, which stays **open** and **blocking**.
* It does **not** assert that any environment is clean. It defines the test; the
  test is performed per run, per repetition, and never asserted in advance.
* It does **not** select a model. `primary_model` stays null and `TD-B03` stays
  open.
* It does **not** live-validate `Q1` or `Q8`.
* It does **not** freeze anything, and `PT08` is **not frozen**.
* It does **not** pass gate `G1`, and no gate is passed.
* It does **not** make `PT08` run eligible.
* It does **not** execute the diagnostic, and **no result exists**.
* It does **not** close `TD-B34`, and priority B is **not started**.
* It does **not** change the **global `TD-B32`** row, which stays open, and
  leaves `TD-B12`/`G6` unchanged.
* It does **not** advance a private linkage baseline and requires **no** re-link:
  it moves no pinned path.
* It does **not** perform any accounting synchronization, and states no active
  opportunity count, decision-cluster count or observation depth.

Nothing here is frozen, and the protocol remains **PRE-FREEZE**.
