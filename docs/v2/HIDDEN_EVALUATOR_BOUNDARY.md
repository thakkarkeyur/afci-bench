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

## 2. What the public repository MAY contain — and why that is NOT the same as
## what the model sees

The public repository may contain, because none of it reveals a task-specific
answer:

- evaluator **schemas** (`experiments/v2/schemas/*.schema.json`);
- generic **engine code** (the oracle framework and the dependency-direction
  reference checker under `experiments/v2/oracle/`);
- **synthetic fixtures** (the oracle's own validation cases, which contain no
  benchmark task and no task-specific answer);
- **documentation** (this file, the rule catalog, the manual rubric, policies);
- **empty templates** without task answers.

**None of this reaches the coding model.** An earlier revision of this section
said the canonical architecture context was "deliberately deliverable to the
model" and drew the line at *answer-bearing* content only. An independent review
showed that reading was unsound: because the coding worktree was the whole
repository, [`ARCHITECTURE_CONTEXT.md`](ARCHITECTURE_CONTEXT.md) (the explicit
architecture payload) and
[`ARCHITECTURE_RULE_CATALOG.yml`](ARCHITECTURE_RULE_CATALOG.yml) (the rule
catalog the oracle scores against) were readable in **every** condition,
including the no-guidance C1 baseline — a direct confound on the primary
C4-vs-C1 contrast, and a contradiction of C1's own prohibited-files list in
[`CONDITIONS.md`](CONDITIONS.md) §3.

The line is therefore drawn at the **model-visible worktree**, not at the
repository:

- The architecture payload is **content that must be delivered by channel**, to
  C3 and C4 only, through the mechanism their condition specifies. It is never
  present as a repository file the model can read.
- The coding worktree is **built** by
  [`MODEL_VISIBLE_WORKTREE_POLICY.md`](MODEL_VISIBLE_WORKTREE_POLICY.md) from an
  allowlist (`apps/`, `libs/`, build/type-check/test configuration, the
  agent-visible lint config). `docs/`, `experiments/`, `paper/` and `archive/` are
  excluded wholesale, so every document listed above — including this one — is
  absent from the model's worktree.
- What deliberately remains visible is the **substrate**: folder names, nx scope
  tags, path aliases, source code and existing visible tests (D3). The implicit
  architectural tension stays real; only the explicit statement of the rules is
  removed.

Runner-time enforcement of that preparation step is **`TD-B22`** and is **open**.

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

# Functional Acceptance Observation Boundary

Sections 1–8 above govern **where** hidden material lives and **who** may see it.
This section governs something different and previously unstated: **what a hidden
acceptance test is allowed to look at when it decides pass or fail**. It is
decided **before** any further hidden acceptance is implemented, so no task's
grading surface is chosen after its assertions are written. Blocking decisions:
**`TD-B39`** (migrate the existing hidden acceptance packages onto this boundary)
and **`TD-B40`** (the analytically inactive dependency opportunities still
physically present in the private manifests).

## 9. The name of the boundary

**Externally observable functional acceptance through HTTP plus explicitly
declared task-relevant application seams.**

The longer name is deliberate. Calling the evaluator "HTTP-only" would be false:
`PT04`'s public task requires structured log records, which are an externally
*emitted* behaviour that no HTTP response carries, and `PT04` is gradeable only
because the application publicly declares a log-output seam. "HTTP-only" would
either misdescribe `PT04` or invite an undeclared exception for it later.

- **HTTP is the default observation channel.** Unless a task says otherwise, an
  acceptance assertion is derived from an HTTP request and its response.
- **A declared seam is exceptional**, is justified by the public task, and is
  registered in §12 before hidden tests are implemented.
- **Internal persistence and module state are not observation channels** and can
  never become one.

## 10. What hidden functional acceptance MAY do

1. **Instantiate the application through its public factory** `createApp`.
2. **Supply only publicly declared dependencies** — the members of the
   application's declared `AppDependencies` / test-seam surface, and nothing else.
