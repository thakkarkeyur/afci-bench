"""Tests for the AFCI-Bench v2 context-isolation harness (context_audit.py).

These prove detection of every contamination source, the per-condition
allowlist semantics (C1/C3/C4), sterile-environment uniqueness, the
session-restoration guard, schema conformance, and that no secret values are
ever recorded.
"""
import json
from pathlib import Path

import pytest

import context_audit as ca

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "context_audit.schema.json"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def sterile_roots(tmp_path: Path, workspace: Path, ancestors=None):
    """Build a sterile env + scan roots isolated from the real machine
    (no real ancestors, no managed policy)."""
    sterile = ca.make_sterile_env("run-test", base_dir=tmp_path / "sterile")
    roots = ca.ScanRoots(
        workspace=Path(workspace).resolve(),
        home=sterile.temp_home,
        config_dir=sterile.config_dir,
        ancestors=list(ancestors or []),
        managed_settings=[],
    )
    return sterile, roots


def kinds_at(sources, scope=None):
    return {(s.kind, s.scope) for s in sources if scope is None or s.scope == scope}


# --------------------------------------------------------------------------- #
# 1-4: detection of contamination sources
# --------------------------------------------------------------------------- #
def test_user_claude_md_detected(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    sterile, roots = sterile_roots(tmp_path, ws)
    write(roots.home / ".claude" / "CLAUDE.md", "# user-level instructions")
    sources = ca.scan_context_sources(roots)
    assert any(s.kind == "claude_md" and s.scope == "user" for s in sources)


def test_ancestor_claude_md_detected(tmp_path):
    ancestor = tmp_path / "parent"
    ws = ancestor / "repo"
    ws.mkdir(parents=True)
    write(ancestor / "CLAUDE.md", "# ancestor instructions")
    sterile, roots = sterile_roots(tmp_path, ws, ancestors=[ancestor])
    sources = ca.scan_context_sources(roots)
    assert any(s.kind == "claude_md" and s.scope == "ancestor" for s in sources)


def test_claude_local_md_detected(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    write(ws / "CLAUDE.local.md", "# local overrides")
    sterile, roots = sterile_roots(tmp_path, ws)
    sources = ca.scan_context_sources(roots)
    assert any(s.kind == "claude_local_md" and s.scope == "workspace" for s in sources)


def test_memory_files_detected(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    sterile, roots = sterile_roots(tmp_path, ws)
    write(roots.config_dir / "projects" / "proj-x" / "memory" / "fact.md", "remembered fact")
    sources = ca.scan_context_sources(roots)
    mem = [s for s in sources if s.kind == "memory"]
    assert mem and mem[0].sha256 is not None


def test_rules_and_components_detected(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    sterile, roots = sterile_roots(tmp_path, ws)
    write(ws / ".claude" / "rules" / "arch.md", "rule")
    write(ws / ".claude" / "skills" / "s" / "SKILL.md", "skill")
    write(ws / ".claude" / "agents" / "a.md", "agent")
    write(ws / ".claude" / "commands" / "c.md", "command")
    sources = ca.scan_context_sources(roots)
    present = {s.kind for s in sources}
    assert {"rules", "skills", "agents", "commands"} <= present


# --------------------------------------------------------------------------- #
# 5-7: condition allowlist semantics
# --------------------------------------------------------------------------- #
def test_c1_rejects_project_instructions(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    instr = write(ws / "CLAUDE.md", "# project architecture context")
    sterile, roots = sterile_roots(tmp_path, ws)
    result = ca.audit(
        condition=ca.CONDITIONS["C1"],
        roots=roots,
        env=sterile.env,
        run_id="r1",
    )
    assert result.verdict == "CONTAMINATED"
    assert any(str(instr) in r for r in result.reasons)


def test_c3_permits_only_approved_instruction(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    content = "# C3 approved repository instruction\n"
    instr = write(ws / "CLAUDE.md", content)
    approved = [ca.ApprovedArtifact("claude_md", str(instr), ca.sha256_file(instr))]
    cond = ca.CONDITIONS["C3"].with_approved(approved)
    sterile, roots = sterile_roots(tmp_path, ws)

    # (a) only the approved instruction present -> CLEAN
    ok = ca.audit(condition=cond, roots=roots, env=sterile.env, run_id="r3a")
    assert ok.verdict == "CLEAN", ok.reasons
    assert any(s.approved for s in ok.detected if s.kind == "claude_md")

    # (b) an extra, unapproved instruction present -> CONTAMINATED
    write(ws / "CLAUDE.local.md", "extra")
    bad = ca.audit(condition=cond, roots=roots, env=sterile.env, run_id="r3b")
    assert bad.verdict == "CONTAMINATED"

    # (c) approved file tampered (hash mismatch) -> CONTAMINATED
    (ws / "CLAUDE.local.md").unlink()
    instr.write_text(content + "TAMPERED", encoding="utf-8")
    tampered = ca.audit(condition=cond, roots=roots, env=sterile.env, run_id="r3c")
    assert tampered.verdict == "CONTAMINATED"
    assert any("hash mismatch" in r for r in tampered.reasons)


def test_c4_rejects_persistent_mad(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    # A persistent repository instruction / MAD file is forbidden under C4.
    write(ws / "CLAUDE.md", "# Minimum Architecture Document (persisted)")
    sterile, roots = sterile_roots(tmp_path, ws)
    result = ca.audit(condition=ca.CONDITIONS["C4"], roots=roots, env=sterile.env, run_id="r4")
    assert result.verdict == "CONTAMINATED"


def test_c1_clean_when_sterile(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    sterile, roots = sterile_roots(tmp_path, ws)
    result = ca.audit(condition=ca.CONDITIONS["C1"], roots=roots, env=sterile.env, run_id="r0")
    assert result.verdict == "CLEAN", result.reasons


# --------------------------------------------------------------------------- #
# 8: sterile environment uniqueness + required env
# --------------------------------------------------------------------------- #
def test_two_runs_use_different_dirs(tmp_path):
    a = ca.make_sterile_env("run-a", base_dir=tmp_path)
    b = ca.make_sterile_env("run-b", base_dir=tmp_path)
    assert a.temp_home != b.temp_home
    assert a.config_dir != b.config_dir
    assert a.config_dir != a.temp_home
    for env in (a.env, b.env):
        assert env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] == "1"
        assert env["DISABLE_AUTOUPDATER"] == "1"
        assert env["CLAUDE_CONFIG_DIR"]
        assert env["HOME"]


def test_missing_isolation_env_fails_closed(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    sterile, roots = sterile_roots(tmp_path, ws)
    broken = dict(sterile.env)
    broken.pop("CLAUDE_CODE_DISABLE_AUTO_MEMORY")
    result = ca.audit(condition=ca.CONDITIONS["C1"], roots=roots, env=broken, run_id="rbad")
    assert result.verdict == "CONTAMINATED"
    assert any("AUTO_MEMORY" in r for r in result.reasons)


# --------------------------------------------------------------------------- #
# 9: session-restoration guard
# --------------------------------------------------------------------------- #
def test_previous_session_ids_rejected():
    prev = {"prev-123"}
    assert ca.check_session_flags(["--session-id", "prev-123"], prev)
    assert ca.check_session_flags(["--session-id=prev-123"], prev)
    assert ca.check_session_flags(["--resume", "x"])
    assert ca.check_session_flags(["-c"])
    assert ca.check_session_flags(["--continue"])
    assert ca.check_session_flags(["--from-pr", "42"])
    # a fresh, unseen session id is allowed
    assert ca.check_session_flags(["--session-id", "fresh-999"], prev) == []


def test_audit_flags_session_restoration(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    sterile, roots = sterile_roots(tmp_path, ws)
    result = ca.audit(
        condition=ca.CONDITIONS["C1"],
        roots=roots,
        env=sterile.env,
        launch=ca.LaunchCommand(argv=("claude", "-p", "--resume", "old-session")),
        require_launch=True,
        run_id="rsess",
    )
    assert result.session_restored is True
    assert result.verdict == "CONTAMINATED"


# --------------------------------------------------------------------------- #
# Schema conformance + secret redaction
# --------------------------------------------------------------------------- #
def test_audit_conforms_to_schema(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    write(ws / "CLAUDE.md", "unapproved")  # produce a non-trivial (CONTAMINATED) audit
    sterile, roots = sterile_roots(tmp_path, ws)
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    for cond in ("C1", "C2", "C3", "C4"):
        result = ca.audit(
            condition=ca.CONDITIONS[cond], roots=roots, env=sterile.env, run_id=f"r-{cond}"
        )
        errors = ca.validate_against_schema(result.to_dict(), schema)
        assert errors == [], f"{cond}: {errors}"


def test_clean_audit_conforms_to_schema(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    sterile, roots = sterile_roots(tmp_path, ws)
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    result = ca.audit(condition=ca.CONDITIONS["C1"], roots=roots, env=sterile.env, run_id="rc")
    assert result.verdict == "CLEAN"
    assert ca.validate_against_schema(result.to_dict(), schema) == []


def test_no_secret_values_recorded(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    sterile, roots = sterile_roots(tmp_path, ws)
    secret = "sk-SECRET-TOKEN-DO-NOT-LEAK-42"
    # MCP config with a token, and a settings file with hooks carrying a secret.
    write(roots.config_dir / ".claude.json", json.dumps({"mcpServers": {"x": {"token": secret}}}))
    write(
        roots.config_dir / "settings.json",
        json.dumps({"hooks": {"PreToolUse": [{"command": f"curl -H {secret}"}]}}),
    )
    result = ca.audit(condition=ca.CONDITIONS["C1"], roots=roots, env=sterile.env, run_id="rsec")
    blob = json.dumps(result.to_dict())
    assert secret not in blob
    # but the sources are still detected (by hash), so the run is contaminated
    assert result.verdict == "CONTAMINATED"
    assert any(s.kind == "mcp" for s in result.detected)


def test_schema_file_is_valid_json():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["type"] == "object"
    assert "contamination" in schema["properties"]


# --------------------------------------------------------------------------- #
# P1-1: launch-command / session-restoration enforcement (fail-closed)
#
# The audit must be given the exact Claude launch command; an experimental audit
# with no command supplied must fail closed instead of silently claiming a fresh
# session (the pre-fix defect: main() hard-coded argv=[]).
# --------------------------------------------------------------------------- #
def test_experimental_audit_requires_launch_command(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    sterile, roots = sterile_roots(tmp_path, ws)
    result = ca.audit(
        condition=ca.CONDITIONS["C1"],
        roots=roots,
        env=sterile.env,
        launch=None,
        require_launch=True,
        run_id="rnl",
    )
    assert result.verdict == "CONTAMINATED"
    assert result.session_command_supplied is False
    assert any("launch command" in r for r in result.reasons)
    sr = result.to_dict()["session_restoration"]
    assert sr["status"] == "unknown"
    assert sr["command_supplied"] is False
    assert sr["command_source"] == "none"


def test_fresh_process_command_passes(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    sterile, roots = sterile_roots(tmp_path, ws)
    launch = ca.fresh_launch_command(["--model", "claude-opus-4-8[1m]", "--effort", "xhigh"])
    result = ca.audit(
        condition=ca.CONDITIONS["C1"],
        roots=roots,
        env=sterile.env,
        launch=launch,
        require_launch=True,
        run_id="rfresh",
    )
    assert result.verdict == "CLEAN", result.reasons
    sr = result.to_dict()["session_restoration"]
    assert sr["restored"] is False
    assert sr["status"] == "fresh"
    assert sr["command_supplied"] is True
    assert sr["command_source"] == "fake-executor"


def test_continue_flag_rejected(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    sterile, roots = sterile_roots(tmp_path, ws)
    launch = ca.LaunchCommand(argv=("claude", "-p", "--continue"))
    result = ca.audit(
        condition=ca.CONDITIONS["C1"],
        roots=roots,
        env=sterile.env,
        launch=launch,
        require_launch=True,
        run_id="rcont",
    )
    assert result.verdict == "CONTAMINATED"
    assert result.session_restored is True
    assert any("--continue" in r for r in result.reasons)


def test_resume_flag_rejected(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    sterile, roots = sterile_roots(tmp_path, ws)
    launch = ca.LaunchCommand(argv=("claude", "-p", "--resume", "sess-42"))
    result = ca.audit(
        condition=ca.CONDITIONS["C1"],
        roots=roots,
        env=sterile.env,
        launch=launch,
        require_launch=True,
        run_id="rres",
    )
    assert result.verdict == "CONTAMINATED"
    assert result.session_restored is True
    assert any("--resume" in r for r in result.reasons)


def test_previous_session_id_rejected_by_audit(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    sterile, roots = sterile_roots(tmp_path, ws)
    reused = ca.LaunchCommand(argv=("claude", "-p", "--session-id", "prev-123"))
    result = ca.audit(
        condition=ca.CONDITIONS["C1"],
        roots=roots,
        env=sterile.env,
        launch=reused,
        require_launch=True,
        previous_session_ids=["prev-123"],
        run_id="rprev",
    )
    assert result.verdict == "CONTAMINATED"
    assert result.session_restored is True
    assert any("previous session ID reused" in r for r in result.reasons)

    # a fresh, unseen session id under the same guard is accepted
    fresh_id = ca.LaunchCommand(argv=("claude", "-p", "--session-id", "fresh-999"))
    ok = ca.audit(
        condition=ca.CONDITIONS["C1"],
        roots=roots,
        env=sterile.env,
        launch=fresh_id,
        require_launch=True,
        previous_session_ids=["prev-123"],
        run_id="rprev2",
    )
    assert ok.verdict == "CLEAN", ok.reasons


def test_json_report_reflects_supplied_command(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    sterile, roots = sterile_roots(tmp_path, ws)
    launch = ca.LaunchCommand(
        argv=("claude", "-p", "TOP-SECRET-PROMPT-BODY", "--model", "opus", "--resume", "sess-9"),
        source="argv",
    )
    result = ca.audit(
        condition=ca.CONDITIONS["C1"],
        roots=roots,
        env=sterile.env,
        launch=launch,
        require_launch=True,
        run_id="rjson",
    )
    sr = result.to_dict()["session_restoration"]
    assert sr["command_supplied"] is True
    assert sr["command_source"] == "argv"
    # recognized flags are recorded; free-text values (the -p prompt, the model
    # value) are never written into the report
    assert "--model" in sr["inspected_flags"]
    assert "--resume" in sr["inspected_flags"]
    assert "-p" in sr["inspected_flags"]
    assert "opus" not in sr["inspected_flags"]
    blob = json.dumps(result.to_dict())
    assert "TOP-SECRET-PROMPT-BODY" not in blob


def test_launch_manifest_round_trip_and_validation(tmp_path):
    good = tmp_path / "launch.json"
    good.write_text(json.dumps({"argv": ["claude", "-p", "--resume", "x"]}), encoding="utf-8")
    launch = ca.load_launch_manifest(good)
    assert launch.source == "manifest"
    assert any("--resume" in v for v in ca.check_session_flags(list(launch.argv)))

    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"no_argv_here": 1}), encoding="utf-8")
    with pytest.raises(ValueError):
        ca.load_launch_manifest(bad)

    empty = tmp_path / "empty.json"
    empty.write_text(json.dumps({"argv": []}), encoding="utf-8")
    with pytest.raises(ValueError):
        ca.load_launch_manifest(empty)


# --------------------------------------------------------------------------- #
# P1-2a: C2 condition allowlist semantics
#
# C2 = same isolation as C1 plus ONLY the approved generic, token-matched
# guidance file. It must reject all persistent context except that one file.
# --------------------------------------------------------------------------- #
_C2_GENERIC = "# Generic token-matched guidance (no repository specifics)\n"


def test_c2_rejects_persistent_context(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    sterile, roots = sterile_roots(tmp_path, ws)
    # user + project + local persistent context, none approved under C2
    write(ws / "CLAUDE.md", "# project instructions")
    write(ws / "CLAUDE.local.md", "# local overrides")
    write(roots.home / ".claude" / "CLAUDE.md", "# user instructions")
    result = ca.audit(condition=ca.CONDITIONS["C2"], roots=roots, env=sterile.env, run_id="rc2a")
    assert result.verdict == "CONTAMINATED"
    # every persistent source is flagged as unapproved
    assert sum("unapproved context source" in r for r in result.reasons) >= 3


def test_c2_rejects_repo_architecture_instructions(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    sterile, roots = sterile_roots(tmp_path, ws)
    # C2 approves only a generic guidance file (by its hash)...
    gpath = write(ws / "CLAUDE.md", _C2_GENERIC)
    approved = [ca.ApprovedArtifact("claude_md", str(gpath), ca.sha256_file(gpath))]
    cond = ca.CONDITIONS["C2"].with_approved(approved)
    # ...but the file actually present carries repository-specific architecture
    gpath.write_text("# Repository architecture: layers, modules, dependency rules\n", encoding="utf-8")
    result = ca.audit(condition=cond, roots=roots, env=sterile.env, run_id="rc2b")
    assert result.verdict == "CONTAMINATED"
    assert any("hash mismatch" in r for r in result.reasons)


def test_c2_permits_only_approved_generic_guidance(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    sterile, roots = sterile_roots(tmp_path, ws)
    gpath = write(ws / "CLAUDE.md", _C2_GENERIC)
    approved = [ca.ApprovedArtifact("claude_md", str(gpath), ca.sha256_file(gpath))]
    cond = ca.CONDITIONS["C2"].with_approved(approved)
    result = ca.audit(condition=cond, roots=roots, env=sterile.env, run_id="rc2c")
    assert result.verdict == "CLEAN", result.reasons
    assert any(s.approved for s in result.detected if s.kind == "claude_md")


def test_c2_rejects_additional_unapproved_files(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    sterile, roots = sterile_roots(tmp_path, ws)
    gpath = write(ws / "CLAUDE.md", _C2_GENERIC)
    approved = [ca.ApprovedArtifact("claude_md", str(gpath), ca.sha256_file(gpath))]
    cond = ca.CONDITIONS["C2"].with_approved(approved)
    # approved generic file is fine, but an extra unapproved file appears
    write(ws / "CLAUDE.local.md", "extra unapproved instruction")
    result = ca.audit(condition=cond, roots=roots, env=sterile.env, run_id="rc2d")
    assert result.verdict == "CONTAMINATED"
    assert any("CLAUDE.local.md" in r for r in result.reasons)


# --------------------------------------------------------------------------- #
# P1-2b: managed / remote organization policy detection
#
# Account-tied policy follows the identity, not the filesystem, so a fresh
# temporary HOME / CLAUDE_CONFIG_DIR does NOT clear it. Whenever a policy cache
# is detected the environment is non-sterile and the audit must fail closed.
# --------------------------------------------------------------------------- #
def test_managed_policy_detected_marks_environment_nonsterile(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    sterile, roots = sterile_roots(tmp_path, ws)
    write(
        roots.config_dir / "policy-limits.json",
        json.dumps({"restrictions": {"a": 1}, "defaults": {}}),
    )
    result = ca.audit(condition=ca.CONDITIONS["C1"], roots=roots, env=sterile.env, run_id="rmp1")
    assert result.verdict == "CONTAMINATED"
    mp = [s for s in result.detected if s.kind == "managed_settings"]
    assert mp and mp[0].scope == "config"
    assert any("managed_settings" in r for r in result.reasons)


def test_temp_dirs_do_not_clear_managed_policy(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    sterile, roots = sterile_roots(tmp_path, ws)
    # policy cached inside the freshly relocated temporary HOME
    write(roots.home / "remote-settings.json", json.dumps({"monitoring_notice": "x"}))
    result = ca.audit(condition=ca.CONDITIONS["C1"], roots=roots, env=sterile.env, run_id="rmp2")
    # the env IS isolated, yet the account-tied policy is still detected
    assert result.home_isolated is True
    assert result.config_dir_isolated is True
    assert result.verdict == "CONTAMINATED"
    assert any(s.kind == "managed_settings" and s.scope == "user" for s in result.detected)


def test_managed_policy_os_path_detected(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    sterile, base = sterile_roots(tmp_path, ws)
    pol = write(
        tmp_path / "ProgramData" / "ClaudeCode" / "managed-settings.json",
        json.dumps({"restrictions": {}}),
    )
    roots = ca.ScanRoots(
        workspace=base.workspace,
        home=base.home,
        config_dir=base.config_dir,
        ancestors=[],
        managed_settings=[pol],
    )
    result = ca.audit(condition=ca.CONDITIONS["C1"], roots=roots, env=sterile.env, run_id="rmp3")
    assert result.verdict == "CONTAMINATED"
    assert any(s.kind == "managed_settings" and s.scope == "managed" for s in result.detected)


def test_audit_fails_closed_unless_isolated_env_policy_satisfied(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    sterile, roots = sterile_roots(tmp_path, ws)
    pol = write(roots.config_dir / "policy-limits.json", json.dumps({"defaults": {}}))
    dirty = ca.audit(condition=ca.CONDITIONS["C1"], roots=roots, env=sterile.env, run_id="rmp4a")
    assert dirty.verdict == "CONTAMINATED"
    # once the isolated-environment requirement (no managed policy present) is
    # satisfied, a full experimental audit passes
    pol.unlink()
    clean = ca.audit(
        condition=ca.CONDITIONS["C1"],
        roots=roots,
        env=sterile.env,
        launch=ca.fresh_launch_command(),
        require_launch=True,
        run_id="rmp4b",
    )
    assert clean.verdict == "CLEAN", clean.reasons


def test_managed_policy_no_secrets_in_report(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    sterile, roots = sterile_roots(tmp_path, ws)
    secret = "org-POLICY-SECRET-TOKEN-77"
    write(
        roots.config_dir / "policy-limits.json",
        json.dumps({"restrictions": {"api_token": secret}, "compliance_taints": [secret]}),
    )
    result = ca.audit(condition=ca.CONDITIONS["C1"], roots=roots, env=sterile.env, run_id="rmp5")
    blob = json.dumps(result.to_dict())
    assert secret not in blob
    assert result.verdict == "CONTAMINATED"
    assert any(s.kind == "managed_settings" for s in result.detected)
