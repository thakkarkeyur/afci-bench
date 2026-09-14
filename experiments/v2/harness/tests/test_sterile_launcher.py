"""Fail-closed tests for the sterile subscription launcher (``SL-PT08-04``).

Two properties, tested separately because they fail for different reasons.

**The launcher refuses before it spends anything.** Every refusal below happens
*before* ``subprocess.run`` could be reached, which is the only defensible
failure point for a paid run: a launcher that discovered a contaminated profile
after the model had already answered would have bought a worthless observation.
The tests therefore assert the refusal AND that no process was started.

**The audit tells authentication apart from context.** ``SL-PT08-04`` permits
exactly one file — the credential — in a sterile profile, and permits account
metadata the runtime re-creates for itself, and nothing else. The five
differential cases at the end pin that line: credential alone is CLEAN, and the
credential plus any instruction-bearing artefact is CONTAMINATED. A filename
exemption would pass all five; only reading the material passes the right one.

No model is invoked here. Every process is a fake, and the one real subprocess
path is monkeypatched.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HARNESS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HARNESS))

import context_audit as ca  # noqa: E402
import model_adapter as ma  # noqa: E402
import run_governance as gov  # noqa: E402


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
def _sterile(tmp_path: Path, *, credential: bool = True) -> ca.SterileEnv:
    """A sterile profile built the way the runner builds one."""
    source = None
    if credential:
        source = tmp_path / ".credentials.json"
        source.write_text('{"token": "sk-ant-FAKE-NOT-A-REAL-TOKEN-000"}', encoding="utf-8")
    return ca.make_sterile_env(
        "t", base_dir=tmp_path / "rt", credential_source=source, launchable=True
    )


def _worktree(tmp_path: Path) -> Path:
    wt = tmp_path / "run" / "worktree"
    wt.mkdir(parents=True)
    (wt / "package.json").write_text("{}", encoding="utf-8")
    return wt


def _plan(tmp_path: Path, sterile: ca.SterileEnv, **kw) -> ma.LaunchPlan:
    prompt = tmp_path / "task_prompt.md"
    prompt.write_text("do the task", encoding="utf-8")
    params = dict(
        prompt_path=str(prompt),
        workspace=str(_worktree(tmp_path)),
        model_id="claude-sonnet-5",
        sterile_env=sterile.env,
        sterile=True,
        permission_mode=ma.DIAGNOSTIC_PERMISSION_MODE,
        tools=ma.DIAGNOSTIC_TOOLS,
    )
    params.update(kw)
    return ma.build_fresh_launch(**params)


def _launcher(tmp_path: Path, sterile: ca.SterileEnv, **kw) -> ma.RealClaudeCodeLauncher:
    params = dict(
        executable="claude-does-not-run-in-these-tests",
        cwd=tmp_path / "run" / "worktree",
        env=dict(sterile.env),
        evidence_path=tmp_path / "out" / "runtime_evidence.jsonl",
        governed_root=tmp_path / "run",
        canonical_repo=tmp_path / "canonical",
        config_dir=sterile.config_dir,
    )
    params.update(kw)
    return ma.RealClaudeCodeLauncher(**params)


@pytest.fixture
def no_process(monkeypatch):
    """Prove no process is started: any attempt is a hard test failure."""
    def _boom(*a, **k):  # pragma: no cover - reaching this IS the failure
        raise AssertionError("a process was started despite a fail-closed refusal")

    monkeypatch.setattr(ma.subprocess, "run", _boom)
    return _boom


# --------------------------------------------------------------------------- #
# 1-5 — the model and session contract
# --------------------------------------------------------------------------- #
def test_1_no_model_supplied_is_refused(tmp_path, no_process):
    sterile = _sterile(tmp_path)
    with pytest.raises(gov.RunnerRefusal) as exc:
        _plan(tmp_path, sterile, model_id=None, require_model=True)
    assert exc.value.code == gov.MODEL_SELECTION_REQUIRED


def test_1b_a_plan_without_a_model_cannot_be_launched(tmp_path, no_process):
    sterile = _sterile(tmp_path)
    plan = _plan(tmp_path, sterile, model_id=None, require_model=False)
    with pytest.raises(gov.RunnerRefusal) as exc:
        _launcher(tmp_path, sterile)(plan)
    assert exc.value.code == gov.MODEL_SELECTION_REQUIRED


def test_2_fallback_model_is_refused(tmp_path, no_process):
    sterile = _sterile(tmp_path)
    with pytest.raises(gov.RunnerRefusal) as exc:
        _plan(tmp_path, sterile, extra=("--fallback-model", "claude-opus-4-8"))
    assert exc.value.code == gov.FALLBACK_MODEL_REJECTED


@pytest.mark.parametrize(
    "flag,code",
    [
        ("--resume", gov.SESSION_RESUME_REJECTED),
        ("-r", gov.SESSION_RESUME_REJECTED),
        ("--continue", gov.SESSION_CONTINUE_REJECTED),
        ("-c", gov.SESSION_CONTINUE_REJECTED),
        ("--from-pr", gov.SESSION_RESUME_REJECTED),
    ],
)
def test_3_and_4_session_restoration_is_refused(tmp_path, no_process, flag, code):
    sterile = _sterile(tmp_path)
    with pytest.raises(gov.RunnerRefusal) as exc:
        _plan(tmp_path, sterile, extra=(flag,))
    assert exc.value.code == code


def test_5_reused_session_id_is_refused(tmp_path, no_process):
    sterile = _sterile(tmp_path)
    with pytest.raises(gov.RunnerRefusal) as exc:
        _plan(
            tmp_path, sterile,
            session_id="11111111-1111-1111-1111-111111111111",
            previous_session_ids=("11111111-1111-1111-1111-111111111111",),
        )
    assert exc.value.code == gov.SESSION_ID_REUSED


def test_5b_a_fresh_session_id_is_permitted(tmp_path):
    sterile = _sterile(tmp_path)
    plan = _plan(tmp_path, sterile, session_id="22222222-2222-2222-2222-222222222222")
    assert "--session-id" in plan.argv
    assert ca.check_session_flags(plan.argv, ("11111111-1111-1111-1111-111111111111",)) == []


# --------------------------------------------------------------------------- #
# 6-7 — where the model is allowed to write
# --------------------------------------------------------------------------- #
def test_6_canonical_repository_as_cwd_is_refused(tmp_path, no_process):
    sterile = _sterile(tmp_path)
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    plan = _plan(tmp_path, sterile)
    with pytest.raises(gov.RunnerRefusal) as exc:
        _launcher(tmp_path, sterile, cwd=canonical, governed_root=None)(plan)
    assert exc.value.code == gov.CANONICAL_REPOSITORY_EXECUTION_REFUSED


def test_6b_a_directory_inside_the_canonical_repository_is_refused(tmp_path, no_process):
    sterile = _sterile(tmp_path)
    inside = tmp_path / "canonical" / "apps" / "api"
    inside.mkdir(parents=True)
    plan = _plan(tmp_path, sterile)
    with pytest.raises(gov.RunnerRefusal) as exc:
        _launcher(tmp_path, sterile, cwd=inside, governed_root=None)(plan)
    assert exc.value.code == gov.CANONICAL_REPOSITORY_EXECUTION_REFUSED


def test_7_worktree_outside_the_governed_root_is_refused(tmp_path, no_process):
    sterile = _sterile(tmp_path)
    stray = tmp_path / "elsewhere"
    stray.mkdir()
    plan = _plan(tmp_path, sterile)
    with pytest.raises(gov.RunnerRefusal) as exc:
        _launcher(tmp_path, sterile, cwd=stray)(plan)
    assert exc.value.code == gov.CANONICAL_REPOSITORY_EXECUTION_REFUSED


def test_7b_a_missing_worktree_is_refused(tmp_path, no_process):
    sterile = _sterile(tmp_path)
    plan = _plan(tmp_path, sterile)
    with pytest.raises(gov.RunnerRefusal) as exc:
        _launcher(tmp_path, sterile, cwd=tmp_path / "run" / "absent")(plan)
    assert exc.value.code == gov.MODEL_WORKTREE_NOT_LAUNCHABLE


# --------------------------------------------------------------------------- #
# 8-11 — the environment and the profile
# --------------------------------------------------------------------------- #
def test_8_non_sterile_home_is_refused(tmp_path, no_process):
    sterile = _sterile(tmp_path)
    env = dict(sterile.env)
    env["HOME"] = str(Path("~").expanduser())
    env["USERPROFILE"] = str(Path("~").expanduser())
    plan = _plan(tmp_path, sterile)
    with pytest.raises(gov.RunnerRefusal) as exc:
        _launcher(tmp_path, sterile, env=env)(plan)
    assert exc.value.code == gov.ISOLATED_ENVIRONMENT_NOT_VERIFIED


def test_8b_an_env_with_no_isolation_variables_is_refused(tmp_path, no_process):
    sterile = _sterile(tmp_path)
    plan = _plan(tmp_path, sterile)
    with pytest.raises(gov.RunnerRefusal) as exc:
        _launcher(tmp_path, sterile, env={"PATH": "x"})(plan)
    assert exc.value.code == gov.ISOLATED_ENVIRONMENT_NOT_VERIFIED


def test_8c_an_inherited_session_variable_is_refused(tmp_path, no_process):
    """The calling session exports CLAUDE_CODE_SESSION_ID and friends."""
    sterile = _sterile(tmp_path)
    env = dict(sterile.env)
    env["CLAUDE_CODE_SESSION_ID"] = "inherited-from-the-developer-session"
    plan = _plan(tmp_path, sterile)
    with pytest.raises(gov.RunnerRefusal) as exc:
        _launcher(tmp_path, sterile, env=env)(plan)
    assert exc.value.code == gov.ISOLATED_ENVIRONMENT_NOT_VERIFIED
    assert "CLAUDE_CODE_SESSION_ID" in exc.value.message


@pytest.mark.parametrize(
    "relative,is_dir",
    [
        ("skills/reviewer/SKILL.md", False),
        ("plugins/p/plugin.json", False),
        ("commands/deploy.md", False),
        ("agents/helper.md", False),
        ("settings.json", False),
        ("CLAUDE.md", False),
        ("sessions/prior-session.jsonl", False),
    ],
)
def test_9_10_11_any_context_artifact_in_the_profile_is_refused(
    tmp_path, no_process, relative, is_dir
):
    sterile = _sterile(tmp_path)
    target = sterile.config_dir / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('{"hooks": {"PreToolUse": []}}', encoding="utf-8")
    plan = _plan(tmp_path, sterile)
    with pytest.raises(gov.RunnerRefusal) as exc:
        _launcher(tmp_path, sterile)(plan)
    assert exc.value.code == gov.CONTEXT_AUDIT_CONTAMINATED


def test_11b_a_missing_credential_is_refused(tmp_path, no_process):
    sterile = _sterile(tmp_path, credential=False)
    plan = _plan(tmp_path, sterile)
    with pytest.raises(gov.RunnerRefusal) as exc:
        _launcher(tmp_path, sterile)(plan)
    assert exc.value.code == gov.CONTEXT_AUDIT_CONTAMINATED


def test_11c_only_a_credential_may_be_provisioned(tmp_path):
    """No API for copying anything else into a sterile profile exists."""
    other = tmp_path / "settings.json"
    other.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError):
        ca.make_sterile_env("t", base_dir=tmp_path / "rt2", credential_source=other)


# --------------------------------------------------------------------------- #
# 12-14 — what counts as an invalid observation
# --------------------------------------------------------------------------- #
class _FakeProc:
    def __init__(self, stdout="", stderr="", returncode=0):
        self.stdout, self.stderr, self.returncode = stdout, stderr, returncode


def _run_with(monkeypatch, tmp_path, stdout="", stderr="", returncode=0):
    sterile = _sterile(tmp_path)
    plan = _plan(tmp_path, sterile)
    monkeypatch.setattr(
        ma.subprocess, "run",
        lambda *a, **k: _FakeProc(stdout, stderr, returncode),
    )
    return _launcher(tmp_path, sterile)(plan)


def test_12_missing_structured_readback_is_invalid(monkeypatch, tmp_path):
    outcome = _run_with(monkeypatch, tmp_path, stdout="not json at all\n")
    assert outcome.invoked is True
    with pytest.raises(gov.RunnerRefusal) as exc:
        ma.validate_model_identity("claude-sonnet-5", outcome.runtime_evidence)
    assert exc.value.code == gov.MODEL_READBACK_MISSING


def test_13_model_mismatch_is_invalid(monkeypatch, tmp_path):
    event = {"type": "system", "subtype": "init", "model": "claude-opus-4-8"}
    outcome = _run_with(monkeypatch, tmp_path, stdout=json.dumps(event))
    with pytest.raises(gov.RunnerRefusal) as exc:
        ma.validate_model_identity("claude-sonnet-5", outcome.runtime_evidence)
    assert exc.value.code == gov.MODEL_READBACK_MISMATCH


def test_13b_two_distinct_resolved_ids_are_ambiguous_not_a_pass(monkeypatch, tmp_path):
    """The auxiliary-model case the determinism control exists to prevent."""
    stdout = "\n".join([
        json.dumps({"type": "system", "subtype": "init", "model": "claude-sonnet-5"}),
        json.dumps({"type": "result", "modelUsage": {
            "claude-sonnet-5": {}, "claude-haiku-4-5-20251001": {}}}),
    ])
    outcome = _run_with(monkeypatch, tmp_path, stdout=stdout)
    with pytest.raises(gov.RunnerRefusal) as exc:
        ma.validate_model_identity("claude-sonnet-5", outcome.runtime_evidence)
    assert exc.value.code == gov.MODEL_READBACK_AMBIGUOUS


def test_13c_a_single_resolved_id_validates(monkeypatch, tmp_path):
    stdout = "\n".join([
        json.dumps({"type": "system", "subtype": "init", "model": "claude-sonnet-5"}),
        json.dumps({"type": "result", "modelUsage": {"claude-sonnet-5": {}}}),
    ])
    outcome = _run_with(monkeypatch, tmp_path, stdout=stdout)
    result = ma.validate_model_identity("claude-sonnet-5", outcome.runtime_evidence)
    assert result.valid and result.resolved == "claude-sonnet-5"


def test_14_process_failure_is_reported_as_failure(monkeypatch, tmp_path):
    outcome = _run_with(monkeypatch, tmp_path, stderr="boom", returncode=2)
    assert outcome.status == "PROCESS_FAILED"
    assert outcome.exit_status == 2


def test_14b_a_timeout_is_invalid_rather_than_partial(monkeypatch, tmp_path):
    sterile = _sterile(tmp_path)
    plan = _plan(tmp_path, sterile)

    def _timeout(*a, **k):
        raise ma.subprocess.TimeoutExpired(cmd="claude", timeout=1)

    monkeypatch.setattr(ma.subprocess, "run", _timeout)
    with pytest.raises(gov.RunnerRefusal) as exc:
        _launcher(tmp_path, sterile)(plan)
    assert exc.value.code == gov.MODEL_PROCESS_FAILED


def test_14c_the_launch_is_never_run_through_a_shell(monkeypatch, tmp_path):
    seen = {}

    def _capture(argv, **kwargs):
        seen["argv"], seen["kwargs"] = argv, kwargs
        return _FakeProc(stdout="{}")

    sterile = _sterile(tmp_path)
    plan = _plan(tmp_path, sterile)
    monkeypatch.setattr(ma.subprocess, "run", _capture)
    _launcher(tmp_path, sterile)(plan)
    assert isinstance(seen["argv"], list), "argv must be a list, never a string"
    assert seen["kwargs"].get("shell") is False
    assert seen["kwargs"]["cwd"] == str((tmp_path / "run" / "worktree").resolve())


# --------------------------------------------------------------------------- #
# 15 — redaction
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "secret",
    [
        "sk-ant-oat01-ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "Bearer abcdefghijklmnop.qrstuv",
        '"accessToken": "super-secret-value"',
        '"refreshToken": "another-secret-value"',
        "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dBjftJeZ4CVPmB92K27uhbUJU1p1r",
    ],
)
def test_15_secrets_are_redacted_before_anything_is_written(monkeypatch, tmp_path, secret):
    outcome = _run_with(
        monkeypatch, tmp_path,
        stdout=json.dumps({"type": "system", "subtype": "init", "note": secret}),
        stderr=f"auth failed: {secret}",
    )
    written = Path(outcome.runtime_evidence_path).read_text(encoding="utf-8")
    stderr_file = Path(outcome.runtime_evidence_path).with_suffix(".stderr.txt")
    assert secret not in written
    assert secret not in stderr_file.read_text(encoding="utf-8")
    assert "[REDACTED]" in written or "[REDACTED]" in stderr_file.read_text(encoding="utf-8")


def test_15b_the_credential_contents_never_reach_an_artifact(monkeypatch, tmp_path):
    outcome = _run_with(
        monkeypatch, tmp_path,
        stdout=json.dumps({"type": "system", "subtype": "init", "model": "claude-sonnet-5"}),
    )
    blob = Path(outcome.runtime_evidence_path).read_text(encoding="utf-8")
    assert "sk-ant-FAKE-NOT-A-REAL-TOKEN-000" not in blob


# --------------------------------------------------------------------------- #
# SL-PT08-04 — authentication material vs experiment-relevant context
# --------------------------------------------------------------------------- #
def _audit_profile(tmp_path, sterile, workspace):
    roots = ca.ScanRoots.discover(
        workspace=workspace,
        home=sterile.temp_home,
        config_dir=sterile.config_dir,
        managed_settings=[],
        include_ancestors=False,
    )
    return ca.audit(
        condition=ca.CONDITIONS["C1"],
        roots=roots,
        env=sterile.env,
        launch=ca.LaunchCommand(argv=("claude", "-p", "--no-session-persistence")),
        require_launch=True,
        run_id="sl-pt08-04",
        account_policy_adjudication=True,
        credential_path=sterile.credential_path,
        verify_profile=True,
    )


def test_credential_only_sterile_config_is_clean(tmp_path):
    """The case the whole clarification exists to make possible."""
    sterile = _sterile(tmp_path)
    result = _audit_profile(tmp_path, sterile, _worktree(tmp_path))
    assert result.verdict == "CLEAN", result.reasons
    assert result.authentication["credential_provisioned"] is True
    assert result.authentication["api_key_required"] is False
    assert result.authentication["credential_contents_read"] is False


def test_credential_plus_runtime_recreated_account_metadata_is_clean(tmp_path):
    """What the runtime writes for itself after authenticating must not fail."""
    sterile = _sterile(tmp_path)
    (sterile.config_dir / "remote-settings.json").write_text("{}", encoding="utf-8")
    (sterile.config_dir / "policy-limits.json").write_text(
        json.dumps({
            "restrictions": {"allow_remote_control": {"allowed": False}},
            "compliance_taints": [],
            "monitoring_notice": None,
            "defaults": {"remote_control_at_startup": False},
        }),
        encoding="utf-8",
    )
    (sterile.config_dir / ".claude.json").write_text(
        json.dumps({"firstStartTime": "x", "machineID": "y", "userID": "z"}),
        encoding="utf-8",
    )
    result = _audit_profile(tmp_path, sterile, _worktree(tmp_path))
    assert result.verdict == "CLEAN", result.reasons
    assert result.account_policy, "the metadata must be RECORDED, not ignored"
    assert not any(
        f["injects_experiment_relevant_context"] for f in result.account_policy
    )


@pytest.mark.parametrize(
    "relative,payload",
    [
        ("skills/reviewer/SKILL.md", "---\nname: reviewer\n---\nprefer adapters"),
        ("settings.json", json.dumps({"hooks": {"PreToolUse": [{"command": "x"}]}})),
        ("plugins/p/plugin.json", json.dumps({"name": "p"})),
        ("commands/go.md", "run the thing"),
        ("agents/a.md", "you are an agent"),
    ],
)
def test_credential_plus_any_context_artifact_is_contaminated(tmp_path, relative, payload):
    sterile = _sterile(tmp_path)
    target = sterile.config_dir / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(payload, encoding="utf-8")
    result = _audit_profile(tmp_path, sterile, _worktree(tmp_path))
    assert result.verdict == "CONTAMINATED"


def test_credential_plus_a_prior_session_is_contaminated(tmp_path):
    sterile = _sterile(tmp_path)
    sessions = sterile.config_dir / "sessions"
    sessions.mkdir(parents=True)
    (sessions / "prior.jsonl").write_text('{"role":"user"}', encoding="utf-8")
    result = _audit_profile(tmp_path, sterile, _worktree(tmp_path))
    assert result.verdict == "CONTAMINATED"
    assert any("sessions/" in r or "prior-session" in r for r in result.reasons)


def test_an_account_policy_that_carries_text_is_contaminated(tmp_path):
    """Presence is permitted; injected text is not."""
    sterile = _sterile(tmp_path)
    (sterile.config_dir / "policy-limits.json").write_text(
        json.dumps({"monitoring_notice": "Always prefer a layered architecture."}),
        encoding="utf-8",
    )
    result = _audit_profile(tmp_path, sterile, _worktree(tmp_path))
    assert result.verdict == "CONTAMINATED"
    assert any(f["injects_experiment_relevant_context"] for f in result.account_policy)


def test_an_account_file_configuring_mcp_is_contaminated(tmp_path):
    sterile = _sterile(tmp_path)
    (sterile.config_dir / ".claude.json").write_text(
        json.dumps({"mcpServers": {"x": {"url": "https://example.invalid"}}}),
        encoding="utf-8",
    )
    result = _audit_profile(tmp_path, sterile, _worktree(tmp_path))
    assert result.verdict == "CONTAMINATED"


def test_adjudication_is_off_by_default_so_the_strict_reading_is_unchanged(tmp_path):
    """A caller without the clarification still sees account metadata as context."""
    sterile = _sterile(tmp_path)
    (sterile.config_dir / "policy-limits.json").write_text(
        json.dumps({"restrictions": {}, "defaults": {}}), encoding="utf-8"
    )
    roots = ca.ScanRoots.discover(
        workspace=_worktree(tmp_path), home=sterile.temp_home,
        config_dir=sterile.config_dir, managed_settings=[], include_ancestors=False,
    )
    strict = ca.audit(
        condition=ca.CONDITIONS["C1"], roots=roots, env=sterile.env, run_id="strict"
    )
    assert strict.verdict == "CONTAMINATED"


def test_enterprise_managed_settings_are_never_adjudicated(tmp_path):
    """TD-B19's managed-policy prohibition is untouched by the clarification."""
    sterile = _sterile(tmp_path)
    policy = tmp_path / "ProgramData" / "ClaudeCode" / "managed-settings.json"
    policy.parent.mkdir(parents=True)
    policy.write_text(json.dumps({"restrictions": {}}), encoding="utf-8")
    roots = ca.ScanRoots.discover(
        workspace=_worktree(tmp_path), home=sterile.temp_home,
        config_dir=sterile.config_dir, managed_settings=[policy],
        include_ancestors=False,
    )
    result = ca.audit(
        condition=ca.CONDITIONS["C1"], roots=roots, env=sterile.env,
        launch=ca.LaunchCommand(argv=("claude", "-p")), require_launch=True,
        run_id="managed", account_policy_adjudication=True,
        credential_path=sterile.credential_path, verify_profile=True,
    )
    assert result.verdict == "CONTAMINATED"
    assert any("managed" in r for r in result.reasons)


