# SL-V2-EFF-FUNC-01 — what `FUNCTIONAL_VALID` means for the efficiency pilot

Status: **Study-Lead decision, PRE-DATA and NON-CONFIRMATORY.** It defines one
term the frozen pilot analysis already depends on, and it changes nothing that
[`AFCI_EFFICIENCY_PILOT_DECISION.md`](AFCI_EFFICIENCY_PILOT_DECISION.md) froze.

**Zero efficiency observations exist at the moment it is written.** That is not
a courtesy sentence: a definition of "did the run work" written after seeing how
runs went is a definition chosen to make them look a particular way. A test
asserts the zero mechanically rather than this record asserting it in prose.

It passes no gate. `G1` is not passed, `G2` is not passed, and `TD-B01`,
`TD-B11`, `TD-B34`, `TD-B32`, `TD-B12`/`G6`, `TD-B03`, `TD-B39` and `TD-B42` all
remain **OPEN**. The suite is **not** frozen. No task manifest is frozen. No
independent review is obtained and none is claimed.

Authority: `SL-V2-EFF-FUNC-01`
Pilot authority: `SL-V2-EFF-01` ([`AFCI_EFFICIENCY_PILOT_DECISION.md`](AFCI_EFFICIENCY_PILOT_DECISION.md))
Oracle authority: `SL-V2-ORACLE-01` (the validated `PT01`/`PT04`/`PT07` hidden
functional acceptance runtimes)

---

## 1. The gap this closes

The pilot's frozen analysis uses the phrase "functionally valid" four times and
makes the whole thing turn on it:

> §10.1 — A pair is **eligible** only if **both** of its runs are functionally
> valid. A cost figure from a run that did not work is not a cheaper way of
> doing the task.

> §11.0 — At least **12 of the 18** blocks must have both conditions
> functionally valid. Otherwise the outcome is **PILOT INCONCLUSIVE —
> INSUFFICIENT PAIRED FUNCTIONAL DATA**, and no efficiency claim of any kind is
> made.

Nothing said what the phrase meant, and nothing computed it. The consequence was
narrow and total: the pilot was **executable and not analysable**. All 36 runs
could have been performed, every cost figure recorded, and the first gate that
admits a cost figure would have had no input. The runs would have been real and
the money spent; the answer would not have existed.

Three facts made that fixable rather than structural:

1. the runner **preserves** the post-run worktree — `CAPTURE_WORKTREE` copies it
   to an immutable capture directory outside the coding worktree;
2. `PT01`, `PT04` and `PT07` have **validated hidden functional acceptance
   runtimes** ([`TASK_ACCEPTANCE_MATRIX.csv`](TASK_ACCEPTANCE_MATRIX.csv) records
   all three `status=validated` under `SL-V2-ORACLE-01`);
3. those runtimes scored only *declared* candidates — a reference variant or a
   seeded mutant — and could not be pointed at a worktree nobody declared in
   advance.

Only (3) was missing. This record supplies the definition; the transport is
harness work carried out under it.

---

## 2. The decision

For run purpose `AFCI_EFFICIENCY_PILOT`, and for that purpose alone:

> A run is **`FUNCTIONAL_VALID`** if and only if:
>
> 1. the correct task-specific **validated hidden runtime** executes
>    successfully against the **preserved candidate worktree**;
> 2. **every** hidden acceptance case classified as **SEMANTIC** for that task
>    passes;
> 3. **no** semantic case is missing, unexecuted, indeterminate or errored.

### 2.1 Non-semantic cases

Every hidden acceptance case classified **NON-SEMANTIC** — the restraint and
guard cases — is treated as follows, and the four clauses are separate
commitments:

| | |
|---|---|
| executed | **yes**, on every run |
| recorded | **yes**, in the run record, with its own pass / fail / error counts |
| reported | **separately**, never folded into the semantic tally |
| determines `FUNCTIONAL_VALID` | **no** |
| enters the paired-functional-valid eligibility gate | **no** |

### 2.2 Why the split is not new, and is not drawn here

It was drawn by the recorded oracle validation and is read from there. A
non-semantic case **issues no request**: it asserts something about the suite —
that ordering is not required, that echo is not required, that the assertion
surface is closed — and it passes for a candidate that cannot even be
constructed. A case that sends nothing cannot tell a working candidate from a
broken one, so counting it towards validity would let a candidate whose
application does not build look behaviourally live.

