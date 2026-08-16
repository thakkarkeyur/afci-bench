# docs/v2 — Oracle Validation Requirements

Status: **development requirements for study v2**. Specifies what the conformance
oracle and acceptance evaluator must satisfy **before** any confirmatory data is
scored, so that the measured **dependency-direction violation rate** is valid and
reliable (directly answering the v1 defects: a guard blind to `@afci-bench/*`
aliases that flagged nothing, a saturated `ci_pass`, and a constant
`layer_jaccard`). Development artifact only: it does **not** freeze the final
benchmark configuration and authorizes **no** paid model run.

> **The confirmatory construct is NARROW (suite-classification decision D).**
> Endpoint **E1** is the **dependency-direction violation rate per applicable
> frozen opportunity** and measures **layered dependency-direction conformance
> only**. §6 pins its accounting; nothing in this document may be read as
> licensing a per-rule denominator or a broader conformance endpoint.

Related: [`CLAIMS_CONSTRUCTS_METRICS.csv`](CLAIMS_CONSTRUCTS_METRICS.csv) (CL14
measurement validity), [`PILOT_GATE_MATRIX.csv`](PILOT_GATE_MATRIX.csv) (G1 oracle
validity, G6 guard precision/recall), the schemas in
[`experiments/v2/schemas/`](../../experiments/v2/schemas/). Blocking decisions:
**`TD-B04`** (rule catalog), **`TD-B05`** (acceptance manifest), **`TD-B12`**
(guard/oracle validation). No oracle threshold is invented here beyond the stated
inter-rater agreement target.

---

## 1. Resolution correctness (the oracle must see real dependencies)

The oracle must resolve the code as the compiler/runtime does, not by literal
string matching:

- **Alias resolution** — resolve TypeScript path aliases (`@afci-bench/*`, from
  `tsconfig.base.json`) to their real target project. *(The v1 guard matched
  literal `libs/*` and was blind to `@afci-bench/*`, so it reported total = 0.)*
- **Barrel and re-export resolution** — follow `index.ts` barrels and
  `export … from …` re-exports to the true defining module, so a dependency
  laundered through a barrel is still attributed correctly.
- **Moved/deleted-code analysis** — correctly handle code that was **moved**,
  **renamed**, or **deleted**; a violation must not be missed because a symbol
  moved, nor invented because a file was deleted.
- **Full-repository evaluation, not added-line-only** — evaluate the **whole
  resulting repository state** against the rules, not just the added lines of the
  diff. A change can introduce a violation elsewhere (e.g. by changing an export)
  or by editing an existing import; added-line-only analysis misses these.

### 1a. Opportunity attribution is scope-based, not file-based

A frozen opportunity is an architectural **decision**, not a filename. It is
located by `locator.scope` — the `id` of a layer in the frozen
`dependency_policy.layers` — together with the target layers that decision
forbids, and it is evaluated over **every source file the frozen layer path globs
assign to that scope**.

- **A violation anywhere in the frozen scope violates the opportunity.** A task
  may legitimately place its new implementation code in a different file of the
  same scope, so matching one exact historical importer path would score such a
  change `SATISFIED` while its forbidden edge sat in `raw_violation_count` only
  (`TD-B27`). Attribution must not depend on which file the model chose.
- **`locator.importer_path` is provenance/authoring evidence only.** It records
  where the decision was authored and **must not** determine scoring; deleting,
  renaming, or moving it cannot change the outcome.
- **`NOT_APPLICABLE` requires an absent SCOPE.** It is reported only when the
  frozen architectural scope itself carries no source material to evaluate — never
  because the historical anchor file was deleted or moved.
- **One frozen opportunity is one opportunity.** Several forbidden edges inside a
  single frozen decision are **one** violated opportunity, so
  `raw_violation_count` may legitimately exceed
  `violated_opportunity_count`. The denominator is the frozen manifest
  opportunity count and never depends on files the model created or edited, on
  how many imports matched, or on the size of the final patch.
