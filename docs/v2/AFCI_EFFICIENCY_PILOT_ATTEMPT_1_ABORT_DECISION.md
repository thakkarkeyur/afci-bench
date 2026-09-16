# SL-V2-EFF-ABORT-01 — Attempt 1 of the AFCI efficiency pilot is aborted

**Decision id:** `SL-V2-EFF-ABORT-01`
**Decided by:** Study Lead
**Status:** decided
**Scope:** the `AFCI_EFFICIENCY_PILOT` run purpose, execution attempt 1, only
**Authorises no execution.** The replacement is authorised separately, by
`SL-V2-EFF-RESTART-01`, and that decision is recorded *after* this one for a
reason given in §8.

---

## 1. The decision

Execution attempt 1 of the frozen 36-run `AFCI_EFFICIENCY_PILOT` schedule is
**ABORTED**, on the ground of deterministic infrastructure corruption of its
artifact identity. It is excluded **wholesale** from every efficiency analysis.

Its classification is:

```
ABORTED_INFRASTRUCTURE_ATTEMPT
```

This classification is introduced here because no existing one fits. It is
explicitly **not** any of `INCONCLUSIVE`, `STOP`, `STRONG GO`, `QUALIFIED GO` or
`RESET-SPECIFIC GO`. Those five are outcomes of a **completed pilot's analysis**
— they are statements about what the observations showed. Attempt 1 produced no
analysis at all (§5), so every one of them would be a claim about evidence that
was never computed. An abort is a statement about the *instrument*, not about
the *effect*.

### 1.1 The decision table

| key | value |
| --- | --- |
| `decision_id` | `SL-V2-EFF-ABORT-01` |
| `run_purpose` | `AFCI_EFFICIENCY_PILOT` |
| `execution_attempt` | 1 |
| `disposition` | `ABORTED_INFRASTRUCTURE_ATTEMPT` |
| `abort_ground` | deterministic infrastructure corruption |
| `scheduled_rows` | 36 |
| `rows_attempted` | 9 |
| `rows_not_started` | 27 |
| `intact_governed_observations` | 7 |
| `damaged_observations` | 2 |
| `collision_pairs_in_schedule` | 18 |
| `comparative_analysis_performed` | false |
| `token_ratio_analysis_performed` | false |
| `pilot_decision_emitted` | false |
| `continuation_threshold_evaluated` | false |
| `excluded_from_every_efficiency_analysis` | true |
| `poolable_with_replacement_execution` | false |
| `any_artifact_reconstructed` | false |
| `is_result` | false |
| `scored` | false |

The same values are carried as data by
`docs/v2/AFCI_EFFICIENCY_PILOT_ATTEMPT_1_EVIDENCE_INVENTORY.json`, which is
derived from the artifacts themselves rather than from this document, so a
disagreement between the two is a mechanical failure rather than a reading.

---

## 2. The root cause

`run_artifacts.derive_run_id` seeded a run's identity with

```
run_purpose | task_id | condition | task_sha256 | substrate_content_hash | mode | repetition
```

and **omitted the reset state**.

The `AFCI_EFFICIENCY_PILOT` crosses every cell with `NON_RESET` and `RESET`
(`SL-V2-EFF-01` §4). So for each of the 18 (task, condition, repetition) cells,
the two arms hashed to one run id and therefore to one artifact directory:

```
36 scheduled rows  ->  18 distinct run ids  ->  18 collisions
```

The omission was not a coincidence of the pilot's design; it was invisible to
every check that existed. `SL-RUNID-01` had added the repetition index to the
seed for exactly this class of defect, and correctly, but it was decided when no
registered purpose crossed a reset factor — so nothing in the repository
compared a schedule's derived identities against each other before running it.

### 2.1 Why the defect surfaced at sequence 9 and not sequence 1

A collision only becomes visible when the *second* member of a pair executes.
Sequence 9 (`PT01 / C4 / NON_RESET / R2`) is the first row in the frozen order
whose partner had already run — sequence 6 (`PT01 / C4 / RESET / R2`), three rows
earlier. Sequences 1–5 and 7–8 all had partners scheduled later (at 10, 17, 18,
19, 20, 23–36), so they executed into directories that were genuinely empty and
are genuinely intact.

That is worth stating plainly: the eight rows before sequence 9 are not intact
because anything protected them. They are intact because of the order the
schedule happened to draw.

---

## 3. What the collision did, in order

Sequence 6 ran to `COMPLETE` and wrote its governed record. Sequence 9 then
derived the same directory and:

1. **`PRECHECK`** — created nothing new (the directory already existed), and
   overwrote `readiness.json`, `prompt_manifest.json` and `prompts/`;
2. **`PREPARE_WORKTREE`** — recursively deleted sequence 6's prepared
   `worktree/` and rebuilt its own in place, and overwrote
   `prepared_manifest.json`;
3. **`CONTEXT_AUDIT`** — overwrote `context_audit.json`;
4. **`BUILD_FRESH_LAUNCH`** — overwrote `launch_manifest.json`;
5. **`MODEL_INVOCATION`** — **delivered the task and ran the model to
   completion**, writing `runtime_evidence.jsonl`;
6. **`MODEL_IDENTITY_VALIDATION`** — passed;
7. **`CAPTURE_WORKTREE`** — **refused**, `PREPARED_WORKTREE_DIRTY`, because the
   capture destination `worktree_post_run/` was not empty. It was not empty
   because it held sequence 6's captured worktree;
8. the refusal handler then wrote sequence 9's **refusal record** over sequence
   6's completed `run_record.json`.

The failure was therefore detected by the *last* control that could have caught
it, after the money had been spent, and the detection itself destroyed a record.

---

