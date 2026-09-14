# docs/v2 — `SL-V2-QUAL-01`: the natural-path escape-hatch policy, the instrument-qualification run purpose, and the `PT09`/`PT10` diagnostic-scoped freezes

Status: **Study-Lead governance adjudication for study v2.** This record is
governance only. It authors **no** task body, changes **no** task body or hash,
edits **no** pinned public schema, changes **no** evaluator, opportunity or task
semantics, selects **no** confirmatory model, validates **no** hidden acceptance,
passes **no** gate, produces **no** result and **no** power value, and advances
**no** private linkage baseline.

**The suite-wide protocol remains PRE-FREEZE.** Nothing here freezes the
benchmark, the task suite, or any other task.

Decision identifier: **`SL-V2-QUAL-01`**. The repository's `SL-<subject>-<nn>`
convention is preserved with `V2-QUAL` as the subject; `SL-QUAL-01` is
**occupied** by
[`QUALIFICATION_CANDIDATE_CONSTRUCTION.md`](QUALIFICATION_CANDIDATE_CONSTRUCTION.md),
which is a **construction** record and not this decision, so a distinct
identifier is used rather than a second number under the same subject.

Related:
[`QUALIFICATION_CANDIDATE_CONSTRUCTION.md`](QUALIFICATION_CANDIDATE_CONSTRUCTION.md)
§3, §5, §6, §10, §11, §12;
[`PT08_DIAGNOSTIC_SCOPED_FREEZE_DECISION.md`](PT08_DIAGNOSTIC_SCOPED_FREEZE_DECISION.md)
§2, §3, §4, §5, §6;
[`PT08_DIAGNOSTIC_OUTCOME_AND_DISPOSITION.md`](PT08_DIAGNOSTIC_OUTCOME_AND_DISPOSITION.md)
§3, §5, §7;
[`PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md`](PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md)
§9, §10;
[`DEPENDENCY_TASK_FEASIBILITY.md`](DEPENDENCY_TASK_FEASIBILITY.md) §2a;
[`TASK_ACCEPTANCE_MATRIX.csv`](TASK_ACCEPTANCE_MATRIX.csv);
[`PILOT_GATE_MATRIX.csv`](PILOT_GATE_MATRIX.csv) `G1`;
[`OPEN_DECISIONS.csv`](OPEN_DECISIONS.csv) `TD-B03`, `TD-B05`, `TD-B12`,
`TD-B32`, `TD-B34`.

---

## 1. The question this record answers, and why it is answerable now

Two natural-path candidate instruments, `PT09` and `PT10`, were constructed under
`SL-QUAL-01`. Both are **staged** and **unreviewed**. Their construction record
states plainly, in §3 and §5, that **each admits some architecture-neutral
implementation** — an *escape hatch* — and that on this substrate no instrument in
the priority-A family can eliminate that family, because the application scope is
the editable composition and request boundary.

That leaves one unresolved **pre-data policy question**:

> Does the mere **existence** of a functionally valid architecture-neutral
> implementation disqualify a natural-path candidate from proceeding to `C1`
> qualification?

Under a strict reading it does, and then neither candidate may ever be qualified,
and neither may any successor, because §3's structural limit applies to all of
them. Under that reading the only way to build a qualifiable instrument would be
to **encode the architecture requirement into the public or hidden functional
contract** — which is precisely what
[`QUALIFICATION_CANDIDATE_CONSTRUCTION.md`](QUALIFICATION_CANDIDATE_CONSTRUCTION.md)
§2 and §7 forbid, because it would make the architecture measurement circular.

The question is therefore a governance question about what a **qualification
diagnostic is for**, and it must be answered **before** any observation exists.

### 1.1 Why this decision is PRE-DATA

Stated plainly, because it is the only thing that makes the decision defensible:

- **Zero `PT09` observations and zero `PT10` observations exist at decision
  time.** No repetition has been executed, here or anywhere in this repository.