# --------------------------------------------------------------------------- #
# The runtime's own report of what it loaded
# --------------------------------------------------------------------------- #
def test_an_absent_init_event_is_not_demonstrated_rather_than_clean(tmp_path):
    evidence = ca.audit_runtime_context(None)
    assert evidence.clean is False
    assert evidence.to_dict()["verdict"] == "NOT_DEMONSTRATED"


def test_an_empty_runtime_context_is_clean():
    evidence = ca.audit_runtime_context({
        "skills": [], "slash_commands": [], "plugins": [], "mcp_servers": [],
        "output_style": "default", "apiKeySource": "none",
        "claude_code_version": "2.1.229",
    })
    assert evidence.clean is True
    assert evidence.api_key_source == "none"


@pytest.mark.parametrize("field", list(ca.RUNTIME_CONTEXT_FIELDS))
def test_any_loaded_context_field_fails_the_runtime_audit(field):
    init = {f: [] for f in ca.RUNTIME_CONTEXT_FIELDS}
    init[field] = ["something"]
    evidence = ca.audit_runtime_context(init)
    assert evidence.clean is False
    assert any(field in v for v in evidence.violations)


def test_a_non_default_output_style_fails_the_runtime_audit():
    init = {f: [] for f in ca.RUNTIME_CONTEXT_FIELDS}
    init["output_style"] = "terse-reviewer"
    assert ca.audit_runtime_context(init).clean is False


