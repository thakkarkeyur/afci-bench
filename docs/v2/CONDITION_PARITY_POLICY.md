# docs/v2 — Condition Parity Policy

Status: **development policy for study v2**. Specifies exactly what is held
identical and what is allowed to differ across conditions, so each contrast
isolates one factor and no contrast is confounded. Development artifact only: it
does **not** freeze the final benchmark configuration, authorizes **no** paid
model run, and creates **no** final content hashes.

Companion table: [`CONDITION_CONTENT_MATRIX.csv`](CONDITION_CONTENT_MATRIX.csv).
Binding decisions: [`CRITICAL_DESIGN_DECISIONS.md`](CRITICAL_DESIGN_DECISIONS.md)
D4 (C3≈C4 valid), D5 (byte-identical C3/C4 content), D6 (C2 construction).
Conditions: [`CONDITIONS.md`](CONDITIONS.md). Blocker for the frozen hashes:
**`TD-B18`** (and `TD-B08` for the C2 token match).

---

## 1. What is held identical across all conditions

- The **functional task source** (byte-identical shared source across C1–C4).
- The **model-execution configuration** within a model (`--model`, `--effort`,
  workflow state, CLI version) — see
  [`MODEL_EXECUTION_CONTROLS.md`](MODEL_EXECUTION_CONTROLS.md) §6.
- The **total budget** and **reset procedure** (see
  [`RESET_PROTOCOL.md`](RESET_PROTOCOL.md)).
- The **evidentiary environment** (isolated container + dedicated identity,
  `context_audit` CLEAN) — D11 / `TD-B19`.
- The **model-visible worktree substrate**. Every condition receives the same
  allowlisted snapshot (`apps/`, `libs/`, build/type-check/test configuration, the
  agent-visible lint config) and **no** explicit architecture material: no
  `ARCHITECTURE_CONTEXT.md`, no `ARCHITECTURE_RULE_CATALOG.yml`, no
  architecture-enforcing `.eslintrc.json`, no `docs/`, `experiments/`, `paper/` or
  `archive/`. The snapshot manifest's `content_hash` makes substrate parity
  mechanically checkable, and the only permitted per-condition difference inside
  the worktree is C3's single approved repository-instruction file. See
  [`MODEL_VISIBLE_WORKTREE_POLICY.md`](MODEL_VISIBLE_WORKTREE_POLICY.md);
  runner-time enforcement is **`TD-B22`** (open).

  Without this, parity was broken at the root: the architecture payload and the
  oracle's rule catalog were repository files inside every condition's worktree,
  so C1 was not a no-architecture arm at all.

## 2. C3 vs C4 — the delivery-channel contrast (D4, D5)

**C3 and C4 receive byte-identical frozen architecture content** (the same MAD
bytes). The **only** intended difference is the **delivery channel**:

- **C3:** the architecture content is delivered as a **persistent
  repository-instruction file** (it stays in place across the reset).
- **C4:** the same content is delivered as **explicit governed prompt
  injection**, and is **re-injected** as primary context after a reset. C4's
  prepared worktree carries **no** persistent instruction file.

The preparation mechanism records `architecture_sha256` for both conditions, so
the byte-identity requirement (`TD-B18`) is checked mechanically: the same payload
hash must appear on C3 and C4 with different `architecture_delivery` values.

Rules:

- **No architecture hard rule may appear in C4 that is absent from C3, or vice
  versa.** Content parity is verified by an **architecture-content hash**
  recorded per condition (`architecture_content_hash` in the matrix), frozen
  before pilot outcome collection (`TD-B18`).
- **C3 ≈ C4 is a valid outcome.** The contrast is analysed as an
  equivalence-aware / two-sided comparison, not a one-sided superiority test
  (see [`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md)). Paper
  viability does not depend on C4 beating C3.
- **Unavoidable channel/ordering differences are documented**, not hidden: the
  governed-injection framing wrapper, the position of the content in context
  (primary vs persistent-file), and the post-reset re-injection are recorded in
  the matrix's `unavoidable_differences` column.

## 3. C2 vs C4 — the content contrast (D6)

C2 holds the **delivery channel** (explicit prompt injection) constant with C4
and varies only the **content**: generic software-engineering guidance with
**no** repository specifics (no names, paths, layers, or dependency directions).

- C2 text is **frozen before pilot outcome collection**.
- C2 is **token-matched to the C4 architecture-context component** using the
  **runtime tokenizer**, provisional tolerance **±5%** (final value `TD-B08`).
- The match concerns the **architecture-context component**, not the whole task
  prompt.
- Recorded as `generic_content_hash` (frozen) in the matrix.

## 4. C1 — the floor

C1 delivers the functional task only: no architecture content, no generic
guidance, empty approved allowlist.

## 5. Per-condition record (matrix columns)

For each condition, [`CONDITION_CONTENT_MATRIX.csv`](CONDITION_CONTENT_MATRIX.csv)
records: the identical **functional task source**, the **architecture-content
hash**, the **generic-content hash**, the **delivery channel**, the **ordering**,
the **persistence**, the **reset behaviour**, the **allowed files**, the
**unavoidable differences**, and the **context-audit checks**.

## 6. Hashes are NOT frozen here

The `architecture_content_hash` and `generic_content_hash` cells are `TODO`
placeholders. They are computed and frozen only when the approved MAD (`TD-B04`)
and the frozen C2 guidance exist, before pilot outcome collection — under
**`TD-B18`** (parity) and `TD-B08` (token match). No final hash is created in
this work package.
