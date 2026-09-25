# SL-V2-BACKSTAGE-TQ-02 — Backstage task qualification V2, pre-registered

Status when written: **PRE-DATA freeze. PRE-TREATMENT INSTRUMENT QUALIFICATION.
C1 ONLY. EXPLORATORY. 15 intended observations, 0 attempted, 0 completed.**

> **HALTED 2026-09-25 after 1 of 15 observations** — Study-Lead decision
> [`SL-V2-BACKSTAGE-TQ-02-H1`](AFCI_BACKSTAGE_TASK_QUALIFICATION_V2_HALT_DECISION.md).
> The runtime pin launched the frozen binary by an extensionless path, which broke
> Claude Code's built-in Grep tool in the one delivered observation; the executor
> was stopped before a second task was delivered, and the Study Lead stopped the
> phase. No candidate status is determined and no task newly qualified. Results:
> [`study-results/10_backstage_task_qualification_v2/`](../../study-results/10_backstage_task_qualification_v2/README.md).
> **Everything below is the pre-data record and is unchanged.**

This phase is **not** an AFCI treatment-effect study and produces **no** AFCI
treatment evidence. It runs the baseline condition **C1 only**. **No C4
observation is permitted**: no architecture packet is composed, delivered or
simulated, nothing is compared against a hypothetical C4, and no treatment
effect is estimated or predicted.

| Field | Value |
| --- | --- |
| Phase id | `AFCI_BACKSTAGE_TASK_QUALIFICATION_V2` |
| Authority | `SL-V2-BACKSTAGE-TQ-02` |
| Execution controls reused unchanged | `SL-V2-BACKSTAGE-PILOT-03` |
| Condition | C1 only |
| Model / effort / runtime | `claude-sonnet-5` / `high` / Claude Code `2.1.229` (pinned by absolute path) |
| Reset state / turn ceiling | `NON_RESET` / 96 |
| Observations | 3 per candidate × 5 candidates = **15 intended** |
| Frozen substrate / export tree | `f285f6e46ba57d30c5be8448fd018b960d7d4748` / `4dfadc101db1c9f29b82934db25def67a93a2563` |
| Seed | `AFCI_BACKSTAGE_TASK_QUALIFICATION_V2_20260925` |
| Execution plan SHA-256 | `2c34bcb8e326a9687b563f0583de5460bb0ce5d6288b9b1f2476422c585bcc55` |
| Scientific schedule SHA-256 | `deed9a041fba330d6da261046a0ac95e8bcdd6a7d0af7c0665584d13d441903f` |
| Scientific projection SHA-256 | `c316325b9964e7d4a4057625c01ab0d2d52a89cdf478574f1bad9be6a4804790` |

---

## 1. Why a second qualification batch

