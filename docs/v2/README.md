# docs/v2 — Study v2 Design Documentation

Design and methodology documents for **AFCI-Bench study v2**.

This directory holds the v2 study design as it is written: the research
questions, the measurement model, threats-to-validity analysis, the v2 protocol,
and the architecture-conformance rule specification. It is the v2 counterpart to
the v0 documents on `main` (`docs/MAD_v0.md`, `docs/PROMPT_PACK_v0.md`,
`docs/ARCH_RULES.yml`), which remain immutable.

## Status: PRE-FREEZE DRAFT (not scientifically frozen)

The previous commit (`b23409f`) described this protocol as "frozen". That was
premature. Following the external **pre-execution scientific-design review**, the
protocol is reclassified:

- The existing protocol is a **pre-freeze draft**.
- It is **structurally complete but NOT scientifically frozen**: mandatory
  scientific decisions remain unresolved (see
  [`CRITICAL_DESIGN_DECISIONS.md`](CRITICAL_DESIGN_DECISIONS.md) and
  [`OPEN_DECISIONS.md`](OPEN_DECISIONS.md)).
- **Scientific freeze occurs only after** this reconciliation is **independently
  approved** *and* the relevant **blocking decisions are closed**.
- **No `protocol-freeze` tag currently exists**, and none is created by this work
  package.

It authorizes **no** paid model run, freezes **no** final benchmark /
model-execution configuration and **no** task / repetition / run count, and uses
**no** v1 result to choose any threshold, power input, or effect size. Unresolved
decisions are tracked as explicit blockers in
[`OPEN_DECISIONS.md`](OPEN_DECISIONS.md); binding design decisions are recorded in
[`CRITICAL_DESIGN_DECISIONS.md`](CRITICAL_DESIGN_DECISIONS.md).

### Pre-execution design-review reconciliation (this work package)

- [`CRITICAL_DESIGN_DECISIONS.md`](CRITICAL_DESIGN_DECISIONS.md) — binding design
  decisions D1–D13 (v1 use, task wording, C3≈C4, content parity, reset, primary
  endpoint, hypothesis hierarchy, model screening, environment, study size).
- [`EXPERIMENTAL_CI_POLICY.md`](EXPERIMENTAL_CI_POLICY.md) — the agent-visible CI
  (`npm run ci:agent`) vs repository validation (`npm run ci`).
- [`TASK_AUTHORING_POLICY.md`](TASK_AUTHORING_POLICY.md) +
  [`TASK_LEAKAGE_TERMS.yml`](TASK_LEAKAGE_TERMS.yml) — public-task leakage policy.
- [`CONDITION_PARITY_POLICY.md`](CONDITION_PARITY_POLICY.md) +
  [`CONDITION_CONTENT_MATRIX.csv`](CONDITION_CONTENT_MATRIX.csv) — condition parity.
- [`ORACLE_VALIDATION_REQUIREMENTS.md`](ORACLE_VALIDATION_REQUIREMENTS.md) — oracle
  validity bar.
- [`PILOT_AND_POWER_POLICY.md`](PILOT_AND_POWER_POLICY.md) — staged pilot and
  mandatory interaction-focused power simulation.

### Pilot task candidates (this work package)

- [`experiments/v2/tasks/public/`](../../experiments/v2/tasks/public/) — six
  primary (`PT01`–`PT06`) and two reserve (`PR01`–`PR02`) **public functional
  task bodies**, plus `TASK_INDEX.csv`, `TASK_SCHEMA.yml`,
  `TASK_AUTHORING_REPORT.md`, and the front-matter schema
  [`public_task.schema.json`](../../experiments/v2/schemas/public_task.schema.json).
  Each body states functional requirements and observable behaviour only; the
  public-task leakage validator reports OK for all (partial advance on `TD-B17`).
- **Hidden evaluator packages** for these candidates (per-task manifests, hidden
  acceptance plans, fixed opportunity sets, expected/prohibited areas, legitimate
  alternatives, reset predicates, threat reviews) exist **only in a separate
  local private evaluator repository**, never in this repository. Every manifest
  is status `review` (not frozen); the architecture oracle refuses to score it
  (`MANIFEST_NOT_FROZEN`).
- **Status:** candidates authored, **not approved and not frozen**. Task-specific
  oracle validity, hidden-acceptance validation, reset-checkpoint review, and
  benchmark discrimination remain open; gates **G1/G2 not passed**; the protocol
  remains **PRE-FREEZE**; **no pilot model execution occurred** and no
  task/repetition/run count or numerical budget was selected.

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
  plus **redacted** per-candidate rows: every task-specific hidden field is
  `stored_in_private_evaluator_repo`, never a real rule id, expected area, or
  hidden criterion.
- [`PILOT_PUBLIC_TASK_MATRIX.csv`](PILOT_PUBLIC_TASK_MATRIX.csv) — public
  per-candidate view (id, title, functional category, public task hash, visible
  CI command, scope, leakage-validation status); carries no hidden answer.
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