- **Fail closed on a locator that cannot be scored as written.** The scope must
  be a known frozen layer; every forbidden target must be a known layer that the
  frozen matrix genuinely forbids for that scope; `rule_id` must be the
  implemented **leaf** clause for that relationship; and no two opportunities may
  claim the same `(scope, target)` decision
  (`INVALID_OPPORTUNITY_SCOPE`, `OPPORTUNITY_RULE_SCOPE_MISMATCH`,
  `DUPLICATE_OPPORTUNITY_SCOPE`).
- **The `AR-DEP-001` umbrella can never back a scored opportunity.** It may
  appear in `applicable_rule_ids` to put the whole matrix in force and so expand
  **raw** dependency-family exposure (`TD-B28`), but a fixed E1 opportunity must
  name the implemented leaf clause `AR-DEP-002…006`
  (`UMBRELLA_OPPORTUNITY_RULE`). A scope/target relationship the family covers
  only by the umbrella therefore cannot carry a scored opportunity at all.

This is validated end-to-end by the committed mutation corpus
(`experiments/v2/oracle/tests/scopeAttribution.test.ts`, cases **M0–M7**): the
same forbidden edge is scored identically in the historical anchor, in a new
file, and after the anchor is moved or deleted; a conforming new file stays
`SATISFIED`; several edges in one decision raise
`violated_opportunity_count` by exactly one; and the frozen denominator is
identical across every mutant. It does **not** discharge `G6` — the labelled
corpus, precision/recall bar, and inter-rater validation remain open.

### 1b. Production-source scoring (E1 measures production dependencies only)

**The defect this closes.** The frozen `dependency_policy.source_globs`
(`apps/**`, `libs/**` TypeScript) and the frozen **layer path globs**
(`apps/api/**`, `libs/features/**`, …) both match test and tooling TypeScript that
physically sits inside an architectural scope: `apps/api/src/app.spec.ts` is
assigned layer `api`, and each library's `jest.config.ts` is assigned that
library's layer. A dependency written **only** to construct a test double or to
configure a tool could therefore violate a **production** architectural
opportunity. That is not the construct E1 names.

**The two graphs.** Before any import edge is resolved, the engine partitions the
source-glob-selected TypeScript into two **disjoint** sets:

| Graph | Contents | Role |
|---|---|---|
| **Production dependency graph** | everything the production-source policy classifies as `production` | **the only** graph edges are built over; the only graph that can reach a finding, `raw_violation_count`, or `opportunity_accounting` |
| **Excluded test/config/support graph** | test specs, test support material, tooling/build configuration | **never scored**; recorded descriptively so the partition is auditable |

**The policy (baseline `PSP-V1`).** Explicit and auditable, never ad-hoc substring
matching. Three exclusion lists, evaluated in a fixed order:

1. **Tooling/build configuration** — exact **basenames**: `jest.config.ts`,
   `jest.setup.ts`, `jest.preset.ts`, `vitest.config.ts`, `vite.config.ts`,
   `webpack.config.ts`, `rollup.config.ts`, `babel.config.ts`, `eslint.config.ts`,
   `karma.conf.ts`, `cypress.config.ts`, `playwright.config.ts`.
2. **Test specs** — **basename-only** globs: `*.spec.ts`, `*.spec.tsx`,
   `*.test.ts`, `*.test.tsx`.
3. **Test support material** — exact **path-segment** names, whole subtree:
   `__tests__`, `__mocks__`, `__fixtures__`, `test-fixtures`, `test-helpers`,
   `test-utils`.

Anything else is **production**.

**Genuine production source is never excluded for an incidental word.**
Classification is by exact basename, basename-only glob, and whole path segment —
never by substring — so `latest.ts`, `contest.ts`, `testUtils.ts` and
`libs/core/src/protest/index.ts` all stay production (`*.test.ts` requires a
literal `.` before `test`). `*.config.ts` is deliberately **not** a wildcard,
because `app.config.ts` is genuine production source in common frameworks; tooling
config is therefore enumerated exhaustively instead. `testing/` is deliberately
**not** a blanket-excluded directory name, for the same reason.

**The frozen architectural layer scopes are unchanged.** The partition happens at
**source selection**, not at layer assignment: no layer path glob moved, no frozen
opportunity locator moved, and no `(scope, forbidden target)` decision changed.