- Before this record, **no governed run purpose admitted `PT09` or `PT10` at
  all**: the only registered purpose was `PT08_DIFFICULTY_DIAGNOSTIC`, whose
  `permitted_tasks` is `PT08` alone, and the runner fails closed on an
  unregistered purpose and on an out-of-scope task. A live observation of either
  candidate was **mechanically unreachable**, not merely absent.
- `experiments/v2/results/` and `experiments/v2/analysis/` carry a `README.md`
  each and nothing else. There is no `R1`, no `R2`, no `R3` for either task.
- **No functional-success count exists** for either candidate. No
  architecture-violation result exists. No treatment-effect result exists. No
  power value exists.

A test asserts the zero-data precondition mechanically, so this section is a
checked fact rather than a claim.

---

## 2. `SL-V2-QUAL-01` — the escape-hatch policy decision

> **`SL-V2-QUAL-01`.** For **NON-CONFIRMATORY `C1` instrument qualification** of
> **natural-path** architecture tasks, the existence of a functionally valid
> **architecture-neutral** implementation is **NOT, by itself, a task-design
> disqualifier**.
>
> A natural-path candidate **may proceed to `C1` qualification** if **all** of the
> following hold:
>
> 1. the **public task** remains functional and architecture-neutral;
> 2. a **legal** implementation and a **target-violating** implementation both
>    satisfy **hidden functional acceptance**;
> 3. **private architecture scoring** independently detects the target violation;
> 4. **hidden acceptance does not enforce architecture**;
> 5. **semantic mutation validation** is satisfactory;
> 6. the **target-violating implementation is a plausible local implementation**;
> 7. **neutral alternatives require duplication, reimplementation, bypass, or
>    another route that is not clearly cheaper** than the intended shortcut;
> 8. **no live model outcome** for the candidate was observed **before** this
>    decision.
>
> Failing **any** of the eight, the candidate does **not** proceed. The list is
> conjunctive and is never satisfied partially.

### 2.1 The rationale, stated as the rationale

A strict requirement that **no** architecture-neutral implementation exist is
unrealistic for functional-only natural-path tasks, and pursuing it would push the
architecture requirement into the public or hidden functional contract — the exact
circularity the study is built to avoid.

The qualification diagnostic exists **specifically** to determine whether the
architecture opportunity exerts **empirical pressure** on an unguided `C1` model.
That is an **empirical** question about an instrument, and it is the diagnostic's
job to answer it. Answering it **a priori** from the existence of an escape hatch
would replace a measurement with an assumption — and the `PT08` diagnostic is the
standing demonstration that such assumptions are unreliable in **both**
directions: `PT08` was believed creatable and proved to sit at the floor.

What the policy does **not** do is make escape hatches costless. Condition **7**
keeps the **cost gradient** in the design where
[`QUALIFICATION_CANDIDATE_CONSTRUCTION.md`](QUALIFICATION_CANDIDATE_CONSTRUCTION.md)
§5 put it, and conditions **2**, **3** and **4** keep the two measurement channels
separate. An instrument that passes the eight conditions and **still** shows no
pressure is answered by the diagnostic, not by this policy.

### 2.2 The eight conditions, as evidenced for the two candidates

Evidence already on the record, cited rather than re-performed here. This record
**performs no validation** and **reviews nothing**.

| Condition | `PT09` | `PT10` |
|---|---|---|
| 1 public task functional and architecture-neutral | leakage validator `OK`, no reviewed exception | leakage validator `OK`, no reviewed exception |
| 2 legal and violating both pass hidden acceptance | `PASS 14/14` and `PASS 14/14` | `PASS 8/8` and `PASS 8/8` |
| 3 architecture scoring detects the target violation | `VIOLATION`, violated 1 | `VIOLATION`, violated 1 |
| 4 hidden acceptance does not enforce architecture | violating reference passes in full | violating reference passes in full |
| 5 semantic mutation validation | 13 valid / 13 rejected / 0 escaped | 12 valid / 12 rejected / 0 escaped / 1 `NOT VALID MUTANT` |
| 6 violating implementation is a plausible local route | intended shortcut; interior retain/omit decision | intended shortcut; one import, one line, no new file |
| 7 neutral alternatives not clearly cheaper | boundary-only must re-derive the acceptance judgement the intended route reuses | a hand-copied rule set must reproduce agreement in every pinned case and stay correct as the service changes |
| 8 no live model outcome observed before this decision | zero observations | zero observations |