That is the same reasoning, and the same register, that `SL-V2-ORACLE-01` used
to exclude those cases from the mutant liveness bar. This record **reuses** it.
It reclassifies nothing, adds no case, removes no case, and touches no
assertion.

### 2.3 The counts, as already published

| task | semantic cases | non-semantic cases |
|---|---|---|
| `PT01` | 4 | 0 |
| `PT04` | 4 | 0 |
| `PT07` | 4 | 3 |

These are the counts [`TASK_ACCEPTANCE_MATRIX.csv`](TASK_ACCEPTANCE_MATRIX.csv)
already records. **The case identifiers are not published here.** They stay in
the private evaluator repository, exactly as `PT08`'s guard case identity does,
and no public artifact in this repository names one.

---

## 3. The derivation, stated as arithmetic

`FUNCTIONAL_VALID` is **derived**, never supplied. There is no parameter for it
anywhere on the path, and a block whose flag disagrees with its own counts is
**refused** rather than corrected:

```
functional_valid = TRUE  iff
      semantic_case_count_executed == semantic_case_count_expected
  AND semantic_pass_count          == semantic_case_count_expected
  AND semantic_fail_count          == 0
  AND semantic_error_count         == 0
  AND missing_semantic_case_ids    == []
  AND runtime_error                == null
  AND semantic_case_count_expected  > 0
```

No clause mentions a non-semantic count. A non-semantic failure is recorded,
reported and visible, and it does **not** flip the verdict.

The derivation happens **twice, independently**: once in the private scorer from
its own report, and once in
[`experiments/v2/harness/functional_evaluation.py`](../../experiments/v2/harness/functional_evaluation.py)
from the counts it is handed. A disagreement between the two records **neither**
verdict and reports `FUNCTIONAL_VALID_NOT_DERIVABLE`. It is derived a third time
when the run record is assembled, so a hand-edited block cannot be written.

---

## 4. Where the verdict may come from

Exactly one place:

```
record.functional_evaluation.functional_valid
```

The frozen analysis reads that field and nothing else. It is **never** inferred
from CI success, from model prose, from an exit status alone, from an
architecture score, or from the number of files changed. A run with no
functional evaluation block is `MISSING`, which is reported as its own status
and is **not** valid — "this run did not work" and "nobody scored this run" are
different facts, and a pair is eligible only when both runs are *known* to have
worked.

---

## 5. Architecture, and the report that implied one was owed

`AFCI_EFFICIENCY_PILOT` is **cost-only** under its own frozen governance: it
produces no architecture score, no violation value and no `E1` contribution.
Its run record nevertheless reported the absent architecture result as an
outstanding **`BLOCKED`** evaluation channel, which says an architecture result
is *owed*. It is not owed and never will be for this purpose.

The channel is therefore reported as **`NOT_PRODUCED`**, and the pilot report
carries this statement:

> **ARCHITECTURE:** Not produced by `AFCI_EFFICIENCY_PILOT` under its frozen
> cost-only governance. Existing pre-data legal/violating architecture
> validation was used only for eligibility. No live-run architecture treatment
> inference is made.

This is a **reporting-consistency correction, not a new endpoint**:

* no architecture scoring is added, enabled or performed;
* `E1` is not re-enabled and the confirmatory register is unchanged;
* the pre-data architecture validation `SL-V2-EFF-ELIG-01` relied on is
  unchanged and keeps its eligibility-only role;
* **no continuation threshold changes**, because none of §11's thresholds
  depends on architecture — §11.1, §11.2, §11.3 and §11.4 are byte-identical.

---

## 6. The evaluator boundary

| | |
|---|---|
| where acceptance logic lives | the private evaluator repository, and only there |
| what this repository gains | an invocation boundary and a derivation |
| when the scorer runs | **after** the model process has finished and the worktree has been captured |
| what it is given | the **preserved** post-run capture, copied again before use |
| what the candidate worktree gets | **nothing**; no hidden test is ever materialised into it |
| what crosses the boundary | counts, declared case identifiers, two digests, a verdict |
| what never crosses it | any assertion, any failure message, any suite text, any hidden path |
| evaluator console output | quarantined; its size and digest are recorded, its content is not read |
| exit status | fail-closed |

