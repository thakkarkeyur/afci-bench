#!/usr/bin/env python3
"""Stage-0 runtime probes: the real context audit, ``Q8`` and ``Q1``.

Three controls that must be demonstrated against a LIVE runtime before any
counted repetition, and that are deliberately kept out of the run state machine
because none of them is a run:

* **AUDIT** — build the sterile profile the diagnostic will actually launch in,
  then audit *that* profile: the real HOME, the real configuration directory,
  the real environment and the real launch command. Reports local-context
  cleanliness, whether subscription authentication is available, whether the
  runtime re-created account-policy metadata, and whether any of it injects
  experiment-relevant context.
* **Q8** — ask the runtime for an impossible model id and require an explicit
  rejection with no fallback, no substitution and no assistant execution.
* **Q1** — ask for the stable selector and read the resolved exact model id back
  out of the runtime's own ``system.init``/``modelUsage``, so the id that is
  pinned afterwards is one the runtime reported rather than one we assumed.

``Q1`` and ``Q8`` are runtime controls. **Neither is a diagnostic repetition**,
neither is scored, and neither produces a result.

Credential contents are never read, printed, logged or committed. Every captured
stream is redacted before it is written.
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import Dict, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

import context_audit as ca  # noqa: E402
import model_adapter as ma  # noqa: E402
import run_governance as gov  # noqa: E402

#: A model id no registry governs and no provider could resolve.
DEFAULT_INVALID_MODEL_ID = "claude-nonexistent-model-9x7q-not-a-real-id"

#: The smallest prompt that still forces a real assistant turn.
Q1_PROMPT = "Reply with exactly the word: READBACK\n"


def _write(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def prepare(
    *, run_id: str, artifact_root: Path, credential: Path
) -> Dict[str, object]:
    """Build one fresh sterile profile and a disposable workspace for one probe."""
    root = Path(artifact_root) / run_id
    workspace = root / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    sterile = ca.make_sterile_env(
        run_id,
        base_dir=root / "runtime",
        credential_source=Path(credential),
        launchable=True,
    )
    return {"root": root, "workspace": workspace, "sterile": sterile}


def run_probe(
    *,
    executable: str,
    credential: Path,
    artifact_root: Path,
    model_id: str,
    run_id: str,
    prompt: str,
    timeout_seconds: int = 300,
) -> Dict[str, object]:
    """One fresh process, in one fresh sterile profile, for one model id."""
    ctx = prepare(run_id=run_id, artifact_root=artifact_root, credential=credential)
    sterile: ca.SterileEnv = ctx["sterile"]
    root: Path = ctx["root"]
    workspace: Path = ctx["workspace"]

    prompt_path = root / "prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8")

    plan = ma.build_fresh_launch(
        prompt_path=str(prompt_path),
        workspace=str(workspace),
        model_id=model_id,
        sterile_env=sterile.env,
        sterile=True,
        permission_mode=ma.DIAGNOSTIC_PERMISSION_MODE,
        tools=(),  # a runtime control needs no tool; it needs a model id
        session_id=str(uuid.uuid4()),
        require_model=True,
    )

    launcher = ma.RealClaudeCodeLauncher(
        executable=executable,
        cwd=workspace,
        env=plan.environment(),
        evidence_path=root / "runtime_evidence.jsonl",
        governed_root=root,
        config_dir=sterile.config_dir,
        timeout_seconds=timeout_seconds,
    )
    try:
        outcome = launcher(plan)
    except gov.RunnerRefusal as refusal:
        return {
            "run_id": run_id,
            "refused": True,
            "code": refusal.code,
            "detail": refusal.message,
            "argv": list(plan.argv),
        }
    init = ma.first_init_event(outcome.runtime_evidence)
    return {
        "run_id": run_id,
        "refused": False,
        "argv": list(plan.argv),
        "requested_model_id": model_id,
        "exit_status": outcome.exit_status,
        "status": outcome.status,
        "detail": outcome.detail,
        "runtime_evidence_path": outcome.runtime_evidence_path,
        "events": outcome.runtime_evidence,
        "init": init,
        "sterile": sterile,
        "root": root,
        "workspace": workspace,
        "plan": plan,
    }


# --------------------------------------------------------------------------- #
# AUDIT — the real context audit against the real launch environment
# --------------------------------------------------------------------------- #
def probe_audit(
    *, executable: str, credential: Path, artifact_root: Path, model_id: str
) -> Dict[str, object]:
    """Audit the profile the diagnostic will actually launch in, after a live
    authentication has had the chance to re-create whatever it re-creates."""
    live = run_probe(
        executable=executable,
        credential=credential,
        artifact_root=artifact_root,
        model_id=model_id,
        run_id="audit",
        prompt=Q1_PROMPT,
    )
    if live["refused"]:
        return {"probe": "AUDIT", "verdict": "REFUSED", **live}

    sterile: ca.SterileEnv = live["sterile"]
    roots = ca.ScanRoots.discover(
        workspace=Path(live["workspace"]),
        home=sterile.temp_home,
        config_dir=sterile.config_dir,
    )
    result = ca.audit(
        condition=ca.CONDITIONS["C1"],
        roots=roots,
        env=sterile.env,
        launch=live["plan"].launch_command(),
        require_launch=True,
        run_id="audit",
        account_policy_adjudication=True,
        credential_path=sterile.credential_path,
        verify_profile=True,
        runtime_init_event=live["init"],
    )
    payload = result.to_dict()
    init = live["init"] or {}
    payload["stage0"] = {
        "local_context_cleanliness": "CLEAN" if result.is_clean else "NOT CLEAN",
        "subscription_authentication": (
            "available" if live["exit_status"] == 0 else "unavailable"
        ),
        "api_key_used": bool(init.get("apiKeySource") not in (None, "none")),
        "account_policy_metadata": (
            "present" if result.account_policy else "absent"
        ),
        "experiment_relevant_injected_account_context": (
            "detected"
            if any(
                f["injects_experiment_relevant_context"] for f in result.account_policy
            )
            else "not detected"
        ),
        "observed_cli_version": init.get("claude_code_version"),
        "audited_argv": list(live["plan"].argv),
    }
    _write(Path(live["root"]) / "context_audit.json", payload)
    return {"probe": "AUDIT", "verdict": result.verdict, "report": payload}


# --------------------------------------------------------------------------- #
# Q8 — invalid-model-id rejection
# --------------------------------------------------------------------------- #
def probe_q8(
    *, executable: str, credential: Path, artifact_root: Path, invalid_model_id: str
) -> Dict[str, object]:
    if invalid_model_id in gov.governed_model_ids():
        raise gov.RunnerRefusal(
            gov.MODEL_ID_NOT_GOVERNED,
            f"{invalid_model_id!r} is governed; a Q8 probe id must be one the "
            "registry does NOT govern",
        )
    live = run_probe(
        executable=executable,
        credential=credential,
        artifact_root=artifact_root,
        model_id=invalid_model_id,
        run_id="q8",
        prompt=Q1_PROMPT,
    )
    if live["refused"]:
        return {"probe": "Q8", "verdict": "REFUSED_BEFORE_LAUNCH", **live}

    judged = ma.validate_invalid_model_id_rejection(
        invalid_model_id,
        exit_status=live["exit_status"],
        evidence=live["events"],
    )
    payload = {
        "probe": "Q8",
        "invalid_model_id": invalid_model_id,
        "cli_version_reported": (live["init"] or {}).get("claude_code_version"),
        "exit_status": live["exit_status"],
        "judgement": judged.to_dict(),
        "fallback_status": "no fallback requested and none observed",
        "assistant_turns": sum(
            1 for e in (live["events"] or []) if e.get("type") == "assistant"
        ),
        "resolved_model_ids": sorted(
            {m for _, m in ma.extract_resolved_model_ids(live["events"] or [])}
        ),
        "evidence_path": live["runtime_evidence_path"],
    }
    _write(Path(live["root"]) / "q8.json", payload)
    return payload


# --------------------------------------------------------------------------- #
# Q1 — resolved-model-id readback
# --------------------------------------------------------------------------- #
def probe_q1(
    *, executable: str, credential: Path, artifact_root: Path, selector: str
) -> Dict[str, object]:
    live = run_probe(
        executable=executable,
        credential=credential,
        artifact_root=artifact_root,
        model_id=selector,
        run_id="q1",
        prompt=Q1_PROMPT,
    )
    if live["refused"]:
        return {"probe": "Q1", "verdict": "REFUSED_BEFORE_LAUNCH", **live}

    pairs = ma.extract_resolved_model_ids(live["events"] or [])
    distinct = sorted({m for _, m in pairs})
    init = live["init"] or {}
    payload = {
        "probe": "Q1",
        "requested_selector": selector,
        "resolved_model_ids": distinct,
        "resolved_model_id": distinct[0] if len(distinct) == 1 else None,
        "readback_sources": sorted({s for s, _ in pairs}),
        "unambiguous": len(distinct) == 1,
        "cli_version_reported": init.get("claude_code_version"),
        "api_key_source": init.get("apiKeySource"),
        "exit_status": live["exit_status"],
        "evidence_path": live["runtime_evidence_path"],
        "verdict": "PASS" if len(distinct) == 1 and live["exit_status"] == 0 else "FAIL",
    }
    _write(Path(live["root"]) / "q1.json", payload)
    return payload


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--probe", required=True, choices=["audit", "q8", "q1"])
    p.add_argument("--executable", required=True)
    p.add_argument("--credential", required=True)
    p.add_argument("--artifact-root", required=True)
    p.add_argument("--selector", default="sonnet")
    p.add_argument("--invalid-model-id", default=DEFAULT_INVALID_MODEL_ID)
    return p


def main(argv: Optional[list] = None) -> int:
    args = _parser().parse_args(argv)
    common = dict(
        executable=args.executable,
        credential=Path(args.credential),
        artifact_root=Path(args.artifact_root),
    )
    if args.probe == "audit":
        out = probe_audit(model_id=args.selector, **common)
        summary = out.get("report", {}).get("stage0", {})
        print(json.dumps({"verdict": out["verdict"], **summary}, indent=2, sort_keys=True))
        return 0 if out["verdict"] == "CLEAN" else 1
    if args.probe == "q8":
        out = probe_q8(invalid_model_id=args.invalid_model_id, **common)
        print(json.dumps(out, indent=2, sort_keys=True, default=str))
        return 0 if out.get("judgement", {}).get("status") == "Q8_REJECTED" else 1
    out = probe_q1(selector=args.selector, **common)
    print(json.dumps(out, indent=2, sort_keys=True, default=str))
    return 0 if out.get("verdict") == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
