# docs/v2 — Statistical Analysis Plan (SAP)

Status: **provisional development SAP for study v2**. Pre-registers the
confirmatory endpoints, candidate models, and analysis discipline **before** any
data collection. Development artifact only: it does **not** freeze the final
benchmark configuration and authorizes **no** paid model run.

> **No threshold in this plan is derived from v1.** No significance level, power
> target, minimum detectable effect, effect-size boundary, ceiling assumption, or
> "unacceptable cost" tolerance is taken from any observed v1 result. All such
> values are pilot-set open decisions (`TD-B07`, `TD-B10`, `TD-B15`).
>
> **Distribution selection and the final endpoint specification are PROVISIONAL**
> until the pilot evaluates over/under-dispersion and ceiling/floor effects
> (`TD-B06`).
>
> **The confirmatory construct is NARROW (suite-classification decision D).** E1
> measures **layered dependency-direction conformance** and nothing wider. See §2
> for what E1 does **not** measure and §2.1 for the pinned accounting.

Claims and their constructs are in
[`CLAIMS_CONSTRUCTS_METRICS.csv`](CLAIMS_CONSTRUCTS_METRICS.csv); constructs in
[`RESEARCH_QUESTIONS.md`](RESEARCH_QUESTIONS.md).

---

## 1. Design and unit of analysis

- **Unit of analysis:** one **run** = (task × condition × reset-state × model ×
  repetition), each yielding one patch and its records.
- **Fixed effects:** `condition` (C1–C4) and `reset` (reset / non-reset), plus
  their interaction for RQ2.
- **Decision cluster:** every scored E1 opportunity carries
  `decision_cluster_id` = `source_scope + forbidden_target + leaf_rule`. There are
  **three** such clusters on the canonical substrate and there can be no more
  (§4b; [`DEPENDENCY_TASK_FEASIBILITY.md`](DEPENDENCY_TASK_FEASIBILITY.md)), so
  the cluster factor is **fixed**, not random.
- **Blocking / random effect:** `task` (random intercept, and random slopes where
  estimable). Repetitions are nested within cell. **Whether `task` enters as a
  random intercept or as a fixed block is constrained by §4b** — a variance
  component is estimated only where the realised number of levels identifies it.
- **Model (LLM):** analysed either as an additional **factor** or via a
  **separate generalizability analysis** per model; the final choice is
  provisional (`TD-B06`) and depends on how many models are run (`TD-B03`).
- **Replication count** (repetitions per cell) is a pilot open decision
  (`TD-B10`), set from the pilot's observed dispersion and the target precision —
  **not** from v1. Single-run-per-cell (the v1 defect) is disallowed.

---

## 2. Endpoints (pre-registered)

**The single primary endpoint is the dependency-direction violation rate per
applicable frozen opportunity (E1).** Raw violation counts are retained as a
separate descriptive diagnostic series; **applicable-opportunity satisfaction (E2)
is a descriptive transformation of the same measurement, NOT an independent
confirmatory endpoint** (see
[`CRITICAL_DESIGN_DECISIONS.md`](CRITICAL_DESIGN_DECISIONS.md) D8). The **hidden
acceptance-test pass proportion (E3)** is the **principal (confirmatory)
completeness endpoint**. **Acceptance-criteria coverage (CL08) is a supporting
descriptive measure reported alongside E3 — exploratory, NOT an independent
confirmatory endpoint** (analogous to how E2 supports E1; see
[`CRITICAL_DESIGN_DECISIONS.md`](CRITICAL_DESIGN_DECISIONS.md) D8), so it carries
no separate endpoint ID or confirmatory-family multiplicity slot.

