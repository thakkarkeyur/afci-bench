# docs/v2 — Open Decisions Registry (Blocking & Non-Blocking TODOs)

Status: **authoritative registry of unresolved decisions for study v2**. Every
`TD-*` reference in the v2 protocol resolves to a row here. This is the single
source of truth for what is **not yet decided**, who owns it, whether it
**blocks** data collection, and where it is resolved. Development artifact only:
it does **not** freeze the final benchmark configuration and authorizes **no**
paid model run.

> **Pre-freeze draft.** The protocol is **structurally complete but not
> scientifically frozen** (see [`README.md`](README.md)). **None** of these
> decisions is resolved by the pre-execution design-review reconciliation;
> scientific freeze occurs only after that reconciliation is **independently
> approved** and the relevant blocking decisions are **closed**. Binding *design*
> decisions (D1–D13) are recorded separately in
> [`CRITICAL_DESIGN_DECISIONS.md`](CRITICAL_DESIGN_DECISIONS.md); they are not
> resolutions of these data/artifact-dependent blockers. No `protocol-freeze` tag
> exists.

Machine-readable companion: [`OPEN_DECISIONS.csv`](OPEN_DECISIONS.csv). A test
(`experiments/v2/harness/tests/test_open_decisions.py`) asserts that every `TD-*`
cited anywhere in the protocol appears here, that every entry has an owner, and
that none is yet marked resolved.

## Counts

- **Blocking decisions: 37** (`TD-B01`–`TD-B37`) — must be resolved before the
  corresponding data collection; all are cited inline across the protocol files.
  `TD-B16`–`TD-B21` were added by the pre-execution design-review reconciliation;
  `TD-B22` was added by the independent public review of the pilot task package;
  **`TD-B23`–`TD-B33` were added by the suite-classification decision (decision
  D)** that narrowed the confirmatory construct to dependency-direction
  conformance; **`TD-B34`–`TD-B37` were added by the independent pre-authoring
  opportunity reassessment** (`DECISION B`, `PT05`'s reclassification, the
  production-source scoring policy, and the statistical-governance consequences).
- **Non-blocking decisions: 6** (`TD-N01`–`TD-N06`) — refinements that do not
  block the confirmatory design.
- **Total decisions: 43**, of which **2 are resolved** (`TD-B23`, `TD-B24`) and
  **41 remain open**. The two resolved entries are the model-visible
  architecture-comment remediation and the leakage audit that proves it; both were
  completed **before** any benchmark or model execution and neither freezes
  anything. Every other decision — including every task-authoring blocker
  (`TD-B34`, `TD-B26`, `TD-B31`) and runner-time enforcement (`TD-B22`) — is
  **still open**.

A **blocking** decision, if left unresolved, would invalidate or bias the
associated result; it maps to a pilot gate (`G1`–`G8`) where feasible. A
**non-blocking** decision improves rigor or reproducibility but does not gate the
confirmatory analysis.

---

## Blocking decisions (TD-B01 – TD-B37)

