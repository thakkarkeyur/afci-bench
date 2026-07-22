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
   advantage (D3).

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

## What stays unfrozen

**12 tasks, 14 tasks, 480 runs, and 560 runs are all unfrozen.** Final task and
repetition counts require rule-class coverage, pilot ceiling/variance analysis,
and the interaction-focused power simulation. Five repetitions per cell is
**provisional**.
