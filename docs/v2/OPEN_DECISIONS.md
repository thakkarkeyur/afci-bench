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
that **only the explicitly enumerated resolved decisions** are marked resolved —
every other row must still be `open`, and the Stage-0 blockers are asserted open
by name.

## Counts

- **Blocking decisions: 41** (`TD-B01`–`TD-B41`) — must be resolved before the
  corresponding data collection; all are cited inline across the protocol files.
  `TD-B16`–`TD-B21` were added by the pre-execution design-review reconciliation;
  `TD-B22` was added by the independent public review of the pilot task package;
  **`TD-B23`–`TD-B33` were added by the suite-classification decision (decision
  D)** that narrowed the confirmatory construct to dependency-direction
  conformance; **`TD-B34`–`TD-B37` were added by the independent pre-authoring
  opportunity reassessment** (`DECISION B`, `PT05`'s reclassification, the
  production-source scoring policy, and the statistical-governance consequences);
  **`TD-B38` was added by the independent architecture-neutral-substrate review**
  that found the model-visible package/`.gitattributes` metadata still announcing
  the experiment itself; **`TD-B39`–`TD-B40` were added by the pre-authoring
  governance package that defined the functional acceptance observation boundary**
  and recorded that the reassessment's preservation-only opportunities had not yet
  been migrated out of the private manifests (`TD-B40` was then **re-scoped** to
  the residual inactive-reserve and re-approval housekeeping that survives the
  migration, and is now **resolved** — both residuals complete; closure freezes
  nothing and passes no gate); **`TD-B41` was added by the remaining-leaf feasibility governance
  package** that re-scoped `TD-B34` to replication depth and had to settle how a
  fixed, very small decision space is analysed at the **realised** cluster count.
- **Non-blocking decisions: 6** (`TD-N01`–`TD-N06`) — refinements that do not
  block the confirmatory design.
- **Total decisions: 47**, of which **4 are resolved** (`TD-B23`, `TD-B24`,
  `TD-B38`, `TD-B40`) and **43 remain open**. Three of the resolved entries are
  the model-visible architecture-comment remediation, the leakage audit that
  proves it, and the experiment-awareness remediation; all were completed
  **before** any task authoring and **before** any benchmark or model execution.
  The fourth, `TD-B40`, closed once **both** of its two residuals were complete —
  the inactive-reserve reconciliation and the **independent re-approval of the
  complete migration**. **None of the four freezes anything.** In particular,
  closing `TD-B40` freezes **no** manifest, passes **no** gate (`G1` included),
  makes **no** experiment run-ready, activates **no** reserve and resolves
  **neither** `TD-B34` **nor** `TD-B39`. Every other decision — including every
  task-authoring blocker (`TD-B34`, `TD-B26`, `TD-B31`), the hidden-acceptance
  isolation migration (`TD-B39`) and runner-time enforcement (`TD-B22`) — is
  **still open**.

A **blocking** decision, if left unresolved, would invalidate or bias the
associated result; it maps to a pilot gate (`G1`–`G8`) where feasible. A
**non-blocking** decision improves rigor or reproducibility but does not gate the
confirmatory analysis.

---