| ID | Decision | Owner | Resolved during | Gate |
|----|----------|-------|-----------------|------|
| **TD-B01** | **Condition-neutral, non-canonical** reset checkpoint predicates + the pre/post-reset budget split (pre-reset consumption logged separately from **equal** post-reset allowance) per task | Pilot Task Designer | pilot task design | G2 |
| **TD-B02** | Freeze the final model-execution settings after resolving MODEL_EXECUTION_CONTROLS Q1–Q10 by a controlled dry run | Harness Engineer | after dry-run validation | — |
| **TD-B03** | Select the primary benchmark model (do **not** select Sonnet or Opus yet); screen incl **C1/C3/C4**; **never** select on the largest AFCI effect (D10) | Study Lead | after dry-run validation (TD-B02) | — |
| **TD-B04** | Author the approved MAD and machine-checkable architecture-rule catalog (rule ids; severity; evaluator) delivered by C3/C4 | Oracle Designer | pilot task design | G1/G5 |
| **TD-B05** | Author the hidden acceptance criteria, out-of-scope surface, and legitimate alternatives per task (kept hidden) | Oracle Designer | pilot task design | G1 |
| **TD-B06** | Final distribution/family and endpoint specification and degenerate-outcome coding (after dispersion & ceiling checks) | Statistician | pilot | G2 |
| **TD-B07** | Significance level, power target, minimum detectable effect, effect-size boundaries (**NOT** from v1) | Statistician | a-priori + pilot | G3 |
| **TD-B08** | The C2↔C4 token-match tolerance value (from the measured C4 MAD token count) | Study Lead + Statistician | pilot task design | G4 |
| **TD-B09** | Industrial data availability, AFCI adoption date, minimum interpretable sample, raw-data access, anonymization feasibility | Industrial Data Owner (FGC) | feasibility audit | G7 |
| **TD-B10** | Replication count per cell (from pilot dispersion + target precision; **NOT** from v1) | Statistician | pilot | G2/G3 |
| **TD-B11** | Total fixed budget per run (tokens/turns/time) kept equal for reset and non-reset | Harness Engineer | pilot task design | — |
| **TD-B12** | Guard/oracle validation (labelled corpus; mutation tests; **alias + barrel + re-export** resolution; **moved/deleted-code + full-repository** eval; **seeded-violation sensitivity**; **known-good specificity**; legitimate alternatives frozen before confirmatory data; blinded double rating **≥0.70**) | Guard Engineer | pilot | G6 |
| **TD-B13** | Demonstrate benchmark discrimination (tasks/checkpoints distinguish conditions; non-degenerate) | Pilot Task Designer + Statistician | pilot | G2 |
| **TD-B14** | Task-suite selection and layer taxonomy (required/optional/prohibited layers per task) | Task Designer | pilot task design | G1/G2 |
| **TD-B15** | The pre-registered unacceptable-cost tolerance for RQ3 | Statistician + Study Lead | pilot | — |
| **TD-B16** | Agent-visible CI separation enforced in the live runner (`ci:agent` only; hidden acceptance + architecture-oracle checks never in the model workspace/feedback loop) | Harness Engineer | after the runner exists (TD-B02) | — |
| **TD-B17** | Public-task architecture-leakage validation of the authored v2 task suite (validator OK; exceptions justified) | Task Designer | pilot task design | G1 |
| **TD-B18** | Byte-identical C3/C4 frozen architecture-content parity (hashes recorded; no C4-only hard rule; frozen before pilot) | Oracle Designer | pilot task design | G5 |
| **TD-B19** | Isolated container + dedicated identity + CLEAN context audit (managed policy absent) for every counted run | Harness Engineer | container baseline | — |
| **TD-B20** | Interaction-focused power simulation (condition × reset), mandatory before the core grid; final counts simulation-determined | Statistician | pilot | G2/G3 |
| **TD-B21** | Runtime model-id dry runs (Q1 resolved-id readback; Q8 invalid-id rejection), blocking before the paid pilot | Harness Engineer | after dry-run validation (TD-B02) | — |
| **TD-B22** | **Runner-time enforcement of the model-visible worktree policy**: every counted run's worktree built from the allowlist by `prepare_model_worktree.py`; **no** `ARCHITECTURE_CONTEXT.md`, `ARCHITECTURE_RULE_CATALOG.yml` or architecture-enforcing `.eslintrc.json` in any condition's workspace; C3 persistent payload / C4 prompt-only payload verified; snapshot `content_hash` recorded per run | Harness Engineer | after the runner exists (TD-B02) | G3/G4/G5 |

### Added by the suite-classification decision (decision D) — `TD-B23` – `TD-B33`

Narrowing the confirmatory construct to **layered dependency-direction
conformance** exposed eleven separate blockers. Two of them — **`TD-B23`** (the
baseline substrate stated the scored rules in source comments) and **`TD-B24`**
(the leakage sweep could not see source comments) — are now **resolved**, by
actually removing the disclosure and actually extending the audit, before any
benchmark or model execution. **The remaining nine stay open**, and none of them
may be closed by restating the classification.

