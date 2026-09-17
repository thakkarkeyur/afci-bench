# 04 — efficiency pilot, execution attempt 1 (ABORTED)

**9 of 36 scheduled rows attempted · `claude-sonnet-5` · aborted at sequence 9 ·
authority `SL-V2-EFF-ABORT-01`**

> **Classification: `ABORTED_INFRASTRUCTURE_ATTEMPT`.**
> **`eligible_for_analysis = false` for every row, including the seven intact
> ones.** This folder exists so the professor can see that these runs happened —
> never so a number can be taken from them.

## Files here

| file | what it is |
| --- | --- |
| `attempt1_attempted_rows.csv` | **derived** — the 9 attempted rows, flattened |
| `AFCI_EFFICIENCY_PILOT_ATTEMPT_1_EVIDENCE_INVENTORY.json` | **verbatim copy** of the governed inventory |

The inventory is derived **from the artifacts**, not from the decision prose, so a
disagreement between the two is a mechanical failure rather than a reading. Raw
evidence stays at `D:\afci-runs\obs` with operator logs at `D:\afci-runs\logs`.

## The counts

| | |
| --- | ---: |
| scheduled rows | 36 |
| attempted | 9 |
| never started | 27 |
| intact governed observations | **7** (sequences 1–5, 7, 8) |
| damaged | **2** (sequences 6, 9) |
| collision pairs in the schedule | 18 |
| analyses performed | **0** |

## Root cause

`run_artifacts.derive_run_id` seeded a run's identity with
`run_purpose | task_id | condition | task_sha256 | substrate_content_hash | mode | repetition`
and **omitted the reset state**. The pilot crosses every cell with `NON_RESET` and
`RESET`, so:

```
36 scheduled rows  ->  18 distinct run ids  ->  18 collisions
```

The omission was invisible to every check that existed. `SL-RUNID-01` had added
the repetition index to the seed for exactly this class of defect, and correctly —
but it was decided when no registered purpose crossed a reset factor, so nothing
compared a schedule's derived identities against each other before running it.

A collision only becomes visible when the *second* member of a pair executes.
Sequence 9 is the first row whose partner had already run (sequence 6, three rows
earlier). **The eight rows before it are not intact because anything protected
them — they are intact because of the order the schedule happened to draw.**

## What the collision did

Sequence 6 ran to `COMPLETE` and wrote its governed record. Sequence 9 derived the
same directory and: overwrote the readiness, prompt and prompt-manifest artifacts;
recursively deleted sequence 6's prepared worktree and rebuilt its own; overwrote
the prepared manifest, context audit and launch manifest; **delivered the task and
ran the model to completion**; passed model-identity validation; then **refused**
at `CAPTURE_WORKTREE` with `PREPARED_WORKTREE_DIRTY`, because the capture
destination already held sequence 6's captured worktree — and the refusal handler
wrote sequence 9's refusal record **over sequence 6's completed `run_record.json`**.

The failure was caught by the last control that could have caught it, after the
money had been spent, and the detection itself destroyed a record.

## The two damaged rows

Both share the directory `…afci-efficiency-pilot-pt01-c4-real-r2-d0837c0e6305`.

| seq | cell | status |
| --- | --- | --- |
| 6 | PT01 / C4 / RESET / R2 | `DAMAGED_GOVERNED_RECORD_OVERWRITTEN` |
| 9 | PT01 / C4 / NON_RESET / R2 | `DAMAGED_POST_DELIVERY_COLLIDING_OBSERVATION` |

Sequence 6's raw phase evidence, functional evaluation and captured worktree all
survive. **They must not be used to reconstruct a governed record**: a record
assembled from the evidence it is supposed to attest cannot attest it. The row is
recorded as damaged and left damaged.

Sequence 9 is *not* a pre-observation infrastructure-invalid attempt. The task was
delivered, the model ran to completion, the turns were spent; only the capture
failed, afterwards, for a reason unrelated to the run. Calling it "never really
happened" would understate what Attempt 1 consumed.

## Why the 7 intact rows are excluded too

The tempting move is to keep them and run 29 more. Refused for three reasons:

1. **They are not a random seven.** They survived because their collision partners
   were scheduled later — a selection mechanism nobody designed and nobody can
   adjust for.
2. **Pooling would break the pairing.** The analysis is paired within each of 18
   blocks; pooling would mix blocks measured in different sessions, the exact drift
   within-block randomisation exists to prevent.
3. **A restart that keeps the convenient rows is not a restart.** It is selective
   replacement, and after the fact it is indistinguishable from replacing rows
   because of what they showed.

## No analysis preceded the abort

No `TOKEN_RATIO` analysis · no C1-vs-C4 comparison for any task, arm or repetition ·
no pilot outcome · no continuation-threshold evaluation · no Attempt-1 efficiency
figure read, cited, summarised or compared. The abort rests on 18 deterministic
identity collisions, fully established without reading a single measured quantity.

## The exclusion is enforced, not merely stated

`efficiency_pilot_analysis.assert_single_execution_attempt` refuses a record set
spanning execution attempts (`ANALYSIS_SPANS_EXECUTION_ATTEMPTS`) and refuses any
Attempt-1 record **even on its own** (`ANALYSIS_INCLUDES_ABORTED_ATTEMPT`).
Attempt-1 records are recognised by their silence: a record written after the
repair declares its execution attempt, and one that declares none was written
before it. Every report states on its face which single execution it read.

## The repairs

| repair | where |
| --- | --- |
| reset state joins the run-id seed and prefix | `run_artifacts.derive_run_id` |
| execution-attempt namespace | `run_artifacts.derive_run_id`, `execution_attempt` |
| pre-invocation artifact ownership guard | `run_artifacts.assert_destination_ownable` |
| destructive-reuse prevention | `run_artifacts.ArtifactDirectory.remove_temporary` |
| whole-schedule identity preflight | `execution_attempt.preflight` |
| execution-root isolation | `run_artifacts.assert_execution_root_isolated` |
| the exclusion rule, enforced | `efficiency_pilot_analysis.assert_single_execution_attempt` |

Each is proved by tests in
`experiments/v2/harness/tests/test_efficiency_attempt_identity.py`, including a
reproduction of the pre-repair seed so the defect cannot later be described as
hypothetical.

## Evidence preservation

Every Attempt-1 artifact is preserved exactly as found. Nothing deleted,
rewritten, normalised, repaired, renamed or re-derived; no missing artifact
reconstructed. **The evidence is preserved for audit and provenance only. It is
not a dataset.**
