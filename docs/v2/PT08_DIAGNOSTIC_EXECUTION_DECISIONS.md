# docs/v2 — `SL-PT08-02` and `SL-PT08-03`: the `PT08` `C1` diagnostic's execution-record schema and repetition count

Status: **Study-Lead governance adjudication for study v2.** This record is
governance only. It authors **no** task body, changes **no** task body or hash,
edits **no** pinned public schema, runs **no** model, executes **no** benchmark
condition, validates **no** hidden acceptance, freezes **nothing**, passes **no**
gate, produces **no** result and **no** power value, performs **no** power
calculation or power simulation, selects **no** model, establishes **no**
isolated environment, and advances **no** private linkage baseline. The protocol
remains **PRE-FREEZE**.

Decision identifiers: **`SL-PT08-02`** and **`SL-PT08-03`**, in the repository's
existing Study-Lead convention `SL-<subject>-<nn>` — the same convention that
numbers `SL-CA1-01` and `SL-CA1-02` in
[`CAND_A1_PREAUTHORING_DECISION.md`](CAND_A1_PREAUTHORING_DECISION.md) §3–§4, and
`SL-PT08-01` in
[`PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md`](PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md)
§2. New identifiers are used because `SL-PT08-01` **expressly deferred** both
questions rather than answering them: its §9 records the quarantine fields as
"mandatory future runner requirements, to be added by the package that builds the
runner", and its §11 records the sample size as "**STUDY-LEAD DECISION
PENDING**". Those two statements remain **accurate records of what `SL-PT08-01`
did**, and that record is **not edited** by this one.

Related: [`PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md`](PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md)
§7, §9, §10, §11, §12;
[`PT08_PUBLIC_ACCOUNTING_SYNCHRONIZATION.md`](PT08_PUBLIC_ACCOUNTING_SYNCHRONIZATION.md);
[`CAND_A1_PREAUTHORING_DECISION.md`](CAND_A1_PREAUTHORING_DECISION.md) §4;
[`PILOT_AND_POWER_POLICY.md`](PILOT_AND_POWER_POLICY.md);
[`FAILURE_RERUN_POLICY.md`](FAILURE_RERUN_POLICY.md) §4;
[`MODEL_EXECUTION_CONTROLS.md`](MODEL_EXECUTION_CONTROLS.md) §7;
[`RESET_PROTOCOL.md`](RESET_PROTOCOL.md).

---

## 1. What these two decisions settle

`SL-PT08-01` authorised one pre-Stage-0, `PT08`-only, `C1`-only,
**non-confirmatory** difficulty diagnostic and quarantined its observations. Two
questions were left open, and each is now blocking the *preparation* of that
diagnostic rather than its science:

1. **Which schema is authoritative for the diagnostic's execution record?** The
   runner emits a harness-local `run_record.json`. The pinned canonical
   result-manifest schema carries none of §9's quarantine fields and sets
   `additionalProperties: false`, so an artifact validating against it could not
   carry the firewall at all.
2. **How many repetitions does the diagnostic run?** `SL-PT08-01` §11 pinned
   none.

`SL-PT08-02` answers the first. `SL-PT08-03` answers the second. Neither answers
anything else.

---

## 2. `SL-PT08-02` — the authoritative execution-record schema for this diagnostic

### 2.1 The decision

> **`SL-PT08-02`.** For `run_purpose` = **`PT08_DIFFICULTY_DIAGNOSTIC`** and for
> that purpose **only**:
>
> - the diagnostic is **not an experimental result**;
> - `is_result` is **`false`** and `scored` is **`false`**;
> - its artifact must **never** be written under `experiments/v2/results`, under
>   `experiments/v2/analysis`, or in any other confirmatory or result-bearing
>   location, and must **never** be treated as a confirmatory analysis artifact;
> - the existing harness schema
>   [`experiments/v2/harness/run_record.schema.json`](../../experiments/v2/harness/run_record.schema.json),
>   which **already mechanically requires** the quarantine and firewall fields,
>   is the **authoritative execution-record schema for this diagnostic only**;
> - the pinned canonical
>   [`experiments/v2/schemas/run_manifest.schema.json`](../../experiments/v2/schemas/run_manifest.schema.json)
>   remains **UNCHANGED** and remains the **governed result-manifest schema for
>   future confirmatory and result-bearing runs**;
> - **no claim is made that the canonical run-manifest schema gap is fixed
>   globally**;
> - **no private-linkage baseline advance is authorised or required** merely for
>   this diagnostic-specific adjudication.

**The reason, stated as the reason.** `SL-PT08-01` defines this vehicle as a
quarantined non-confirmatory difficulty diagnostic, and the existing runner
record schema already mechanically enforces every quarantine field. Changing a
**pinned confirmatory** schema for an explicitly **non-confirmatory** artifact
would edit governed bytes that the private evaluator's public linkage pins, in
order to accommodate an artifact that is not a result — when the schema the
artifact actually validates against already fails closed correctly.

### 2.2 The applicability table

Machine-readable. The runner re-derives these values from this table, so a drift
between the adjudication and the code is a mechanical failure rather than a
reading.

| Field | Required value |
|---|---|
| `run_purpose` | `PT08_DIFFICULTY_DIAGNOSTIC` |
| `authoritative_execution_record_schema` | `experiments/v2/harness/run_record.schema.json` |
| `canonical_run_manifest_schema` | `UNCHANGED` |
| `canonical_result_schema_requirement` | `NOT WAIVED FOR CONFIRMATORY/RESULT-BEARING RUNS` |
| `canonical_schema_gap_globally_resolved` | `false` |
| `diagnostic_result_status` | `non-result` |
| `is_result` | `false` |
| `scored` | `false` |
| `confirmatory_eligible` | `false` |
| `enters_confirmatory_dataset` | `false` |
| `enters_confirmatory_e1_analysis` | `false` |
| `enters_treatment_effect_analysis` | `false` |
| `enters_power_estimation` | `false` |
| `private_linkage_baseline_advance_required` | `false` |

