"""Synthetic runtime fixtures for the runner tests. No model is ever invoked.

Everything here is deliberately *evidence*, never a verdict or a weakening. The
synthetic audit builds a real :class:`context_audit.AuditResult` so the runner's
own verdict enforcement still decides what happens; the synthetic launcher edits
a worktree the way a model would, so post-run capture can be exercised against
real bytes; the synthetic runtime evidence is the shape
``MODEL_EXECUTION_CONTROLS`` §3.1 names, so the ``Q1`` readback contract can be
exercised without a live runtime.

None of these is reachable from the production path: the runner's defaults are
the real audit and a launcher that refuses.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import context_audit as ca
import model_adapter as ma


def _result(
    *, verdict: str, reasons: Sequence[str], run_id: str, condition: str,
    generated_at: str, launch: ca.LaunchCommand,
) -> ca.AuditResult:
    return ca.AuditResult(
        run_id=run_id,
        condition=condition,
        generated_at=generated_at,
        temp_home="<synthetic-sterile-home>",
        config_dir="<synthetic-sterile-config>",
        auto_memory_disabled=True,
        autoupdater_disabled=True,
        config_dir_isolated=True,
        home_isolated=True,
        session_restored=False,
        session_status="fresh",
        session_violations=[],
        session_command_supplied=True,
        session_command_source=launch.source,
        session_command_flags=launch.flag_tokens(),
        detected=[],
        approved=[],
        component_status={k: "none" for k in ca.COMPONENT_KINDS},
        verdict=verdict,
        reasons=list(reasons),
    )


def synthetic_clean_audit(**kwargs) -> ca.AuditResult:
    """A CLEAN audit fixture, so the full state machine can be exercised.

    This does not weaken the real audit: the runner still requires the verdict
    to be CLEAN, and the real audit remains the default provider.
    """
    return _result(
        verdict="CLEAN",
        reasons=[],
        run_id=kwargs["run_id"],
        condition=kwargs["condition"],
        generated_at=kwargs["generated_at"],
        launch=kwargs["launch"],
    )


def synthetic_contaminated_audit(**kwargs) -> ca.AuditResult:
    return _result(
        verdict="CONTAMINATED",
        reasons=["unapproved context source [claude_md] present at <synthetic>"],
        run_id=kwargs["run_id"],
        condition=kwargs["condition"],
        generated_at=kwargs["generated_at"],
        launch=kwargs["launch"],
    )


def synthetic_unknown_verdict_audit(**kwargs) -> ca.AuditResult:
    result = synthetic_clean_audit(**kwargs)
    result.verdict = "SOMETHING_ELSE"
    return result


def exploding_audit(**kwargs) -> ca.AuditResult:
    raise OSError("synthetic audit failure")


def missing_audit(**kwargs) -> Optional[ca.AuditResult]:
    return None


# --------------------------------------------------------------------------- #
# Runtime evidence (Q1 / Q8)
# --------------------------------------------------------------------------- #
def runtime_evidence(model_id: Optional[str], *, usage_model: Optional[str] = None) -> List[dict]:
    """Approved-shape runtime evidence: a ``system.init`` event and ``modelUsage``."""
    events: List[dict] = []
    if model_id is not None:
        events.append({"type": "system", "subtype": "init", "model": model_id})
    if usage_model is not None:
        events.append({"type": "result", "modelUsage": {usage_model: {"inputTokens": 1}}})
    return events


def write_runtime_evidence(path: Path, events: Sequence[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8", newline="\n"
    )
    return path


# --------------------------------------------------------------------------- #
# A launcher that edits the worktree the way a model would
# --------------------------------------------------------------------------- #
def workspace_of(plan: ma.LaunchPlan) -> Path:
    argv = list(plan.argv)
    return Path(argv[argv.index("--add-dir") + 1])


def editing_launcher(
    *, edits: Dict[str, Optional[str]], evidence: Sequence[dict], exit_status: int = 0
):
    """Return a launcher that applies ``edits`` and reports ``evidence``.

    ``edits`` maps a worktree-relative path to its new text, or to ``None`` to
    delete it. No process is started and no model is contacted.
    """

    def launcher(plan: ma.LaunchPlan) -> ma.ModelInvocationOutcome:
        workspace = workspace_of(plan)
        for rel, text in edits.items():
            target = workspace / rel
            if text is None:
                if target.is_file():
                    target.unlink()
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8", newline="\n")
        return ma.ModelInvocationOutcome(
            invoked=True,
            status="SYNTHETIC_COMPLETED",
            exit_status=exit_status,
            runtime_evidence=list(evidence),
            detail="synthetic launcher; no model was contacted",
        )

    return launcher