**Manifest extension is additive only.** A manifest may declare
`dependency_policy.production_source_policy` to **add** further test/config
material for a particular repository. It can never re-admit an excluded class, so
this defect cannot be reintroduced by editing a manifest. The field is optional —
omitting it yields the baseline, so the partition is always in force — but a
**malformed** declaration fails closed (`INVALID_PRODUCTION_SOURCE_POLICY`) rather
than silently reverting to the baseline.

**Excluded files may still be examined descriptively.** Every scored finding
records `production_source.policy_id`, `production_file_count`,
`excluded_file_count` and the exact sorted `excluded_paths`, so a reviewer can
verify precisely what was held out. A checker may read that list for diagnostics.
Nothing derived from it may enter E1.

**Why an excluded edge can never enter the E1 numerator.** Excluded files are
removed from the file list handed to the resolver, so no edge is ever built from
them. An edge that does not exist cannot become a `VIOLATION` finding, cannot be
linked to a frozen `opportunity_id`, and cannot be counted in
`raw_violation_count`. There is no later filter to bypass — the exclusion is
structural, not a post-hoc suppression.

**Why an excluded file can never move the E1 denominator.**
`applicable_opportunity_count` is the **frozen manifest opportunity count** (§1a).
It is not a file count, not a count of matched imports, and not derived from the
snapshot at all. Adding a thousand test files, or deleting every test file, leaves
it identical. The only snapshot-dependent branch is `NOT_APPLICABLE`, which asks
whether the frozen scope carries **production** source material; a scope left with
test files only is correctly `NOT_APPLICABLE` (its production decision has no
material to evaluate) rather than falsely `SATISFIED`.

This is regression-locked end-to-end by mutation cases **M8-A**–**M8-F** in
`experiments/v2/oracle/tests/scopeAttribution.test.ts`. Revalidating the labelled
corpus and the private per-task opportunity sets under this policy is blocking
decision **`TD-B36`**; it is **not** discharged here.

## 2. Sensitivity and specificity (the oracle must be validated on labelled data)

- **Seeded-violation sensitivity** — a labelled corpus of **seeded** boundary
  violations (including alias-laundered and barrel-laundered ones) must be
  **detected** (recall). Seeded `@afci-bench/*` alias violations must be flagged.
- **Known-good diverse-solution specificity** — a set of **known-good, legitimate
  and diverse** solutions must **not** be flagged (no false positives / no style
  bias). Multiple correct shapes of a solution must all pass.
- **Legitimate alternatives frozen before confirmatory data** — the set of
  accepted legitimate solution shapes per task is **authored and frozen before**
  any confirmatory data is collected, so specificity is not tuned to the observed
  model behaviour.

## 3. Blindness and separation (the oracle must not know the condition)

- **Evaluator blindness to model and condition** — the oracle/acceptance
  evaluator receives the **patch and repository state only**; it must not receive,
  and must not be able to infer, the **model** or the **condition** (C1–C4) that
  produced the patch. Inputs are stripped/normalized to prevent leakage
  (e.g. no condition tag in paths or filenames handed to the evaluator).
- **Hidden evaluator separation** — the evaluator and its manifests run **outside**
  the coding model's workspace and feedback loop (see
  [`EXPERIMENTAL_CI_POLICY.md`](EXPERIMENTAL_CI_POLICY.md)); the model can run only
  `ci:agent`, never the oracle.

### 3a. Channel separation between architecture scoring and functional acceptance (`TD-B39`)

Blindness (§3) keeps the evaluator from knowing *which condition* produced a
patch. This keeps its **two scoring channels** from contaminating each other, and
fixes what each channel is permitted to observe. Normative statement:
[`HIDDEN_EVALUATOR_BOUNDARY.md`](HIDDEN_EVALUATOR_BOUNDARY.md) §9–§14.

- **Architecture scoring** is computed from the **production dependency graph**
  (§1a, §1b) and from nothing else. A functional acceptance result is **never** an
  input to an architecture finding.