| ID | Endpoint | Role | Construct | Claims |
|----|----------|------|-----------|--------|
| **E1** | **Dependency-direction violation rate per applicable frozen opportunity** (raw counts retained separately) | **PRIMARY** (single) | CON-AC | CL01–CL03 |
| **E2** | Applicable-frozen-opportunity satisfaction proportion | **Descriptive transformation** of E1 (not independent confirmatory) | CON-AC | CL04 |
| **E3** | Hidden acceptance-test pass proportion | **Principal completeness** outcome (confirmatory, secondary to the E1 family) | CON-TC | CL07 |
| **E4** | Condition × reset interaction on the dependency-direction violation rate | Confirmatory (interaction) | CON-RR | CL06 |

> **E1's construct is narrowed (suite-classification decision D).** E1 measures
> **layered dependency-direction conformance only** (rule family
> `AR-DEP-001…006`). **E1 does not directly measure contract ownership,
> port/interface placement, observability completeness, duplicated logic, or
> general business-logic placement.** Those dimensions are pre-registered
> **secondary / manual** evidence under **CON-ACB**
> ([`RESEARCH_QUESTIONS.md`](RESEARCH_QUESTIONS.md)); their confirmatory use
> requires two blinded raters and **Cohen's κ ≥ 0.70** where applicable
> ([`MANUAL_RATING_PROTOCOL.md`](MANUAL_RATING_PROTOCOL.md)), failing which they
> are reported descriptively only. **The paper must not describe E1 as broad or
> general architectural conformance** (gate **G8**).

### 2.1 E1 accounting (pinned; no ambiguity permitted)

E1 is computed **only** from the frozen-opportunity accounting block of the blind
`architecture_finding.json`
([`architecture_finding.schema.json`](../../experiments/v2/schemas/architecture_finding.schema.json)):

| Role in E1 | Field | Source |
|---|---|---|
| **Numerator** | `opportunity_accounting.violated_opportunity_count` | blind architecture finding |
| **Denominator / offset** | `opportunity_accounting.applicable_opportunity_count` | frozen per-task evaluator manifest |

Binding consequences:

- **`applicable_rule_count` must NOT be used as the E1 offset.** It counts rules
  put in force, not exposure, and it moves when a rule is registered rather than
  when the patch has an opportunity to violate one.
- **Stub or unimplemented rules must not increase the E1 denominator.** Only
  frozen dependency-direction opportunities enter `applicable_opportunity_count`;
  `AR-CONTRACT-001`, `AR-OBSERV-001`, `AR-CODE-001` and
  `AR-CHANGE-FOOTPRINT-001` are unimplemented stubs that report `UNIMPLEMENTED`,
  never PASS, and contribute **nothing** to either side of the rate.
- **`raw_violation_count` is a separate descriptive diagnostic series**, reported
  alongside E1 and never substituted into it. It counts every forbidden edge in
  the snapshot, including edges that link to no frozen opportunity.
- **The denominator is never derived from how many files or layers the change
  happened to touch.** It is frozen in the per-task evaluator manifest before any
  run.
- **A task with `applicable_opportunity_count = 0` is structurally ineligible for
  E1 — it is NOT coded as zero violations**, NOT entered with a zero numerator,
  and NOT recorded as a failed run. It is excluded from the E1 model as
  out-of-exposure, exactly as a zero-offset observation must be in a rate model.
- **An E1-ineligible task still contributes** to hidden functional acceptance
  (E3), the engineering-cost measures, and pre-registered exploratory analyses.
  Exclusion from E1 is a statement about architectural exposure, not about the
  task's validity or the run's success.

Per-candidate eligibility is recorded publicly in
[`PILOT_PUBLIC_TASK_MATRIX.csv`](PILOT_PUBLIC_TASK_MATRIX.csv) and
`experiments/v2/tasks/public/TASK_INDEX.csv` (`e1_analysis_eligibility` ∈
{`scored`, `functional-only`, `inactive-reserve`}). Under the current
classification **`PT01`–`PT04` and `PT07` are `scored`**, **`PT05` and `PT06` are
`functional-only`** (primary functional candidates, structurally excluded from
E1), and **`PR01`/`PR02` are `inactive-reserve`** (not activated; they enter no
endpoint). Task counts and the final opportunity count remain **unfrozen**
(`TD-B10`/`TD-B14`/`TD-B20`), and a `scored` eligibility records **intent**: a
candidate enters E1 only once its private evaluator package is authored,
validated, approved and shown to carry a valid non-zero frozen opportunity set
(`TD-B05`/`TD-B14`, gate `G1`).

