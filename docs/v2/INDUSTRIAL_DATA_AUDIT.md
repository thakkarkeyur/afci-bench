# docs/v2 — Industrial Data Feasibility Audit (RQ4)

Status: **development feasibility audit for study v2**. Determines **whether**
the objective industrial evidence RQ4 needs (CON-IE) can be obtained from FGC's
real records **before** any industrial claim is made. Development artifact only:
it does **not** freeze the final benchmark configuration and authorizes **no**
paid model run.

> **No FGC count, adoption date, sample size, or effect is invented here.** Every
> FGC-specific value is an explicit **unconfirmed** placeholder owned by the
> Industrial Data Owner (open decision `TD-B09`). Until this audit is resolved,
> RQ4's objective claim (CL11) is **ungated** (gate **G7**) and the industrial
> result may only be reported as *infeasible* or *perception-only*, transparently.

Constructs: [`RESEARCH_QUESTIONS.md`](RESEARCH_QUESTIONS.md) (CON-IE). Claims:
CL11 (objective) and CL12 (perception) in
[`CLAIMS_CONSTRUCTS_METRICS.csv`](CLAIMS_CONSTRUCTS_METRICS.csv).

---

## 1. Purpose and gating

RQ4 asks how **objective** review/delivery measures changed after AFCI adoption
at FGC, and how they compare with **practitioner perception**. This audit exists
because an observational before/after claim is only defensible if:

1. the underlying **raw records** are accessible and verifiable;
2. a **pre-registered minimum interpretable sample** is met;
3. **confounders** can be identified and adjusted or acknowledged;
4. **anonymization** protects individuals.

If any of these fails, the objective RQ4 claim is not made. This is gate **G7**
([`PILOT_GATE_MATRIX.csv`](PILOT_GATE_MATRIX.csv)).

**Feasibility work begins in parallel** with the controlled benchmark
(RQ1–RQ3): the availability audit and access negotiation do not block, and are
not blocked by, the controlled study. **No private FGC data is committed to this
repository** at any point — the audit records only element definitions, sources,
and `UNCONFIRMED` placeholders (see §4).

---

## 2. Data-element availability audit

For each element: its definition, a candidate source, its **availability status
(all UNCONFIRMED here — to be filled by the Industrial Data Owner, `TD-B09`)**, a
candidate extraction method, and the main quality/confound risk. No value below
asserts a real FGC figure.

| Element | Definition | Candidate source | Availability | Extraction method | Quality / confound risk |
|---|---|---|---|---|---|
| **AFCI adoption date** | The date AFCI was adopted at FGC (the before/after cutpoint) | FGC change record / rollout log | UNCONFIRMED (`TD-B09`) | Documented rollout date; validate against first-use evidence | A fuzzy or gradual rollout makes a single cutpoint invalid |
| **Pre/post PR availability** | Existence of PRs in comparable windows before and after adoption | Git host (PRs) | UNCONFIRMED (`TD-B09`) | Query PRs by merge date window | Unequal window length / volume between eras |
| **Review rounds** | Number of review iterations per PR | PR review threads | UNCONFIRMED (`TD-B09`) | Count review submissions / re-request cycles | Reviewer-behaviour changes unrelated to AFCI |
| **Architecture-related comments** | Review comments about architecture/layering/boundaries | PR review comments | UNCONFIRMED (`TD-B09`) | Labelled/classified comments (rater + rubric) | Classification subjectivity; needs inter-rater agreement |
| **Time to first approval** | Elapsed time from PR open to first approval | PR timeline | UNCONFIRMED (`TD-B09`) | Timestamp difference | Working hours / timezone / reviewer availability |
| **Time to merge** | Elapsed time from PR open to merge | PR timeline | UNCONFIRMED (`TD-B09`) | Timestamp difference | Release cadence / freeze windows |
| **PR size** | Lines/files changed per PR | Git diff stats | UNCONFIRMED (`TD-B09`) | Diff statistics | Size correlates with task type and era |
| **Author tenure** | Author experience at review time | HR / commit-history proxy | UNCONFIRMED (`TD-B09`) | Tenure at PR date (pseudonymized) | Team composition drift over time |
| **Hotfix / urgency status** | Whether a PR was an urgent hotfix | Labels / branch naming / incident link | UNCONFIRMED (`TD-B09`) | Label/branch heuristic + manual check | Urgent PRs skip normal review (strong confound) |
| **Task type** | Category of change (feature/fix/refactor/etc.) | Labels / conventional-commit type | UNCONFIRMED (`TD-B09`) | Label / commit-type classification | Task-type mix differs pre/post |
| **Confounding changes** | Concurrent process/tooling/team changes near adoption | Change log / interviews | UNCONFIRMED (`TD-B09`) | Timeline of co-occurring changes | Co-adopted tooling can explain effects |
| **Raw-data access** | Whether raw records can be exported and re-verified | Data owner grant | UNCONFIRMED (`TD-B09`) | Access request + export | No access ⇒ claim cannot be verified |
| **Anonymization** | Removal/pseudonymization of personal identifiers | Extraction pipeline | UNCONFIRMED (`TD-B09`) | Pseudonymize authors/reviewers; aggregate reporting | Re-identification risk in small teams |
| **Minimum interpretable sample** | Smallest pre/post sample that yields an interpretable estimate | Pre-registered a-priori | UNCONFIRMED value; **rule pre-registered** (`TD-B09` count; precision target `TD-B07`) | Set from target precision **a-priori**, not from FGC data | Too few PRs ⇒ report as infeasible, not as a null |

