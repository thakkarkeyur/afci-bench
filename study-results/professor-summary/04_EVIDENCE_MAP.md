# AFCI-Bench — evidence map

How to get from any number in this package to the raw artifact behind it.
Full detail in [`../AFCI_EVIDENCE_INDEX.md`](../AFCI_EVIDENCE_INDEX.md).

---

## The general shape

```
summary table  ->  derived CSV in this package
               ->  analysis artifact (frozen report / scoring JSON / v1 aggregate)
               ->  per-run governed record (run_record.json)
               ->  raw runtime evidence (runtime_evidence.jsonl, captured worktree)
```

Every step is a file on disk or a git object. Nothing is asserted without one.

---

## Where the raw evidence lives

Bulk artifacts are **not** copied into the repository. The package stores derived
tables, pointers and hashes.

| experiment | raw evidence | in-repo derived |
| --- | --- | --- |
| v1 original | git branch `rerun-v1-opus7-artifacts` (not checked out) | [`01_v1_original_study/`](../01_v1_original_study/) |
| PT08 diagnostic | `D:\pt08-diagnostic` | [`02_pt08_diagnostic/`](../02_pt08_diagnostic/) |
| PT09 / PT10 | `D:\afci-v2-qual` | [`03_pt09_pt10_qualification/`](../03_pt09_pt10_qualification/) |
| Efficiency Attempt 1 | `D:\afci-runs\obs`, `D:\afci-runs\logs` | [`04_efficiency_attempt_1_aborted/`](../04_efficiency_attempt_1_aborted/) |
| Efficiency Attempt 2 | `D:\afci-runs\attempt-2` | [`05_efficiency_attempt_2_completed/`](../05_efficiency_attempt_2_completed/) |

---

## Four worked traces

### "AFCI increased code churn by 65.7%" (v1)

1. [`01_v1_original_study/v1_headline_recomputed.csv`](../01_v1_original_study/v1_headline_recomputed.csv)
2. [`01_v1_original_study/v1_taskwise_churn_recomputed.csv`](../01_v1_original_study/v1_taskwise_churn_recomputed.csv) — all 12 tasks
3. `git show rerun-v1-opus7-artifacts:experiments/paper/results_v1.csv`
   (blob `0d350eb262b49385f290d0a9df6693b34ba3d919`), columns
   `code_additions + code_deletions`
4. `git show rerun-v1-opus7-artifacts:experiments/runs_v1/T05/afci/metrics.json`
   — and the sibling `patch.diff`, `prompt.md`, `ci_output.txt`, `run_meta.json`

### "median C4/C1 input tokens = 1.4014" (Attempt 2)

1. [`05_efficiency_attempt_2_completed/attempt2_endpoint_ratios.csv`](../05_efficiency_attempt_2_completed/attempt2_endpoint_ratios.csv)
2. [`05_efficiency_attempt_2_completed/attempt2_primary_pairs.csv`](../05_efficiency_attempt_2_completed/attempt2_primary_pairs.csv)
   — the 16 pairs whose median it is
3. [`05_efficiency_attempt_2_completed/efficiency_pilot_frozen_analysis_report.json`](../05_efficiency_attempt_2_completed/efficiency_pilot_frozen_analysis_report.json)
   → `primary_endpoint.pairs`
4. `D:\afci-runs\attempt-2\afci-efficiency-pilot-pt01-c1-real-r1-non-reset-a2-739ef44ece2e\run_record.json`
   → `efficiency.usage.TOTAL_INPUT_TOKENS`
5. the same directory's `runtime_evidence.jsonl` — the terminal result event

### "PT10 violated its target in 1 of 3 runs"

1. [`03_pt09_pt10_qualification/qualification_classification.csv`](../03_pt09_pt10_qualification/qualification_classification.csv)
2. [`03_pt09_pt10_qualification/qualification_runs.csv`](../03_pt09_pt10_qualification/qualification_runs.csv)
3. `D:\afci-v2-qual\score\pt10-r3.json` → `architecture.target_findings[0]`
   — the field, not its value: the finding id carries the rule id and the anchor
   path, which are hidden evaluator semantics and stay private
