# AFCI-Bench - evidence map

Compiled 2026-09-18. Professor-safe traceability: summary result -> analysis artifact ->
run record -> raw artifact, with a hash at each anchor.

Every chain stops at the private boundary, and it stops at a **field**, not at its value.
No private evaluator identifier appears anywhere in this package.

---

## Traceability chains

### Median C4/C1 input tokens = 1.4014 (Sonnet)

- **analysis artifact** - study-results/05_efficiency_attempt_2_completed/attempt2_endpoint_ratios.csv -> attempt2_primary_pairs.csv (16 rows) -> efficiency_pilot_frozen_analysis_report.json (primary_endpoint.pairs)
- **run record** - AFCI_MASTER_RUN_RESULTS.csv, experiment_id = V2_EFF_ATTEMPT2 (36 rows)
- **raw artifact** - `D:\afci-runs\attempt-2\<run_id>\run_record.json -> efficiency.usage.TOTAL_INPUT_TOKENS -> runtime_evidence.jsonl terminal result event`
- **hash / SHA** - `run plan sha256 0038cd8b563ea804f4887d21cb37ceddb3a8f7632c4dd2315c260d3a9af95767`
- **status** - VERIFIED - recomputed from the run rows in 20_RECOMPUTATION_AUDIT

### Median C4/C1 input tokens = 2.0372 (Haiku)

- **analysis artifact** - study-results/06_lower_model_pilot_completed/lower_model_endpoint_ratios.csv -> lower_model_primary_pairs.csv (8 rows) -> lower_model_pilot_frozen_analysis_report.json (efficiency.endpoints.TOTAL_INPUT_TOKENS.pairs)
- **run record** - AFCI_MASTER_RUN_RESULTS.csv, experiment_id = V2_LOWER_MODEL_PILOT (18 rows)
- **raw artifact** - `D:\afci-runs\lower-model-pilot\<run_id>\run_record.json -> efficiency.usage.TOTAL_INPUT_TOKENS -> runtime_evidence.jsonl terminal result event`
- **hash / SHA** - `run plan sha256 f045c0d93370f7e6f785274acd7df6b34bb28f52ba60cdcfd49eb6812b86b026`
- **status** - VERIFIED - recomputed from the run rows

### Haiku architecture 0 violations in both arms

- **analysis artifact** - study-results/06_lower_model_pilot_completed/lower_model_architecture_summary.csv -> frozen analysis report, architecture.overall
- **run record** - AFCI_MASTER_RUN_RESULTS.csv, architecture_applicable / architecture_violated columns (18 rows)
- **raw artifact** - `D:\afci-runs\lower-model-pilot\<run_id>\architecture_evaluation_result.json`
- **hash / SHA** - `prepared worktree content hash da7a679552d50857408d14e980cc5257ed42e33d7116630433f8451450d1bad6 (49 entries)`
- **status** - VERIFIED - recomputed from the run rows

### PT10 target violation in 1 of 3 runs