## Blocking decisions (TD-B01 – TD-B41)

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
| **TD-B30** | **Repeated opportunities collapse onto a small number of shared boundary decisions**, so opportunity instances are **pseudo-replicates**, not independent observations. The mandatory interaction power simulation (`TD-B20`) must **model this pseudo-replication**, and the analysis must carry a matching sensitivity re-fit. **The pseudo-replication is governed explicitly by `decision_cluster_id`** (`source_scope + forbidden_target + leaf_rule`): every scored opportunity carries it into the analysis artifact, several already-authored scored tasks are repeated observations of **one** cluster and are never entered as independent architecture decisions, and the adjudicated active set holds **5** opportunities across only **3** clusters. Because that count is **fixed and small (G = 3)**, the clustering is represented by `decision_cluster_id` as a **fixed factor** rather than by a random-intercept variance estimated from three groups ([`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md) §4b; `TD-B41`), and the matching sensitivity is the small-cluster robust/randomisation programme recorded there. | Statistician | pilot (with `TD-B20`) | G2/G3 |
| **TD-B31** | **A suite-wide public-interface reachability validation is required, not a `PT06`-only guard.** Every completion criterion of every candidate must be provably reachable through the public interface of the unchanged substrate, with no failure-injection hook, test-only route, special header or environment flag. `test_pt06_feasibility.py` covers one task. | Task Designer | pilot task design (before freeze) | G1/G2 |
| **TD-B32** | **Hidden evaluator scaffolds remain `draft_unvalidated`** and require independent review plus reference and mutation validation before any package may be approved or frozen. | Oracle Designer + Guard Engineer | private review and validation (with `TD-B05`/`TD-B12`) | G1/G6 |
| **TD-B33** | **Implementing `AR-CONTRACT-001` or `AR-CODE-001` remains future work intended to BROADEN E1** to further architecture dimensions. It must **never** be used to readmit a structurally excluded task **post hoc**, and any broadening requires its own pre-registration before data collection. | Oracle Designer + Study Lead | future protocol version (not this package) | G1/G8 |

### Added by the pre-authoring opportunity reassessment — `TD-B34` – `TD-B37`

| ID | Decision | Owner | Resolved during | Gate |
|----|----------|-------|-----------------|------|
| **TD-B34** | **DECISION B (re-scoped) — govern adequate coverage of the COMPLETE task-creatable dependency-decision space of the canonical substrate before Stage 0, through replication depth over the three demonstrated decision clusters.** <!-- TD-B34-BREADTH-HISTORICAL --> **The original breadth objective** — author tasks exercising genuinely different leaf rules and source/target boundaries — **is superseded and structurally unattainable**: an independent remaining-leaf feasibility review classified `AR-DEP-002` (contracts), `AR-DEP-003` (core) and `AR-DEP-004` (infra) **theoretically detectable but not task-creatable** on this substrate, leaving a hard ceiling of **3 clusters / 2 leaf rules / 2 source scopes / 3 forbidden targets**, all three clusters already represented ([`DEPENDENCY_TASK_FEASIBILITY.md`](DEPENDENCY_TASK_FEASIBILITY.md)). The motivation is unchanged — **construct validity**: the adjudicated active set carries **5** E1 opportunities across **3** clusters, **two of them singletons**, and repeated tasks over one boundary are one architectural instrument observed repeatedly, not independent architecture constructs. **Re-scoped objective:** (1) retain all three clusters; (2) add independent functional instruments to the singletons where scientifically feasible — priority **A** `DC-FEATURES-API-AR-DEP-006` (n=1), then **B** `DC-API-CORE-AR-DEP-005` (n=1); `DC-FEATURES-INFRA-AR-DEP-006` (n=3) is **not** the immediate priority; (3) **no artificial tasks created only to hit mechanically implemented leaves**; (4) record the breadth ceiling as a **construct-validity limitation**; (5) defer broader generalisation to a **declared substrate redesign**, not to wishful authoring. **No exact new task body is specified and it is not asserted that two suitable tasks exist** — functional distinctness and task-created validity need a separate pre-authoring review. This decision **predates any benchmark or model outcome** and **no experimental result exists**. **No reserve is activated merely to restore task count.** The deficiency is **task-set coverage, not an oracle failure**; the repaired scope-based oracle **remains** the approved attribution mechanism; and **no new rule family is required**, because the binding constraint is substrate feasibility, not checker coverage. Gates **G1/G2/G6** stay **blocking** and the suite is **not** ready. **Progress, not resolution:** one new primary task — **`PT07`** *Price a proposed order before it is placed* (`pricing-endpoint`, `primary`, `scored`, `candidate`, SHA-256 `557caed09420354e…`) — was authored under this decision **before** any benchmark or model execution, from a candidate whose design and public-interface feasibility were **independently reviewed beforehand**; it is decidable through **HTTP alone** with no declared seam, no internal-state inspection, no seeded state and **no non-persistence assertion** (that criterion was independently **rejected as externally ungradeable**); and **no reserve was activated**. **`TD-B34` remains open and blocking:** the three achievable clusters are occupied but two carry a single observation each, the replication-candidate review has not happened, **no power simulation may run yet** (`TD-B37`), and `PT07` still cannot enter E1. **Reconciled against the authorised private state:** `PT07`'s private evaluator package **has now been authored** and linked to the approved public hash, so the earlier statement that it has none is **withdrawn as stale**. It **has also now been independently reviewed and APPROVED** — an external independent **read-only** review returned verdict **APPROVE** with **P0 = 0**, **P1 = 0** and **P2 = 6** hardening findings, all six since implemented, and that approval is now propagated into the private governance record; the earlier statement that the package has **not** been independently reviewed is therefore **also withdrawn as stale**. **That approval is not a freeze and not a gate pass:** the package is `status=review` and **not frozen**, gate `G1` is **not** passed, `PT07` is **not yet E1 run-eligible**, and its opportunity set is a **candidate rather than a demonstrated frozen denominator** (`TD-B05`/`TD-B14`/`TD-B32`). No reviewer identity, external URL or timestamp was supplied and none is claimed, and the review **precedes** the commit that records it. The approval covers the **`PT07` package only** — not the opportunity migration (`TD-B40` residual (B)) and not the eight other private packages, which remain `review_required`. It must **not** be closed by authoring toward the superseded breadth objective, by activating a reserve, or by raising the task count. **Priority-A pre-authoring progress, not resolution:** the replication-candidate pre-authoring review this re-scope requires **has now happened for priority A**. An independent Priority-A review of the provisional candidate **`CAND-A1`** — a caller-declared order-value ceiling on order creation, targeting `DC-FEATURES-API-AR-DEP-006` — returned **`DECISION B` — REPAIR CANDIDATE BEFORE AUTHORING** with **P0 = 0** and **four P1 findings**, all four now closed: **`P1-1`** (requirement 5 ambiguity about a new request header) closed by **`SL-CA1-01`**, which selects a **publicly specified query parameter `maxTotal`** as the carrier instead of a new request header, so no special-header adjudication is required because **no special header is used**; **`P1-2`** (natural-path rather than strict forcing, with a legitimate **boundary-only** implementation that is **cheaper** than the intended features-side one) closed by **`SL-CA1-02`**, which **accepts** `CAND-A1` as a scientifically valid independent replication instrument while recording that it is **not** preservation-only, that **doing nothing fails the functional contract**, that it creates a real **new** functional requirement, that a violating implementation is compiling / CI-agent-clean / evaluator-detectable, that conforming implementations exist, that a legitimate boundary-only implementation also exists and is **cheaper than both** the intended conforming features-side and the violating implementation, that the task therefore does **not strictly force `features`-scope work**, that its forcing class is **natural-path / opportunity-creating, not strict**, that this weaker forcing is **accepted as a construct-validity limitation**, that discriminative difficulty must be evaluated **only** through the pre-registered **Stage-1 baseline-only `C1`** pilot, that the task must **never** be tuned on `C4` or any treatment-effect result, that `CAND-A1` must **not** be represented as having forcing strength equal to `features → infra` tasks, and that within-cluster observations remain **pseudo-replicates**; **`P1-3`** (task-createdness not distinguished from forcing strength) closed by recording the `features → infra` versus `features → api` **forcing-strength asymmetry** normatively in [`DEPENDENCY_TASK_FEASIBILITY.md`](DEPENDENCY_TASK_FEASIBILITY.md) §2a; and **`P1-4`** (the completed `TD-B40(B)` independent re-approval never propagated) closed by **propagating** that already-completed external read-only re-approval into both repositories, which is what lets `TD-B40` close. The contract decisions the review required **before** authoring are pinned in [`CAND_A1_PREAUTHORING_DECISION.md`](CAND_A1_PREAUTHORING_DECISION.md): **`P-3`** rejection outcome (HTTP **409**, error `OrderValueLimitExceeded`, response keys exactly `error`/`message`/`correlationId` with **no** additional key and the exact message text deliberately unpinned); **`P-4`** wire determinacy for `maxTotal` (absent leaves existing behaviour unchanged; zero is valid; negative, empty, non-numeric, `NaN`/`Infinity` spellings and repeated values are invalid and reuse the existing **400** `ValidationError` envelope; **equality is accepted**; above the ceiling yields **409**) with the deterministic precedence that **existing body validation wins** when body and `maxTotal` both fail; **`P-5`** **no new money semantics** at all, the ceiling being compared against the **existing service-reported total**; and **`P-6`** an **HTTP-only** observation boundary with no seam, no hidden setup, no persistence inspection, no seeded state, **no `resetOrderRepository()`**, and a fresh application over a freshly evaluated module graph per hidden case. Legitimate implementation families **`ALT-A`, `ALT-C`, `ALT-F`, `ALT-H`, `ALT-I`, `ALT-K`** are **pre-declared** so the hidden architecture scorer cannot mistake a legal solution for a violation; **`ALT-C`** (boundary-only enforcement) is the **strongest task-createdness counterexample** and is **cheaper** than the feature-side implementation, **`ALT-K`** may also **reduce violation frequency**, both consequences are **expected and accepted**, and **no hidden architecture rule may be designed around eliminating them**. **As originally recorded, none of that authored anything:** **no `PT08` identifier was assigned**, no public task body existed, no private evaluator package or manifest existed, `CAND-A1` had **no** eligibility status, it was **not** an active opportunity and it entered **no** E1 denominator row. **The active counts as recorded then:** at that point the active set held **5** opportunities over **3** decision clusters at depths **3 / 1 / 1**, and `DC-FEATURES-API-AR-DEP-006` stood at **one active** observation — the cluster reaches two only after the public task is authored, an independent public-authoring review passes, a private package is subsequently authored and validated, and eligibility governance permits inclusion. **As recorded then, the candidate was not finally approved:** closing the four P1 findings was remediation, not approval, and **one focused independent remediation re-review was required** before authoring could begin. **Priority-A public authoring is now complete, and is still not resolution:** that focused remediation re-review has since **passed**, with verdict **APPROVE — public authoring may begin**, and `CAND-A1` has been publicly authored as the task body **`PT08`** *Apply a caller-declared maximum total to order creation* (`write-endpoint`; `primary`; `e1_analysis_eligibility=scored`; `task_status=candidate`; public SHA-256 `a31bb515b79cc1e2…`), with that identifier assigned **at public authoring** and nowhere earlier. The authored body implements the pinned **`P-3`**–**`P-6`** decisions unchanged; its wording is **functional only** and passes the unmodified leakage validator with **no** reviewed exception; it is decidable through **HTTP alone** with no declared seam, no internal-state inspection, no seeded state and **no assertion about stored state**, which is what keeps the pre-declared **boundary-only** family legal; and unpinned numeric spellings are explicitly **out of scope** rather than silently decided. **What public authoring did not do — as recorded then:** at that point the independent public-authoring review of `PT08` was **pending**; **no** private evaluator package, manifest or architecture opportunity existed for it; it entered **no** active E1 denominator and added **no** active observation to any decision cluster; and its `scored` eligibility recorded **intent only**. **Priority-A admission is now complete, and is still not resolution:** the independent public-authoring review of `PT08` **has since passed**; its **private evaluator package has since been authored** and **approved on a discharged conditional independent review**; and a **separately recorded governance admission step** then admitted its single fixed architecture opportunity to the active E1 denominator and the active cluster register. The active set therefore now holds **6** opportunities over **3** decision clusters at depths **3 / 2 / 1**; the priority-A cluster `DC-FEATURES-API-AR-DEP-006` stands at **two** observations; and **`PT08` adds the second active observation**. **That depth is replication depth over one shared decision:** `PT04` and `PT08` stay **pseudo-replicates**, the cluster count is unchanged at **3**, and admission creates **no new decision cluster**. **What admission still does not do:** gate **`G1`** is **not** passed; `PT08` is **not** frozen, **not** run-ready and **not** E1 run-eligible; its manifest is `status=review`; its hidden functional acceptance stays `draft_unvalidated`; **no** result, violation value, success value or treatment-effect estimate exists; no reserve was activated; and no power simulation may run (`TD-B37`). **`TD-B34` therefore remains open and blocking:** priority **B** (`DC-API-CORE-AR-DEP-005`) has had **no** candidate review at all and **priority B is not started**, so the re-scoped replication-depth objective is **not** satisfied, and gates **G1/G2/G6** stay **blocking**. | Task Designer + Study Lead | further public task-authoring work packages (before Stage 0) | G1/G2/G6 |
| **TD-B35** | **`PT05` is reclassified `scored` → `functional-only`** because its required functional work creates no currently scored dependency-direction opportunity; its **private** per-task manifest must be migrated to `e1_analysis_eligibility=functional-only` with **no** opportunity denominator, or the engine fails closed. A **construct/feasibility** reclassification made **before any run** — never zero violations, failed, missing, invalid or a refusal. The private evaluator repository was **not accessed**. | Oracle Designer | private manifest re-authoring (with `TD-B05`/`TD-B14`) | G1 |
| **TD-B36** | **The labelled corpus and every private frozen opportunity set must be re-checked under the production-source policy** (§1b): no opportunity may depend on a test-only or config-only dependency, and no seeded violation may sit in an excluded file. The policy itself needs independent review before freeze. Regression-locked publicly by **M8-A**–**M8-F**; **not** discharged. | Guard Engineer | pilot (with `TD-B12`/`TD-B27`) | G6 |
| **TD-B37** | **The current architecture task set is not confirmatory-ready and no final power value may be frozen from it.** Repeated exposures to one boundary are **clustered**; **task count ≠ independent architecture-decision count**; the final interaction power simulation (`TD-B20`) runs **only after** the `TD-B34` objective is met and approved; and a **decision/boundary cluster identifier** must be carried in the eventual analysis artifact, with a matching sensitivity re-fit (`TD-B30`). First recorded against the four-task set of the time (`PT01`–`PT04`); the set is now **five** scored candidates over **three** clusters, **two of them singletons**, which does not discharge it. **The simulation stays blocked until all four preconditions hold:** (a) the `TD-B34` re-scope to replication depth is complete and its authoring outcome independently approved; (b) the **replication design is known** — which clusters gain an independent instrument and which stay singletons; (c) the **small-cluster (G = 3) analysis method is pre-registered** ([`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md) §4b, subject to `TD-B41`); (d) the **final E1 denominator structure is known** — which candidates carry a valid non-zero frozen opportunity set (`TD-B05`/`TD-B14`, `G1`). **No power simulation was run here or by the re-scope package.** | Statistician | after the `TD-B34` objective is met and approved (with `TD-B20`/`TD-B30`/`TD-B41`) | G2/G3 |

