# Qualification candidates `PT09` and `PT10` — construction record

**Authority:** Study Lead decision `SL-QUAL-01`.
**Status of this document:** a construction and design record. It **freezes
nothing**, passes **no gate**, admits **no** opportunity to the active E1
denominator, closes **no** open decision, and records **no** benchmark result.
**No model was invoked** while it was produced.

**Disclosure convention.** This is a **public** document, so it never binds a task
identifier to a rule identifier, an opportunity identifier, a decision-cluster
identifier or a named boundary. The two candidates are referred to by their
**governance slots** — the **priority-A replication slot** and the **priority-B
slot** — exactly as the public `TD-B34` record already names them. Every
architecture mapping stays in the private evaluator repository.

---

## 1. Why two, and why now

The priority-A `C1` difficulty diagnostic put its instrument at the **architecture
floor** ([`PT08_DIAGNOSTIC_OUTCOME_AND_DISPOSITION.md`](PT08_DIAGNOSTIC_OUTCOME_AND_DISPOSITION.md)).
Excluding unchanged `PT08` from the confirmatory-candidate set leaves the
re-scoped `TD-B34` objective — **replication depth inside the under-replicated
decision clusters** — further from satisfied than before, not closer. Two of the
three clusters stood at **one** confirmatory-candidate observation each.

Two instruments were therefore required: a **replacement** for the confirmatory
role `PT08` was intended to fill in the **priority-A slot**, and the **priority-B**
instrument `TD-B34` has been naming since it was re-scoped. Nothing else was
authored and **no reserve was activated**.

## 2. The design principle the diagnostic forced

The diagnostic exposed one failure mode above all others:

> A task can be **functionally valid** and still be **useless for architecture
> discrimination**, if a cheaper implementation satisfies the entire functional
> contract without ever encountering the placement decision the instrument exists
> to expose.

`PT08` failed in exactly that way. Its required behaviour was decidable **entirely
at the request boundary**, from a value the boundary already had in hand, so the
cheapest correct implementation never entered the scored scope.

Both new instruments were therefore designed against a sharper bar than "the
decision is creatable":

1. the functional requirement must make the **natural, minimal-diff** route pass
   through the scored placement decision; and
2. any architecture-neutral alternative must be **strictly more work**, not less.

Neither instrument is permitted to buy that pressure with hidden tests.
**Functional acceptance and architecture scoring stay separate channels**, and
this package proves it by executing a deliberately violating reference and showing
it **passes hidden acceptance in full** (§5, §7).

## 3. A structural limit, stated before the designs

An independently reviewed feasibility finding already on the record
([`DEPENDENCY_TASK_FEASIBILITY.md`](DEPENDENCY_TASK_FEASIBILITY.md) §2a) holds
that the priority-A family is **natural-path / opportunity-creating and never
strictly forcing** on this substrate, because the application scope is the
editable composition and request boundary: it holds the request, it receives the
finished result, and it may therefore pre-process its input or post-process its
output.

This package **confirms** that finding rather than overturning it. Every concept
examined for the priority-A slot admitted **some** architecture-neutral
implementation. The design question is therefore not *whether* one exists but
**how expensive and how unnatural it is relative to the intended route** — the
gradient `PT08` had backwards.

That limitation is recorded here as a **construct-validity limitation of the
study**, exactly as `SL-CA1-02` recorded it, and is **not** engineered away with
hidden assertions.

---

## 4. Priority-A slot: candidate analysis

Concepts were evaluated sequentially against naturalness, public-task clarity,
the intended implementation route, the plausible shortcut, the escape families,
hidden-acceptance discriminability, opportunity applicability, and the risk of
leaking design intent.

### Concept D-1 — complete the structured audit record order creation emits

**Rejected: it duplicates an existing instrument.** The record is emitted from
inside the existing operation and the missing values are request-owned, so the
pull toward the intended route is genuine — but that is precisely `PT04`'s lever.
A second instrument of the same shape in the same slot would be a near-clone of
`PT04` rather than an **independent** instrument, failing authoring requirement 9
and defeating the purpose of replication depth.

### Concept D-2 — per-request line-item omission (**SELECTED**, authored as `PT09`)

A caller may ask for the order to be created from the line items the service
accepts, with the unacceptable ones left out and their submitted positions
reported.

- **Naturalness.** An everyday integration complaint: an all-or-nothing create
  forces a caller assembling a basket from a catalogue it does not control to
  retry blind. Partial acceptance is the ordinary fix.
- **Why the natural route is the intended one.** The retain/omit decision is
  **interior**: it happens after the service's own acceptance judgement and before
  pricing, and it changes **what is created**, not merely what is reported. The
  minimal diff runs through the existing operation and **reuses the acceptance
  judgement already in place**.
- **The decision it creates.** The mode is a per-request datum only the request
  boundary can read, so an implementation that decides where the work happens
  needs that datum to travel — the same decision `PT08` created, now on the route
  a solution actually takes rather than on one it abandons.
