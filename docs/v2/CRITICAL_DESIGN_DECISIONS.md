# docs/v2 — Critical Design Decisions (Binding)

Status: **binding design decisions for study v2**, recorded during the
pre-execution scientific-design reconciliation. These are the **resolved design
questions** that the reconciliation settles; they are distinct from the
**open, data/artifact-dependent blockers** in
[`OPEN_DECISIONS.md`](OPEN_DECISIONS.md) (`TD-B*`/`TD-N*`), which remain open.

> **This document does not freeze the protocol.** It records *how* the study is
> designed to answer its questions honestly. The protocol is a **pre-freeze
> draft** (see [`README.md`](README.md)): scientific freeze occurs only after
> this reconciliation is independently approved **and** the relevant blocking
> decisions are closed. No `protocol-freeze` tag exists. This document
> authorizes **no** paid model run, freezes **no** task/repetition/run count,
> and derives **no** value from v1 results.

Each decision below is binding for the protocol. Where a decision creates or
sharpens a blocker, the `TD-*` id is named and lives in
[`OPEN_DECISIONS.md`](OPEN_DECISIONS.md).

---

## D1 — Use of v1

- v1 remains **immutable and exploratory**. It is referenced only via the
  pointers in [`archive/v1/`](../../archive/v1/README.md); nothing here
  regenerates or edits v1 evidence.
- v1 is **never statistically pooled** with v2. It supplies **no** confirmatory
  variance, power, effect-size, ceiling, or "unacceptable cost" assumption.
- v1 patches **may later be rescored** by the v2 oracle **only** to
  stress-test the oracle implementation (a software-validation exercise), never
  to estimate a v2 effect.
- Any threshold, distribution family, or power input derived from observed v1
  numbers is prohibited (see [`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md) §7).

## D2 — Public task wording

- Public v2 task files contain **functional requirements and observable
  behaviour only**.
- Public tasks **must not** reveal: MAD rules, layer names (used
  prescriptively), dependency directions, contract/port locations, boundary
  rules, "follow the architecture" language, or architecture-specific
  observability/acceptance requirements.
- All architecture criteria live **only** in the **hidden evaluator manifests**
  (rule catalog, acceptance manifest, oracle spec) — never in the public task.
- v1 task **concepts** may be reused; v1 task **wording is not reused**.
- Enforced by the leakage policy: [`TASK_AUTHORING_POLICY.md`](TASK_AUTHORING_POLICY.md),
  [`TASK_LEAKAGE_TERMS.yml`](TASK_LEAKAGE_TERMS.yml), and
  `experiments/v2/tasks/validate_public_tasks.py`. Blocker for the authored
  suite: **`TD-B17`**.

## D3 — Implicit repository architecture

- Coding models **may inspect the actual repository**. Folder names and existing
  code are **not artificially hidden**; the repository's structure is part of
  the realistic setting.
- Tasks must therefore contain **realistic architectural decision points** where
  the locally convenient implementation may conflict with a global rule — so the
  measurement is not trivially won by copying the nearest file.
- **Task hardening uses baseline-only difficulty criteria** (C1 behaviour: does
  the unguided baseline make the mistake often enough to measure?), **never** the
  size of the observed AFCI (C4) advantage. Tuning difficulty toward a larger C4
  effect is prohibited.

## D4 — C3 versus C4

- The study **measures the relationship** between C3 (persistent repository
  instruction) and C4 (explicit governed injection); it does **not assume C4
  wins**.
- **C3 ≈ C4 is a valid, publishable outcome.** Paper viability **must not**
  depend on C4 superiority.
- Under equivalence, the contribution becomes: the **benchmark**, the
  **validated oracle**, the **governance/auditability process**, and an
  **honest equivalence finding** about delivery channel.
- The C4-vs-C3 contrast is therefore two-sided / equivalence-aware, not a
  one-sided superiority test (see [`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md)).

## D5 — C3/C4 content parity

- C3 and C4 receive **byte-identical frozen architecture content** (the same
  approved MAD bytes).
- C4 must contain **no architecture hard rules absent from C3**, and vice versa.
- The **intended, isolated difference** is **delivery**: persistent repository
  instruction (C3) versus explicit governed injection and re-injection (C4).
- Any **unavoidable channel or ordering differences** (framing wrappers, position
  in context, re-injection after reset) are **documented**, not hidden.
- Recorded and hash-verified per [`CONDITION_PARITY_POLICY.md`](CONDITION_PARITY_POLICY.md)
  and [`CONDITION_CONTENT_MATRIX.csv`](CONDITION_CONTENT_MATRIX.csv). Blocker for
  the frozen hashes: **`TD-B18`**.

## D6 — C2 construction

- C2 (token-matched placebo) is **generic and repository-agnostic**: no
  repository names, paths, layers, or dependency directions.
- The exact C2 text is **frozen before pilot outcome collection**.
- C2 is **token-matched to the architecture context** using the **runtime
  tokenizer**, with a **provisional tolerance of ±5%** (final value = `TD-B08`).
- The match concerns the **architecture-context component** delivered under C4,
  not the whole task prompt.

## D7 — Reset