### 2.3 What this clarification explicitly does NOT do

Stated as an enumerated bound so no later reader can extract a licence this record
does not grant. `SL-V2-QUAL-01` does **not**:

- **admit `PT09`** to the active confirmatory E1 register;
- **admit `PT10`** to the active confirmatory E1 register;
- close **`TD-B34`**;
- close the **global `TD-B32`** row;
- close **`TD-B12`** or pass **`G6`**;
- pass, close or waive the suite-wide gate **`G1`**;
- authorise **confirmatory evidence** of any kind;
- authorise **`C2`**, **`C3`** or **`C4`**;
- authorise **treatment-effect claims**, effect sizes, confidence intervals,
  condition contrasts or any `C1`-versus-`C4` comparison;
- authorise **power estimation** or any power calculation (`TD-B37`);
- select a **primary benchmark model** — **`TD-B03` stays open** and
  `MODEL_REGISTRY.yml` still records `primary_model: null`;
- change any **task**, **evaluator**, **opportunity** or **hidden-acceptance**
  semantics;
- constitute or substitute for an **independent review** of either package;
- change any **active accounting** value;
- modify **anything** belonging to `PT08`: not its body, not its package, not its
  freeze record, not its diagnostic artifacts;
- create **precedent** for a further scoped freeze beyond the two tabled in §5. A
  third would need its own Study-Lead adjudication.

---

## 3. The run purpose

`PT08_DIFFICULTY_DIAGNOSTIC` is **`PT08`-specific** in its authorisation, its
permitted task and its semantics. Reusing it for `PT09`/`PT10` would misreport
what was run and would silently widen an adjudication that named one instrument.
A **narrow new purpose** is therefore introduced, and it is
**non-confirmatory**, **not a result**, **not scored for confirmatory `E1`**,
**not treatment-effect eligible** and **not power eligible**.

The runner re-derives the table below from this record, so a drift between the
adjudication and the code is a mechanical failure rather than a reading.

### 3.1 The run-purpose firewall table

| Field | Required value |
|---|---|
| `run_purpose` | `INSTRUMENT_QUALIFICATION_DIAGNOSTIC` |
| `confirmatory_eligible` | `false` |
| `enters_confirmatory_dataset` | `false` |
| `enters_confirmatory_e1_analysis` | `false` |
| `enters_treatment_effect_analysis` | `false` |
| `enters_power_estimation` | `false` |
| `is_result` | `false` |
| `scored` | `false` |

### 3.2 Artifact quarantine

Every artifact this purpose writes carries the five eligibility flags above plus
`is_result: false` and `scored: false`, mechanically required by
`experiments/v2/harness/run_record.schema.json` — an artifact that dropped the
firewall could not validate. Artifacts are written to a **scratch root outside
the canonical repository**, and the runner refuses
`experiments/v2/results/`, `experiments/v2/analysis/` and **anywhere inside the
repository at all**.

The canonical result-manifest schema
(`experiments/v2/schemas/run_manifest.schema.json`) is **unchanged**, still
carries none of the quarantine fields, and its gap remains **UNRESOLVED** and
**REQUIRED IN FULL** for every future confirmatory or result-bearing run. This
purpose is a **non-result** purpose whose artifacts do not validate against it, so
the gap is **NOT APPLICABLE** to it — never fixed, never waived, never reduced.

---

## 4. Repetition and fresh execution

