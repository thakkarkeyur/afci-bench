# docs/v2 — Research Questions and Construct Definitions

Status: **development protocol for study v2**. This document fixes the four
research questions and the construct definitions on which every v2 claim,
metric, and evaluator depends. It is a design artifact: it does **not** freeze
the final benchmark configuration, it authorizes **no** paid model run, and it
uses **no** observed v1 result to choose any threshold, endpoint, or effect
size. Constructs defined here are operationalized in
[`CLAIMS_CONSTRUCTS_METRICS.csv`](CLAIMS_CONSTRUCTS_METRICS.csv); the experimental
conditions they are measured across are defined in [`CONDITIONS.md`](CONDITIONS.md).

AFCI = **Architecture-First Context Injection**. In the experimental design AFCI
is condition **C4** (see [`CONDITIONS.md`](CONDITIONS.md)); the three comparison
conditions are C1 (task only), C2 (token-matched generic guidance), and C3
(persistent repository instruction file). "MAD" = the approved **Minimum
Architecture Document** (rule set) for a task.

---

## 1. Research questions

### RQ1 — Architectural conformance

How does AFCI affect **architectural conformance** compared with:

- **task-only prompting** (C1);
- **token-matched generic guidance** (C2);
- **persistent repository instruction files** (C3)?

Confirmatory. The **single primary outcome is the architecture-violation rate per
applicable rule/opportunity**; the comparison C4 vs {C1, C2, C3} on that rate is
the primary contrast family (see
[`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md)). The **C4-vs-C3**
comparison **allows superiority, equivalence, or inferiority** — the study
measures the relationship rather than assuming C4 wins, and **C3 ≈ C4 is a valid,
publishable outcome** ([`CRITICAL_DESIGN_DECISIONS.md`](CRITICAL_DESIGN_DECISIONS.md)
D4). Under equivalence the contribution is the benchmark, the validated oracle,
the governance/auditability process, and an honest equivalence finding.

### RQ2 — Reset robustness

Does **controlled mid-task context interruption** (a *reset*, defined in
[`RESET_PROTOCOL.md`](RESET_PROTOCOL.md)) degrade architectural conformance and
task completeness, and does AFCI **attenuate** that degradation?

Confirmatory for the **condition × reset interaction** on a direct outcome;
the reset main effect is reported alongside it.

### RQ3 — Completeness and engineering cost

Does AFCI improve **acceptance-criteria satisfaction** (task completeness)
**without unacceptable increases** in:

- unnecessary changes (change footprint);
- tokens;
- execution time;
- verification iterations;
- files changed?

Completeness is confirmatory; the engineering-cost measures are secondary /
cost-side and are reported as effect sizes with confidence intervals rather than
as a single pass/fail. "Unacceptable" is a **pre-registered tolerance to be set
during pilot design** (blocking decision `TD-B08`/`TD-B15`; see
[`OPEN_DECISIONS.md`](OPEN_DECISIONS.md)) and must not be chosen from v1 data.

### RQ4 — Industrial impact

How did **objective** review and delivery measures change after AFCI adoption at
**FGC** (Fintech Global Center), and how do those measures compare with
**practitioner perceptions**?

Observational / exploratory. Objective measures and perception (survey) measures
are reported **separately**; perception never substitutes for an objective
measure. Feasibility, availability, and the minimum interpretable sample are
audited in [`INDUSTRIAL_DATA_AUDIT.md`](INDUSTRIAL_DATA_AUDIT.md) before any
industrial claim is made.

---

## 2. Construct definitions

Each construct below states (a) what it means, (b) how it is **directly**
operationalized in v2, and (c) what must **not** be used as a proxy for it. IDs
(`CON-*`) are referenced by [`CLAIMS_CONSTRUCTS_METRICS.csv`](CLAIMS_CONSTRUCTS_METRICS.csv).

### CON-AC — Architectural conformance

**Definition.** The degree to which a produced patch obeys the repository's
declared, machine-checkable architecture rules for the task (the approved MAD
rule set): permitted vs prohibited inter-module/inter-layer dependencies, the
correct layer placement of new code, and use of the sanctioned interfaces and
import boundaries.

**Direct operationalization.** The **single primary metric** is the **rate of
architecture-rule violations per applicable rule/opportunity** in the patch (raw
counts retained). The **proportion of applicable rules satisfied** is a
**descriptive transformation** of the same measurement, reported for
interpretability but **not** an independent confirmatory endpoint
([`CRITICAL_DESIGN_DECISIONS.md`](CRITICAL_DESIGN_DECISIONS.md) D8). Both are
produced by a validated conformance oracle (e.g. nx `enforce-module-boundaries`
plus per-rule checks, with manual adjudication for rules that cannot be
automated; see [`ORACLE_VALIDATION_REQUIREMENTS.md`](ORACLE_VALIDATION_REQUIREMENTS.md)).
Rule applicability, severity, and evaluator are recorded per task in
[`TASK_RULE_MATRIX.csv`](TASK_RULE_MATRIX.csv).

**Must NOT be proxied by.** Code churn / `Delta-CodeLOC` (a change-footprint
metric, not conformance), `layer_jaccard`-style self-comparisons, or `npm run
ci` passing (a verification outcome, not conformance). The v1 guard was
non-functional and blind; a v2 conformance metric is valid only after guard
precision/recall validation (gate **G6**).

### CON-TC — Task completeness

**Definition.** The degree to which the produced patch satisfies the task's
**acceptance criteria** — the behaviour the task actually required — independent
of whether visible CI passes.

**Direct operationalization.** (1) **Hidden acceptance-test pass proportion**
(tests withheld from the model, exercising the required behaviour) and (2)
**acceptance-criteria coverage** (each criterion adjudicated satisfied / not).
Criteria and their oracles are recorded per task in
[`TASK_ACCEPTANCE_MATRIX.csv`](TASK_ACCEPTANCE_MATRIX.csv) and
[`ORACLE_TRACEABILITY.csv`](ORACLE_TRACEABILITY.csv).

**Must NOT be proxied by.** Visible-CI pass alone (gameable; in v1 `ci_pass`
saturated True on every run and the default parse returned True), or "a patch was
produced".

### CON-RR — Reset robustness

**Definition.** The change in the **direct** outcomes (CON-AC and CON-TC) caused
by a controlled mid-task context interruption (reset), and the degree to which a
condition **attenuates** that change.

**Direct operationalization.** Degradation = (non-reset outcome − reset outcome)
within a condition; **attenuation** = a smaller degradation under AFCI (C4) than
under a comparison condition. Estimated as the **condition × reset interaction**
on a direct outcome (see [`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md)).
The reset itself is defined operationally in [`RESET_PROTOCOL.md`](RESET_PROTOCOL.md)
and checkpoints in [`RESET_CHECKPOINT_MATRIX.csv`](RESET_CHECKPOINT_MATRIX.csv).

