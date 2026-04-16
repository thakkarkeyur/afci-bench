# AFCI-Bench

AFCI-Bench is an anonymized benchmark repository accompanying the paper:

**Architecture-First Context Injection (AFCI): Preserving Architecture Integrity in GenAI-Assisted Software Development**

This repo packages (1) a runnable benchmark codebase, (2) AFCI “architecture constitution” artifacts (MAD + rules + prompt pack),
(3) a task suite, and (4) **paper-ready v0 outputs** (tables/figures/CSV evidence) committed as immutable artifacts.

Repository: https://github.com/thakkarkeyur/afci-bench

---

## Quickstart (run CI)

```bash
npm ci
npm run ci
```

This runs lint + typecheck + tests using the same deterministic gates referenced by the paper.

---

## Repository Layout

### Constitution artifacts (`docs/`)
These define the AFCI architecture constitution and prompt templates:

- `docs/MAD_v0.md` — Master Architecture Document (MAD)
- `docs/ARCH_RULES.yml` — machine-checkable rule definitions / severities
- `docs/PROMPT_PACK_v0.md` — baseline vs AFCI prompt templates

### Experiment suite (`experiments/`)
- `experiments/tasks_v0/` — task specifications (T01–T12) + `TASK_TEMPLATE.md`
- `experiments/scripts/` — conformance utilities (AFCI-Guard scripts)
- `experiments/paper/` — v0 CSV evidence used in paper figures/tables  
  - `experiments/paper/drift_summary_v0_codeonly.csv`

### Paper artifacts (`paper/`)
**Exact v0 outputs used in the paper** (committed as immutable artifacts):

- `paper/figures/Figure1_AFCI_Workflow.png`
- `paper/figures/Figure3_drift_codeonly.pdf`
- `paper/figures/sources/Figure1_AFCI_Workflow.drawio` (editable source)
- `paper/tables/table2b_drift_codeonly.tex`
- `paper/tables/table_conformance_summary.tex`

---

## Paper Artifact (v0, immutable)

The following files are the authoritative v0 artifacts used in the manuscript:

**Figures**
- `paper/figures/Figure1_AFCI_Workflow.png`
- `paper/figures/Figure3_drift_codeonly.pdf`

**Tables**
- `paper/tables/table2b_drift_codeonly.tex`
- `paper/tables/table_conformance_summary.tex`

**CSV evidence**
- `experiments/paper/drift_summary_v0_codeonly.csv`

> These v0 artifacts should not be overwritten by regeneration scripts. Future “v1+” reruns should be added as new outputs (e.g., `*_v1.csv`)
> or released as separate bundles.

---

## Task suite (v0)

The task suite is located in `experiments/tasks_v0/`.

The paper’s main drift analysis focuses on the eight-task subset:
**T01–T06, T11–T12**.

---

## AFCI-Guard (conformance checking)

Conformance utilities are in `experiments/scripts/`:

- `experiments/scripts/afci_guard_check.py`
- `experiments/scripts/aggregate_conformance.py`

These scripts support patch-level conformance checks aligned to MAD constraints (e.g., ports placement, contract ownership,
observability heuristics). They are included for paper transparency and as a foundation for expanded reproducibility.

---

## Notes on full reproduction

This repo includes the benchmark codebase, constitution artifacts, task suite, and paper-ready v0 outputs.
Full regeneration from raw per-run artifacts typically requires the `experiments/runs/**` bundle (prompts/patches/CI logs per run),
which may be released separately due to size.

---

## License

MIT (see `LICENSE`).
