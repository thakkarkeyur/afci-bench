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
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

SCHEMA_VERSION = "1.1.0"

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

#: AUTHENTICATION MATERIAL, which is NOT experiment-relevant context.
#:
#: ``SL-PT08-04`` draws the line this constant encodes: isolation is defined by
#: the effective MODEL-VISIBLE EXECUTION CONTEXT, not by billing identity. A
#: credential answers "may this account call the API at all"; it carries no
#: instruction, no skill, no tool and no task guidance, so its presence can
#: never change what the model is told. It is therefore permitted in a sterile
#: profile — and, because permitting it silently would be indistinguishable from
#: failing to look, it is RECORDED as authentication material rather than
#: ignored. Its CONTENTS are never read, hashed into a report, or logged.
AUTHENTICATION_FILES = frozenset({".credentials.json"})

#: Account-tied metadata the runtime RE-CREATES for itself after a successful
#: subscription authentication. These files are not copied into a sterile
#: profile; they appear anyway, which is why a filesystem-only audit that treats
#: every non-empty config file as contamination can never return CLEAN for a
#: subscription-authenticated run. Under ``SL-PT08-04`` they are adjudicated on
#: CONTENT (see :func:`account_policy_injects_context`) and only count as
#: contamination when they demonstrably inject model-visible context.
ACCOUNT_POLICY_FILES = frozenset(
    {"policy-limits.json", "remote-settings.json", ".claude.json", "claude.json"}
)

#: Directories the runtime creates for its own bookkeeping inside a sterile
#: config dir. They carry no instruction; ``sessions`` must additionally be
#: EMPTY, because a populated one would be exactly the prior-session state the
#: reset protocol forbids.
RUNTIME_CREATED_DIRS = frozenset({"backups", "sessions", "statsig", "telemetry"})

#: Environment variables a sterile launch pins beyond :data:`REQUIRED_ENV`.
#: ``DISABLE_NON_ESSENTIAL_MODEL_CALLS`` is load-bearing for the model-identity
#: contract, not a tidiness control: without it the runtime makes auxiliary
#: calls to a DIFFERENT model for its own housekeeping, those calls appear in
#: ``modelUsage``, and the Q1 readback then reports two distinct resolved model
#: ids and fails as AMBIGUOUS. Pinning it is what makes the readback single-valued.
STERILE_DETERMINISM_ENV: Dict[str, str] = {
    "DISABLE_NON_ESSENTIAL_MODEL_CALLS": "1",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "DISABLE_TELEMETRY": "1",
    "DISABLE_ERROR_REPORTING": "1",
    "DISABLE_BUG_COMMAND": "1",
}

#: The ONLY host environment variables inherited by a sterile launch. Everything
#: else — notably every ``CLAUDE_*``/``ANTHROPIC_*`` variable belonging to the
#: developer session that starts the run — is dropped. This is an allowlist
#: because a denylist cannot be proved complete.
ENV_ALLOWLIST: Tuple[str, ...] = (
    "SystemRoot", "windir", "COMSPEC", "ComSpec", "PATHEXT", "OS",
    "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE", "PROCESSOR_IDENTIFIER",
    "SystemDrive", "ProgramData", "ProgramFiles", "ProgramFiles(x86)",
    "PATH", "LANG", "LC_ALL", "TZ",
)

#: Variable-name prefixes that may never survive into a sterile launch.
FORBIDDEN_ENV_PREFIXES: Tuple[str, ...] = ("CLAUDE", "ANTHROPIC", "AWS_", "GOOGLE_")