---

## 3. Confounding and causal-inference caveats

RQ4 is **observational** before/after; it cannot establish causation. The
analysis must:

- adjust for or stratify by **PR size**, **task type**, **author tenure**, and
  **urgency/hotfix** status where possible;
- acknowledge **secular trends**, **reviewer/team turnover**, **regression to the
  mean**, and **co-adopted tooling** as threats;
- report **effect sizes with 95% CIs**, framed as association, not causation.

The industrial analysis is **exploratory** and reported **separately** from the
controlled benchmark (RQ1–RQ3).

---

## 4. Anonymization and ethics

- **No PII enters git.** (Consistent with the existing practice that survey data
  is kept untracked; no personal data is committed.)
- Authors/reviewers are **pseudonymized**; results are reported in **aggregate**;
  small-cell suppression is applied where re-identification is plausible.
- Perception (survey, CL12) is stored untracked and reported as perception, never
  merged into an objective estimate.

---

## 5. Objective vs perception

Objective measures (CL11) and perception (CL12) are reported **side-by-side**,
never combined. Agreement or divergence between them is itself a finding, but
perception never substitutes for an objective measure, and an objective claim is
made only if this audit clears gate **G7**.

---

## 6. Go / No-Go (gate G7)

- **Go (objective RQ4 reported):** raw records accessible and re-verifiable; the
  pre-registered minimum interpretable sample met; confounders auditable;
  anonymization in place.
- **No-Go:** any of the above fails ⇒ the objective RQ4 claim is **not** made;
  RQ4 is reported as *infeasible* and/or *perception-only*, stated explicitly.

Resolution owner: **Industrial Data Owner (FGC)**; blocking decision `TD-B09`
(see [`OPEN_DECISIONS.md`](OPEN_DECISIONS.md)).

---

## 7. Design choice for RQ4 (ITS vs crossover) — decide before committing

The observational design is **not** pre-committed. Before choosing an
interrupted-time-series (ITS) analysis, the audit must first **determine the AFCI
adoption date, the accessible PR window (pre and post), and the confounders**
(§2–§3). Only then:

- **ITS is used only when its assumptions and a sufficient number of time points
  are defensible** — a clear, non-gradual adoption cutpoint; enough pre- and
  post-adoption periods to estimate level and slope; and confounders that can be
  modelled. A fuzzy/gradual rollout or too few time points ⇒ ITS is **not** used.
- **A counterbalanced crossover handoff study is the PREFERRED causal
  complement.** Where feasible, comparable work is handed off under AFCI vs
  non-AFCI in a counterbalanced order (teams/periods crossed over), giving a
  within-unit contrast that is far less confounded than a single before/after
  cut. It is the preferred way to move RQ4 toward a causal statement.
- **The survey remains perception evidence only** (CL12): reported separately,
  never merged into an objective estimate, never used to establish an objective
  outcome.

All of these choices depend on the availability audit (`TD-B09`) and the
precision target (`TD-B07`); none is frozen here, and no FGC data is committed.
