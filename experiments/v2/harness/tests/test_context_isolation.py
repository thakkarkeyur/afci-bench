"""Tests for the AFCI-Bench v2 context-isolation harness (context_audit.py).

These prove detection of every contamination source, the per-condition
allowlist semantics (C1/C3/C4), sterile-environment uniqueness, the
session-restoration guard, schema conformance, and that no secret values are
ever recorded.
"""
import json
from pathlib import Path

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
        argv=["--resume", "old-session"],
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