| ID | Decision | Owner | Resolved during | Gate |
|----|----------|-------|-----------------|------|
| **TD-B23** | ✅ **RESOLVED — disposition: neutralise.** Model-visible TypeScript comments explicitly stated scored dependency rules to every condition, including the C1 baseline: `apps/api/src/app.ts` stated the `api → core` prohibition, named the architecture-CI consequence and carried a worked commented-out forbidden import; `libs/infra/src/index.ts` justified avoiding `core` as "a deliberate architectural choice"; `libs/features/src/index.ts` restated the `api → core` prohibition from the `features` side. All six lines are removed. The edit is **comment-only** and proven non-behavioural (identical emitted JS with comments stripped, identical AST fingerprint, identical import/export edges), so the substrate was **re-identified, not re-designed**. Structural signals stay (folder names, `scope:*` tags, path aliases, import edges, behaviour-describing comments), and `api → core`, `infra → core` and `features → infra` all remain structurally detectable. Regression proof: **PROOF 10**, with the verbatim pre-remediation bytes preserved in [`../../experiments/v2/leakage_fixtures/`](../../experiments/v2/leakage_fixtures/). No benchmark or model execution; nothing frozen. | Task Designer + Study Lead | resolved before the pilot (substrate decision) | G2/G3 |
| **TD-B24** | ✅ **RESOLVED.** The worktree leakage sweep now reads file **content**, not only names. `scan_source_comment_disclosures` parses JS/TS line and block comments (skipping string, template and regex literals), JSON string **values** (not keys, so `.eslintrc.agent.json` is not flagged for naming the rule it switches off), hash-comment config files and prose files; `scan_snapshot_violations` refuses with the new code `ARCHITECTURE_COMMENT_DISCLOSURE`. A comment counts only when it states a **rule** — a worked violation example, a commented-out workspace-package import, a named rule/opportunity id, or a prohibition/exclusivity claim **paired with a named layer** — so prose that merely names layers, modules or imports is not flagged. Positive **and** negative regression cases exist (**PROOF 10**), including the verbatim pre-remediation bytes and a negative fixture of the retained prose, and the real prepared **C1 and C2** snapshots pass. Runner-time enforcement of the surrounding policy remains open as **`TD-B22`**. | Harness Engineer | resolved before the pilot (`TD-B22` still open) | G2/G3 |
| **TD-B25** | **`PT03`'s public repeat-request contract is contradictory.** It permits a change to any of the five accepted values — including `delivered` and `cancelled` — while also requiring that repeating the same request returns the same stored status, *and* that a current status of `delivered` or `cancelled` answers HTTP 409 `ConflictError`. A target of `delivered` or `cancelled` cannot satisfy both. Requires a **separate public task amendment** and a **private relink** of `PT03`'s package to the amended hash. **Deliberately not fixed in this commit.** | Task Designer | separate public `PT03` amendment | G1/G2 |
| **TD-B26** | **`PR02`'s terminal-state completion criterion is not externally reachable at the source substrate.** Cancelling a `shipped` or `delivered` order must answer HTTP 409 `ConflictError`, but no public endpoint can move an order out of its created status and `PR02` creates none. **`PR02` must not be activated or promoted until the criterion is repaired and the repair is independently re-approved.** | Task Designer | before any reserve activation | G1/G2 |
| **TD-B27** | **The attribution rule is now decided and implemented publicly; the private opportunity sets and the labelled-corpus validation are not.** `dependencyDirection.ts` no longer matches an exact importer path: an opportunity is scored over its **frozen architectural scope** (`locator.scope` resolved through the frozen `dependency_policy.layers` path globs), `locator.importer_path` is **provenance only**, `NOT_APPLICABLE` requires an **absent scope**, and one frozen decision contributes **at most one** violation — regression-locked by the **M0–M7** mutation corpus (`experiments/v2/oracle/tests/scopeAttribution.test.ts`) covering violations in **new** files, **moved** files, and after **anchor deletion**. **Still blocking:** every private per-task opportunity set must be re-authored and re-justified under scope attribution (scope + forbidden targets + implemented leaf rule; no `AR-DEP-001` umbrella opportunities; no duplicated decisions), and the attribution must still be validated on the labelled corpus against the pre-registered precision/recall bar. | Guard Engineer | pilot (with `TD-B12`) | G6 |
| **TD-B28** | **`AR-DEP-001` must be considered for all private manifests** so relevant dependency-family violations are not silently omitted. `AR-DEP-001` is the umbrella rule that puts the whole matrix in force; a manifest listing only some per-layer clauses scores only those clauses and drops the rest. | Oracle Designer | private manifest re-authoring (with `TD-B05`/`TD-B14`) | G1/G6 |
| **TD-B29** | **The private opportunity identified as `PT04-OPP-01` must be independently re-justified or removed privately.** The identifier is recorded here **as an identifier only**; its content, justification and disposition stay in the private evaluator repository. | Oracle Designer | private manifest re-authoring (with `TD-B05`) | G1 |
| **TD-B30** | **Repeated opportunities collapse onto a small number of shared boundary decisions**, so opportunity instances are **pseudo-replicates**, not independent observations. The mandatory interaction power simulation (`TD-B20`) must **model this pseudo-replication**, and the analysis must carry a matching sensitivity re-fit. | Statistician | pilot (with `TD-B20`) | G2/G3 |
| **TD-B31** | **A suite-wide public-interface reachability validation is required, not a `PT06`-only guard.** Every completion criterion of every candidate must be provably reachable through the public interface of the unchanged substrate, with no failure-injection hook, test-only route, special header or environment flag. `test_pt06_feasibility.py` covers one task. | Task Designer | pilot task design (before freeze) | G1/G2 |
| **TD-B32** | **Hidden evaluator scaffolds remain `draft_unvalidated`** and require independent review plus reference and mutation validation before any package may be approved or frozen. | Oracle Designer + Guard Engineer | private review and validation (with `TD-B05`/`TD-B12`) | G1/G6 |
| **TD-B33** | **Implementing `AR-CONTRACT-001` or `AR-CODE-001` remains future work intended to BROADEN E1** to further architecture dimensions. It must **never** be used to readmit a structurally excluded task **post hoc**, and any broadening requires its own pre-registration before data collection. | Oracle Designer + Study Lead | future protocol version (not this package) | G1/G8 |

