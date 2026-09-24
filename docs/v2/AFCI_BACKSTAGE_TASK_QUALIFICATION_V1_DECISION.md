# SL-V2-BACKSTAGE-TQ-01 — Backstage task qualification V1, pre-registered

Status when written: **PRE-DATA freeze. PRE-TREATMENT INSTRUMENT QUALIFICATION.
EXPLORATORY. 15 intended observations, 0 attempted, 0 completed.**

This phase is **not** an AFCI treatment-effect study and produces **no** AFCI
treatment evidence. It runs the baseline condition **C1 only**. **No C4
observation is permitted**: no architecture packet is composed, delivered or
simulated, nothing is compared against a hypothetical C4, and no treatment
effect is estimated.

| Field | Value |
| --- | --- |
| Phase id | `AFCI_BACKSTAGE_TASK_QUALIFICATION_V1` |
| Authority | `SL-V2-BACKSTAGE-TQ-01` |
| Execution controls reused unchanged | `SL-V2-BACKSTAGE-PILOT-03` |
| Condition | C1 only |
| Model / effort / runtime | `claude-sonnet-5` / `high` / Claude Code `2.1.229` |
| Reset state / turn ceiling | `NON_RESET` / 96 |
| Observations | 3 per candidate × 5 candidates = **15 intended** |
| Frozen substrate / export tree | `f285f6e46ba57d30c5be8448fd018b960d7d4748` / `4dfadc101db1c9f29b82934db25def67a93a2563` |
| Seed | `AFCI_BACKSTAGE_TASK_QUALIFICATION_V1_20260923` |
| Execution plan SHA-256 | `6b913631e1c35a6115fdb81bc7000f8b9e609dc0894b6c79036113e3c59dbee8` |
| Scientific schedule SHA-256 | `26c92596ef170c8baefe184b3c527e797f01021372533cd59bb62ce9298c1de0` |
| Scientific projection SHA-256 | `cb8e0d7f60d4ac6cef5c1faaa8bde5a9a7981c1855c57d448941c3b892b8d03c` |

---

## 1. Why a qualification phase

Backstage Attempt 2 (`SL-V2-BACKSTAGE-PILOT-03`) completed 18/18 valid
observations and its frozen continuation rule returned **NO ARCHITECTURE
SIGNAL**. That result stands unchanged. It also showed that the *instrument*
limited what the study could see:

* **T1 was functionally underspecified.** All six T1 runs failed the same single
  semantic case while both frozen controlled references pass it, so T1 was inert
  on both endpoints.
* **T2 sat at an architecture floor.** C1 0/3 and C4 0/3 target violations:
  there was no baseline violation for a treatment to reduce.
* **T5 discriminated.** Two of three C1 runs made the wrong placement decision —
  measurable baseline architecture pressure.

A later C1-vs-C4 study is informative only on tasks that are functionally
attainable as stated, admit both a legal and a violating functionally correct
implementation, are not policed by the visible gate, and exhibit architecture
pressure at baseline. This phase establishes the first three statically and
measures the fourth with C1 only.

## 2. The prior Backstage attempts are immutable

* **Attempt 1** remains HALTED / EXCLUDED (`SL-V2-BACKSTAGE-PILOT-02`).
* **Attempt 2** remains COMPLETE with its frozen result. It is not rescored, no
  row is excluded post hoc, and its continuation decision is not reinterpreted.
  Its run artifacts were digested before this phase and are re-verified before
  the first and after the last qualification observation.
* Attempt-2 outcomes **motivate** this phase and are **never pooled** with it; no
  Attempt-2 run counts as a qualification repetition.

## 3. The five candidates

| Slot | Task id | Origin | Architecture rule family | Statement SHA-256 |
| --- | --- | --- | --- | --- |
| Q1 | `BTQ-T1R` | T1 repaired — a **new identity**; the original T1 bytes are untouched | extension-point placement / ownership | `6600ef341a2588f26d250348591b22a52cd34ed90f49d098319e99693ba02aa5` |
| Q2 | `BTQ-T5` | original T5, **byte for byte** | shared contract / permission ownership | `8db333264895b3d6df869adf27cc419c9adbd696da065cead8bbae610d62ba3d` |
| Q3 | `BTQ-C02` | newly mined real Backstage change | shared contract / permission ownership | `a84a926b6e2c24a08a2c29888ccd63a3a4d6df1fc93d18c0ea5c3d7038902cc9` |
| Q4 | `BTQ-C04` | newly mined real Backstage change | package / role ownership | `ed65b5e932924c5e8c977987044e726431efc66aec4ea4d13b857776e63c2bf9` |
| Q5 | `BTQ-C05` | newly mined real Backstage change (re-posed at reduced scope) | shared contract / API ownership | `7197af4dee32739c157dcc9bfd897b6ae6433df64bb595c87329ee71bb87635a` |

The mined changes were merged into Backstage **after** the frozen substrate and
are re-posed at it, exactly as T2 and T5 were in the pilot. Their historical
identifiers, the verbatim statements, the hidden legal and violating placements,
the scorer mappings and the controlled references are retained in the private
evaluator, because each of them points at a hidden answer; every statement is
identified here by its SHA-256.

**T2 is RETIRED** from this phase because Attempt 2 demonstrated an architecture
floor. It is not silently substituted.

### 3.1 The T1 repair

