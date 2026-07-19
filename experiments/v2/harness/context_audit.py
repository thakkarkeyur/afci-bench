#!/usr/bin/env python3
"""Claude context-isolation audit harness for AFCI-Bench study v2.

Purpose
-------
Experimental runs must not inherit context from development sessions, previous
runs, or machine-level Claude configuration. This module (1) prepares a sterile
environment for a run, (2) scans every known context source, (3) compares what
is present against a per-condition allowlist of *approved* context, and (4)
emits ``context_audit.json`` with a fail-closed contamination verdict.

Design notes
------------
* Pure standard library (matches the repo's dependency-free Python scripts).
* All scan roots are injectable so the behaviour is unit-testable against
  synthetic filesystem layouts.
* Fails closed: any unapproved/unexpected context source, any tampered approved
  artifact, any missing isolation control, or any session-restoration flag makes
  the verdict ``CONTAMINATED`` and drives a non-zero CLI exit.
* Never records secret values. Files are represented by their SHA-256 hash and a
  non-secret ``detail`` string only; file contents, tokens, keys, and MCP server
  configs are never parsed into the audit.

This is development scaffolding for study v2. It does NOT freeze the final
benchmark configuration and it never invokes a model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

SCHEMA_VERSION = "1.0.0"

# Environment variables that MUST be set for every experimental run.
REQUIRED_ENV = {
    "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
    "DISABLE_AUTOUPDATER": "1",
}

# Session flags that restore or reuse a previous conversation. Forbidden.
RESTORATION_FLAGS = {"-c", "--continue", "-r", "--resume", "--from-pr"}
SESSION_ID_FLAGS = {"--session-id"}

# Component kinds tracked in the component_status block.
COMPONENT_KINDS = ("mcp", "plugins", "hooks", "skills", "agents", "commands")


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ApprovedArtifact:
    """A context artifact permitted to be present for a given condition."""

    kind: str
    path: str
    sha256: str

    def real(self) -> str:
        return os.path.realpath(self.path)


@dataclass(frozen=True)
class Condition:
    """An experimental condition and its filesystem context allowlist.

    ``approved`` is the single source of truth for which context artifacts may
    be present. Anything detected that is not in ``approved`` (or an approved
    artifact whose content hash does not match) is contamination.
    """

    name: str
    description: str
    context_delivery: str
    approved: Tuple[ApprovedArtifact, ...] = ()

    def with_approved(self, approved: Iterable[ApprovedArtifact]) -> "Condition":
        return Condition(
            name=self.name,
            description=self.description,
            context_delivery=self.context_delivery,
            approved=tuple(approved),
        )


# Baseline condition definitions. Approved artifacts are attached at audit time
# (from a manifest or the caller); defaults are empty = strictest fail-closed.
CONDITIONS: Dict[str, Condition] = {
    "C1": Condition(
        name="C1",
        description=(
            "Sterile baseline: no persistent Claude instructions or memory, and "
            "no repository architecture context."
        ),
        context_delivery="none",
    ),
    "C2": Condition(
        name="C2",
        description=(
            "Same isolation as C1, plus only the approved generic, "
            "token-matched guidance file."
        ),
        context_delivery="approved generic token-matched guidance file only",
    ),
    "C3": Condition(
        name="C3",
        description=(
            "Sterile user environment with only the approved condition-specific "
            "repository instruction file."
        ),
        context_delivery="single approved condition-specific repository instruction file",
    ),
    "C4": Condition(
        name="C4",
        description=(
            "No persistent repository instruction. The MAD is supplied only "
            "through explicit AFCI prompt injection and re-injected after reset."
        ),
        context_delivery="MAD via explicit AFCI prompt injection (re-injected after reset); no persistent file",
    ),
}


@dataclass
class DetectedSource:
    """A context source found present during a scan."""

    kind: str
    scope: str  # workspace | ancestor | user | config | managed | runtime
    path: str
    is_dir: bool
    sha256: Optional[str]
    detail: str
    approved: bool = False

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "scope": self.scope,
            "path": self.path,
            "is_dir": self.is_dir,
            "sha256": self.sha256,
            "detail": self.detail,
            "approved": self.approved,
        }


@dataclass
class ScanRoots:
    """Filesystem roots to scan. All injectable for testing."""

    workspace: Path
    home: Path
    config_dir: Path
    ancestors: List[Path] = field(default_factory=list)
    managed_settings: List[Path] = field(default_factory=list)

    @classmethod
    def discover(
        cls,
        workspace: Path,
        home: Path,
        config_dir: Path,
        managed_settings: Optional[Sequence[Path]] = None,
        include_ancestors: bool = True,
    ) -> "ScanRoots":
        workspace = Path(workspace).resolve()
        ancestors: List[Path] = []
        if include_ancestors:
            ancestors = list(workspace.parents)
        managed = (
            [Path(p) for p in managed_settings]
            if managed_settings is not None
            else default_managed_settings_paths()
        )
        return cls(
            workspace=workspace,
            home=Path(home),
            config_dir=Path(config_dir),
            ancestors=ancestors,
            managed_settings=managed,
        )


@dataclass
class SterileEnv:
    """A prepared sterile environment for one experimental run."""

    run_id: str
    temp_home: Path
    config_dir: Path
    env: Dict[str, str]


@dataclass
class AuditResult:
    run_id: str
    condition: str
    generated_at: str
    temp_home: str
    config_dir: str
    auto_memory_disabled: bool
    autoupdater_disabled: bool
    config_dir_isolated: bool
    home_isolated: bool
    session_restored: bool
    session_violations: List[str]
    detected: List[DetectedSource]
    approved: List[ApprovedArtifact]
    component_status: Dict[str, str]
    verdict: str
    reasons: List[str]

    @property
    def is_clean(self) -> bool:
        return self.verdict == "CLEAN"

    def to_dict(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "condition": self.condition,
            "generated_at": self.generated_at,
            "sterile_environment": {
                "temp_home": self.temp_home,
                "claude_config_dir": self.config_dir,
                "auto_memory_disabled": self.auto_memory_disabled,
                "autoupdater_disabled": self.autoupdater_disabled,
                "config_dir_isolated": self.config_dir_isolated,
                "home_isolated": self.home_isolated,
            },
            "auto_memory": {
                "disabled": self.auto_memory_disabled,
                "status": "disabled" if self.auto_memory_disabled else "enabled",
            },
            "session_restoration": {
                "restored": self.session_restored,
                "status": "restored" if self.session_restored else "fresh",
                "violations": list(self.session_violations),
            },
            "detected_context_sources": [d.to_dict() for d in self.detected],
            "permitted_context_sources": [
                {"kind": a.kind, "path": a.path, "sha256": a.sha256}
                for a in self.approved
            ],
            "approved_context_hashes": {a.path: a.sha256 for a in self.approved},
            "component_status": dict(self.component_status),
            "contamination": {"verdict": self.verdict, "reasons": list(self.reasons)},
        }


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def default_managed_settings_paths() -> List[Path]:
    """Known OS locations for enterprise managed-settings.json (not relocatable
    by env vars)."""
    return [
        Path(r"C:\ProgramData\ClaudeCode\managed-settings.json"),
        Path("/Library/Application Support/ClaudeCode/managed-settings.json"),
        Path("/etc/claude-code/managed-settings.json"),
    ]


def _dir_has_entries(path: Path) -> bool:
    try:
        return path.is_dir() and any(path.iterdir())
    except OSError:
        return False


def _settings_hooks_count(path: Path) -> int:
    """Return the number of hook groups configured in a settings file, WITHOUT
    reading any hook command values."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0
    hooks = data.get("hooks") if isinstance(data, dict) else None
    if isinstance(hooks, dict):
        return len(hooks)
    if isinstance(hooks, list):
        return len(hooks)
    return 0


