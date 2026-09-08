#!/usr/bin/env python3
"""Deterministic run-artifact layout and the run record's firewall.

Layout, under ``<artifact_root>/<run_id>/``::

    run_record.json          the top-level record (carries the quarantine flags)
    readiness.json           the prerequisite report
    context_audit.json       context_audit.py's own artifact, unmodified
    launch_manifest.json     ART-LAUNCH: the exact argv, no free-text values
    prepared_manifest.json   prepare_model_worktree.py's snapshot manifest
    worktree/                the prepared model-visible worktree
    worktree_post_run/       the captured model-modified worktree (real runs)
    run_output.jsonl         ART-RUNLOG: runtime output, when one exists

Three properties are load-bearing:

**The purpose is mandatory.** :func:`build_run_record` derives the five
eligibility flags from the governed purpose and refuses to write a record that
lacks a purpose or carries flags disagreeing with it. A caller cannot promote a
diagnostic artifact by handing in different flags.

**Non-confirmatory artifacts stay out of the confirmatory areas.**
``experiments/v2/results/`` and ``experiments/v2/analysis/`` are refused as
artifact roots for a non-confirmatory purpose; the default root is a scratch
directory outside the repository.

**Records are deterministic.** ``run_id`` is derived from the run's own identity
(purpose, task, condition, task hash, substrate hash, mode) and timestamps are
caller-supplied, matching ``context_audit.py``'s ``--generated-at`` convention.
Two identical runs produce identical records.

A run record is not a result. The schema pins ``is_result: false`` and
``scored: false``, so no record this runner can currently emit is expressible as
a scored observation.

No model is invoked and no benchmark task is executed.
"""
from __future__ import annotations

import hashlib
import json
import platform
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import context_audit as ca
import run_governance as gov

SCHEMA_PATH = Path(__file__).resolve().parent / "run_record.schema.json"
RECORD_SCHEMA_VERSION = "1.0.0"

