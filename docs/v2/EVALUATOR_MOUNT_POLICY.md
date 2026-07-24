# docs/v2 — Evaluator Mount Policy

Status: **development policy for study v2**. The mechanical rules for **where** the
hidden evaluator (manifest, hidden tests, scoring outputs) is mounted relative to
the coding model's worktree, and the fail-closed behaviour when those rules are
violated. Companion to [`HIDDEN_EVALUATOR_BOUNDARY.md`](HIDDEN_EVALUATOR_BOUNDARY.md).
Development artifact only: it does **not** freeze the final benchmark
configuration and authorizes **no** paid model run.

Blocking decisions: **`TD-B16`** (runner-time CI/evaluator separation),
**`TD-B05`** (hidden per-task answers), **`TD-B12`** (oracle validation).

---

## 1. Definitions

- **Coding worktree** — the repository snapshot the model edits and the only tree
  its `ci:agent` runs against. Denote its absolute, symlink-resolved real path
  `W`.
- **Evaluator mount** — the directory holding the frozen `evaluator_manifest.json`,
  the hidden tests, and (after scoring) the scoring outputs. Denote its absolute,
  symlink-resolved real path `E`.

## 2. Mount rules (mechanical, fail-closed)

1. **`E` must be outside `W`.** `E` must not be `W`, must not be nested inside `W`,
   and no path inside `E` may resolve (through symlinks) back inside `W`.
2. **`W` must be clean.** No file listed in
   [`HIDDEN_EVALUATOR_BOUNDARY.md`](HIDDEN_EVALUATOR_BOUNDARY.md) §1 may exist
   inside `W` at generation time.
3. **Resolve real paths first.** Both `W` and `E` are resolved to real
   (canonical, symlink-free) absolute paths **before** the containment check, so a
   symlink cannot smuggle the mount inside the worktree.
4. **Fail closed.** If rule 1 or 2 is violated, or if `E` (or the manifest inside
   it) is missing or unreadable, the oracle refuses to score and the run is marked
   `INFRA_EVALUATOR_MOUNT` (mount inside worktree / unreadable mount) or
   `SETUP_CONTAMINATED` (forbidden artifact found inside `W`). A refusal is never
   downgraded to a pass.
5. **Read-only during scoring.** The oracle treats `W` as read-only input; it
   writes scoring outputs only under `E` (or a separate results directory), never
   back into `W`.

## 3. Machine-checkable enforcement

Two independent, automated checks enforce this policy in this package:

- **Oracle-engine rejection (TypeScript).** The oracle engine calls
  `assertEvaluatorMountOutsideWorktree(snapshotDir, manifestPath)` before doing any
  work; it throws an `OracleError` with reason `INFRA_EVALUATOR_MOUNT` when the
  manifest resolves to a path inside the snapshot. Proven by the Jest test
  `experiments/v2/oracle/tests/mountPolicy.test.ts` (a manifest placed inside the
  snapshot is rejected; a sibling mount is accepted).
- **Coding-worktree cleanliness (Python).** The harness test
  `experiments/v2/harness/tests/test_evaluator_mount_policy.py` asserts that the
  committed coding-worktree fixture
  (`experiments/v2/oracle/fixtures/coding_worktree/`) contains **none** of the
  forbidden artifact kinds, and that a mount nested inside a worktree path is
  rejected by the shared containment predicate.

The forbidden-name set both checks use is defined in §4.

## 4. Forbidden artifact names inside the coding worktree

The following names/kinds must never appear inside `W` (case-insensitive on the
basename):

- `evaluator_manifest.json`, `*.evaluator.json`
- `oracle_result.json`, `architecture_finding.json`, `acceptance_result.json`,
  `guard_result.json`
- any `hidden/` or `hidden_tests/` directory
- `expected_layers.*`, `prohibited_layers.*`, `required_areas.*`,
  `prohibited_areas.*`
- `legitimate_alternatives.*`, `legitimate_answers.*`

`.gitignore` already keeps evaluator mounts and generated results out of version
control (`.evaluator_mounts/`, `eval_mounts/`, `*.evalmount/`,
`/experiments/v2/results/*`); this policy additionally forbids these names from
appearing **inside a coding worktree** regardless of git tracking.

## 5. Run-manifest recording

For every counted run the manifest records the evaluator mount's identity and
content hashes (`run_manifest.schema.json` `evaluator_mount`:
`manifest_id`, `manifest_version`, `mount_outside_worktree`, `content_hashes`,
`contents_exposed`) **without** exposing the manifest or hidden-test contents.

## 6. Status

Mechanical rules and both automated checks are **delivered and tested** at the
fixture level here. Enforcement in the live runner (`TD-B16`) and the authored
per-task hidden manifests/tests (`TD-B05`) remain **open**; no paid model run is
performed in this package.
