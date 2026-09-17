"""`SL-V2-LOWER-MODEL-01` - the lower-capability-model pilot, before any data.

What this file pins, and why each item is here rather than trusted:

  * the purpose exists, is NON-CONFIRMATORY on every axis, and its firewall is
    re-derived from the authorising record rather than from the runner's own
    constants;
  * the matrix is PT01/PT04/PT07 x C1/C4 x NON_RESET x 3, and the reset arm is
    refused rather than silently unused;
  * the model is pinned by its EXACT id, that id is the one the registry carries,
    and pinning it selects no primary model;
  * the turn ceiling is the Sonnet pilot's own 64, identical in both arms, and it
    was not lowered because the model is cheaper;
  * the corpus exemption is this purpose's OWN, adjudicated in its own record;
  * the continuation rule is frozen, in full, before any observation exists;
  * nothing pools with the Sonnet efficiency pilot;
  * ZERO lower-model observations exist.

No model is invoked and no benchmark task is executed.
"""
import json
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[4]
HARNESS = REPO / "experiments" / "v2" / "harness"
sys.path.insert(0, str(HARNESS))

import architecture_evaluation as ae  # noqa: E402
import functional_evaluation as fe  # noqa: E402
import lower_model_run_plan as lmp  # noqa: E402
import reset_budget as rb  # noqa: E402
import run_governance as gov  # noqa: E402
import run_v2  # noqa: E402

PURPOSE = "AFCI_LOWER_MODEL_PILOT"
AUTHORITY = "SL-V2-LOWER-MODEL-01"
RECORD = REPO / "docs" / "v2" / "AFCI_LOWER_MODEL_PILOT_DECISION.md"
MODEL = "claude-haiku-4-5-20251001"
TASKS = ("PT01", "PT04", "PT07")
CONDITIONS = ("C1", "C4")

#: The Sonnet pilot, named so every "not pooled with" assertion points at a real
#: registered purpose rather than at a phrase.
SONNET_PURPOSE = "AFCI_EFFICIENCY_PILOT"


def _text() -> str:
    return RECORD.read_text(encoding="utf-8")


def _flat() -> str:
    return re.sub(r"\s+", " ", _text())


# --------------------------------------------------------------------------- 1
# The purpose exists, and is non-confirmatory on every axis
# --------------------------------------------------------------------------- #
def test_the_purpose_is_registered_and_carries_its_authority():
    purpose = gov.resolve_run_purpose(PURPOSE)
    assert purpose.decision_id == AUTHORITY
    assert purpose.permitted_tasks == TASKS
    assert purpose.permitted_conditions == CONDITIONS
    assert purpose.repetitions == 3


def test_the_purpose_is_quarantined_on_every_axis():
    purpose = gov.resolve_run_purpose(PURPOSE)
    assert purpose.confirmatory is False
    assert purpose.result_bearing is False
    assert purpose.firewall_flags() == {f: False for f in gov.FIREWALL_FIELDS}
    assert gov.artifact_schema_problems(purpose) == []


def test_the_firewall_is_re_derived_from_the_authorising_record():
    """The runner's constants are not trusted on their own."""
    purpose = gov.resolve_run_purpose(PURPOSE)
    governed = gov.governed_firewall_from_record(
        purpose.firewall_record_path(REPO), purpose.firewall_heading
    )
    assert governed.get("run_purpose") == PURPOSE
    for flag in gov.FIREWALL_FIELDS:
        assert governed.get(flag) is False, flag


def test_a_task_or_condition_outside_the_authority_is_refused():
    purpose = gov.resolve_run_purpose(PURPOSE)
    for task in ("PT08", "PT09", "PT02", "PR01"):
        with pytest.raises(gov.RunnerRefusal) as excinfo:
            gov.assert_task_and_condition_permitted(purpose, task, "C1")
        assert excinfo.value.code == gov.TASK_NOT_PERMITTED_FOR_PURPOSE
    for condition in ("C2", "C3"):
        with pytest.raises(gov.RunnerRefusal) as excinfo:
            gov.assert_task_and_condition_permitted(purpose, "PT01", condition)
        assert excinfo.value.code == gov.CONDITION_NOT_PERMITTED_FOR_PURPOSE


