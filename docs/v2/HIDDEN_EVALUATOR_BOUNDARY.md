# docs/v2 — Hidden Evaluator Boundary

Status: **development policy for study v2**. Defines the boundary between what the
coding model may see (its worktree and the single agent-visible CI) and the hidden
evaluator (the architecture-conformance oracle, the acceptance oracle, and their
task-specific manifests and hidden tests). Development artifact only: it does
**not** freeze the final benchmark configuration and authorizes **no** paid model
run.

Related: [`EVALUATOR_MOUNT_POLICY.md`](EVALUATOR_MOUNT_POLICY.md) (the mechanical
mount rules and the machine-checkable test), [`EXPERIMENTAL_CI_POLICY.md`](EXPERIMENTAL_CI_POLICY.md)
(the `ci:agent`-only surface, `TD-B16`), [`CONTEXT_ISOLATION_POLICY.md`](CONTEXT_ISOLATION_POLICY.md)
(sterile context, `TD-B19`), [`ORACLE_VALIDATION_REQUIREMENTS.md`](ORACLE_VALIDATION_REQUIREMENTS.md)
(section 3, blindness and separation). Blocking decisions: **`TD-B05`** (hidden
answers per task), **`TD-B16`** (runner-time CI separation), **`TD-B12`**
(oracle validation).

---

## 1. What the coding model's worktree must NOT contain

While the coding model is generating a change, its worktree (the repository
snapshot it edits and the only tree its CI runs against) must **not** contain any
of the following:

- task-specific evaluator manifests (the frozen `evaluator_manifest.json` for the
  task);
- hidden acceptance tests (the withheld behavioural suite);
- expected layers / required areas for the task;
- prohibited layers / prohibited areas for the task;
- legitimate-answer lists (the accepted legitimate-alternative solution shapes);
- architecture scoring outputs (`oracle_result.json`, `architecture_finding.json`,
  `acceptance_result.json`, `guard_result.json`) from this or any prior run.

If any such artifact is detected inside the coding worktree, the run is invalid:
the harness records `SETUP_CONTAMINATED` (setup-time) or `INFRA_EVALUATOR_MOUNT`
(a mount placed inside the worktree) and the run is not scored.

## 2. What the public repository MAY contain

The public repository (which the model may see) may contain, because none of it
reveals a task-specific answer:

- evaluator **schemas** (`experiments/v2/schemas/*.schema.json`);
- generic **engine code** (the oracle framework and the dependency-direction
  reference checker under `experiments/v2/oracle/`);
- **synthetic fixtures** (the oracle's own validation cases, which contain no
  benchmark task and no task-specific answer);
- **documentation** (this file, the rule catalog, the manual rubric, policies);
- **empty templates** without task answers.

The distinction is answer-bearing content, not architecture content: the
canonical architecture context ([`ARCHITECTURE_CONTEXT.md`](ARCHITECTURE_CONTEXT.md))
is deliberately deliverable to the model; the task-specific manifest and hidden
tests are not.

## 3. Where task-specific hidden material must reside

Task-specific hidden manifests and hidden tests must reside either:

- in a **separate private evaluator repository**, or
- in a **separately mounted evaluator directory outside the coding worktree**
  (a sibling/parent path the model process cannot read).

The oracle reads its manifest and hidden tests from that external location. The
mechanical rules and the rejection test are in
[`EVALUATOR_MOUNT_POLICY.md`](EVALUATOR_MOUNT_POLICY.md).

## 4. The evaluator runs only after generation ends

The oracle and acceptance evaluator run **only after** the model's generation
phase has fully ended (the patch is finalized against the frozen base SHA). They
never run inside the generation loop.

## 5. No hidden evaluator output is fed back to the coding model

No hidden evaluator output — no finding, verdict, score, hidden-test result, or
manifest content — is ever returned to the coding model or placed where its next
turn could read it. The only feedback surface the model has is `ci:agent`
(`TD-B16`), which excludes architecture enforcement and all hidden checks.

## 6. The evaluator is blind to condition and model during scoring

During scoring the evaluator receives the **patch and repository state only**. It
must not receive, and must not be able to infer, the **condition** (C1–C4) or the
**model** that produced the patch:

- the oracle engine's scoring API takes no condition or model parameter;
- inputs handed to the evaluator are normalized so no condition tag or model
  identity appears in paths, filenames, or manifest fields it reads;
- the raw finding record (`architecture_finding.json`) carries no condition or
  model field.

## 7. Condition/model metadata is appended only after blind scoring

The harness may attach condition and model identity to the **assembled** record
(`oracle_result.json` / `run_manifest.json`) **only after** blind scoring has
produced the findings. Attaching identity is a post-scoring bookkeeping step; it
never influences a finding.

## 8. Mounted evaluator content is hashed in the run manifest

Each run's manifest records the **content hashes** of the mounted evaluator
material (manifest id/version and per-file SHA-256) so a run is reproducible and
auditable, **without exposing the contents** in the public record. The run
manifest's optional `evaluator_mount` block carries these hashes and asserts
`mount_outside_worktree: true` and `contents_exposed: false`
(`run_manifest.schema.json`).

---

## Status

The boundary and its mechanical policy are **specified and machine-checked at the
fixture level** in this package (the mount-rejection test and the
coding-worktree-cleanliness test). Runner-time enforcement in the live experiment
(`TD-B16`) and the authored per-task hidden material (`TD-B05`) remain **open**;
no paid model run is performed here.
