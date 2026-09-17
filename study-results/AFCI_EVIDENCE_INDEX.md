# AFCI-Bench — evidence index

Purpose: let a reader walk **summary number → analysis artifact → run records →
raw evidence** for every figure in this package.

**Repository anchors**

| what | value |
| --- | --- |
| public repo HEAD (`study-v2`) | `c544cc87a4f72dc33763035b0ba2c589ad8e72db` |
| public repo `main` (v1 base, tag `paper-v0`) | `2adc8741acad7ea5423f0bf3d9ad821ff023a35f` |
| private evaluator repo HEAD | `e1154227008101f7054c61c33247e5d2c7c52e59` |
| governed substrate commit | `630d3180af0d02a86330dfb599f559e78df65e94` |
| governed substrate content hash | `0198d76c189f38589e872cab4305527c08e86ef736e1550e428e05f9178060f3` (49 entries) |

The private repository was **read only** for evidence lookup. Nothing in it was
modified and nothing is pushed.

---

## Governance documents and their hashes

SHA-256 of the file as committed on `study-v2` @ `c544cc87`.

| document | sha256 |
| --- | --- |
| `docs/v2/ARCHITECTURE_CONTEXT.md` (**the MAD**) | `bf6f32b162a23b851596d8b489d938bef10d0b8616a50dcc039873d12ffa7a4d` |
| `docs/v2/AFCI_EFFICIENCY_PILOT_RUN_PLAN.json` | `0038cd8b563ea804f4887d21cb37ceddb3a8f7632c4dd2315c260d3a9af95767` |
| `docs/v2/AFCI_EFFICIENCY_PILOT_DECISION.md` | `e3110d9a90009be180e76fb30368179529c187263ab823391635990b2cc0d8df` |
| `docs/v2/AFCI_EFFICIENCY_PILOT_ATTEMPT_2_EXECUTION_PLAN.json` | `562415031c04b0673c54ac352a4ca35a66e885023aa212cedc284da0c65a087e` |
| `docs/v2/AFCI_EFFICIENCY_PILOT_ATTEMPT_1_ABORT_DECISION.md` | `21547ed7d3f86e3c6793e830ca128ffe7bf3c6665ada07568c99d2c493a66445` |
| `docs/v2/AFCI_EFFICIENCY_PILOT_ATTEMPT_1_EVIDENCE_INVENTORY.json` | `9985860fb3b7a5842e676cc1c66c876e712ea93a196999457d711332ba12683f` |
| `docs/v2/V2_QUALIFICATION_DIAGNOSTIC_DECISION.md` | `e5bcebe5717ab301e9fe27565ddd9593677f56d5c6a78399c21ea1e260416385` |
| `docs/v2/PT08_DIAGNOSTIC_OUTCOME_AND_DISPOSITION.md` | `3658dd21b2ac5b829df92bb8d4da5a8ad71262b6c36bd0c4f7ccbd1c1b94515e` |

The MAD hash is independently corroborated: the frozen run plan records
`architecture_context_sha256 = bf6f32b1…`, and hashing the file on disk today
reproduces it.

### Task body hashes (public task SHA-256)

| task | sha256 | used by |
| --- | --- | --- |
| PT01 | `6c938822fe19cd6e87942a6ee24ec8f604c0883da1b7f80d45216be35d7c9c39` | efficiency pilot |
| PT04 | `f349b150b1d8fe5676fed8460b1840b988ee2bb0a78b1966ef82ae9ce9c8a9b5` | efficiency pilot |
| PT07 | `557caed09420354efbc823c8b72e54b0760ac72847aba0d9c07d99e37ff7d2d7` | efficiency pilot |
| PT08 | `a31bb515b79cc1e211a662de2a8761c97082dd8bf266ee5b4f660981435badf2` | PT08 diagnostic |
| PT09 | `bac32dc0e7163c9ab1816ac6eea6c98738092cca5cf56715e280f1ec1c0ac44c` | qualification |
| PT10 | `1b1fe29881b3c9f309939df042272b03164fb3baae878c64345e75edddf36b86` | qualification |

Every run record carries the hash of the task body it was actually handed, and
the runner refuses on a mismatch.

