# docs/v2 — Public Task Authoring & Leakage Policy

Status: **development policy for study v2**. Governs how **public** v2 task files
are written so that no hidden design detail — architecture, hidden acceptance,
reset predicates, evaluator machinery — leaks into the task the coding model
sees. Development artifact only: it does **not** freeze the final benchmark
configuration, authorizes **no** paid model run, and freezes **no** task count
(see [`CRITICAL_DESIGN_DECISIONS.md`](CRITICAL_DESIGN_DECISIONS.md) D13).

Binding decisions: [`CRITICAL_DESIGN_DECISIONS.md`](CRITICAL_DESIGN_DECISIONS.md)
D2 (public task wording), D3 (implicit repository architecture). Enforced by
[`TASK_LEAKAGE_TERMS.yml`](TASK_LEAKAGE_TERMS.yml) +
`experiments/v2/tasks/validate_public_tasks.py` +
`experiments/v2/tasks/tests/test_public_task_leakage.py` +
`experiments/v2/harness/tests/test_public_task_integrity.py`. Blocker for the
authored suite: **`TD-B17`**.

---

## 1. The separation

Every v2 task has **two** parts:

| Part | Location | Visible to model? | Contains hidden design? |
|---|---|---|---|
| **Public task** | `experiments/v2/tasks/public/<id>.md` | **Yes** | **Never** |
| **Hidden evaluator package** | separate private evaluator repository (`TD-B04`/`TD-B05`) | **No** | **Yes** (rules, layer expectations, hidden acceptance, reset predicates, legitimate alternatives) |

The public task states **functional requirements and observable behaviour
only**. All architecture criteria — MAD rules, layer placement, dependency
directions, contract/port locations, boundary rules, architecture-specific
acceptance — and all evaluation machinery live **only** in the private evaluator
package.

## 2. Where public tasks live, and what counts as one

- Public task bodies live under **`experiments/v2/tasks/public/`**.
- **`TASK_INDEX.csv`** (in that directory) is the authoritative definition of the
  expected task set. A task file that is not indexed, and an indexed task with no
  file, are both failures.
- Discovery is **recursive** over `experiments/v2/tasks/`, so a task body nested
  in a subdirectory cannot escape scanning.
- The only supported task-body extension is **`.md`**. A task-like file (stem
  `PT01`, `PR02`, `T07`, …) with any other extension is **rejected**, never
  silently skipped.
- `README.md` and `TASK_AUTHORING_REPORT.md` are documented **non-task** files.
  The authoring report is a public handoff document, not a benchmark task, and is
  never counted as one.
- Eight **draft candidates** currently exist: six primary (`PT01`–`PT06`) and two
  reserve (`PR01`–`PR02`). They are **candidates**: authored, **not approved and
  not frozen**.

## 3. What is scanned

Validation covers **both** the task body and its front matter:

- **Front matter** — every string value and mapping key, at any nesting depth, in
  any list or mapping. YAML metadata is **not** safe merely because it is
  metadata: a leaky `title`, `notes`, or nested `hint` is leakage. Only the
  `leakage_exceptions` subtree is excluded, because a justification must be able
  to quote the term it excepts.
- **Body physical lines** — for precise line numbers.
- **Body logical text** — hard-wrapped prose joined within a paragraph or list
  item, so a phrase split across adjacent lines (`must not` / `import …`) is
  still detected. Headings, blank lines, list-item starts, table rows and fenced
  code blocks are unit boundaries, so unrelated paragraphs are never glued
  together and the normaliser cannot invent a phrase nobody wrote.

## 4. What a public task MUST NOT contain (fail closed)

The validator's **hard-leak** tier rejects, and no exception can permit, any of
these families (pattern ids in [`TASK_LEAKAGE_TERMS.yml`](TASK_LEAKAGE_TERMS.yml)):

| Family | Examples |
|---|---|
| MAD references | "MAD", "minimum architecture document" |
| Boundary instructions | module/layer boundaries, "enforce-module-boundaries", "cross-layer" |
| Follow-the-architecture language | "follow the architecture", "match the repository architecture" |
| Dependency directions | "must not import", "may only depend", "point inward" |
| Prescriptive layer names | "put X in the core layer" |
| Contract/port placement | "the port must live in …" |
| Architecture-specific acceptance | "must not violate the layering", "no boundary violation" |
| Prescribed repository paths | `libs/core/src/…`, `apps/api/…`, `docs/v2/…`, `@afci-bench/…` |
| Source filenames as instructions | "wire it in `app.ts`", "export it from `index.ts`" |
| Required/prohibited placement | "required areas", "must be placed under …" |
| Hidden-test / withheld-grading clues | "the withheld grading suite asserts …", "the graders check …" |
| Reset / checkpoint / restart clues | "checkpoint CK-…", "your session is restarted", `--continue` |
| Condition names | `C1`, `C2`, `C3`, `C4`, "token-matched", "placebo", "AFCI" |
| Opportunity and rule ids | `OPP-…`, `AR-…`, "fixed opportunity set", "rule id" |
| Evaluator / oracle clues | "oracle", "evaluator", `oracle_result.json`, "scored" |
| Expected implementation | "the expected implementation adds …", "reference solution" |
| Legitimate-alternative disclosures | "a legitimate alternative is …" |

## 5. Ambiguous terms → review, not blanket rejection