3. **Issue requests through HTTP semantics** (supertest or any equivalent HTTP
   client): method, path, query string, request headers, and a JSON *or raw*
   request body. `PT06` needs an unparseable raw body with a JSON content type;
   that is an HTTP observation, not an exception to this boundary.
4. **Observe the HTTP response** — status code, response headers, and response
   body.
5. **Observe one explicitly declared, task-relevant application seam** — and only
   where the public task itself requires an externally emitted behaviour that HTTP
   cannot faithfully carry. The declared seams are enumerated in §12; there are
   currently no others, and a task may not invent one.
6. **Compare two HTTP responses against each other** — for example, asserting that
   a new endpoint reports the same monetary values as an existing endpoint for the
   same line items. A response-to-response comparison introduces no new rule and
   reads no internal state.

## 11. What hidden functional acceptance MAY NOT do

1. **Import or inspect internal domain implementation** in order to grade
   behaviour.
2. **Use internal persistence or module state as an acceptance oracle** — this
   includes `getOrderRepository()`, `InMemoryOrderRepository.count()`,
   `resetOrderRepository()`, and any successor of them.
3. **Seed state through implementation modules.** Every precondition an assertion
   depends on must be established through the public interface. A precondition that
   is not reachable that way is an **unreachable-setup blocker** for the task
   (`TD-B31`), not a licence to reach inside.
4. **Read implementation files to decide pass or fail.**
5. **Require a particular class, function, file, or module layout.**
6. **Use architecture-oracle results to determine functional acceptance** (§13).
7. **Assume the solution still uses the substrate's original singleton, its
   original repository implementation, or its internal test helpers.**

A conforming implementation with a **different internal design must remain
gradeable**. If a planned assertion can only pass under one internal design, the
assertion — not the solution — is inadmissible.

### 11a. Test isolation is not an acceptance oracle, and `resetOrderRepository` is not the isolation mechanism

Isolation between acceptance cases is **task-neutral plumbing**. It may never
appear in, or be relied on by, an assertion.

The obvious candidate mechanism — calling the substrate's exported
`resetOrderRepository()` between cases, as the visible `apps/api/src/app.spec.ts`
does — was assessed and **rejected as the normative method**, because it couples
the evaluator to one implementation in two independent ways:

- **The symbol is not guaranteed to survive a conforming change.** It is an export
  of the persistence adapter and it manipulates a module-level singleton. A
  solution that injects the repository through `AppDependencies`, replaces the
  adapter, or removes the singleton may legitimately leave no such function. A
  grader that calls it would then fail a correct solution for a reason the public
  task never stated.
- **Even where the symbol survives, its effect is implementation-dependent.**
  `createApp` resolves the repository **once, at construction**. Whether a reset
  actually isolates the next case therefore depends on when the application was
  constructed and on whether the solution resolves persistence once or per
  request. Isolation whose effect depends on the implementation is not isolation.

**Normative method.** Each acceptance case runs against a **freshly constructed
application over a freshly evaluated module graph** — a fresh process, or a
module-registry reset followed by a fresh import of the application factory. This
is implementation-independent: it re-establishes whatever state the solution
happens to hold, singleton or not.

`resetOrderRepository()` is therefore classified as **legacy baseline-test
infrastructure** belonging to the substrate's visible test suite. It stays in the
substrate untouched — removing it would change the substrate and is not in scope
here — but it is **not** an approved hidden-evaluator mechanism and is **never**
evidence for an acceptance assertion.

## 12. Declared seam register

A seam is admissible only if **all** of the following hold. The register is
public; what the hidden tests assert through a seam is not.

1. The **public task's required behaviour names the externally emitted behaviour**
   the seam carries.
2. HTTP **cannot faithfully carry** that behaviour.
3. The seam is part of the application's **publicly declared dependency surface**,
   not an internal module reached around the front door.
4. It is **declared here before** the task's hidden tests are implemented.