---

## 1. `V1_ORIGINAL`

| | |
| --- | --- |
| status | COMPLETE, PUBLISHED, superseded |
| included in analysis | **NO** — historical/exploratory only |
| model | "Opus 7" (48/48 run records agree) |
| executed | 2026-04-20T19:54:46Z → 2026-04-23T22:23:23Z |
| base tag | `paper-v0` (48/48) |
| CI | `ci_exit_code = 0` in 48/48 |

**Evidence lives on git branch `rerun-v1-opus7-artifacts`** (never checked out,
never merged). Read it with `git show <branch>:<path>`.

| role | path | git blob |
| --- | --- | --- |
| **run-level records** | `experiments/runs_v1/<TASK>/<COND>/{run_meta,metrics,conformance}.json`, `patch.diff`, `prompt.md`, `ci_output.txt` | — (288 files) |
| **aggregate analysis** | `experiments/paper/results_v1.csv` | `0d350eb262b49385f290d0a9df6693b34ba3d919` |
| reset-drift analysis | `experiments/paper/drift_true_v1_codeonly.csv` | `1d2891abd3447836c6118df7105fe8830ecc2396` |
| drift summary | `experiments/paper/drift_summary_v1_codeonly.csv` | `5b2dead72374a06e8ed16513b84337e0da8a6a6c` |
| completeness summary | `experiments/paper/completeness_summary_v1.csv` | `4c71a84cd69ec26b34d34f108333a90b5da92334` |
| conformance (**invalid**) | `experiments/paper/conformance_summary_v1.csv` | `7f2d79814c5d84198133f3350cb32d45e00eb9a4` |
| taskwise churn | `experiments/paper/completeness_taskwise_v1.csv` | `af1d74fc678829f57433e496619dcf3820a1580e` |
| published table | `paper/tables/table2c_true_drift_codeonly_v1.tex` | `50938f83d6379761a6b042a34d13455cf46282a2` |
| published table | `paper/tables/table_completeness_v1.tex` | `cf5e47cd0769ca84db8a2637c1c31880ba22b158` |
| harness (**did not invoke a model**) | `experiments/scripts/run_one_v1.sh` | `b72abb2d2afd3bb04db9975dda83510f15699a8b` |

**Governance:** `archive/v1/REFERENCE_MANIFEST.yml` on `study-v2` — the immutability
statement and limitations L1–L7. **Release:** GitHub `ase2026-artifacts-v1` @
`1ba21ad75dacbac5eb87d354a490b088078c30da`. **DOI:** `10.5281/zenodo.19757261`.

**Trace an example.** "+65.7% code churn" →
[`01_v1_original_study/v1_headline_recomputed.csv`](01_v1_original_study/v1_headline_recomputed.csv)
→ [`01_v1_original_study/v1_taskwise_churn_recomputed.csv`](01_v1_original_study/v1_taskwise_churn_recomputed.csv)
→ `results_v1.csv` columns `code_additions + code_deletions` for
`condition ∈ {baseline, afci}` → per-run `metrics.json` under
`experiments/runs_v1/<TASK>/<COND>/`.

---

## 2. `V2_PT08_DIAGNOSTIC`

| | |
| --- | --- |
| status | COMPLETE |
| included in analysis | **NO** — diagnostic only |
| authority | `SL-PT08-01` (diagnostic), `SL-PT08-06` (scoped freeze), `SL-PT08-07` (disposition) |
| executed | 2026-09-13, 06:28–06:35 UTC |
| model / runtime | `claude-sonnet-5`, CLI `2.1.229`, PINNED, identity VALIDATED 3/3 |
| context audit | CLEAN 3/3 |
| artifact root | `D:\pt08-diagnostic` (outside both repositories) |