### Added by the pre-authoring opportunity reassessment — `TD-B34` – `TD-B37`

| ID | Decision | Owner | Resolved during | Gate |
|----|----------|-------|-----------------|------|
| **TD-B34** | **DECISION B — author additional public tasks exercising genuinely different existing dependency-direction leaf rules and source/target boundaries before Stage 0.** The motivation is **construct validity**: the current active set (`PT01`–`PT04`) does not sample enough **distinct** dependency-direction decisions to support the intended confirmatory endpoint; repeated tasks over one boundary are one architectural instrument observed repeatedly, not independent architecture constructs. This decision **predates any benchmark or model outcome** and **no experimental result exists**. **No reserve is activated merely to restore task count.** The deficiency is **task-set coverage, not an oracle failure**; the repaired scope-based oracle **remains** the approved attribution mechanism; and **no new rule family is required**, because unused implemented dependency leaf relationships already exist (`AR-DEP-002`…`AR-DEP-006`). Gates **G1/G2/G6** stay **blocking** and the suite is **not** ready. | Task Designer + Study Lead | next public task-authoring work package (before Stage 0) | G1/G2/G6 |
| **TD-B35** | **`PT05` is reclassified `scored` → `functional-only`** because its required functional work creates no currently scored dependency-direction opportunity; its **private** per-task manifest must be migrated to `e1_analysis_eligibility=functional-only` with **no** opportunity denominator, or the engine fails closed. A **construct/feasibility** reclassification made **before any run** — never zero violations, failed, missing, invalid or a refusal. The private evaluator repository was **not accessed**. | Oracle Designer | private manifest re-authoring (with `TD-B05`/`TD-B14`) | G1 |
| **TD-B36** | **The labelled corpus and every private frozen opportunity set must be re-checked under the production-source policy** (§1b): no opportunity may depend on a test-only or config-only dependency, and no seeded violation may sit in an excluded file. The policy itself needs independent review before freeze. Regression-locked publicly by **M8-A**–**M8-F**; **not** discharged. | Guard Engineer | pilot (with `TD-B12`/`TD-B27`) | G6 |
| **TD-B37** | **The current four-task architecture set is not confirmatory-ready and no final power value may be frozen from it.** Repeated exposures to one boundary are **clustered**; **task count ≠ independent architecture-decision count**; the final interaction power simulation (`TD-B20`) runs **only after** additional distinct decisions are authored and approved (`TD-B34`); and a **decision/boundary cluster identifier** must be carried in the eventual analysis artifact, with a matching sensitivity re-fit (`TD-B30`). **No power simulation was run here.** | Statistician | after `TD-B34` authoring is approved (with `TD-B20`/`TD-B30`) | G2/G3 |

