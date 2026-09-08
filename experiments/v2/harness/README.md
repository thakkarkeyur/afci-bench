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

## Modules

| Module | Role |
|---|---|
| `prepare_model_worktree.py` | Builds the governed model-visible worktree and its snapshot manifest (`MODEL_VISIBLE_WORKTREE_POLICY.md`). **Byte-pinned by the private evaluator's public linkage — do not edit without a linkage re-approval.** |
| `substrate_identity.py` | The canonical substrate content hash, from committed Git blob bytes. **Also byte-pinned.** |
| `context_audit.py` | Sterile-environment preparation, the context-source scan, the frozen session-restoration guard, and the fail-closed `CLEAN`/`CONTAMINATED` verdict. |
| `evaluator_mount.py` | Evaluator-mount boundary predicates (`EVALUATOR_MOUNT_POLICY.md`). |
| `governance_text.py` | Governance-prose passage/claim helpers used by the doc tests. |
| `run_v2.py` | **The runner.** The fail-closed state machine and the CLI. |
| `run_governance.py` | Governed inputs, refusal codes, the run-purpose firewall, and the prerequisite report. |
| `run_worktree.py` | Runner-time enforcement of the worktree policy (`TD-B22`) and post-run capture. |
| `model_adapter.py` | Fresh-process launch construction, the invocation adapter, and the `Q1`/`Q8` model-identity contract. |
| `run_artifacts.py` | The deterministic run-artifact layout and the run record, validated against `run_record.schema.json`. |

## The runner

```bash
# What is ready, and what blocks the authorised run
python experiments/v2/harness/run_v2.py --check-readiness \
    --task PT08 --condition C1 --run-purpose PT08_DIFFICULTY_DIAGNOSTIC

# Every safe pre-launch state, and no model process
python experiments/v2/harness/run_v2.py --dry-run \
    --task PT08 --condition C1 --run-purpose PT08_DIFFICULTY_DIAGNOSTIC
```

State machine, entered strictly in order, each state only from its immediate
predecessor and only after that predecessor recorded an explicit `PASS` or a
coded `SKIPPED`:

```
PRECHECK -> PREPARE_WORKTREE -> CONTEXT_AUDIT -> BUILD_FRESH_LAUNCH
         -> MODEL_INVOCATION -> MODEL_IDENTITY_VALIDATION -> CAPTURE_WORKTREE
         -> POST_RUN_EVALUATION -> RECORD_ARTIFACTS -> COMPLETE
```

**A run must declare an explicit `--run-purpose`.** The only authorised purpose
is `PT08_DIFFICULTY_DIAGNOSTIC` (`SL-PT08-01`), which admits `PT08` only, `C1`
only, and stamps every artifact with `confirmatory_eligible`,
`enters_confirmatory_dataset`, `enters_confirmatory_e1_analysis`,
`enters_treatment_effect_analysis` and `enters_power_estimation` all `false`.
The flags are derived from the purpose and re-checked against it, so an artifact
cannot be promoted by handing in different values; an unmarked artifact is an
error and never a confirmatory observation.

**Artifacts go to a scratch root** (default: a temp directory outside the
repository). Writing a non-confirmatory artifact under `experiments/v2/results/`
or `experiments/v2/analysis/` is refused.

**No model is selected, and there is no fallback.** `MODEL_REGISTRY.yml` records
`primary_model: null` (`TD-B03`), so real invocation is refused before any
process could be created. A dry run reports `MODEL_SELECTION_REQUIRED` and never
substitutes a model.

The runner **implements** runner-time worktree enforcement (`TD-B22`) and the
`Q1`/`Q8` validation paths (`TD-B21`); none of that has been **validated in a
live runtime**, and the run record says so (`live_runtime_validated: false`).
`run_record.schema.json` is harness-local because `experiments/v2/schemas/` is
byte-pinned by the private linkage and cannot gain the quarantine fields without
a re-approval — the runner reports that as a prerequisite rather than editing a
pinned payload.