| role | path |
| --- | --- |
| run records | `D:\pt08-diagnostic\runs\R{1,2,3}\<run_id>\run_record.json` |
| runner state summaries | `D:\pt08-diagnostic\runs\R{1,2,3}\driver_summary.json` |
| **scoring analysis** | `D:\pt08-diagnostic\scoring\R{1,2,3}\scoring_summary.json` |
| architecture findings | `D:\pt08-diagnostic\scoring\R{1,2,3}\architecture_finding.json` |
| runtime evidence | `…\<run_id>\runtime_evidence.jsonl` |
| frozen evaluator mount | `D:\pt08-diagnostic\control\mount\PT08.diagnostic-frozen.evaluator_manifest.json` |
| derived table | [`02_pt08_diagnostic/pt08_diagnostic_runs.csv`](02_pt08_diagnostic/pt08_diagnostic_runs.csv) |
| governance | `docs/v2/PT08_DIAGNOSTIC_OUTCOME_AND_DISPOSITION.md` |

**Evaluator manifest provenance.** Shipped private manifest
`bdb4f0bb68a366ddef93f712c2325092f97387c2765dc94a78037ca6c1768f3b`
(`status=review`, unmodified) → derived diagnostic-scoped mount
`9fdbb347aa936ddc98d19737937b954c0a925ab1e13ace6c385dce0b8bb098dc`
(`status=frozen`). Exactly two lifecycle fields differ; **zero semantic fields
differ**; never committed.

**Run-id caveat.** All three repetitions minted the identical run id
`pt08-difficulty-diagnostic-pt08-c1-real-97c5ca96498e` (pre-`SL-RUNID-01`
defect). They stayed separable only because each was given its own
`--artifact-root`. Distinguish them by `label` (R1/R2/R3) and `session_id`:
`85e54e73…`, `1f970b85…`, `b3643495…`.

**Do not misread `worktree_content_hash`.** `da7a6795…` is identical across all
three runs because it is the **prepared (input) worktree** hash, recorded before
model invocation. It says the three runs got identical inputs. It says nothing
about their outputs.

---

## 3. `V2_PT09_QUALIFICATION` / `V2_PT10_QUALIFICATION`

| | |
| --- | --- |
| status | COMPLETE |
| included in analysis | **NO** — qualification / instrument validation only |
| authority | `SL-V2-QUAL-01` |
| model / runtime | `claude-sonnet-5`, CLI `2.1.229`, identity VALIDATED 6/6 |
| context audit | CLEAN 6/6 |
| artifact root | `D:\afci-v2-qual` |