### 2.3 The canonical result-manifest schema is UNCHANGED and NOT WAIVED

Stated separately so it cannot be dropped when the decision above is quoted.

- The canonical schema is **not edited** by this record and is **not edited** by
  the package that records it.
- The canonical schema's missing quarantine fields are **a real, open gap** for
  any future confirmatory or result-bearing run. That gap is **UNRESOLVED**.
- This record **does not remediate** that gap, **does not waive** it, and **does
  not reduce** its scope. It records only that the gap is **not applicable** to
  an artifact that is not a result and does not validate against that schema.
- Any future **confirmatory or result-bearing** run purpose remains subject to
  the canonical result-manifest schema requirement **in full**. A later package
  that introduces such a purpose must resolve the canonical gap on its own
  terms, with whatever review and re-linkage that requires.
- Nothing here is precedent for binding a **result-bearing** artifact to a
  harness-local schema.

---

## 3. `SL-PT08-03` — the diagnostic repetition count

### 3.1 The decision

> **`SL-PT08-03`.** The `PT08` `C1` difficulty diagnostic runs **three
> independent repetitions**.
>
> Each repetition must use: a **fresh process**; a **fresh session**; **no**
> `--resume`; **no** `--continue`; **no** session reuse; the **identical frozen
> `PT08` task**; **`C1` only**; the **same selected primary model**; and the
> **same governed execution settings**.

### 3.2 The applicability table

| Field | Required value |
|---|---|
| `diagnostic_repetitions` | `3` |
| `condition` | `C1` |
| `task` | `PT08` |
| `model` | `one primary model, NOT SELECTED` |
| `process_per_repetition` | `fresh` |
| `session_per_repetition` | `fresh` |
| `resume_permitted` | `false` |
| `continuation_permitted` | `false` |
| `session_reuse_permitted` | `false` |
| `power_claim` | `none` |
| `precision_claim` | `none` |
| `treatment_effect_claim` | `none` |

### 3.3 What the three observations are permitted to inform

Exactly the purposes `SL-PT08-01` §2 and §10 already pin, and nothing wider:

- `PT08` baseline difficulty;
- floor/ceiling assessment;
- whether `C1` produces sufficient discriminative pressure;
- whether `PT08` should be retained, revised or retired;
- whether further benchmark investment is justified.

### 3.4 What the three observations must never enter

- the **confirmatory dataset**;
- **confirmatory `E1` analysis**;
- **treatment-effect analysis**;
- **power estimation**.

### 3.5 What three repetitions is, and is not

**No power calculation was performed to justify this count, and none is
implied.** The count is a Study-Lead judgement about how much repeated
observation is worth spending on an instrument check before the instrument is
frozen. It is **not** derived from a power analysis, it **licenses no power
claim**, it **licenses no precision claim**, and it **licenses no
treatment-effect claim**.

**The three observations are repeated difficulty probes of one instrument under
one condition.** They are **not** three independent architecture constructs.
Repeating an observation of one instrument adds **repetition depth only**.

**The `E1` accounting is untouched.** This record states no active opportunity
count, no decision-cluster count and no observation depth; it changes none, and
it neither confirms nor updates any public count. The existing pseudo-replication
governance is unchanged in every respect.

---

## 4. Requirements neither record waives

Every remaining item on `SL-PT08-01` §7 stays a prerequisite **for the diagnostic
itself**, and recording these two decisions does **not** make the diagnostic
executable. Outstanding, and untouched here:

1. **primary-model selection by the Study Lead** (`TD-B03`) — `primary_model`
   stays **null**;
2. a **clean, governed, isolated execution environment and identity**
   (`TD-B19`), demonstrated per run and never asserted in advance;
3. **`Q1`** resolved-model-id readback and **`Q8`** invalid-model-id rejection,
   **validated against a live runtime** (`TD-B21`,
   [`MODEL_EXECUTION_CONTROLS.md`](MODEL_EXECUTION_CONTROLS.md) §7);
4. **`PT08`'s required manifest freeze** under the existing lifecycle rules
   (`TD-B05`/`TD-B14`/`TD-B32`, gate `G1`).

---

## 5. Prohibitions attaching to these records

Stated so no later reader can extract a licence these records do not grant.

- **The canonical confirmatory run-manifest schema is NOT fixed**, not
  remediated and not waived. Its gap is **UNRESOLVED**.
- **No pinned public schema was edited.**
- **No model is selected.** `primary_model` stays null and `TD-B03` stays open.
- **No isolated execution environment has been established**, and isolation is
  not asserted to be clean.
- **`Q1` and `Q8` are NOT live-validated.**
- **`PT08` is not frozen**, and nothing here freezes anything.
- **Gate `G1` is not passed**, and no gate is passed.
- **`PT08` is not run eligible.**
- **The diagnostic has not been executed**, here or anywhere in this repository.
- **No result exists**, no violation value, no success value, no outcome value
  and no treatment-effect estimate.
- **No power simulation was run, no power calculation was performed, and no
  power value is produced.**
- **`TD-B34` is not closed** and is not weakened. *As recorded then* **priority B was not started**; the later `SL-QUAL-01` package authored `PT10`, so **priority b is started and is not complete**, and **this diagnostic neither started nor completed it**.
- **The global `TD-B32` row stays open**; **`TD-B12`/`G6` are unchanged**.
- **No private-linkage baseline is advanced** and **no re-link is performed**.
- **No accounting synchronization is performed here.**
- Nothing here is frozen, and the protocol remains **PRE-FREEZE**.