Added by the pre-execution design-review reconciliation: `TD-B16`–`TD-B21`; added
by the independent public review of the pilot task package: `TD-B22`; added by the
suite-classification decision: `TD-B23`–`TD-B33`; added by the pre-authoring
opportunity reassessment: `TD-B34`–`TD-B37`. Each
is **open** (none resolved here — the CI/leakage **mechanisms** are delivered and
tested, but the runner-time enforcement, authored suite, frozen hashes,
container, pilot simulation, and dry runs all remain outstanding).

**Oracle-foundation package: partial advances, none resolved.** `TD-B04` is
partially advanced — the machine-checkable architecture-rule catalog
(`ARCHITECTURE_RULE_CATALOG.yml`) and the alias/barrel/re-export-aware
dependency-direction reference checker (`experiments/v2/oracle/`) exist with
synthetic unit validation — but the catalog is **not frozen** and `TD-B04` stays
**open**. `TD-B12` is partially advanced — alias/barrel/re-export +
moved/deleted-code + full-repository evaluation are implemented and unit-validated
— but the labelled corpus, the multi-category mutation set, and blinded
inter-rater κ ≥ 0.70 are **not** done, so `TD-B12` stays **open**. The
hidden-evaluator boundary and mount policy (`HIDDEN_EVALUATOR_BOUNDARY.md`,
`EVALUATOR_MOUNT_POLICY.md`) are delivered and machine-checked, but runner-time
enforcement (`TD-B16`) and authored per-task hidden material (`TD-B05`) remain
**open**. Gates **G1** and **G6** are **not** passed.

**Pilot task-authoring package: partial advances, none resolved.** The pilot
task candidates (six primary `PT01`–`PT06`, two reserve `PR01`–`PR02`) have been
**authored** as public functional task bodies
([`experiments/v2/tasks/public/`](../../experiments/v2/tasks/public/)), and the
public-task leakage validator reports **OK** for every one — a partial advance on
`TD-B17` (the authored draft suite is leakage-clean and self-checked), which
**stays open** pending independent review at freeze. All hidden evaluator material
for these candidates (per-task manifests, hidden acceptance plans, fixed
opportunity sets, expected/prohibited areas, legitimate alternatives, reset
predicates, threat reviews) lives **only in a separate local private evaluator
repository** and is absent from this repository, so `TD-B05` (hidden
acceptance/alternatives/out-of-scope) and `TD-B14` (task-suite selection + layer
taxonomy) are **partially advanced but remain open** — the material is drafted,
not approved or frozen, and its task-specific oracle validity is unverified.
`TD-B13` (benchmark discrimination) is **untouched**: no pilot run occurred. Every
private manifest is status `review` (not frozen); the architecture oracle refuses
to score it (`MANIFEST_NOT_FROZEN`). No final task/repetition/run count and no
numerical reset budget were selected. Gates **G1** and **G2** remain **not
passed**; the protocol remains **pre-freeze**.

