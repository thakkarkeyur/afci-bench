# docs/v2 — `SL-PT08-01`: the pre-Stage-0 `PT08` `C1` difficulty diagnostic

Status: **Study-Lead governance adjudication for study v2.** This record is
governance only. It authors **no** task body, changes **no** task body or hash,
builds **no** runner, runs **no** model, executes **no** benchmark condition,
validates **no** hidden acceptance, freezes **nothing**, passes **no** gate,
produces **no** result and **no** power value, activates **no** reserve, and
touches **no** file under `apps/`, `libs/`, the oracle or the canonical
substrate. The protocol remains **PRE-FREEZE**.

Decision identifier: **`SL-PT08-01`**, in the repository's existing Study-Lead
convention `SL-<subject>-<nn>` (`SL-CA1-01`, `SL-CA1-02` in
[`CAND_A1_PREAUTHORING_DECISION.md`](CAND_A1_PREAUTHORING_DECISION.md) §3–§4).
It is the smallest identifier consistent with that convention for a decision
whose subject is the public task body `PT08`.

Related: [`CAND_A1_PREAUTHORING_DECISION.md`](CAND_A1_PREAUTHORING_DECISION.md)
§4 (`SL-CA1-02`), [`PILOT_AND_POWER_POLICY.md`](PILOT_AND_POWER_POLICY.md)
(Stage 0, Stage 1, pre-Stage-0 instrument diagnostics),
[`CRITICAL_DESIGN_DECISIONS.md`](CRITICAL_DESIGN_DECISIONS.md) D3,
[`MODEL_EXECUTION_CONTROLS.md`](MODEL_EXECUTION_CONTROLS.md) §7 Q1/Q8,
[`ORACLE_VALIDATION_REQUIREMENTS.md`](ORACLE_VALIDATION_REQUIREMENTS.md),
[`FAILURE_RERUN_POLICY.md`](FAILURE_RERUN_POLICY.md) §4/§7,
[`OPEN_DECISIONS.md`](OPEN_DECISIONS.md).

---

## 1. The circularity this record resolves

The repository as it stood created a closed loop:

1. `SL-CA1-02` records that `PT08`'s discriminative difficulty may be evaluated
   **only** through baseline `C1` evidence, and **never** through `C4` or any
   treatment-effect result.
2. The only vehicle that record named for that baseline evidence is the
   **Stage-1 screening pilot**.
3. Stage 1 sits **after** Stage 0.
4. Stage 0 is gated on `DECISION B` (`TD-B34`), which is open and blocking and
   requires priority-B replication work.

So the instrument's own baseline difficulty could not be checked until further
benchmark expansion was complete — even though that difficulty check is one of
the inputs that should decide whether such expansion is worth the investment.
The pilot-readiness review classified this as a **Study-Lead adjudication
question**, not something derivable from the existing text. This record carries
the Study Lead's approved adjudication of it.

---

## 2. `SL-PT08-01` — the authoritative decision

> **`SL-PT08-01`.** One pre-registered, `PT08`-only, `C1`-only,
> **non-confirmatory** difficulty diagnostic is permitted **before** `TD-B34`
> closure.
>
> Its outputs may be used **only** to evaluate: `PT08` baseline difficulty;
> floor/ceiling behaviour; whether `C1` produces sufficient discriminative
> pressure; whether `PT08` should be retained, revised or retired before final
> freeze; and whether additional benchmark expansion is worth further
> investment.
>
> Its outputs **must not**: enter the confirmatory dataset; enter confirmatory
> `E1` effect estimation; be pooled with the later Stage-1 or core-grid
> observations; be reported as a `C1`-versus-`C4` treatment effect; be used to
> estimate AFCI benefit; be used for confirmatory interaction estimates;
> discharge `TD-B34`; discharge priority B; pass Stage 0; pass `G1`; or
> discharge the global power-analysis gates.
>
> If `PT08` is changed on the strength of this diagnostic, the changed task and
> the changed evaluator must receive **new hashes** and must pass the applicable
> review, re-link and freeze process **before** any later confirmatory run.

**Scope, stated as a bound.** The authorisation is for **one** instrument
(`PT08`), **one** condition (`C1`), and **one** purpose (instrument difficulty).
It extends to no other task, no other condition, and no other question.

---

## 3. Where the diagnostic sits — not Stage 0, not Stage 1, not the core grid

