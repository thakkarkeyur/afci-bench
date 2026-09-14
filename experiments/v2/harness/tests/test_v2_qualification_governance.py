"""`SL-V2-QUAL-01`: the pre-data escape-hatch policy and the PT09/PT10 freezes.

These tests exist to make the adjudication **checkable** rather than merely
written down. Each of them fails if the record and the runner ever disagree, and
several of them are deliberately NEGATIVE: a policy that can only be shown to
permit things is not a policy.

The load-bearing ones, stated plainly:

* the escape-hatch clarification **alone** admits nothing — no task, no gate, no
  denominator, no confirmatory eligibility;
* the record was written while **zero** live observations of either candidate
  existed, and that is asserted mechanically rather than promised in prose;
* `C2`/`C3`/`C4` and every result-bearing use stay **refused**;
* the two suite-wide registers are **unchanged**.

No model is invoked and no benchmark task is executed.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

HARNESS = Path(__file__).resolve().parents[1]
REPO = HARNESS.parents[2]
sys.path.insert(0, str(HARNESS))

import run_evaluation as ev  # noqa: E402
import run_governance as gov  # noqa: E402

PURPOSE_NAME = "INSTRUMENT_QUALIFICATION_DIAGNOSTIC"
DECISION_ID = "SL-V2-QUAL-01"
RECORD = REPO / "docs" / "v2" / "V2_QUALIFICATION_DIAGNOSTIC_DECISION.md"
CANDIDATES = ("PT09", "PT10")
TASK_SHA = {
    "PT09": "bac32dc0e7163c9ab1816ac6eea6c98738092cca5cf56715e280f1ec1c0ac44c",
    "PT10": "1b1fe29881b3c9f309939df042272b03164fb3baae878c64345e75edddf36b86",
}


@pytest.fixture(scope="module")
def purpose() -> gov.RunPurpose:
    return gov.resolve_run_purpose(PURPOSE_NAME)


@pytest.fixture(scope="module")
def text() -> str:
    return RECORD.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# 1. The record exists, is the authority, and is PRE-DATA.
# --------------------------------------------------------------------------- #
def test_the_record_is_the_named_authority(purpose, text):
    assert RECORD.is_file(), f"{RECORD} is the authority and must exist"
    assert purpose.decision_id == DECISION_ID
    assert purpose.diagnostic_freeze_authority == DECISION_ID
    assert DECISION_ID in text


def test_no_live_observation_of_either_candidate_exists(purpose):
    """The pre-data precondition, asserted rather than promised (§1.1).

    Two independent readings, because either alone is weak. The first is the
    absence of any artifact; the second is the stronger structural fact that no
    confirmatory artifact area holds anything at all.
    """
    for area in gov.CONFIRMATORY_ARTIFACT_DIRS:
        entries = sorted(p.name for p in area.iterdir()) if area.is_dir() else []
        assert entries == ["README.md"], (
            f"{area} holds {entries}; the qualification decision is PRE-DATA and "
            "no result artifact may exist for any task"
        )


def test_the_only_purposes_that_admit_the_candidates_are_this_one(purpose):
    """Before this record, PT09/PT10 were mechanically unreachable (§1.1).

    The claim is not "nobody ran them", which is unverifiable, but "no governed
    purpose permitted them", which is. Exactly one purpose may name them, and it
    is the one this record authorises.
    """
    admitting = {
        name
        for name, p in gov.RUN_PURPOSES.items()
        if set(CANDIDATES) & set(p.permitted_tasks)
    }
    assert admitting == {PURPOSE_NAME}


# --------------------------------------------------------------------------- #
# 2. Escape-hatch existence alone admits NOTHING.
# --------------------------------------------------------------------------- #
def test_the_policy_admits_neither_candidate_to_the_active_register(text):
    """The clarification permits a diagnostic; it does not admit an opportunity."""
    for phrase in (
        "does **not**",
        "**admit `PT09`**",
        "**admit `PT10`**",
    ):
        assert phrase in text, f"the record must state that it {phrase}"
    # The two registers are stated, and stated as UNCHANGED.
    assert "6 / 3 / 3-2-1" in text and "7 / 3 / 3-2-2" in text


def test_the_scoped_freeze_never_reports_a_suite_wide_gate_as_granted(purpose):
    """The global pins are what stop a scoped freeze becoming a gate pass."""
    pins = dict(purpose.global_pins())
    assert pins["global_g1"] is False
    assert pins["global_g1_passed_by_this_record"] is False
    assert pins["suite_frozen"] is False
    assert pins["global_manifest_frozen"] is False
    assert pins["global_td_b32_status"] == "open"
    assert pins["td_b12_g6_status"] == "open"
    assert pins["td_b34_status"] == "open"
    assert pins["td_b03_status"] == "open"


def test_a_record_that_claimed_g1_would_be_refused(purpose, tmp_path):
    """Negative: the check can fail. A policy that cannot refuse is decorative."""
    forged = tmp_path / "forged.md"
    forged.write_text(
        RECORD.read_text(encoding="utf-8").replace(
            "| `global_g1` | `false` |", "| `global_g1` | `true` |"
        ),
        encoding="utf-8",
    )
    problems = gov.diagnostic_freeze_problems(
        purpose, "PT09", "C1", record=forged
    )
    assert gov.SUITE_WIDE_G1_MUST_NOT_BE_CLAIMED in {c for c, _ in problems}


def test_a_record_that_relaxed_an_execution_pin_would_be_refused(purpose, tmp_path):
    forged = tmp_path / "forged.md"
    forged.write_text(
        RECORD.read_text(encoding="utf-8").replace(
            "| `diagnostic_freeze_resume_permitted` | `false` |",
            "| `diagnostic_freeze_resume_permitted` | `true` |",
        ),
        encoding="utf-8",
    )
    problems = gov.diagnostic_freeze_problems(purpose, "PT09", "C1", record=forged)
    assert gov.DIAGNOSTIC_FREEZE_RECORD_INCONSISTENT in {c for c, _ in problems}


# --------------------------------------------------------------------------- #
# 3. The candidate must still carry its evidence.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("task_id", CANDIDATES)
def test_the_frozen_task_hash_is_re_derived_from_the_approved_index(task_id):
    """The record's pin is never taken on trust: it is checked against the index
    AND against the bytes on disk. Three sources, one answer."""
    assert gov.expected_task_sha256(task_id) == TASK_SHA[task_id]
    body = gov.public_task_path(task_id)
    import prepare_model_worktree as pmw

    assert pmw.sha256_file(body) == TASK_SHA[task_id]


@pytest.mark.parametrize("task_id", CANDIDATES)
def test_a_wrong_task_hash_in_the_record_is_refused(purpose, task_id, tmp_path):
    forged = tmp_path / "forged.md"
    forged.write_text(
        RECORD.read_text(encoding="utf-8").replace(TASK_SHA[task_id], "0" * 64),
        encoding="utf-8",
    )
    problems = gov.diagnostic_freeze_problems(purpose, task_id, "C1", record=forged)
    assert gov.TASK_SHA_MISMATCH in {c for c, _ in problems}


@pytest.mark.parametrize("task_id", CANDIDATES)
def test_hidden_functional_acceptance_must_be_validated(task_id):
    """Condition 2/4: a legal AND a violating reference pass hidden acceptance.

    The public authority records the validation; this asserts the runner reads it
    and would refuse without it.
    """
    assert gov.hidden_acceptance_is_validated(task_id)
    channel = ev.functional_acceptance_channel(task_id)
    assert channel.ready


@pytest.mark.parametrize("task_id", CANDIDATES)
def test_the_acceptance_row_records_that_a_violating_reference_also_passes(task_id):
    """Condition 4, read off the public authority rather than asserted here.

    If a violating implementation could NOT pass, the functional oracle would be
    enforcing placement and the architecture measurement would be circular.
    """
    row = gov.acceptance_matrix_row(task_id)
    blob = " ".join(str(v) for v in row.values()).lower()
    assert "functional acceptance never enforces placement" in blob
    assert "also passes" in blob


@pytest.mark.parametrize("task_id", CANDIDATES)
def test_mutation_evidence_is_recorded_for_each_candidate(task_id):
    """Condition 5. The counts are the ones the construction package executed."""
    row = gov.acceptance_matrix_row(task_id)
    blob = " ".join(str(v) for v in row.values()).lower()
    expected = {
        "PT09": "13 of 13 valid reference-fail mutants are rejected with 0 escaped",
        "PT10": "12 of 12 valid reference-fail mutants are rejected with 0 escaped",
    }[task_id]
    assert expected in blob
    # PT10's single equivalent mutation is recorded rather than hidden.
    if task_id == "PT10":
        assert "not valid mutant" in blob


@pytest.mark.parametrize("task_id", CANDIDATES)
def test_the_private_architecture_scorer_is_reachable_for_the_candidate(
    purpose, task_id
):
    """Condition 3: the target violation must be independently detectable.

    Availability of the authored corpus is what the runner can check from the
    public side; it never imports private code and never scores anything here.
    """
    ok, detail = gov.private_architecture_corpus_available(
        task_id, None, purpose.corpus_script_for(task_id)
    )
    if not ok:
        pytest.skip(f"sibling private repository not present: {detail}")
    assert "qualification_corpus.py" in detail


def test_a_named_corpus_module_is_never_guessed(purpose):
    """Negative: a purpose naming an absent module reports absent, not searched."""
    ok, detail = gov.private_architecture_corpus_available(
        "PT09", None, "scripts/does_not_exist_corpus.py"
    )
    assert ok is False and "not available" in detail


# --------------------------------------------------------------------------- #
# 4. The policy authorises C1 QUALIFICATION ONLY.
# --------------------------------------------------------------------------- #
def test_the_purpose_is_c1_only(purpose):
    assert purpose.permitted_conditions == ("C1",)
    assert set(purpose.permitted_tasks) == set(CANDIDATES)


@pytest.mark.parametrize("condition", ["C2", "C3", "C4"])
@pytest.mark.parametrize("task_id", CANDIDATES)
def test_c2_c3_c4_are_refused_for_the_candidates(purpose, task_id, condition):
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        gov.assert_task_and_condition_permitted(purpose, task_id, condition)
    assert excinfo.value.code == gov.CONDITION_NOT_PERMITTED_FOR_PURPOSE


@pytest.mark.parametrize("condition", ["C2", "C3", "C4"])
@pytest.mark.parametrize("task_id", CANDIDATES)
def test_no_scoped_freeze_exists_outside_c1(purpose, task_id, condition):
    problems = gov.diagnostic_freeze_problems(purpose, task_id, condition)
    assert gov.DIAGNOSTIC_FREEZE_SCOPE_EXCEEDED in {c for c, _ in problems}
    assert gov.diagnostic_freeze_for(purpose, task_id, condition) is None


@pytest.mark.parametrize("task_id", ["PT01", "PT04", "PT07", "PT08", "PR01"])
def test_the_purpose_admits_no_other_task(purpose, task_id):
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        gov.assert_task_and_condition_permitted(purpose, task_id, "C1")
    assert excinfo.value.code == gov.TASK_NOT_PERMITTED_FOR_PURPOSE


def test_the_pt08_purpose_still_admits_only_pt08():
    """The generalisation must not have widened the pre-existing exception."""
    pt08 = gov.resolve_run_purpose("PT08_DIFFICULTY_DIAGNOSTIC")
    assert pt08.permitted_tasks == ("PT08",)
    assert pt08.diagnostic_freeze_authority == "SL-PT08-06"
    for task_id in CANDIDATES:
        problems = gov.diagnostic_freeze_problems(pt08, task_id, "C1")
        assert gov.DIAGNOSTIC_FREEZE_SCOPE_EXCEEDED in {c for c, _ in problems}


def test_the_two_purposes_never_read_one_anothers_tables():
    """Each purpose's authority is its own record/section, not a shared constant."""
    pt08 = gov.resolve_run_purpose("PT08_DIFFICULTY_DIAGNOSTIC")
    qual = gov.resolve_run_purpose(PURPOSE_NAME)
    assert pt08.diagnostic_freeze_record != qual.diagnostic_freeze_record
    assert pt08.firewall_record != qual.firewall_record
    assert set(pt08.diagnostic_freeze_table_headings) == {"PT08"}
    assert set(qual.diagnostic_freeze_table_headings) == set(CANDIDATES)
    # PT09's table and PT10's table are DIFFERENT sections with different values.
    pt09 = gov.governed_diagnostic_freeze(
        qual.freeze_record_path(), qual.freeze_table_heading("PT09")
    )
    pt10 = gov.governed_diagnostic_freeze(
        qual.freeze_record_path(), qual.freeze_table_heading("PT10")
    )
    assert pt09["diagnostic_freeze_task"] == "PT09"
    assert pt10["diagnostic_freeze_task"] == "PT10"
    assert pt09["diagnostic_freeze_task_sha256"] != pt10["diagnostic_freeze_task_sha256"]