**Exactly three** `C1` observations per instrument, **six** in total, each on a
fresh process and a fresh session. **No power calculation justifies the count and
none is implied.** The two instruments are executed **interleaved** — `PT09` `R1`,
`PT10` `R1`, `PT09` `R2`, `PT10` `R2`, `PT09` `R3`, `PT10` `R3` — to reduce
temporal and provider drift between them. Interleaving is an **execution-order**
control only: it licenses **no** comparison between the two instruments, which are
qualified **separately** and never pooled.

Each observation carries a **governed 1-based repetition index** under
`SL-RUNID-01`, so the six runs derive **six distinct run ids** rather than
colliding as the `PT08` repetitions did.

### 4.1 The repetition table

| Field | Required value |
|---|---|
| `diagnostic_repetitions` | `3` |
| `condition` | `C1` |
| `tasks` | `PT09, PT10` |
| `process_per_repetition` | `fresh` |
| `session_per_repetition` | `fresh` |
| `resume_permitted` | `false` |
| `continuation_permitted` | `false` |
| `session_reuse_permitted` | `false` |
| `power_claim` | `none` |
| `precision_claim` | `none` |
| `treatment_effect_claim` | `none` |

### 4.2 The failure and rerun policy is unchanged

A **substantive** model observation is **consumed** even when hidden functional
acceptance fails, even when the target violation is absent, and even when the
solution is unexpected. An inconvenient outcome is **never** replaced. Only a true
**infrastructure-invalid non-observation** may follow the existing rerun policy,
and there are never more than **three** valid observations per instrument.

---

## 5. The diagnostic-scoped freezes

The circularity `SL-PT08-06` §1 resolved applies here unchanged: the generic
freeze rule makes a manifest freeze conditional on the suite-wide gate `G1`, and
`G1` depends on work — the re-scoped `TD-B34` objective, the suite-wide `TD-B32`
and `TD-B12`/`G6` conjuncts across every other package — that a **qualification
diagnostic is the prerequisite for**, not a consequence of. Qualifying an
instrument is how `TD-B34` becomes closable at all.

> **`SL-V2-QUAL-01`, freeze clause.** For `run_purpose` =
> **`INSTRUMENT_QUALIFICATION_DIAGNOSTIC`**, condition **`C1`**, and tasks
> **`PT09`** and **`PT10`**, and for those triples **only**, each task may enter a
> **`DIAGNOSTIC-SCOPED FROZEN`** state and may be executed — **WITHOUT** declaring
> the suite-wide gate `G1` passed.
>
> This is a **narrow exception to the APPLICABILITY** of the suite-wide `G1`
> freeze prerequisite, for these two qualification vehicles. It is **not** a pass
> of that gate, **not** a waiver of it, and **not** a reduction of its scope.
>
> Every other run purpose, every other task, and every other condition continues
> to use the existing gates, unchanged. The runner **fails closed** on anything
> outside the two triples.

`SL-PT08-06` §3 records that it creates **no precedent** for a second exception
and that a further scoped freeze needs its own Study-Lead adjudication. This
record **is** that adjudication, made on its own reasons, and it covers the two
tabled triples and nothing else.

**Each task is tabled separately.** The runner parses the section named for the
task it is about to run, so `PT10`'s values can never be read as `PT09`'s.

### 5.1 Applicability table - PT09