The confirmatory sequence is **Stage 0 → Stage 1 → core grid**
([`PILOT_AND_POWER_POLICY.md`](PILOT_AND_POWER_POLICY.md)). This diagnostic is
**outside** that sequence and is deliberately **not** called Stage 1, because
Stage 1 is the paid screening pilot over `C1`/`C3`/`C4` for both candidate
models, and calling this by that name would conflate two different instruments.

Its governed name is the **pre-Stage-0 `PT08` `C1` difficulty diagnostic**.

| Property | Stage 0 | Stage 1 screening pilot | This diagnostic |
|---|---|---|---|
| **Purpose** | prove the machinery works | screen models and conditions | measure one instrument's baseline difficulty |
| **Conditions** | none scored | `C1`, `C3`, `C4` | **`C1` only** |
| **Tasks** | none scored | the pilot task set | **`PT08` only** |
| **Evidence class** | non-evidentiary | pre-confirmatory pilot evidence | **non-confirmatory, exploratory** |
| **Feeds effect estimation** | no | informs design, never the effect | **no, and barred from it** |
| **Position** | first in the sequence | after Stage 0 | **outside the sequence** |
| **Gated on `TD-B34`** | yes | yes | **no — the one bounded exception** |

**It is a pre-confirmatory instrument-difficulty diagnostic only.** It is not a
dry run, not a screening pilot, not a pilot cell, and not a step of the staged
progression. Completing it advances no stage.

---

## 4. `SL-CA1-02` is clarified, not rewritten

`SL-CA1-02`'s scientific intent is preserved in full:

- **baseline-only `C1` evidence may inform `PT08` difficulty**;
- **`C4` and treatment-effect results may never tune `PT08`** — an observed AFCI
  advantage, a condition contrast and an interaction estimate all remain
  inadmissible inputs to task tuning.

**As recorded then**, the only vehicle `SL-CA1-02` named for that baseline
evidence was the pre-registered Stage-1 baseline-only `C1` pilot, and that
sentence stands unedited in
[`CAND_A1_PREAUTHORING_DECISION.md`](CAND_A1_PREAUTHORING_DECISION.md) §4. It is
history that still describes the confirmatory path correctly, and it is not
deleted, reworded or presented as though it had never been written.

**Clarified on this point only, and on no other:** the approved pre-Stage-0
`PT08`-only `C1` diagnostic is now an **additional authorised vehicle** for
satisfying the **baseline-difficulty purpose** of `SL-CA1-02`. The clarification
changes the vehicle, never the evidence class: the admissible evidence is still
baseline `C1` behaviour and nothing else.

Every other element of `SL-CA1-02` is untouched and remains binding — the
natural-path forcing class, the construct-validity limitation, the prohibition
on representing `PT08`'s forcing strength as equal to a `features → infra`
instrument's, and the pseudo-replicate status of within-cluster observations.

---

## 5. `TD-B34` — the exception boundary, stated precisely

`TD-B34` **remains OPEN and BLOCKING** for:

- **Stage 0**;
- **normal Stage 1**;
- **final pilot progression**;
- **confirmatory execution**;
- **the power simulation, where applicable**.

`TD-B34` does **not** block **this one** specifically authorised
non-confirmatory `PT08` difficulty diagnostic.

**What the exception is not.** It:

- does **not** mark priority B complete;
- does **not** weaken `TD-B34`'s final closure conditions in any respect;
- does **not** count the diagnostic as a replication observation;
- does **not** change any decision-cluster observation depth;
- does **not** create an additional active opportunity;
- closes **no** `TD-B34` subcondition — **none**;
- is **not** precedent for any second exception; a further diagnostic would need
  its own Study-Lead adjudication.

**The active architecture accounting is unchanged by this record.** This record
states no count, moves no count, and reconciles no count; see §11.

---

## 6. `TD-B12` / `G6` — the narrow diagnostic exception

The Study Lead also approved this narrow rule: **for this `PT08`-only
non-confirmatory diagnostic only**, completion of the **global** `TD-B12` / `G6`
precision-and-recall bar is **not required before the diagnostic**.

**Evidence basis, recorded exactly as supplied.** The narrow exception rests on
`PT08`'s **task-specific architecture corpus**, which is held in the private
evaluator repository and was covered by the private-side independent review of
that corpus. Its recorded outcomes, as supplied to the Study Lead, are:

| Corpus case | Applicable | Violated |
|---|---|---|
| a conforming implementation | **1** | **0** |
| the pre-declared boundary-only family `ALT-C` | **1** | **0** |
| a direct forbidden-direction edge | **1** | **1** |
| a forbidden-direction edge in a newly created source file | **1** | **1** |