- **Determinism.** Acceptability is defined by **observable behaviour** — an entry
  is acceptable exactly when a request carrying only that entry is answered
  HTTP 201 — so the task states no new rule, and the existing requirements are not
  restated as an algorithm that could simply be copied. Non-object entries and
  whitespace-only strings are explicitly out of scope rather than silently decided.
- **Leakage.** No layer, no path, no file, no rule, no scorer, no placement. The
  unmodified leakage validator reports `OK` with no reviewed exception.

### What was rejected inside Concept D-2

- **A caller-declared quantity cap** — the boundary can clamp the request body
  before invoking anything. Pure input pre-processing; no pull toward the intended
  route.
- **A running-total cut-off** — a restatement of `PT08`'s subject matter with
  extra steps, and it introduces new monetary semantics the task is forbidden to
  add.
- **A new response value derived from the created order** — post-processable at
  the boundary from what the existing operation already returns.

## 5. Priority-A slot: escape-hatch analysis, as executed

Every row below was **built and run**: the hidden suite against a real
application, and the **real public architecture oracle** against a real snapshot.
Architecture identifiers are withheld; outcomes are reported as the oracle
reports them for the task's single authored opportunity.

| Implementation | Hidden acceptance | Scored opportunity | Classification |
| --- | --- | --- | --- |
| Unimplemented substrate | **9 of 13 semantic cases FAIL** | `SATISFIED` | discriminates implemented from unimplemented |
| Intended conforming reference | **PASS 14/14** | `SATISFIED`, applicable 1, violated 0 | **intended conforming route** |
| Deliberately violating reference | **PASS 14/14** | **`VIOLATION`**, violated 1 | **intended shortcut; detected** |
| Boundary-only, with a local copy of the acceptance rules | PASS 14/14 | `SATISFIED` | **VALID ESCAPE HATCH** |
| Boundary-only, reaching the existing judgement directly | PASS 14/14 | `SATISFIED` for this opportunity, **a different forbidden edge recorded as a raw violation** | **VALID ESCAPE HATCH** from the scored decision — and itself non-conforming |
| Existing operation bypassed and reimplemented at the boundary | PASS 14/14 | `SATISFIED` | **VALID ESCAPE HATCH** (implausible) |

**Honest reading.** `PT09` does **not** eliminate the boundary-only family, and §3
says why no instrument in this slot can. What it does is **invert the cost
gradient** `PT08` had backwards:

- under `PT08`, boundary-only was **cheaper** than the intended route — it
  compared two values the boundary already held;
- under `PT09`, boundary-only requires the boundary to **re-derive an acceptance
  judgement the service already makes**, while the intended route **reuses** it.

The fifth row is the one worth stating plainly: the shortest way to make the
boundary-only route work is to reach the existing judgement directly, which is
**itself non-conforming** and is recorded as a raw violation under a different
rule. An implementation can leave `PT09`'s scored opportunity satisfied and still
not be architecturally clean.

**No hidden assertion was added to close any of these escapes**, and none may be.

## 6. Priority-B slot: candidate analysis

### Concept B-1 — refuse creation with a structured per-item fault report

**Rejected: it overlaps the priority-A candidate.** It puts the same subject
matter — per-item acceptance — into both new instruments, which is the task
overlap authoring requirement 9 forbids.

### Concept B-2 — ask whether a proposed order would be accepted (**SELECTED**, authored as `PT10`)

- **Naturalness.** A caller that discovers refusal only by attempting the write
  has no way to warn a user or to validate a part-built order. Asking in advance
  is ordinary.
- **Why it creates a placement decision.** Answering the question requires the
  service's **acceptance judgement**, which is behaviour the request-handling
  scope reaches legitimately through the existing inward surface. The **cheapest**
  route is a single import of exactly the capability needed, taken directly rather
  than through that surface — one line, no new file. Here the shortcut is the
  **locally cheapest** option rather than the more expensive one.
- **Independence from `PT07`.** `PT07` asks *what a proposed order would cost* and
  pulls on the pricing capability; `PT10` asks *whether it would be accepted* and
  pulls on the acceptance capability. Different capability, different answer shape,
  different failure semantics — `PT10` adds **no** error answer at all and never
  refuses a question — and a different functional category. It is not a rename and
  not a clone.
- **Why duplication is unattractive.** The verdict must **agree with the answer
  the service already gives**. A hand-copied rule set has to reproduce that
  agreement in every pinned case and stay correct as the service changes, so reuse
  is the natural instinct — and reuse is where the placement decision lives.

### Priority-B slot: escape-hatch analysis, as executed

| Implementation | Hidden acceptance | Scored opportunity | Classification |
| --- | --- | --- | --- |
| Unimplemented substrate | **5 of 7 semantic cases FAIL** | `SATISFIED` | discriminates implemented from unimplemented |
| Intended conforming reference | **PASS 8/8** | `SATISFIED`, applicable 1, violated 0 | **intended conforming route** |
| Deliberately violating reference | **PASS 8/8** | **`VIOLATION`**, violated 1 | **intended shortcut; detected** |
| A local copy of the acceptance rules at the boundary | PASS 8/8 | `SATISFIED` | **VALID ESCAPE HATCH** |
| The existing inward operation reused and its outcome read | PASS 8/8 | `SATISFIED` | **VALID BUT STILL CREATES THE OPPORTUNITY** — a legitimate alternative, not an escape |