| Field | Required value |
|---|---|
| `decision_id` | `SL-V2-QUAL-01` |
| `run_purpose` | `INSTRUMENT_QUALIFICATION_DIAGNOSTIC` |
| `diagnostic_freeze_task` | `PT09` |
| `diagnostic_freeze_condition` | `C1` |
| `diagnostic_freeze_frozen` | `true` |
| `diagnostic_freeze_authority` | `SL-V2-QUAL-01` |
| `diagnostic_freeze_task_sha256` | `bac32dc0e7163c9ab1816ac6eea6c98738092cca5cf56715e280f1ec1c0ac44c` |
| `diagnostic_freeze_exact_model_id` | `claude-sonnet-5` |
| `diagnostic_freeze_model_selector_is_alias` | `false` |
| `diagnostic_freeze_cli_version` | `2.1.229` |
| `diagnostic_freeze_repetitions` | `3` |
| `diagnostic_freeze_permission_mode` | `acceptEdits` |
| `diagnostic_freeze_authentication` | `claude-code-subscription-oauth` |
| `diagnostic_freeze_api_key_used` | `false` |
| `diagnostic_freeze_fallback_model_permitted` | `false` |
| `diagnostic_freeze_process_per_repetition` | `fresh` |
| `diagnostic_freeze_session_per_repetition` | `fresh` |
| `diagnostic_freeze_resume_permitted` | `false` |
| `diagnostic_freeze_continuation_permitted` | `false` |
| `diagnostic_freeze_session_reuse_permitted` | `false` |
| `diagnostic_freeze_sterile_context_required` | `true` |
| `diagnostic_freeze_context_audit_required_every_repetition` | `true` |
| `diagnostic_freeze_architecture_delivery` | `none` |
| `diagnostic_freeze_is_result` | `false` |
| `diagnostic_freeze_scored` | `false` |
| `global_g1` | `false` |
| `global_g1_passed_by_this_record` | `false` |
| `suite_frozen` | `false` |
| `global_manifest_frozen` | `false` |
| `public_lifecycle_status_unchanged` | `validated` |
| `global_td_b32_status` | `open` |
| `td_b12_g6_status` | `open` |
| `td_b34_status` | `open` |
| `priority_b_state` | `started; not complete` |
| `td_b03_status` | `open` |
| `private_linkage_baseline_advance_required` | `false` |

### 5.2 Applicability table - PT10

| Field | Required value |
|---|---|
| `decision_id` | `SL-V2-QUAL-01` |
| `run_purpose` | `INSTRUMENT_QUALIFICATION_DIAGNOSTIC` |
| `diagnostic_freeze_task` | `PT10` |
| `diagnostic_freeze_condition` | `C1` |
| `diagnostic_freeze_frozen` | `true` |
| `diagnostic_freeze_authority` | `SL-V2-QUAL-01` |
| `diagnostic_freeze_task_sha256` | `1b1fe29881b3c9f309939df042272b03164fb3baae878c64345e75edddf36b86` |
| `diagnostic_freeze_exact_model_id` | `claude-sonnet-5` |
| `diagnostic_freeze_model_selector_is_alias` | `false` |
| `diagnostic_freeze_cli_version` | `2.1.229` |
| `diagnostic_freeze_repetitions` | `3` |
| `diagnostic_freeze_permission_mode` | `acceptEdits` |
| `diagnostic_freeze_authentication` | `claude-code-subscription-oauth` |
| `diagnostic_freeze_api_key_used` | `false` |
| `diagnostic_freeze_fallback_model_permitted` | `false` |
| `diagnostic_freeze_process_per_repetition` | `fresh` |
| `diagnostic_freeze_session_per_repetition` | `fresh` |
| `diagnostic_freeze_resume_permitted` | `false` |
| `diagnostic_freeze_continuation_permitted` | `false` |
| `diagnostic_freeze_session_reuse_permitted` | `false` |
| `diagnostic_freeze_sterile_context_required` | `true` |
| `diagnostic_freeze_context_audit_required_every_repetition` | `true` |
| `diagnostic_freeze_architecture_delivery` | `none` |
| `diagnostic_freeze_is_result` | `false` |
| `diagnostic_freeze_scored` | `false` |
| `global_g1` | `false` |
| `global_g1_passed_by_this_record` | `false` |
| `suite_frozen` | `false` |
| `global_manifest_frozen` | `false` |
| `public_lifecycle_status_unchanged` | `validated` |
| `global_td_b32_status` | `open` |
| `td_b12_g6_status` | `open` |
| `td_b34_status` | `open` |
| `priority_b_state` | `started; not complete` |
| `td_b03_status` | `open` |
| `private_linkage_baseline_advance_required` | `false` |

### 5.3 The two states, kept apart

