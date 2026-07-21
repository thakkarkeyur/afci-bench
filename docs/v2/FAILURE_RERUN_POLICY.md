# docs/v2 — Failure and Rerun Policy

Status: **development protocol for study v2**. Defines exactly which failures may
be rerun and which outcomes are **data that must never be silently rerun**, so
that run independence and the integrity of the frozen result set are provable.
Development artifact only: it does **not** freeze the final benchmark
configuration and authorizes **no** paid model run.

This policy exists to prevent the v1 defects of non-independent, hand-curated
runs. Its reason codes are reused by the run schema
[`experiments/v2/schemas/run_manifest.schema.json`](../../experiments/v2/schemas/run_manifest.schema.json)
(`exit_reason`, `exclusion_status`, `rerun`).

---

## 1. Governing principle

> A **valid model outcome is data.** A bad outcome (incomplete work, failing
> tests, an architecture violation) is a *result to record*, never a reason to
> rerun. Only **infrastructure / setup failures** — where the harness, not the
> model, failed — may be rerun, and even then **both** the original and the
> replacement attempt are retained and logged.

No outcome is ever improved by re-prompting, hand-editing, or quietly discarding
and retrying until a "good" result appears.

---

## 2. Infrastructure / setup failures — RERUN-ELIGIBLE (both attempts logged)

These indicate the **harness or environment** failed before the model produced a
scorable outcome. They may be rerun; the original aborted attempt **and** its
replacement are both logged and linked (§5).

| Reason code | Failure |
|---|---|
| `INFRA_AUTH_OUTAGE` | Authentication outage (provider auth unavailable) |
| `INFRA_API_TRANSPORT` | API transport failure (network / 5xx / dropped stream) |
| `INFRA_WORKTREE_CORRUPT` | Corrupted worktree (base checkout / isolation broke) |
| `INFRA_RUNNER_CRASH` | Runner crash (harness process died) |
| `INFRA_EVALUATOR_MOUNT` | Evaluator mount failure (oracle/guard container/mount unavailable) |
| `INFRA_MISSING_ARTIFACT` | A required artifact is missing **because of a harness failure** |
| `SETUP_CONTAMINATED` | Context audit verdict `CONTAMINATED` (isolation setup defect; see [`CONDITIONS.md`](CONDITIONS.md) §4) |

Rules:
- A rerun is permitted **only** if the exit is one of the codes above.
- The replacement starts from the **same** clean base SHA, condition, task,
  model, protocol versions, and total budget as the original.
- `INFRA_MISSING_ARTIFACT` applies **only** when the artifact is absent due to
  harness failure. A missing artifact that reflects a model outcome
  (e.g. `NO_PATCH`) is **not** infrastructure and is **not** rerun (§3).

---

## 3. Valid model outcomes — MUST NOT be silently rerun (recorded as data)

These are outcomes of the model's own behaviour. Each is **recorded** and kept in
the analysis set; none is a rerun trigger.

| Reason code | Outcome |
|---|---|
| `INCOMPLETE_IMPLEMENTATION` | Incomplete implementation |
| `VISIBLE_CI_FAIL` | Failing **visible** CI |
| `HIDDEN_TEST_FAIL` | Hidden acceptance-test failure |
| `ARCH_VIOLATION` | Architecture violation (conformance failure) |
| `TIMEOUT` | Wall-clock timeout |
| `BUDGET_TOKENS_EXHAUSTED` | Token budget exhausted |
| `BUDGET_TURNS_EXHAUSTED` | Turn budget exhausted |
| `REFUSAL` | Model refusal |
| `INVALID_CODE` | Invalid / non-building code |
| `NO_PATCH` | No patch produced |
| `COMPLETED` | Ran to completion (then scored by the oracle/guard) |

A poor evaluation result (arch violation, hidden-test failure, visible-CI
failure) is stored in the oracle / acceptance / guard result records, **not** as
a rerun.

---

## 4. Exclusion reasons (what may be dropped from the confirmatory analysis)

A run may be **excluded** from the confirmatory analysis set **only** for a
reason on this closed list, and every exclusion is logged with its code, the
excluding person/role, and a timestamp:

| Exclusion code | Meaning |
|---|---|
| `EXCL_NONE` | Not excluded (default) |
| `EXCL_INFRA_SUPERSEDED` | An infrastructure-failed attempt superseded by a logged replacement (§2) |
| `EXCL_CONTAMINATED` | Context audit `CONTAMINATED` (§2 `SETUP_CONTAMINATED`) |
| `EXCL_PROTOCOL_MISMATCH` | Produced under a superseded protocol version (§7) |
| `EXCL_PREREGISTERED_RULE` | Dropped by a **pre-registered** rule fixed before data collection (documented in [`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md)) |

**A valid model outcome (§3) is NEVER an exclusion reason.** "The result was bad"
is not on this list. Exploratory analyses may report differently but must state
any deviation explicitly.

---

## 5. Replacement-run linkage

Every replacement run records, in its manifest:

- `rerun.is_replacement = true`;
- `rerun.replaces_run_id = <original run id>`;
- `rerun.reason_code = <one of the §2 infrastructure codes>`;
- the original run records `rerun.replaced_by_run_id = <replacement run id>` and
  `exclusion_status = EXCL_INFRA_SUPERSEDED`.

Both records are retained in the frozen data. The confirmatory analysis uses the
**single** non-superseded attempt per (task, condition, reset-state, model,
repetition) cell; the linkage makes every rerun auditable. There is no limit-
free retry loop: repeated infrastructure failure on the same cell is escalated,
not silently re-attempted (escalation policy = open decision `TD-N06`).

---

## 6. Manual-intervention prohibition

For any run counted as evidence:

- **No** human edits to the model's patch, tests, or output.
- **No** re-prompting, hint injection, or "nudging" beyond the fixed
  condition context and reset protocol.
- **No** hand-fixing to make visible CI or hidden tests pass.
- **No** selecting the "better" of several unlinked attempts.

The run is exactly what the model produced under the fixed condition. Any manual
touch voids the run (it becomes non-evidence and is logged as such).

---

## 7. Data-freeze and protocol-version invalidation

**Data freeze.** Once a run's records enter the frozen result set they are
**immutable**. Corrections are made only by adding **new** records (with linkage),
never by editing or deleting frozen rows. The frozen set is identified by a
content hash manifest.

**Protocol versions.** Each run stamps the versions of the protocols it ran under
(condition spec, oracle/acceptance spec, reset protocol, model-execution config,
guard spec — see the run schema `protocol_versions`). If any of these changes in
a way that affects comparability:

1. the changed protocol's version is **bumped**;
2. runs produced under **different** protocol versions are **not pooled** in one
   confirmatory analysis;
3. superseded-protocol runs are **retained** but marked
   `exclusion_status = EXCL_PROTOCOL_MISMATCH` and dropped from the current
   frozen analysis set;
4. the change and its rationale are recorded in
   [`OPEN_DECISIONS.md`](OPEN_DECISIONS.md) / the reviewer-response log.

This guarantees that a mid-study protocol change can never silently contaminate a
pooled result.
