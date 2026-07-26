# docs/v2 — Experimental Conditions

Status: **development protocol for study v2**. Defines the four experimental
conditions, the context each is and is not allowed, and how each proves
isolation. Development artifact only: it does **not** freeze the final benchmark
configuration and authorizes **no** paid model run.

Companion table: [`CONDITION_MATRIX.csv`](CONDITION_MATRIX.csv). Enforced by the
isolation harness
[`experiments/v2/harness/context_audit.py`](../../experiments/v2/harness/context_audit.py)
(condition allowlists `CONDITIONS["C1".."C4"]`) and the
[`CONTEXT_ISOLATION_POLICY.md`](CONTEXT_ISOLATION_POLICY.md). Constructs measured
across these conditions are defined in
[`RESEARCH_QUESTIONS.md`](RESEARCH_QUESTIONS.md).

The **functional task requirements** ("visible task content") are **identical**
across C1–C4 for a given task; the model-execution configuration (`--model`,
`--effort`, workflow state, CLI version) is **identical** across C1–C4 for a
given model (see [`MODEL_EXECUTION_CONTROLS.md`](MODEL_EXECUTION_CONTROLS.md) §6).
**Only the context — its content and its delivery channel — differs between
conditions.** "MAD" = the approved **Minimum Architecture Document** rule set for
the task.

**The model-visible worktree is identical across C1–C4 and contains no explicit
architecture material.** It is built from an allowlist (source substrate +
build/type-check/test configuration + the agent-visible lint config) by
[`MODEL_VISIBLE_WORKTREE_POLICY.md`](MODEL_VISIBLE_WORKTREE_POLICY.md), which
excludes `docs/` (including `ARCHITECTURE_CONTEXT.md` and
`ARCHITECTURE_RULE_CATALOG.yml`), `experiments/`, `paper/`, `archive/` and the
architecture-enforcing `.eslintrc.json`. Before that mechanism existed the
worktree was the whole repository, so the architecture payload and the oracle's
rule catalog were readable in every condition — including this C1 baseline —
which would have confounded the primary C4-vs-C1 contrast. Runner-time
enforcement is **`TD-B22`** (open); no run may be counted until it is closed.

---

## 1. The four conditions

### C1 — Task only
Functional task requirements only. **No** MAD, **no** architecture instructions,
**no** persistent Claude context. Sterile disk and environment. This is the
no-guidance baseline.

### C2 — Token-matched generic guidance
The same functional task, plus **generic software-engineering guidance** that
contains **no repository-specific architecture information**, injected as prompt
context. Its token count is **matched to C4's MAD injection** for the same task
within a documented tolerance (tolerance value = open decision `TD-B08`). C2 is
the **token-matched placebo** for C4: it isolates the effect of *architecture
content* from the effect of *simply having more guidance tokens*, holding the
delivery channel (prompt) constant with C4.

### C3 — Repository instructions
The approved MAD supplied **only** through the **frozen repository-instruction
mechanism** (a single approved repository-instruction file), with **no** explicit
MAD injection in the task prompt, in a **sterile user and auto-memory
environment**. C3 holds MAD *content* identical to C4 but changes the *delivery
channel* to a persistent repository file.

### C4 — AFCI
The approved MAD supplied **explicitly as the primary context**, with the task
supplied as **secondary context**, and **no persistent repository instruction**.
The approved MAD is **re-injected as explicit context after a reset**
(see [`RESET_PROTOCOL.md`](RESET_PROTOCOL.md)). C4 is AFCI.

---

## 2. What each comparison isolates

| Comparison | Holds constant | Varies | Isolates |
|---|---|---|---|
| **C4 vs C1** | task, model config | all guidance | total AFCI effect vs no guidance |
| **C4 vs C2** | task, model config, delivery channel (prompt), guidance token count (±`TD-B08`) | guidance **content** (architecture MAD vs generic) | that the effect is the *architecture content*, not token volume |
| **C4 vs C3** | task, model config, guidance **content** (**byte-identical** MAD; hash-verified, `TD-B18`) | **delivery channel** (explicit governed injection + re-injection vs persistent repository file) | whether the delivery channel matters, **allowing equivalence** |

C2 pairs with C4 (token-matched placebo); C3 contrasts the delivery channel with
C4 while holding the architecture content **byte-identical**
([`CONDITION_PARITY_POLICY.md`](CONDITION_PARITY_POLICY.md),
[`CONDITION_CONTENT_MATRIX.csv`](CONDITION_CONTENT_MATRIX.csv)). C1 is the floor.