The false-positive that matters for this instrument — the sanctioned re-export
chain, by which the request-handling scope already obtains what it needs through
the inward surface — is present in **every** row and is **never** mis-scored.

## 7. Both instruments: functional acceptance never enforces placement

For **both** tasks the deliberately violating reference **passes hidden functional
acceptance in full**. That is not incidental; it is the property that keeps the
two channels separate. If a violating implementation could not pass, the
functional oracle would be enforcing placement, and the architecture measurement
would be circular.

Equally, both conforming references and every tested escape hatch pass in full, so
no arrangement of files is privileged by the functional oracle.

## 8. Mutation pressure (executed)

| | `PT09` | `PT10` |
| --- | --- | --- |
| Mutations authored | 13 | 13 |
| Classified `NOT VALID MUTANT` (equivalent under the public contract) | 0 | 1 |
| **Valid mutants** | **13** | **12** |
| **Rejected (`CAUGHT AS INTENDED`)** | **13** | **12** |
| **ESCAPED** (0 escaped for both) | **0** | **0** |
| Semantic cases with at least one mutant targeting them | 13 of 13 | 7 of 7 |

The one `NOT VALID MUTANT` is recorded rather than hidden: removing `PT10`'s
explicit empty-collection guard changes nothing observable, because the acceptance
judgement already refuses an empty line-item collection. Under the standing
escaped-mutant policy that is **equivalence**, not an escape, and it is **not** a
licence to invent a hidden requirement the public task never stated.

The non-semantic closed-assertion-surface guard case is **excluded** from both
liveness denominators: it issues no request and would pass for a candidate that
cannot even be constructed.

## 9. Agent-visible validation stays silent about all of it

`npm run ci:agent` was executed against **both** conforming references and **both**
deliberately violating references. All four exit `0`, and no agent-visible output
names a boundary, a scope or a placement constraint. The intended shortcut is
therefore neither revealed to the model by its own validation command nor blocked
before the private scorer can observe it.

## 10. Confirmatory-candidate accounting

Two registers, kept apart, and neither may be read off the other.

**Admitted active E1 register — UNCHANGED by this package.** **6** opportunities,
**3** decision clusters, depths **3 / 2 / 1**. Both new opportunities are
**staged**, exactly as the priority-A one was before its own separately recorded
admission step: admission requires independent private review and an explicit
admission decision, and neither has happened for either candidate.

**Confirmatory-candidate set — recorded by this package.** **7** opportunities
over the **same 3** decision clusters, depths **3 / 2 / 2**. It is the admitted
active set **minus unchanged `PT08`, plus the two new candidates**. Per-cluster
depths are published; the task-to-cluster mapping is not.

`PT05`/`PT06` stay `functional-only`, `PR01`/`PR02` stay inactive reserves, and no
reserve was activated.

For E1 the numerator stays `opportunity_accounting.violated_opportunity_count` and
the denominator/offset stays
`opportunity_accounting.applicable_opportunity_count`. `applicable_rule_count` is
**not** an admissible denominator.

Within-cluster observations remain **pseudo-replicates**, statistically clustered,
and are never entered as independent architecture decisions. Adding two candidates
creates **no new decision cluster** and does **not** change the substrate's
feasibility ceiling.

## 11. What this package deliberately did NOT do

- It ran **no** live model repetition of any kind, for any task. There are **zero
  new model observations** in this package.
- It ran **no** `C1` qualification diagnostic, and **no** `C2`/`C3`/`C4` anything.
- It froze **no** task and **no** manifest.
- It admitted **no** opportunity to the active E1 denominator.
- It passed **no** gate; `G1` is not passed and `G2`/`G6` are unchanged.
- It closed **no** decision: `TD-B34`, the global `TD-B32`, `TD-B12`/`G6` and
  `TD-B03` all stay open. `TD-B34` in particular is **not** closed here, because
  candidate construction is not qualification — qualification diagnostics remain
  outstanding for both candidates.
- It modified **nothing** belonging to `PT08`: not its body, not its package, not
  its freeze record, not its diagnostic artifacts.
- It obtained **no** independent review. Nothing in this package may be described
  as independently reviewed, and the `TD-B32` review requirement is untouched.

## 12. Qualification readiness

Both instruments are **ready for a `C1`-only qualification diagnostic**, on the
same firewalled, quarantined footing the earlier diagnostic used, **if and when**
the Study Lead authorises one. Neither is ready for anything else: not for
freezing, not for `C2`/`C3`/`C4`, not for confirmatory evidence, and not for entry
into any denominator.

The decision to run that diagnostic is the Study Lead's and is **not** taken here.
