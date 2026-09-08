"""The runner's orchestration: ordered, total, and fail-closed at every edge.

Covers the state machine itself, the two dry-run paths (the real environment's
and a synthetic-CLEAN one that exercises every state), and the CLI.

Nothing here invokes a model, and the synthetic audit fixture supplies
*evidence* rather than a verdict: the runner's own enforcement still decides.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import run_governance as gov
import run_v2
import runner_fixtures as fx

REPO = Path(__file__).resolve().parents[4]
RUNNER = REPO / "experiments" / "v2" / "harness" / "run_v2.py"

PURPOSE = "PT08_DIFFICULTY_DIAGNOSTIC"


def _request(tmp_path: Path, **kwargs) -> run_v2.RunRequest:
    base = dict(
        task_id="PT08",
        condition="C1",
        run_purpose=PURPOSE,
        artifact_root=tmp_path / "runs",
        generated_at="fixture",
    )
    base.update(kwargs)
    return run_v2.RunRequest(**base)


def _by_state(result: run_v2.RunResult):
    return {entry["state"]: entry for entry in result.machine.log}


# --------------------------------------------------------------------------- #
# The machine itself
# --------------------------------------------------------------------------- #
def test_the_governed_state_sequence_is_the_one_the_package_specifies():
    assert run_v2.STATES == (
        "PRECHECK",
        "PREPARE_WORKTREE",
        "CONTEXT_AUDIT",
        "BUILD_FRESH_LAUNCH",
        "MODEL_INVOCATION",
        "MODEL_IDENTITY_VALIDATION",
        "CAPTURE_WORKTREE",
        "POST_RUN_EVALUATION",
        "RECORD_ARTIFACTS",
        "COMPLETE",
    )


def test_a_state_may_only_be_entered_from_its_immediate_predecessor():
    m = run_v2.StateMachine()
    with pytest.raises(gov.RunnerRefusal) as exc:
        m.enter("CONTEXT_AUDIT")
    assert exc.value.code == run_v2.STATE_TRANSITION_REFUSED
    m.enter("PRECHECK")
    m.passed()
    with pytest.raises(gov.RunnerRefusal):
        m.enter("MODEL_INVOCATION")


def test_an_unresolved_state_never_advances():
    """The load-bearing property: a failed step cannot slip into a later state."""
    m = run_v2.StateMachine()
    m.enter("PRECHECK")  # entered, never settled
    with pytest.raises(gov.RunnerRefusal) as exc:
        m.enter("PREPARE_WORKTREE")
    assert "recorded no outcome" in exc.value.message


def test_a_refusal_is_terminal():
    m = run_v2.StateMachine()
    m.enter("PRECHECK")
    m.refuse("SOME_CODE", "because")
    assert m.refused and not m.completed
    with pytest.raises(gov.RunnerRefusal):
        m.enter("PREPARE_WORKTREE")


def test_a_skip_is_explicit_coded_and_never_a_silent_pass():
    m = run_v2.StateMachine()
    m.enter("PRECHECK")
    m.skipped("DRY_RUN_NO_INVOKE", "no process started")
    entry = m.log[-1]
    assert entry["result"] == "SKIPPED"
    assert entry["code"] == "DRY_RUN_NO_INVOKE"
    assert entry["detail"]


def test_completion_requires_every_state_to_have_been_settled():
    m = run_v2.StateMachine()
    for state in run_v2.STATES[:-1]:
        m.enter(state)
        m.passed()
    assert not m.completed
    m.enter("COMPLETE")
    m.passed()
    assert m.completed


# --------------------------------------------------------------------------- #
# The real-environment dry run
# --------------------------------------------------------------------------- #
def test_the_real_environment_dry_run_reaches_and_enforces_the_audit(tmp_path):
    """The environment is expected to be contaminated; that is a valid outcome.

    What must be true is that the pipeline *reached* the audit, enforced it, and
    refused invocation — not that the machine happens to be sterile.
    """
    result = run_v2.run(_request(tmp_path))
    states = _by_state(result)

    assert states["PRECHECK"]["result"] == "PASS"
    assert states["PREPARE_WORKTREE"]["result"] == "PASS"
    assert "CONTEXT_AUDIT" in states, "the pipeline never reached the audit"

    if states["CONTEXT_AUDIT"]["result"] == "PASS":
        # A genuinely sterile machine is also a legitimate state to be in.
        assert result.record["context_audit"]["verdict"] == "CLEAN"
    else:
        assert result.refusal_code in {
            gov.CONTEXT_AUDIT_CONTAMINATED,
            gov.CONTEXT_AUDIT_UNKNOWN,
        }
        assert "MODEL_INVOCATION" not in states, (
            "the runner advanced past a non-CLEAN audit"
        )
        assert result.record["invocation"]["invoked"] is False


def test_the_real_environment_dry_run_never_invokes_a_model(tmp_path):
    result = run_v2.run(_request(tmp_path))
    assert result.record is not None
    assert result.record["invocation"]["invoked"] is False
    assert result.record["model_identity"]["resolved_model_id"] is None
    assert result.record["outcome"]["is_result"] is False
    assert result.record["outcome"]["scored"] is False


def test_the_dry_run_records_the_refusal_rather_than_losing_it(tmp_path):
    result = run_v2.run(_request(tmp_path))
    if result.refusal_code is None:
        pytest.skip("this machine's context audit is CLEAN")
    assert result.record["outcome"]["status"] == "DRY_RUN_REFUSED"
    assert result.record["outcome"]["code"] == result.refusal_code
    assert Path(result.record_path).is_file()


# --------------------------------------------------------------------------- #
# The synthetic-CLEAN dry run — every state exercised
# --------------------------------------------------------------------------- #
def test_a_synthetic_clean_audit_exercises_the_whole_state_machine(tmp_path):
    result = run_v2.run(_request(tmp_path, audit_provider=fx.synthetic_clean_audit))
    assert result.refusal_code is None, result.refusal_detail
    assert result.machine.completed
    states = _by_state(result)
    assert [s["state"] for s in result.machine.log] == list(run_v2.STATES)
    assert states["CONTEXT_AUDIT"]["result"] == "PASS"
    # ... and the states that cannot happen without a model are SKIPPED, coded.
    for state, code in (
        ("MODEL_INVOCATION", "DRY_RUN_NO_INVOKE"),
        ("MODEL_IDENTITY_VALIDATION", "NOT_PERFORMED_DRY_RUN"),
        ("CAPTURE_WORKTREE", "DRY_RUN_NO_MODEL_EDITS"),
        ("POST_RUN_EVALUATION", "DRY_RUN_NO_SCORING"),
    ):
        assert states[state]["result"] == "SKIPPED"
        assert states[state]["code"] == code


def test_the_synthetic_clean_dry_run_still_invokes_nothing(tmp_path):
    result = run_v2.run(_request(tmp_path, audit_provider=fx.synthetic_clean_audit))
    assert result.record["invocation"]["invoked"] is False
    assert result.record["invocation"]["status"] == "DRY_RUN_NO_INVOKE"
    assert result.record["model"]["resolved_model_id"] is None
    assert result.record["model"]["selection_status"] == gov.MODEL_SELECTION_REQUIRED
    assert result.record["fresh_launch"]["executable"] is False


def test_the_synthetic_clean_dry_run_reports_every_downstream_blocker(tmp_path):
    result = run_v2.run(_request(tmp_path, audit_provider=fx.synthetic_clean_audit))
    codes = {b["code"] for b in result.record["prerequisite_blockers"]}
    assert gov.PRIMARY_MODEL_NOT_SELECTED in codes
    assert gov.hidden_acceptance_refusal_code("PT08") in codes
    assert gov.MANIFEST_NOT_FROZEN in codes
    assert gov.PRIVATE_PUBLIC_SYNC_PROPAGATION_REQUIRED_BEFORE_FREEZE in codes
    evaluation_codes = {c["code"] for c in result.record["evaluation"]["channels"]}
    assert gov.hidden_acceptance_refusal_code("PT08") in evaluation_codes
    assert gov.MANIFEST_NOT_FROZEN in evaluation_codes


def test_a_synthetic_contaminated_audit_still_refuses(tmp_path):
    result = run_v2.run(
        _request(tmp_path, audit_provider=fx.synthetic_contaminated_audit)
    )
    assert result.refusal_code == gov.CONTEXT_AUDIT_CONTAMINATED
    assert "MODEL_INVOCATION" not in _by_state(result)


@pytest.mark.parametrize(
    "provider,code",
    [
        (fx.synthetic_unknown_verdict_audit, gov.CONTEXT_AUDIT_UNKNOWN),
        (fx.exploding_audit, gov.CONTEXT_AUDIT_ERROR),
        (fx.missing_audit, gov.CONTEXT_AUDIT_MISSING),
    ],
)
def test_every_non_clean_audit_outcome_refuses(tmp_path, provider, code):
    result = run_v2.run(_request(tmp_path, audit_provider=provider))
    assert result.refusal_code == code
    assert "MODEL_INVOCATION" not in _by_state(result)


def test_the_default_audit_provider_is_the_real_unweakened_audit():
    """The fixture is a test seam, never the production path."""
    request = run_v2.RunRequest(task_id="PT08", condition="C1", run_purpose=PURPOSE)
    assert request.audit_provider is None
    source = (REPO / "experiments" / "v2" / "harness" / "run_v2.py").read_text(
        encoding="utf-8"
    )
    assert "request.audit_provider or real_context_audit" in source
    assert "require_launch=True" in source


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(RUNNER), *args],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )


def test_the_cli_readiness_command_reports_the_authorised_run():
    proc = _cli(
        "--check-readiness", "--task", "PT08", "--condition", "C1",
        "--run-purpose", PURPOSE, "--json",
    )
    assert proc.returncode == 1, "readiness must exit non-zero while blockers stand"
    report = json.loads(proc.stdout)
    assert report["run_eligible"] is False
    assert report["run_purpose"] == PURPOSE
    items = {p["item"]: p for p in report["prerequisites"]}
    for passing in (
        "public_body_identity", "c1_worktree_preparation", "diagnostic_governance",
        "public_private_linkage", "architecture_corpus_availability",
    ):
        assert items[passing]["status"] == gov.PASS, items[passing]
    for blocked in (
        "model_selection", "clean_isolated_context", "hidden_acceptance_validation",
        "manifest_freeze", "private_sync_propagation_before_freeze",
        "q1_q8_live_runtime_validation",
    ):
        assert items[blocked]["status"] == gov.BLOCKED, items[blocked]


def test_the_cli_dry_run_exits_non_zero_when_it_refuses(tmp_path):
    proc = _cli(
        "--dry-run", "--task", "PT08", "--condition", "C1",
        "--run-purpose", PURPOSE, "--artifact-root", str(tmp_path / "runs"), "--json",
    )
    payload = json.loads(proc.stdout)
    states = [e["state"] for e in payload["states"]]
    assert "PRECHECK" in states and "PREPARE_WORKTREE" in states
    assert "CONTEXT_AUDIT" in states
    if payload["refusal_code"] is None:
        assert proc.returncode == 0
    else:
        assert proc.returncode == 1
        assert "MODEL_INVOCATION" not in states
    shutil.rmtree(tmp_path / "runs", ignore_errors=True)


def test_the_cli_requires_a_mode_and_a_run_purpose():
    assert _cli("--task", "PT08", "--condition", "C1").returncode != 0
    proc = _cli("--dry-run", "--task", "PT08", "--condition", "C1")
    assert proc.returncode == 1
    assert gov.RUN_PURPOSE_MISSING in proc.stderr


def test_the_cli_offers_the_documented_surface():
    help_text = _cli("--help").stdout
    for flag in (
        "--task", "--condition", "--run-purpose", "--dry-run", "--check-readiness",
        "--model", "--effort", "--artifact-root",
    ):
        assert flag in help_text, flag