Task Qualification V1 (`SL-V2-BACKSTAGE-TQ-01`) is COMPLETE with **INSUFFICIENT
QUALIFIED TASKS**: 15/15 valid final observations, and exactly one candidate,
**`BTQ-T5`**, qualified. `BTQ-T1R`, `BTQ-C02`, `BTQ-C04` and `BTQ-C05` were
`ARCHITECTURE_FLOOR_REJECT` — functionally valid in 3 of 3 observations, with
0 of 3 target architecture violations. A later C1-vs-C4 study needs three
qualified tasks. `BTQ-T5` holds one slot; this phase looks for **at least two
more** in a new batch of five **new** candidates, under a new pre-data freeze
(V1's own rule forbade further mining inside V1).

**The lesson this batch applies.** V1's four floors shared one property: from
the frozen substrate, a single obvious nearby precedent revealed the documented
owner, and the model followed it. The one candidate that qualified had no such
precedent near the code being changed. Being architecture-*sensitive* is
therefore not enough. This batch was mined for **genuine ambiguity**: changes
where, from the substrate, the nearest code or a competing precedent points
*away* from the documented owner, and the violating placement is functionally
equivalent and invisible to the visible gate.

## 2. Prior phases are immutable; `BTQ-T5` is reserved

* **Attempt 1** remains HALTED / EXCLUDED (`SL-V2-BACKSTAGE-PILOT-02`).
* **Attempt 2** remains COMPLETE with NO ARCHITECTURE SIGNAL
  (`SL-V2-BACKSTAGE-PILOT-03`).
* **Task Qualification V1** remains COMPLETE with INSUFFICIENT QUALIFIED TASKS
  (`SL-V2-BACKSTAGE-TQ-01`).
* None of these classifications is altered. Nothing is re-run, rescored, pooled
  or redefined. The run artifacts of Attempt 2 and of V1 were digested before
  this phase and are re-verified after its last observation.
* **`BTQ-T5` is carried forward as QUALIFIED, untouched.** It is not re-run,
  re-scored or re-posed here; its statement bytes are checked unchanged before
  the first observation.
* No V2 candidate is, or re-words, any task used before (T1, T2, T5, `BTQ-T1R`,
  `BTQ-C02`, `BTQ-C04`, `BTQ-C05`), and V1's two static rejects are not revived.
  The schedule generator refuses any candidate whose statement carries a prior
  task's bytes.

## 3. The five candidates

| Slot | Task id | Origin | Architecture rule family | Statement SHA-256 |
| --- | --- | --- | --- | --- |
| Q6 | `BTQ2-C01` | newly mined real Backstage change (reduced scope) | family E: extension contract placement / ownership | `3b91a6ae7be948a2ab26bd2035abd18e1c0853981c888f1928ed0f05aff7cdf0` |
| Q7 | `BTQ2-C02` | newly mined real Backstage change | family P: package / role ownership | `79252b843f675948a98b5f41a5d06b9775a4ffa5abd3dfe7fde8259ee6968aa0` |
| Q8 | `BTQ2-C03` | newly mined real Backstage change | family P: package / role ownership | `76d8c7b81df8093dbaf0dba4806c4408287a772f69fb599ba90bae1757f01456` |
| Q9 | `BTQ2-C04` | newly mined real Backstage change | family S: shared / public contract ownership | `702b65623b098e868fc4412151687407b424f4a1f76d54e3c0668665dbbc7db0` |
| Q10 | `BTQ2-C05` | newly mined real Backstage change | family S: shared / public contract ownership | `4f94ddc656b93e1b8a8a1a1211727f86b86ee3f9b4fc726ccf665f2daf50b2b2` |

`BTQ-T5` belongs to **family S**. The family letters stand for the private
scorer's rule families, so the selection rule in §8 can be audited from this
record alone.

The mined changes were merged into Backstage **after** the frozen substrate and
are re-posed at it, as V1's were. One is re-posed at reduced scope — smaller,
not different: the placement decision it asks for is the historical one. The
historical identifiers, the verbatim statements, the hidden legal and violating
placements, the scorer mappings, the oracles and the controlled references are
retained in the private evaluator, because each of them points at a hidden
answer; every statement is identified here by its SHA-256.

### 3.1 How the candidates were found

Seven systematic passes were made over the first-parent history between the
substrate and the current upstream head (2,388 merges): a pickaxe over every
contract-constructing call; changes that gave a shared library new public API
while a sibling package of the same plugin changed; every public export added
after the substrate to a shared library; symbols moved between packages;
placements that differ between the upstream head and the substrate; a keyword
sweep of every merge subject; and precedent maps of the substrate itself. Two
whole rule families were set aside, not as candidates but as families, because
the repository's own tooling or documentation leaves no invisible, unique legal
home in them. More than thirty leads were examined and rejected, each with a
recorded reason (already used, not re-posable at the substrate, no unique legal
home, an obvious nearby precedent, or too large to re-pose faithfully). One lead
with the strongest pressure evidence — the upstream maintainers' own placement
contradicts the documented rule — was rejected statically because no faithful,
testable slice of it could be re-posed.

## 4. Static qualification — every candidate, before any model run

Each candidate has one pre-specified architecture opportunity, a hidden legal
target, a hidden violating target, a placement-agnostic functional oracle, an
architecture scorer, the frozen visible gate, and a legal and a violating
controlled reference. Required for all five:

| Tree | Functional | Applicable | Violated | Target violation |
| --- | --- | --- | --- | --- |
| untouched substrate | semantic cases fail (the task is not already done) | 0 | 0 | no |
| legal reference | PASS | 1 | 0 | no |
| violating reference | PASS | 1 | 1 | yes |

**All five candidates meet every requirement, and none was replaced.**

* **Reference matrix.** For each candidate the untouched substrate fails every
  semantic case and passes every restraint case at 0 / 0; the legal reference
  passes the oracle at 1 / 0; the violating reference passes the same oracle at
  1 / 1 with a target architecture violation. Architecture was scored both on the
  changed files and on the full workspace, and the two modes agree for every tree.
* **Visible gate.** Both references of every candidate pass the model-visible gate
  (type-check, lint, formatting, differential tests, differential API reports),
  so the architecture distinction is not reachable through visible CI.
* **Task / oracle alignment** (new in V2). Every hidden oracle case is traced to
  verbatim statement wording that asks for it. The statement says what is
  required, never where it must live.
* **Answer leakage.** All five statements pass the architecture-answer leakage
  audit.
* **Real preparation.** All five warm-up sets are proved through the real
  preparation path. Two candidates first failed it under the frozen warm-up alone,
  for the reason given in §7, and prepare under the pre-registered warm-up report
  restore, which restored exactly one API report each and nothing else. The other
  three prepared without it. For two candidates the warm-up's own test step reports
  pre-existing substrate test failures, exactly as the same warm-up sets did in V1;
  preparation does not gate on them, and the visible gate's tests are differential.

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
estimates AFCI behaviour on ARCHITECTURE-PRESSURE-QUALIFIED BACKSTAGE TASKS. It
must NOT be presented as an unbiased estimate over arbitrary Backstage software
changes.** This limitation will appear in every later report that uses the
selection, including the professor package.

## 7. Execution

* One deterministic C1-only schedule over the 15 cells (seed above; sort by
  SHA-256 of a seeded string, no language RNG). New run ids, roots and sessions,
  with zero overlap with Attempts 1 and 2 and with V1.
* **All 15 observations run, in the frozen order, whatever interim statuses
  look like.** There is no early stop.
* **Runtime.** The launcher never resolves the CLI from `PATH` (the host's
  default CLI is a newer release). It runs the frozen `2.1.229` binary by
  absolute path, checks its reported version before anything is written or any
  network call is made, and refuses unless the answer is exactly `2.1.229`; it
  re-checks the binary's digest immediately before task delivery. A refusal
  consumes nothing.
* **Network preflight** before every observation (VPN adapter down, name
  resolution and endpoint reachability, three consecutive passes). A failure
  before task delivery consumes nothing and is retried on the same identity.
* **Power.** Before the schedule, the host's sleep, hibernate and lid-close
  settings are recorded and set so the machine cannot sleep; before every launch
  the executor checks AC power and those settings and stops, consuming nothing,
  if either fails. The recorded settings are restored afterwards. This is an
  infrastructure control only.
* **Infrastructure retries.** `execution_attempt` 1 and 2 are pre-authorised for
  every cell. Attempt 2 is used only after an objectively infrastructure-invalid
  attempt 1: either under the frozen Attempt-2 classification, or — **pre-
  authorised here, before data** — a proved pre-delivery preparation failure,
  where the attempt's own artifacts show that the runtime and network checks
  passed and the prompt was composed, that no model process was started, and
  that workspace preparation failed. This covers the failure V1 recorded as
  deviation `SL-V2-BACKSTAGE-TQ-01-D1` without any mid-study amendment, and it
  was tested synthetically before observation 1. Attempt 2 is never used for a
  functional failure, an architecture outcome, MAX_TURNS, cost, tokens,
  permission denials, a model strategy or a test failure. There is no attempt 3.
* **Warm-up report restore — pre-authorised here, before data.** At the frozen
  substrate, some packages' committed API reports do not regenerate identically
  from the untouched source, and the frozen workspace warm-up rewrites them, so
  the frozen preparation refuses the workspace. This is the condition that
  rejected one V1 candidate, and it failed two V2 candidates in their first real
  preparation checks although both passed every other static check. Rather than
  lose them, the Study Lead decided before any data: after the frozen warm-up,
  and before the frozen check that no tracked file changed, every package-level
  API report the warm-up rewrote in place is restored byte-for-byte from the
  substrate commit. Nothing else is restored: any other change still makes
  preparation refuse. The model therefore starts from the exact frozen substrate
  tree, the warm-up set and commands are unchanged, and the rule never decides
  which packages are warmed. It applies identically to all five V2 candidates and
  to no other phase; V1 is untouched.
* The frozen Attempt-2 permission policy applies unchanged, identical to V1's,
  and is never widened; permission denials are recorded descriptively.
* Hidden scoring is post hoc, in a separate process, against the preserved
  workspace. Task, oracle, scorer, schedule and retry-rule bytes are pinned
  before observation 1 and cannot change after it; no candidate may be replaced
  after the schedule is committed.

## 8. Future-study selection — deterministic, pre-data

`BTQ-T5` holds one slot; this phase needs at least two newly QUALIFIED
candidates.

1. fewer than two newly QUALIFIED → **INSUFFICIENT ADDITIONAL QUALIFIED
   TASKS**: report and stop, with no further mining in this phase;
2. exactly two → the future set is `BTQ-T5` plus both;
3. more than two → exactly two, chosen by (a) the largest number of distinct
   rule families among `BTQ-T5` (family S) and the two chosen, then (b) the lower
   slots (Q6 < Q7 < Q8 < Q9 < Q10).

Never by violation counts or functional score beyond the thresholds, token cost,
speed, C1 difficulty, model failures, expected AFCI benefit or qualitative
attractiveness. This decision does not create or run the future C1/C4 study.

## 9. What this decision does NOT do

It estimates no treatment effect, runs no C4, selects no primary model, confers
no confirmatory eligibility, re-runs, rescores or reinterprets nothing from
Attempts 1 and 2 or from V1, and pools nothing with them. At the moment it is
committed, the phase has **15 intended observations and 0 executed.**
