# `PT08` — diagnostic outcome and confirmatory disposition

**Authority:** Study Lead decision `SL-PT08-07`.
**Status of this document:** a governance record. It **freezes nothing**, passes
**no gate**, closes **no** open decision, and creates **no** result.

This record states what the `PT08` `C1` difficulty diagnostic observed, what the
Study Lead decided about `PT08` as a consequence, and — just as importantly —
what that decision explicitly does **not** do to `PT08`.

---

## 1. What was run

The `C1` difficulty diagnostic authorised by
[`PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md`](PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md)
and unblocked by the diagnostic-scoped freeze `SL-PT08-06`
([`PT08_DIAGNOSTIC_SCOPED_FREEZE_DECISION.md`](PT08_DIAGNOSTIC_SCOPED_FREEZE_DECISION.md))
was executed: **three repetitions**, condition `C1` only, the pinned diagnostic
model and runtime, sterile subscription execution, artifacts quarantined outside
both repositories.

Every artifact it produced carries `run_purpose = PT08_DIFFICULTY_DIAGNOSTIC` and
its five quarantine flags, so **none** of it is confirmatory, **none** enters the
E1 analysis, **none** enters treatment-effect estimation and **none** enters power
estimation. That was true when it was written and is unchanged by this record.

## 2. What it observed

- **Functional completion: 3 of 3.** Hidden functional acceptance passed in full
  on every repetition.
- **Architecture: 1 applicable opportunity, 0 violated, on every repetition.**
  The descriptive violation proportion is `0.0` — the **architecture floor**.
- **Every repetition enforced the ceiling at the request boundary.** The
  use-case scope was never entered, so the decision the instrument exists to
  expose was never taken.

Those are **exploratory observations about an instrument**, never an outcome
value for `PT08` and never evidence about any experimental condition. `C1` is a
baseline, and a baseline at the floor has no room beneath it.

## 3. The decision

> **`PT08` = REVISE.** **Benchmark investment = CONTINUE.**

`PT08` is **functionally valid** and **not** defective. What the diagnostic
established is narrower and more useful: **unchanged, `PT08` is unsuitable as a
confirmatory architecture-discrimination instrument**, because its baseline sits
at the architecture floor and therefore cannot discriminate.

This was the pre-registered risk. `SL-CA1-02` recorded, **before** any execution,
that `PT08`'s forcing class is **natural-path / opportunity-creating** rather than
**strict**, that a legal boundary-only implementation exists and is **cheaper**
than the feature-side one, and that discriminative difficulty was to be evaluated
**only** through this baseline-only `C1` pilot. The diagnostic confirmed the
pre-registered risk empirically, cheaply, and before Stage 0 — which is what it
was for.

## 4. `PT08`'s recorded disposition

| Property | Value |
| --- | --- |
| Task status | `candidate` (unchanged) |
| Public body | **preserved byte-for-byte**; SHA-256 `a31bb515b79cc1e2...` unchanged |
| Private evaluator package | **preserved**; `status=review`, `not_yet_frozen`, unchanged |
| Diagnostic evidence | **preserved**, quarantined, never promoted |
| Diagnostic disposition | `DIAGNOSTIC-VALIDATED` |
| Confirmatory disposition | `REVISE` — **NOT a confirmatory candidate unchanged** |
| Confirmatory-candidate set | **excluded** (see §5) |
| Admitted active E1 register | **unchanged** — the historical admission stands |

### What `REVISE` means here, exactly

- **It is not `INVALID`.** `PT08` is functionally valid, its hidden acceptance is
  validated, its oracle linkage works, and its diagnostic ran end to end.
- **It is not `RETIRED`.** The repository distinguishes *revise* from *retire*,
  and nothing about `PT08` is being retired: no body is deleted, no package is
  invalidated, no manifest is marked `invalidated`, and no artifact is removed.
- **It is not a finding about the benchmark.** The runner, sterile execution,
  model pinning, hidden acceptance, the architecture oracle, the artifact firewall
  and the diagnostic quarantine all worked end to end. This is a **task-design**
  finding about **one instrument**.
- **It is instrument-development evidence.** `PT08` remains the worked record of
  how a natural-path features-to-application instrument behaves at baseline, and
  it is the direct reason the replacement instrument was designed the way it was
  ([`QUALIFICATION_CANDIDATE_CONSTRUCTION.md`](QUALIFICATION_CANDIDATE_CONSTRUCTION.md)).

### What may never be done to it

- Its public body, its private package, its freeze record and its diagnostic
  artifacts **must not** be modified, overwritten, repurposed or deleted.
- Its diagnostic observations **must never** be retrospectively promoted to
  confirmatory status, re-labelled as a result, or entered into any denominator,
  numerator, dataset or power estimate.
- A **revised** `PT08` would be a **new body with a new hash** and would need the
  full author / independent review / re-link / freeze path before any confirmatory
  use. No such revision is authored here.

## 5. Effect on opportunity accounting

Two registers are kept apart, because they answer different questions.

**The admitted active E1 register is UNCHANGED by this record.** It still holds
**6** opportunities over **3** decision clusters at depths **3 / 2 / 1**, `PT08`'s
admitted row included. An admission that happened is a historical fact and is not
rewritten by a later diagnostic.

**The confirmatory-candidate set EXCLUDES unchanged `PT08`.** That set is the
forward-looking answer to "what could carry the confirmatory construct", and
unchanged `PT08` cannot, for the reason in §3. Its composition after the
qualification-candidate package is recorded in
[`QUALIFICATION_CANDIDATE_CONSTRUCTION.md`](QUALIFICATION_CANDIDATE_CONSTRUCTION.md)
§6.

`PT08`'s opportunity is therefore **withdrawn from the confirmatory-candidate
set** while **remaining** an admitted historical row. Neither statement may be
read off the other.

## 6. What this record does not change

- Gate `G1` is **not** passed. Gates `G2` and `G6` are unchanged.
- `TD-B34` stays **open and blocking**. The diagnostic did not satisfy the
  replication-depth objective; it removed one of the observations that was
  supposed to serve it.
- The global `TD-B32` row stays **open**; `TD-B12`/`G6` are unchanged; `TD-B03`
  is unchanged.
- No reserve is activated. `PR01` and `PR02` stay inactive, and `PR02` stays
  blocked under `TD-B26`.
- No power simulation may run (`TD-B37`).
- No confirmatory evidence collection begins.

## 7. One mechanical defect the diagnostic exposed

`run_artifacts.derive_run_id` hashed only the run's content identity, so all three
repetitions minted the **same** `run_id`; they stayed separable only because each
was handed its own `--artifact-root`. That is an **artifact-identity** defect, not
a scientific one, and it is fixed under `SL-RUNID-01` before any multi-repetition
qualification or confirmatory run. The `PT08` diagnostic artifacts are **not**
rewritten: they keep the ids they were written with.