Some words (`layer`, `contract`, `port`, `module`, `architecture`, `boundary`,
`dependency`, `repository`, `use case`, `adapter`, and configuration filenames)
appear in perfectly ordinary functional writing (a "caching layer", a "network
port", a "service contract" in the business sense). Blanket rejection would be
wrong. The validator's **review-required** tier flags these for human review. A
flagged occurrence passes **only** if the task carries a matching **approved,
reviewed exception**.

### Exception format (task front matter)

```markdown
---
leakage_exceptions:
  - id: RR-LAYER                  # the review-required pattern id / category
    location: "body:14"           # exact location: body:<line> or front-matter:<key>
    match: "caching layer"        # optional: scope the exception to this text
    justification: "Functional in-memory caching layer, not a repository layer."
    reviewer: "oracle-designer"
    approved: true                # approval state
---
```

An exception is valid **only** if it targets a review-required id (never a
hard-leak id) **and** carries a non-empty `location`, a non-empty
`justification`, a non-empty `reviewer`, and an affirmative `approved`. A
malformed, unapproved, or mislocated exception **fails closed** — the underlying
finding is treated as un-reviewed leakage. An exception covers only the finding
at its stated location; it never blanket-covers a pattern across the file.

## 6. What a clean validator run does and does not mean

A `[OK]` result means **no detected leakage** by the current term set. It is
**not**:

- proof that the task is scientifically valid;
- proof that the task is well specified, unambiguous, or feasible against the
  frozen base substrate;
- proof that no undetected leakage family exists;
- a substitute for the independent freeze review that closes `TD-B17`.

Functional completeness, ambiguity, wire-format determinacy and base-SHA
feasibility are reviewed **separately** and are recorded in
[`../../experiments/v2/tasks/public/TASK_AUTHORING_REPORT.md`](../../experiments/v2/tasks/public/TASK_AUTHORING_REPORT.md).

## 7. Implicit repository architecture (D3)

The coding model **may inspect the actual repository substrate** it is given;
folder names and existing code are not hidden. Which files the model's worktree
contains is governed by
[`MODEL_VISIBLE_WORKTREE_POLICY.md`](MODEL_VISIBLE_WORKTREE_POLICY.md): the
source substrate (`apps/`, `libs/`, build/test configuration) is present so the
implicit architectural tension is real, while every explicit architecture
document, protocol document, oracle implementation and evaluator artifact is
excluded.

Therefore a good public task deliberately includes a **realistic architectural
decision point** where the locally convenient implementation could conflict with
a global rule — without ever *naming* the rule. The task reads as a normal
engineering request; the architectural tension is real but implicit.

**Task hardening uses baseline-only difficulty criteria** (does the unguided C1
baseline make the mistake often enough to measure?), **never** the size of the
observed C4 advantage.

## 8. Wire-format determinacy (fairness)

A public task must leave **no response key, request key, status code, or asserted
error value** to evaluator guesswork:

- every JSON request body the caller sends is stated with its exact keys;
- every JSON response body is stated with its exact keys;
- every status code is stated;
- where an `error` value is pinned, the task states the exact string; where it is
  **not** pinned, the task says so explicitly, and the private evaluator package
  may then assert only the HTTP status, a non-empty `error`, and a non-empty
  `message`;
- where result ordering is not required, the task says so, and validation must be
  order-independent.

A private hidden test may **never** enforce a string, key, or ordering the public
task did not state.

## 9. v1 reuse boundary

v1 task **concepts** may be reused; v1 task **wording is not reused** (D2). The
validator **never** scans or modifies v1/v0 material (`archive/`,
`experiments/tasks_v0/`); it refuses any such path.

## 10. Private evaluator re-linking (hash coupling)

Each public task's SHA-256 is recorded in `TASK_INDEX.csv` and
[`PILOT_PUBLIC_TASK_MATRIX.csv`](PILOT_PUBLIC_TASK_MATRIX.csv), and is checked
mechanically by `test_public_task_integrity.py`.

**Whenever a public task body changes, its hash changes, and every private
evaluator package pinned to the old hash becomes stale.** A stale private package
must be **re-linked and re-reviewed** before it may be frozen or used; a private
manifest hash must **never** be silently accepted against a changed public task.
See the staleness record in
[`../../experiments/v2/tasks/public/TASK_AUTHORING_REPORT.md`](../../experiments/v2/tasks/public/TASK_AUTHORING_REPORT.md).

## 11. Authoring checklist

1. Write the functional requirement and the observable behaviour only.
2. State every request key, response key, status code and pinned error value
   (§8); say explicitly where a value is not pinned.
3. Verify the task is feasible **against the frozen base substrate** — the
   endpoints, fields and failure paths it refers to must actually exist there, or
   the task must create them.
4. Put every architecture rule and hidden acceptance criterion in the private
   evaluator package (`TD-B04`/`TD-B05`).
5. Run `python experiments/v2/tasks/validate_public_tasks.py` — it must report
   `OK` for every public task and no structural failure.
6. For any review-required flag that is genuinely functional, add an approved,
   located, justified exception; otherwise rewrite the sentence.
7. Update `TASK_INDEX.csv`, `PILOT_PUBLIC_TASK_MATRIX.csv` and the authoring
   report, then run `test_public_task_integrity.py` so the recorded hashes match.
8. Record that the affected private evaluator packages are now stale (§10).
9. Never tune wording or difficulty toward a larger C4 effect (D3).
