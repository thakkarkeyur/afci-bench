# experiments/v2/harness — Execution Harness (v2)

The v2 **run harness**: the orchestration that, for each (task x condition),
prepares an isolated working state, invokes the model, captures the produced
change, and records inputs/outputs for analysis.

This replaces the v1 harness (`experiments/scripts/run_one_v1.sh`), which
snapshotted `git diff paper-v0` over a never-reset, accumulating working tree and
did not itself invoke a model — yielding non-independent, single-run cells (see
`archive/v1/REFERENCE_MANIFEST.yml`, limitations `L1`/`L2`). The v2 harness
should give each run an independent, reset starting state and couple model
invocation with change capture.

Add harness scripts/config here. Raw transcripts, temporary worktrees, and
evaluator mounts are gitignored and must not be committed.