# --------------------------------------------------------------------------- #
# Q8 — an echoed request is not a substitution, and modelUsage settles it
# --------------------------------------------------------------------------- #
BOGUS = "claude-nonexistent-model-9x7q-not-a-real-id"


def _q8_observed():
    """The shape Claude Code 2.1.229 actually produces for an unknown id.

    system.init echoes the REQUESTED id because the CLI does not validate ids
    locally; the assistant turn is a synthetic CLI error rather than a model
    answer; modelUsage is empty because nothing served the request.
    """
    return [
        {"type": "system", "subtype": "init", "model": BOGUS,
         "claude_code_version": "2.1.229"},
        {"type": "assistant", "message": {"model": "<synthetic>", "content": [
            {"type": "text", "text": "There's an issue with the selected model"}]}},
        {"type": "result", "subtype": "success", "is_error": True, "modelUsage": {}},
    ]


def test_q8_an_echoed_request_with_no_model_usage_is_a_rejection():
    probe = ma.validate_invalid_model_id_rejection(
        BOGUS, exit_status=1, evidence=_q8_observed()
    )
    assert probe.status == "Q8_REJECTED"
    assert ma.model_usage_ids(_q8_observed()) == [], (
        "modelUsage is the evidence that no model served the request"
    )


def test_q8_a_different_model_answering_is_still_a_substitution():
    evidence = _q8_observed()
    evidence[2]["modelUsage"] = {"claude-sonnet-5": {}}
    probe = ma.validate_invalid_model_id_rejection(
        BOGUS, exit_status=1, evidence=evidence
    )
    assert probe.status == "Q8_SILENTLY_DEGRADED"
    assert probe.resolved_model_id == "claude-sonnet-5"


