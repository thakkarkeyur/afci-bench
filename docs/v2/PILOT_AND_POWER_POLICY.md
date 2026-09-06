# docs/v2 — Pilot and Power Policy

Status: **development policy for study v2**. Defines the staged path from
technical dry runs to the confirmatory core grid, and makes an
**interaction-focused power simulation mandatory before the core grid**.
Development artifact only: it does **not** freeze the final benchmark
configuration, authorizes **no** paid model run, and freezes **no** task,
repetition, or run count (all are `TD-B10`/`TD-B13`/`TD-B14`/`TD-B20`; see
[`CRITICAL_DESIGN_DECISIONS.md`](CRITICAL_DESIGN_DECISIONS.md) D13).

Related: [`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md),
[`PILOT_GATE_MATRIX.csv`](PILOT_GATE_MATRIX.csv),
[`MODEL_EXECUTION_CONTROLS.md`](MODEL_EXECUTION_CONTROLS.md) (§7 Q1/Q8),
[`ORACLE_VALIDATION_REQUIREMENTS.md`](ORACLE_VALIDATION_REQUIREMENTS.md).

---

## Stage 0 — Non-evidentiary technical dry runs

Stage 0 produces **no** experimental evidence. It exists to prove the machinery
works before any scored run. It validates:

- **container sterility** — isolated container / dedicated environment, dedicated
  identity, and **managed/organization policy absent** (D11 / `TD-B19`);
- **context audit** — every dry run emits `context_audit.json` and the harness
  fails closed on `CONTAMINATED`;
- **exact model identity** — the resolved model id is read back from headless
  output (`MODEL_EXECUTION_CONTROLS.md` §7 **Q1**);
- **invalid model rejection** — an unrecognized `--model` id is rejected, not
  silently degraded (§7 **Q8**);
- **process reset** — the reset terminates process A and starts a genuinely fresh
  process B (no `--continue`/`--resume`/session reuse), per
  [`RESET_PROTOCOL.md`](RESET_PROTOCOL.md);
- **artifact capture** — the run manifest and all required artifacts
  ([`RUN_ARTIFACT_MATRIX.csv`](RUN_ARTIFACT_MATRIX.csv)) are produced and hash-linked;
- **hidden evaluator isolation** — the coding model sees only `ci:agent`; the
  oracle/acceptance evaluator runs outside its workspace/feedback loop;
- **oracle determinism** — the oracle produces identical results on identical
  inputs (byte-stable), a precondition for validity.

The **Q1/Q8 model-runtime dry runs remain blocking** and are **not performed in
this work package** (no runner exists; no paid/dry run here) — `TD-B21`
(cross-references `TD-B02`).

**Stage 0 is additionally gated on `DECISION B` (`TD-B34`), now re-scoped to
replication depth.** `TD-B34` remains **open and blocking** before Stage 0, but
what it requires has changed and the earlier breadth directive is **withdrawn**.

> <!-- TD-B34-BREADTH-HISTORICAL -->
> **Withdrawn directive.** This gate previously required additional public
> architecture tasks exercising *genuinely different* dependency-direction leaf
> rules and source/target boundaries. That objective is **scientifically obsolete
> and structurally unattainable**: the independent remaining-leaf feasibility
> review established a demonstrated ceiling of **3 decision clusters / 2 leaf rules
> / 2 source scopes / 3 forbidden targets** on the canonical substrate, and **all
> three clusters are already represented**
> ([`DEPENDENCY_TASK_FEASIBILITY.md`](DEPENDENCY_TASK_FEASIBILITY.md) §2–§3). No
> new leaf rule or source scope can be authored here, so Stage 0 must **not** be
> gated on producing one.

What `TD-B34` now requires before Stage 0 is **adequate replication depth and
balance over the complete demonstrated task-creatable decision space**:

- **all three demonstrated clusters stay represented**;
- **the two singleton clusters** — `DC-FEATURES-API-AR-DEP-006` (n = 1) and
  `DC-API-CORE-AR-DEP-005` (n = 1) — receive **independent functional instruments
  where scientifically feasible**, priority **A** then **B**;
  `DC-FEATURES-INFRA-AR-DEP-006` (n = 3) is **not** the immediate priority;
- **no impossible breadth is demanded**: no additional leaf rule, source scope or
  cluster beyond the ceiling is required, and no artificial task may be authored
  merely to hit a mechanically implemented leaf;
- **replicate candidates are not assumed to exist.** It is **not** asserted that a
  suitable replication task exists for either singleton cluster. Each candidate
  requires its **own separate pre-authoring review** against the eleven authoring
  requirements and §8a of
  [`TASK_AUTHORING_POLICY.md`](TASK_AUTHORING_POLICY.md) before it may be written;
  that review has **not** happened;
- the residual breadth ceiling is carried as a **construct-validity limitation** of
  the study, not as a Stage-0 deliverable.

That decision **predates any benchmark or model outcome**, is a **task-set
coverage** deficiency rather than an oracle failure, and is **not** a reason to
activate a reserve.

**One bounded exception, and only one.** `TD-B34` stays **open and blocking**
before Stage 0, before normal Stage 1, before final pilot progression, before
confirmatory execution and before the power simulation where applicable. It does
**not** block the single pre-registered, `PT08`-only, `C1`-only,
**non-confirmatory** difficulty diagnostic authorised by **`SL-PT08-01`**
([`PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md`](PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md)),
which sits outside the staged sequence entirely (next section). The exception
marks priority B neither started nor complete, weakens none of `TD-B34`'s
closure conditions, closes none of its subconditions, counts as no replication
observation, changes no observation depth and creates no additional active
opportunity.

## Pre-Stage-0 instrument diagnostics (outside the staged sequence)

Exactly one such diagnostic is authorised, by **`SL-PT08-01`**: a
pre-registered, **`PT08`-only**, **`C1`-only**, **non-confirmatory** difficulty
diagnostic, permitted **before** `TD-B34` closure. It exists because the
instrument's own baseline difficulty is one of the inputs that should decide
whether further benchmark expansion is worth the investment, and the staged
sequence could not deliver that evidence until after the expansion it was meant
to inform.

- **It is not Stage 0** (Stage 0 scores nothing and proves the machinery), **not
  Stage 1** (the paid `C1`/`C3`/`C4` screening pilot over both candidate models)
  and **not** part of the core grid. Completing it advances **no** stage.
- **It is analytically quarantined.** Its observations must never enter the
  confirmatory dataset, confirmatory `E1` effect estimation, treatment-effect
  analysis or power estimation, and must never be pooled with the later Stage-1
  or core-grid observations.
- **It discharges nothing** — not `TD-B34`, not priority B, not Stage 0, not
  `G1`, and not the global power-analysis gates.
- **For this diagnostic only**, completion of the **global** `TD-B12`/`G6`
  precision-and-recall bar is not required beforehand. That narrow exception
  discharges **neither** `TD-B12` **nor** `G6`, and the global precision/recall
  and blinded double-rating requirements stay mandatory at their existing gate.
- **It is not executable on the strength of this policy.** A real runner,
  runner-time worktree enforcement, a fresh process, a clean context audit,
  governed isolation and identity, Study-Lead model selection with `Q1`/`Q8`
  validation, `PT08` hidden-acceptance authoring, validation and independent
  review, `PT08`'s manifest freeze and the public `PT08-PUB-P2-2`
  synchronization that must precede it are **all still required**.
- **Its sample size is undecided** (Study-Lead decision pending) and **no model
  is selected** (`primary_model` stays null; `TD-B03` open).

The full adjudication, its evidence basis, its data firewall and the complete
list of what it does and does not waive are in
[`PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md`](PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md).

## Stage 1 — Screening pilot (paid; NOT part of this work package)

- **Conditions:** includes **C1, C3, and C4** for **both** candidate models
  (Sonnet and Opus) — so screening reflects the persistent-instruction channel,
  not just floor and AFCI (D10).
- **Reset:** both **reset** and **non-reset**.
- **Repetitions:** **provisional three** per cell (not final; `TD-B10`).
- **Pilot task number:** decided through **rule-class coverage** (every
  architecture rule class exercised), **not** a fixed number here (`TD-B14`).
- **C2** is added **for the selected primary model** only, once its architecture
  content exists to token-match against (`TD-B08`); C2 is not needed to screen
  models.

### Model selection (D10)

Selection criteria: **reliability**, **non-ceiling baseline behaviour** (the C1
baseline must make measurable mistakes), **operational stability**, and **useful
C3 discrimination**. **The model is never selected on the largest favourable AFCI
effect** (`TD-B03`).

## Pilot usage (what the pilot data may and may not be used for)

The pilot informs, in order:

1. **operational reliability** — infra failure rates, contamination rates;
2. **ceiling detection** — is any condition saturated (floor/ceiling)? (guards
   against the v1 saturated-`ci_pass` failure);
3. **dispersion and variance** — over/under-dispersion of the violation-rate
   endpoint, for the distribution family (`TD-B06`);
4. **interaction-focused power simulation** — a simulation targeting the
   **condition × reset interaction** (the least-powered confirmatory effect),
   which **must** be run **before** the core grid to set the final task and
   repetition counts (`TD-B20`, feeding `TD-B10`/`TD-B14`);
5. **baseline-only task-hardening decisions** — difficulty is tuned on **C1
   baseline** behaviour only, **never** on the size of the observed AFCI (C4)
   advantage (D3). The Stage-1 pilot is not the **only** authorised vehicle for
   that baseline-only evidence: the pre-Stage-0 `PT08` `C1` difficulty
   diagnostic (`SL-PT08-01`) is authorised separately, on the same baseline-only
   terms and with the same prohibition on `C4`/effect-based tuning.

**Pilot data must not be pooled into confirmatory results** when **any** relevant
task, oracle, condition, or protocol changed afterward (a changed
`protocol_versions` stamp ⇒ `EXCL_PROTOCOL_MISMATCH`; see
[`FAILURE_RERUN_POLICY.md`](FAILURE_RERUN_POLICY.md) §7).

## Core (confirmatory) grid

- **Task-blocked** design (`task` a random/blocking effect).
- **Condition order randomized / interleaved** to avoid order confounds.
- **Final size is simulation-determined** (from the Stage-1 interaction power
  simulation), never assumed and never taken from v1 (`TD-B20` → `TD-B10`/`TD-B14`).
- The **second model** is analysed as a **separate generalizability study**, not
  pooled as an extra factor unless the SAP's provisional model-as-factor plan is
  confirmed at pilot (`TD-B06`).

## Precondition on the power simulation (`TD-B37`)

The mandatory interaction-focused power simulation **must not be run on the
current architecture task set**, and **no final power value is frozen**:

- **Repeated task exposures to the same source/target boundary are clustered.**
  They are correlated observations of **one** architectural instrument.
- **Task count is not the independent architecture-decision count.** The
  confirmatory unit is the **distinct dependency decision**.
- After `PT05`'s pre-run reclassification to `functional-only` (`TD-B35`) and the
  authoring of `PT07`, the E1-scored candidates are `PT01`–`PT04` and `PT07`, and
  their adjudicated active opportunities number **5** across **3** decision
  clusters, **two of them observed once each**. **The remedy is replication depth,
  not further breadth**: the substrate's task-creatable ceiling is **3 clusters /
  2 leaf rules / 2 source scopes / 3 forbidden targets**, and all three clusters
  are already represented (re-scoped **`DECISION B`**, `TD-B34`;
  [`DEPENDENCY_TASK_FEASIBILITY.md`](DEPENDENCY_TASK_FEASIBILITY.md)).
- The simulation runs **only after all four preconditions hold**: (a) the `TD-B34`
  re-scope is complete and its authoring outcome **independently approved**; (b)
  the **replication design is known** — which clusters gain an independent
  instrument and which remain singletons; (c) the **small-cluster (G = 3) analysis
  method is pre-registered** ([`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md)
  §4b, subject to `TD-B41`); (d) the **final E1 denominator structure is known**
  (`TD-B05`/`TD-B14`, `G1`). It must carry the **decision/boundary cluster
  identifier** so the clustering is modelled rather than assumed away (`TD-B30`;
  §4a), and it must model the cluster factor as **fixed at G = 3**, never as a
  variance component estimated from three groups.

**No power simulation was run** in the package that recorded this section, and
this section freezes no power value.

## What stays unfrozen

**12 tasks, 14 tasks, 480 runs, and 560 runs are all unfrozen.** Final task and
repetition counts require rule-class coverage, pilot ceiling/variance analysis,
and the interaction-focused power simulation. Five repetitions per cell is
**provisional**. **No final power value is frozen** (`TD-B37`), and Stage 0 is
additionally gated on `DECISION B` (`TD-B34`).