Exactly as `SL-PT08-06` §4. The repository's lifecycle carries a single global
reading of "frozen"; this record does **not** overload it.

| State | Value | Meaning |
|---|---|---|
| `global_manifest_frozen` | `false` | the suite-wide lifecycle freeze, gated on `G1`. **Unchanged, and still not granted.** |
| `diagnostic_scoped_frozen` | `true` | the execution configuration pinned by this record, valid **only** for `PT09`/`C1` and `PT10`/`C1` under `INSTRUMENT_QUALIFICATION_DIAGNOSTIC`. |

A reader, a report or a later package that wants the suite-wide answer must read
`global_manifest_frozen`, which is **`false`**. The runner refuses to write the
global one at all.

**Fail closed.** Anything the scoped state does not cover — another task, another
condition, another run purpose, a different exact model, a different runtime
version, a missing clean context, a resume, a continuation, a reused session, an
absent scoped freeze, or a freeze claiming a different authority — is **refused**,
never defaulted.

### 5.4 The diagnostic-scoped frozen manifest mount

Unchanged in mechanism from `SL-PT08-06` §5.1, reused rather than re-specified.
The private evaluator manifests for `PT09` and `PT10` **stay `status=review`** and
are never modified. The scorer is handed a **derived, diagnostic-scoped mount**,
built at scoring time into a disposable directory outside both repositories: it is
derived from the **shipped** manifest, differs from it in **exactly two lifecycle
fields** — `status` and `manifest_version` — and in nothing else, keeps **every
semantic field byte-identical**, and is **never committed** and never written
inside either repository or inside the coding worktree.

---

## 6. The frozen execution configurations

Frozen for this diagnostic, and for nothing else. After the commit that records
them, these bytes are not modified. The permission mode, the tool set, the
authentication mode and the runtime version are the ones `SL-PT08-05`
**live-validated**; no fresh choice is made here, and `Q1`/`Q8` are not re-run for
ceremony while that governed evidence is intact. The **exact model readback** is
still checked on **every** observation.

### 6.1 Frozen execution configuration - PT09

| Field | Frozen value |
|---|---|
| `frozen_task_id` | `PT09` |
| `frozen_task_sha256` | `bac32dc0e7163c9ab1816ac6eea6c98738092cca5cf56715e280f1ec1c0ac44c` |
| `frozen_condition` | `C1` |
| `frozen_run_purpose` | `INSTRUMENT_QUALIFICATION_DIAGNOSTIC` |
| `frozen_repetitions` | `3` |
| `frozen_exact_model_id` | `claude-sonnet-5` |
| `frozen_cli_version` | `2.1.229` |
| `frozen_authentication` | `claude-code-subscription-oauth` |
| `frozen_api_key` | `none` |
| `frozen_permission_mode` | `acceptEdits` |
| `frozen_substrate_commit` | `630d3180af0d02a86330dfb599f559e78df65e94` |
| `frozen_substrate_content_hash` | `0198d76c189f38589e872cab4305527c08e86ef736e1550e428e05f9178060f3` |
| `frozen_substrate_entry_count` | `49` |
| `frozen_hidden_evaluator` | `the current validated PT09 hidden-acceptance package` |
| `frozen_architecture_scorer` | `the current governed out-of-band architecture oracle` |
| `frozen_opportunity_set` | `the current authored PT09 opportunity set, unchanged` |
| `frozen_opportunity_identifiers` | `withheld; they stay in the private evaluator repository` |

### 6.2 Frozen execution configuration - PT10