`PT05`'s move from `scored` to `functional-only` is a **pre-run construct and
feasibility reclassification**: its required functional work creates no currently
scored dependency-direction opportunity. It was decided **before any benchmark or
model execution**, from the task body and the substrate, and is **never** to be
reported as zero violations, a failed run, a missing task, an invalid task or a
refusal. **No reserve was activated** to restore the scored task count.

### 2.2 What an E1 result generalises to (represented decision space)

E1's construct is **layered dependency-direction conformance**, and it is measured
over the **pre-registered task-creatable dependency decisions represented by the
canonical substrate and task suite** — not over the rule family in the abstract.
That represented space is small and, on this substrate, **bounded**: **3 decision
clusters, 2 leaf rules, 2 source scopes, 3 forbidden targets**, which is the
demonstrated task-creatable ceiling, not a sampling choice
([`DEPENDENCY_TASK_FEASIBILITY.md`](DEPENDENCY_TASK_FEASIBILITY.md)).

Binding on reporting:

- **Observed E1 effects generalise directly to the represented
  dependency-decision families, not automatically to all architecture rules or all
  layer pairs.** An effect measured over `features`- and `api`-sourced decisions is
  evidence about those decision families; extending it to `contracts`-, `core`- or
  `infra`-sourced conformance is an **inference beyond the represented space** and
  must be labelled as such.
- **The breadth ceiling is reported as a construct-validity limitation**, with the
  reason (the substrate cannot *create* the remaining decisions under black-box
  functional acceptance) rather than as an omission.
- **This does not broaden E1.** Contract ownership, observability completeness,
  duplicated logic, port/interface placement and general business-logic placement
  remain **CON-ACB** secondary/manual evidence and are still not measured by E1
  (gate **G8**).

### Hypothesis hierarchy (pre-registered order; D9)

No numerical success thresholds are set here (they are `TD-B07`, pilot-set, never
from v1):

1. **C4 vs C1** on the dependency-direction violation rate (E1).
2. **Condition × reset interaction** on the dependency-direction violation rate (E4).
3. **C4 vs C2** (E1).
4. **C4 vs C3** (E1), allowing **superiority, equivalence, or inferiority**
   (D4) — analysed equivalence-aware / two-sided, not as a one-sided superiority
   test. **C3 ≈ C4 is a valid, publishable outcome.**
5. **Hidden acceptance outcomes** (E3).
6. **Cost and footprint outcomes** — secondary / descriptive.

---

## 3. Candidate statistical models

Provisional; final link/family fixed after the pilot dispersion & ceiling checks
(`TD-B06`).

- **Violated-opportunity counts (E1):** **Poisson** mixed model, escalating to
  **negative-binomial** if over-dispersion is present. The response is
  `opportunity_accounting.violated_opportunity_count`; the offset is
  `log(opportunity_accounting.applicable_opportunity_count)`, so the fitted
  quantity is a **rate** rather than a raw count (§2.1). Observations with
  `applicable_opportunity_count = 0` contribute no exposure and are **structurally
  excluded**, never entered as zero violations. `applicable_rule_count` is **not**
  an admissible offset.
- **Acceptance / satisfaction outcomes (E2, E3):** **binomial (logistic) mixed
  model** on the pass/satisfied proportion; if the outcome is saturated
  (ceiling), use an appropriate adjustment (e.g. penalized likelihood / exact /
  Bayesian) rather than reporting a degenerate fit.
- **Time:** **lognormal** (or gamma / other suitable positive-continuous) mixed
  model for execution time.