**C3 ≈ C4 is a valid, supported interpretation** — the study measures the C3/C4
relationship and does **not** assume C4 wins; paper viability does not depend on
C4 superiority ([`CRITICAL_DESIGN_DECISIONS.md`](CRITICAL_DESIGN_DECISIONS.md) D4).

---

## 3. Per-condition context specification

For each condition: **visible task content**, **explicit context**, **persistent
context**, **reset context**, **allowed files**, **prohibited files**,
**token-count rule**, **context-audit requirement**, and **contamination failure
behaviour**. Each field is also a column in
[`CONDITION_MATRIX.csv`](CONDITION_MATRIX.csv).

### C1 — Task only
- **Visible task content:** functional task requirements only (the
  acceptance-relevant task statement); no architecture guidance.
- **Explicit context:** none beyond the task statement.
- **Persistent context:** none. Sterile: no `CLAUDE.md`, `CLAUDE.local.md`,
  `.claude/*`, memory, rules, or non-default settings.
- **Reset context:** on reset, re-supply the **same functional task statement
  only** — no MAD, no architecture guidance.
- **Allowed files:** none (empty approved allowlist; the task is delivered via the
  prompt).
- **Prohibited files:** all persistent Claude context — any `CLAUDE.md`,
  `CLAUDE.local.md`, `.claude/*`, auto-memory, MAD file, or generic-guidance file.
  This includes any **repository-resident** architecture document: the prepared
  worktree carries no `ARCHITECTURE_CONTEXT.md`, no
  `ARCHITECTURE_RULE_CATALOG.yml`, and no architecture-enforcing `.eslintrc.json`
  (see [`MODEL_VISIBLE_WORKTREE_POLICY.md`](MODEL_VISIBLE_WORKTREE_POLICY.md)).
- **Token-count rule:** reference zero guidance tokens; **not** token-matched.
- **Context-audit requirement:** `context_audit.json` verdict **CLEAN** with an
  **empty** approved allowlist; `component_status` all `none`; sterile
  environment and a fresh (non-restoring) session.
- **Contamination failure behaviour:** see §4.

### C2 — Token-matched generic guidance
- **Visible task content:** same functional task requirements as all conditions.
- **Explicit context:** generic software-engineering guidance with **no**
  repository-specific architecture information, injected as **prompt** context.
- **Persistent context:** none (sterile; the guidance is prompt-delivered, not
  persisted to disk).
- **Reset context:** re-supply the same functional task statement **and** the same
  generic guidance (still token-matched); no MAD.
- **Allowed files:** none by default (prompt delivery). The harness also supports
  a single **approved generic-guidance file** if a file-delivery variant is ever
  chosen; the frozen protocol uses prompt delivery so C2 and C4 differ only in
  guidance **content**, not channel.
- **Prohibited files:** any repository-architecture instruction (MAD / rules
  file); any unapproved persistent context.
- **Token-count rule:** generic-guidance tokens within **± `TD-B08`** of the C4
  MAD injection for the **same task**; tolerance value is a pilot open decision.
- **Context-audit requirement:** verdict **CLEAN**; approved allowlist empty
  (prompt delivery) or exactly the one approved generic file (hash-matched);
  nothing repository-specific present.
- **Contamination failure behaviour:** see §4.

### C3 — Repository instructions
- **Visible task content:** same functional task requirements as all conditions.
- **Explicit context:** **none** injected in the task prompt (no explicit MAD in
  the prompt).
- **Persistent context:** the approved MAD supplied **only** through the frozen
  repository-instruction mechanism (a single approved repository-instruction
  file), in a sterile user and auto-memory environment.
- **Reset context:** the persistent repository-instruction file **remains in
  place** after reset (the mechanism is persistent by construction); the task
  statement is re-supplied.
- **Allowed files:** exactly **one** approved condition-specific
  repository-instruction file (MAD-bearing), content **hash-matched**.
- **Prohibited files:** any explicit MAD in the prompt; any additional
  `CLAUDE.md` / `.claude/*` / memory / second instruction file.
- **Token-count rule:** MAD content is **byte-identical to C4** (verified by the
  architecture-content hash, `TD-B18`); token count is the MAD's own (recorded),
  **not** adjusted to match another condition. No architecture hard rule may be
  present in C3 that is absent from C4, or vice versa.