- **Functional acceptance** is computed from **externally observable behaviour**:
  HTTP request/response, plus an explicitly declared, task-grounded application
  seam where the public task requires an externally emitted behaviour HTTP cannot
  carry. An architecture finding is **never** an input to a functional pass/fail.
- **Internal persistence and module state are not an acceptance oracle.** Hidden
  acceptance may not read implementation-specific persistence, module state,
  classes or source files to decide pass or fail, and may not seed preconditions
  through implementation modules. A precondition unreachable through the public
  interface is an unreachable-setup blocker (`TD-B31`).
- **Test isolation is not an acceptance oracle.** Cases are isolated by a freshly
  constructed application over a freshly evaluated module graph — never by an
  implementation-specific reset helper, and never in a way an assertion depends on.
- **Implementation independence is a validity requirement, not a courtesy.** A
  conforming solution with a different internal design must remain gradeable;
  otherwise the acceptance oracle measures conformity to one implementation rather
  than the behaviour the public task states, and its specificity result is not
  interpretable.

Migrating the existing hidden acceptance packages onto this boundary is **open**
(`TD-B39`) and is part of the same private re-authoring already tracked by
`TD-B05`/`TD-B14`/`TD-B27`.

## 4. Subjective rules (manual rubric + blinded double rating)

Some architecture rules cannot be automated. For these:

- a **manual rubric** defines each rule's satisfied/violated criteria;
- **blinded double rating** — two raters, blind to model and condition, rate
  independently;
- **inter-rater agreement target ≥ 0.70** (e.g. Cohen's/Fleiss' κ or an
  equivalent chance-corrected statistic) before the manual rule contributes to a
  confirmatory endpoint; disagreements are adjudicated and the rubric refined
  **before** confirmatory scoring, not after seeing effects.

**Manual assessments never enter E1.** Every rule that requires manual judgement
belongs to **CON-ACB** (broader architectural conformance: contract ownership,
port/interface placement, observability completeness, duplicated logic, general
business-logic placement) and is **secondary / manual evidence**. It contributes
**nothing** to `opportunity_accounting.violated_opportunity_count` or
`opportunity_accounting.applicable_opportunity_count`, is never pooled into E1 or
E2, and — even at κ ≥ 0.70 — supports only its own CON-ACB claim (`CL15`), never a
restatement of the E1 result
([`RESEARCH_QUESTIONS.md`](RESEARCH_QUESTIONS.md) CON-ACB;
[`MANUAL_RATING_PROTOCOL.md`](MANUAL_RATING_PROTOCOL.md)).

*(0.70 is the only agreement target stated; no other oracle threshold is invented
here.)*

## 5. Governance (manifests committed, hashed, and change-invalidating)

- **Manifests committed and content-hashed** — the rule catalog (`TD-B04`), the
  acceptance manifest (`TD-B05`), the legitimate-alternatives set, and the rubric
  are committed and **content-hashed**; each run's manifest records the
  `oracle_spec` / `acceptance_spec` / `guard_spec` versions it ran under
  (`run_manifest.schema.json` `protocol_versions`).
- **Post-run blinded false-positive / style-bias audit** — after runs, a
  **blinded** audit re-examines a sample of flagged and unflagged patches for
  false positives and style bias; findings feed the specificity record.
- **Manifest changes invalidate affected confirmatory runs** — if a manifest
  changes in a way that affects comparability, its version is bumped and the
  affected runs are marked `EXCL_PROTOCOL_MISMATCH` and dropped from the current
  frozen analysis set (see
  [`FAILURE_RERUN_POLICY.md`](FAILURE_RERUN_POLICY.md) §7); they are never
  silently rescored into a pooled result.

## 6. Endpoint alignment (pinned; no ambiguity permitted)

The oracle's **primary** output is the **dependency-direction violation rate per
applicable frozen opportunity** (CON-AC / endpoint **E1**). E1 measures **layered
dependency-direction conformance only** — the `AR-DEP-001…006` rule family — and
nothing wider.

