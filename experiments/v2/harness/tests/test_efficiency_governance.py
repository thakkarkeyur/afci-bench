#!/usr/bin/env python3
"""``SL-V2-EFF-01``'s governance, as the runner actually re-derives it.

Nothing here trusts a constant in the harness on its own. Every governed value
is read back out of the decision record and compared, so a drift between the
code and the adjudication is a mechanical failure rather than a reading.

No model is invoked, nothing is scored, and no pilot observation is produced.
"""
from __future__ import annotations

import glob
import json
import shutil
import sys
from pathlib import Path

import pytest

HARNESS = Path(__file__).resolve().parents[1]
if str(HARNESS) not in sys.path:
    sys.path.insert(0, str(HARNESS))

import condition_prompt as cp  # noqa: E402
import efficiency_metrics as em  # noqa: E402
import model_adapter as ma  # noqa: E402
import prepare_model_worktree as pmw  # noqa: E402
import reset_budget as rb  # noqa: E402
import run_governance as gov  # noqa: E402
import run_v2  # noqa: E402
import stream_launcher as sl  # noqa: E402

PURPOSE = "AFCI_EFFICIENCY_PILOT"
TASKS = ("PT01", "PT04", "PT07")
CONDITIONS = ("C1", "C4")
MODEL = "claude-sonnet-5"
RUNTIME = "2.1.229"
CI = "npm run ci:agent"
RECORD = gov.REPO / "docs" / "v2" / "AFCI_EFFICIENCY_PILOT_DECISION.md"


# --------------------------------------------------------------------------- #
# The purpose, and its firewall
# --------------------------------------------------------------------------- #
def test_the_purpose_is_registered_and_non_confirmatory():
    purpose = gov.resolve_run_purpose(PURPOSE)
    assert purpose.decision_id == "SL-V2-EFF-01"
    assert purpose.confirmatory is False
    assert purpose.result_bearing is False
    assert purpose.permitted_tasks == TASKS
    assert purpose.permitted_conditions == CONDITIONS
    assert purpose.repetitions == 3
    assert all(value is False for _, value in purpose.firewall)


def test_the_firewall_is_re_derived_from_the_record():
    purpose = gov.resolve_run_purpose(PURPOSE)
    governed = gov.governed_firewall_from_record(
        purpose.firewall_record_path(), purpose.firewall_heading
    )
    assert governed["run_purpose"] == PURPOSE
    for field in gov.FIREWALL_FIELDS:
        assert governed[field] is False, field


def test_the_repetition_table_is_re_derived_from_the_record():
    purpose = gov.resolve_run_purpose(PURPOSE)
    governed = gov.governed_execution_decisions(
        purpose.execution_decisions_record_path(), purpose.execution_decisions_heading
    )
    assert governed["diagnostic_repetitions"] == 3
    assert governed["condition"] == "C1, C4"
    for key, expected in purpose.pins_for_repetitions():
        assert governed.get(key) == expected, key


@pytest.mark.parametrize("task", TASKS)
@pytest.mark.parametrize("condition", CONDITIONS)
def test_every_cell_has_its_own_resolvable_scoped_freeze(task, condition):
    purpose = gov.resolve_run_purpose(PURPOSE)
    problems = gov.diagnostic_freeze_problems(purpose, task, condition)
    assert problems == [], problems
    freeze = gov.diagnostic_freeze_for(purpose, task, condition)
    assert freeze is not None
    assert freeze.task_id == task and freeze.condition == condition
    assert freeze.exact_model_id == MODEL
    assert freeze.cli_version == RUNTIME
    assert freeze.repetitions == 3
    # The exception narrows applicability and grants nothing suite-wide.
    assert freeze.global_g1 is False
    assert freeze.suite_frozen is False
    assert freeze.global_manifest_frozen is False


@pytest.mark.parametrize("condition", CONDITIONS)
def test_the_record_pins_the_right_architecture_delivery_per_arm(condition):
    purpose = gov.resolve_run_purpose(PURPOSE)
    heading = purpose.freeze_table_heading("PT01", condition)
    table = gov.governed_diagnostic_freeze(RECORD, heading)
    assert table["diagnostic_freeze_architecture_delivery"] == (
        gov.architecture_delivery_for(condition)
    )


def test_a_cell_outside_the_matrix_has_no_scoped_freeze():
    purpose = gov.resolve_run_purpose(PURPOSE)
    for task, condition in (("PT08", "C1"), ("PT01", "C3"), ("PT09", "C4")):
        assert gov.diagnostic_freeze_for(purpose, task, condition) is None