The structured result is swept for hidden-material path fragments before it is
recorded. A result naming one is **refused**, and the record is not written: a
boundary that only promises to withhold the suite is not a boundary.

---

## 7. Failure is recorded, never inferred

Every one of these is written into the run record as an explicit, coded
`runtime_error` with `executed: false` and `functional_valid: false`, and none
of them is silently omitted:

`FUNCTIONAL_EVALUATION_NO_WORKTREE`, `FUNCTIONAL_EVALUATOR_UNAVAILABLE`,
`FUNCTIONAL_EVALUATOR_TIMEOUT`, `FUNCTIONAL_EVALUATOR_NO_RESULT`,
`FUNCTIONAL_EVALUATOR_MALFORMED_RESULT`, `FUNCTIONAL_VALID_NOT_DERIVABLE`,
`CANDIDATE_WORKTREE_REFUSED`, `EVALUATOR_NO_REPORT`,
`EVALUATOR_SUITE_DID_NOT_RUN`, `EVALUATOR_CASE_REGISTER_INCONSISTENT`.

The candidate worktree is refused outright when it is not absolute, does not
exist, is not a directory, is the canonical public repository or the private
evaluator repository or lies inside either, is not this substrate, or carries
hidden-evaluator material.

---

## 8. The reset arm

`RESET_CHECKPOINT_NOT_REACHED` keeps the policy §8.1 already froze, unchanged:
no phase B is fabricated, no rerun is scheduled, no budget is raised and no
alternate checkpoint is substituted.

Such an observation still has a **finished process** and a **preserved final
state**, so it is scored against that state like any other. Its checkpoint
status is recorded independently in the `reset` block. The functional verdict
says nothing about the checkpoint in either direction, and the checkpoint
detector is handed no functional result — it could not read one if it were.

---

## 9. What this decision does NOT do

| | status after this record |
|---|---|
| any hidden acceptance assertion | **UNCHANGED** |
| the set of hidden acceptance cases | **UNCHANGED** — none added, none removed |
| case classification (semantic / non-semantic) | **UNCHANGED** — read, never redrawn |
| `PT01` / `PT04` / `PT07` public task bodies | **UNCHANGED**, byte-identical |
| the MAD | **UNCHANGED**, byte-identical |
| reset checkpoints and the 32/32/64 budgets | **UNCHANGED** |
| the permission allowlist | **UNCHANGED** |
| token, time and tool metric definitions | **UNCHANGED** |
| the 36-observation run schedule and its hash | **UNCHANGED** |
| `C1` / `C4` definitions | **UNCHANGED** |
| §11 continuation thresholds | **UNCHANGED** |
| model and runtime configuration | **UNCHANGED** |
| architecture scoring | **NOT ENABLED** |
| confirmatory `E1` | **NOT RE-ENABLED** |
| gate `G1` | **NOT PASSED** |
| gate `G2` | **NOT PASSED** |
| `TD-B32` (global) | **OPEN** |
| `TD-B34` | **OPEN** |
| `TD-B39` | **OPEN** |
| `TD-B42` | **OPEN** |
| `TD-B01` / `TD-B11` | **OPEN** |
| `TD-B12` / `G6` | **OPEN** |
| `TD-B03` | **OPEN**; `primary_model: null` |
| suite freeze | **false** |
| independent review | **NOT OBTAINED AND NOT CLAIMED** |

No result, violation value, success value, outcome value or treatment-effect
estimate exists, and none is created by this record.

---

## 10. Pre-data status

**Efficiency-pilot observations at the time of writing: ZERO.** The frozen
36-observation schedule has not started, and `experiments/v2/results/` and
`experiments/v2/analysis/` each hold their README and nothing else.

The frozen analysis is implemented at
[`experiments/v2/harness/efficiency_pilot_analysis.py`](../../experiments/v2/harness/efficiency_pilot_analysis.py),
beside `efficiency_run_plan.py`, rather than under `experiments/v2/analysis/`.
That directory's **emptiness is itself the pre-data evidence** — a dozen guards
read it as "no observation exists" — and a script placed there would have had to
weaken every one of them to say something this record can say in a sentence.