**It measures that family only where the suite represents it.** The oracle's
*coverage* of the dependency matrix is a property of the checker; what E1 actually
observes is the set of **task-creatable** decisions the canonical substrate admits
— **3 decision clusters over 2 leaf rules and 2 source scopes**
([`DEPENDENCY_TASK_FEASIBILITY.md`](DEPENDENCY_TASK_FEASIBILITY.md)). An E1 result
therefore speaks to the **represented** decision families and **not automatically
to all architecture rules or all layer pairs**; that a leaf clause is implemented
and mechanically detectable is **not** evidence that the study measured it.

E1 is computed **only** from the frozen-opportunity accounting block of the blind
`architecture_finding.json`
([`architecture_finding.schema.json`](../../experiments/v2/schemas/architecture_finding.schema.json)),
exactly as pinned in
[`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md) §2.1:

| Role in E1 | Field |
|---|---|
| **Numerator** | `opportunity_accounting.violated_opportunity_count` |
| **Denominator / offset** | `opportunity_accounting.applicable_opportunity_count` |

Binding requirements on the oracle:

- **`applicable_rule_count` is NOT an E1 denominator and NOT an E1 offset.** It
  counts rules put in force, not exposure, and it moves when a rule is registered
  rather than when the patch has an opportunity to violate one. An oracle that
  reports a rate per applicable rule does not satisfy these requirements.
- **`satisfaction_proportion` is descriptive only.** The frozen-opportunity
  satisfaction proportion (E2) is a **descriptive transformation** of the same
  measurement (D8), never an independent confirmatory endpoint; the rule-based
  `satisfaction_proportion` field on `oracle_result.json` is a **legacy
  descriptive diagnostic** and must never be used as E1 or E2.
- **Manual and stub-rule assessments must not enter E1.** `AR-CONTRACT-001`,
  `AR-OBSERV-001`, `AR-CODE-001` and `AR-CHANGE-FOOTPRINT-001` are unimplemented
  stubs that report `UNIMPLEMENTED`, never PASS, and contribute **nothing** to
  either side of the rate. No manual adjudication may be pooled into the E1
  numerator or denominator.
- **Only implemented dependency-direction LEAF opportunities may enter E1.** A
  frozen opportunity enters `applicable_opportunity_count` only if its `rule_id`
  is an implemented member of the dependency-direction family and is in force for
  the manifest; the engine fails closed (`INVALID_OPPORTUNITY_RULE`) otherwise.
  The `AR-DEP-001` umbrella is additionally refused as a scored opportunity rule
  (`UMBRELLA_OPPORTUNITY_RULE`): it may expand raw exposure through
  `applicable_rule_ids`, but the denominator is built only from leaf clauses
  (§1a).
- **The `observability` source scope has no leaf rule and is umbrella-only.**
  `leafRuleFor('observability', target)` returns `null` for **every** target
  (`experiments/v2/oracle/src/checkers/dependencyDirection.ts`), so an
  `observability`-sourced forbidden edge is covered **only** by the `AR-DEP-001`
  umbrella: it can appear in raw exposure and in the descriptive raw-violation
  series, and it can **never** back a scored opportunity — the engine refuses one
  with `OPPORTUNITY_RULE_SCOPE_MISMATCH` regardless of how the task or manifest is
  worded. This records existing, already-tested behaviour; **no oracle behaviour
  changes with it**.
- **E1 is computed from the PRODUCTION dependency graph only.** Test specs, test
  support material and tooling/build configuration TypeScript are partitioned out
  **before** any import edge is resolved (§1b), so a dependency introduced solely
  for a test, a fixture, a test helper or a tool contributes **nothing** to the
  numerator, and because the denominator is the frozen opportunity count, adding
  or removing such files cannot change `applicable_opportunity_count` either.
  Excluded files remain visible descriptively on
  `production_source.excluded_paths`; nothing derived from them enters E1.
- **The denominator is scope-anchored and model-independent.** Opportunities are
  attributed by frozen architectural scope, so `applicable_opportunity_count` does
  not move when the model creates files, edits files, adds imports, or enlarges
  the patch; and `violated_opportunity_count` counts each frozen decision at most
  once (§1a).
- **Broader architectural constructs belong to CON-ACB.** Contract ownership,
  port/interface placement, observability completeness, duplicated logic and
  general business-logic placement are **not** measured by this oracle; they are
  pre-registered **secondary / manual** evidence (§4), κ ≥ 0.70 gated, reported
  under `CL15` and never as an E1 result (gate **G8**).
- **`raw_violation_count` is a separate descriptive diagnostic series**, reported
  alongside E1 and never substituted into it. Under scope attribution it exceeds
  `violated_opportunity_count` whenever one frozen decision carries several
  forbidden edges, or an edge falls outside every frozen decision; that is
  expected, not a defect signal.
- **A zero-exposure task is structurally ineligible, not zero-violation.** A task
  whose `applicable_opportunity_count` is `0` is excluded from the E1 model as
  out-of-exposure; it is **not** entered with a zero numerator and **not**
  recorded as a failed run.
- **Analysis eligibility is manifest-bound.** Every evaluator manifest carries
  `e1_analysis_eligibility` ∈ {`scored`, `functional-only`, `inactive-reserve`}
  which must match the approved public task index; the integrity gates in §6a are
  fail-closed.

The acceptance evaluator's **hidden acceptance-test pass proportion** is the
principal completeness outcome (CON-TC / E3), and it admits E1-ineligible
(`functional-only`) tasks.

### 6a. Manifest eligibility integrity (fail-closed)

Every evaluator manifest carries a **required** `e1_analysis_eligibility` field.
A manifest that omits it, or carries a value outside
{`scored`, `functional-only`, `inactive-reserve`}, is refused by the loader
(`ELIGIBILITY_MISSING`) — it is never defaulted, so a manifest authored before
this decision cannot be scored under an assumed eligibility.

The oracle then refuses to score a manifest whose declared analysis eligibility is
inconsistent with its frozen opportunity set or with the approved public task
index. The five gates, enforced by the engine and not merely by schema:

1. **Index agreement** — the manifest's `e1_analysis_eligibility` must equal the
   value recorded for that `task_id` in
   [`PILOT_PUBLIC_TASK_MATRIX.csv`](PILOT_PUBLIC_TASK_MATRIX.csv) /
   `experiments/v2/tasks/public/TASK_INDEX.csv`
   (`ELIGIBILITY_TASK_INDEX_MISMATCH`).
2. **`functional-only` contributes no denominator** — it must carry no
   dependency-direction opportunity (`ELIGIBILITY_DENOMINATOR_CONFLICT`).
3. **`inactive-reserve` enters no E1 run or aggregation** unless a separately
   recorded pre-run activation decision changes its eligibility
   (`ELIGIBILITY_RESERVE_INACTIVE`). A reserve **may retain draft opportunities**;
   they are **analytically inactive** until formal activation, and the engine
   reports `applicable_opportunity_count = 0` for it rather than requiring their
   deletion.
4. **`scored` requires a valid non-zero frozen denominator** before entering E1
   (`ELIGIBILITY_SCORED_WITHOUT_OPPORTUNITIES`).
5. **Any eligibility mismatch is an explicit lifecycle/manifest-integrity
   failure**, never a silent rescore or a silent zero.

> **Private manifests require migration.** The `e1_analysis_eligibility` field is
> introduced by this public change. The per-task manifests in the separate private
> evaluator repository were **not** touched here and must be migrated to carry the
> field before any of them can be scored; until then they fail closed on the
> gates above. Migration is part of the private manifest re-authoring already
> tracked by `TD-B05`/`TD-B14` (see [`OPEN_DECISIONS.md`](OPEN_DECISIONS.md)).

## 7. Status

This package delivers the **oracle framework** and the **dependency-direction
reference checker** with **synthetic unit validation**. It does **not** validate
the oracle on a labelled/mutation/manual corpus and authors **no** task-specific
material. Gates **G1** and **G6** and blocking decisions **`TD-B04`**,
**`TD-B05`**, **`TD-B12`** remain **open**; none is resolved here.

**Implemented in this package**

- Oracle framework — deterministic, blind (no condition/model), fail-closed —
  `experiments/v2/oracle/` (TypeScript compiler API; not regex import matching).
- Dependency-direction reference checker (`AR-DEP-001` family): alias, relative,
  index/barrel, and re-export resolution; moved/deleted-code handling; whole-
  repository (not added-line-only) evaluation. It resolves the repository's real
  `@afci-bench/*` aliases and barrels; the committed self-scan test
  (`experiments/v2/oracle/tests/realRepo.test.ts`) scores the real repository
  source as `CONFORMANT` and confirms the sanctioned api→features→core re-export
  is not false-flagged.
- Machine-checkable rule catalog (`TD-B04`, **partial**) —
  `ARCHITECTURE_RULE_CATALOG.yml` + `architecture_rule_catalog.schema.json` +
  `ARCHITECTURE_RULE_TRACEABILITY.csv`, grounded in the real `.eslintrc.json`
  depConstraints.
- Synthetic unit validation — `experiments/v2/oracle/fixtures/` + Jest: seeded
  alias/relative/barrel violations detected; known-good and a legitimate
  alternative not flagged; comments/strings create no false import; moved/deleted
  handled; deterministic ordering; blindness to condition/model labels; unknown
  and unimplemented rules cannot report PASS; malformed alias config fails closed.
- Scope-attribution and production-source mutation corpus (**M0–M8**) —
  `experiments/v2/oracle/tests/scopeAttribution.test.ts`: end-to-end scoring
  against synthetic frozen manifests built inside the test process (no repository
  manifest is altered or frozen). **M0–M7** prove §1a — new-file and moved-file
  violations are attributed to the same frozen opportunity, anchor deletion
  cannot hide a live violation, `NOT_APPLICABLE` needs an absent scope, one
  decision contributes at most one violation, the denominator is invariant across
  every mutant, and the umbrella/locator integrity gates fail closed.
  **M8-A–M8-F** prove §1b — a prohibited import in a new **production** file still
  violates its frozen opportunity, while the same import in a `*.spec.ts`, under
  `__tests__/`, or in `jest.config.ts` does not; a conforming production file whose
  *test* carries the forbidden dependency stays `SATISFIED`; a forbidden production
  dependency surrounded by harmless test dependencies violates **exactly once**;
  and adding test/config files moves neither `applicable_opportunity_count` nor the
  numerator.
- Production-source policy (§1b) — `experiments/v2/oracle/src/productionSource.ts`:
  baseline `PSP-V1`, additive-only manifest extension, fail-closed on a malformed
  declaration (`INVALID_PRODUCTION_SOURCE_POLICY`), and per-result audit trail on
  `production_source`.
- Hidden-evaluator boundary and mount policy
  ([`HIDDEN_EVALUATOR_BOUNDARY.md`](HIDDEN_EVALUATOR_BOUNDARY.md),
  [`EVALUATOR_MOUNT_POLICY.md`](EVALUATOR_MOUNT_POLICY.md)) with a machine-checkable
  mount-rejection test and a coding-worktree-cleanliness test.
- Manual-rubric foundation ([`MANUAL_ORACLE_RUBRIC.md`](MANUAL_ORACLE_RUBRIC.md),
  [`MANUAL_RATING_PROTOCOL.md`](MANUAL_RATING_PROTOCOL.md)).

**Future — NOT built here; required before G1/G6**

- Known-good **diverse-solution** specificity corpus (multiple correct shapes per
  task); only a single legitimate-alternative fixture exists so far.
- Seeded **multi-category mutation** corpus covering the contract, observability,
  and coding-discipline rules (currently explicit unimplemented stubs), with
  precision/recall on a labelled set.
- **Manual inter-rater** validation (two blinded raters, κ ≥ 0.70) for the manual
  rules.
- **Task-specific manifest** validation: authored per-task frozen manifests,
  fixed-opportunity denominators, hidden acceptance tests, and legitimate
  alternatives (`TD-B05`), validated end-to-end.
- Acceptance oracle and guard precision/recall on the full labelled corpus.

These requirements remain the acceptance bar for gates **G1** and **G6** and for
blocking decisions **`TD-B04`**, **`TD-B05`**, **`TD-B12`**. No oracle threshold
is invented here beyond the stated κ ≥ 0.70.