def _settings_mcp_count(path: Path) -> int:
    """Return count of configured MCP servers WITHOUT reading names/urls/tokens."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0
    if not isinstance(data, dict):
        return 0
    servers = data.get("mcpServers")
    if isinstance(servers, dict):
        return len(servers)
    return 0


# --------------------------------------------------------------------------- #
# Sterile environment preparation
# --------------------------------------------------------------------------- #
def make_sterile_env(run_id: str, base_dir: Optional[Path] = None) -> SterileEnv:
    """Create a unique temporary HOME and CLAUDE_CONFIG_DIR for a run and return
    the environment overrides required for isolation.

    Two calls with different ``run_id`` values always yield distinct directories.
    """
    root = Path(base_dir) if base_dir else Path(tempfile.gettempdir())
    root.mkdir(parents=True, exist_ok=True)
    prefix = f"afci-v2-{_safe(run_id)}-"
    home = Path(tempfile.mkdtemp(prefix=prefix + "home-", dir=str(root)))
    config_dir = Path(tempfile.mkdtemp(prefix=prefix + "cfg-", dir=str(root)))

    env = {
        "HOME": str(home),
        "USERPROFILE": str(home),  # Windows HOME analogue
        "CLAUDE_CONFIG_DIR": str(config_dir),
        "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
        "DISABLE_AUTOUPDATER": "1",
    }
    return SterileEnv(run_id=run_id, temp_home=home, config_dir=config_dir, env=env)


def _safe(text: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "-" for c in text)[:40]


# --------------------------------------------------------------------------- #
# Session-restoration guard
# --------------------------------------------------------------------------- #
def check_session_flags(
    argv: Sequence[str], previous_session_ids: Iterable[str] = ()
) -> List[str]:
    """Return a list of session-restoration violations for the given argv.

    Forbids ``--continue``/``--resume``/``--from-pr`` outright and rejects
    ``--session-id`` values that reuse a previously seen session ID. A fresh,
    unseen ``--session-id`` is allowed.
    """
    prev = set(previous_session_ids)
    violations: List[str] = []
    tokens = list(argv)
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        flag, _, inline = tok.partition("=")
        if flag in RESTORATION_FLAGS:
            violations.append(f"session-restoration flag used: {flag}")
        elif flag in SESSION_ID_FLAGS:
            value = inline if inline else (tokens[i + 1] if i + 1 < len(tokens) else "")
            if value in prev and value:
                violations.append(f"previous session ID reused: {flag} {value}")
        i += 1
    return violations


# --------------------------------------------------------------------------- #
# Context source scanning
# --------------------------------------------------------------------------- #
def scan_context_sources(roots: ScanRoots) -> List[DetectedSource]:
    """Scan every known context location under ``roots`` and return the sources
    that are actually present."""
    found: List[DetectedSource] = []

    def add_file(kind: str, scope: str, path: Path, detail: str = "") -> None:
        if path.is_file():
            found.append(
                DetectedSource(
                    kind=kind,
                    scope=scope,
                    path=str(path),
                    is_dir=False,
                    sha256=sha256_file(path),
                    detail=detail or kind,
                )
            )

    def add_dir(kind: str, scope: str, path: Path, detail: str = "") -> None:
        if _dir_has_entries(path):
            found.append(
                DetectedSource(
                    kind=kind,
                    scope=scope,
                    path=str(path),
                    is_dir=True,
                    sha256=None,
                    detail=detail or f"{kind} directory populated",
                )
            )

    def scan_claude_dir(scope: str, base: Path) -> None:
        cdir = base / ".claude"
        add_file("claude_md", scope, base / "CLAUDE.md")
        add_file("claude_local_md", scope, base / "CLAUDE.local.md")
        add_file("claude_md", scope, cdir / "CLAUDE.md", "dot-claude CLAUDE.md")
        add_dir("rules", scope, cdir / "rules")
        add_dir("skills", scope, cdir / "skills")
        add_dir("agents", scope, cdir / "agents")
        add_dir("commands", scope, cdir / "commands")
        add_dir("hooks", scope, cdir / "hooks")
        add_dir("plugins", scope, cdir / "plugins")
        for name in ("settings.json", "settings.local.json"):
            sp = cdir / name
            if sp.is_file():
                hooks = _settings_hooks_count(sp)
                detail = f"settings file ({hooks} hook group(s))" if hooks else "settings file"
                found.append(
                    DetectedSource(
                        kind="hooks" if hooks else "settings",
                        scope=scope,
                        path=str(sp),
                        is_dir=False,
                        sha256=sha256_file(sp),
                        detail=detail,
                    )
                )
        # project-scoped MCP config
        add_file("mcp", scope, base / ".mcp.json", "project MCP config")

    # Workspace + ancestor directories.
    scan_claude_dir("workspace", roots.workspace)
    for anc in roots.ancestors:
        scan_claude_dir("ancestor", anc)

    # User HOME (~/.claude/...). A sterile run points HOME at a temp dir, so this
    # is normally empty; a non-sterile HOME surfaces here.
    scan_claude_dir("user", roots.home)

    # CLAUDE_CONFIG_DIR (settings, skills, plugins, agents, commands, memory).
    cfg = roots.config_dir
    for name in ("settings.json", "settings.local.json"):
        sp = cfg / name
        if sp.is_file():
            hooks = _settings_hooks_count(sp)
            found.append(
                DetectedSource(
                    kind="hooks" if hooks else "settings",
                    scope="config",
                    path=str(sp),
                    is_dir=False,
                    sha256=sha256_file(sp),
                    detail=f"config settings ({hooks} hook group(s))" if hooks else "config settings",
                )
            )
    add_dir("skills", "config", cfg / "skills")
    add_dir("agents", "config", cfg / "agents")
    add_dir("commands", "config", cfg / "commands")
    add_dir("plugins", "config", cfg / "plugins")
    add_dir("rules", "config", cfg / "rules")
    # MCP config lives in a ~/.claude.json style file: inside CLAUDE_CONFIG_DIR
    # when relocated, or at the HOME root in the default (non-relocated) layout.
    for base, scope in ((cfg, "config"), (roots.home, "user")):
        for mcp_name in (".claude.json", "claude.json"):
            mp = base / mcp_name
            if mp.is_file():
                n = _settings_mcp_count(mp)
                found.append(
                    DetectedSource(
                        kind="mcp",
                        scope=scope,
                        path=str(mp),
                        is_dir=False,
                        sha256=sha256_file(mp),
                        detail=f"MCP config ({n} server(s) configured)",
                    )
                )
    # Account-tied managed / remote policy caches. Organization policy follows
    # the authenticated account, not the filesystem, so it can persist across a
    # relocated HOME/config dir and is surfaced here as fail-closed context.
    for base, scope in ((cfg, "config"), (roots.home, "user")):
        for pol_name in ("policy-limits.json", "remote-settings.json", "managed-settings.json"):
            pp = base / pol_name
            if pp.is_file():
                found.append(
                    DetectedSource(
                        kind="managed_settings",
                        scope=scope,
                        path=str(pp),
                        is_dir=False,
                        sha256=sha256_file(pp),
                        detail=f"managed/remote policy cache ({pol_name})",
                    )
                )

    # Auto-memory files: <config>/projects/<project>/memory/*
    projects = cfg / "projects"
    if projects.is_dir():
        for mem_dir in projects.glob("*/memory"):
            for mem_file in sorted(mem_dir.rglob("*")):
                if mem_file.is_file():
                    found.append(
                        DetectedSource(
                            kind="memory",
                            scope="config",
                            path=str(mem_file),
                            is_dir=False,
                            sha256=sha256_file(mem_file),
                            detail="auto-memory file",
                        )
                    )
    # A stray project-root MEMORY.md is also memory context.
    add_file("memory", "workspace", roots.workspace / "MEMORY.md", "MEMORY.md")

    # Managed / enterprise policy (cannot be relocated by env vars).
    for mp in roots.managed_settings:
        if Path(mp).is_file():
            found.append(
                DetectedSource(
                    kind="managed_settings",
                    scope="managed",
                    path=str(mp),
                    is_dir=False,
                    sha256=sha256_file(Path(mp)),
                    detail="enterprise managed-settings policy",
                )
            )

    return found


# --------------------------------------------------------------------------- #
# Audit
# --------------------------------------------------------------------------- #
def audit(
    *,
    condition: Condition,
    roots: ScanRoots,
    env: Dict[str, str],
    argv: Sequence[str] = (),
    previous_session_ids: Iterable[str] = (),
    run_id: str,
    generated_at: str = "unspecified",
) -> AuditResult:
    """Produce a fail-closed context-isolation audit for one run."""
    approved = list(condition.approved)
    approved_by_real: Dict[str, ApprovedArtifact] = {a.real(): a for a in approved}

    detected = scan_context_sources(roots)
    reasons: List[str] = []

    # --- context-source allowlist check ---
    for src in detected:
        real = os.path.realpath(src.path)
        art = approved_by_real.get(real)
        if art is None:
            reasons.append(
                f"unapproved context source [{src.kind}] present at {src.path}"
            )
        elif src.is_dir or src.sha256 is None:
            reasons.append(
                f"approved artifact at {src.path} is a directory / unhashable; cannot verify"
            )
        elif src.sha256 != art.sha256:
            reasons.append(
                f"approved artifact at {src.path} content hash mismatch "
                f"(expected {art.sha256[:12]}..., found {src.sha256[:12]}...)"
            )
        else:
            src.approved = True

    # --- environment / isolation checks ---
    auto_memory_disabled = env.get("CLAUDE_CODE_DISABLE_AUTO_MEMORY") == "1"
    autoupdater_disabled = env.get("DISABLE_AUTOUPDATER") == "1"
    if not auto_memory_disabled:
        reasons.append("CLAUDE_CODE_DISABLE_AUTO_MEMORY is not set to 1")
    if not autoupdater_disabled:
        reasons.append("DISABLE_AUTOUPDATER is not set to 1")

    cfg_val = env.get("CLAUDE_CONFIG_DIR", "")
    config_dir_isolated = bool(cfg_val) and Path(cfg_val).resolve() == Path(
        roots.config_dir
    ).resolve()
    if not cfg_val:
        reasons.append("CLAUDE_CONFIG_DIR is not set")
    elif not config_dir_isolated:
        reasons.append("CLAUDE_CONFIG_DIR does not point at the isolated run config dir")

    home_val = env.get("HOME") or env.get("USERPROFILE") or ""
    home_isolated = bool(home_val) and Path(home_val).resolve() == Path(
        roots.home
    ).resolve()
    if not home_isolated:
        reasons.append("HOME/USERPROFILE does not point at the isolated temporary home")

    # --- session-restoration guard ---
    session_violations = check_session_flags(argv, previous_session_ids)
    reasons.extend(session_violations)
    session_restored = bool(session_violations)

    # --- per-component status ---
    component_status = {k: "none" for k in COMPONENT_KINDS}
    for src in detected:
        if src.kind in component_status:
            if src.approved:
                if component_status[src.kind] != "present-unapproved":
                    component_status[src.kind] = "approved"
            else:
                component_status[src.kind] = "present-unapproved"

    verdict = "CONTAMINATED" if reasons else "CLEAN"

    return AuditResult(
        run_id=run_id,
        condition=condition.name,
        generated_at=generated_at,
        temp_home=str(roots.home),
        config_dir=str(roots.config_dir),
        auto_memory_disabled=auto_memory_disabled,
        autoupdater_disabled=autoupdater_disabled,
        config_dir_isolated=config_dir_isolated,
        home_isolated=home_isolated,
        session_restored=session_restored,
        session_violations=session_violations,
        detected=detected,
        approved=approved,
        component_status=component_status,
        verdict=verdict,
        reasons=reasons,
    )


# --------------------------------------------------------------------------- #
# Minimal dependency-free JSON Schema validation (subset)
# --------------------------------------------------------------------------- #
class SchemaError(Exception):
    pass


_TYPE_MAP = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
    "number": (int, float),
    "integer": int,
    "null": type(None),
}


def validate_against_schema(instance, schema, path: str = "$") -> List[str]:
    """Validate ``instance`` against a JSON-Schema subset (type, properties,
    required, items, enum, additionalProperties:false). Returns a list of error
    strings (empty == valid)."""
    errors: List[str] = []
    types = schema.get("type")
    if types is not None:
        type_list = types if isinstance(types, list) else [types]
        py_types = tuple(_TYPE_MAP[t] for t in type_list)
        ok = isinstance(instance, py_types)
        # bool is a subclass of int; guard integer/number against bool.
        if ok and isinstance(instance, bool) and not ({"boolean"} & set(type_list)):
            ok = False
        if not ok:
            errors.append(f"{path}: expected type {type_list}, got {type(instance).__name__}")
            return errors

    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} not in enum {schema['enum']}")

    if isinstance(instance, dict) and (schema.get("type") == "object" or "properties" in schema):
        props = schema.get("properties", {})
        for req in schema.get("required", []):
            if req not in instance:
                errors.append(f"{path}: missing required property '{req}'")
        if schema.get("additionalProperties") is False:
            for key in instance:
                if key not in props:
                    errors.append(f"{path}: additional property '{key}' not allowed")
        for key, subschema in props.items():
            if key in instance:
                errors.extend(validate_against_schema(instance[key], subschema, f"{path}.{key}"))

    if isinstance(instance, list) and "items" in schema:
        for idx, item in enumerate(instance):
            errors.extend(validate_against_schema(item, schema["items"], f"{path}[{idx}]"))

    return errors


# --------------------------------------------------------------------------- #
# Approved-context manifest loading
# --------------------------------------------------------------------------- #
def load_approved_manifest(path: Path) -> List[ApprovedArtifact]:
    """Load approved artifacts from a JSON manifest:
    ``{"approved": [{"kind": ..., "path": ..., "sha256": ...}, ...]}``."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    items = data.get("approved", []) if isinstance(data, dict) else data
    return [
        ApprovedArtifact(kind=i["kind"], path=i["path"], sha256=i["sha256"]) for i in items
    ]


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Prepare a sterile environment and audit Claude context isolation."
    )
    p.add_argument("--condition", required=True, choices=sorted(CONDITIONS))
    p.add_argument("--run-id", required=True)
    p.add_argument("--workspace", default=".", help="Repository working directory to scan.")
    p.add_argument("--out", default="context_audit.json", help="Audit JSON output path.")
    p.add_argument(
        "--approved-manifest",
        default=None,
        help="JSON manifest of approved artifacts for the condition.",
    )
    p.add_argument(
        "--base-tmp",
        default=None,
        help="Base directory for the temporary HOME/config dir (default: system temp).",
    )
    p.add_argument(
        "--previous-session-id",
        action="append",
        default=[],
        help="A previously used session ID to reject on reuse (repeatable).",
    )
    p.add_argument(
        "--generated-at",
        default="unspecified",
        help="Timestamp string to stamp into the audit (caller-supplied; keeps this pure).",
    )
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        condition = CONDITIONS[args.condition]
        if args.approved_manifest:
            condition = condition.with_approved(
                load_approved_manifest(Path(args.approved_manifest))
            )
        sterile = make_sterile_env(
            args.run_id, base_dir=Path(args.base_tmp) if args.base_tmp else None
        )
        roots = ScanRoots.discover(
            workspace=Path(args.workspace),
            home=sterile.temp_home,
            config_dir=sterile.config_dir,
        )
        result = audit(
            condition=condition,
            roots=roots,
            env=sterile.env,
            argv=[],  # this harness never restores a session
            previous_session_ids=args.previous_session_id,
            run_id=args.run_id,
            generated_at=args.generated_at,
        )
        payload = result.to_dict()
    except Exception as exc:  # fail closed on any error
        payload = {
            "schema_version": SCHEMA_VERSION,
            "run_id": args.run_id,
            "condition": args.condition,
            "generated_at": args.generated_at,
            "sterile_environment": {
                "temp_home": "",
                "claude_config_dir": "",
                "auto_memory_disabled": False,
                "autoupdater_disabled": False,
                "config_dir_isolated": False,
                "home_isolated": False,
            },
            "auto_memory": {"disabled": False, "status": "enabled"},
            "session_restoration": {"restored": True, "status": "restored", "violations": []},
            "detected_context_sources": [],
            "permitted_context_sources": [],
            "approved_context_hashes": {},
            "component_status": {k: "none" for k in COMPONENT_KINDS},
            "contamination": {"verdict": "CONTAMINATED", "reasons": [f"audit error: {exc}"]},
        }

    Path(args.out).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    verdict = payload["contamination"]["verdict"]
    print(f"[context_audit] condition={args.condition} run_id={args.run_id} verdict={verdict}")
    for reason in payload["contamination"]["reasons"]:
        print(f"  - {reason}")
    return 0 if verdict == "CLEAN" else 1


if __name__ == "__main__":
    sys.exit(main())