### Added by the independent architecture-neutral-substrate review — `TD-B38`

The review that checked whether the `TD-B23` remediation had actually produced a
neutral baseline found that it had produced an **architecture-rule**-neutral one
which was still **experiment-aware**: the model-visible `package.json` and
`.gitattributes` announced the benchmark, the canonical architecture context, the
conditions and the hidden oracle. This is filed as its own decision rather than
reopening `TD-B23`, because the two threat classes are different and the review
treated them as such — `TD-B23` is the substrate *coaching the answer*, `TD-B38`
is the substrate *revealing the experiment*. Neither subsumes the other.

| ID | Decision | Owner | Resolved during | Gate |
|----|----------|-------|-----------------|------|
| **TD-B38** | ✅ **RESOLVED — disposition: neutralise.** Model-visible metadata disclosed the **experiment** to every condition including the C1 baseline: `package.json` carried `description` = "Architecture-First Context Injection Benchmark" (expanding the AFCI construct in full and naming the study a benchmark) plus the `oracle:test` / `oracle:typecheck` scripts, whose names disclosed a hidden oracle and whose commands pointed at `experiments/v2/oracle`; `.gitattributes` carried prose naming "AFCI-Bench study v2", the canonical architecture context, its delivery "identically to the repository-instruction conditions", and the committed fixtures. A C1/C2 model reading these learns nothing about **which** dependency direction is legal — so `TD-B23` does not cover it — but does learn that architecture is the **scored construct** and that a treatment and an oracle exist. Remediated in `630d3180af0d02a86330dfb599f559e78df65e94`, which **replaces `15aa99f5` as the canonical source substrate**: neutral description, both oracle scripts removed with **no** replacement model-visible script pointing at the oracle or the experiment tree, and a neutral `.gitattributes` retaining **every** functional directive. All participant scripts byte-identical; no architecture rule, dependency graph, task body, task hash, task eligibility or application behaviour changed; `apps/` and `libs/` trees byte-identical to `15aa99f5`; `package-lock.json` unchanged. Detector: `scan_experiment_awareness`, refusal code `EXPERIMENT_AWARENESS_DISCLOSURE`, matching only **contextual combinations** (never bare `architecture`/`test`/`condition`/`context`/`benchmark`) and flattening wrapped prose. Regression proof: **PROOF 11**, with the verbatim pre-remediation bytes in `experiments/v2/leakage_fixtures/`. **Residual, accepted and recorded:** the `@afci-bench/*` workspace scope remains in `tsconfig.base.json` aliases and `apps/`/`libs/` imports; removing it means editing application source and re-identifying the substrate, so it needs its own work package. Found and fixed **before** task authoring and **before** any benchmark or model execution. | Harness Engineer + Study Lead | resolved before the pilot (substrate decision, pre-authoring) | G2/G3 |

