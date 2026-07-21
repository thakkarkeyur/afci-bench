# docs/v2 — Study v2 Design Documentation

Design and methodology documents for **AFCI-Bench study v2**.

This directory holds the v2 study design as it is written: the research
questions, the measurement model, threats-to-validity analysis, the v2 protocol,
and the architecture-conformance rule specification. It is the v2 counterpart to
the v0 documents on `main` (`docs/MAD_v0.md`, `docs/PROMPT_PACK_v0.md`,
`docs/ARCH_RULES.yml`), which remain immutable.

This is a **protocol-development freeze**: it defines the study design and the
evidence contracts. It authorizes **no** paid model run, freezes **no** final
benchmark/model-execution configuration, and uses **no** v1 result to choose any
threshold. Unresolved decisions are tracked as explicit TODOs in
[`OPEN_DECISIONS.md`](OPEN_DECISIONS.md).

Scientific protocol:

- [`RESEARCH_QUESTIONS.md`](RESEARCH_QUESTIONS.md) — RQ1–RQ4 and construct
  definitions (incl. architectural integrity as a broader, not-directly-measured
  construct).
- [`CONDITIONS.md`](CONDITIONS.md) + [`CONDITION_MATRIX.csv`](CONDITION_MATRIX.csv)
  — the four conditions C1–C4.
- [`RESET_PROTOCOL.md`](RESET_PROTOCOL.md) +
  [`RESET_CHECKPOINT_MATRIX.csv`](RESET_CHECKPOINT_MATRIX.csv) — controlled reset.
- [`FAILURE_RERUN_POLICY.md`](FAILURE_RERUN_POLICY.md) — rerun vs data.
- [`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md) — pre-registered
  endpoints (provisional).
- [`INDUSTRIAL_DATA_AUDIT.md`](INDUSTRIAL_DATA_AUDIT.md) — RQ4 feasibility.

Evidence matrices:

- [`CLAIMS_CONSTRUCTS_METRICS.csv`](CLAIMS_CONSTRUCTS_METRICS.csv) — claim ↔
  construct ↔ direct metric.
- [`TASK_RULE_MATRIX.csv`](TASK_RULE_MATRIX.csv),
  [`TASK_ACCEPTANCE_MATRIX.csv`](TASK_ACCEPTANCE_MATRIX.csv),
  [`TASK_LAYER_MATRIX.csv`](TASK_LAYER_MATRIX.csv),
  [`ORACLE_TRACEABILITY.csv`](ORACLE_TRACEABILITY.csv) — task/oracle templates
  (hidden answers deliberately not populated).
- [`MODEL_REGISTRY.yml`](MODEL_REGISTRY.yml) /
  [`MODEL_REGISTRY.csv`](MODEL_REGISTRY.csv) — verified model info; no primary
  model selected.
- [`REVIEWER_RESPONSE_MATRIX.csv`](REVIEWER_RESPONSE_MATRIX.csv),
  [`PILOT_GATE_MATRIX.csv`](PILOT_GATE_MATRIX.csv) — reviewer concerns and gates
  G1–G8 (none passed).
- [`RUN_ARTIFACT_MATRIX.csv`](RUN_ARTIFACT_MATRIX.csv) — per-run artifacts and
  their schemas (`experiments/v2/schemas/`).

Direct **architectural-conformance** (v1's guard was non-functional; see
`archive/v1/REFERENCE_MANIFEST.yml`) and **task-acceptance** measurement models
are defined by the oracle/guard schemas in
[`experiments/v2/schemas/`](../../experiments/v2/schemas/) and validated by the
tests in `experiments/v2/harness/tests/`.

Nothing here references or regenerates v1 results. Cross-reference v1 only via the
pointers in [`archive/v1/`](../../archive/v1/README.md).