def test_the_pilot_purpose_grants_nothing_to_the_other_purposes():
    """Adding a purpose must not widen the two that already existed."""
    pt08 = gov.RUN_PURPOSES["PT08_DIFFICULTY_DIAGNOSTIC"]
    qual = gov.RUN_PURPOSES["INSTRUMENT_QUALIFICATION_DIAGNOSTIC"]
    assert pt08.permitted_conditions == ("C1",)
    assert qual.permitted_conditions == ("C1",)
    for purpose in (pt08, qual):
        # Their freeze pins still include the static architecture-delivery pin.
        assert ("diagnostic_freeze_architecture_delivery", "none") in purpose.freeze_pins()
        for condition in ("C2", "C3", "C4"):
            with pytest.raises(gov.RunnerRefusal):
                gov.assert_task_and_condition_permitted(
                    purpose, purpose.permitted_tasks[0], condition
                )


# --------------------------------------------------------------------------- #
# Architecture delivery
# --------------------------------------------------------------------------- #
def test_c4_is_authorised_only_under_a_purpose_that_names_it():
    pilot = gov.resolve_run_purpose(PURPOSE)
    gov.assert_architecture_delivery_authorised(pilot, "C4")
    gov.assert_architecture_delivery_authorised(pilot, "C1")
    pt08 = gov.RUN_PURPOSES["PT08_DIFFICULTY_DIAGNOSTIC"]
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        gov.assert_architecture_delivery_authorised(pt08, "C4")
    assert excinfo.value.code == gov.ARCHITECTURE_DELIVERY_VIOLATION


def test_the_architecture_payload_is_the_approved_bytes():
    assert gov.architecture_context_sha256() == (
        "bf6f32b162a23b851596d8b489d938bef10d0b8616a50dcc039873d12ffa7a4d"
    )
    assert gov.architecture_payload_for("C1") is None
    assert gov.architecture_payload_for("C4") is not None


def test_a_c1_prompt_carrying_architecture_is_refused():
    """Fails closed in BOTH directions; either failure would be invisible."""
    body = b"do the thing\n"
    contaminated = cp.compose_task_prompt("C4", body)
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        cp.assert_architecture_payload("C1", contaminated)
    assert excinfo.value.code == gov.ARCHITECTURE_CONTEXT_HASH_MISMATCH

    demoted = cp.compose_task_prompt("C1", body)
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        cp.assert_architecture_payload("C4", demoted)
    assert excinfo.value.code == gov.ARCHITECTURE_CONTEXT_HASH_MISMATCH


def test_c4_prepares_a_worktree_with_no_persistent_architecture_file(tmp_path):
    result = pmw.prepare_model_worktree(
        pmw.PreparationRequest(
            condition="C4",
            source_root=gov.REPO,
            dest_root=tmp_path / "worktree",
            task_path=gov.public_task_path("PT01"),
            task_id="PT01",
            architecture_text=gov.architecture_payload_for("C4"),
        )
    )
    assert result.manifest["architecture_delivery"] == "prompt_injection"
    assert result.manifest["architecture_persistent_path"] is None
    assert result.manifest["architecture_sha256"] == gov.architecture_context_sha256()
    assert not (tmp_path / "worktree" / "CLAUDE.md").exists()
    names = {p.name for p in (tmp_path / "worktree").rglob("*") if p.is_file()}
    assert "ARCHITECTURE_CONTEXT.md" not in names
    assert "ARCHITECTURE_RULE_CATALOG.yml" not in names
    shutil.rmtree(tmp_path / "worktree", ignore_errors=True)


def test_the_continuation_wording_is_condition_neutral():
    body = b"the task body\n"
    c1 = cp.compose_continuation_prompt("C1", body)
    c4 = cp.compose_continuation_prompt("C4", body)
    # C4 is C1 with the architecture payload prepended, and NOTHING else changed.
    assert c4.endswith(c1)
    assert c4[: -len(c1)] == (
        cp.ARCHITECTURE_HEADER
        + gov.architecture_context_bytes().decode("utf-8")
        + cp.TASK_HEADER
    )
    assert cp.CONTINUATION_WORDING in c1 and cp.CONTINUATION_WORDING in c4