# --------------------------------------------------------------------------- 2
# One arm, and the other is refused rather than merely unused
# --------------------------------------------------------------------------- #
def test_the_reset_arm_is_refused_not_merely_unscheduled():
    purpose = gov.resolve_run_purpose(PURPOSE)
    request = run_v2.RunRequest(
        task_id="PT01", condition="C1", run_purpose=PURPOSE, reset_state=rb.RESET
    )
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        run_v2._resolve_reset_state(purpose, request)
    assert excinfo.value.code == gov.RESET_NOT_AUTHORISED_FOR_PURPOSE


def test_the_arm_is_never_defaulted():
    """A purpose that declares a reset state must be told which one."""
    purpose = gov.resolve_run_purpose(PURPOSE)
    request = run_v2.RunRequest(
        task_id="PT01", condition="C1", run_purpose=PURPOSE, reset_state=None
    )
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        run_v2._resolve_reset_state(purpose, request)
    assert excinfo.value.code == gov.RESET_STATE_INVALID


def test_the_non_reset_arm_resolves():
    purpose = gov.resolve_run_purpose(PURPOSE)
    request = run_v2.RunRequest(
        task_id="PT01", condition="C4", run_purpose=PURPOSE, reset_state=rb.NON_RESET
    )
    assert run_v2._resolve_reset_state(purpose, request) == rb.NON_RESET


def test_no_reset_allowance_exists_for_this_purpose():
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        rb.turn_budget(
            run_purpose=PURPOSE, reset_state=rb.RESET, phase=rb.PHASE_A
        )
    assert excinfo.value.code == gov.RESET_NOT_AUTHORISED_FOR_PURPOSE


# --------------------------------------------------------------------------- 3
# The model
# --------------------------------------------------------------------------- #
def test_the_model_is_pinned_by_its_exact_id_and_confers_no_primary_selection():
    assert gov.diagnostic_primary_model(PURPOSE) == MODEL
    assert MODEL in gov.governed_model_ids()
    # The confirmatory selection is untouched.
    assert gov.primary_model() is None


def test_the_live_runtime_controls_are_recorded_for_this_purpose():
    q1, q8, cli = gov.live_runtime_validation(PURPOSE)
    assert q1 == "PASS"
    assert q8 == "PASS"
    assert cli == "2.1.229"


def test_the_record_states_how_the_model_was_found_rather_than_asserting_it():
    """A model identity that was guessed is a model identity nobody can check."""
    flat = _flat()
    assert "read as bytes" in flat or "enumerated" in flat
    assert "No Haiku 5 or any newer" in flat
    assert MODEL in flat
    # The probe is recorded as an infrastructure probe, not as an observation.
    assert "infrastructure-only" in flat
    assert "study observation created" in flat


def test_the_record_does_not_claim_q8_was_re_performed():
    flat = _flat()
    assert "cited, not re-performed" in flat


# --------------------------------------------------------------------------- 4
# The turn budget
# --------------------------------------------------------------------------- #
def test_the_budget_is_re_derived_from_the_record():
    assert rb.budget_problems(run_purpose=PURPOSE) == []
    governed = rb.governed_budget_table(run_purpose=PURPOSE)
    for key, want in rb.LOWER_MODEL_BUDGET_PINS:
        assert governed[key] == want, key


def test_the_ceiling_is_the_sonnet_pilots_own_and_identical_across_conditions():
    ceiling = rb.turn_budget(run_purpose=PURPOSE, reset_state=rb.NON_RESET).max_turns
    assert ceiling == 64
    assert ceiling == rb.turn_budget(
        run_purpose=SONNET_PURPOSE, reset_state=rb.NON_RESET
    ).max_turns
    # The launch-time value the runner would actually impose, for both arms.
    assert run_v2._frozen_max_turns(PURPOSE, rb.NON_RESET) == 64
    governed = rb.governed_budget_table(run_purpose=PURPOSE)
    assert governed["allowances_identical_across_conditions"] is True
    assert governed["budget_lowered_because_the_model_is_cheaper"] is False


def test_a_drifted_budget_record_refuses(tmp_path):
    drifted = tmp_path / "drifted.md"
    drifted.write_text(
        _text().replace(
            "| `non_reset_max_turns` | `64` |", "| `non_reset_max_turns` | `24` |"
        ),
        encoding="utf-8",
    )
    problems = rb.budget_problems(record=drifted, run_purpose=PURPOSE)
    assert problems
    assert all(code == gov.RESET_BUDGET_NOT_FROZEN for code, _ in problems)
    with pytest.raises(gov.RunnerRefusal):
        rb.turn_budget(
            run_purpose=PURPOSE, reset_state=rb.NON_RESET, record=drifted
        )


