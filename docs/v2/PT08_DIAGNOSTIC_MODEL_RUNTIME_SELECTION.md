# docs/v2 — `SL-PT08-05`: the model and runtime pinned for the `PT08` `C1` difficulty diagnostic

Status: **Study-Lead governance adjudication for study v2.** This record is
governance only. It authors **no** task body, changes **no** task body or hash,
edits **no** pinned public schema, executes **no** benchmark condition, validates
**no** hidden acceptance, freezes **nothing**, passes **no** gate, produces **no**
result and **no** power value, and advances **no** private linkage baseline. The
protocol remains **PRE-FREEZE**.

Decision identifier: **`SL-PT08-05`**, in the repository's existing Study-Lead
convention. Related: [`PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md`](PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md)
§7 items 8–10; [`PT08_DIAGNOSTIC_EXECUTION_DECISIONS.md`](PT08_DIAGNOSTIC_EXECUTION_DECISIONS.md)
§4 items 1 and 3; [`PT08_DIAGNOSTIC_ISOLATION_CLARIFICATION.md`](PT08_DIAGNOSTIC_ISOLATION_CLARIFICATION.md);
[`MODEL_EXECUTION_CONTROLS.md`](MODEL_EXECUTION_CONTROLS.md) §7;
[`MODEL_REGISTRY.yml`](MODEL_REGISTRY.yml) `diagnostic_model_selection`.

---

## 1. What was validated, and in what order

The order matters and is recorded because it is what makes the pin evidential
rather than assumed. **No diagnostic result existed at any point below, and none
exists now.**

1. A sterile profile was built and the **real context audit** was run against
   the environment a repetition will actually launch in — the same HOME, the
   same configuration directory, the same variables and the same command.
   Verdict **`CLEAN`**, with the runtime's own `system.init` reporting
   `skills: []`, `slash_commands: []`, `plugins: []`, `mcp_servers: []` and
   `output_style: default`.
2. **`Q8`** was performed against the live runtime with a deliberately
   impossible model id. **Rejected.**
3. **`Q1`** was performed against the live runtime with the stable selector.
   **One** model id was resolved, reported by two independent channels.
4. Only then was the exact resolved id pinned, below.

## 2. `SL-PT08-05` — the decision

> **`SL-PT08-05`.** For `run_purpose` = **`PT08_DIFFICULTY_DIAGNOSTIC`** and for
> that purpose **only**, the diagnostic runs on the **Claude Sonnet** family, at
> the exact model id **`claude-sonnet-5`** that the runtime itself resolved, on
> the Claude Code runtime version **actually validated on the execution machine,
> `2.1.229`**, under permission mode **`acceptEdits`** with a fixed tool set,
> with **no fallback model**, for **three** repetitions.
>
> All three repetitions request the **exact model id**, never the alias. A
> repetition whose readback resolves anything else is **invalid**.

### 2.1 The applicability table

| Field | Value |
|---|---|
| `run_purpose` | `PT08_DIFFICULTY_DIAGNOSTIC` |
| `primary_model_family` | Claude Sonnet |
| `requested_selector_at_Q1` | `sonnet` |
| `resolved_exact_model_id` | `claude-sonnet-5` |
| `selector_used_for_every_repetition` | `claude-sonnet-5` (exact id, never the alias) |
| `Q1_readback` | **PASS** — unambiguous, one id |
| `Q1_readback_sources` | `system.init.model` and `modelUsage`, in agreement |
| `Q8_invalid_model_id` | `claude-nonexistent-model-9x7q-not-a-real-id` |
| `Q8_rejection` | **PASS** — exit status 1, `modelUsage` empty, no substitution |
| `sterile_context_validation` | **PASS** — audit verdict `CLEAN` |
| `authentication` | Claude Code subscription OAuth; `apiKeySource: none` |
| `ANTHROPIC_API_KEY_used` | **no** |
| `fallback_model` | none; `--fallback-model` is refused by the launcher |
| `permission_mode` | `acceptEdits` |
| `tools` | `Read, Edit, Write, Glob, Grep, Bash` |
| `repetitions` | 3 (`SL-PT08-03`, unchanged) |
| `validated_cli_version` | **2.1.229** |
| `governed_toolchain_cli_version` | 2.1.209 |
| `cli_version_discrepancy` | **UNRESOLVED** — see §4 |

