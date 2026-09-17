# AFCI-Bench — next study plan

**Status of everything below: NOT STARTED.** No runs exist, no results are
pre-populated, and no placeholder row appears in any results table.

**Experiment A is now DESIGNED AND FROZEN, and still NOT STARTED.** Its five
open decisions have been taken and are recorded in
[`SL-V2-LOWER-MODEL-01`](../../docs/v2/AFCI_LOWER_MODEL_PILOT_DECISION.md); its
18-row schedule is committed; and its endpoints and continuation rule are frozen
**before** any observation exists. Zero lower-model observations exist. §A below
is updated to record what was decided; nothing else in this document changes.

---

## What the evidence points at

Two rival explanations account for every v2 null, and they are not separable from
current data:

| explanation | the claim | the evidence for it |
| --- | --- | --- |
| **strong-model ceiling** | `claude-sonnet-5` already knows what the MAD would tell it | functional acceptance saturated everywhere (3/3, 3/3, 3/3, 17/18, 17/18); baseline architecture violations at or near zero across three instruments |
| **substrate legibility** | a 49-file synthetic Nx monorepo advertises its own architecture through imports and path aliases | three purpose-built instruments all landed at or near the architecture floor on the same substrate |

Each planned experiment varies **one** of these and holds the other fixed.

---

## Experiment A — `AFCI_LOWER_MODEL_PILOT` — **FROZEN PRE-DATA**

**Question.** Does a lower-capability model escape the architecture floor, and
does explicit architecture context pay for itself there?

**Why it comes first.** It reuses the entire existing apparatus — same substrate,
same tasks, same hidden acceptance packages, same architecture oracle, same
runner, same frozen analysis. Only the model changes. It is by far the cheaper of
the two and it tests the explanation that is easiest to falsify.

**What it would keep fixed.** Substrate `630d3180` / `0198d76c…` (49 files); tasks
PT01, PT04, PT07 at their existing hashes; conditions C1 and C4 with the MAD at
`bf6f32b1…`; the block-paired design and within-block randomisation; CLI 2.1.229;
sterile subscription execution with exact model readback.

**What had to be decided before it runs, and what was decided.** All five are now
taken, in `SL-V2-LOWER-MODEL-01`, before any observation exists.

| open decision | what was decided |
| --- | --- |
| 1. the exact model id, and whether `TD-B03` is engaged | `claude-haiku-4-5-20251001`. It was **not guessed**: the installed 2.1.229 runtime was enumerated read-only first — the only Haiku-family identifiers it carries are `claude-haiku-4-5` and the dated form, with no Haiku 5 or newer — and then one infrastructure-only probe requested the **exact dated id** and read it back unambiguously from `system.init.model` and `modelUsage`, exit 0, no API key. `TD-B03` is **explicitly held open**: `primary_model` stays `null`. |
| 2. cost pilot, architecture pilot, or both | **Both, on ONE purpose, as two INDEPENDENT channels.** Architecture quality and efficiency are measured, reported and decided on separately, and are combined into no single score — because AFCI may be useful when violations fall and tokens rise modestly, and a composite would hide exactly that case. |
| 3. a new `run_purpose` | `AFCI_LOWER_MODEL_PILOT`, with its own firewall, its own freeze tables, its own corpus-eligibility adjudication and its own budget authority. It deliberately does not reuse `AFCI_EFFICIENCY_PILOT`: a second model under one purpose marker would make two experiments indistinguishable in every artifact that carries only the purpose. |
| 4. repetition count and the decision rule | 3 repetitions per (task, condition) — 18 runs, 9 paired blocks — and a two-branch continuation rule (quality signal **or** efficiency signal), both frozen in §12 of the record before any observation. No power calculation justifies the count and none is implied. |
| 5. whether a weaker model needs a different budget | **No change: 64 turns, `NON_RESET`, identical in both arms.** It is deliberately not lowered because the model is cheaper. A weaker model needing more turns to reach the same place is the phenomenon under study, and a smaller ceiling would convert that phenomenon into a truncation artefact. |

**One design choice the original plan did not anticipate.** The pilot is
**`NON_RESET` only**. The reset arm is refused rather than merely unscheduled, so
that MODEL CAPABILITY is the single moderator this experiment varies; adding
context-loss at the same time would leave any difference attributable to either.
The reset factor remains available as a separate future experiment.

**The architecture endpoint this pilot adds.** Attempt 2 was cost-only and
produced no architecture value at all. This pilot records, for every run,
`architecture_applicable_opportunity_count`,
`architecture_violated_opportunity_count`, `raw_architecture_violation_count` and
a target-violation boolean — scored post hoc, out of band, against the preserved
worktree, by a channel that is separate from functional scoring in both
directions. The coding model is never given the scorer, its rules, the hidden
opportunity definitions or the target rule identities, and the run record carries
counts and a one-way digest rather than any private identifier.

**The comparison with Sonnet is descriptive and never pooled.** Within-Sonnet
`C4/C1` against within-lower-model `C4/C1`, with the direction and magnitude of
the difference described. One asymmetry is stated wherever the comparison is
made: the Sonnet pilot produced no architecture measurement, so the quality
channel has no Sonnet counterpart and is lower-model only.