def test_the_permission_allowlist_is_the_sonnet_pilots_unchanged():
    for task in TASKS:
        mine = run_v2._frozen_allowed_tools(PURPOSE, task)
        theirs = run_v2._frozen_allowed_tools(SONNET_PURPOSE, task)
        assert mine == theirs and mine, task
    # ...and no other purpose acquired one.
    assert run_v2._frozen_allowed_tools("PT08_DIFFICULTY_DIAGNOSTIC", "PT08") == ()


# --------------------------------------------------------------------------- 5
# The scoped freeze, per cell
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("task", TASKS)
@pytest.mark.parametrize("condition", CONDITIONS)
def test_every_cell_has_a_scoped_freeze_that_re_derives(task, condition):
    purpose = gov.resolve_run_purpose(PURPOSE)
    assert gov.diagnostic_freeze_problems(purpose, task, condition) == []
    freeze = gov.diagnostic_freeze_for(purpose, task, condition)
    assert freeze is not None
    assert freeze.authority == AUTHORITY
    assert freeze.exact_model_id == MODEL
    assert freeze.cli_version == "2.1.229"
    assert freeze.repetitions == 3
    # And it claims no suite-wide state.
    assert freeze.global_g1 is False
    assert freeze.suite_frozen is False
    assert freeze.global_manifest_frozen is False


@pytest.mark.parametrize(
    "condition,expected", [("C1", "none"), ("C4", "prompt_injection")]
)
def test_the_two_arms_pin_different_architecture_deliveries(condition, expected):
    """The one value a freeze table exists to pin, and the reason there are six."""
    purpose = gov.resolve_run_purpose(PURPOSE)
    assert gov.architecture_delivery_for(condition) == expected
    governed = gov.governed_diagnostic_freeze(
        purpose.freeze_record_path(REPO),
        purpose.freeze_table_heading("PT01", condition),
    )
    assert governed["diagnostic_freeze_architecture_delivery"] == expected


def test_a_freeze_record_that_claimed_a_suite_wide_gate_is_refused(tmp_path):
    purpose = gov.resolve_run_purpose(PURPOSE)
    forged = tmp_path / "forged.md"
    forged.write_text(
        _text().replace("| `global_g1` | `false` |", "| `global_g1` | `true` |"),
        encoding="utf-8",
    )
    problems = gov.diagnostic_freeze_problems(
        purpose, "PT01", "C1", record=forged
    )
    assert any(
        code == gov.SUITE_WIDE_G1_MUST_NOT_BE_CLAIMED for code, _ in problems
    ), problems


def test_a_freeze_record_that_pinned_another_model_is_refused(tmp_path):
    purpose = gov.resolve_run_purpose(PURPOSE)
    forged = tmp_path / "forged.md"
    forged.write_text(_text().replace(MODEL, "claude-sonnet-5"), encoding="utf-8")
    problems = gov.diagnostic_freeze_problems(
        purpose, "PT01", "C1", record=forged
    )
    assert any(code == gov.DIAGNOSTIC_MODEL_ID_MISMATCH for code, _ in problems)


# --------------------------------------------------------------------------- 6
# The corpus exemption is this purpose's own
# --------------------------------------------------------------------------- #
def test_the_exemption_is_this_purposes_own_and_not_inherited():
    purpose = gov.resolve_run_purpose(PURPOSE)
    assert purpose.architecture_corpus_exemption == AUTHORITY
    assert purpose.architecture_corpus_exemption_record == (
        "docs/v2/AFCI_LOWER_MODEL_PILOT_DECISION.md"
    )
    sonnet = gov.RUN_PURPOSES[SONNET_PURPOSE]
    assert purpose.architecture_corpus_exemption != sonnet.architecture_corpus_exemption
    assert (
        purpose.architecture_corpus_exemption_record
        != sonnet.architecture_corpus_exemption_record
    )


@pytest.mark.parametrize("task", TASKS)
def test_the_eight_conditions_hold_for_every_instrument(task):
    purpose = gov.resolve_run_purpose(PURPOSE)
    assert gov.architecture_corpus_exemption_problems(purpose, task) == []