# --------------------------------------------------------------------------- #
# The launch the purpose builds
# --------------------------------------------------------------------------- #
def test_the_allowlist_reaches_the_launch_as_separate_tokens(tmp_path):
    prompt = tmp_path / "p.md"
    prompt.write_text("task\n", encoding="utf-8")
    plan = ma.build_fresh_launch(
        prompt_path=str(prompt),
        workspace=str(tmp_path),
        model_id=MODEL,
        sterile=True,
        permission_mode=ma.DIAGNOSTIC_PERMISSION_MODE,
        tools=ma.DIAGNOSTIC_TOOLS,
        allowed_tools=ma.bash_allow_rule(CI),
        max_turns=64,
    )
    argv = list(plan.argv)
    index = argv.index("--allowed-tools")
    assert argv[index + 1] == "Bash(npm run ci:agent)"
    assert argv[index + 2] == "Bash(npm run ci:agent:*)"
    assert argv[argv.index("--max-turns") + 1] == "64"
    # --tools is a DIFFERENT flag and still carries the tool SET.
    assert argv[argv.index("--tools") + 1] == "Read,Edit,Write,Glob,Grep,Bash"
    assert plan.allowed_tools == ma.bash_allow_rule(CI)


def test_no_allowlist_and_no_ceiling_unless_one_is_frozen(tmp_path):
    """Every purpose that freezes neither gets exactly the launch it had."""
    prompt = tmp_path / "p.md"
    prompt.write_text("task\n", encoding="utf-8")
    plan = ma.build_fresh_launch(
        prompt_path=str(prompt), workspace=str(tmp_path), model_id=MODEL,
        sterile=True, permission_mode="acceptEdits", tools=ma.DIAGNOSTIC_TOOLS,
    )
    argv = list(plan.argv)
    assert "--allowed-tools" not in argv
    assert "--max-turns" not in argv
    assert plan.allowed_tools == () and plan.max_turns is None


@pytest.mark.parametrize("bad", [0, -1, "8", 1.5, True])
def test_a_non_positive_turn_ceiling_is_refused(tmp_path, bad):
    prompt = tmp_path / "p.md"
    prompt.write_text("task\n", encoding="utf-8")
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        ma.build_fresh_launch(
            prompt_path=str(prompt), workspace=str(tmp_path), model_id=MODEL,
            max_turns=bad,
        )
    assert excinfo.value.code == gov.RESET_BUDGET_NOT_FROZEN


def test_the_frozen_cli_defaults_match_the_record():
    assert run_v2._frozen_allowed_tools(PURPOSE, "PT01") == ma.bash_allow_rule(CI)
    assert run_v2._frozen_allowed_tools("PT08_DIFFICULTY_DIAGNOSTIC", "PT08") == ()
    assert run_v2._frozen_max_turns(PURPOSE, rb.NON_RESET) == 64
    # A RESET run carries no OUTER ceiling: each phase carries its own.
    assert run_v2._frozen_max_turns(PURPOSE, rb.RESET) is None
    assert run_v2._frozen_max_turns("PT08_DIFFICULTY_DIAGNOSTIC", None) is None


# --------------------------------------------------------------------------- #
# The reset state is never defaulted
# --------------------------------------------------------------------------- #
def test_a_reset_aware_purpose_must_declare_its_arm():
    purpose = gov.resolve_run_purpose(PURPOSE)
    request = run_v2.RunRequest(
        task_id="PT01", condition="C1", run_purpose=PURPOSE, reset_state=None
    )
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        run_v2._resolve_reset_state(purpose, request)
    assert excinfo.value.code == gov.RESET_STATE_INVALID


def test_a_purpose_with_no_reset_authority_refuses_a_reset_state():
    purpose = gov.RUN_PURPOSES["PT08_DIFFICULTY_DIAGNOSTIC"]
    request = run_v2.RunRequest(
        task_id="PT08", condition="C1", run_purpose="PT08_DIFFICULTY_DIAGNOSTIC",
        reset_state=rb.RESET,
    )
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        run_v2._resolve_reset_state(purpose, request)
    assert excinfo.value.code == gov.RESET_NOT_AUTHORISED_FOR_PURPOSE
    request.reset_state = None
    assert run_v2._resolve_reset_state(purpose, request) is None


@pytest.mark.parametrize("bad", ["reset", "NONE", "", "PARTIAL", "RECOVERED"])
def test_only_the_two_governed_reset_states_exist(bad):
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        rb.assert_reset_state(bad)
    assert excinfo.value.code == gov.RESET_STATE_INVALID