| Seam | Supplied through | Task that grounds it | Why HTTP is insufficient |
|---|---|---|---|
| `LogOutput` sink | `createApp({ logOutput })` — a declared member of `AppDependencies` | `PT04` — "Emit structured request and error logs for order creation" | The required behaviour *is* the emitted log record; it is never part of any HTTP response, and `PT04` states explicitly that no request body, response body, status code or header of any existing endpoint changes. |

No other seam is declared. In particular:

- **Internal persistence state is not a seam** and may not be declared as one, at
  any time, for any task.
- **A hidden test may not create a seam.** If a planned assertion needs an
  undeclared seam, either the public task is amended (publicly, with its hash
  changing and its private package re-linked, §10 of
  [`TASK_AUTHORING_POLICY.md`](TASK_AUTHORING_POLICY.md)) or the assertion is
  dropped. Discovering the need *while writing hidden tests* is exactly the case
  this rule forbids resolving privately.

## 13. Architecture scoring and functional acceptance stay channel-separated

The two evaluations are computed from **different evidence** and neither may be
an input to the other:

- an architecture finding (`architecture_finding.json` / `oracle_result.json`,
  computed from the production dependency graph) **never** contributes to a
  functional pass or fail;
- a functional acceptance result (`acceptance_result.json`, computed from the
  observations permitted by §10) **never** contributes to an architecture finding;
- a task may fail functional acceptance while satisfying every frozen dependency
  opportunity, and vice versa. Those are separate, separately reported outcomes.

This is the acceptance-side counterpart of §6's blindness requirement: §6 keeps
the evaluator from knowing *which condition* produced a patch, and §13 keeps its
two scoring channels from contaminating each other.

## 14. Applying the boundary to the current candidates

High-level audit of the eight candidates against §10/§11. It records what each
task's acceptance **needs**, and does not disclose any hidden assertion.

| Task | Channel required | Status |
|---|---|---|
| `PT01` | HTTP only | admissible |
| `PT02` | HTTP only | admissible |
| `PT03` | HTTP only — the public task makes request repetition the way persistence is observed | admissible; the separate `TD-B25` contract contradiction is unaffected by this boundary |
| `PT04` | HTTP + the declared `LogOutput` seam (§12) | admissible; the sole grounded seam exception |
| `PT05` | HTTP only | admissible (`functional-only`) |
| `PT06` | HTTP only — including a raw unparseable body with a JSON content type, and the `Content-Type` response header | admissible; its out-of-scope classes are graded as *unchanged relative to a baseline capture*, which is itself an HTTP observation, and whether every named out-of-scope class is elicitable on the substrate stays open under `TD-B31` |
| `PR01` | HTTP only | admissible (`inactive-reserve`) |
| `PR02` | **unresolved / unreachable setup** | blocked. Its terminal-state precondition (`shipped`, `delivered`) is not reachable through the public interface of the unchanged substrate (`TD-B26`), and §11.3 forecloses the only workaround — seeding that state through implementation modules. This boundary makes `TD-B26` **stricter**, not softer. |

No task contract is amended here; violations and blockers are recorded only.

**Consequence for the existing hidden acceptance packages (`TD-B39`).** The
private scaffolds' recorded runtime wiring names "repository reset" as part of
their intended setup. Under §11a that is no longer the normative isolation
mechanism, so every hidden acceptance package must be migrated to fresh-app
isolation before it may be validated or frozen. The private evaluator repository
is **not** modified by the package that records this.

---

## Status

The boundary and its mechanical policy are **specified and machine-checked at the
fixture level** in this package (the mount-rejection test and the
coding-worktree-cleanliness test). The **functional acceptance observation
boundary** (§9–§14) is now **decided and machine-checked as governance**
(`experiments/v2/harness/tests/test_functional_acceptance_boundary.py`); what
remains open is migrating the private hidden acceptance packages onto it
(`TD-B39`). Runner-time enforcement in the live experiment (`TD-B16`) and the
authored per-task hidden material (`TD-B05`) remain **open**; no paid model run is
performed here.