### Added by the pre-authoring functional-evaluator boundary package — `TD-B39` – `TD-B40`

Two pre-authoring conditions had to close before the next architecture candidate
could be authored: **what a hidden acceptance test may look at** when it decides
pass or fail, and **which architecture decisions are actually active** once the
reassessment's preservation-only opportunities are set aside. Both are decided
here **before** any further hidden acceptance exists, so no grading surface and no
novelty claim can be chosen after the fact. **No task was authored, no task body
or hash changed, `apps/` and `libs/` are unchanged, no reserve was activated, the
private evaluator repository was not modified, and no benchmark or model ran** by
the package that opened these two rows.

> **`TD-B40` was re-scoped and is now RESOLVED.** The private opportunity
> migration it called for was performed under separate authorised private work:
> the preservation-only rows are out of the active E1 set and survive only as
> superseded, non-scoring audit records, and the row stopped stating that
> `api → core` is unrepresented. `TD-B40` then governed **only** the residual
> inactive-reserve rows and the outstanding independent re-approval — and **both
> of those residuals are now complete**, the complete migration having been
> **independently re-approved** in an external read-only re-review. The row below
> carries the closure text.
>
> **Closure is bounded, and the bound is part of the decision.** Closing `TD-B40`
> freezes **no** manifest, passes **no** gate (`G1` included), makes **no**
> experiment run-ready, activates **no** reserve, and resolves **neither**
> `TD-B34` **nor** `TD-B39`. Freeze and `G1` are governed by
> `TD-B05`/`TD-B14`/`TD-B32` and, for the eight legacy hidden-acceptance packages,
> by `TD-B39`; `TD-B40` never governed freeze, so a still-pending freeze is **not**
> a `TD-B40` residual and must not be used to hold the row open.