def test_a_budget_is_refused_for_any_other_purpose():
    for purpose in ("PT08_DIFFICULTY_DIAGNOSTIC", "INSTRUMENT_QUALIFICATION_DIAGNOSTIC"):
        with pytest.raises(gov.RunnerRefusal) as excinfo:
            rb.turn_budget(run_purpose=purpose, reset_state=rb.NON_RESET)
        assert excinfo.value.code == gov.RESET_NOT_AUTHORISED_FOR_PURPOSE


def test_the_budget_is_re_derived_from_its_record():
    assert rb.budget_problems() == []
    for key, expected in rb.RESET_BUDGET_PINS:
        assert rb.governed_budget_table()[key] == expected, key


def test_a_drifted_budget_record_refuses(tmp_path):
    """A record whose numbers no longer add up has frozen nothing."""
    source = gov.REPO / rb.RESET_BUDGET_RECORD
    drifted = tmp_path / "drifted.md"
    drifted.write_text(
        source.read_text(encoding="utf-8").replace(
            "| `post_reset_max_turns` | `32` |", "| `post_reset_max_turns` | `48` |"
        ),
        encoding="utf-8",
    )
    problems = rb.budget_problems(record=drifted)
    assert problems, "a 32 + 48 against a 64 total was accepted"
    assert all(code == gov.RESET_BUDGET_NOT_FROZEN for code, _ in problems)
    with pytest.raises(gov.RunnerRefusal):
        rb.turn_budget(
            run_purpose=PURPOSE, reset_state=rb.RESET, phase=rb.PHASE_A, record=drifted
        )


# --------------------------------------------------------------------------- #
# Artifact quarantine
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "area", ["experiments/v2/results", "experiments/v2/analysis", "docs/v2", ""]
)
def test_the_confirmatory_areas_are_refused_as_artifact_roots(area):
    purpose = gov.resolve_run_purpose(PURPOSE)
    with pytest.raises(gov.RunnerRefusal):
        gov.assert_artifact_area_permitted(gov.REPO / area, purpose)


def test_the_results_and_analysis_directories_hold_only_their_readme():
    for name in ("results", "analysis"):
        directory = gov.REPO / "experiments" / "v2" / name
        assert sorted(p.name for p in directory.iterdir()) == ["README.md"], (
            f"an efficiency observation appeared in experiments/v2/{name}"
        )


def test_zero_pilot_observations_exist():
    """The state this session must leave behind, asserted rather than asserted of."""
    runs = list(gov.default_artifact_root().glob(f"{PURPOSE.lower().replace('_', '-')}*"))
    assert runs == [], f"a pilot observation exists: {runs}"


# --------------------------------------------------------------------------- #
# End to end, through the REAL state machine, with no model
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("condition", CONDITIONS)
@pytest.mark.parametrize("reset_state", [rb.NON_RESET, rb.RESET])
def test_a_dry_run_completes_for_every_arm(tmp_path, condition, reset_state):
    """Every safe pre-launch state runs, and no model process is created."""
    result = run_v2.run(
        run_v2.RunRequest(
            task_id="PT01",
            condition=condition,
            run_purpose=PURPOSE,
            mode="dry-run",
            reset_state=reset_state,
            repetition=2,
            artifact_root=tmp_path / "runs",
            audit_provider=lambda **kw: _clean_audit(),
            keep_worktree=False,
            allowed_tools=ma.bash_allow_rule(CI),
            max_turns=run_v2._frozen_max_turns(PURPOSE, reset_state),
        )
    )
    assert result.refusal_code is None, (result.refusal_code, result.refusal_detail)
    assert result.ok, [e for e in result.machine.log if e["result"] != "PASS"]
    record = result.record
    assert record["run_purpose"]["name"] == PURPOSE
    assert record["condition"] == condition
    assert record["repetition"] == 2
    assert record["outcome"]["is_result"] is False
    assert record["outcome"]["scored"] is False
    assert record["invocation"]["invoked"] is False

    # The arm is recorded as the arm it was ASSIGNED to, never inferred from
    # whether a phase happened to run.
    assert record["reset"]["reset_state"] == reset_state
    if reset_state == rb.NON_RESET:
        assert record["reset"]["max_turns"] == 64
        assert record["reset"]["single_process"] is True
    else:
        assert record["reset"]["pre_reset_turn_limit"] == 32
        assert record["reset"]["post_reset_turn_limit"] == 32
        assert record["reset"]["single_process"] is False
    assert record["reset"]["unused_pre_reset_transfers"] is False
    # A dry run measures nothing, and reports nothing rather than zeros.
    assert record.get("efficiency") is None

    # The prompt carries exactly what the condition should deliver.
    manifest = json.loads(
        (Path(record["worktree"]["prepared_root"]).parent / "prompt_manifest.json")
        .read_text(encoding="utf-8")
    )
    assert manifest["architecture_matches"] is True
    assert manifest["architecture_delivery"] == gov.architecture_delivery_for(condition)