- **Tokens / iterations:** **negative-binomial** (or another suitable
  count/over-dispersed) mixed model for tokens and verification iterations.
- **Random/fixed structure (all):** `task` as a **blocking** effect (random
  intercept only where the realised level count identifies the variance — §4b);
  **`decision_cluster_id` as a FIXED factor** for E1 and E4, never as a
  random-intercept variance estimated from three clusters (§4b); `condition` and
  `reset` as **fixed effects**; `model` as a **factor** or a **separate
  generalizability analysis**.
- **Reporting (all):** **effect sizes with 95% confidence intervals** (e.g. rate
  ratios, odds ratios, ratios of geometric means), not p-values alone.
- **Multiplicity:** a pre-registered **multiplicity correction** (e.g. Holm or an
  equivalent) applied **within the confirmatory family** (the C4-vs-comparison
  contrasts and the interaction). Exploratory analyses are reported without
  inflating the confirmatory family and are flagged as exploratory.

---

## 4. Contrasts and interaction

- **RQ1 (E1, primary):** marginal contrasts **C4 vs C1**, **C4 vs C2**, **C4 vs
  C3** on the dependency-direction violation rate, fitted over the E1-eligible
  task set only (§2.1), in the hierarchy order of §2. The **C4-vs-C3**
  contrast is **equivalence-aware / two-sided** (D4): equivalence is a valid
  outcome, tested with a pre-registered equivalence procedure (e.g. TOST on the
  rate ratio) alongside the difference test, with the equivalence margin set at
  pilot (`TD-B07`) and **never** from v1. E2 (frozen-opportunity satisfaction) is reported as a
  **descriptive transformation**, not an independent confirmatory contrast.
- **RQ2 (E4):** the **condition × reset** interaction on the dependency-direction
  violation rate; within-condition reset − non-reset simple effects reported as
  supporting detail. The reset **main effect** (CL05) is exploratory. **An
  interaction-focused power simulation is mandatory before the core grid**
  (`TD-B20`; see [`PILOT_AND_POWER_POLICY.md`](PILOT_AND_POWER_POLICY.md)), because
  the interaction is the least-powered confirmatory effect. That simulation must
  **model pseudo-replication**: the frozen opportunities repeat across tasks but
  collapse onto a **small number of shared boundary decisions**, so treating
  opportunities as independent would overstate the effective sample size
  (`TD-B30`). It must **not** be run on the current task set — see §4a.

### 4a. The current architecture task set is NOT confirmatory-ready (`TD-B37`)

Binding on the analysis, recorded **before** any data exists:

- **Repeated task exposures to the same boundary are clustered.** Two tasks that
  each create a decision on the *same* `(source scope, forbidden target)`
  relationship yield **correlated** observations of **one** architectural
  instrument, not two independent architecture measurements.
- **Task count is not the independent architecture-decision count.** The
  confirmatory unit of architectural evidence is the **distinct dependency
  decision**, not the task. Reporting *n tasks* as though it were *n independent
  architecture constructs* is prohibited.
- **The current active set is insufficient.** After `PT05`'s pre-run
  reclassification and the authoring of `PT07`, the E1-scored candidates are
  `PT01`–`PT04` and `PT07`; their adjudicated active opportunities number **5**
  across **3** decision clusters, **two of which carry a single observation**.
  That is not enough replicated dependency decisions to support the confirmatory
  endpoint. **The remedy is replication depth, not further breadth**: the
  substrate's task-creatable ceiling is 3 clusters / 2 leaf rules / 2 source
  scopes / 3 forbidden targets and all three clusters are already represented, so
  additional leaf rules and source scopes are **structurally unavailable here**
  (re-scoped **`DECISION B`**, `TD-B34`;
  [`DEPENDENCY_TASK_FEASIBILITY.md`](DEPENDENCY_TASK_FEASIBILITY.md)).
