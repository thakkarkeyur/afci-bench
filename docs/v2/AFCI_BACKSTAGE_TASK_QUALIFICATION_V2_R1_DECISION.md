# SL-V2-BACKSTAGE-TQ-02-R1 — Backstage task qualification V2-R1, pre-registered

Status when written: **PRE-DATA freeze. PRE-TREATMENT INSTRUMENT QUALIFICATION.
C1 ONLY. EXPLORATORY. 15 intended observations, 0 attempted, 0 completed.**

This phase is a **clean re-execution** of Backstage Task Qualification V2 after a
runtime-launch defect. It is **not** an AFCI treatment-effect study and produces
**no** AFCI treatment evidence. It runs the baseline condition **C1 only**. **No C4
observation is permitted**: no architecture packet is composed, delivered or
simulated, nothing is compared against a hypothetical C4, and no treatment effect
is estimated or predicted.

| Field | Value |
| --- | --- |
| Phase id | `AFCI_BACKSTAGE_TASK_QUALIFICATION_V2_R1` |
| Authority | `SL-V2-BACKSTAGE-TQ-02-R1` |
| Re-executes | `SL-V2-BACKSTAGE-TQ-02` (V2), halted by `SL-V2-BACKSTAGE-TQ-02-H1` |
| Execution controls reused unchanged | `SL-V2-BACKSTAGE-PILOT-03` |
| Condition | C1 only |
| Model / effort / runtime | `claude-sonnet-5` / `high` / Claude Code `2.1.229` (a byte-identical copy of the frozen binary carrying the `.exe` extension) |
| Runtime executable SHA-256 | `5736c66be98a372d5e5e3b3598ead89ab5a9d1aca60d347fe7b561801c58376c` |
| Reset state / turn ceiling | `NON_RESET` / 96 |
| Observations | 3 per candidate × 5 candidates = **15 intended** |
| Frozen substrate / export tree | `f285f6e46ba57d30c5be8448fd018b960d7d4748` / `4dfadc101db1c9f29b82934db25def67a93a2563` |
| Seed | `AFCI_BACKSTAGE_TASK_QUALIFICATION_V2_R1_20260925` |
| Execution plan SHA-256 | `090d87892e9b2f20680cc82da32eb3df1f490774a04bc5696e68a5ca09be817d` |
| Scientific schedule SHA-256 | `2038a94de6524a4276b551d5cadf9ce4ec02e25e72e859bc58fa8baefe634080` |
| Scientific projection SHA-256 | `1cd6b71a51f83e816f46cc0d2eba0173747a2c603f5a82412e13e05264204f7e` |

---

## 1. Why this phase exists

Task Qualification V2 (`SL-V2-BACKSTAGE-TQ-02`) was **halted after 1 of 15
observations** ([`SL-V2-BACKSTAGE-TQ-02-H1`](AFCI_BACKSTAGE_TASK_QUALIFICATION_V2_HALT_DECISION.md)).
Its runtime pin launched the frozen Claude Code `2.1.229` binary through a path
without an executable extension. The version and digest checks passed, but Claude
Code's built-in Grep tool — and the built-in file-glob tool, which uses the same
bundled search — re-launches its own executable, and Windows cannot resolve an
executable without an extension, so the tool could not start.

V2's first observation ran under that defect and is **not qualification
evidence**; its second identity received no task; the remaining thirteen never
started. **V2 is excluded wholesale** because of a scientific-runtime
instrumentation defect. This phase does not rescore V2, reinterpret or reuse its
one observation, pool V2 with this phase, or modify any V2 record. Every V2
candidate status remains **NOT DETERMINED** in V2's own record, and V2's provider
cost — **$1.3543**, all of it under the defect — is reported, not hidden.

This phase re-executes the **same five statically qualified V2 candidates from
scratch**, under a corrected and pre-validated `2.1.229` launch, with new run ids,
new sessions, new workspaces, new destinations and a new execution-plan identity.

**Why the same candidates are legitimate.** All five candidate definitions and
their static qualification were frozen and passed V2's readiness gate before V2's
only observation. The defect lies in execution infrastructure — which file the
launcher started — and is independent of task, placement and model outcome. No
model output informed the candidates, their statements, oracles, scorers,
references or rules, and nothing is re-mined, replaced or re-worded.

## 2. Prior phases are immutable

* **Attempt 1** remains HALTED / EXCLUDED (`SL-V2-BACKSTAGE-PILOT-02`).
* **Attempt 2** remains COMPLETE with NO ARCHITECTURE SIGNAL (`SL-V2-BACKSTAGE-PILOT-03`).
* **Task Qualification V1** remains COMPLETE with INSUFFICIENT QUALIFIED TASKS
  (`SL-V2-BACKSTAGE-TQ-01`); its one qualified task, **`BTQ-T5`**, is carried forward
  untouched and holds one future slot.