def _clean_audit():
    class _Audit:
        def to_dict(self):
            return {"contamination": {"verdict": "CLEAN", "reasons": []}}

    return _Audit()


def test_a_real_run_without_the_frozen_allowlist_or_ceiling_is_refused(tmp_path):
    """Both checks fail CLOSED; the alternative reproduces the defect TD-B42 names."""
    base = dict(
        task_id="PT01",
        condition="C1",
        run_purpose=PURPOSE,
        mode="real",
        artifact_root=tmp_path / "runs",
        keep_worktree=False,
    )
    purpose = gov.resolve_run_purpose(PURPOSE)

    # No allowlist at all.
    request = run_v2.RunRequest(
        **base, reset_state=rb.NON_RESET, allowed_tools=(), max_turns=64
    )
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        run_v2._assert_frozen_launch_configuration(purpose, request, rb.NON_RESET)
    assert excinfo.value.code == gov.DIAGNOSTIC_FREEZE_RECORD_INCONSISTENT

    # A plausible-looking but different allowlist.
    request = run_v2.RunRequest(
        **base, reset_state=rb.NON_RESET,
        allowed_tools=("Bash(npm run ci)",), max_turns=64,
    )
    with pytest.raises(gov.RunnerRefusal):
        run_v2._assert_frozen_launch_configuration(purpose, request, rb.NON_RESET)

    # No ceiling on the arm that has one.
    request = run_v2.RunRequest(
        **base, reset_state=rb.NON_RESET,
        allowed_tools=ma.bash_allow_rule(CI), max_turns=None,
    )
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        run_v2._assert_frozen_launch_configuration(purpose, request, rb.NON_RESET)
    assert excinfo.value.code == gov.RESET_BUDGET_NOT_FROZEN

    # An outer ceiling on the arm that must not have one.
    request = run_v2.RunRequest(
        **base, reset_state=rb.RESET,
        allowed_tools=ma.bash_allow_rule(CI), max_turns=32,
    )
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        run_v2._assert_frozen_launch_configuration(purpose, request, rb.RESET)
    assert excinfo.value.code == gov.RESET_BUDGET_NOT_FROZEN

    # And the two frozen configurations pass.
    for state, turns in ((rb.NON_RESET, 64), (rb.RESET, None)):
        ok = run_v2.RunRequest(
            **base, reset_state=state,
            allowed_tools=ma.bash_allow_rule(CI), max_turns=turns,
        )
        run_v2._assert_frozen_launch_configuration(purpose, ok, state)


def test_a_real_run_is_refused_while_its_own_readiness_says_it_is_not_eligible():
    """The fail-OPEN this package closed, and the one blocker that stays allowed."""
    class Item:
        def __init__(self, item, code, detail=""):
            self.item, self.code, self.detail = item, code, detail

    class Report:
        def __init__(self, blocked):
            self.blocked = blocked

    # The context verdict alone is permitted through: CONTEXT_AUDIT runs next
    # and refuses on anything but CLEAN.
    run_v2._assert_readiness_permits_a_real_run(
        Report([Item("clean_isolated_context", gov.CONTEXT_AUDIT_UNKNOWN)])
    )
    run_v2._assert_readiness_permits_a_real_run(Report([]))

    for code in (
        gov.ARCHITECTURE_CORPUS_NOT_AVAILABLE,
        gov.PRIVATE_PUBLIC_SYNC_PROPAGATION_REQUIRED_BEFORE_FREEZE,
        gov.PRIVATE_LINKAGE_NOT_VERIFIABLE,
        gov.HIDDEN_ACCEPTANCE_NOT_VALIDATED,
        gov.MANIFEST_NOT_FROZEN,
    ):
        with pytest.raises(gov.RunnerRefusal) as excinfo:
            run_v2._assert_readiness_permits_a_real_run(
                Report([Item("x", code, "why")])
            )
        assert excinfo.value.code == code

    # Every outstanding blocker is reported at once, not one at a time.
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        run_v2._assert_readiness_permits_a_real_run(
            Report([
                Item("clean_isolated_context", gov.CONTEXT_AUDIT_UNKNOWN),
                Item("a", gov.ARCHITECTURE_CORPUS_NOT_AVAILABLE, "no corpus"),
                Item("b", gov.PRIVATE_PUBLIC_SYNC_PROPAGATION_REQUIRED_BEFORE_FREEZE, "no sync"),
            ])
        )
    message = excinfo.value.message
    assert "2 run-eligibility prerequisite(s)" in message
    assert "no corpus" in message and "no sync" in message
    assert "clean_isolated_context" not in message


