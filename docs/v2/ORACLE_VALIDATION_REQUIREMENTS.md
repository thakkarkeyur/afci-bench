# docs/v2 — Oracle Validation Requirements

Status: **development requirements for study v2**. Specifies what the conformance
oracle and acceptance evaluator must satisfy **before** any confirmatory data is
scored, so that a measured architecture-violation rate is valid and reliable
(directly answering the v1 defects: a guard blind to `@afci-bench/*` aliases that
flagged nothing, a saturated `ci_pass`, and a constant `layer_jaccard`).
Development artifact only: it does **not** freeze the final benchmark
configuration and authorizes **no** paid model run.

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

## 4. Subjective rules (manual rubric + blinded double rating)

Some architecture rules cannot be automated. For these:

- a **manual rubric** defines each rule's satisfied/violated criteria;
- **blinded double rating** — two raters, blind to model and condition, rate
  independently;
- **inter-rater agreement target ≥ 0.70** (e.g. Cohen's/Fleiss' κ or an
  equivalent chance-corrected statistic) before the manual rule contributes to a
  confirmatory endpoint; disagreements are adjudicated and the rubric refined
  **before** confirmatory scoring, not after seeing effects.

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

## 6. Endpoint alignment

The oracle's **primary** output is the **architecture-violation rate per
applicable rule/opportunity** (CON-AC / endpoint E1). Raw violation counts are
retained; **applicable-rule satisfaction is a descriptive transformation** of the
same measurement, not an independent confirmatory endpoint (D8). The acceptance
evaluator's **hidden acceptance-test pass proportion** is the principal
completeness outcome (CON-TC / E3).

## 7. Status

The oracle, guard, rule catalog, acceptance manifest, labelled corpus, and
legitimate-alternatives set **do not exist yet** and are **not built in this work
package**. These requirements are the acceptance bar for gates **G1** and **G6**
and for blocking decisions **`TD-B04`**, **`TD-B05`**, **`TD-B12`**.