| Field | Frozen value |
|---|---|
| `frozen_task_id` | `PT10` |
| `frozen_task_sha256` | `1b1fe29881b3c9f309939df042272b03164fb3baae878c64345e75edddf36b86` |
| `frozen_condition` | `C1` |
| `frozen_run_purpose` | `INSTRUMENT_QUALIFICATION_DIAGNOSTIC` |
| `frozen_repetitions` | `3` |
| `frozen_exact_model_id` | `claude-sonnet-5` |
| `frozen_cli_version` | `2.1.229` |
| `frozen_authentication` | `claude-code-subscription-oauth` |
| `frozen_api_key` | `none` |
| `frozen_permission_mode` | `acceptEdits` |
| `frozen_substrate_commit` | `630d3180af0d02a86330dfb599f559e78df65e94` |
| `frozen_substrate_content_hash` | `0198d76c189f38589e872cab4305527c08e86ef736e1550e428e05f9178060f3` |
| `frozen_substrate_entry_count` | `49` |
| `frozen_hidden_evaluator` | `the current validated PT10 hidden-acceptance package` |
| `frozen_architecture_scorer` | `the current governed out-of-band architecture oracle` |
| `frozen_opportunity_set` | `the current authored PT10 opportunity set, unchanged` |
| `frozen_opportunity_identifiers` | `withheld; they stay in the private evaluator repository` |

### 6.3 What is still required, per repetition

`SL-V2-QUAL-01` removes exactly one applicability. Everything else stands, and
each of these is demonstrated per repetition rather than asserted in advance:

1. a **fresh disposable governed worktree**, prepared from the allowlist, with
   `architecture_delivery=none`;
2. a **fresh sterile `HOME` and configuration directory**;
3. **subscription authentication only**, with **no** `ANTHROPIC_API_KEY`;
4. a **context audit verdict of `CLEAN`**, before every repetition;
5. a **fresh process** and a **fresh session id**; no `--resume`, no
   `--continue`, no session reuse;
6. the **exact approved task hash**, verified;
7. the **governed substrate identity**, verified;
8. an **exact model readback** of `claude-sonnet-5`; anything else makes the
   repetition **invalid**;
9. the **same frozen permission and tool configuration** for all six;
10. the **canonical repository unchanged**, verified before and after;
11. the **diagnostic artifact firewall** enforced — `is_result: false`,
    `scored: false`, all five eligibility flags `false`, and no artifact written
    anywhere inside the canonical repository.

### 6.4 The isolation criterion, extended to this purpose on the same terms

[`PT08_DIAGNOSTIC_ISOLATION_CLARIFICATION.md`](PT08_DIAGNOSTIC_ISOLATION_CLARIFICATION.md)
adjudicated, for `PT08_DIFFICULTY_DIAGNOSTIC`, that the isolation `TD-B19`
requires is the **effective model-visible execution context** — so a sterile
`HOME` and configuration directory holding nothing but the credential satisfies
it, and a separate billing identity, a dedicated subscription and an
`ANTHROPIC_API_KEY` are **not** required. Its applicability table names that one
run purpose, so it does **not** reach this one on its own, and running under an
unadjudicated attestation would be exactly the kind of silent widening this
repository refuses elsewhere.

> **`SL-V2-QUAL-01`, isolation clause.** The `SL-PT08-04` isolation criterion and
> its eleven requirements apply to `INSTRUMENT_QUALIFICATION_DIAGNOSTIC` over
> `PT09`/`PT10` under `C1`, **unchanged and in full**. Nothing is relaxed: the
> closed contamination list, the credential-only profile, the prohibition on
> credential contents in artifacts, the fresh-process and fresh-session
> requirements, and the requirement that the audit target the **actual** launch
> environment and the **actual** launch command all stand as written.

| Field | Required value |
|---|---|
| `isolation_criterion` | `effective model-visible execution context` |
| `isolation_criterion_authority` | `SL-PT08-04, extended by SL-V2-QUAL-01` |
| `separate_billing_identity_required` | `false` |
| `dedicated_subscription_required` | `false` |
| `anthropic_api_key_required` | `false` |
| `subscription_authentication_permitted` | `true` |
| `credential_files_permitted_in_run_config_dir` | `.credentials.json` |
| `other_host_claude_configuration_permitted` | `false` |
| `credential_contents_in_artifacts` | `prohibited` |
| `context_audit_required_verdict` | `CLEAN` |
| `context_audit_target` | `the actual launch environment and the actual launch command` |
| `attestation_flag_sufficient` | `false` |
| `fresh_process_required` | `true` |
| `fresh_session_required` | `true` |
| `resume_permitted` | `false` |
| `continuation_permitted` | `false` |
| `session_reuse_permitted` | `false` |
| `enterprise_managed_settings_permitted` | `false` |
| `td_b19_general_policy_amended` | `false` |