# --------------------------------------------------------------------------- #
# 5. Confirmatory flags stay false; the artifacts stay quarantined.
# --------------------------------------------------------------------------- #
def test_every_confirmatory_flag_is_false(purpose):
    assert purpose.confirmatory is False
    assert purpose.result_bearing is False
    assert purpose.firewall_flags() == {f: False for f in gov.FIREWALL_FIELDS}


def test_the_record_and_the_runner_agree_on_the_firewall(purpose):
    governed = gov.governed_firewall_from_record(
        purpose.firewall_record_path(), purpose.firewall_heading
    )
    assert governed["run_purpose"] == PURPOSE_NAME
    for flag in gov.FIREWALL_FIELDS:
        assert governed[flag] is False, f"{flag} must be pinned false in the record"


def test_the_artifact_schema_mechanically_enforces_the_quarantine(purpose):
    assert gov.artifact_schema_problems(purpose) == []
    schema = gov.load_json_schema(purpose.artifact_schema_path())
    assert "run_purpose" in schema["required"]


def test_an_artifact_that_dropped_a_flag_is_refused(purpose):
    flags = {f: False for f in gov.FIREWALL_FIELDS}
    gov.assert_firewall_consistent(purpose, flags)  # the clean case passes
    for flag in gov.FIREWALL_FIELDS:
        broken = dict(flags, **{flag: True})
        with pytest.raises(gov.RunnerRefusal) as excinfo:
            gov.assert_firewall_consistent(purpose, broken)
        assert excinfo.value.code == gov.DIAGNOSTIC_FIREWALL_INCONSISTENT