def test_q8_a_model_serving_the_invalid_id_is_a_substitution():
    """If tokens were served under the made-up id, it was answered, not rejected."""
    evidence = _q8_observed()
    evidence[2]["modelUsage"] = {BOGUS: {}}
    probe = ma.validate_invalid_model_id_rejection(
        BOGUS, exit_status=1, evidence=evidence
    )
    assert probe.status == "Q8_SILENTLY_DEGRADED"


def test_q8_a_zero_exit_is_never_a_rejection():
    probe = ma.validate_invalid_model_id_rejection(
        BOGUS, exit_status=0, evidence=_q8_observed()
    )
    assert probe.status == "Q8_NOT_REJECTED"


def test_model_usage_ids_ignores_the_system_init_echo():
    assert ma.model_usage_ids(
        [{"type": "system", "subtype": "init", "model": "claude-sonnet-5"}]
    ) == []


# --------------------------------------------------------------------------- #
# The launch command itself
# --------------------------------------------------------------------------- #
def test_the_sterile_launch_carries_every_verified_isolation_flag(tmp_path):
    plan = _plan(tmp_path, _sterile(tmp_path))
    for flag in ("--safe-mode", "--setting-sources", "--strict-mcp-config",
                 "--disable-slash-commands"):
        assert flag in plan.argv, flag
    assert plan.argv[:3] == ("claude", "-p", "--no-session-persistence")
    assert "--bare" not in plan.argv, (
        "--bare would force ANTHROPIC_API_KEY and never read OAuth, which makes "
        "subscription authentication impossible"
    )


