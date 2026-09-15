# SL-V2-EFF-ELIG-01 — the pilot-scoped architecture-corpus eligibility rule

Status: **Study-Lead decision, PRE-DATA and NON-CONFIRMATORY.** It adjudicates
one narrow question about run *eligibility* for one run purpose, and it changes
nothing the [`AFCI_EFFICIENCY_PILOT_DECISION.md`](AFCI_EFFICIENCY_PILOT_DECISION.md)
froze.

**Zero efficiency observations exist at the moment it is written.** That is not
a courtesy sentence: it is the reason a rule about what the pilot may run can be
written at all without being a rule chosen to fit a result. A test asserts it
mechanically rather than this record asserting it in prose.

It passes no gate. `G1` is not passed, `G2` is not passed, and `TD-B01`,
`TD-B11`, `TD-B34`, `TD-B32`, `TD-B12`/`G6`, `TD-B03`, `TD-B39` and `TD-B42` all
remain **OPEN**. The suite is **not** frozen.

Authority: `SL-V2-EFF-ELIG-01`
Pilot authority: `SL-V2-EFF-01` ([`AFCI_EFFICIENCY_PILOT_DECISION.md`](AFCI_EFFICIENCY_PILOT_DECISION.md))

---

## 1. The question

`AFCI_EFFICIENCY_PILOT_DECISION.md` §12a records the pilot as **FROZEN but not
run-eligible**, and records two outstanding blockers. It also records, in the
same breath, that it would not answer the second of them:

> Whether a COST-ONLY purpose — which produces no architecture score, violation
> value or E1 contribution — needs the architecture-oracle validation corpus at
> all is a reasonable question, and it is **not answered here**. This record does
> not weaken a prerequisite so that its own pilot passes.

That was the right refusal at the time: a record must not relax the bar its own
work has to clear. The question is now adjudicated separately, on its merits,
still before any observation exists.

**The first blocker is not touched by this record.** The private pre-freeze
public-synchronisation propagation remains **mandatory in full** for every task
in the pilot. Nothing below weakens it, and it is discharged by propagation
rather than by adjudication.

---

## 2. What the architecture corpus is for, and what this pilot does with it

The per-task architecture corpus is a labelled set of mutated production
dependency shapes, each scored against the real public oracle and each required
to resolve to a declared status. It exists to establish that the **architecture
scorer** attributes correctly across the mutation space a task can reach:
anchor moves, anchor deletion, multiple forbidden edges collapsing to one
violated opportunity, test-only edges excluded from the production graph, scope
absence, and the sanctioned re-export chain that must not be synthesised into a
direct forbidden edge.

That is exactly what a **confirmatory architecture measurement** needs, because
in `E1` the corpus is what stands between a violation count and a
misattribution. `E1` is gated on `G1`/`TD-B34`, both open, and this record moves
neither.

The efficiency pilot's primary endpoint is `TOTAL_INPUT_TOKENS`, with
wall-clock, tool-call and exploration secondary endpoints. Architecture is
retained in the pilot as a **descriptive quality guardrail** — the reading of
"did the arm that was handed the architecture context make a mess of it?" — and
for nothing else. No architecture score, violation value, success value, outcome
value or treatment-effect estimate is produced, read or implied by any pilot
observation, and `AFCI_EFFICIENCY_PILOT_DECISION.md` §3.1 pins that firewall
mechanically.

A guardrail reading needs the scorer to be *sound on the thing it is reading*:
that a conforming implementation is not reported as a violation, and that the
intended forbidden shape is reported as one. It does not need the full
attribution-precision corpus, because no attribution precision figure is
produced and none may be.

---

## 3. The decision

For run purpose **`AFCI_EFFICIENCY_PILOT`**, a full per-task architecture
mutation/corpus package is **NOT a run-eligibility prerequisite** when **ALL**
of the following are already satisfied **before** any pilot data exists:

1. hidden functional acceptance is **validated**;
2. a **legal / reference implementation** passes hidden functional acceptance;
3. that legal implementation **creates the intended applicable architecture
   opportunity** and records **zero** target violations;
4. a **functionally correct target-violating reference** also passes hidden
   acceptance;
5. the **architecture scorer detects the exact intended target violation** on
   that violating reference;
6. functional acceptance **does not enforce architecture**;
7. architecture measurements in this pilot are **descriptive quality guardrails
   only**;
8. the pilot **does not enter** confirmatory `E1` analysis, treatment-effect
   analysis or power estimation.

All eight are **conjunctive**. A task that fails any one of them is blocked, and
is blocked rather than degraded: there is no partial exemption and no "mostly
validated" instrument.

Conditions 1, 7 and 8 are re-derived from the **public** authorities — the
acceptance matrix, the purpose's own non-result-bearing registration, and the
run-purpose firewall table. Conditions 2 to 6 are facts about executed private
validation, read read-only out of the private package record by the public
readiness check, which never imports private code and never writes into the
private repository.

### 3.1 The eligibility rule table

The runner re-derives this table from this record rather than trusting a
constant, so a drift between the code and the adjudication is a mechanical
failure rather than a reading.