- **The final power simulation must occur only after** the four `TD-B37`
  preconditions hold: the `TD-B34` re-scope is complete and its authoring outcome
  independently approved; the **replication design is known**; the **G = 3
  analysis method is pre-registered** (§4b, subject to `TD-B41`); and the **final
  E1 denominator structure is known** (`TD-B05`/`TD-B14`, `G1`). Running it on the
  current set would size the study from a clustered, under-dispersed set of
  exposures.
- **A decision/boundary cluster identifier will be required** in the eventual
  analysis artifact, so each opportunity can be attributed to the architectural
  decision it instantiates and the clustering can be modelled explicitly, with the
  matching sensitivity re-fit (`TD-B30`).
- **No final power value is frozen now**, and **no power simulation was run** in
  the package that recorded this section. Minimum detectable effect, power target,
  task count and repetition count all remain unfrozen
  (`TD-B07`/`TD-B10`/`TD-B14`/`TD-B20`).
- **RQ3 completeness (E3):** contrasts as in RQ1; the engineering-cost endpoints
  (tokens/time/iterations/churn/files) are **exploratory** and only **qualify** a
  completeness/conformance result via the pre-registered tolerance (`TD-B15`),
  never establish one.
- **Model:** both candidate models are screened including **C1, C3, and C4**
  (D10); the second model is analysed as a **separate generalizability study**
  unless the model-as-factor plan is confirmed at pilot (`TD-B06`).

### 4b. Analysis with a fixed, very small number of decision clusters (G = 3)

Pre-registered **before any data exists**, because the number of decision clusters
is a property of the substrate rather than of the data: the canonical substrate's
task-creatable ceiling is **three** clusters and all three are represented, so
**G = 3 and cannot grow without a substrate redesign**
([`DEPENDENCY_TASK_FEASIBILITY.md`](DEPENDENCY_TASK_FEASIBILITY.md)). This section
replaces any reading of §3 or §6 under which the shared boundary decision is
modelled as a **random intercept**: with three groups that variance is not
identified in any useful sense, and inference resting on it would be a false
precision.

**Primary specification (pre-registered).**

1. **`decision_cluster_id` enters as a FIXED factor** (3 levels → 2 contrasts).
   **No cluster-level variance component is estimated.** The three clusters are an
   **exhaustively enumerated, pre-registered set** — every task-creatable cluster
   this substrate admits — not a sample from a population of clusters, so a fixed
   representation is what the design actually supports, and the inferential target
   is the effect **within these decision families** (§2.2).
2. **The condition effect remains the inferential target.** `condition`, `reset`
   and their interaction stay fixed effects, and they are **identified within
   clusters**: every scored task is run under every condition and reset state, so
   including the cluster (and the task block) removes between-cluster and
   between-task variation from the contrast instead of relying on it. Blocking a
   within-block treatment contrast on a fixed block is unbiased however small the
   number of blocks.
3. **Opportunities and runs remain nested observations inside the three known
   clusters.** They are **never** entered as independent architecture decisions.
   Several already-authored scored tasks are repeated observations of **one**
   cluster; `decision_cluster_id` is carried on every scored opportunity in the
   analysis artifact so that fact is represented in the model rather than assumed
   away (`TD-B30`).
4. **Repeated structure below the cluster** — `task` and repetitions within a
   (task × condition × reset) cell — is modelled explicitly: `task` as a **block
   nested within cluster**, and within-cell replication through the count family's
   dispersion (negative-binomial where over-dispersed, §3). A `task` **random**
   intercept is used **only** where the realised number of scored tasks identifies
   the variance; otherwise `task` is fixed. That choice is `TD-B41`(1) and is made
   by pre-registered criteria at pilot, **never** by which option gives the larger
   effect.
5. **Cluster heterogeneity is inspected, not assumed away.** A fixed
   `cluster × condition` interaction is fitted as a **heterogeneity check** and
   reported as three cluster-specific estimates alongside the pooled within-cluster
   estimate; the pooled estimate is the confirmatory quantity. Whether the check is
   reportable at the realised cell sizes is `TD-B41`(3).