| ID | Decision | Owner | Resolved during | Gate |
|----|----------|-------|-----------------|------|
| **TD-B39** | **The functional acceptance observation boundary is defined suite-wide, and the existing hidden acceptance packages must be migrated onto it before any may be validated or frozen.** *Externally observable functional acceptance through HTTP plus explicitly declared task-relevant application seams* ([`HIDDEN_EVALUATOR_BOUNDARY.md`](HIDDEN_EVALUATOR_BOUNDARY.md) §9–§14): HTTP request/response is the **default** surface; a declared seam is permitted **only** where the public task requires an externally emitted behaviour HTTP cannot faithfully carry, and **exactly one** is declared suite-wide (the `LogOutput` sink through `createApp({ logOutput })`, grounded in `PT04`); a seam must be declared **before** hidden-test implementation and a hidden test may never create one; hidden acceptance may not inspect implementation-specific persistence, module state, classes, files or architecture findings; **hidden state seeding through implementation modules is prohibited**; a conforming implementation with a different internal design must remain gradeable; **test isolation is never an acceptance oracle**; and the two scoring channels stay separated. `resetOrderRepository()` was independently assessed and **rejected** as the normative isolation mechanism — the symbol need not survive a conforming change, and even where it does its effect is implementation-dependent because `createApp` resolves persistence once at construction — so it is reclassified as **legacy baseline-test infrastructure**, left in the substrate untouched, and the normative method is a **freshly constructed application over a freshly evaluated module graph**. **Still blocking:** the private scaffolds name "repository reset" in their intended wiring and must be migrated, and every planned assertion re-checked against the permitted channels. **Now surfaced privately, still not repaired:** authorised private work has recorded this blocker against each of the **eight legacy packages** (`PT01`–`PT06`, `PR01`, `PR02`) in its blocker summary, per-package records and generated governance artifacts, and records `PT07` as **already conforming** because it was authored after this boundary. That surfacing is **documentation-only**: no hidden acceptance plan, scaffold assertion or fixture behaviour was migrated, and `TD-B39` is **not** resolved. | Oracle Designer | private hidden acceptance re-authoring (with `TD-B05`/`TD-B32`) | G1/G6 |
| **TD-B40** | ✅ **RESOLVED / CLOSED — both residuals complete; this row is no longer a blocking gate.** **What closure does NOT do, stated first so it cannot be quoted without it:** closing `TD-B40` freezes **no** manifest, passes **no** gate (`G1` included), makes **no** experiment run-ready, activates **neither** `PR01` **nor** `PR02`, resolves **neither** `TD-B34` **nor** `TD-B39`, and produces **no** experimental result and **no** power value. Every manifest remains `status=review` and unfrozen. Freeze and `G1` are governed by `TD-B05`/`TD-B14`/`TD-B32` and, for the eight legacy hidden-acceptance packages, by `TD-B39`; **`TD-B40` never governed freeze**, so a still-pending freeze is **not** a `TD-B40` residual. **What was discharged earlier:** the reassessment's preservation-only dependency opportunities are **no longer in the active E1 set** — none appears in any per-task evaluator manifest opportunity set, none counts toward any E1 denominator, and each survives only as an explicitly **superseded, detection-only historical record** carrying its removal reason, so removal was enacted as **auditable supersession** rather than silent deletion. **What this row once asserted and is now withdrawn as false:** that every retained active dependency decision sits in one source scope under one leaf rule; that the active set spans only **two** clusters; and that the **`api`** source scope and **`AR-DEP-005`** (`api → core`) are **unrepresented**. *As recorded at closure*, the adjudicated active set held **5 opportunities across 3 clusters** over **2 leaf rules, 2 source scopes and 3 forbidden targets** — the demonstrated ceiling, all three clusters represented ([`DEPENDENCY_TASK_FEASIBILITY.md`](DEPENDENCY_TASK_FEASIBILITY.md) §2–§3) — and the remaining coverage deficiency was **replication depth** in the two singleton clusters. **Current post-admission state, which `TD-B40` neither caused nor governs:** `PT08`'s separately reviewed and separately admitted opportunity moved the active set to **6** over the same **3** clusters at depths **3 / 2 / 1**, leaving **one** singleton. That deficiency belongs to the re-scoped `TD-B34`, not here, and `TD-B34` **stays open and blocking**. **Residual (A) — inactive-reserve re-authoring / reconciliation: COMPLETE.** `PR01`/`PR02` held draft rows authored before the repaired scope-based oracle and the reassessment and still shaped as scored rows. Authorised private work **re-assessed every one of them** under the current governance, and each carries an explicit recorded disposition: **four were demoted** to superseded, detection-only, non-scoring records — `PR01`'s two and `PR02`'s `api → core` row as **preservation-only**, and `PR02`'s `infra → core` / `AR-DEP-004` row as **detectable but not task-creatable** on this substrate, which additionally **bars it from ever entering an E1 denominator** and means no legacy reserve row may be read as a task-creatable **fourth cluster** — and **one survives** as a task-created reserve candidate migrated to scope attribution. `PR01` consequently carries **no** dependency-direction opportunity and could only ever be activated as a **functional** candidate. That reconciliation is now **independently re-adjudicated**: the external read-only re-review that discharged residual (B) records the `PR01`/`PR02` reserve reconciliation **expressly inside its own scope**, which is exactly what (A) was still waiting on. **Residual (B) — independent re-approval of the complete migration: COMPLETE.** An **external independent read-only** re-review of the complete migration — the six active-set supersessions, the current five active opportunities over three decision clusters, the `PR01`/`PR02` reserve reconciliation, the active cluster register, and the repaired cross-repository linkage — closed linkage findings **`P1-J1`** and **`P1-J2`**, raised **no new P0** and **no new P1** (**0** P0 against the linkage remediation or the re-approval decision; **0** P1 remaining against the migration re-approval), confirmed the **migration state unchanged** by the re-review, confirmed the repaired linkage **fails closed** on evaluation-relevant drift, and returned **`TD-B40(B)` COMPLETE MIGRATION — INDEPENDENTLY RE-APPROVED** together with **APPROVE LINKAGE REMEDIATION — `TD-B40(B)` RE-APPROVED — REPLICATION REVIEW MAY BEGIN**. **Provenance, recorded exactly as supplied:** the re-review event **precedes** the commits that record it; both repositories **propagate** that result and **neither performs it**, so nothing recorded here is a second independent opinion; and because the re-review was deliberately **read-only** it changed no byte, which is why both repositories still carried stale not-yet-re-approved metadata afterwards — that meant the re-approval had not been **propagated**, never that the re-review had not happened. **No reviewer identity, external URL, timestamp, transcript or external evidence identifier was supplied and none is claimed** — the same honest convention already used for the `PT07` package approval under `TD-B34`. **Package approval and migration re-approval remain different facts even now that both exist:** neither may be read off the other, and **neither is a freeze**. **Closure rationale:** the re-scoped definition contained exactly these two residuals and nothing else, both are complete, and no further substantive obligation remains inside the row's own definition — so it is closed rather than carried open against conditions it does not govern. **Standing rules that survive closure** as permanent constraints, not residual work, none of which closure relaxes: a reserve may be activated **only** through a separately recorded, independently approved pre-run activation decision, and **none exists**; `PR01`/`PR02` remain `inactive-reserve` with a reserve denominator of **0** and enter no active cluster register; `PR02` stays independently blocked by `TD-B26` because its terminal-state criterion is not externally reachable, and a defensible architecture row does not unblock an ungradeable functional contract; the demoted `AR-DEP-004` row is **permanently barred** from any E1 denominator on any future activation; and every demoted row stays a superseded, detection-only, historical non-scoring record and is **never deleted**. **Historical record preserved:** closure deletes nothing — the fifteen-row before-state inventory, all six removed active rows, all four demoted reserve rows with their removal reasons, the reserve dispositions and the full residual history remain in the private migration register and the per-task linkage records. **Not** an oracle failure: the repaired scope-based oracle remains the approved attribution mechanism. **No benchmark or model result exists**, and none informed the migration, the reconciliation or the re-review. | Oracle Designer | resolved — inactive-reserve re-authoring complete and independently re-adjudicated, and the complete migration independently re-approved (with `TD-B27`/`TD-B32`/`TD-B35`/`TD-B36`) | G1/G6 |

