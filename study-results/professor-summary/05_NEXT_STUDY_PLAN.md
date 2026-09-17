# AFCI-Bench — next study plan

**Status of everything below: NOT STARTED.** No runs exist, no results are
pre-populated, and no placeholder row appears in any results table.

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

## Experiment A — `LOWER_MODEL_PILOT`

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

**What must be decided before it runs** — none of which is decided here:

1. The exact model id, and whether `TD-B03` (primary model selection) is thereby
   engaged or explicitly held open.
2. Whether it is a **cost** pilot (mirroring Attempt 2) or an **architecture**
   pilot, or both on separate purposes. These are different run purposes with
   different firewalls, and Attempt 2's cost-only governance produced no
   architecture endpoint by design.
3. A new `run_purpose` with its own eligibility flags, since
   `AFCI_EFFICIENCY_PILOT` is pinned to `claude-sonnet-5` in its frozen plan.
4. Repetition count and the decision rule — **frozen before any observation**, as
   `SL-V2-EFF-01` and `SL-V2-QUAL-01` both were.
5. Whether a weaker model needs a different turn budget. The current budgets are 64
   non-reset, 32 pre-reset, 32 post-reset; a weaker model may hit the ceiling, and
   a ceiling-hit run is a different object from a completed one.

**What would make it informative even if it is another null.** A lower-capability
model that *also* sits at the architecture floor would make the substrate
explanation much harder to avoid, and would redirect effort to Experiment B. A
model that produces non-zero baseline violations gives the study its first
discriminating instrument, which is currently the binding constraint on everything.

**Reusable without change:** `run_v2.py` and the runner state machine; sterile
`HOME`/config construction; the context auditor; `efficiency_metrics.py`;
`functional_evaluation.py`; the architecture oracle and evaluator mount mechanism;
`efficiency_pilot_analysis.py`; the run-identity and execution-attempt guards.

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

1. **Decide the Experiment A model and run purpose**, and freeze its decision rule
   before any observation.
2. **Run Experiment A.** Preflight the whole schedule's derived identities first —
   that check exists now precisely because its absence cost Attempt 1.
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