- **analysis artifact** - study-results/03_pt09_pt10_qualification/qualification_classification.csv -> qualification_runs.csv (row PT10, 3)
- **run record** - AFCI_MASTER_RUN_RESULTS.csv, experiment_id = V2_PT10_QUALIFICATION
- **raw artifact** - `D:\afci-v2-qual\score\pt10-r3.json -> architecture.target_findings[0]; captured worktree under ...pt10-c1-real-r3-8f809ab6ee92\worktree_post_run\`
- **hash / SHA** - `task sha256 1b1fe29881b3c9f309939df042272b03164fb3baae878c64345e75edddf36b86`
- **status** - VERIFIED to the FIELD. The field's VALUE resolves to a private finding id and stays in the private evaluator repository.

### PT08 0 violations in 3 of 3 runs

- **analysis artifact** - study-results/02_pt08_diagnostic/pt08_diagnostic_runs.csv
- **run record** - AFCI_MASTER_RUN_RESULTS.csv, experiment_id = V2_PT08_DIAGNOSTIC
- **raw artifact** - `D:\pt08-diagnostic\scoring\R{1,2,3}\scoring_summary.json and architecture_finding.json`
- **hash / SHA** - `task sha256 a31bb515b79cc1e211a662de2a8761c97082dd8bf266ee5b4f660981435badf2; diagnostic-scoped evaluator mount 9fdbb347aa936ddc98d19737937b954c0a925ab1e13ace6c385dce0b8bb098dc`
- **status** - VERIFIED

### V1 code churn +65.7%

- **analysis artifact** - study-results/01_v1_original_study/v1_headline_recomputed.csv -> v1_taskwise_churn_recomputed.csv
- **run record** - AFCI_MASTER_RUN_RESULTS.csv, experiment_id = V1_ORIGINAL (48 rows)
- **raw artifact** - `git branch rerun-v1-opus7-artifacts: experiments/paper/results_v1.csv, columns code_additions + code_deletions; per-run experiments/runs_v1/<TASK>/<COND>/metrics.json`
- **hash / SHA** - `results_v1.csv git blob 0d350eb262b49385f290d0a9df6693b34ba3d919`
- **status** - VERIFIED - but HISTORICAL ONLY (limitations L1-L7)

### Sonnet NON_RESET provider cost ratio 1.4928

- **analysis artifact** - study-results/05_efficiency_attempt_2_completed/attempt2_provider_cost.csv (9 rows + median)
- **run record** - AFCI_MASTER_RUN_RESULTS.csv, provider_cost_usd column, 19 of 36 rows populated
- **raw artifact** - `D:\afci-runs\attempt-2\<run_id>\runtime_evidence.jsonl terminal result event`
- **hash / SHA** - `execution plan sha256 562415031c04b0673c54ac352a4ca35a66e885023aa212cedc284da0c65a087e`
- **status** - VERIFIED - NON_RESET only; there is no RESET cost comparison

### Attempt 1 aborted, 18 identity collisions

- **analysis artifact** - study-results/04_efficiency_attempt_1_aborted/AFCI_EFFICIENCY_PILOT_ATTEMPT_1_EVIDENCE_INVENTORY.json
- **run record** - AFCI_MASTER_RUN_RESULTS.csv, experiment_id = V2_EFF_ATTEMPT1 (9 rows)
- **raw artifact** - `D:\afci-runs\obs\...; operator logs D:\afci-runs\logs\seq-0{1..9}.log`
- **hash / SHA** - `evidence inventory sha256 9985860fb3b7a5842e676cc1c66c876e712ea93a196999457d711332ba12683f`
- **status** - VERIFIED - and excluded wholesale. No analysis was ever performed.

---

## Repository and governance anchors

| what | value |
| --- | --- |
| public repo branch | `study-v2` |
| evidence commit (last change to study-results/ outside this package) | `cfdb646b22f41404bb8d414d55cdd2fc630f7492` |
| that commit's subject | study(backstage): halt AFCI pilot attempt 1 and record the escalation |
| public repo origin | https://github.com/thakkarkeyur/afci-bench.git |
| public repo `main` (v1 base, tag `paper-v0`) | `2adc8741acad7ea5423f0bf3d9ad821ff023a35f` |
| private evaluator repo HEAD (read-only, unchanged) | `8ad5e3738a50804aa81bbf99928acf7e54372b51` |
| governed substrate commit | `630d3180af0d02a86330dfb599f559e78df65e94` |
| governed substrate content hash | `0198d76c189f38589e872cab4305527c08e86ef736e1550e428e05f9178060f3` (49 entries) |
| the MAD, `docs/v2/ARCHITECTURE_CONTEXT.md` | `bf6f32b162a23b851596d8b489d938bef10d0b8616a50dcc039873d12ffa7a4d` |
| v1 release | GitHub `ase2026-artifacts-v1` @ `1ba21ad75dacbac5eb87d354a490b088078c30da` |
| v1 DOI | `10.5281/zenodo.19757261` |

## Governance document hashes

| document | sha256 |
| --- | --- |
| `docs/v2/AFCI_EFFICIENCY_PILOT_RUN_PLAN.json` | `0038cd8b563ea804f4887d21cb37ceddb3a8f7632c4dd2315c260d3a9af95767` |
| `docs/v2/AFCI_EFFICIENCY_PILOT_DECISION.md` | `e3110d9a90009be180e76fb30368179529c187263ab823391635990b2cc0d8df` |
| `docs/v2/AFCI_EFFICIENCY_PILOT_ATTEMPT_2_EXECUTION_PLAN.json` | `562415031c04b0673c54ac352a4ca35a66e885023aa212cedc284da0c65a087e` |
| `docs/v2/AFCI_EFFICIENCY_PILOT_ATTEMPT_1_ABORT_DECISION.md` | `21547ed7d3f86e3c6793e830ca128ffe7bf3c6665ada07568c99d2c493a66445` |
| `docs/v2/AFCI_EFFICIENCY_PILOT_ATTEMPT_1_EVIDENCE_INVENTORY.json` | `9985860fb3b7a5842e676cc1c66c876e712ea93a196999457d711332ba12683f` |
| `docs/v2/AFCI_LOWER_MODEL_PILOT_DECISION.md` | `cbb73e76d4f9936319123f650751b079e33044e66afe6422b0c246fdbc716203` |
| `docs/v2/AFCI_LOWER_MODEL_PILOT_RUN_PLAN.json` | `f045c0d93370f7e6f785274acd7df6b34bb28f52ba60cdcfd49eb6812b86b026` |
| `docs/v2/AFCI_LOWER_MODEL_PILOT_EXECUTION_PLAN.json` | `2ff3f9b45e4ddf6f3318bb2a419d9d12b5eaab5b1a297acec425796ed4a24318` |
| `docs/v2/V2_QUALIFICATION_DIAGNOSTIC_DECISION.md` | `e5bcebe5717ab301e9fe27565ddd9593677f56d5c6a78399c21ea1e260416385` |
| `docs/v2/PT08_DIAGNOSTIC_OUTCOME_AND_DISPOSITION.md` | `3658dd21b2ac5b829df92bb8d4da5a8ad71262b6c36bd0c4f7ccbd1c1b94515e` |

## Task body hashes (public)

| task | sha256 | used by |
| --- | --- | --- |
| PT01 | `6c938822fe19cd6e87942a6ee24ec8f604c0883da1b7f80d45216be35d7c9c39` | efficiency pilot; lower-model pilot |
| PT04 | `f349b150b1d8fe5676fed8460b1840b988ee2bb0a78b1966ef82ae9ce9c8a9b5` | efficiency pilot; lower-model pilot |
| PT07 | `557caed09420354efbc823c8b72e54b0760ac72847aba0d9c07d99e37ff7d2d7` | efficiency pilot; lower-model pilot |
| PT08 | `a31bb515b79cc1e211a662de2a8761c97082dd8bf266ee5b4f660981435badf2` | PT08 diagnostic |
| PT09 | `bac32dc0e7163c9ab1816ac6eea6c98738092cca5cf56715e280f1ec1c0ac44c` | qualification |
| PT10 | `1b1fe29881b3c9f309939df042272b03164fb3baae878c64345e75edddf36b86` | qualification |

---

## What is withheld, and why no digest replaces it

Withheld: private opportunity identifiers, rule identifiers, forbidden source and target scopes,
anchor paths, and hidden acceptance case semantics. They live in the private evaluator repository,
and the run record refuses to carry them at all - a structured scorer result naming hidden evaluator
material is rejected rather than written. **No numeric result is withheld.**

No hash is published in place of a withheld identifier. A digest would not be a redaction here: the
public rule catalog and the public corpus together bound the preimage space to a few thousand
candidates, so any such digest is recoverable by enumeration. Traceability instead runs through values
that are already public and already high-entropy - the run id, the task sha256, and the evaluator
manifest digests above. Those identify the evidence uniquely without disclosing what it says.

---

## Recomputation

Every headline figure in this package was recomputed from the 128 run/attempt rows
and compared against the frozen per-experiment analysis artifact:
**124 checks, 0 mismatches.** The full list is in workbook sheet
`20_RECOMPUTATION_AUDIT`. Regenerate this package with:

```sh
python study-results/professor-delivery/_build/build_professor_delivery.py
```