- A **reset** means **interrupting and continuing the same partial
  implementation**; process B is **new**. **No** `--continue`, `--resume`,
  session restoration, or `--from-pr` (enforced by the launch-command guard in
  [`context_audit.py`](../../experiments/v2/harness/context_audit.py)).
- **Checkpoint predicates must be externally detectable and condition-neutral.**
  They **must not** require a canonical layer, a specific file path, or a correct
  architecture — otherwise the checkpoint would advantage the guided conditions.
- **Preferred checkpoint:** task-specific **functional / worktree progress**
  (an observable, condition-neutral state).
- **Fallback checkpoint:** the **first visible validation attempt after at least
  one edit** (e.g. first `npm run ci:agent` invocation after an edit).
- **Equal post-reset budget across conditions.** **Pre-reset consumption** and
  **post-reset allowance** are **logged separately** (run manifest `budget`).
- **Every task intended for reset analysis must have a frozen checkpoint.**
  Refines **`TD-B01`** and **`TD-B11`**.

## D8 — Primary endpoint

- **Primary outcome: the architecture-violation rate per applicable
  rule/opportunity** (CON-AC), analysed as a rate with an exposure offset.
- **Raw violation counts are retained.**
- **Applicable-rule satisfaction is a descriptive transformation** of the same
  measurement — reported for interpretability, **not** an independent
  confirmatory endpoint.
- The **hidden acceptance-test pass proportion** (CON-TC) is the **principal
  completeness outcome**.
- See [`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md) §2 (endpoint
  E1 primary; E2 descriptive).

## D9 — Hypothesis hierarchy

Ordered; **no numerical success thresholds are set** (thresholds/power are
`TD-B07`, pilot-set, never from v1):

1. **C4 vs C1** on the architecture-violation rate.
2. **Condition × reset interaction** on the architecture-violation rate.
3. **C4 vs C2**.
4. **C4 vs C3**, allowing **superiority, equivalence, or inferiority** (D4).
5. **Hidden acceptance outcomes** (completeness).
6. **Cost and footprint outcomes** as secondary/descriptive.

## D10 — Model screening

- **Screen Sonnet and Opus.** **C3 is included in the initial model-screening
  pilot** (so screening reflects the persistent-instruction channel, not just
  C1/C4).
- **Selection criteria:** reliability, **non-ceiling baseline behaviour**,
  operational stability, and **useful C3 discrimination**.
- **The model is never selected on the largest favourable AFCI effect.** Refines
  **`TD-B03`**.

## D11 — Evidentiary environment

- An **isolated container (or equivalent dedicated environment) and a dedicated
  identity are mandatory** for every counted run.
- Every counted run requires a **`context_audit` verdict `CLEAN`**.
- **Managed/organization policy must be absent** (account-tied policy is not
  cleared by a fresh HOME/config dir — see
  [`CONTEXT_ISOLATION_POLICY.md`](CONTEXT_ISOLATION_POLICY.md) §7).
- **Contaminated executions are excluded as environment failures**
  (`EXCL_CONTAMINATED` / `SETUP_CONTAMINATED`), **not** treated as valid model
  outcomes. New blocker: **`TD-B19`** (mandatory container + dedicated identity).

## D12 — Model-runtime dry runs

- **Unresolved runtime questions remain blocking before paid pilot execution.**
- The **resolved model-ID readback** (`MODEL_EXECUTION_CONTROLS.md` §7 **Q1**)
  and **invalid-model-ID rejection** (§7 **Q8**) **must be verified through
  controlled dry runs after the runner exists**.
- **These are not marked complete in this work package** (no runner exists; no
  paid/dry run performed here). New blocker: **`TD-B21`** (cross-references
  `TD-B02`).

## D13 — Study size

- **12 tasks, 14 tasks, 480 runs, and 560 runs are all UNFROZEN.**
- Final task and repetition counts require: **rule-class coverage**, **pilot
  ceiling/variance analysis**, and **power simulation targeting the condition ×
  reset interaction** (`TD-B20`).
- **Five repetitions per cell is provisional, not final** (`TD-B10`).

---

## Relationship to the open-decision registry

| Decision | Effect on registry |
|---|---|
| D1 | reaffirms the no-v1-thresholds rule (`TD-B07`, `TD-B10`, `TD-B15`) |
| D2 | new blocker **`TD-B17`** (public-task leakage validation) |
| D4/D5 | new blocker **`TD-B18`** (byte-identical C3/C4 content parity) |
| D6 | provisional ±5% tolerance; final value `TD-B08` |
| D7 | refines **`TD-B01`**, **`TD-B11`** (condition-neutral checkpoints; separated budget) |
| D8/D9 | single primary endpoint; rule satisfaction descriptive (SAP) |
| D10 | refines **`TD-B03`** (C3 in screening; no effect-maximizing selection) |
| D11 | new blocker **`TD-B19`** (mandatory container + dedicated identity + CLEAN) |
| D12 | new blocker **`TD-B21`** (Q1/Q8 runtime model-ID dry runs) |
| D13 | counts unfrozen (`TD-B10`, `TD-B14`); interaction power sim **`TD-B20`** |
| CI | new blocker **`TD-B16`** (agent-visible CI separation enforced in the live runner) |

None of these blockers is resolved by this work package (each depends on future
tasks, oracle, model dry runs, the runner, the container, or the pilot).