* **Task Qualification V2** remains HALTED after 1 of 15, with no candidate status
  determined (`SL-V2-BACKSTAGE-TQ-02-H1`).

None of these is re-run, rescored, pooled or redefined. The run artifacts of
Attempt 2, V1 and the halted V2 — every file of V2's two spent identities, its
preserved workspaces, its record and its logs — were digested before this phase and
are re-verified before its first observation and after its last.

## 3. The five candidates — V2's, unchanged

| Slot | Task id | Origin | Architecture rule family | Statement SHA-256 |
| --- | --- | --- | --- | --- |
| Q6 | `BTQ2-C01` | newly mined real Backstage change (reduced scope) | family E: extension contract placement / ownership | `3b91a6ae7be948a2ab26bd2035abd18e1c0853981c888f1928ed0f05aff7cdf0` |
| Q7 | `BTQ2-C02` | newly mined real Backstage change | family P: package / role ownership | `79252b843f675948a98b5f41a5d06b9775a4ffa5abd3dfe7fde8259ee6968aa0` |
| Q8 | `BTQ2-C03` | newly mined real Backstage change | family P: package / role ownership | `76d8c7b81df8093dbaf0dba4806c4408287a772f69fb599ba90bae1757f01456` |
| Q9 | `BTQ2-C04` | newly mined real Backstage change | family S: shared / public contract ownership | `702b65623b098e868fc4412151687407b424f4a1f76d54e3c0668665dbbc7db0` |
| Q10 | `BTQ2-C05` | newly mined real Backstage change | family S: shared / public contract ownership | `4f94ddc656b93e1b8a8a1a1211727f86b86ee3f9b4fc726ccf665f2daf50b2b2` |

`BTQ-T5` belongs to **family S**. These are the statement digests V2 froze; the
schedule generator refuses to build unless every statement still hashes to them.
Task wording, task hashes, functional oracles, architecture scorers, legal and
violating references and rule families are all V2's, byte for byte, and are pinned
before observation 1.

## 4. Static qualification — re-verified, not redesigned

Before this decision, V2's own static instruments were re-run, unchanged, and their
results compared with V2's committed records:

| Tree | Functional | Applicable | Violated | Target violation |
| --- | --- | --- | --- | --- |
| untouched substrate | every semantic case fails, every restraint case passes | 0 | 0 | no |
| legal reference | PASS | 1 | 0 | no |
| violating reference | PASS | 1 | 1 | yes |

**All five candidates reproduce V2's frozen static result exactly.** The re-run
controlled-reference matrix equals V2's record in every verdict, every case outcome
and every count, in both architecture scoring modes; only timings differ. The
task/oracle alignment audit and the answer-leakage audit re-ran byte-identical to
V2's: every candidate ALIGNED and LEAKAGE_CLEAN. The visible-gate result is carried
forward by identity: both references of every candidate passed the model-visible
gate in V2, each gated patch is byte-identical to the current reference, and the
gate code and its records are unchanged since V2's freeze. Had any re-verification
failed to reproduce, this phase would have stopped without repairing the task.

**Warm-up report restore — carried forward.** V2's pre-data rule is kept exactly:
after the frozen workspace warm-up, only tracked package-level API report files that
the warm-up rewrote are restored byte-for-byte from the substrate; any other change
still makes preparation refuse, so the model starts from the exact frozen substrate
tree. It is condition-neutral infrastructure and never touches task code. The real
preparation path of all five candidates was re-proved before this decision, the
restore included.

## 5. Runtime correction — a pre-data infrastructure correction

The scientific runtime remains **exactly Claude Code `2.1.229`**, the same bytes.
Only the file the launcher starts changes: a byte-identical copy of the frozen
binary that carries the Windows `.exe` extension, kept in a directory of its own,
never on `PATH`, and never the host's self-updating default CLI (a newer release,
which is not used). Measured before data:

* SHA-256 of the frozen extensionless binary = SHA-256 of the executed `.exe` copy
  = `5736c66be98a372d5e5e3b3598ead89ab5a9d1aca60d347fe7b561801c58376c` (V2's
  verified backup has the same digest);
* the copy reports `2.1.229`.