@pytest.mark.parametrize("area", [p.name for p in gov.CONFIRMATORY_ARTIFACT_DIRS])
def test_artifacts_may_never_be_written_into_a_confirmatory_area(purpose, area):
    target = REPO / "experiments" / "v2" / area / "whatever"
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        gov.assert_artifact_area_permitted(target, purpose)
    assert excinfo.value.code == gov.DIAGNOSTIC_ARTIFACT_IN_CONFIRMATORY_AREA


def test_artifacts_may_never_be_written_inside_the_repository_at_all(purpose):
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        gov.assert_artifact_area_permitted(REPO / "docs" / "v2" / "scratch", purpose)
    assert excinfo.value.code == gov.ARTIFACT_ROOT_INSIDE_CANONICAL_REPOSITORY


def test_the_canonical_result_manifest_gap_is_scoped_out_never_resolved(purpose):
    """It is NOT_APPLICABLE to a non-result purpose and stays UNRESOLVED globally."""
    assert gov.canonical_run_manifest_carries_firewall() is False
    report = gov.check_readiness("PT09", "C1", PURPOSE_NAME)
    item = next(
        p
        for p in report.prerequisites
        if p.item == "canonical_confirmatory_run_manifest_firewall"
    )
    assert item.status == gov.NOT_APPLICABLE
    assert item.code == gov.RUN_MANIFEST_SCHEMA_LACKS_DIAGNOSTIC_FIREWALL