### Added by the remaining-leaf feasibility governance package — `TD-B41`

The independent remaining-leaf feasibility review established that the canonical
substrate has a **hard task-creatable ceiling of three decision clusters**, and
that all three are already represented. That turns the eventual E1 analysis into
one with a **fixed, exhaustively enumerated, very small number of clusters** — a
regime in which a random-intercept cluster variance is not a credible primary
specification. The structural commitments that follow from it are pre-registered
in [`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md) §4b **before**
any data exists; what genuinely cannot be fixed without the runner data shape is
filed here with its permitted options enumerated, rather than guessed.

**The cluster count is a ceiling, not a guarantee.** Three is the maximum the
substrate admits *and* the current expectation, but final E1 eligibility still
depends on manifest validation, approval and freeze (`TD-B05`/`TD-B14`/`TD-B32`/
`TD-B40`, gate `G1`), so the **realised** `G` is only known once those gates
resolve. §4c therefore pre-registers the realised-cluster rule **before** any
power simulation: the definition of `G`, the primary specification at **G = 3**,
the contingency at **G = 2**, and the rule that at **G < 2** the confirmatory
condition model requiring architecture-decision blocking is **not run**. `TD-B41`
governs the residual structure under whichever `G` realises and no longer asserts
that the count can only ever be three.

| ID | Decision | Owner | Resolved during | Gate |
|----|----------|-------|-----------------|------|
| **TD-B41** | **Residual specification of the small-cluster E1 analysis at the realised cluster count `G`.** **`G` is not asserted to be three:** `G` is the number of `decision_cluster_id` levels carrying at least one **final, frozen, E1-eligible** opportunity once the eligibility gates resolve (§4c). Three is the demonstrated **ceiling** and the current **expectation**, never a guarantee; the **G = 2** contingency and the **G < 2** blocking rule are pre-registered in §4c **before** any power simulation. **Already pre-registered and not reopened** (§4b–§4c): `decision_cluster_id` is a **fixed** factor at every admissible `G` and **no cluster random-intercept variance is ever estimated from so few clusters**; the clusters are an **exhaustively enumerated fixed set**, not a sample from a population of clusters; `condition`, `reset` and their interaction remain the **inferential target** and are identified **within** clusters, because every scored task is run under every condition; opportunities and repeated runs stay **nested observations inside the known clusters** and are never entered as independent architecture decisions; and inference is never reported as if `G` were large. **Still open, with the permitted options enumerated so the choice cannot drift:** (1) the repeated-measures structure for `task` and run at the realised counts — **(1a)** `task` as a fixed block nested within cluster, **(1b)** `task` as a random intercept **only if** identifiable at the realised count, or **(1c)** a cell-level dispersion / observation-level term — chosen by pre-registered criteria at pilot, **never** by which option yields the larger effect; (2) whether the cluster-robust sensitivity is **CR2 or CR3 with Satterthwaite-style degrees of freedom**, conditional on the implementation supporting it reliably at the realised `G`, with the honest fallback that at three clusters the corrected degrees of freedom are unreliable and **at G = 2 unusable** — in which case the **within-block randomisation inference** carries the sensitivity and the cluster-robust re-fit is **omitted or labelled unreliable**, never promoted to primary evidence; (3) whether the `cluster × condition` heterogeneity check is reportable at the realised cell sizes, noting that **at G = 2 it carries a single between-cluster contrast** and must be read as such. **Nothing data-dependent may be run before this is resolved, and it must be resolved before the `TD-B37` power simulation.** No model was fitted, no data exist, no power value is frozen. | Statistician | before the `TD-B37` power simulation (with `TD-B06`/`TD-B20`/`TD-B30`) | G2/G3 |

Added by the pre-execution design-review reconciliation: `TD-B16`–`TD-B21`; added
by the independent public review of the pilot task package: `TD-B22`; added by the
suite-classification decision: `TD-B23`–`TD-B33`; added by the pre-authoring
opportunity reassessment: `TD-B34`–`TD-B37`; added by the
architecture-neutral-substrate review: `TD-B38`; added by the pre-authoring
functional-evaluator boundary package: `TD-B39`–`TD-B40`; added by the
remaining-leaf feasibility governance package: `TD-B41`. Apart from the three
substrate/leakage entries recorded as resolved above (`TD-B23`, `TD-B24`,
`TD-B38`), each is **open** — the CI/leakage **mechanisms** are delivered and
tested, but the runner-time enforcement, authored suite, frozen hashes,
container, pilot simulation, and dry runs all remain outstanding.

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
task candidates of that package (six primary `PT01`–`PT06`, two reserve
`PR01`–`PR02`; the suite now holds **seven** primary `PT01`–`PT07` after `PT07`
was authored later under `TD-B34`) have been
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

**Remaining-leaf feasibility: `TD-B34` re-scoped, one blocker opened, none
closed.** An independent review of the *remaining* implemented dependency leaves —
carried out against the canonical substrate and the functional acceptance
observation boundary, **before any benchmark or model execution** — found that
`AR-DEP-002` (`contracts`), `AR-DEP-003` (`core`) and `AR-DEP-004` (`infra`) are
**theoretically detectable but not task-creatable** on this substrate. The
demonstrated ceiling is therefore **3 decision clusters / 2 leaf rules / 2 source
scopes / 3 forbidden targets**, and **all three achievable clusters are already
represented**, so the breadth expansion `TD-B34` originally directed is
**structurally impossible here**, not merely unfinished. Consequences, all
recorded rather than acted on:

- **`TD-B34` is re-scoped, not resolved** — from breadth expansion to **replication
  depth** over the three demonstrated clusters, with the under-replicated clusters
  as the named priorities (*as recorded then*, both were singletons; priority A has
  since been replicated and priority B is still a singleton and **not started**). It
  stays **open and blocking**, and **no task was authored
  and no exact new task body was specified**; whether suitable replication
  candidates exist is a separate pre-authoring review.
- **The feasibility result is recorded normatively** in
  [`DEPENDENCY_TASK_FEASIBILITY.md`](DEPENDENCY_TASK_FEASIBILITY.md), which also
  annotates the 15 theoretical `(source scope, forbidden target)` pairs with their
  feasibility status, so **mechanically detectable is never read as task-creatable**,
  and documents that the **`observability` source scope has no leaf rule** and is
  **umbrella-only** under `AR-DEP-001`.
- **Substrate redesign is recorded as a DECLARED ALTERNATIVE — NOT SELECTED**, with
  its full re-validation cost, leaving the choice with the Study Lead.
- **The breadth ceiling becomes a construct-validity limitation of the study**: E1
  effects generalise directly to the **represented** dependency-decision families,
  not automatically to all architecture rules or all layer pairs.
- **`TD-B41` is opened** for the residual small-cluster (G = 3) analysis
  specification; `TD-B30` now names `decision_cluster_id` explicitly; and `TD-B37`
  now lists its four preconditions.

**No task was authored, no task body or hash changed, no eligibility changed, no
reserve was activated, `apps/` and `libs/` are byte-identical, the canonical
substrate identity is unchanged, the private evaluator repository was not accessed,
no benchmark or model ran, no power simulation was run and no power value was
produced, and nothing was frozen.** One blocker was **opened** (`TD-B41`); **no
blocking decision is closed**, gates **G1**–**G8** remain **not passed**, and the
protocol remains **pre-freeze**.

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