#: The governing documents whose identities are recorded as protocol versions.
PROTOCOL_DOCS: Dict[str, str] = {
    "condition_spec": "docs/v2/CONDITIONS.md",
    "oracle_spec": "docs/v2/ORACLE_VALIDATION_REQUIREMENTS.md",
    "acceptance_spec": "docs/v2/HIDDEN_EVALUATOR_BOUNDARY.md",
    "reset_protocol": "docs/v2/RESET_PROTOCOL.md",
    "model_execution_config": "docs/v2/MODEL_EXECUTION_CONTROLS.md",
    "guard_spec": "docs/v2/ARCHITECTURE_RULE_CATALOG.yml",
    "worktree_policy": "docs/v2/MODEL_VISIBLE_WORKTREE_POLICY.md",
    "diagnostic_decision": "docs/v2/PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def protocol_versions(repo: Path = gov.REPO) -> Dict[str, str]:
    """Identify each governing document by path and content hash.

    A protocol "version" that is a hand-written number drifts silently. A
    content hash cannot: if the governing text changes, the recorded version
    changes with it.
    """
    versions: Dict[str, str] = {}
    for key, rel in PROTOCOL_DOCS.items():
        path = Path(repo) / rel
        if not path.is_file():
            raise gov.RunnerRefusal(
                gov.GOVERNANCE_RECORD_UNREADABLE,
                f"the {key} protocol document is missing: {rel}",
            )
        versions[key] = f"{rel}@sha256:{sha256_file(path)[:16]}"
    return versions


def governed_toolchain(path: Path = gov.MODEL_REGISTRY) -> Dict[str, Optional[str]]:
    """The pinned CLI / SDK versions, read from the registry (never guessed)."""
    text = Path(path).read_text(encoding="utf-8")

    def pin(key: str) -> Optional[str]:
        m = re.search(rf"^\s*{key}:\s*\"?([^\"#\s]+)\"?", text, re.MULTILINE)
        return m.group(1) if m else None

    return {
        "claude_code_cli_version": pin("claude_code_cli_version"),
        "claude_agent_sdk_version": pin("claude_agent_sdk_version"),
    }


def derive_run_id(
    *, purpose: str, task_id: str, condition: str, task_sha: str,
    substrate_hash: str, mode: str,
) -> str:
    """A deterministic, collision-resistant run id carrying its own provenance."""
    seed = "|".join([purpose, task_id, condition, task_sha, substrate_hash, mode])
    digest = sha256_bytes(seed.encode("utf-8"))[:12]
    slug = purpose.lower().replace("_", "-")
    return f"{slug}-{task_id.lower()}-{condition.lower()}-{mode}-{digest}"


class ArtifactDirectory:
    """The on-disk home of one run's artifacts, created fail-closed."""

    def __init__(self, root: Path, run_id: str, purpose: gov.RunPurpose) -> None:
        self.purpose = purpose
        self.root = gov.assert_artifact_area_permitted(Path(root), purpose)
        self.run_dir = self.root / run_id
        self.run_id = run_id

    def create(self) -> "ArtifactDirectory":
        self.run_dir.mkdir(parents=True, exist_ok=True)
        return self

    # -- paths ------------------------------------------------------------ #
    @property
    def worktree(self) -> Path:
        return self.run_dir / "worktree"

    @property
    def worktree_post_run(self) -> Path:
        return self.run_dir / "worktree_post_run"

    def path(self, name: str) -> Path:
        return self.run_dir / name

    # -- writing ---------------------------------------------------------- #
    def write_json(self, name: str, payload) -> Path:
        target = self.path(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        return target

    def relative(self, path: Optional[Path]) -> Optional[str]:
        if path is None:
            return None
        return str(Path(path))


def build_run_record(
    *,
    purpose: gov.RunPurpose,
    run_id: str,
    task_id: str,
    task_sha256: str,
    condition: str,
    mode: str,
    state_log: Sequence[Dict[str, object]],
    model: Dict[str, object],
    environment: Dict[str, object],
    worktree: Dict[str, object],
    context_audit: Dict[str, object],
    fresh_launch: Dict[str, object],
    invocation: Dict[str, object],
    model_identity: Dict[str, object],
    post_run_capture: Optional[Dict[str, object]],
    evaluation: Dict[str, object],
    manifest_freeze: Dict[str, object],
    artifacts: Dict[str, str],
    prerequisite_blockers: Sequence[Dict[str, str]],
    outcome: Dict[str, object],
    generated_at: str = "unspecified",
    repo: Path = gov.REPO,
) -> Dict[str, object]:
    """Assemble the run record, deriving the firewall from the purpose itself."""
    firewall = purpose.firewall_flags()
    run_purpose_block: Dict[str, object] = {
        "name": purpose.name,
        "decision_id": purpose.decision_id,
        "confirmatory": purpose.confirmatory,
    }
    run_purpose_block.update(firewall)

    # The flags are re-checked against the purpose even though they were just
    # derived from it: the check is what makes a hand-edited or mutated record
    # fail closed instead of being written.
    gov.assert_firewall_consistent(purpose, run_purpose_block)

    return {
        "schema_version": RECORD_SCHEMA_VERSION,
        "record_kind": "runner_run_record",
        "run_id": run_id,
        "generated_at": generated_at,
        "run_purpose": run_purpose_block,
        "task_id": task_id,
        "task_sha256": task_sha256,
        "condition": condition,
        "mode": mode,
        "state_log": list(state_log),
        "model": model,
        "environment": environment,
        "protocol_versions": protocol_versions(repo),
        "worktree": worktree,
        "context_audit": context_audit,
        "fresh_launch": fresh_launch,
        "invocation": invocation,
        "model_identity": model_identity,
        "post_run_capture": post_run_capture,
        "evaluation": evaluation,
        "manifest_freeze": manifest_freeze,
        "artifacts": dict(artifacts),
        "prerequisite_blockers": [dict(b) for b in prerequisite_blockers],
        "outcome": outcome,
    }


def load_schema(path: Path = SCHEMA_PATH) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_run_record(record: Dict[str, object], schema: Optional[dict] = None) -> None:
    """Validate a record and re-check its firewall; refuse rather than warn."""
    schema = schema if schema is not None else load_schema()
    errors = ca.validate_against_schema(record, schema)
    if errors:
        raise gov.RunnerRefusal(
            gov.PREPARED_MANIFEST_INVALID,
            "the run record does not validate: " + "; ".join(errors[:6]),
        )
    block = record.get("run_purpose")
    if not isinstance(block, dict) or not block.get("name"):
        raise gov.RunnerRefusal(
            gov.RUN_ARTIFACT_PURPOSE_MISSING,
            "the run record carries no run purpose; an unmarked artifact is an "
            "error and is never read as a confirmatory observation",
        )
    purpose = gov.resolve_run_purpose(str(block["name"]))
    gov.assert_firewall_consistent(purpose, block)


def write_run_record(
    directory: ArtifactDirectory, record: Dict[str, object]
) -> Path:
    """Validate then write. A record that does not validate is never written."""
    validate_run_record(record)
    return directory.write_json("run_record.json", record)


def environment_block(
    *, observed_cli_version: Optional[str] = None,
    isolated_environment_verified: bool = False,
    registry: Path = gov.MODEL_REGISTRY,
) -> Dict[str, object]:
    """Environment facts, separating what is *governed* from what is *observed*."""
    pins = governed_toolchain(registry)
    return {
        "os": f"{platform.system()} {platform.release()}",
        "governed_cli_version": pins["claude_code_cli_version"],
        "observed_cli_version": observed_cli_version,
        "governed_agent_sdk_version": pins["claude_agent_sdk_version"],
        "python_version": platform.python_version(),
        "isolated_environment_verified": isolated_environment_verified,
    }