# --------------------------------------------------------------------------- #
# 6. The repetition count and the classification rule are frozen before any run.
# --------------------------------------------------------------------------- #
def test_exactly_three_repetitions_per_instrument(purpose):
    assert purpose.repetitions == 3
    governed = gov.governed_execution_decisions(
        purpose.execution_decisions_record_path(), purpose.execution_decisions_heading
    )
    assert governed["diagnostic_repetitions"] == 3
    assert governed["condition"] == "C1"
    assert governed["tasks"] == "PT09, PT10"
    for key in (
        "resume_permitted",
        "continuation_permitted",
        "session_reuse_permitted",
    ):
        assert governed[key] is False
    for key in ("power_claim", "precision_claim", "treatment_effect_claim"):
        assert governed[key] == "none"


def test_the_repetition_probe_passes_and_can_fail(purpose, tmp_path, monkeypatch):
    assert gov._repetition_decision_probe(purpose).status == gov.PASS
    forged_repo = tmp_path / "repo"
    (forged_repo / "docs" / "v2").mkdir(parents=True)
    (forged_repo / purpose.execution_decisions_record).write_text(
        RECORD.read_text(encoding="utf-8").replace(
            "| `diagnostic_repetitions` | `3` |", "| `diagnostic_repetitions` | `4` |"
        ),
        encoding="utf-8",
    )
    probe = gov._repetition_decision_probe(purpose, forged_repo)
    assert probe.status == gov.BLOCKED
    assert probe.code == gov.DIAGNOSTIC_REPETITION_DECISION_INCONSISTENT


