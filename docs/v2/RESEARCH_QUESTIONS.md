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

### RQ1 — Layered dependency-direction conformance

How does AFCI affect **layered dependency-direction conformance** compared with:

- **task-only prompting** (C1);
- **token-matched generic guidance** (C2);
- **persistent repository instruction files** (C3)?

Confirmatory. The **single primary outcome is the dependency-direction violation
rate per applicable frozen opportunity**; the comparison C4 vs {C1, C2, C3} on
that rate is the primary contrast family (see
[`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md)).

> **Scope of RQ1 is narrowed (suite-classification decision D).** RQ1's
> confirmatory endpoint measures **dependency direction only**. Contract
> ownership, port/interface placement, observability completeness, duplicated
> logic and general business-logic placement are **not** directly measured by it;
> they are pre-registered **secondary / manual** evidence under **CON-ACB**
> (§2). RQ1 must not be reported as broad or general architectural conformance.
>
> **And it is narrowed again by what the substrate can create.** The endpoint is
> measured over the **represented** task-creatable dependency decisions (§2,
> CON-AC), which on the canonical substrate are three decision clusters over two
> leaf rules and two source scopes. An RQ1 answer is an answer **about those
> decision families**; it is not automatically an answer about every architecture
> rule or every layer pair.

The **C4-vs-C3**
comparison **allows superiority, equivalence, or inferiority** — the study
measures the relationship rather than assuming C4 wins, and **C3 ≈ C4 is a valid,
publishable outcome** ([`CRITICAL_DESIGN_DECISIONS.md`](CRITICAL_DESIGN_DECISIONS.md)
D4). Under equivalence the contribution is the benchmark, the validated oracle,
the governance/auditability process, and an honest equivalence finding.

### RQ2 — Reset robustness

Does **controlled mid-task context interruption** (a *reset*, defined in
[`RESET_PROTOCOL.md`](RESET_PROTOCOL.md)) degrade **layered dependency-direction
conformance** and task completeness, and does AFCI **attenuate** that
degradation?

Confirmatory for the **condition × reset interaction** on a direct outcome;
the reset main effect is reported alongside it.

> **Scope of RQ2 is narrowed (suite-classification decision D).** RQ2's
> confirmatory endpoint **E4** is the condition × reset interaction on the
> **dependency-direction violation rate** (E1's response), fitted over the
> E1-eligible task set only, and on the hidden acceptance-test pass proportion
> (E3). Like RQ1 it must **not** be reported as broad or general architectural
> conformance. Reset effects on the broader **CON-ACB** dimensions (contract
> ownership, port/interface placement, observability completeness, duplicated
> logic, general business-logic placement) may be observed, but only as clearly
> labelled **secondary / exploratory** manual evidence (§2, `CL15`), never as part
> of the confirmatory interaction.

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

### CON-AC — Layered dependency-direction conformance (directly measured)

**Definition (narrowed by suite-classification decision D).** The degree to which
a produced patch keeps every internal module import inside the layer boundaries
permitted by the frozen dependency matrix: dependencies point inward, and a
forbidden inter-layer edge is a violation however it is expressed (path alias,
relative path, or barrel / re-export). This is **one facet** of architecture — the
dependency-direction rule family **AR-DEP-001…006** in
[`ARCHITECTURE_RULE_CATALOG.yml`](ARCHITECTURE_RULE_CATALOG.yml) — and nothing
wider.

**Direct operationalization.** The **single primary metric** is the
**dependency-direction violation rate per applicable frozen opportunity** (E1;
raw violation counts retained separately as a descriptive diagnostic). The
numerator is `opportunity_accounting.violated_opportunity_count` and the
denominator/offset is `opportunity_accounting.applicable_opportunity_count`, both
from the blind architecture finding
([`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md) §2.1). The
**proportion of applicable opportunities satisfied** is a **descriptive
transformation** of the same measurement, reported for interpretability but
**not** an independent confirmatory endpoint
([`CRITICAL_DESIGN_DECISIONS.md`](CRITICAL_DESIGN_DECISIONS.md) D8). Both are
produced by the alias/barrel/re-export-aware dependency-direction checker
(`experiments/v2/oracle/`), which is valid for this purpose only after guard
precision/recall validation (gate **G6**;
[`ORACLE_VALIDATION_REQUIREMENTS.md`](ORACLE_VALIDATION_REQUIREMENTS.md)).
Rule applicability, severity, and evaluator are recorded per task in
[`TASK_RULE_MATRIX.csv`](TASK_RULE_MATRIX.csv); which candidate tasks contribute
to E1 at all is recorded publicly in
[`PILOT_PUBLIC_TASK_MATRIX.csv`](PILOT_PUBLIC_TASK_MATRIX.csv)
(`e1_analysis_eligibility`).

**The measured space is the represented one, and it is bounded.** CON-AC is
measured over the **pre-registered task-creatable dependency decisions represented
by the canonical substrate and task suite**, not over the rule family in the
abstract. On this substrate that space has a demonstrated ceiling of **3 decision
clusters, 2 leaf rules, 2 source scopes and 3 forbidden targets**: the remaining
implemented leaves (`AR-DEP-002` `contracts`, `AR-DEP-003` `core`, `AR-DEP-004`
`infra`) are **detectable but not task-creatable** under black-box functional
acceptance
([`DEPENDENCY_TASK_FEASIBILITY.md`](DEPENDENCY_TASK_FEASIBILITY.md)). Therefore:

- **observed E1 effects generalise directly to the represented
  dependency-decision families, not automatically to all architecture rules or all
  layer pairs**;