def test_the_permission_mode_and_tool_set_are_pinned(tmp_path):
    plan = _plan(tmp_path, _sterile(tmp_path))
    i = plan.argv.index("--permission-mode")
    assert plan.argv[i + 1] == ma.DIAGNOSTIC_PERMISSION_MODE == "acceptEdits"
    tools = plan.argv[plan.argv.index("--tools") + 1].split(",")
    assert tools == list(ma.DIAGNOSTIC_TOOLS)
    for excluded in ("Task", "WebSearch", "WebFetch"):
        assert excluded not in tools, f"{excluded} must not be available to a repetition"


def test_the_determinism_control_that_keeps_the_readback_single_valued(tmp_path):
    sterile = _sterile(tmp_path)
    assert sterile.env["DISABLE_NON_ESSENTIAL_MODEL_CALLS"] == "1"
    plan = _plan(tmp_path, sterile)
    assert plan.environment()["DISABLE_NON_ESSENTIAL_MODEL_CALLS"] == "1"


def test_the_sterile_environment_is_built_by_allowlist(tmp_path):
    sterile = _sterile(tmp_path)
    assert ca.inherited_env_violations(sterile.env) == []
    assert "ANTHROPIC_API_KEY" not in sterile.env
    built = ca.build_allowlisted_env({"PATH": "p", "CLAUDE_CODE_SESSION_ID": "s", "FOO": "f"})
    assert built == {"PATH": "p"}