def test_the_classification_rule_is_written_down_before_any_run(text):
    """§7 must state all four outcomes and the constraints that bind them."""
    for outcome in (
        "`QUALIFY`",
        "`REVISE / WEAK PRESSURE`",
        "`FAIL / ARCHITECTURE FLOOR`",
        "`INSUFFICIENT FUNCTIONAL VALIDITY`",
    ):
        assert outcome in text, f"the frozen rule must name {outcome}"
    assert "**No fourth observation**" in text
    assert "**not changed** after observing results" in text
    assert "Non-functional runs never inflate the violation count" in text
    assert "STOP / REASSESS" in text


def test_the_prohibited_analyses_are_named_as_prohibited(text):
    for banned in (
        "treatment-effect",
        "confidence interval",
        "power estimation",
        "`C2`",
        "`C3`",
        "`C4`",
    ):
        assert banned in text


# --------------------------------------------------------------------------- #
# 7. Nothing about the suite moved.
# --------------------------------------------------------------------------- #
def test_gate_g1_is_not_passed_and_is_reported_as_not_applicable():
    report = gov.check_readiness("PT09", "C1", PURPOSE_NAME)
    gate = next(p for p in report.prerequisites if p.item == "suite_wide_gate_g1")
    assert gate.status == gov.NOT_APPLICABLE
    assert "NOT PASSED" in gate.detail
    state = gov.manifest_freeze_state(
        "PT09", condition="C1", run_purpose=PURPOSE_NAME
    )
    assert state["global_frozen"] is False
    assert state["suite_frozen"] is False
    assert state["global_gate_g1_passed"] is False
    assert state["diagnostic_frozen"] is True
    assert state["changed_by_this_runner"] is False