## 4. The two damaged rows, and why they are damaged differently

### 4.1 Sequence 6 — `PT01 / C4 / RESET / R2`

A **completed run whose governed record was overwritten**. Status
`DAMAGED_GOVERNED_RECORD_OVERWRITTEN`.

Its raw phase evidence (`phase_a_runtime_evidence.jsonl`,
`phase_b_runtime_evidence.jsonl`, both phase context audits),
`functional_evaluation.json`, `functional_evaluation_result.json` and
`worktree_post_run/` all survive, and are preserved.

They **must not** be used to reconstruct a governed scientific record.
Reconstructing one would mean assembling, by hand and after the fact, the single
artifact whose whole purpose is to be the run's own contemporaneous account of
itself. A record assembled from the evidence it is supposed to attest cannot
attest it. The row is recorded as damaged and left damaged.

### 4.2 Sequence 9 — `PT01 / C4 / NON_RESET / R2`

A **substantive post-delivery damaged observation**. Status
`DAMAGED_POST_DELIVERY_COLLIDING_OBSERVATION`.

This is not a pre-observation infrastructure-invalid attempt, and the difference
is material. The task **was** delivered, the model **did** run to completion, and
the turns **were** spent. What failed was the capture, afterwards, for a reason
having nothing to do with the run itself. Classifying it as "never really
happened" would understate what Attempt 1 consumed and would misdescribe a real
model execution as a non-event.

It is excluded from analysis for the same reason every other Attempt-1 row is —
not because it is invalid, but because the attempt is aborted (§6).

---

## 5. No analysis preceded this abort

Recorded explicitly, because an abort issued *after* a comparative result would
be a different and far less defensible act:

* **no `TOKEN_RATIO` analysis was performed;**
* **no C1-vs-C4 comparison was computed**, for any task, arm or repetition;
* **no pilot outcome was emitted;**
* **no continuation threshold was evaluated**, and no continuation decision was
  taken;
* no efficiency figure from Attempt 1 has been read, cited, summarised or
  compared against any other figure.

The abort rests on an infrastructure fact — 18 deterministic identity collisions
— that is fully established without looking at a single measured quantity, and
it was taken on that basis alone.

---

## 6. The exclusion rule

> **No observation from execution attempt 1 may enter any efficiency analysis,
> under any circumstance, in whole or in part.**

This covers the seven intact rows as well as the two damaged ones. The seven are
individually sound, and that is exactly why the rule has to be stated: the
tempting move is to keep them and run 29 more.

That move is refused, for three reasons.

1. **The seven are not a random seven.** They are the rows whose collision
   partners happened to be scheduled later. Which rows survived is a function of
   the frozen order interacting with the defect, and that is a selection
   mechanism nobody designed and nobody can adjust for.
2. **Pooling would break the pairing.** The analysis is paired within each of
   the 18 blocks. Attempt 1 holds three complete blocks and several half-blocks,
   so pooling would mix blocks measured in one session against blocks measured in
   another, which is the drift the within-block randomisation exists to prevent.
3. **A restart that keeps the convenient rows is not a restart.** It is
   selective replacement, and it is indistinguishable after the fact from
   replacing rows because of what they showed — even though, here, nobody has
   looked at what any of them showed (§5).

Attempt 1 is therefore excluded as an attempt, not row by row.

---

## 7. Evidence preservation

Every Attempt-1 artifact is **preserved exactly as found**. Nothing was deleted,
rewritten, normalised, repaired, renamed or re-derived, and no missing artifact
was reconstructed.

`AFCI_EFFICIENCY_PILOT_ATTEMPT_1_EVIDENCE_INVENTORY.json` records, per attempted
row: the derived identity, the artifact directory, whether a model was invoked,
which runtime-evidence streams exist and their SHA-256, whether a governed record
survives and which row it is attributable to, whether a functional evaluation and
a captured worktree exist and whether they are attributable to *that* row, the
collision partner, and the row's status.

The two rows that share a directory are inventoried separately and their
artifacts are attributed individually, because "the directory contains a captured
worktree" is true for both and answers the wrong question.

The evidence is preserved **for audit and provenance only**. It is not a dataset.

---

## 8. What this decision does not do

It does not authorise a replacement execution. That authorisation is
`SL-V2-EFF-RESTART-01` and is a separate record, written after this one, so the
order of the two is legible in the repository's own history: the abort is
justified by the infrastructure defect, and the restart is justified by the
abort. A single combined record would let a later reader wonder whether the
abort was reached in order to license the restart.

It also passes no gate, closes no open decision, changes no task body, no
condition, no budget, no checkpoint predicate, no metric, no threshold and no
part of the scientific design. `TD-B32`, `TD-B34`, `TD-B03`, `TD-B01`, `TD-B11`
and `G1`/`G2` are exactly as they were.

---

## 9. The defect is repaired, and the repair is not this document

`SL-V2-EFF-ABORT-01` is the disposition. The engineering it requires is:

| repair | where |
| --- | --- |
| the reset state joins the run-id seed and prefix | `run_artifacts.derive_run_id` |
| an execution-attempt namespace | `run_artifacts.derive_run_id`, `execution_attempt` |
| a pre-invocation artifact ownership guard | `run_artifacts.assert_destination_ownable` |
| destructive-reuse prevention | `run_artifacts.ArtifactDirectory.remove_temporary` |
| whole-schedule identity preflight | `execution_attempt.preflight` |
| execution-root isolation | `run_artifacts.assert_execution_root_isolated` |

Each is proved by tests in
`experiments/v2/harness/tests/test_efficiency_attempt_identity.py`, including a
reproduction of the pre-repair seed so the defect cannot later be described as
hypothetical.