# --------------------------------------------------------------------------- #
# The prompt must survive delivery, whatever the host locale is
# --------------------------------------------------------------------------- #
def test_the_launcher_delivers_a_non_ascii_prompt_verbatim(tmp_path, monkeypatch):
    """Regression: the task body is delivered as UTF-8, not as the host locale.

    ``subprocess.run(..., text=True)`` with no explicit encoding uses the process
    locale. On a Windows host that is cp1252, so a task body containing an arrow,
    an en dash or a curly quote raised UnicodeEncodeError while WRITING THE
    PROMPT: the model received an empty stdin, emitted no ``system.init``, and the
    repetition was invalid for a reason that had nothing to do with the model.

    The public task bodies genuinely contain such characters, so this is not a
    hypothetical. The check is on the bytes the child actually receives.
    """
    import json
    import subprocess
    import sys

    prompt = tmp_path / "task_prompt.md"
    # Every character here appears in at least one approved public task body.
    body = "Return the accepted items → report the rest — “exactly”.\n"
    prompt.write_text(body, encoding="utf-8")

    echo = tmp_path / "echo_stdin.py"
    echo.write_text(
        "import sys\n"
        "data = sys.stdin.buffer.read()\n"
        "sys.stdout.buffer.write(data)\n",
        encoding="utf-8",
    )

    # Drive the same call shape the launcher uses, with the same pinned encoding.
    proc = subprocess.run(
        [sys.executable, str(echo)],
        input=prompt.read_text(encoding="utf-8"),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == body, (
        "the prompt did not survive delivery; the child received "
        f"{proc.stdout!r} instead of {body!r}"
    )

    # And the launcher itself must PIN the encoding on the call that delivers the
    # prompt, rather than inheriting whatever the host locale happens to be.
    source = (HARNESS / "model_adapter.py").read_text(encoding="utf-8")
    call = source.split("input=stdin_text,", 1)
    assert len(call) == 2, "the launcher no longer delivers the prompt over stdin"
    # Everything up to the close of that subprocess.run call.
    tail = call[1].split("shell=False", 1)[0]
    assert 'encoding="utf-8"' in tail, (
        "the prompt-delivering subprocess.run does not pin encoding='utf-8'; it "
        "would encode the task body with the host locale"
    )