- the breadth ceiling is reported as a **construct-validity limitation** of the
  study, with its cause, rather than left as an unexplained gap;
- this narrows what may be claimed; it **does not** broaden CON-AC, and none of the
  CON-ACB dimensions below becomes measurable by it.

**E1 does NOT directly measure** — each of these is CON-ACB evidence, not CON-AC:

- **contract ownership** (where externally visible shapes are declared);
- **port / interface placement** (dependency inversion seams);
- **observability completeness** (required log fields on every handler/error path);
- **duplicated logic** across layers;
- **general business-logic placement**.

**Must NOT be proxied by.** Code churn / `Delta-CodeLOC` (a change-footprint
metric, not conformance), `layer_jaccard`-style self-comparisons, or `npm run
ci` passing (a verification outcome, not conformance). The v1 guard was
non-functional and blind. `applicable_rule_count` must **not** be used as the E1
offset, and a stub or unimplemented rule must **not** enlarge the E1 denominator.

### CON-ACB — Broader architectural conformance (NOT directly measured by E1)

**Definition.** Conformance to the declared architecture rules that E1 does not
evaluate: contract ownership (`AR-CONTRACT-001`), observability completeness
(`AR-OBSERV-001`), and coding/change discipline including duplicated logic and
business-logic placement (`AR-CODE-001`), plus port/interface placement as a
design-seam judgement.

**Status in v2.** These dimensions remain **pre-registered secondary / manual
evidence**. They are **not** part of the confirmatory family, they carry no
endpoint id, and they are **excluded from E1's numerator and denominator** — each
is an unimplemented oracle stub that reports `UNIMPLEMENTED` and can never report
PASS. **Confirmatory use of manual evidence is permitted only** under the stated
reliability gate: two blinded raters and **Cohen's κ ≥ 0.70** where applicable
([`MANUAL_RATING_PROTOCOL.md`](MANUAL_RATING_PROTOCOL.md),
[`ORACLE_VALIDATION_REQUIREMENTS.md`](ORACLE_VALIDATION_REQUIREMENTS.md)); below
that bar the dimension is reported **descriptively only**.

**Must NOT be proxied by.** E1. A result on the dependency-direction rate is
evidence about dependency direction and nothing else. **The paper must not
describe E1 as broad or general architectural conformance**, and no CON-ACB
dimension may be reported as "directly measured" (final-claim audit, gate
**G8**). Implementing `AR-CONTRACT-001` or `AR-CODE-001` as automated checkers is
**future work intended to broaden E1** — not a route to readmit an
already-excluded task post hoc (`TD-B33`).

### CON-TC — Task completeness

**Definition.** The degree to which the produced patch satisfies the task's
**acceptance criteria** — the behaviour the task actually required — independent
of whether visible CI passes.

**Direct operationalization.** (1) **Hidden acceptance-test pass proportion**
(tests withheld from the model, exercising the required behaviour) is the
**confirmatory / principal completeness endpoint** (E3; claim CL07). (2)
**Acceptance-criteria coverage** (each criterion adjudicated satisfied / not) is a
**supporting descriptive measure** (exploratory; claim CL08) reported alongside
E3, **not** an independent confirmatory endpoint.
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
v2 metric. Dependency-direction conformance (CON-AC) is a *necessary, measurable
proxy* for **one facet** of integrity, but conformance to one rule family is **not
identical** to integrity, and neither CI pass nor `Delta-CodeLOC` is evidence of
it. The evidence ladder is deliberately three-tiered and must not be collapsed:

| Tier | What it is | v2 status |
|---|---|---|
| **CON-AC** | layered dependency-direction conformance | **directly measured** (E1, confirmatory) |
| **CON-ACB** | broader architectural conformance (contract ownership, port/interface placement, observability completeness, duplicated logic, business-logic placement) | **secondary / manual**, κ ≥ 0.70 gated |
| **CON-AI** | architectural integrity (latent) | **not directly measured at all** |

Any statement about "architectural integrity" must be phrased as **conformance to
the declared dependency-direction rules** unless *converging, pre-registered*
evidence across constructs is shown to support the broader claim. Marking a
broad-integrity claim "supported" is prohibited before data collection and, even
after, requires explicit justification (final-claim audit, gate **G8**).

---

## 3. Unit of analysis and evidence discipline

- **Unit of analysis:** one experimental **run** = (task × condition × reset-state
  × model × repetition), producing one patch and one set of records. **Task** is
  a blocking / random effect; **condition** and **reset** are fixed effects; see
  [`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md).
- **Analysis eligibility is a per-task structural property, not a run outcome.** A
  task whose frozen `applicable_opportunity_count` is **0** carries no
  dependency-direction exposure and is therefore **structurally ineligible for
  E1** — it is **not** coded as zero violations, and it is **not** a failed run.
  Eligibility per candidate is recorded in
  [`PILOT_PUBLIC_TASK_MATRIX.csv`](PILOT_PUBLIC_TASK_MATRIX.csv) and
  `experiments/v2/tasks/public/TASK_INDEX.csv` as `scored`, `functional-only`, or
  `inactive-reserve`. An E1-ineligible task still contributes to hidden functional
  acceptance (E3), the cost measures, and pre-registered exploratory analyses.
- **Direct over indirect:** RQ1–RQ3 endpoints are direct conformance/completeness
  outcomes; change-footprint, tokens, time, and iterations are **secondary**.
  CON-ACB dimensions are secondary/manual and never substitute for E1.
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