4. `D:\afci-v2-qual\runs\instrument-qualification-diagnostic-pt10-c1-real-r3-8f809ab6ee92\worktree_post_run\`
   — the captured post-run worktree; the modified file and line are identified by
   step 3 and are withheld here for the same reason

Steps 3 and 4 need the private evaluator repository and the raw evidence root,
both outside this repository. Steps 1 and 2 are public and carry every number.

### "Attempt 1 attempted 9 of 36 rows and is excluded"

1. [`04_efficiency_attempt_1_aborted/attempt1_attempted_rows.csv`](../04_efficiency_attempt_1_aborted/attempt1_attempted_rows.csv)
2. [`04_efficiency_attempt_1_aborted/AFCI_EFFICIENCY_PILOT_ATTEMPT_1_EVIDENCE_INVENTORY.json`](../04_efficiency_attempt_1_aborted/AFCI_EFFICIENCY_PILOT_ATTEMPT_1_EVIDENCE_INVENTORY.json)
   — derived from the artifacts, not from prose
3. `docs/v2/AFCI_EFFICIENCY_PILOT_ATTEMPT_1_ABORT_DECISION.md`
4. `D:\afci-runs\obs\afci-efficiency-pilot-*\` and `D:\afci-runs\logs\seq-0*.log`

---

## Reproducibility anchors

| anchor | value |
| --- | --- |
| public repo `study-v2` | `c544cc87a4f72dc33763035b0ba2c589ad8e72db` |
| public repo `main` / tag `paper-v0` | `2adc8741acad7ea5423f0bf3d9ad821ff023a35f` |
| private evaluator repo | `e1154227008101f7054c61c33247e5d2c7c52e59` (read only; not modified, not pushed) |
| governed substrate commit | `630d3180af0d02a86330dfb599f559e78df65e94` |
| substrate content hash | `0198d76c189f38589e872cab4305527c08e86ef736e1550e428e05f9178060f3` (49 entries) |
| **MAD** `docs/v2/ARCHITECTURE_CONTEXT.md` | `bf6f32b162a23b851596d8b489d938bef10d0b8616a50dcc039873d12ffa7a4d` |
| efficiency run plan | `0038cd8b563ea804f4887d21cb37ceddb3a8f7632c4dd2315c260d3a9af95767` |
| Attempt-2 execution plan | `562415031c04b0673c54ac352a4ca35a66e885023aa212cedc284da0c65a087e` |
| schedule seed | `AFCI_EFFICIENCY_PILOT_V1_20260914` (SHA-256 ordering, no language RNG) |
| model / runtime, all v2 runs | `claude-sonnet-5` / Claude Code CLI `2.1.229` |
| v1 release | GitHub `ase2026-artifacts-v1` @ `1ba21ad75dacbac5eb87d354a490b088078c30da` |
| v1 DOI | `10.5281/zenodo.19757261` |

The MAD hash is corroborated independently: the frozen run plan records it as
`architecture_context_sha256`, and hashing the file today reproduces it.

### Task body hashes

| task | sha256 |
| --- | --- |
| PT01 | `6c938822fe19cd6e87942a6ee24ec8f604c0883da1b7f80d45216be35d7c9c39` |
| PT04 | `f349b150b1d8fe5676fed8460b1840b988ee2bb0a78b1966ef82ae9ce9c8a9b5` |
| PT07 | `557caed09420354efbc823c8b72e54b0760ac72847aba0d9c07d99e37ff7d2d7` |
| PT08 | `a31bb515b79cc1e211a662de2a8761c97082dd8bf266ee5b4f660981435badf2` |
| PT09 | `bac32dc0e7163c9ab1816ac6eea6c98738092cca5cf56715e280f1ec1c0ac44c` |
| PT10 | `1b1fe29881b3c9f309939df042272b03164fb3baae878c64345e75edddf36b86` |

Each run record carries the hash of the body it was handed; the runner refuses on
a mismatch.

---

## Reproducing the Attempt-2 analysis

```sh
python experiments/v2/harness/efficiency_pilot_analysis.py \
    --records <the 36 afci-efficiency-pilot-* directories under D:\afci-runs\attempt-2> \
    --out report.json
```

**Pass the 36 directories, not the `attempt-2` root.** The root also contains 12
dry-run readiness records under `readiness-context-audit\` which share the R1
blocks' coordinates; including them corrupts pairing and yields 12 eligible blocks
and a 1.3895 median instead of the correct 16 and 1.4014.

---

## Two traps for a reader of the raw records

1. **`worktree_content_hash` is an input hash.** It is recorded before model
   invocation ("prepared bytes unchanged before launch"). It being identical
   across PT08's three repetitions means they received identical inputs — it says
   nothing about whether their outputs matched.
2. **PT08's three runs share one `run_id`.** All three minted
   `pt08-difficulty-diagnostic-pt08-c1-real-97c5ca96498e` under the pre-`SL-RUNID-01`
   defect, and stayed separable only through distinct `--artifact-root`s.
   Distinguish them by directory (`R1`/`R2`/`R3`) and `session_id`.