| role | path |
| --- | --- |
| run records | `D:\afci-v2-qual\runs\instrument-qualification-diagnostic-pt{09,10}-c1-real-r{1,2,3}-<hash>\run_record.json` |
| runtime evidence | same directory, `runtime_evidence.jsonl` |
| captured worktrees | same directory, `worktree_post_run\` (49 entries each) |
| **scoring analysis** | `D:\afci-v2-qual\score\pt{09,10}-r{1,2,3}.json` |
| per-channel detail | `D:\afci-v2-qual\score\pt{09,10}-r{1,2,3}\{functional,architecture}\` |
| infrastructure-invalid attempt | `D:\afci-v2-qual\invalid\pt09-r1-attempt-1-INFRA_RUNNER_CRASH\` |
| derived tables | [`03_pt09_pt10_qualification/`](03_pt09_pt10_qualification/) |
| governance | `docs/v2/V2_QUALIFICATION_DIAGNOSTIC_DECISION.md`, `docs/v2/QUALIFICATION_CANDIDATE_CONSTRUCTION.md` |

Run ids: `…pt09…r1-d5498c8f4eca`, `r2-0ba9ebeb6c49`, `r3-6378df59d9ec`;
`…pt10…r1-f9390db4a505`, `r2-30d1570b59b7`, `r3-8f809ab6ee92` — six distinct ids,
the `SL-RUNID-01` fix working.

**Evaluator manifest provenance.** PT10 shipped
`ffcab0ef61daafbd7562f5226c4056ada3ab4a7283adc39249d56edf45edbab6` → derived
`fdc9114806fdefade12d9a091eb9f26c55b09e755af54025bbb228c2a888c952`. Both private
manifests remain `status=review` and unmodified.

**Trace the one violation.** "PT10 1/3" → `qualification_classification.csv` →
`D:\afci-v2-qual\score\pt10-r3.json` → `architecture.target_findings[0]`:
`AR-DEP-005::viol::apps/api/src/app.ts::4::1::import`, evidence
`import '@afci-bench/core'` at `apps/api/src/app.ts:4:1` → the captured worktree
under `…pt10-c1-real-r3-8f809ab6ee92\worktree_post_run\`.

---

## 4. `V2_EFF_ATTEMPT1` — aborted

| | |
| --- | --- |
| status | `ABORTED_INFRASTRUCTURE_ATTEMPT` |
| included in analysis | **NO — excluded wholesale, including the 7 intact rows** |
| authority | `SL-V2-EFF-ABORT-01` |
| artifact root | `D:\afci-runs\obs`; operator logs `D:\afci-runs\logs\seq-0{1..9}.log` |

| role | path |
| --- | --- |
| **governed evidence inventory** | `docs/v2/AFCI_EFFICIENCY_PILOT_ATTEMPT_1_EVIDENCE_INVENTORY.json` |
| abort decision | `docs/v2/AFCI_EFFICIENCY_PILOT_ATTEMPT_1_ABORT_DECISION.md` |
| restart authorisation | `docs/v2/AFCI_EFFICIENCY_PILOT_RESTART_AUTHORIZATION.md` |
| per-row artifacts | `D:\afci-runs\obs\afci-efficiency-pilot-…\` (9 rows, 8 directories) |
| copy + derived table | [`04_efficiency_attempt_1_aborted/`](04_efficiency_attempt_1_aborted/) |

The inventory is derived **from the artifacts**, not from the decision prose, so
a disagreement between the two is a mechanical failure rather than a reading. It
carries, per row: derived run id, artifact directory, whether a model was
invoked, which runtime-evidence streams exist and their SHA-256, whether a
governed record survives and which row it is attributable to, the collision
partner, and the row status.

**There is no analysis artifact for Attempt 1, because no analysis was ever
performed** — no token-ratio analysis, no C1-vs-C4 comparison, no pilot outcome,
no continuation-threshold evaluation. The abort rests on 18 deterministic
identity collisions alone.

**The two damaged rows share one directory**
(`…pt01-c4-real-r2-d0837c0e6305`): sequence 6 (`PT01/C4/RESET/R2`,
`DAMAGED_GOVERNED_RECORD_OVERWRITTEN`) and sequence 9 (`PT01/C4/NON_RESET/R2`,
`DAMAGED_POST_DELIVERY_COLLIDING_OBSERVATION`). They are inventoried separately
and their artifacts attributed individually, because "the directory contains a
captured worktree" is true for both and answers the wrong question.

---

## 5. `V2_EFF_ATTEMPT2` — completed

| | |
| --- | --- |
| status | COMPLETE |
| included in analysis | **YES** — and still **non-confirmatory** |
| authority | `SL-V2-EFF-01` (design), `SL-V2-EFF-RESTART-01` (this execution) |
| executed | 2026-09-16T14:28:58Z → 2026-09-16T20:02:54Z |
| model / runtime | `claude-sonnet-5`, CLI `2.1.229` |
| artifact root | `D:\afci-runs\attempt-2` |
| sterile base | `D:\afci-sterile\attempt-2` |

### Plan and identity

| what | value |
| --- | --- |
| scientific run plan | `docs/v2/AFCI_EFFICIENCY_PILOT_RUN_PLAN.json`, sha256 `0038cd8b…` |
| execution plan | `docs/v2/AFCI_EFFICIENCY_PILOT_ATTEMPT_2_EXECUTION_PLAN.json`, sha256 `562415…` |
| scientific projection sha256 | `417c32d51ae16f09c615db90fd2741155d67d233dddf149cca00bf25fd1386c5` |
| schedule seed | `AFCI_EFFICIENCY_PILOT_V1_20260914` (SHA-256 ordering; no language RNG) |
| run-id algorithm | version **2** — `run_purpose, task_id, condition, task_sha256, substrate_content_hash, mode, repetition, reset_state, execution_attempt` |
| `reuses_any_attempt_1_observation` | **false** |
| turn budgets | non-reset 64; pre-reset 32; post-reset 32 |

### Artifacts

| role | path |
| --- | --- |
| **run records (36)** | `D:\afci-runs\attempt-2\afci-efficiency-pilot-…-a2-<hash>\run_record.json` |
| runtime evidence, non-reset | same directory, `runtime_evidence.jsonl` |
| runtime evidence, reset | same directory, `phase_a_runtime_evidence.jsonl` + `phase_b_runtime_evidence.jsonl` |
| functional evaluation | same directory, `functional_evaluation.json`, `functional_evaluation_result.json` |
| captured worktrees | same directory, `worktree_post_run\` |
| context audits | same directory, `context_audit.json` (+ `phase_{a,b}_context_audit.json`) |
| operator logs | `D:\afci-runs\attempt-2\logs\seq-{01..36}.log` |
| operator progress | `attempt2_progress.json` (seq 1–12), `attempt2_progress_from_13.json` (seq 13–36) |
| dry-run readiness records (**not observations**) | `D:\afci-runs\attempt-2\readiness-context-audit\` (12) |

### Analysis

| role | path |
| --- | --- |
| **frozen analysis code** | `experiments/v2/harness/efficiency_pilot_analysis.py` |
| **analysis report (this package)** | [`05_efficiency_attempt_2_completed/efficiency_pilot_frozen_analysis_report.json`](05_efficiency_attempt_2_completed/efficiency_pilot_frozen_analysis_report.json) |
| derived tables | [`05_efficiency_attempt_2_completed/`](05_efficiency_attempt_2_completed/) |
| functional-validity source | `record.functional_evaluation.functional_valid` — **and nowhere else** |
| governance | `docs/v2/AFCI_EFFICIENCY_PILOT_DECISION.md` §10–§11 |

The report asserts on its face `execution_attempt: 2` and
`aborted_execution_attempt_excluded: 1`. The analysis refuses a record set
spanning attempts (`ANALYSIS_SPANS_EXECUTION_ATTEMPTS`) and refuses any Attempt-1
record even alone (`ANALYSIS_INCLUDES_ABORTED_ATTEMPT`).

### Trace the headline number

"median C4/C1 input tokens = 1.4014" →
[`attempt2_endpoint_ratios.csv`](05_efficiency_attempt_2_completed/attempt2_endpoint_ratios.csv)
→ [`attempt2_primary_pairs.csv`](05_efficiency_attempt_2_completed/attempt2_primary_pairs.csv)
(16 rows; median of the 16 ratios) →
`efficiency_pilot_frozen_analysis_report.json` → `primary_endpoint.pairs` →
each run's `run_record.json` → `efficiency.usage.TOTAL_INPUT_TOKENS` →
`runtime_evidence.jsonl` terminal result event (or, for a reset phase A, the
per-message reconstruction).

### Sequence → run id

The full map is in the execution plan's `identities` array and is reproduced
per-row in [`AFCI_MASTER_RUN_RESULTS.csv`](AFCI_MASTER_RUN_RESULTS.csv)
(`sequence` column). Sequence 12 is the refused row.

---

## 6. Non-observation records, listed so they are not miscounted

These produced files but are **not runs** and appear in no run count:

| what | where | count |
| --- | --- | --- |
| Attempt-2 dry-run readiness records | `D:\afci-runs\attempt-2\readiness-context-audit\` | 12 |
| PT08 dry-run probe | `D:\pt08-diagnostic\dryrun\…-dry-run-262ce8672f3c\` | 1 |
| PT08 readiness probes | `D:\pt08-diagnostic\readiness\`, `…\readiness-final\` | 2 |
| PT10 dry-run probe | `D:\afci-v2-qual\runs\probe\…-dry-run-r1-d722c7a9946d\` | 1 |
| PT10 smoke scoring | `D:\afci-v2-qual\score\smoke-pt10.json` | 1 |
| Attempt-1 readiness audits | `D:\afci-runs\readiness-context-audit\`, `D:\afci-runs\probe\` | — |

The single exception is the PT09 `INFRA_RUNNER_CRASH` attempt, which **is** a row
in the master run results: it was a genuine attempted observation, not a probe.
It is marked `INFRASTRUCTURE_INVALID_NON_OBSERVATION` and is not eligible.