**Full corpus: 11 of 11 cases resolve as expected.** No case resolves
`NOT_APPLICABLE`, and the denominator is exactly **1** in every case.

**What this exception explicitly does not do.**

- It does **not** discharge `TD-B12`, which stays open and blocking.
- It does **not** pass `G6`, which stays open and blocking.
- It does **not** permit confirmatory scoring before `G6`.
- The **global** precision/recall requirement, the labelled-corpus requirement
  and the blinded double-rating requirement all remain **mandatory at their
  existing final-study gate**, unchanged in scope and unchanged in bar.
- Task-specific evidence about one instrument is **not** global guard
  validation, and this record does not present it as any part of one.

---

## 7. Requirements that are **not** waived

Every one of the following remains a prerequisite **for the diagnostic itself**.
Recording this decision does **not** make the diagnostic executable, and the
current mechanical state is **NO-GO** until they are completed:

1. a real **runner / execution harness** — none exists in this repository today;
2. **runner-time worktree enforcement** (`TD-B22`);
3. a **fresh process/session** — no `--resume`, no `--continue`, no session
   reuse ([`RESET_PROTOCOL.md`](RESET_PROTOCOL.md));
4. a **clean context audit**, failing closed on `CONTAMINATED`;
5. an **isolated container / VM** as governed (`TD-B19`);
6. a **dedicated, uncontaminated identity** as governed (`TD-B19`);
7. **absence of managed / account-tied policy contamination** (`TD-B19`);
8. **primary-model selection by the Study Lead** (`TD-B03`);
9. **exact model-id input with runtime readback validation**
   ([`MODEL_EXECUTION_CONTROLS.md`](MODEL_EXECUTION_CONTROLS.md) §7 **Q1**,
   `TD-B21`);
10. **invalid-model-id rejection**, validated (§7 **Q8**, `TD-B21`);
11. **`PT08` hidden functional acceptance fixture authoring** (`TD-B05`);
12. **`PT08` reference-pass / reference-fail / mutation validation**;
13. the **required independent review of that hidden-acceptance validation**
    (`TD-B32`);
14. **`PT08`'s required manifest freeze** under the existing lifecycle rules
    (`TD-B05`/`TD-B14`/`TD-B32`, gate `G1`);
15. **public `PT08-PUB-P2-2` synchronization before that freeze** — the **one**
    item on this list that is now **COMPLETE and CLOSED**
    ([`PT08_PUBLIC_ACCOUNTING_SYNCHRONIZATION.md`](PT08_PUBLIC_ACCOUNTING_SYNCHRONIZATION.md));
    its closure discharges **nothing else here** and confers **no** readiness;
16. **`PT08` public/private hash and linkage consistency**;
17. **no signed non-finite hidden semantic cases while public `P2-1` remains
    open**;
18. **no out-of-scope numeric hidden cases** — the hidden functional evaluator
    may test only the publicly pinned forms;
19. **no persistence assertion** — the observation boundary stays HTTP-only
    ([`HIDDEN_EVALUATOR_BOUNDARY.md`](HIDDEN_EVALUATOR_BOUNDARY.md) §9–§14);
20. the **existing observation-isolation requirements**, in full.

**Nothing above is relaxed by this record, and this record confers no readiness.**

---

## 8. Requirements that are **not** prerequisites for this diagnostic

The following are **not** required before the diagnostic, and **none of their
statuses is changed by this record**:

- priority-B candidate authoring or review;
- `TD-B34` closure;
- migration of the eight legacy `TD-B39` packages;
- `PT03` repair;
- `PR02` activation;
- `C2` token-matching work (`TD-B08`);
- `C3` execution;
- `C4` execution;
- treatment-effect analysis;
- the global power simulation (`TD-B37`);
- the small-cluster power work (`TD-B41`);
- the final task-count decision (`TD-B14`);
- the final core-grid repetition count (`TD-B10`);
- the final confirmatory gates `G3`, `G4`, `G5`, `G7` and `G8`.

Each of these remains exactly as it was: open where it was open, blocking where
it was blocking, unstarted where it was unstarted.

---

## 9. The diagnostic data firewall (analytic quarantine)

Diagnostic observations are **analytically quarantined**. Any run produced under
`SL-PT08-01` must be marked, in its run metadata, with all of:

| Field | Required value |
|---|---|
| `run_purpose` | `PT08_DIFFICULTY_DIAGNOSTIC` |
| `confirmatory_eligible` | `false` |
| `enters_confirmatory_dataset` | `false` |
| `enters_confirmatory_e1_analysis` | `false` |
| `enters_treatment_effect_analysis` | `false` |
| `enters_power_estimation` | `false` |