@pytest.mark.parametrize("task", TASKS)
@pytest.mark.parametrize("condition", CONDITIONS)
def test_the_pilot_tasks_are_run_eligible_but_for_the_context_verdict(task, condition):
    """The state §12a predicted this test would reach, reached.

    Its predecessor asserted that the three instruments were NOT run-eligible:
    they had never been through the private pre-freeze public-sync propagation,
    and PT01/PT04 had no private architecture corpus. Its docstring said that
    when the private package work was done the test would fail, and that the
    failure was the signal to re-read the freeze rather than to delete the test.
    That is what happened, so it is re-read here rather than deleted.

    The sync item was discharged by PROPAGATION — each package now records it
    SATISFIED against a public commit the runner independently verifies is an
    ancestor of HEAD. The corpus item is `SL-V2-EFF-ELIG-01`'s narrowing, and it
    is asserted as `N/A` rather than `PASS`, because the corpus still does not
    exist and the requirement is unchanged everywhere it applies.

    The context verdict is the one blocker left, it is not of this kind, and
    `_assert_readiness_permits_a_real_run` lets exactly it through because
    `CONTEXT_AUDIT` runs the real audit moments later and refuses on anything
    but CLEAN.
    """
    report = gov.check_readiness(
        task, condition, PURPOSE, private_root=gov.default_private_root()
    )
    codes = {str(item.code) for item in report.blocked}
    assert codes == {gov.CONTEXT_AUDIT_UNKNOWN}, (
        f"{task}/{condition} carries a blocker other than the context verdict: "
        f"{[(i.item, i.code, i.detail) for i in report.blocked]}"
    )
    statuses = {item.item: item.status for item in report.prerequisites}
    assert statuses["private_sync_propagation_before_freeze"] == gov.PASS
    assert statuses["pilot_architecture_validation"] == gov.PASS
    # PT07 ships a corpus; PT01 and PT04 do not and are exempt, never "passed".
    assert statuses["architecture_corpus_availability"] == (
        gov.PASS if task == "PT07" else gov.NOT_APPLICABLE
    )
    # And the narrowing claims nothing: G1 is still not passed.
    assert statuses["suite_wide_gate_g1"] == gov.NOT_APPLICABLE


@pytest.mark.parametrize("task", TASKS)
@pytest.mark.parametrize("condition", CONDITIONS)
def test_a_clean_context_verdict_leaves_no_blocker_at_all(task, condition):
    """The whole frozen matrix, with the one deferred verdict supplied."""
    report = gov.check_readiness(
        task, condition, PURPOSE,
        private_root=gov.default_private_root(), context_verdict="CLEAN",
    )
    assert report.blocked == [], [(i.item, i.code) for i in report.blocked]
    assert report.run_eligible is True


def test_a_dry_run_refuses_a_condition_the_purpose_does_not_authorise(tmp_path):
    result = run_v2.run(
        run_v2.RunRequest(
            task_id="PT01",
            condition="C3",
            run_purpose=PURPOSE,
            mode="dry-run",
            reset_state=rb.NON_RESET,
            artifact_root=tmp_path / "runs",
            keep_worktree=False,
        )
    )
    assert result.refusal_code == gov.CONDITION_NOT_PERMITTED_FOR_PURPOSE


def test_a_dry_run_refuses_a_task_the_purpose_does_not_authorise(tmp_path):
    result = run_v2.run(
        run_v2.RunRequest(
            task_id="PT08",
            condition="C1",
            run_purpose=PURPOSE,
            mode="dry-run",
            reset_state=rb.NON_RESET,
            artifact_root=tmp_path / "runs",
            keep_worktree=False,
        )
    )
    assert result.refusal_code == gov.TASK_NOT_PERMITTED_FOR_PURPOSE


