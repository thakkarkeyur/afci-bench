# experiments/v2/manifests — Run Manifests (v2)

**Manifests** that pin down exactly what each v2 run/batch executed: the task
and condition identities, model and version, environment, git base SHA, seeds/
parameters, and the schema versions in effect.

A manifest is the provenance record for a batch of results — it should be
sufficient, together with the harness and the pinned base, to explain how a
given result set was produced. Manifests are tracked; the bulk run outputs they
describe are not (see `../results/`).

Add run manifests here. Derive base SHAs and identifiers from git/tooling — do
not invent provenance.

---

## `evaluator_manifest.template.json` — analysis eligibility is REQUIRED

The evaluator-manifest template in this directory is the public, answer-free
shape of the frozen per-task manifests that live in the **separate private
evaluator repository**. Following the suite-classification decision (decision D)
it carries a **required** field:

```json
"e1_analysis_eligibility": "scored" | "functional-only" | "inactive-reserve"
```

This binds each manifest to the approved public classification in
[`TASK_INDEX.csv`](../tasks/public/TASK_INDEX.csv) and
[`PILOT_PUBLIC_TASK_MATRIX.csv`](../../../docs/v2/PILOT_PUBLIC_TASK_MATRIX.csv),
so the public classification and what the evaluator actually scores cannot
silently diverge.

### Fail-closed integrity gates (enforced by the engine, not just the schema)

| # | Gate | Fail reason |
|---|---|---|
| 1 | For a real `task_id`, the manifest value must equal the approved public value (and an approved index must be supplied at all) | `ELIGIBILITY_TASK_INDEX_MISMATCH` |
| 2 | A `functional-only` task must contribute **no** E1 opportunity denominator | `ELIGIBILITY_DENOMINATOR_CONFLICT` |
| 3 | An `inactive-reserve` task enters **no** E1 run or aggregation unless a separately recorded pre-run activation decision changes its eligibility | `ELIGIBILITY_RESERVE_INACTIVE` |
| 4 | A `scored` task must have a valid **non-zero** frozen opportunity denominator before it can enter E1 | `ELIGIBILITY_SCORED_WITHOUT_OPPORTUNITIES` |
| 5 | A missing or unrecognised value is an explicit manifest-integrity failure, never a default | `ELIGIBILITY_MISSING` |

An inactive reserve is **not** required to delete its draft opportunities. While
it is inactive nothing about it is scored at all, so those opportunities are
**analytically inactive** by construction; activation is a separate, recorded,
pre-run decision (`reserveActivation`), never an edit to the manifest label.

### Private manifests require migration

> **The per-task manifests in the private evaluator repository were NOT touched by
> this public change and do not yet carry `e1_analysis_eligibility`.** They fail
> closed (`ELIGIBILITY_MISSING`) until migrated, which is deliberate: a
> pre-decision manifest must never be scored under an assumed eligibility.
> Migration is part of the private manifest re-authoring already tracked by
> `TD-B05`/`TD-B14` and must be completed — and the resulting values reconciled
> against the public index — before any manifest is approved or frozen. No private
> manifest was read or written by this package.