**Public pilot-task repair package: new blocker opened, none resolved.** An
independent review of the public pilot task package found four task defects
(`PT06` impossible against the frozen base; `PT04` partly unsatisfiable; `PT02`
and `PT03` leaving their JSON wire formats undefined), two fairness gaps
(unpinned `error` values; `PR01`'s worked example already satisfied at the base),
four demonstrated bypasses in the leakage validator (front matter unscanned;
line-scoped hard-leak matching; only the architecture family covered; nested task
files undiscovered), and a workspace confound. The task bodies were repaired and
re-hashed, the validator was hardened with regression tests for every demonstrated
bypass, and public hash/index/matrix integrity is now machine-checked. `TD-B17`
(public-task leakage validation of the authored suite) is **further advanced but
still open** — the mechanism is stronger and the suite is clean, but independent
approval at freeze has not happened. `TD-B05`/`TD-B14` remain **open and are now
further behind**: `PT04` and `PT06` changed subject matter, so their hidden
packages must be re-authored, and every other candidate's pinned public-task hash
changed. The workspace confound is tracked as the new blocking decision
**`TD-B22`**: the delivered `prepare_model_worktree.py` mechanism and its nine
proofs are development-time only, and **runner-time enforcement does not exist**
because the live runner does not exist (`TD-B02`). Gates **G1**, **G2**, **G3**,
**G4** and **G5** remain **not passed**; the protocol remains **pre-freeze**.

**`PT06` amendment: one candidate re-scoped, nothing resolved.** A further review
found that the repaired `PT06` still required a behaviour **no external caller can
provoke** against the unchanged source substrate — a failure that is not caused by
invalid input, answered HTTP 500 with `error` `InternalServerError`. Validating it
would have required a failure-injection hook, test-only route, special header,
environment flag or other implementation-specific seam in the substrate every
condition shares, which is itself a design answer and was refused. `PT06` is
re-scoped to the rejection envelope of `POST /orders`: the existing
semantic-validation failures and an unparseable JSON body must answer the same HTTP
400 `ValidationError` body, success unchanged. Three existing validation rules are
named publicly and feasibility is machine-checked
([`test_pt06_feasibility.py`](../../experiments/v2/harness/tests/test_pt06_feasibility.py));
the base answers an unparseable body as HTML today, so the task is not already
satisfied. Only `PT06`'s public bytes and hash changed
(`3994a158…` → `ae87303c…`); `apps/` and `libs/` are byte-identical. `TD-B17` is
**further advanced but still open** — the amended body is leakage-clean and now
feasibility-checked, but independent approval at freeze has not happened.
`TD-B05`/`TD-B14` remain **open**: **only `PT06`'s** private package is made stale by
this amendment and must be **substantively re-authored** after the amendment is
approved; the seven others (including `PT04`) stay linked to the public bytes
reviewed at `0e77d49`, and the private commit built against those bytes must not be
reviewed as a complete eight-task package until `PT06` is updated. No model ran, no
task count was fixed, gates **G1**–**G5** remain **not passed**, and the protocol
remains **pre-freeze**.

**`PT06` rejection contract clarified: two under-determinations closed, nothing
resolved.** An independent review of the amendment above found no defect that
invalidated it, but two places where `PT06`'s public text did not fully determine the
required behaviour — either of which could have let a conforming solution satisfy every
stated criterion and still fail acceptance. (1) The text constrained the rejection
*body* ("JSON — never HTML, never empty") but not the *declared media type*, so a
serialised envelope sent under `text/html` conformed to the letter. `PT06` now requires
a `Content-Type` response header whose media type begins with `application/json` on
both covered rejections, and states that **no other response header** is part of its
required behaviour. (2) The text opened with an unqualified "a rejected `POST /orders`
request answers with HTTP 400" while pinning only two kinds in its criteria; that gap
is externally reachable, because the base answers an over-large body **HTTP 413** and
an unsupported charset **HTTP 415**, both as HTML. `PT06` now names exactly two covered
kinds in a **Scope** section and states that HTTP 413, HTTP 415, aborted requests and
every other transport-level or body-parsing rejection are outside its scope and keep
their current status codes and bodies. Only `PT06`'s public bytes and hash changed
(`ae87303c…` → `3e0f84cf…`); `apps/` and `libs/` are byte-identical, and **no**
architecture wording, applicable rule, expected area or task-specific opportunity was
added to any public artifact. `TD-B17` is **further advanced but still open**.
`TD-B05`/`TD-B14` remain **open** and their `PT06` scope is unchanged: still **only**
`PT06`'s private package is stale, it must be **substantively re-authored** under the
`PT06` acceptance-scope constraints now recorded publicly, and private commit
`5733ca6151f7739c7105a5c1405fcbc8fb3cb59d` must not be reviewed as a complete
eight-task package until it is. Separately, whether the amended `PT06` still carries a
**non-empty fixed opportunity set** is a **future private-evaluator blocker** under
`TD-B05`/`TD-B14`, gated by **G1** — not a defect in `PT06`'s public text, deliberately
not settleable in public without publishing private material, and to be demonstrated
during that private re-authoring before the package may be approved or frozen. No model
ran, no task count was fixed, gates **G1**–**G5** remain **not passed**, and the
protocol remains **pre-freeze**.

**Suite classification narrowed (decision D): eleven new blockers, nothing
resolved.** An independently approved suite-level decision narrowed the
confirmatory construct to **layered dependency-direction conformance**. `E1` is
renamed **"dependency-direction violation rate per applicable frozen
opportunity"**, its numerator pinned to
`opportunity_accounting.violated_opportunity_count` and its denominator/offset to
`opportunity_accounting.applicable_opportunity_count`; `applicable_rule_count` is
**not** an admissible offset, stub rules do **not** enlarge the denominator,
`raw_violation_count` is a separate descriptive diagnostic, and a task with
`applicable_opportunity_count = 0` is **structurally ineligible** for E1 rather
than coded as zero violations. Analysis eligibility is now recorded publicly per
candidate ([`PILOT_PUBLIC_TASK_MATRIX.csv`](PILOT_PUBLIC_TASK_MATRIX.csv),
`TASK_INDEX.csv`): at that decision **`PT01`–`PT05` `scored`**, **`PT06`
`functional-only`** (a valid primary functional candidate, structurally excluded
from E1 but still contributing to hidden functional acceptance, cost and
exploratory analyses), and
**`PR01`/`PR02` `inactive-reserve`** — **no reserve was activated**, and `PR02`
must not be promoted (`TD-B26`). Contract ownership, port/interface placement,
observability completeness, duplicated logic and general business-logic placement
are split out as **CON-ACB**: pre-registered secondary/manual evidence, **not**
directly measured by E1, whose confirmatory use requires blinded double rating
with **Cohen's κ ≥ 0.70**. The **paper must not describe E1 as broad or general
architectural conformance** (gate **G8**). **No task body, task content hash,
manifest, endpoint or protocol was frozen**, no oracle change was made, `apps/`
and `libs/` are byte-identical, the private evaluator repository was **not
accessed**, and **no benchmark or model execution occurred**. Eleven blockers
were **opened** (`TD-B23`–`TD-B33`) and **no blocking decision was
closed**; gates **G1**–**G8** remain **not passed** and the protocol remains
**pre-freeze**.

**Oracle specifications aligned with the narrowed endpoint; private manifests now
require migration.** A follow-up public change propagated decision D into the
measurement-specification layer that the first commit missed:
[`ORACLE_VALIDATION_REQUIREMENTS.md`](ORACLE_VALIDATION_REQUIREMENTS.md) §6,
[`ORACLE_TRACEABILITY.csv`](ORACLE_TRACEABILITY.csv), gate **G3** in
[`PILOT_GATE_MATRIX.csv`](PILOT_GATE_MATRIX.csv), `oracle_result.schema.json` and
RQ2 in [`RESEARCH_QUESTIONS.md`](RESEARCH_QUESTIONS.md) had all retained the
pre-narrowing "architecture-violation rate per applicable rule" framing. They now
state the narrowed endpoint and its pinned accounting; `oracle_result.json` makes
`opportunity_accounting` **required** and demotes `applicable_rule_count` /
`satisfaction_proportion` to explicitly descriptive diagnostics, so a result
carrying only rule-based accounting is no longer sufficient for E1.
`evaluator_manifest.schema.json` gains a **required** `e1_analysis_eligibility`
field with five fail-closed engine gates binding each manifest to the approved
public task index.

> **The per-task manifests in the private evaluator repository were NOT accessed
> or modified and do not carry the new field.** They **fail closed**
> (`ELIGIBILITY_MISSING`) until migrated, so none can be scored under an assumed
> eligibility. This migration — and the reconciliation of each manifest's declared
> eligibility against the public index — is part of the private manifest
> re-authoring already tracked by **`TD-B05`**/**`TD-B14`** and must complete
> before any package is approved or frozen. **No blocker was closed**, no task body
> or hash changed, nothing was frozen, and no benchmark or model execution
> occurred.

**Pre-authoring opportunity reassessment: `PT05` reclassified, `DECISION B`
recorded, production scoring isolated — four new blockers, nothing resolved.** An
independent reassessment of the active architecture set, carried out **before any
benchmark or model execution** and from the public task bodies and the unchanged
substrate only:

- **`PT05` → `functional-only`** (`TD-B35`). It is **functionally valid but
  structurally ineligible for E1**, because its required functional work creates
  **no currently scored dependency-direction opportunity**. A **construct and
  feasibility** reclassification, **not** a model outcome: `PT05` is never
  reported as zero violations, failed, missing, invalid, or a refusal, and it
  still contributes to hidden functional acceptance, cost, reset-related
  functional outcomes and pre-registered exploratory analyses. Its body, hash and
  `primary` kind are **unchanged**. **No reserve was activated** to restore the
  scored count — `PR01`/`PR02` stay inactive and `PR02` stays blocked (`TD-B26`).
- **`DECISION B`** (`TD-B34`): the surviving active set exercises **too few
  distinct dependency boundaries** for confirmatory inference, so **additional
  public architecture tasks must be authored before Stage 0**. The deficiency is
  **task-set coverage, not an oracle failure**, and **no new rule family** is
  needed — unused implemented leaf relationships already exist. Only the authoring
  **requirements** are recorded here; **no task was authored**.
- **Production-source scoring** (`TD-B36`): the P0 that let test and configuration
  TypeScript enter the scored dependency scopes is closed. E1 is computed from the
  **production dependency graph** only; test specs, test support material and
  tooling config are partitioned into a separate, never-scored graph before any
  import edge is built. The **frozen layer scopes are unchanged**, and the
  denominator remains the frozen opportunity count, so test files move neither
  side of E1.
- **Statistical governance** (`TD-B37`): the current four-task architecture set is
  **not confirmatory-ready**; repeated exposures to one boundary are **clustered**;
  **task count ≠ independent architecture-decision count**; the final power
  simulation waits for `TD-B34`; a **cluster identifier** will be required in the
  analysis artifact; and **no power value is frozen**.

**No task body or hash changed, no reserve was activated, no task was authored,
no manifest/endpoint/protocol was frozen, `apps/` and `libs/` are byte-identical,
the private evaluator repository was not accessed or modified, and no benchmark or
model execution occurred.** Four blockers were **opened** (`TD-B34`–`TD-B37`);
**no blocking decision is closed**, gates **G1**–**G8** remain **not passed**, and
the protocol remains **pre-freeze**.

---

## Non-blocking decisions (TD-N01 – TD-N06)

| ID | Decision | Owner | Resolved during |
|----|----------|-------|-----------------|
| **TD-N01** | Pin CI to the exact Node patch (`node-version-file: .nvmrc`) so CI and local cannot drift | Harness Engineer | before final config freeze |
| **TD-N02** | Triage the 41 known npm advisories in the transitive tree | Harness Engineer | before final config freeze |
| **TD-N03** | Decide whether to add a workflow/agent experimental arm with a recordable mechanism | Study Lead | optional; later |
| **TD-N04** | Capture the container image digest in `environment_fingerprint` once the container baseline is chosen | Harness Engineer | with the container decision |
| **TD-N05** | Detailed anonymization/pseudonymization scheme for the industrial dataset | Industrial Data Owner (FGC) | with G7 |
| **TD-N06** | Escalation policy for repeated infrastructure failure on a single run cell | Harness Engineer | before runs |

---

## Related open items outside this registry

`MODEL_EXECUTION_CONTROLS.md` §7 lists ten runtime **dry-run-required** questions
(Q1–Q10) about the Claude CLI's effort readback, thinking, workflow mode, and
model-id handling. Those are the concrete validations that must be performed
before `TD-B02` (freeze model-execution settings) and `TD-B03` (select the
primary model) can be resolved. They require a controlled `claude -p` run and are
therefore **out of scope for this protocol-development package**, which performs
no paid model run. The **model-id** items specifically — **Q1** (resolved-id
readback) and **Q8** (invalid-id rejection) — are now tracked as their own
blocking decision **`TD-B21`**, dry-run blockers before the paid pilot.

## Updating this registry

- Add or change a decision in **both** [`OPEN_DECISIONS.csv`](OPEN_DECISIONS.csv)
  (authoritative, test-checked) and this table.
- When a decision is resolved, change its `status` to `resolved` **and** record
  the resolution (value + evidence) in the owning artifact; do not delete the
  row (protocol-version history).
- Any new `TD-*` cited in a protocol file must have a row here, or the
  cross-reference test fails.
