# 01 — v1 original study

**48 runs · 12 tasks × {baseline, AFCI} × {non-reset, reset} · model "Opus 7" ·
executed 2026-04-20 → 2026-04-23 · base tag `paper-v0`**

> **Classification: historical / exploratory. NOT eligible for any analysis and
> NOT confirmatory v2 evidence.** See
> [`../AFCI_EXCLUSIONS_AND_LIMITATIONS.md`](../AFCI_EXCLUSIONS_AND_LIMITATIONS.md) §1.

## Files here

| file | what it is |
| --- | --- |
| `v1_headline_recomputed.csv` | **derived** — the four headline figures, recomputed |
| `v1_taskwise_churn_recomputed.csv` | **derived** — per-task churn, ratios and CI outcome |
| `results_v1.csv` | **verbatim copy** — the 48-row run-level aggregate |
| `completeness_summary_v1.csv` | verbatim copy — condition-level means |
| `drift_true_v1_codeonly.csv` | verbatim copy — true reset drift (ΔCodeLOC) |
| `drift_summary_v1_codeonly.csv` | verbatim copy — per-task drift advantage |
| `conformance_summary_v1.csv` | verbatim copy — **all zeros, and INVALID** (L3) |
| `completeness_taskwise_v1.csv` | verbatim copy — per-task churn by condition |

Copies were taken with `git show rerun-v1-opus7-artifacts:<path>`. The branch was
never checked out and never merged. Blob SHAs are in
[`../AFCI_EVIDENCE_INDEX.md`](../AFCI_EVIDENCE_INDEX.md) §1.

## Recomputed headline

| metric | baseline | AFCI | relative | per task |
| --- | ---: | ---: | ---: | --- |
| non-reset code churn, mean | 576.58 | 955.42 | +65.7% | AFCI higher 12/12 |
| non-reset test churn, mean | 172.67 | 244.00 | +41.3% | AFCI higher 12/12 |
| reset true drift ΔCodeLOC, mean | 307.7 | 670.5 | +117.9% | AFCI lower 1/12 |
| CI pass | 100% | 100% | — | 48/48 |

All four reproduce exactly from `results_v1.csv` and `drift_true_v1_codeonly.csv`.
All 48 `run_meta.json` files were also read: model "Opus 7" in 48/48,
`ci_exit_code` 0 in 48/48, `base_tag` `paper-v0` in 48/48.

## Two constructs that are easy to confuse

- **Condition-level reset churn** (`completeness_summary_v1.csv`): baseline_reset
  mean 268.92, afci_reset 286.25.
- **True reset drift ΔCodeLOC** (`drift_true_v1_codeonly.csv`): baseline 307.7,
  AFCI 670.5, defined as `|CodeChurn_reset − CodeChurn_nonreset|` per task.

They answer different questions and must not be swapped.

## Where the raw evidence is

`git show rerun-v1-opus7-artifacts:experiments/runs_v1/<TASK>/<CONDITION>/<FILE>`
where `<CONDITION>` ∈ {`baseline`, `afci`, `baseline_reset`, `afci_reset`} and
`<FILE>` ∈ {`run_meta.json`, `metrics.json`, `conformance.json`, `patch.diff`,
`prompt.md`, `ci_output.txt`} — 288 files.

Published: GitHub release `ase2026-artifacts-v1` @ `1ba21ad7`; Zenodo
`10.5281/zenodo.19757261`.

## Why it cannot be used

L1 non-independent runs (the tree was never reset between tasks) · L2 the harness
never invoked a model · L3 AFCI-Guard's regexes never fire · L4 `ARCH_RULES.yml`
is 0 bytes · L5 `layer_jaccard` is a constant 1.0 · L6 no acceptance oracle and
`ci_pass` saturated · L7 lockfile desync on the base · plus baseline architecture
leakage.

**The all-zero conformance table is not a measurement.** v1 architecture columns
in the master run results are blank, never 0.

**Nothing here was modified.** v1 is immutable by standing rule.
