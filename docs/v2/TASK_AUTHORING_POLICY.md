# docs/v2 — Public Task Authoring & Leakage Policy

Status: **development policy for study v2**. Governs how **public** v2 task files
are written so that the hidden architecture never leaks into the task the coding
model sees. Development artifact only: it does **not** freeze the final
benchmark configuration, authorizes **no** paid model run, and freezes **no**
task count (see [`CRITICAL_DESIGN_DECISIONS.md`](CRITICAL_DESIGN_DECISIONS.md)
D13).

Binding decisions: [`CRITICAL_DESIGN_DECISIONS.md`](CRITICAL_DESIGN_DECISIONS.md)
D2 (public task wording), D3 (implicit repository architecture). Enforced by
[`TASK_LEAKAGE_TERMS.yml`](TASK_LEAKAGE_TERMS.yml) +
`experiments/v2/tasks/validate_public_tasks.py` +
`experiments/v2/tasks/tests/test_public_task_leakage.py`. Blocker for the
authored suite: **`TD-B17`**.

---

## 1. The separation

Every v2 task has **two** parts:

| Part | Location | Visible to model? | Contains architecture? |
|---|---|---|---|
| **Public task** | `experiments/v2/tasks/<id>.md` | **Yes** | **Never** |
| **Hidden evaluator manifest** | hidden oracle/acceptance/rule spec (`TD-B04`/`TD-B05`) | **No** | **Yes** (rules, layer expectations, acceptance) |

The public task states **functional requirements and observable behaviour
only**. All architecture criteria — MAD rules, layer placement, dependency
directions, contract/port locations, boundary rules, architecture-specific
acceptance — live **only** in the hidden manifest.

## 2. What a public task MUST NOT contain (fail closed)

The validator's **hard-leak** tier rejects, and no exception can permit:

- MAD references ("MAD", "minimum architecture document");
- boundary instructions (module/layer boundaries, "enforce-module-boundaries",
  boundary/layering rules, "cross-layer");
- layer names used **prescriptively** ("put X in the core layer");
- contract/port **placement** instructions ("the port must live in …");
- dependency directions ("must not import", "may only depend", "dependency
  direction", "point inward");
- "follow the architecture" / "respect the architecture" language;
- "existing architecture pattern" language;
- architecture-specific acceptance criteria ("must not violate the layering",
  "no boundary violation").

## 3. Ambiguous terms → review, not blanket rejection

Some words (`layer`, `contract`, `port`, `module`, `architecture`, `boundary`,
`dependency`) appear in perfectly ordinary functional writing (a "caching
layer", a "network port", a "service contract" in the business sense). Blanket
rejection would be wrong. The validator's **review-required** tier flags these
for human review. A flagged occurrence passes **only** if the task carries a
matching **reviewed exception**.

### Exception format (task front-matter)

```markdown
---
leakage_exceptions:
  - id: RR-LAYER
    match: "caching layer"          # optional: scope the exception to this text
    justification: "Functional in-memory caching layer, not a repository layer."
    reviewer: "oracle-designer"
---
# Task: …
```

An exception is valid **only** if it targets a review-required id (never a
hard-leak id), and has a **non-empty `justification`** and **`reviewer`**. A
malformed or unjustified exception **fails closed** — the underlying finding is
treated as un-reviewed leakage.

## 4. Implicit repository architecture (D3)

The coding model **may inspect the actual repository**; folder names and existing
code are not hidden. Therefore a good public task deliberately includes a
**realistic architectural decision point** where the locally convenient
implementation could conflict with a global rule — without ever *naming* the
rule. The task reads as a normal engineering request; the architectural tension
is real but implicit.

**Task hardening uses baseline-only difficulty criteria** (does the unguided C1
baseline make the mistake often enough to measure?), **never** the size of the
observed C4 advantage.

## 5. v1 reuse boundary

v1 task **concepts** may be reused; v1 task **wording is not reused** (D2). The
validator **never** scans or modifies v1/v0 material (`archive/`,
`experiments/tasks_v0/`); it refuses any such path and, by default, scans only
`experiments/v2/tasks/*.md` (excluding `README.md`).

## 6. Authoring checklist

1. Write the functional requirement and the observable behaviour only.
2. Put every architecture rule/acceptance in the hidden manifest (`TD-B04`/`TD-B05`).
3. Run `python experiments/v2/tasks/validate_public_tasks.py` — it must report
   `OK` for every public task.
4. For any review-required flag that is genuinely functional, add a justified,
   reviewed exception; otherwise rewrite the sentence.
5. Never tune wording or difficulty toward a larger C4 effect (D3).

Today there are **no** public v2 task files yet (only the tasks `README.md`); the
validator correctly reports "none authored yet". The authored suite is gated by
**`TD-B17`** and does not exist in this work package.