6. **G = 3 is stated wherever E1 inference is reported.** No E1 result may be
   presented in a way that implies a large number of independent architectural
   clusters, and **task count is never reported as independent
   architecture-decision count**.

**Sensitivity programme (pre-registered).** Each is a re-fit of the primary
specification, reported alongside it and never substituted for it:

- **S1 — small-cluster robust inference.** Cluster-robust variance with the
  **CR2** (or **CR3**) small-sample correction and **Satterthwaite-style degrees of
  freedom**, clustering on `decision_cluster_id`, **conditional on the
  implementation supporting it reliably at G = 3**. Recorded honestly: at three
  clusters the corrected degrees of freedom are themselves small and unstable, so
  S1 is a **bounded sensitivity, never the primary basis of inference**. Exact
  choice and tooling verification are `TD-B41`(2).
- **S2 — within-block randomisation inference.** A permutation / randomisation
  test of the condition contrast that permutes condition assignment **within** each
  (task × reset) block. Its validity rests on the randomised within-task assignment
  rather than on the number of clusters, so it is the sensitivity that stays valid
  when G is small; it is reported whenever S1 is unreliable.
- **S3 — leave-one-cluster-out.** Three refits, each dropping one decision cluster,
  to show no single cluster drives the estimate. With G = 3 this is a complete
  enumeration rather than a resampling approximation.
- **S4 — pseudo-replication check.** The re-fit required by `TD-B30`, now expressed
  as the fixed-cluster specification above versus a specification ignoring
  `decision_cluster_id` entirely, to quantify what treating clustered exposures as
  independent would have done.

**What this section does not do.** It runs **no** model, uses **no** data, and
produces **no** power value. The residual specification that genuinely needs the
runner data shape is filed as **`TD-B41`** with its permitted options enumerated,
and **must be resolved before the `TD-B37` power simulation**. Family and link
selection stay with `TD-B06`; thresholds stay with `TD-B07`.

---

## 5. Degenerate outcomes and missing data (provisional)

- Runs coded `NO_PATCH` / `REFUSAL` / `INVALID_CODE` (see
  [`FAILURE_RERUN_POLICY.md`](FAILURE_RERUN_POLICY.md)) are **valid data**, not
  reruns; their coding into each endpoint (e.g. maximal violation, zero
  satisfaction, failed acceptance) is pre-registered here as provisional
  (`TD-B06`) and applied identically across conditions.
- **Structural E1 ineligibility is not a degenerate outcome and not a failure.** A
  zero-exposure task (`applicable_opportunity_count = 0`) is dropped from the E1
  model because it has no exposure, and its runs are still valid data for E3, the
  cost measures, and exploratory analyses. It must never be coded as
  `NO_PATCH`/`REFUSAL`/`INVALID_CODE`, never counted as zero violations, and never
  counted as a failed run. Reporting must state how many tasks were E1-eligible
  and which were excluded, so no reader mistakes exclusion for a null result.
- **Complete/quasi-complete separation** in a binomial fit (plausible if a
  condition saturates) is handled by a pre-registered fallback (penalized /
  Bayesian), decided at pilot (`TD-B06`).
- Infrastructure-superseded and contaminated runs are excluded per the closed
  exclusion list ([`FAILURE_RERUN_POLICY.md`](FAILURE_RERUN_POLICY.md) §4); a
  **valid model outcome is never excluded for being "bad"**.

---

## 6. Sensitivity analyses

- Poisson vs negative-binomial (and with/without the rate offset) for E1.
- **Pseudo-replication sensitivity for E1 (`TD-B30`):** repeated opportunities
  collapse onto a small number of shared boundary decisions, so the shared decision
  must be represented explicitly and not only through `task`. **It is represented
  as `decision_cluster_id`, a FIXED factor, not as a random effect** — there are
  three clusters and a variance component over three groups is not identified
  (§4b). The sensitivity re-fits are **S1–S4 of §4b**; an earlier version of this
  bullet proposed a cluster **random effect** and is **superseded**.