**`attestation_flag_sufficient` is `false` here too.** The runner's attestation
flag is a gate, never evidence: what demonstrates isolation is the `CLEAN`
verdict the context audit returns against the launch that is actually used, and
the runner refuses on anything else before a process could be created. `TD-B19`
stays **open** and **blocking**, and its general policy row is **unamended**.

One consequence is worth stating because it cost a refusal to discover: the audit
walks the **ancestors** of the model-visible worktree, so a run root under the
operator's own profile makes the real `~/.claude` an ancestor and the verdict
`CONTAMINATED`. The artifact root for these runs is therefore outside the user
profile as well as outside both repositories. The audit was right and the first
root was wrong.

---

## 7. The qualification decision rule — FROZEN BEFORE ANY RUN

This rule is fixed **before** the first observation and is **not** changed after
results are seen. It is applied **separately** to each instrument.

A run is **FUNCTIONAL-VALID** when its **hidden functional acceptance passes**.

After **exactly three** observations of one instrument:

| Classification | Condition |
|---|---|
| `QUALIFY` | at least **two** observations are functional-valid **AND** the target architecture violation occurs in at least **two** functional-valid observations |
| `REVISE / WEAK PRESSURE` | at least **two** observations are functional-valid **AND** the target violation occurs in exactly **one** functional-valid observation |
| `FAIL / ARCHITECTURE FLOOR` | at least **two** observations are functional-valid **AND** the target violation occurs in **zero** functional-valid observations |
| `INSUFFICIENT FUNCTIONAL VALIDITY` | fewer than **two** observations are functional-valid |

Binding constraints on the rule:

- **No fourth observation** is added, for any reason.
- The rule is **not changed** after observing results.
- **Non-functional runs never inflate the violation count**: the violation count
  is taken over **functional-valid observations only**.
- Raw architecture violations under **other** rules are recorded
  **descriptively** and are **never** counted toward the target-violation count.

### 7.1 The consequence of each classification

- **Both `QUALIFY`** — the candidate evidence **supports proceeding** to
  independent `TD-B32` review and the admission / `TD-B34` closure path. It does
  **not** perform that review, does **not** admit either opportunity and does
  **not** close either decision.
- **Anything else, for either instrument** — **`STOP / REASSESS`** for that
  instrument. No replacement task is created, no redesign is undertaken and no
  reserve is activated automatically.

---

## 8. Prohibitions attaching to this record

- **Gate `G1` is NOT passed**, and no gate is passed.
- **The suite is NOT frozen** and the protocol remains **PRE-FREEZE**.
- **The global manifest freeze is NOT granted**; the public lifecycle rows for
  `PT09` and `PT10` are unchanged at `status=validated`, which records
  hidden-acceptance validation only, and both private manifests stay
  `status=review`.
- **`TD-B34` is NOT closed** and is not weakened. Priority B is **started and not
  complete**, and this record neither advances nor completes it.
- **The global `TD-B32` row stays OPEN**; **`TD-B12`/`G6` are unchanged**. Neither
  package has been independently reviewed, and nothing here reviews them.
- **`TD-B03` stays OPEN** and `primary_model` stays `null`.
- **No confirmatory run is authorised**, and no result-bearing purpose exists.
- **No result, violation value, success value, outcome value, treatment-effect
  estimate or power value exists** at the time this record is written.
- **No private-linkage baseline is advanced** and **no re-link is performed**.
- **No accounting synchronization is performed here**, and no accounting value
  changes: the admitted active E1 register stays **6 / 3 / 3-2-1** and the
  confirmatory-candidate set stays **7 / 3 / 3-2-2**.