@pytest.mark.parametrize(
    "decision_id", ["TD-B03", "TD-B05", "TD-B12", "TD-B32", "TD-B34"]
)
def test_the_blocking_decisions_stay_open(decision_id):
    assert gov.decision_is_open(decision_id), f"{decision_id} must still be open"


def test_the_public_lifecycle_rows_are_unchanged_at_validated():
    """`validated` records hidden-acceptance validation only. It is NOT a freeze."""
    for task_id in CANDIDATES:
        assert gov.manifest_is_frozen(task_id) is False
        row = gov.acceptance_matrix_row(task_id)
        assert row["status"].strip() == "validated"
        blob = " ".join(str(v) for v in row.values()).upper()
        assert "IS NOT A FREEZE" in blob
        assert "NOT E1 RUN-ELIGIBLE" in blob.replace("_", "-")


def test_the_active_e1_accounting_is_untouched_by_this_package():
    """The admitted register is 6 / 3 / 3-2-1 and this package changes no row.

    Read from the private register when it is present, because that is the
    authority; skipped rather than faked when it is not.
    """
    clusters = gov.default_private_root() / "docs" / "DECISION_CLUSTERS.json"
    if not clusters.is_file():
        pytest.skip("sibling private repository not present")
    data = json.loads(clusters.read_text(encoding="utf-8"))
    assert data["active_opportunity_count"] == 6
    assert data["active_cluster_count"] == 3
    depths = sorted(
        (c["observation_count"] for c in data["clusters"].values()), reverse=True
    )
    assert depths == [3, 2, 1]
    for task_id in CANDIDATES:
        assert task_id in data["staged_opportunities_excluded"] or any(
            task_id in json.dumps(c) for c in [data["staged_opportunities_excluded"]]
        ), f"{task_id} must still be STAGED and excluded from the active register"


def test_pt08_is_preserved_byte_for_byte():
    """SL-PT08-07: PT08's body, package and freeze record must not be touched."""
    import prepare_model_worktree as pmw

    assert pmw.sha256_file(gov.public_task_path("PT08")) == (
        "a31bb515b79cc1e211a662de2a8761c97082dd8bf266ee5b4f660981435badf2"
    )
    assert gov.DIAGNOSTIC_FREEZE_RECORD.is_file()
    pt08_freeze = gov.governed_diagnostic_freeze()
    assert pt08_freeze["diagnostic_freeze_authority"] == "SL-PT08-06"
    assert pt08_freeze["run_purpose"] == "PT08_DIFFICULTY_DIAGNOSTIC"


# --------------------------------------------------------------------------- #
# 8. The record is internally consistent.
# --------------------------------------------------------------------------- #
def test_every_run_purpose_row_in_the_record_names_this_purpose(text):
    """The firewall parse is section-scoped, but a contradictory row anywhere in
    the record would still be a documentation defect. There must be exactly one
    answer to 'what purpose is this?'."""
    rows = re.findall(r"^\|\s*`?run_purpose`?\s*\|(.+?)\|\s*$", text, re.MULTILINE)
    assert rows, "the record must table its run purpose"
    assert {r.strip().strip("`") for r in rows} == {PURPOSE_NAME}


def test_the_per_task_sections_the_runner_parses_all_exist(purpose, text):
    for task_id in CANDIDATES:
        for heading in (
            purpose.freeze_table_heading(task_id),
            purpose.freeze_config_heading(task_id),
        ):
            assert heading in text, f"{heading!r} is parsed by the runner and must exist"
    assert purpose.firewall_heading in text
    assert purpose.execution_decisions_heading in text