The original T1 statement is historically immutable and remains the statement
Attempt 2 ran. The repair creates a new task identity, `BTQ-T1R`, and changes
one thing: the statement described a callback that returns a value, without
saying the value must be returned **synchronously**. The hidden oracle uses it
synchronously; both frozen controlled references return it synchronously; all
six Attempt-2 T1 runs returned it asynchronously, following a neighbouring
convention in the code they were editing. One sentence now states the
synchronous return. **No architecture guidance was added**: the change names no
package, role, plugin, library, location or rule, and the automated leakage audit
confirms it. The oracle, scorer mapping and references are T1's, unchanged.

### 3.2 How the three new candidates were found

Every post-substrate Backstage change that adds a backend extension point or a
permission was enumerated, and the search was then broadened to service
references, utility APIs and frontend blueprints. Five formal candidates were
examined in mining order. **Three passed static qualification. Two were rejected
before any model observation:** one because it cannot be prepared under the
frozen execution infrastructure (a pre-existing substrate condition makes the
frozen workspace warm-up modify a tracked file for any placement-neutral warm-up
set), and one because its documented ownership rule admits two legal homes, so
no unique legal target could be fixed without tuning the scorer to the task.
Replacement was permitted only before the schedule froze; it is now forbidden.

## 4. Static qualification — every candidate, before any model run

Each candidate has one pre-specified architecture opportunity, a hidden legal
target, a hidden violating target, a placement-agnostic functional oracle, an
architecture scorer, the frozen visible gate, a legal and a violating controlled
reference. Required and met for all five:

| Tree | Functional | Applicable | Violated | Target violation |
| --- | --- | --- | --- | --- |
| untouched substrate | semantic cases fail (the task is not already done) | 0 | 0 | no |
| legal reference | PASS | 1 | 0 | no |
| violating reference | PASS | 1 | 1 | yes |

Architecture was scored both on the changed files and on the full workspace (the
mode a real single-commit run workspace uses); both agree for every tree. **Both
references of every candidate pass the model-visible gate** (type-check, lint,
formatting, differential tests, differential API reports), so the architecture
distinction is not reachable through visible CI. The five statements pass the
architecture-answer leakage audit, and the new candidates' workspace warm-up sets
were proved through the real preparation path.

## 5. The C1-only qualification rule — frozen before data

Per candidate, exactly **3 independent C1 observations** — fresh process, fresh
session, fresh workspace, no resume, no continue, no architecture packet.

**A candidate QUALIFIES for a future AFCI study only if both hold:**

1. `FUNCTIONAL_VALID` in **at least 2 of 3** observations; and
2. `TARGET_ARCHITECTURE_VIOLATION` in **at least 1 of 3** observations.

| Outcome | Status |
| --- | --- |
| functional below 2/3, violations at least 1/3 | `FUNCTIONAL_REJECT` |
| functional at least 2/3, violations 0/3 | `ARCHITECTURE_FLOOR_REJECT` |
| functional below 2/3, violations 0/3 | `BOTH_REJECT` |
| both satisfied | `QUALIFIED` |

A MAX_TURNS observation is a scientific outcome: it counts and is never retried.
These thresholds do not change after data.

## 6. What the selection rule means

**This qualification intentionally selects tasks with measurable baseline
architecture pressure. A future treatment study built on its selection therefore
estimates AFCI behaviour on ARCHITECTURE-PRESSURE-QUALIFIED TASKS. It must NOT
be presented as an unbiased estimate over arbitrary Backstage development
tasks.** This limitation will appear in every later report that uses the
selection.

## 7. Execution

* One deterministic C1-only schedule over the 15 cells (seed above; sort by
  SHA-256 of a seeded string, no language RNG). Only C1 exists, so no arm
  balancing applies. New run ids, roots and sessions, with zero overlap with
  either prior attempt.
* **All 15 observations run, in the frozen order, whatever interim statuses
  look like**, so that no candidate's status depends on execution order.
* The frozen network preflight runs before every observation; a failure before
  task delivery consumes nothing.
* `execution_attempt` 1 and 2 are pre-authorised for every cell. Attempt 2 is
  used only after an objectively infrastructure-invalid attempt 1, under the
  frozen Attempt-2 classification — never for a functional failure, an
  architecture outcome, MAX_TURNS, cost, tokens, permission denials or model
  strategy. There is no attempt 3.
* The frozen Attempt-2 permission policy applies unchanged and is never widened
  in response to a qualification denial; permission denials are recorded
  descriptively.
* Hidden scoring is post hoc, in a separate process, against the preserved
  workspace. Task, oracle and scorer bytes are pinned before observation 1 and
  cannot change after it.

## 8. Future-study selection — deterministic, pre-data

1. every QUALIFIED candidate is eligible;
2. exactly three QUALIFIED → those three;
3. more than three → three chosen by (a) broader architecture-rule-family
   coverage, then (b) slot order Q1 < Q2 < Q3 < Q4 < Q5;
4. fewer than three → **INSUFFICIENT QUALIFIED TASKS**: stop after reporting; no
   further mining in this phase (a second batch would need a new pre-data freeze).

Never by violation magnitude beyond the threshold, token cost, C1 difficulty,
model failures or expected AFCI benefit. This decision does not create or run
the future C1/C4 study.

## 9. What this decision does NOT do

It estimates no treatment effect, runs no C4, selects no primary model, confers
no confirmatory eligibility, rescores nothing from Attempts 1 or 2, and pools
nothing with them. At the moment it is committed, the phase has **15 intended
observations and 0 executed.**