---

## 3. Why this is not the `TD-B03` selection

`TD-B03` selects **the primary benchmark model of the confirmatory study**. That
decision is made after screening across `C1`/`C3`/`C4`, and is explicitly never
made on the largest favourable effect. It stays **open**, and
`MODEL_REGISTRY.yml` still records `primary_model: null`.

`TD-B03` also carries the instruction *"do not select Sonnet or Opus yet"*.
**That instruction is recorded here and is not treated as discharged.** It is
about the confirmatory selection, and this pin creates none of the things that
instruction guards against: no screening evidence, no cross-condition
comparison, no effect estimate, and no precedent for the confirmatory choice.
Pinning a model so that a quarantined difficulty probe can execute at all is a
different act from choosing the study's model.

The tension between that instruction and this pin is **stated rather than
resolved**. Resolving it is the confirmatory selection's business, not this
record's, and a reader who wants the confirmatory answer must still go to
`TD-B03`, which is open.

---

## 4. The runtime version, recorded rather than reconciled

The governed toolchain value in `MODEL_REGISTRY.yml` is **2.1.209**. The runtime
actually installed on the execution machine, and the one every probe above was
validated against, is **2.1.229**.

**No version match is manufactured.** The diagnostic records the version it
actually validated; the governed toolchain value is left exactly as it was; and
the difference is carried explicitly as `cli_version_discrepancy: UNRESOLVED`.

Existing governance provides no pre-data mechanism for re-freezing the governed
toolchain version, and inventing one is not this record's to do. What it does
instead is refuse to claim 2.1.209 was validated when 2.1.229 was. A future
package that needs the governed value to match the executed one must change it
deliberately, with whatever review that carries.

---

## 5. What `no_paid_run` used to say

`MODEL_REGISTRY.yml` previously recorded `no_paid_run: true`. Live runtime
control probes have since been executed, so that flag is now **`false`**, with
`paid_activity_to_date` recording exactly what ran.

The narrower claim that remains true, and that matters, is: **a runtime control
is not a benchmark run.** `Q1`, `Q8` and the context audit start real processes
against a real account, and none of them executes a benchmark condition, scores
anything, or produces a result. **`Q1` and `Q8` are not diagnostic repetitions.**

---

## 6. What this record does NOT do

* It does **not** select a primary benchmark model, and **`TD-B03` stays open**.
* It does **not** discharge `TD-B21` for the confirmatory pilot; it records the
  two controls as validated for **this purpose** on **this runtime version**.
* It does **not** freeze anything. **`PT08` is not frozen.**
* It does **not** pass gate `G1`, and **no gate is passed**.
* It does **not** make `PT08` run eligible.
* It does **not** execute the diagnostic. **No result exists**, no violation
  value, no success value and no outcome value.
* It does **not** close `TD-B34`; priority B is **not started**.
* It does **not** change the **global `TD-B32`** row, and leaves `TD-B12`/`G6`
  unchanged — including the narrow diagnostic exception, which is unchanged in
  scope.
* It does **not** advance a private linkage baseline and requires **no** re-link.

Nothing here is frozen, and the protocol remains **PRE-FREEZE**.

---

## 7. What still blocks the diagnostic

After this record, **one** prerequisite of
[`PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md`](PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md)
§7 remains outstanding: **item 14, `PT08`'s required manifest freeze**, under
the existing lifecycle rules (`TD-B05`/`TD-B14`/`TD-B32`, gate `G1`).

`check_readiness('PT08', 'C1', 'PT08_DIFFICULTY_DIAGNOSTIC')` reports
`manifest_freeze` as the **only** blocked prerequisite once the live context
verdict is supplied, and `run_eligible` stays **`false`**.

No existing `SL-PT08` decision authorises a diagnostic-scoped route around that
freeze. `SL-PT08-01` §6 grants a narrow exception for `TD-B12`/`G6` **only** and
expressly leaves item 14 untouched; `SL-PT08-02`/`SL-PT08-03` restate that
nothing there freezes anything and that gate `G1` is not passed. Gate `G1` is
suite-wide and is recorded as blocking for reasons outside this diagnostic.

**This record does not resolve that, and must not be read as narrowing it.**