**Must NOT be proxied by.** Anecdotal "the model forgot the architecture after a
reset"; robustness is only claimed from the measured interaction on direct
outcomes.

### CON-EC — Engineering cost

**Definition.** The resource and rework footprint of producing the patch — the
price paid for any conformance/completeness gain.

**Direct operationalization (secondary / cost-side metrics).**
- **Change footprint:** code churn and test churn (lines added/removed), and
  **files changed**, measured **only** as *unnecessary / out-of-scope* change
  relative to the task's required and legitimate-alternative surface
  ([`TASK_ACCEPTANCE_MATRIX.csv`](TASK_ACCEPTANCE_MATRIX.csv)).
- **Tokens** consumed (input + output, from machine-readable run output).
- **Execution time** (wall clock, per run/phase).
- **Verification iterations** (CI attempts / edit-verify cycles).

**Must NOT be proxied by, or promoted to a primary claim.** Change footprint is a
**secondary** metric; it is *not* architectural drift and *not* a conformance or
integrity measure. A cost metric can only **qualify** a conformance/completeness
claim ("gain without unacceptable cost"), never establish one.

### CON-IE — Industrial evidence

**Definition.** **Objective, independently verifiable** measures from FGC's real
code-review and software-delivery records, compared **before vs after** AFCI
adoption, plus **practitioner perception** treated as a distinct, clearly
labelled evidence type.

**Direct operationalization.** Objective: review rounds, architecture-related
review comments, time to first approval, time to merge, PR size — subject to the
availability audit in [`INDUSTRIAL_DATA_AUDIT.md`](INDUSTRIAL_DATA_AUDIT.md).
Perception: survey responses, reported **separately** and never merged into an
objective estimate.

**Must NOT be proxied by.** Survey/self-report presented as objective outcome, or
any FGC count or adoption date that is not sourced from raw records (no invented
numbers).

### CON-AI — Architectural integrity (broader construct — NOT directly measured)

**Definition.** The sustained **structural soundness** of the codebase as
architects intend it: correct layering, absence of architectural erosion, and
maintainability over time. This is a **broad latent construct**.

**Status in v2.** CON-AI is **NOT** claimed to be directly measured by any single
v2 metric. Rule conformance (CON-AC) is a *necessary, measurable proxy* for one
facet of integrity, but conformance to a finite rule set is **not identical** to
integrity, and neither CI pass nor `Delta-CodeLOC` is evidence of it. Any
statement about "architectural integrity" must be phrased as **conformance to the
declared architecture rules** unless *converging, pre-registered* evidence across
constructs is shown to support the broader claim. Marking a broad-integrity claim
"supported" is prohibited before data collection and, even after, requires
explicit justification (final-claim audit, gate **G8**).

---

## 3. Unit of analysis and evidence discipline

- **Unit of analysis:** one experimental **run** = (task × condition × reset-state
  × model × repetition), producing one patch and one set of records. **Task** is
  a blocking / random effect; **condition** and **reset** are fixed effects; see
  [`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md).
- **Direct over indirect:** RQ1–RQ3 endpoints are direct conformance/completeness
  outcomes; change-footprint, tokens, time, and iterations are **secondary**.
- **Confirmatory vs exploratory** is fixed **before** data collection: RQ1
  (C4 vs C1/C2/C3 on a direct conformance outcome) and RQ2 (condition × reset
  interaction) and RQ3-completeness are confirmatory; RQ3-cost and RQ4 are
  exploratory/observational. Multiplicity correction applies to the confirmatory
  family only.
- **No v1-derived thresholds.** No significance level, power target, effect-size
  boundary, ceiling assumption, or "unacceptable cost" tolerance is taken from v1
  results. All such values are pilot-set open decisions (see
  [`OPEN_DECISIONS.md`](OPEN_DECISIONS.md)).
- **No claim is "supported" before data collection** (see
  [`CLAIMS_CONSTRUCTS_METRICS.csv`](CLAIMS_CONSTRUCTS_METRICS.csv), all
  `status = candidate`).