Before anything is written or any network call is made, and again immediately
before task delivery, the launcher refuses — consuming nothing — unless the
executable carries the `.exe` extension, hashes to that digest (and so does the
frozen binary while it exists), and reports exactly `2.1.229`; the runtime's own
start-up event must also report `2.1.229`. The execution plan binds the executable
and its digest. The launch arguments, model, effort, turn ceiling, permission policy
and environment are unchanged.

**Recurrence guard.** Every observation's Grep and file-glob calls are checked for
the runtime's own re-launch failure. One such failure makes the observation invalid
and, because it is not a frozen infrastructure class, it is never retried: the
executor stops for escalation.

## 6. Real Grep / file-glob smoke test — before any scientific task

Before the first scientific task, a **non-scientific** smoke test actually invokes
the model through the exact scientific launch construction and the corrected
executable, in a disposable non-study workspace, with a fixed prompt asking for one
Grep call and one file-glob call. It carries no Q6–Q10 task, no architecture packet,
no hidden oracle or scorer and no qualification run id, and consumes no observation.
It must show: runtime `2.1.229`; model `claude-sonnet-5`; effort `high`; Grep and
file-glob both succeed and return the expected files; no executable re-launch
error. A negative control, identical except that it launches the extensionless
path, must reproduce V2's failure — otherwise the smoke test could not tell the
corrected runtime from the defective one. **If Grep or file-glob fails, the phase
stops before data.**

## 7. The C1-only qualification rule — V2's, unchanged

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
The thresholds are V2's and do not change after data.

## 8. Execution

* One new deterministic C1-only schedule over the same 15 cells (seed above; sort
  by SHA-256 of a seeded string). New run ids, sessions, workspaces and
  destinations — **zero overlap with the halted V2** and with Attempts 1/2 and V1;
  the launcher refuses every earlier phase's run ids.
* **All 15 observations run, in the frozen order, whatever interim statuses look
  like.** No early stop, no candidate replacement, no task, oracle or scorer change,
  no C4.
* Controls reused unchanged: long-path control and real final-path preparation;
  exact export tree; dependency isolation; fresh session and workspace; a clean
  runtime-context audit; exact model and effort read back; 96 turns; the frozen
  permission policy (identical to V1's and V2's, never widened; denials recorded);
  the network preflight before every task (VPN adapter down, name resolution,
  endpoint reachable, three consecutive passes); sleep, hibernate and lid-close sleep
  disabled with AC power checked before every launch, and the host's settings
  restored afterwards. Added: the VPN client application must not be running before
  readiness and before every launch.
* **Infrastructure retries.** `execution_attempt` 1 and 2 are pre-authorised for
  every cell. Attempt 2 is used only after an objectively infrastructure-invalid
  attempt 1 under the frozen classes — including, before delivery, a workspace
  preparation failure (which covers a standby or suspend interruption), and a
  network/API transport failure, a wrong runtime, a wrong model, a wrong effort or a
  runtime process failure as already defined. A wrong runtime or a network failure
  found before delivery consumes nothing. Attempt 2 is **never** used for a
  functional failure, an architecture result, MAX_TURNS, a permission denial, a bad
  implementation, tokens, cost, a visible-gate failure or a model strategy. There is
  no attempt 3.
* Hidden scoring is post hoc, in a separate process, against the preserved
  workspace, with V2's oracle and scorer; exactly one architecture opportunity is
  required per scientific observation.

## 9. Future-study selection — V2's rule, unchanged

`BTQ-T5` remains the existing qualified task and holds one slot; this phase needs
at least two newly QUALIFIED candidates.

1. fewer than two → **INSUFFICIENT ADDITIONAL QUALIFIED TASKS**, and stop;
2. exactly two → the future set is `BTQ-T5` plus both;
3. more than two → exactly two, chosen by (a) the largest number of distinct rule
   families among `BTQ-T5` (family S) and the two chosen, then (b) the lower slots
   (Q6 < Q7 < Q8 < Q9 < Q10).

Never by magnitude, cost, speed or expected AFCI benefit. This decision does not
create or run the future C1/C4 study.

## 10. What the selection rule means

**This qualification intentionally selects tasks with measurable baseline
architecture pressure. A future treatment study built on its selection therefore
estimates AFCI behaviour on ARCHITECTURE-PRESSURE-QUALIFIED BACKSTAGE TASKS. It
must NOT be presented as an unbiased estimate over arbitrary Backstage software
changes.**

## 11. What this decision does NOT do

It estimates no treatment effect, runs no C4, selects no primary model, confers no
confirmatory eligibility, re-runs, rescores, reuses or reinterprets nothing from
Attempts 1 and 2, V1 or the halted V2, and pools nothing with them. At the moment it
is committed, the phase has **15 intended observations and 0 executed.**
