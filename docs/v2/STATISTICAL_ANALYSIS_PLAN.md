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

Claims and their constructs are in
[`CLAIMS_CONSTRUCTS_METRICS.csv`](CLAIMS_CONSTRUCTS_METRICS.csv); constructs in
[`RESEARCH_QUESTIONS.md`](RESEARCH_QUESTIONS.md).

---

## 1. Design and unit of analysis

- **Unit of analysis:** one **run** = (task × condition × reset-state × model ×
  repetition), each yielding one patch and its records.
- **Fixed effects:** `condition` (C1–C4) and `reset` (reset / non-reset), plus
  their interaction for RQ2.
- **Blocking / random effect:** `task` (random intercept, and random slopes where
  estimable). Repetitions are nested within cell.
- **Model (LLM):** analysed either as an additional **factor** or via a
  **separate generalizability analysis** per model; the final choice is
  provisional (`TD-B06`) and depends on how many models are run (`TD-B03`).
- **Replication count** (repetitions per cell) is a pilot open decision
  (`TD-B10`), set from the pilot's observed dispersion and the target precision —
  **not** from v1. Single-run-per-cell (the v1 defect) is disallowed.

---

## 2. Endpoints (pre-registered)

**The single primary endpoint is the architecture-violation rate per applicable
rule/opportunity (E1).** Raw violation counts are retained; **applicable-rule
satisfaction (E2) is a descriptive transformation of the same measurement, NOT an
independent confirmatory endpoint** (see
[`CRITICAL_DESIGN_DECISIONS.md`](CRITICAL_DESIGN_DECISIONS.md) D8). The **hidden
acceptance-test pass proportion (E3)** is the **principal completeness outcome**.

| ID | Endpoint | Role | Construct | Claims |
|----|----------|------|-----------|--------|
| **E1** | **Architecture-violation rate per applicable rule/opportunity** (raw counts retained) | **PRIMARY** (single) | CON-AC | CL01–CL03 |
| **E2** | Applicable-rule satisfaction proportion | **Descriptive transformation** of E1 (not independent confirmatory) | CON-AC | CL04 |
| **E3** | Hidden acceptance-test pass proportion | **Principal completeness** outcome (confirmatory, secondary to the E1 family) | CON-TC | CL07 |
| **E4** | Condition × reset interaction on the violation rate | Confirmatory (interaction) | CON-RR | CL05, CL06 |

### Hypothesis hierarchy (pre-registered order; D9)

No numerical success thresholds are set here (they are `TD-B07`, pilot-set, never
from v1):

1. **C4 vs C1** on the architecture-violation rate (E1).
2. **Condition × reset interaction** on the violation rate (E4).
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

- **Violation counts (E1):** **Poisson** mixed model, escalating to
  **negative-binomial** if over-dispersion is present; offset by the number of
  applicable rules (or exposure) to model a **rate** rather than a raw count.
- **Acceptance / satisfaction outcomes (E2, E3):** **binomial (logistic) mixed
  model** on the pass/satisfied proportion; if the outcome is saturated
  (ceiling), use an appropriate adjustment (e.g. penalized likelihood / exact /
  Bayesian) rather than reporting a degenerate fit.
- **Time:** **lognormal** (or gamma / other suitable positive-continuous) mixed
  model for execution time.
- **Tokens / iterations:** **negative-binomial** (or another suitable
  count/over-dispersed) mixed model for tokens and verification iterations.
- **Random/fixed structure (all):** `task` as a **blocking / random effect**;
  `condition` and `reset` as **fixed effects**; `model` as a **factor** or a
  **separate generalizability analysis**.
- **Reporting (all):** **effect sizes with 95% confidence intervals** (e.g. rate
  ratios, odds ratios, ratios of geometric means), not p-values alone.
- **Multiplicity:** a pre-registered **multiplicity correction** (e.g. Holm or an
  equivalent) applied **within the confirmatory family** (the C4-vs-comparison
  contrasts and the interaction). Exploratory analyses are reported without
  inflating the confirmatory family and are flagged as exploratory.

---

## 4. Contrasts and interaction

- **RQ1 (E1, primary):** marginal contrasts **C4 vs C1**, **C4 vs C2**, **C4 vs
  C3** on the violation rate, in the hierarchy order of §2. The **C4-vs-C3**
  contrast is **equivalence-aware / two-sided** (D4): equivalence is a valid
  outcome, tested with a pre-registered equivalence procedure (e.g. TOST on the
  rate ratio) alongside the difference test, with the equivalence margin set at
  pilot (`TD-B07`) and **never** from v1. E2 (rule satisfaction) is reported as a
  **descriptive transformation**, not an independent confirmatory contrast.
- **RQ2 (E4):** the **condition × reset** interaction on the violation rate;
  within-condition reset − non-reset simple effects reported as supporting
  detail. The reset **main effect** (CL05) is exploratory. **An
  interaction-focused power simulation is mandatory before the core grid**
  (`TD-B20`; see [`PILOT_AND_POWER_POLICY.md`](PILOT_AND_POWER_POLICY.md)), because
  the interaction is the least-powered confirmatory effect.
- **RQ3 completeness (E3):** contrasts as in RQ1; the engineering-cost endpoints
  (tokens/time/iterations/churn/files) are **exploratory** and only **qualify** a
  completeness/conformance result via the pre-registered tolerance (`TD-B15`),
  never establish one.
- **Model:** both candidate models are screened including **C1, C3, and C4**
  (D10); the second model is analysed as a **separate generalizability study**
  unless the model-as-factor plan is confirmed at pilot (`TD-B06`).

---

## 5. Degenerate outcomes and missing data (provisional)

- Runs coded `NO_PATCH` / `REFUSAL` / `INVALID_CODE` (see
  [`FAILURE_RERUN_POLICY.md`](FAILURE_RERUN_POLICY.md)) are **valid data**, not
  reruns; their coding into each endpoint (e.g. maximal violation, zero
  satisfaction, failed acceptance) is pre-registered here as provisional
  (`TD-B06`) and applied identically across conditions.
- **Complete/quasi-complete separation** in a binomial fit (plausible if a
  condition saturates) is handled by a pre-registered fallback (penalized /
  Bayesian), decided at pilot (`TD-B06`).
- Infrastructure-superseded and contaminated runs are excluded per the closed
  exclusion list ([`FAILURE_RERUN_POLICY.md`](FAILURE_RERUN_POLICY.md) §4); a
  **valid model outcome is never excluded for being "bad"**.

---

## 6. Sensitivity analyses

- Poisson vs negative-binomial (and with/without the rate offset) for E1.
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
| Final task count / repetitions / total run count (all UNFROZEN) | `TD-B10`/`TD-B14`/`TD-B20` | simulation-determined; never from v1 |

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
- Power and effect-size computations are **not** performed against v1 data and
  are **not** reported as if pre-registered until `TD-B07` is resolved.