**What would make it informative even if it is another null.** A lower-capability
model that *also* sits at the architecture floor would make the substrate
explanation much harder to avoid, and would redirect effort to Experiment B. A
model that produces non-zero baseline violations gives the study its first
discriminating instrument, which is currently the binding constraint on everything.

**Reused without change:** `run_v2.py` and the runner state machine; sterile
`HOME`/config construction; the context auditor; `efficiency_metrics.py`;
`functional_evaluation.py` and the `FUNCTIONAL_VALID` definition verbatim; the
architecture oracle and evaluator mount mechanism; the run-identity and
execution-attempt guards; the permission allowlist for the governed CI surface.

**Newly built for it:** `architecture_evaluation.py`, the post-run architecture
channel, and a private arbitrary-worktree architecture scorer behind it;
`lower_model_run_plan.py`, the frozen schedule and its whole-execution preflight;
and `lower_model_pilot_analysis.py`, the frozen analysis. All three are inert for
every other purpose.

**Its analysis is computable, and that was checked before any data.** The
analysis was executed against synthetic records only and returns the frozen
outcome correctly in four directions — including the one the two-channel design
exists for, where architecture improves while token cost rises and a composite
score would have reported a wash. This matters because Attempt 2 of the
efficiency pilot was, for a while, executable and *not* analysable.

**Its controls are executed, not asserted.** For each of PT01, PT04 and PT07 a
legal reference scores one applicable opportunity and zero violations, and a
**functionally correct** target-violating reference scores one applicable and one
violated with the exact intended dependency violation detected — both measured
through the same arbitrary-worktree scorer the pilot will use, on worktrees
shaped exactly like the one a real run leaves behind. That both references pass
hidden functional acceptance is the anti-circularity control: if a violating
implementation could not pass, the functional oracle would be enforcing placement
and the architecture measurement would be circular.

---

## Experiment B — `OPEN_SOURCE_COMPLEXITY_STUDY`

**Question.** On a real repository with genuine architectural complexity — one
whose intended architecture is *not* inferable from its own structure — does
explicit architecture context change behaviour?

**Why it is second.** It needs almost everything new: candidate repositories,
new task bodies, new hidden acceptance packages, new architecture rule linkage,
new opportunity authoring, and independent review of each. That is a far larger
investment and it should be justified by what Experiment A shows.

**What it would have to establish first.**

1. **Repository selection criteria**, fixed in advance — size, layering,
   documented architecture, test suite quality, licence, and above all a stated
   test for *architecture legibility* so "less legible" is a property that was
   measured rather than assumed.
2. **Task authoring** under the existing `TASK_AUTHORING_POLICY.md`, including
   leakage validation.
3. **Hidden acceptance packages** with semantic mutation validation, matching the
   standard PT09/PT10 were held to.
4. **Architecture rule catalogue** for each repository, and opportunity linkage
   that the oracle can score out of band.
5. **A MAD per repository** — and a decision on whether it is authored by hand,
   which raises an author-effort confound the current MAD does not have.
6. Independent review (`TD-B32`) before any confirmatory use.

**The risk worth naming now.** Real repositories bring real confounds: unfamiliar
domains, flaky tests, non-deterministic builds, and training-data contamination if
the repository is public and popular. The last is serious — a model may have
memorised the codebase, which changes what "being told the architecture" even
means. A selection criterion addressing contamination should exist before
repositories are shortlisted.

---

## What neither experiment changes

Both are **non-confirmatory** unless and until the suite-wide gates are passed.
As at 2026-09-17, unchanged by anything in this package:

| item | state |
| --- | --- |
| suite-wide protocol | **PRE-FREEZE** |
| gate `G1` | not passed |
| `TD-B32` independent review | open |
| `TD-B34` replication depth | open and blocking |
| `TD-B03` primary model | open; `primary_model: null` |
| `TD-B19` isolation | open and blocking |
| `TD-B37` power simulation | may not run |
| confirmatory evidence collection | not begun |

---

## Sequencing

1. ~~**Decide the Experiment A model and run purpose**, and freeze its decision
   rule before any observation.~~ **DONE** — `SL-V2-LOWER-MODEL-01`. Zero
   observations existed when it was frozen.
2. **Run Experiment A.** Preflight the whole schedule's derived identities first —
   that check exists now precisely because its absence cost Attempt 1. It is
   `lower_model_run_plan.preflight`, it derives all 18 identities with no model
   and no cost, and it refuses the whole execution on a single defect.
3. **Read the result before planning Experiment B.** If a weaker model escapes the
   architecture floor, the study has its instrument and the priority becomes
   replication depth (`TD-B34`). If it does not, the substrate becomes the prime
   suspect and Experiment B becomes the priority.
4. **Only then** consider whether any confirmatory path is open, which still
   requires `TD-B32`, `TD-B34`, `TD-B12`/`G6` and `G1`.

---

## One honest caveat about scope

Both experiments test *why the current null appeared*. Neither is yet a test of
the AFCI hypothesis itself, because that test needs an instrument that
discriminates architecture at baseline — and no such instrument exists today. Any
plan that skips straight to a confirmatory architecture contrast would be
measuring with a ruler that has already been shown to have no markings on it.