- **Attribution sensitivity for E1:** re-fit with and without runs whose
  `raw_violation_count` exceeds `violated_opportunity_count`. Under scope-based
  attribution that excess is **expected** — several forbidden edges inside one
  frozen decision collapse to one violated opportunity — so it is no longer a
  defect signature; the sensitivity re-fit is retained to check that runs carrying
  forbidden edges **outside** every frozen decision (dependency-family exposure the
  frozen opportunity set does not cover) do not drive the estimate (`TD-B27`).
- With/without random slopes for `condition` over `task`.
- Exclusion sensitivity: re-fit with and without any `EXCL_PREREGISTERED_RULE`
  drops.
- Per-model refits (generalizability) vs pooled model-as-factor fit.

---

## 7. Thresholds are NOT set here (open decisions)

| Decision | ID | Set when / from |
|----------|----|-----------------|
| Significance level, power target, minimum detectable effect, equivalence margin | `TD-B07` | a-priori + pilot precision — **never** v1 |
| Replication count per cell | `TD-B10` | pilot dispersion + target precision |
| Final distribution/family and endpoint specification | `TD-B06` | pilot dispersion & ceiling/floor checks |
| "Unacceptable cost" tolerance (RQ3) | `TD-B15` | pilot-set, pre-registered |
| Interaction-focused power simulation (condition × reset), mandatory before the core grid | `TD-B20` | Stage-1 pilot dispersion |
| Pseudo-replication model for repeated opportunities collapsing onto shared boundary decisions | `TD-B30` | with the power simulation (`TD-B20`); structure fixed by §4b |
| Residual small-cluster (G = 3) specification: `task`/run repeated structure, CR2-vs-CR3 + Satterthwaite feasibility, cluster × condition reportability | `TD-B41` | pre-registered options in §4b; chosen at pilot, **before** `TD-B20` |
| Final task count / repetitions / total run count (all UNFROZEN) | `TD-B10`/`TD-B14`/`TD-B20` | simulation-determined; never from v1 |
| Final E1-eligible task set (which candidates carry a non-empty frozen opportunity set) | `TD-B05`/`TD-B14` | private re-authoring, gated by G1 |

See [`OPEN_DECISIONS.md`](OPEN_DECISIONS.md).

---

## 8. Analysis discipline

- Endpoints, contrasts, families, and candidate models are fixed **before** data
  collection; any post-hoc analysis is labelled exploratory.
- The plan is executed on the **frozen** result set
  ([`FAILURE_RERUN_POLICY.md`](FAILURE_RERUN_POLICY.md) §7); re-running the
  pipeline on the frozen data reproduces the reported estimates.
- **No claim in [`CLAIMS_CONSTRUCTS_METRICS.csv`](CLAIMS_CONSTRUCTS_METRICS.csv)
  is marked `supported` before data collection**; the final-claim audit is gate
  **G8**.
- **No broad-conformance restatement of E1.** An E1 result is reported as a
  dependency-direction result. Restating it as broad or general architectural
  conformance, or as evidence about contract ownership, port/interface placement,
  observability completeness, duplicated logic or business-logic placement, is
  prohibited and is checked at **G8**.
- **No generalisation beyond the represented decision space.** An E1 result is
  reported as evidence about the **represented** dependency-decision families
  (§2.2); extending it to unrepresented source scopes or layer pairs is an
  explicitly labelled inference, never a finding. The **G = 3** cluster count and
  the substrate's breadth ceiling are stated wherever E1 inference is reported
  (§4b).
- Power and effect-size computations are **not** performed against v1 data and
  are **not** reported as if pre-registered until `TD-B07` is resolved.