# --------------------------------------------------------------------------- #
# Part O: the extractor against the REAL saved live artifacts
# --------------------------------------------------------------------------- #
#: The nine executed live runs, outside both repositories by the quarantine
#: policy. Absent on any other machine, which is why this skips rather than
#: fails: the validation is real where the artifacts are, and honestly reported
#: as not performed where they are not.
LIVE_ARTIFACTS = sorted(
    glob.glob(r"D:\afci-v2-qual\runs\*\runtime_evidence.jsonl")
    + glob.glob(r"D:\pt08-diagnostic\runs\*\*\runtime_evidence.jsonl")
)


@pytest.mark.skipif(not LIVE_ARTIFACTS, reason="saved live artifacts not on this host")
@pytest.mark.parametrize("path", LIVE_ARTIFACTS)
def test_the_extractor_reads_every_saved_live_artifact(path):
    events = sl.load_events(path)
    measurement = em.measure_non_reset(events, model_id=MODEL, ci_command=CI)
    usage = measurement.usage

    # Re-derived independently of the extractor, from the raw event.
    raw = [e for e in events if e.get("type") == "result"][-1]["usage"]
    assert usage.total_input_tokens == (
        raw["input_tokens"]
        + raw["cache_creation_input_tokens"]
        + raw["cache_read_input_tokens"]
    )
    # The subcomponents sum to their parent, which is why adding them would
    # double-count. Asserted on the real data rather than on a fixture.
    breakdown = raw.get("cache_creation") or {}
    if breakdown:
        assert sum(breakdown.values()) == raw["cache_creation_input_tokens"]

    assert usage.model_usage_mirror_consistent is True
    assert usage.model_id == MODEL
    assert usage.cost_usd and usage.cost_usd > 0
    assert measurement.unknown_event_types == []
    assert measurement.turns > 0
    assert measurement.tools.total_tool_calls > 0


@pytest.mark.skipif(not LIVE_ARTIFACTS, reason="saved live artifacts not on this host")
@pytest.mark.parametrize("path", LIVE_ARTIFACTS)
def test_partial_reconstruction_is_exact_on_every_saved_artifact(path):
    """The property a reset's phase-A measurement depends on."""
    events = sl.load_events(path)
    full = em.extract_usage(events, expected_model_id=MODEL)
    partial = em.extract_partial_usage(events)
    assert partial.total_input_tokens == full.total_input_tokens
    assert partial.output_tokens is None


@pytest.mark.skipif(not LIVE_ARTIFACTS, reason="saved live artifacts not on this host")
def test_the_recorded_permission_finding_is_true_of_the_artifacts():
    """TD-B42's measurement, re-derived rather than cited.

    44 `ci:agent` attempts, 0 executions, across all nine executed live runs:
    `PT09` 10/3/5, `PT10` 3/5/3, `PT08` 7/5/3.
    """
    attempts = 0
    executed = 0
    for path in LIVE_ARTIFACTS:
        events = sl.load_events(path)
        uses = {}
        for event in events:
            if event.get("type") != "assistant":
                continue
            for block in (event.get("message") or {}).get("content") or []:
                if (
                    isinstance(block, dict)
                    and block.get("type") == "tool_use"
                    and block.get("name") == "Bash"
                    and CI in str((block.get("input") or {}).get("command", ""))
                ):
                    uses[block["id"]] = True
        attempts += len(uses)
        for event in events:
            if event.get("type") != "user":
                continue
            for block in (event.get("message") or {}).get("content") or []:
                if (
                    isinstance(block, dict)
                    and block.get("type") == "tool_result"
                    and block.get("tool_use_id") in uses
                    and not block.get("is_error")
                ):
                    executed += 1
    assert len(LIVE_ARTIFACTS) == 9
    assert attempts == 44, attempts
    assert executed == 0, executed
    # The figure the governance records cite must be the figure measured here.
    for citation in (
        gov.REPO / "docs" / "v2" / "AFCI_EFFICIENCY_PILOT_DECISION.md",
        gov.REPO / "docs" / "v2" / "OPEN_DECISIONS.md",
    ):
        body = citation.read_text(encoding="utf-8")
        assert f"{attempts} attempts, 0 executions" in body or (
            f"attempted **{attempts} times and executed 0 times**" in body
        ), f"{citation.name} cites a different attempt count"