#: ``CLAUDE_*`` names the runner PINS deliberately, as opposed to inheriting.
#: Listed by name so the distinction is explicit: a governed control is one this
#: harness sets on purpose, and everything else with the same prefix came from
#: the session that started the run and must not survive into it.
GOVERNED_CLAUDE_ENV: Tuple[str, ...] = (
    "CLAUDE_CONFIG_DIR",
    "CLAUDE_CODE_DISABLE_AUTO_MEMORY",
    "CLAUDE_CODE_DISABLE_WORKFLOWS",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC",
    "CLAUDE_CODE_DISABLE_TERMINAL_TITLE",
)


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
    #: What this source IS, under ``SL-PT08-04``. ``context`` is the default and
    #: the strict reading: experiment-relevant unless adjudicated otherwise.
    #: ``account_policy`` is generic account metadata proved non-instructional.
    classification: str = "context"

    def to_dict(self) -> dict:
        payload: Dict[str, object] = {
            "kind": self.kind,
            "scope": self.scope,
            "path": self.path,
            "is_dir": self.is_dir,
            "sha256": self.sha256,
            "detail": self.detail,
            "approved": self.approved,
        }
        # Emitted only when it carries information, so a default audit stays
        # byte-compatible with the pinned context_audit schema.
        if self.classification != "context":
            payload["classification"] = self.classification
        return payload


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
    #: Where the provisioned credential was placed, when subscription
    #: authentication was requested. The path is recorded; the contents are not
    #: read, hashed or logged anywhere in this module.
    credential_path: Optional[str] = None


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
    session_status: str
    session_violations: List[str]
    session_command_supplied: bool
    session_command_source: str
    session_command_flags: List[str]
    detected: List[DetectedSource]
    approved: List[ApprovedArtifact]
    component_status: Dict[str, str]
    verdict: str
    reasons: List[str]
    #: SL-PT08-04 dimensions. Defaulted so every existing constructor call and
    #: every existing consumer of this dataclass keeps working unchanged.
    account_policy: List[Dict[str, str]] = field(default_factory=list)
    authentication: Dict[str, object] = field(default_factory=dict)
    runtime_context: Dict[str, object] = field(default_factory=dict)
    profile_findings: List[str] = field(default_factory=list)
    env_violations: List[str] = field(default_factory=list)
    #: True only when a caller asked for an SL-PT08-04 dimension. The extra
    #: report blocks are emitted ONLY then, so a default audit stays byte-
    #: compatible with the PINNED experiments/v2/schemas/context_audit.schema.json
    #: and recording this clarification moves no pinned path and forces no
    #: private re-link.
    diagnostic_mode: bool = False

    @property
    def is_clean(self) -> bool:
        return self.verdict == "CLEAN"

    def to_dict(self) -> dict:
        payload: Dict[str, object] = {
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
                "status": self.session_status,
                "violations": list(self.session_violations),
                "command_supplied": self.session_command_supplied,
                "command_source": self.session_command_source,
                "inspected_flags": list(self.session_command_flags),
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
        if not self.diagnostic_mode:
            return payload
        payload.update({
            "account_policy_metadata": {
                "present": bool(self.account_policy),
                "adjudicated": list(self.account_policy),
                "experiment_relevant_context_detected": any(
                    f.get("injects_experiment_relevant_context")
                    for f in self.account_policy
                ),
            },
            "authentication": dict(self.authentication),
            "runtime_reported_context": dict(self.runtime_context),
            "sterile_profile_findings": list(self.profile_findings),
            "inherited_env_violations": list(self.env_violations),
        })
        return payload


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
def make_sterile_env(
    run_id: str,
    base_dir: Optional[Path] = None,
    *,
    credential_source: Optional[Path] = None,
    launchable: bool = False,
) -> SterileEnv:
    """Create a unique temporary HOME and CLAUDE_CONFIG_DIR for a run and return
    the environment overrides required for isolation.

    Two calls with different ``run_id`` values always yield distinct directories.

    ``launchable=True`` additionally builds the environment a real process can
    actually start in: the OS/runtime allowlist, redirected scratch directories,
    and the determinism controls. The default stays the audit-only view so every
    existing caller keeps the environment it already had.

    ``credential_source`` provisions subscription authentication by copying
    **exactly one file** — the credential — into the sterile config directory.
    Nothing else is copied from the host profile: no settings, no skills, no
    plugins, no commands, no MCP configuration, no memory, no session history.
    The file's CONTENTS are never read by this module.
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

    credential_path: Optional[Path] = None
    if credential_source is not None:
        source = Path(credential_source)
        if source.name not in AUTHENTICATION_FILES:
            raise ValueError(
                f"{source.name!r} is not authentication material; only "
                f"{sorted(AUTHENTICATION_FILES)} may be provisioned into a "
                "sterile profile, and no other host Claude configuration may be "
                "copied under any circumstances"
            )
        if not source.is_file():
            raise FileNotFoundError(f"no credential file at {source}")
        credential_path = config_dir / source.name
        shutil.copyfile(source, credential_path)

    if launchable:
        scratch = home / "scratch"
        for sub in (scratch, home / "AppData" / "Roaming", home / "AppData" / "Local"):
            sub.mkdir(parents=True, exist_ok=True)
        env.update(build_allowlisted_env())
        env.update(STERILE_DETERMINISM_ENV)
        env.update(
            {
                "HOMEDRIVE": os.path.splitdrive(str(home))[0] or "",
                "HOMEPATH": os.path.splitdrive(str(home))[1],
                "APPDATA": str(home / "AppData" / "Roaming"),
                "LOCALAPPDATA": str(home / "AppData" / "Local"),
                "TEMP": str(scratch),
                "TMP": str(scratch),
            }
        )
        # Re-pin the isolation variables last: an allowlisted host value must
        # never be able to overwrite the sterile ones.
        env["HOME"] = str(home)
        env["USERPROFILE"] = str(home)
        env["CLAUDE_CONFIG_DIR"] = str(config_dir)

    return SterileEnv(
        run_id=run_id,
        temp_home=home,
        config_dir=config_dir,
        env=env,
        credential_path=str(credential_path) if credential_path else None,
    )


def build_allowlisted_env(source: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Return only the OS/runtime variables a sterile launch is allowed to keep.

    Built by allowlist, never by subtraction: the developer session that starts a
    run exports its own ``CLAUDE_*`` variables (session id, entrypoint, messaging
    socket and token), and a denylist that missed one would silently hand the
    experimental process a handle back into this session.

    The lookup is deliberately case-insensitive. Windows environment names are
    case-insensitive, and ``dict(os.environ)`` upper-cases every key — so an
    exact-match allowlist silently drops ``SystemRoot``, ``ComSpec``,
    ``ProgramFiles`` and the rest. A launch missing ``SystemRoot`` does not
    degrade politely: the process dies at startup with a stack-buffer-overrun
    status and writes nothing at all to stderr.
    """
    src = dict(os.environ if source is None else source)
    folded = {name.upper(): value for name, value in src.items()}
    return {
        name: folded[name.upper()]
        for name in ENV_ALLOWLIST
        if name.upper() in folded
    }


def inherited_env_violations(env: Dict[str, str]) -> List[str]:
    """Names in ``env`` that a sterile launch may not carry.

    ``CLAUDE_CONFIG_DIR`` and the governed determinism controls are pinned BY the
    runner, so they are permitted by identity; any other ``CLAUDE_*`` /
    ``ANTHROPIC_*`` variable is inheritance from the calling session.
    """
    governed = (
        set(STERILE_DETERMINISM_ENV)
        | set(REQUIRED_ENV)
        | set(GOVERNED_CLAUDE_ENV)
    )
    return sorted(
        name
        for name in env
        if name not in governed
        and name.upper().startswith(FORBIDDEN_ENV_PREFIXES)
    )


def _safe(text: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "-" for c in text)[:40]


# --------------------------------------------------------------------------- #
# SL-PT08-04 — authentication material vs experiment-relevant context
#
# The distinction this section implements is the whole of the clarification, so
# it is implemented as an adjudication over CONTENT rather than as a filename
# exemption. A filename exemption would pass a policy file that had been made to
# carry a system prompt; reading the shape catches that, and fails closed on
# anything it cannot parse or does not recognise.
# --------------------------------------------------------------------------- #

#: Keys that would make an account-tied file instruction-bearing. ``projects``
#: is on this list because that is where per-project history, allowed-tool
#: decisions and directory trust live: prior-session state by another name.
INSTRUCTION_BEARING_KEYS = frozenset(
    {
        "mcpServers", "hooks", "skills", "agents", "commands", "plugins",
        "outputStyle", "systemPrompt", "appendSystemPrompt", "projects",
        "rules", "memory", "customInstructions", "statusLine", "env",
    }
)


def _non_empty(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, (str, bytes)):
        return bool(str(value).strip())
    if isinstance(value, (dict, list, tuple, set)):
        return len(value) > 0
    return True


def _string_leaves(value: object) -> List[str]:
    """Every non-empty string leaf, wherever it sits in the structure."""
    out: List[str] = []
    if isinstance(value, str):
        if value.strip():
            out.append(value)
    elif isinstance(value, dict):
        for nested in value.values():
            out.extend(_string_leaves(nested))
    elif isinstance(value, (list, tuple)):
        for nested in value:
            out.extend(_string_leaves(nested))
    return out


def account_policy_injects_context(path: Path) -> Tuple[bool, str]:
    """Does this account-tied file inject model-visible context? Fail closed.

    Returns ``(injects, reason)``. ``injects=False`` means the file was read and
    positively shown to carry only generic, non-instructional account metadata —
    never merely that it was skipped.
    """
    path = Path(path)
    name = path.name
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return True, f"{name} could not be read or parsed ({exc.__class__.__name__}); fail closed"

    if not isinstance(data, (dict, list)):
        return True, f"{name} is not a JSON object or array"

    if name == "remote-settings.json":
        if _non_empty(data):
            return True, f"{name} carries remote settings content: {sorted(data)[:6]}"
        return False, f"{name} is empty; it carries no remote setting"

    if name == "policy-limits.json":
        present = [k for k in INSTRUCTION_BEARING_KEYS if _non_empty(data.get(k))]
        if present:
            return True, f"{name} carries instruction-bearing keys {present}"
        leaves = _string_leaves(data)
        if leaves:
            return True, (
                f"{name} carries {len(leaves)} non-empty text value(s); text in an "
                "account policy can reach the model, so it is treated as injected "
                f"context (first: {leaves[0][:60]!r})"
            )
        return False, (
            f"{name} carries only non-textual account limits "
            f"({', '.join(sorted(data)) or 'no keys'}); generic restrictions and "
            "defaults, no instruction, no skill, no tool, no task guidance"
        )

    if name in {".claude.json", "claude.json"}:
        present = [k for k in INSTRUCTION_BEARING_KEYS if _non_empty(data.get(k))]
        if present:
            return True, f"{name} carries instruction-bearing keys {present}"
        return False, (
            f"{name} carries only account/machine bookkeeping "
            f"({len(data)} key(s)); no MCP server, no hook, no skill, no command, "
            "no project history"
        )

    return True, f"{name} is not a recognised account-policy file"


def verify_sterile_profile(
    config_dir: Path, *, expect_credential: bool = True
) -> List[str]:
    """Enumerate the WHOLE sterile config directory and report anything unexpected.

    Stronger than :func:`scan_context_sources`, which looks only where context is
    normally found. This walks every entry and requires each to be the
    provisioned credential, an adjudicated account-policy file, or an empty
    runtime-created bookkeeping directory. A file nobody anticipated is a finding
    rather than a silence.
    """
    config_dir = Path(config_dir)
    findings: List[str] = []
    if not config_dir.is_dir():
        return [f"sterile config dir {config_dir} does not exist"]

    credential_seen = False
    for entry in sorted(config_dir.rglob("*")):
        rel = entry.relative_to(config_dir)
        top = rel.parts[0]
        if entry.is_dir():
            if top not in RUNTIME_CREATED_DIRS:
                findings.append(f"unexpected directory in sterile profile: {rel}")
            elif top == "sessions" and _dir_has_entries(entry):
                findings.append(
                    f"sessions/ is populated ({rel}); a sterile profile carries no "
                    "prior-session state"
                )
            continue
        if entry.name in AUTHENTICATION_FILES and len(rel.parts) == 1:
            credential_seen = True
            continue
        if top in RUNTIME_CREATED_DIRS:
            continue
        if entry.name in ACCOUNT_POLICY_FILES and len(rel.parts) == 1:
            injects, reason = account_policy_injects_context(entry)
            if injects:
                findings.append(f"account-tied file injects context: {reason}")
            continue
        findings.append(f"unexpected file in sterile profile: {rel}")

    if expect_credential and not credential_seen:
        findings.append(
            "no credential was provisioned; the launch could not authenticate"
        )
    if not expect_credential and credential_seen:
        findings.append("a credential is present but none was provisioned")
    return findings


# --------------------------------------------------------------------------- #
# Runtime-reported context (the audit of what the model actually saw)
# --------------------------------------------------------------------------- #
#: Fields of the headless ``system.init`` event that enumerate model-visible
#: context. Each must be EMPTY for a sterile run. This is the evidence that
#: makes the audit an observation rather than an attestation: the filesystem
#: scan proves nothing was placed, and this proves nothing was loaded.
RUNTIME_CONTEXT_FIELDS = ("skills", "slash_commands", "plugins", "mcp_servers")


@dataclass
class RuntimeContextEvidence:
    """What the runtime itself reported as loaded, read back from its own event."""

    supplied: bool
    fields: Dict[str, object] = field(default_factory=dict)
    api_key_source: Optional[str] = None
    runtime_version: Optional[str] = None
    permission_mode: Optional[str] = None
    output_style: Optional[str] = None
    session_id: Optional[str] = None
    violations: List[str] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return self.supplied and not self.violations

    def to_dict(self) -> dict:
        return {
            "supplied": self.supplied,
            "loaded_context": dict(self.fields),
            "api_key_source": self.api_key_source,
            "runtime_version": self.runtime_version,
            "permission_mode": self.permission_mode,
            "output_style": self.output_style,
            "session_id": self.session_id,
            "violations": list(self.violations),
            "verdict": "CLEAN" if self.clean else "NOT_DEMONSTRATED",
        }


def audit_runtime_context(init_event: Optional[dict]) -> RuntimeContextEvidence:
    """Judge the runtime's own ``system.init`` report of what it loaded.

    No event means NOT DEMONSTRATED, never clean: an absent readback is the one
    case where assuming sterility would be assuming the thing under test.
    """
    if not isinstance(init_event, dict):
        return RuntimeContextEvidence(
            supplied=False,
            violations=[
                "no system.init event was captured, so what the runtime loaded "
                "cannot be read back and sterility is not demonstrated"
            ],
        )

    fields: Dict[str, object] = {}
    violations: List[str] = []
    for name in RUNTIME_CONTEXT_FIELDS:
        value = init_event.get(name)
        fields[name] = value
        if _non_empty(value):
            violations.append(
                f"the runtime loaded {name}={value!r}; a sterile execution context "
                "loads none"
            )

    style = init_event.get("output_style")
    if style not in (None, "", "default"):
        violations.append(f"a non-default output style was loaded: {style!r}")

    return RuntimeContextEvidence(
        supplied=True,
        fields=fields,
        api_key_source=init_event.get("apiKeySource"),
        runtime_version=init_event.get("claude_code_version"),
        permission_mode=init_event.get("permissionMode"),
        output_style=style,
        session_id=init_event.get("session_id"),
        violations=violations,
    )


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


@dataclass(frozen=True)
class LaunchCommand:
    """The exact command line the experimental runner uses to start Claude.

    The (future) runner must supply this so the audit can prove session freshness
    from the *real* invocation rather than assuming it. ``source`` records
    provenance: ``argv`` (passed directly / built by the runner), ``manifest``
    (loaded from a validated JSON manifest), or ``fake-executor`` (a synthetic
    clean command produced by :func:`fresh_launch_command` for development tests
    only — never for an experimental run).
    """

    argv: Tuple[str, ...]
    source: str = "argv"

    def flag_tokens(self) -> List[str]:
        """Recognized flag tokens (``-x`` / ``--x``) with their values stripped,
        for the audit report. Free-text values — notably a ``-p`` prompt — are
        never recorded, consistent with the no-secret-values rule."""
        return [tok.partition("=")[0] for tok in self.argv if tok.startswith("-")]


def fresh_launch_command(extra: Sequence[str] = ()) -> LaunchCommand:
    """A synthetic clean (non-restoring) ``claude -p`` launch command for
    development tests. Tagged ``fake-executor`` so it can never be mistaken for a
    real experimental launch."""
    argv = ("claude", "-p", "--no-session-persistence", *extra)
    return LaunchCommand(argv=argv, source="fake-executor")


def load_launch_manifest(path: Path) -> LaunchCommand:
    """Load and validate a launch-command manifest: ``{"argv": ["claude", ...]}``.

    Raises ``ValueError`` on any malformed manifest so the caller fails closed."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    argv = data.get("argv") if isinstance(data, dict) else None
    if not isinstance(argv, list) or not argv:
        raise ValueError("launch manifest must be an object with a non-empty 'argv' array")
    if not all(isinstance(tok, str) for tok in argv):
        raise ValueError("launch manifest 'argv' must contain only strings")
    return LaunchCommand(argv=tuple(argv), source="manifest")


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
    launch: Optional[LaunchCommand] = None,
    require_launch: bool = False,
    previous_session_ids: Iterable[str] = (),
    run_id: str,
    generated_at: str = "unspecified",
    account_policy_adjudication: bool = False,
    credential_path: Optional[str] = None,
    runtime_init_event: Optional[dict] = None,
    verify_profile: bool = False,
    require_runtime_readback: bool = False,
) -> AuditResult:
    """Produce a fail-closed context-isolation audit for one run.

    ``launch`` is the exact command the runner will use to start Claude. When
    ``require_launch`` is True (experimental mode) a launch command is mandatory:
    if none is supplied the audit refuses to certify session freshness and fails
    closed. When False (development mode) the session dimension is skipped so the
    other dimensions can be tested in isolation.
    """
    approved = list(condition.approved)
    approved_by_real: Dict[str, ApprovedArtifact] = {a.real(): a for a in approved}

    detected = scan_context_sources(roots)
    reasons: List[str] = []
    account_policy_findings: List[Dict[str, str]] = []

    # --- SL-PT08-04 account-policy adjudication (opt-in, diagnostic-scoped) ---
    #
    # OFF by default, so every caller that has not been granted the clarification
    # keeps the strict reading in which any account-tied file is contamination.
    # ON, each such file is READ and judged: generic limits pass, anything
    # instruction-bearing still fails. Enterprise managed settings at the OS path
    # (scope="managed") are never adjudicated — TD-B19 requires their absence and
    # this clarification does not touch that.
    if account_policy_adjudication:
        for src in detected:
            if src.scope not in {"config", "user"} or src.is_dir:
                continue
            if Path(src.path).name not in ACCOUNT_POLICY_FILES:
                continue
            injects, reason = account_policy_injects_context(Path(src.path))
            account_policy_findings.append(
                {
                    "path": src.path,
                    "injects_experiment_relevant_context": injects,
                    "detail": reason,
                }
            )
            if not injects:
                src.classification = "account_policy"
                src.detail = f"{src.detail}; adjudicated non-instructional: {reason}"

    # --- context-source allowlist check ---
    for src in detected:
        if src.classification == "account_policy":
            # Recorded in the report, and deliberately not a contamination
            # reason: it was read and shown to carry no model-visible context.
            continue
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
    # The launch command is the exact argv the runner uses to start Claude. An
    # experimental audit (require_launch=True) MUST be given one, or it cannot
    # prove the process is fresh and fails closed. Development tests may omit it
    # (require_launch=False) to exercise the other dimensions in isolation.
    session_command_supplied = launch is not None
    session_command_source = launch.source if launch is not None else "none"
    session_command_flags = launch.flag_tokens() if launch is not None else []

    restoration_violations: List[str] = []
    if launch is not None:
        restoration_violations = check_session_flags(launch.argv, previous_session_ids)
    session_violations = list(restoration_violations)
    if launch is None and require_launch:
        session_violations.append(
            "no Claude launch command supplied; cannot certify a fresh session "
            "(experimental audit requires --launch-argv or --launch-manifest)"
        )
    reasons.extend(session_violations)

    session_restored = bool(restoration_violations)
    if session_restored:
        session_status = "restored"
    elif session_command_supplied:
        session_status = "fresh"
    else:
        session_status = "unknown"

    # --- inherited-environment guard ---
    # A sterile HOME is worth nothing if the process still carries the calling
    # session's CLAUDE_* variables, so the environment is checked by allowlist.
    env_violations = inherited_env_violations(env)
    for name in env_violations:
        reasons.append(
            f"inherited environment variable {name} is not in the sterile allowlist"
        )

    # --- authentication material (permitted, and therefore recorded) ---
    credential_present = bool(credential_path) and Path(credential_path).is_file()
    authentication = {
        "mechanism": "claude-code-subscription-oauth",
        "api_key_required": False,
        "api_key_env_var_present": any(
            n.upper() == "ANTHROPIC_API_KEY" for n in env
        ),
        "credential_provisioned": credential_present,
        "credential_path": str(credential_path) if credential_path else None,
        "credential_contents_read": False,
        "classification": (
            "authentication material: permitted under SL-PT08-04 because it "
            "carries no instruction, skill, tool or task guidance and therefore "
            "cannot change what the model is told"
        ),
    }
    if authentication["api_key_env_var_present"]:
        reasons.append(
            "ANTHROPIC_API_KEY is present in the sterile environment; this "
            "diagnostic authenticates by subscription and requires no API key"
        )

    # --- whole-profile verification ---
    profile_findings: List[str] = []
    if verify_profile:
        profile_findings = verify_sterile_profile(
            roots.config_dir, expect_credential=credential_present
        )
        reasons.extend(profile_findings)

    # --- what the runtime itself reported loading ---
    #
    # A pre-launch audit legitimately has no readback yet, so an absent event is
    # only a finding when the caller says the readback is required — which the
    # post-launch audit does. Without that distinction an absent readback would
    # be indistinguishable from a clean one, and the audit would fail OPEN on
    # exactly the run whose process never started.
    runtime_context = audit_runtime_context(runtime_init_event)
    if runtime_init_event is not None or require_runtime_readback:
        reasons.extend(runtime_context.violations)

    # --- per-component status ---
    component_status = {k: "none" for k in COMPONENT_KINDS}
    for src in detected:
        if src.classification == "account_policy":
            continue
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
        session_status=session_status,
        session_violations=session_violations,
        session_command_supplied=session_command_supplied,
        session_command_source=session_command_source,
        session_command_flags=session_command_flags,
        detected=detected,
        approved=approved,
        component_status=component_status,
        verdict=verdict,
        reasons=reasons,
        account_policy=account_policy_findings,
        authentication=authentication,
        runtime_context=runtime_context.to_dict(),
        profile_findings=profile_findings,
        env_violations=env_violations,
        diagnostic_mode=bool(
            account_policy_adjudication
            or verify_profile
            or credential_path
            or require_runtime_readback
            or runtime_init_event is not None
        ),
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
        "--launch-argv",
        default=None,
        help=(
            "JSON array of the exact Claude launch argv the runner will use, e.g. "
            "'[\"claude\", \"-p\", \"--model\", \"claude-opus-4-8[1m]\"]'. Required "
            "for an experimental audit unless --launch-manifest or "
            "--allow-missing-launch is given."
        ),
    )
    p.add_argument(
        "--launch-manifest",
        default=None,
        help="Path to a JSON launch manifest {\"argv\": [...]} (alternative to --launch-argv).",
    )
    p.add_argument(
        "--allow-missing-launch",
        action="store_true",
        help=(
            "DEVELOPMENT ONLY: skip the mandatory launch-command check. Never use "
            "for an experimental run — the session-freshness dimension is then "
            "recorded as 'unknown'."
        ),
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
        # Resolve the launch command supplied by the runner. Experimental mode
        # requires exactly one source; if none is given the audit fails closed
        # (unless --allow-missing-launch is set for development).
        if args.launch_manifest and args.launch_argv:
            raise ValueError("supply only one of --launch-manifest / --launch-argv")
        launch: Optional[LaunchCommand] = None
        if args.launch_manifest:
            launch = load_launch_manifest(Path(args.launch_manifest))
        elif args.launch_argv:
            parsed = json.loads(args.launch_argv)
            if not isinstance(parsed, list) or not all(isinstance(t, str) for t in parsed):
                raise ValueError("--launch-argv must be a JSON array of strings")
            launch = LaunchCommand(argv=tuple(parsed), source="argv")
        result = audit(
            condition=condition,
            roots=roots,
            env=sterile.env,
            launch=launch,
            require_launch=not args.allow_missing_launch,
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
            "session_restoration": {
                "restored": False,
                "status": "unknown",
                "violations": [],
                "command_supplied": False,
                "command_source": "none",
                "inspected_flags": [],
            },
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