**No result schema and no runner artifact is invented here.** The run-manifest
schema carries no such fields today, so the six above are recorded as
**mandatory future runner requirements**, to be added by the package that builds
the runner — not as speculative runtime files, and not by editing a schema in
this governance-only package. They sit alongside, and do not replace, the
existing closed exclusion vocabulary in
[`FAILURE_RERUN_POLICY.md`](FAILURE_RERUN_POLICY.md) §4.

**The future runner must fail closed.** If a diagnostic artifact could be
mistaken for a confirmatory artifact — the purpose marker missing, unreadable,
or inconsistent with the eligibility flags — the runner must refuse to produce
or to score it, rather than defaulting to confirmatory. An unmarked artifact is
an error, never a confirmatory observation.

---

## 10. Permitted and prohibited diagnostic evidence, pre-registered

**The Study Lead may inspect, and only these:**

- functional completion rate;
- `PT08` hidden-acceptance pass/fail;
- `PT08` applicable opportunity count;
- `PT08` violated opportunity count;
- `PT08` architecture-violation proportion under `C1`;
- floor/ceiling behaviour;
- qualitative failure modes, to the extent needed to determine whether `PT08` is
  unusably easy, unusably hard, or structurally non-discriminating.

**Not permitted, in any form:**

- comparison against `C4`;
- any AFCI effect;
- any condition contrast;
- any treatment-effect estimate;
- any interaction estimate;
- selecting or shaping requirements because they maximise an AFCI advantage.

**If the diagnostic motivates a `PT08` modification**, the original diagnostic
observations stay **exploratory and non-confirmatory** — they are not
retrospectively promoted by the change they motivated — and the modified `PT08`
must go through the normal author, review, hash and re-link process before any
confirmatory use.

---

## 11. Sample size, model selection, and accounting

**Sample size: STUDY-LEAD DECISION PENDING.** Current governance carries
provisional Stage-1 repetitions of **three per cell** (`TD-B10`), and there is
**no** governed sample size for a `PT08`-only `C1` diagnostic. This record pins
none, and this adjudication is **not** blocked on that later choice.

**Model selection: a separate Study-Lead decision, taken before execution.**
`primary_model` stays **null** and `TD-B03` stays **open**. No model is selected
here. The selection criterion must remain **independent of any desired AFCI
effect size** (D10).

**No accounting synchronization is performed here.** This record states no active
opportunity count, no decision-cluster count and no observation depth; it changes
none, and it neither confirms nor updates any public count or lifecycle row for
`PT08`. The public accounting synchronization **`PT08-PUB-P2-2` remains REQUIRED
and is NOT performed in this package**, and it must precede `PT08`'s freeze
(§7.15). Any residual difference between the public accounting rows and the
private state is owned by that synchronization and is not resolved here.

> **Superseded on this point only, and on no other.** `PT08-PUB-P2-2` has since
> been performed and **CLOSED** by a separate public accounting-synchronization
> package
> ([`PT08_PUBLIC_ACCOUNTING_SYNCHRONIZATION.md`](PT08_PUBLIC_ACCOUNTING_SYNCHRONIZATION.md)).
> The paragraph above remains an accurate record of what **this** package did — it
> performed none of it — and every other statement in this record stands unchanged.
> This record still states **no** active opportunity count, **no** decision-cluster
> count and **no** observation depth, and it still confirms and updates none. That
> closure freezes nothing, passes no gate, validates no hidden acceptance, makes
> nothing run-eligible, produces no result and no power value, and leaves `TD-B34`
> **open and blocking** and priority B **not started**.

---

## 12. Prohibitions attaching to this record

Stated so no later reader can extract a licence this record does not grant.

- **The diagnostic cannot run now.** Every item in §7 is outstanding.
- **No runner exists.**
- **Isolation is not asserted to be clean**; it must be demonstrated per run.
- **`PT08` hidden acceptance is not validated.**
- **`PT08` is not frozen.**
- **Gate `G1` is not passed**, and no gate is passed.
- **`TD-B34` is not closed** and is not weakened.
- **Priority B is not complete** and is not started.
- **`TD-B12` is not discharged** and **`G6` is not passed**.
- **No model is selected** and no sample size is selected.
- **No experiment has been run and no result exists**, here or anywhere in this
  repository.
- **No power simulation was run and no power value is produced.**
- Nothing here is frozen, and the protocol remains **PRE-FREEZE**.