- **Context-audit requirement:** verdict **CLEAN** with exactly the one approved
  instruction file (hash-matched); sterile user + auto-memory; nothing else.
- **Contamination failure behaviour:** see §4.

### C4 — AFCI
- **Visible task content:** same functional task requirements as all conditions.
- **Explicit context:** the approved MAD injected as **primary** context; the
  functional task supplied as **secondary** context.
- **Persistent context:** **none** (no persistent repository instruction; sterile
  disk).
- **Reset context:** the approved MAD is **re-injected as explicit context after
  reset**; the task is re-supplied as secondary context.
- **Allowed files:** none (empty approved allowlist; the MAD is prompt-delivered,
  not persisted).
- **Prohibited files:** any persistent MAD / repository-instruction file
  (`CLAUDE.md` / rules); any persistent memory.
- **Token-count rule:** the MAD injection is the **reference** token count that C2
  matches (runtime tokenizer, provisional ±5%, `TD-B08`); its architecture
  content is **byte-identical to C3** (`TD-B18`); recorded per task.
- **Context-audit requirement:** verdict **CLEAN** with an **empty** approved
  allowlist; a persistent MAD / instruction file present ⇒ **CONTAMINATED**
  (enforced by `test_c4_rejects_persistent_mad`).
- **Contamination failure behaviour:** see §4.

---

## 4. Contamination failure behaviour (all conditions)

The context audit is **fail-closed**. If a run's `context_audit.json` verdict is
**CONTAMINATED** — any unapproved/unexpected context source, any tampered
approved artifact, any missing isolation control, any session-restoration flag,
or any managed/remote policy present — then:

1. the run is **aborted** (harness CLI exit code 1) and is **not** a valid run;
2. it is treated as a **setup / infrastructure defect**, so it is
   **rerun-eligible**, and **both** the aborted attempt and its replacement are
   **logged** (see [`FAILURE_RERUN_POLICY.md`](FAILURE_RERUN_POLICY.md));
3. it is **never silently discarded or manually "fixed" in place**;
4. if contamination is detected **after** model output exists, that output is
   **excluded** and used for **no** conformance or completeness claim.

Contamination is distinct from a **valid model outcome** (e.g. an incomplete
implementation or an architecture violation), which must **not** be rerun; see
[`FAILURE_RERUN_POLICY.md`](FAILURE_RERUN_POLICY.md).

---

## 5. CI visibility to the coding model

The coding model works under a condition with exactly one CI surface visible:

- **`npm run ci:agent` is the ONLY CI command visible to the coding model.** It
  runs type checking, visible unit tests, and ordinary non-architecture lint, and
  **excludes** `@nx/enforce-module-boundaries` and all hidden checks.
- **`npm run ci` is repository validation, NOT agent feedback.** It keeps
  architecture enforcement and is run by maintainers / repository CI only; it is
  never part of a run's edit-verify loop.
- **Hidden acceptance tests and hidden architecture-oracle checks never run inside
  the coding model's workspace or feedback loop.** They are evaluated after the
  run by the separated evaluator.

See [`EXPERIMENTAL_CI_POLICY.md`](EXPERIMENTAL_CI_POLICY.md) and
[`ORACLE_VALIDATION_REQUIREMENTS.md`](ORACLE_VALIDATION_REQUIREMENTS.md).

## 6. Open decisions affecting conditions

- `TD-B08` (blocking) — the C2↔C4 token-match tolerance value (provisional ±5%,
  runtime tokenizer), set from the measured C4 architecture-content token count.
- `TD-B04` (blocking) — the approved MAD / architecture-rule catalog that C3 and
  C4 deliver (content), authored during pilot task design.
- `TD-B18` (blocking) — the **byte-identical C3/C4 architecture-content parity**
  hashes, frozen before pilot outcome collection
  ([`CONDITION_PARITY_POLICY.md`](CONDITION_PARITY_POLICY.md)).
- `TD-B16` (blocking) — runner-time enforcement that `ci:agent` is the only CI the
  model sees ([`EXPERIMENTAL_CI_POLICY.md`](EXPERIMENTAL_CI_POLICY.md)).

See [`OPEN_DECISIONS.md`](OPEN_DECISIONS.md) for the full registry.