def test_the_exemption_table_re_derives_field_by_field():
    purpose = gov.resolve_run_purpose(PURPOSE)
    governed = gov._table_values(
        gov._section(_text(), purpose.architecture_corpus_exemption_heading)
    )
    assert governed, "the eligibility rule table is absent"
    for key, want in purpose.architecture_corpus_exemption_pins:
        assert governed[key] == want, f"{key}: record={governed.get(key)!r} want={want!r}"


def test_a_record_claiming_a_global_waiver_is_refused(tmp_path, monkeypatch):
    """The narrowing must stay a narrowing, or the exemption stops existing."""
    purpose = gov.resolve_run_purpose(PURPOSE)
    forged = tmp_path / "forged.md"
    forged.write_text(
        _text().replace(
            "| `architecture_corpus_requirement_waived_globally` | `false` |",
            "| `architecture_corpus_requirement_waived_globally` | `true` |",
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        type(purpose), "corpus_exemption_record_path", lambda self, repo=REPO: forged
    )
    problems = gov.architecture_corpus_exemption_problems(purpose, "PT01")
    assert any("waived_globally" in p for p in problems), problems


# --------------------------------------------------------------------------- 7
# Both measurement channels are on, and they are separate
# --------------------------------------------------------------------------- #
def test_both_channels_are_authorised_for_this_purpose():
    purpose = gov.resolve_run_purpose(PURPOSE)
    assert fe.purpose_requires_functional_evaluation(purpose)
    assert ae.purpose_requires_architecture_evaluation(purpose)
    assert purpose.produces_architecture_result is True
    assert purpose.architecture_evaluation_authority == AUTHORITY


def test_the_efficiency_pilot_gains_no_architecture_channel():
    """The COST-ONLY purpose stays cost-only; this package widens nothing."""
    sonnet = gov.RUN_PURPOSES[SONNET_PURPOSE]
    assert sonnet.architecture_evaluation_authority is None
    assert ae.purpose_requires_architecture_evaluation(sonnet) is False
    assert sonnet.produces_architecture_result is False


def test_no_other_purpose_gained_either_channel():
    for name, purpose in gov.RUN_PURPOSES.items():
        if name in (PURPOSE, SONNET_PURPOSE):
            continue
        assert purpose.architecture_evaluation_authority is None, name
        assert purpose.functional_evaluation_authority is None, name


def test_functional_validity_is_adopted_unchanged_rather_than_redefined():
    """A second definition of 'did it work?' would make the two pilots
    incomparable, which is exactly what the cross-model comparison needs them
    not to be."""
    purpose = gov.resolve_run_purpose(PURPOSE)
    sonnet = gov.RUN_PURPOSES[SONNET_PURPOSE]
    assert (
        purpose.functional_evaluation_authority
        == sonnet.functional_evaluation_authority
        == "SL-V2-EFF-FUNC-01"
    )
    assert purpose.functional_evaluation_record == sonnet.functional_evaluation_record


# --------------------------------------------------------------------------- 8
# The repetition decision, re-derived
# --------------------------------------------------------------------------- #
def test_the_repetition_table_re_derives_and_names_one_arm():
    purpose = gov.resolve_run_purpose(PURPOSE)
    governed = gov.governed_execution_decisions(
        purpose.execution_decisions_record_path(REPO),
        purpose.execution_decisions_heading,
    )
    assert governed["diagnostic_repetitions"] == 3
    assert governed["reset_states"] == "NON_RESET"
    for key, want in purpose.pins_for_repetitions():
        assert governed[key] == want, key


# --------------------------------------------------------------------------- 9
# The frozen continuation rule
# --------------------------------------------------------------------------- #
def test_the_continuation_rule_is_frozen_in_full_before_any_data():
    flat = _flat()
    # Two independent signals, either sufficient.
    assert "QUALITY SIGNAL" in flat and "EFFICIENCY SIGNAL" in flat
    # The quality clauses.
    assert "fewer** target architecture-violation runs" in flat
    assert "at least 2 of the 3 tasks" in flat
    assert flat.count("no more than 1 below") >= 2
    # The efficiency clauses, with their exact thresholds and directions.
    assert "median `TOKEN_RATIO` **< 1.00**" in flat
    assert "median `EXPLORATION_RATIO` **\u2264 0.80**" in flat
    assert "median `TOTAL_TOOL_RATIO` **\u2264 0.85**" in flat
    # ...and the otherwise branch, including what it does NOT authorise.
    assert "DO NOT EXPAND THE SYNTHETIC LOWER-MODEL MATRIX AUTOMATICALLY" in flat
    assert "open-source" in flat and "is **not** authorised by this record" in flat


def test_the_two_questions_are_never_collapsed_into_one_score():
    flat = _flat()
    assert "combined into no single score" in flat or "combines them into no single score" in flat
    assert "never** combined into one score" in flat
    plan = lmp.load_plan(REPO)
    assert plan["channels_combined_into_one_score"] is False


def test_no_p_values_or_confidence_intervals_are_promised():
    flat = _flat()
    assert "No p-values. No confidence intervals. No confirmatory effect claim." in flat


# --------------------------------------------------------------------------- 10
# The Sonnet comparison is descriptive, and never pooled
# --------------------------------------------------------------------------- #
def test_the_sonnet_comparison_is_descriptive_and_never_pooled():
    flat = _flat()
    assert "NEVER pooled into one treatment estimate" in flat
    assert "Within Sonnet" in flat and "Within lower model" in flat
    assert "1.5582" in flat, "the historical reference must be stated"
    # Every OTHER Sonnet value is read from the stored package at comparison
    # time, so no number in this record can go stale against its evidence.
    assert "read out of the stored package at comparison time" in flat
    assert "study-results/05_efficiency_attempt_2_completed/" in flat


def test_the_record_states_the_one_asymmetry_of_the_comparison():
    """The Sonnet pilot produced no architecture value, so half the comparison
    has no counterpart. A reader must not have to notice that themselves."""
    flat = _flat()
    assert "no architecture measurement at all" in flat
    assert "lower-model only" in flat


def test_the_sonnet_records_are_not_reinterpreted():
    flat = _flat()
    assert "UNCHANGED, NOT RE-READ, NOT RE-INTERPRETED" in flat


def test_the_purpose_is_not_the_efficiency_pilots():
    """A second model under one purpose marker would make two experiments
    indistinguishable in every artifact that carries only the purpose."""
    assert PURPOSE != SONNET_PURPOSE
    assert PURPOSE in gov.RUN_PURPOSES and SONNET_PURPOSE in gov.RUN_PURPOSES
    assert (
        gov.diagnostic_primary_model(PURPOSE)
        != gov.diagnostic_primary_model(SONNET_PURPOSE)
    )


# --------------------------------------------------------------------------- 11
# Readiness, and the artifact quarantine
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("task", TASKS)
@pytest.mark.parametrize("condition", CONDITIONS)
def test_every_cell_is_run_eligible_but_for_the_live_context_verdict(task, condition):
    report = gov.check_readiness(task, condition, PURPOSE)
    blocked = {str(p.code) for p in report.blocked}
    assert blocked <= {gov.CONTEXT_AUDIT_UNKNOWN}, (
        f"{task}/{condition} carries an unexpected blocker: "
        + "; ".join(f"<{p.code}> {p.item}: {p.detail}" for p in report.blocked)
    )


@pytest.mark.parametrize("task", TASKS)
@pytest.mark.parametrize("condition", CONDITIONS)
def test_a_clean_context_verdict_leaves_no_blocker_at_all(task, condition):
    report = gov.check_readiness(task, condition, PURPOSE, context_verdict="CLEAN")
    assert report.run_eligible, [
        f"<{p.code}> {p.item}: {p.detail}" for p in report.blocked
    ]


@pytest.mark.parametrize(
    "area", ["experiments/v2/results", "experiments/v2/analysis", "docs/v2", ""]
)
def test_the_confirmatory_areas_are_refused_as_artifact_roots(area):
    purpose = gov.resolve_run_purpose(PURPOSE)
    with pytest.raises(gov.RunnerRefusal):
        gov.assert_artifact_area_permitted(REPO / area, purpose)


def test_the_purpose_requires_an_isolated_execution_root():
    purpose = gov.resolve_run_purpose(PURPOSE)
    assert purpose.requires_isolated_execution_root == AUTHORITY


# --------------------------------------------------------------------------- 11a
# End to end through the REAL state machine, with no model
# --------------------------------------------------------------------------- #
def _clean_audit():
    class _Audit:
        def to_dict(self):
            return {"contamination": {"verdict": "CLEAN", "reasons": []}}

    return _Audit()


@pytest.mark.parametrize("task", TASKS)
@pytest.mark.parametrize("condition", CONDITIONS)
def test_a_dry_run_completes_for_every_cell(tmp_path, task, condition):
    """Every safe pre-launch state runs, and no model process is created."""
    result = run_v2.run(
        run_v2.RunRequest(
            task_id=task,
            condition=condition,
            run_purpose=PURPOSE,
            mode="dry-run",
            reset_state=rb.NON_RESET,
            repetition=2,
            execution_attempt=1,
            artifact_root=tmp_path / "runs",
            audit_provider=lambda **kw: _clean_audit(),
            keep_worktree=False,
            allowed_tools=run_v2._frozen_allowed_tools(PURPOSE, task),
            max_turns=run_v2._frozen_max_turns(PURPOSE, rb.NON_RESET),
        )
    )
    assert result.refusal_code is None, (result.refusal_code, result.refusal_detail)
    assert result.ok, [e for e in result.machine.log if e["result"] != "PASS"]

    record = result.record
    assert record["run_purpose"]["name"] == PURPOSE
    assert record["run_purpose"]["confirmatory"] is False
    assert record["condition"] == condition
    assert record["repetition"] == 2
    assert record["execution_attempt"] == 1
    assert record["outcome"]["is_result"] is False
    assert record["outcome"]["scored"] is False
    assert record["invocation"]["invoked"] is False

    # The frozen launch configuration, as the record actually carries it.
    assert record["fresh_launch"]["max_turns"] == 64
    assert record["fresh_launch"]["allowed_tools"] == list(
        run_v2._frozen_allowed_tools(PURPOSE, task)
    )
    assert record["reset"]["reset_state"] == rb.NON_RESET
    assert record["reset"]["single_process"] is True

    # A dry run measures nothing, and reports nothing rather than zeros.
    assert record.get("efficiency") is None
    architecture = record["architecture_evaluation"]
    assert architecture["architecture_scored"] is False
    assert architecture["architecture_violation_present"] is None
    assert architecture["architecture_violated_opportunity_count"] is None
    assert architecture["runtime_error"]["code"] == (
        ae.ARCHITECTURE_EVALUATION_NO_WORKTREE
    )
    # ...and both channels are present and independent.
    assert record["functional_evaluation"]["functional_valid"] is False
    assert record["functional_evaluation"]["architecture_scored"] is False


def test_a_dry_run_delivers_exactly_the_conditions_payload(tmp_path):
    """C1 receives no architecture payload; C4 receives the approved bytes."""
    for condition in CONDITIONS:
        result = run_v2.run(
            run_v2.RunRequest(
                task_id="PT01",
                condition=condition,
                run_purpose=PURPOSE,
                mode="dry-run",
                reset_state=rb.NON_RESET,
                repetition=1,
                artifact_root=tmp_path / condition,
                audit_provider=lambda **kw: _clean_audit(),
                keep_worktree=False,
                allowed_tools=run_v2._frozen_allowed_tools(PURPOSE, "PT01"),
                max_turns=run_v2._frozen_max_turns(PURPOSE, rb.NON_RESET),
            )
        )
        assert result.ok, result.refusal_detail
        manifest_path = (
            Path(result.record["worktree"]["prepared_root"]).parent
            / "prompt_manifest.json"
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["architecture_matches"] is True
        assert manifest["architecture_delivery"] == gov.architecture_delivery_for(
            condition
        )


# --------------------------------------------------------------------------- 12
# Zero observations
# --------------------------------------------------------------------------- #
def test_zero_lower_model_observations_exist():
    """The state this package must leave behind, asserted rather than asserted of."""
    slug = PURPOSE.lower().replace("_", "-")
    roots = [gov.default_artifact_root(), Path(r"D:\afci-runs\lower-model-pilot")]
    found = []
    for root in roots:
        if root.exists():
            found += [p.name for p in root.glob(f"{slug}*")]
    assert found == [], f"a lower-model observation exists: {found}"


def test_the_record_states_zero_observations():
    assert "Lower-model pilot observations at the time of writing: **ZERO**" in _text()


def test_the_results_and_analysis_directories_still_hold_only_their_readme():
    for name in ("results", "analysis"):
        directory = REPO / "experiments" / "v2" / name
        assert sorted(p.name for p in directory.iterdir()) == ["README.md"], (
            f"an observation appeared in experiments/v2/{name}"
        )