| field | value |
|---|---|
| `decision_id` | `SL-V2-EFF-ELIG-01` |
| `run_purpose` | `AFCI_EFFICIENCY_PILOT` |
| `architecture_corpus_required_for_run_eligibility` | `false` |
| `pilot_scoped_conditions_required` | `8` |
| `architecture_measurement_role` | `descriptive quality guardrail` |
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

---

## 4. How it is enforced, and how it fails

The readiness report gains one prerequisite and changes the reported status of
another. Nothing else about eligibility moves.

| item | before | after, for this purpose only |
|---|---|---|
| `architecture_corpus_availability` | `PASS` when the named corpus module is present, `BLOCKED` otherwise | unchanged when present; `N/A` when absent **and** the eight conditions hold; `BLOCKED` otherwise |
| `pilot_architecture_validation` | did not exist | `PASS` when the eight conditions hold, `BLOCKED` otherwise |

`N/A` and never `PASS`. `PASS` would read as *the corpus exists*, and it does
not. The status says what is true: the corpus requirement **does not apply to
this purpose**, and the underlying corpus work is **not done, not waived and not
reduced in scope** for any purpose it does apply to. This is the same
distinction the repository already draws for the canonical result-manifest
firewall gap under `SL-PT08-02`.

Every one of these blocks, and each is a refusal rather than a degradation:

* no private package record, or one that cannot be read;
* no architecture-validation block in it;
* a validation block not bound to the exact approved public task hash;
* a missing or failing hidden functional runtime;
* a missing legal-reference validation;
* a missing target-violating-reference validation;
* a legal reference whose target opportunity is not applicable, or that records
  a non-zero target violation;
* a violating reference the scorer does **not** report as a violation;
* a violating reference whose detected rule or detected source → target edge is
  not the declared target one;
* a target rule that is not a registered rule of the public architecture rule
  catalog, or that is the umbrella family rule, which may never back a scored
  opportunity;
* a record claiming the functional oracle enforces architecture;
* a purpose that is confirmatory, result-bearing, or whose firewall does not pin
  the three analysis-entry flags false.

**For every other run purpose the corpus requirement is unchanged.** The
exemption is carried on the authorising purpose itself, and a purpose that does
not name it is governed by the pre-existing rule in full, including every future
confirmatory or result-bearing purpose. A purpose that has no exemption cannot
acquire one by being run.

---

## 5. What this decision does NOT do

| | status after this record |
|---|---|
| the corpus requirement, globally | **UNCHANGED and REQUIRED** |
| the corpus requirement for confirmatory / `E1` use | **UNCHANGED and REQUIRED** |
| the private pre-freeze public-sync propagation | **UNCHANGED and REQUIRED** |
| gate `G1` | **NOT PASSED** |
| gate `G2` | **NOT PASSED** |
| `TD-B32` (global) | **OPEN** |
| `TD-B34` | **OPEN** |
| `TD-B39` | **OPEN** |
| `TD-B01` / `TD-B11` | **OPEN** |
| `TD-B12` / `G6` | **OPEN** |
| `TD-B03` (primary model) | **OPEN**; `primary_model: null` |
| `TD-B42` (the permission finding) | **OPEN** |
| suite freeze | **false** |
| `E1` register | **UNCHANGED** |
| `E1` admission of any candidate | **UNCHANGED**; nothing is admitted |
| any task manifest | **NOT FROZEN** |
| the pilot's tasks | **NOT confirmatory** |
| the pilot's frozen metrics, thresholds, schedule, budgets, checkpoints, permission rules, model and runtime | **UNCHANGED** |
| independent review | **NOT OBTAINED AND NOT CLAIMED** |

It creates **no precedent** for a confirmatory purpose, for a later pilot, or
for any other prerequisite. It is bounded to `AFCI_EFFICIENCY_PILOT` and expires
with it.

No result, violation value, success value, outcome value or treatment-effect
estimate exists, and none is created by this record.

---

## 6. Why this is not the relaxation it could have been

Three properties are what separate this from weakening a bar to get past it.

**It was decided against a stated construct, not against a blocker.** The
question §1 quotes was recorded as open *by the record that hit the blocker*,
and deliberately left unanswered there. The answer turns on what the measurement
is — cost — and on the firewall that already makes the architecture channel
descriptive for this purpose. It would read the same way if the pilot's tasks
already had corpora.

**It is pre-data.** No pilot observation exists. Nothing about how a run went
could have informed which conditions were chosen, because no run has gone.

**It replaces a coarse check with a stricter one, not with nothing.** Before
this record, `architecture_corpus_availability` asked one question: is a module
with the expected name on disk? It never read it, never ran it, and would have
passed a corpus that validated nothing. The eight conditions instead require
*executed* evidence that both channels work and stay separate — including the
anti-circularity control that a functionally correct violating implementation
passes functional acceptance in full, which a file-presence check does not test
at all.

What remains genuinely weaker is the mutation space: the exemption does not
require the anchor-move, anchor-deletion, multiple-edge, test-only-exclusion and
scope-absence cases. That is a real reduction, it is recorded here as one, and
it is exactly the reduction that would be unacceptable for a confirmatory
attribution figure and is acceptable for a descriptive guardrail attached to a
token count. It is **not** carried anywhere beyond this pilot.