@pytest.mark.parametrize("task_id", CANDIDATES)
def test_the_frozen_configuration_agrees_with_the_applicability_table(purpose, task_id):
    """Two tables, one answer. A drift between them is a mechanical failure."""
    applicability = gov.governed_diagnostic_freeze(
        purpose.freeze_record_path(), purpose.freeze_table_heading(task_id)
    )
    frozen = gov.governed_diagnostic_freeze_configuration(
        purpose.freeze_record_path(), purpose.freeze_config_heading(task_id)
    )
    assert frozen["frozen_task_id"] == applicability["diagnostic_freeze_task"]
    assert frozen["frozen_task_sha256"] == applicability["diagnostic_freeze_task_sha256"]
    assert frozen["frozen_condition"] == applicability["diagnostic_freeze_condition"]
    assert frozen["frozen_run_purpose"] == applicability["run_purpose"]
    assert frozen["frozen_repetitions"] == applicability["diagnostic_freeze_repetitions"]
    assert frozen["frozen_exact_model_id"] == (
        applicability["diagnostic_freeze_exact_model_id"]
    )
    assert frozen["frozen_cli_version"] == applicability["diagnostic_freeze_cli_version"]
    # The substrate the freeze pins is the governed one, re-derived not trusted.
    assert frozen["frozen_substrate_commit"] == gov.SUBSTRATE_COMMIT
    assert frozen["frozen_substrate_content_hash"] == gov.SUBSTRATE_CONTENT_HASH
    assert frozen["frozen_substrate_entry_count"] == gov.SUBSTRATE_ENTRY_COUNT


def test_the_model_and_runtime_are_the_already_validated_ones(purpose):
    assert gov.diagnostic_primary_model(PURPOSE_NAME) == "claude-sonnet-5"
    q1, q8, cli = gov.live_runtime_validation(PURPOSE_NAME)
    assert (q1, q8, cli) == ("PASS", "PASS", "2.1.229")
    # And the global selection is still not made.
    assert gov.primary_model() is None
    assert gov.decision_is_open("TD-B03")


def test_an_alias_or_a_different_model_is_refused_per_repetition(purpose):
    freeze = gov.diagnostic_freeze_for(purpose, "PT09", "C1")
    assert freeze is not None and freeze.exact_model_id == "claude-sonnet-5"
    for bad in ("sonnet", "claude-opus-4-8", "claude-haiku-4-5-20251001"):
        problems = gov.diagnostic_freeze_execution_problems(freeze, model_id=bad)
        assert gov.DIAGNOSTIC_MODEL_ID_MISMATCH in {c for c, _ in problems}


def test_resume_continue_and_session_reuse_are_refused_per_repetition(purpose):
    freeze = gov.diagnostic_freeze_for(purpose, "PT10", "C1")
    assert freeze is not None
    for flag, code in (
        ("--resume", gov.SESSION_RESUME_REJECTED),
        ("--continue", gov.SESSION_CONTINUE_REJECTED),
    ):
        problems = gov.diagnostic_freeze_execution_problems(
            freeze, launch_argv=["claude", flag]
        )
        assert code in {c for c, _ in problems}
    problems = gov.diagnostic_freeze_execution_problems(
        freeze, session_id="s-1", previous_session_ids=["s-1"]
    )
    assert gov.SESSION_ID_REUSED in {c for c, _ in problems}


def test_a_non_clean_context_is_refused_per_repetition(purpose):
    freeze = gov.diagnostic_freeze_for(purpose, "PT09", "C1")
    problems = gov.diagnostic_freeze_execution_problems(
        freeze, context_verdict="CONTAMINATED"
    )
    assert gov.CONTEXT_AUDIT_CONTAMINATED in {c for c, _ in problems}
    problems = gov.diagnostic_freeze_execution_problems(
        freeze, require_all=True, require_context_verdict=True
    )
    assert gov.CONTEXT_AUDIT_UNKNOWN in {c for c, _ in problems}


def test_c1_delivers_no_architecture_content(purpose):
    """A qualification probe is the unguided baseline arm, by construction."""
    gov.assert_architecture_delivery_none("C1")
    assert gov.architecture_delivery_for("C1") == "none"
