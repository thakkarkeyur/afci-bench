#!/usr/bin/env python3
"""The study-v2 execution runner: a fail-closed state machine, and its CLI.

What this is
------------
The orchestrator the repository did not have. It prepares the governed
model-visible worktree, enforces the worktree policy at runner time, audits
context isolation, builds a genuinely fresh launch command, records the model
identity contract, captures the model-modified worktree, hands the capture to
the evaluation boundary, and writes a run record that carries the diagnostic
firewall. Every existing harness module keeps its job; this one sequences them.

What this is not
----------------
It is **not** a model invoker. ``--dry-run`` executes every safe pre-launch
step and never starts a model process. Real invocation is implemented as an
adapter that refuses before any process could be created while
``MODEL_REGISTRY.yml`` records ``primary_model: null`` — which it does. It
selects no model, chooses no sample size, validates no hidden acceptance,
freezes nothing and passes no gate. It produces no result: the run-record schema
pins ``is_result: false`` and ``scored: false``.

The state machine
-----------------
::

    PRECHECK
      -> PREPARE_WORKTREE
      -> CONTEXT_AUDIT
      -> BUILD_FRESH_LAUNCH
      -> MODEL_INVOCATION
      -> MODEL_IDENTITY_VALIDATION
      -> CAPTURE_WORKTREE
      -> POST_RUN_EVALUATION
      -> RECORD_ARTIFACTS
      -> COMPLETE

Transitions are total and ordered: a state may be entered only from its
immediate predecessor, only while no refusal has occurred, and only when that
predecessor recorded an explicit ``PASS`` or an explicit, coded ``SKIPPED``.
A failed prerequisite therefore cannot slip into a later state — the machine
refuses the transition itself, not merely the work inside it.

``CONTEXT_AUDIT`` runs before ``BUILD_FRESH_LAUNCH`` as governed, and the launch
plan the audit certifies is proved byte-identical to the launch that would
actually be used: the plan is derived in ``PRECHECK``, certified in
``CONTEXT_AUDIT``, and frozen in ``BUILD_FRESH_LAUNCH`` under an equality check
(``LAUNCH_COMMAND_DIVERGED_FROM_AUDIT``). Auditing one command and running
another would make the audit decorative.

Usage
-----
::

    python experiments/v2/harness/run_v2.py --check-readiness \\
        --task PT08 --condition C1 --run-purpose PT08_DIFFICULTY_DIAGNOSTIC

    python experiments/v2/harness/run_v2.py --dry-run \\
        --task PT08 --condition C1 --run-purpose PT08_DIFFICULTY_DIAGNOSTIC

No model is invoked and no benchmark task is executed.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

import context_audit as ca  # noqa: E402
import model_adapter as ma  # noqa: E402
import prepare_model_worktree as pmw  # noqa: E402
import run_artifacts as art  # noqa: E402
import run_evaluation as ev  # noqa: E402
import run_governance as gov  # noqa: E402
import run_worktree as wt  # noqa: E402

STATE_TRANSITION_REFUSED = "STATE_TRANSITION_REFUSED"

#: The ordered states. The order is the contract; there is no other path.
STATES: Sequence[str] = (
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


class StateMachine:
    """An ordered, fail-closed orchestration with an auditable trace."""

    def __init__(self, states: Sequence[str] = STATES) -> None:
        self.states = tuple(states)
        self.log: List[Dict[str, object]] = []
        self._index = -1
        self._settled = True  # no state is open
        self.refused = False

    # -- transitions ------------------------------------------------------ #
    def enter(self, state: str) -> None:
        if self.refused:
            raise gov.RunnerRefusal(
                STATE_TRANSITION_REFUSED,
                f"cannot enter {state}: the run already refused and a refusal is "
                "terminal",
            )
        if not self._settled:
            raise gov.RunnerRefusal(
                STATE_TRANSITION_REFUSED,
                f"cannot enter {state}: {self.states[self._index]} recorded no "
                "outcome; an unresolved state never advances",
            )
        expected = (
            self.states[self._index + 1]
            if self._index + 1 < len(self.states)
            else None
        )
        if state != expected:
            raise gov.RunnerRefusal(
                STATE_TRANSITION_REFUSED,
                f"cannot enter {state}: the only permitted next state is "
                f"{expected!r}",
            )
        self._index += 1
        self._settled = False
        self.log.append({"state": state, "result": "ENTERED", "code": None, "detail": ""})

    def _settle(self, result: str, code: Optional[str], detail: str) -> None:
        self.log[-1] = {
            "state": self.states[self._index],
            "result": result,
            "code": code,
            "detail": detail,
        }
        self._settled = True

    def passed(self, detail: str = "") -> None:
        self._settle("PASS", None, detail)

    def skipped(self, code: str, detail: str) -> None:
        """An explicitly coded non-execution. Never a silent pass-through."""
        self._settle("SKIPPED", code, detail)

    def refuse(self, code: str, detail: str) -> None:
        if not self._settled:
            self._settle("REFUSED", code, detail)
        else:  # pragma: no cover - refusal outside an open state
            self.log.append(
                {"state": "REFUSED", "result": "REFUSED", "code": code, "detail": detail}
            )
        self.refused = True

    # -- introspection ---------------------------------------------------- #
    @property
    def current(self) -> Optional[str]:
        return self.states[self._index] if self._index >= 0 else None

    @property
    def completed(self) -> bool:
        return (
            not self.refused
            and self._settled
            and self._index == len(self.states) - 1
        )

    def reached(self, state: str) -> bool:
        return any(entry["state"] == state for entry in self.log)


# --------------------------------------------------------------------------- #
# Request / result
# --------------------------------------------------------------------------- #
@dataclass
class RunRequest:
    task_id: str
    condition: str
    run_purpose: Optional[str]
    mode: str = "dry-run"
    artifact_root: Optional[Path] = None
    model_id: Optional[str] = None
    effort: Optional[str] = None
    session_id: Optional[str] = None
    previous_session_ids: Sequence[str] = ()
    extra_launch_args: Sequence[str] = ()
    generated_at: str = "unspecified"
    repo: Path = gov.REPO
    private_root: Optional[Path] = None
    scored: bool = False
    isolated_environment_attested: bool = False
    audit_provider: Optional[Callable[..., ca.AuditResult]] = None
    process_launcher: Optional[Callable[[ma.LaunchPlan], ma.ModelInvocationOutcome]] = None
    keep_worktree: bool = True


@dataclass
class RunResult:
    machine: StateMachine
    record: Optional[Dict[str, object]] = None
    record_path: Optional[Path] = None
    readiness: Optional[gov.ReadinessReport] = None
    refusal_code: Optional[str] = None
    refusal_detail: str = ""
    run_dir: Optional[Path] = None

    @property
    def ok(self) -> bool:
        return self.machine.completed and self.refusal_code is None


def real_context_audit(
    *, condition: str, run_id: str, workspace: Path, generated_at: str,
    launch: ca.LaunchCommand, previous_session_ids: Sequence[str],
    base_tmp: Optional[Path] = None,
) -> ca.AuditResult:
    """The real, unweakened audit. This is the default and only production path."""
    sterile = ca.make_sterile_env(run_id, base_dir=base_tmp)
    roots = ca.ScanRoots.discover(
        workspace=Path(workspace),
        home=sterile.temp_home,
        config_dir=sterile.config_dir,
    )
    return ca.audit(
        condition=ca.CONDITIONS[condition],
        roots=roots,
        env=sterile.env,
        launch=launch,
        require_launch=True,
        previous_session_ids=previous_session_ids,
        run_id=run_id,
        generated_at=generated_at,
    )


# --------------------------------------------------------------------------- #
# The runner
# --------------------------------------------------------------------------- #
def run(request: RunRequest) -> RunResult:
    """Execute the orchestration for one run, fail-closed at every transition."""
    machine = StateMachine()
    result = RunResult(machine=machine)
    directory: Optional[art.ArtifactDirectory] = None

    # Values populated as states pass; every one starts as a fail-closed default.
    purpose: Optional[gov.RunPurpose] = None
    expected_sha = ""
    substrate: Dict[str, object] = {}
    prepared: Optional[pmw.PreparationResult] = None
    enforcement: Optional[wt.WorktreeEnforcement] = None
    plan: Optional[ma.LaunchPlan] = None
    audited_argv: Optional[Sequence[str]] = None
    audit_block: Dict[str, object] = {
        "verdict": "UNKNOWN",
        "report_path": None,
        "report_sha256": None,
        "reason_count": 0,
        "reasons_sample": [],
    }
    invocation = ma.ModelInvocationOutcome(
        invoked=False, status="NOT_REACHED", detail="the run refused before invocation"
    )
    identity = ma.readback_not_performed(request.model_id)
    capture: Optional[wt.WorktreeCapture] = None
    evaluation: Optional[ev.EvaluationPlan] = None
    repo_state_before: Dict[str, str] = {}
    prompt_path: Optional[Path] = None

    try:
        # ---------------- PRECHECK -------------------------------------- #
        machine.enter("PRECHECK")
        purpose = gov.resolve_run_purpose(request.run_purpose)
        gov.assert_task_and_condition_permitted(
            purpose, request.task_id, request.condition
        )
        gov.assert_architecture_delivery_none(request.condition)

        expected_sha = gov.expected_task_sha256(request.task_id)
        body = gov.public_task_path(request.task_id)
        actual_sha = pmw.sha256_file(body)
        if actual_sha != expected_sha:
            raise gov.RunnerRefusal(
                gov.TASK_SHA_MISMATCH,
                f"{body} hashes {actual_sha}; the approved index pins {expected_sha}",
            )
        substrate = gov.assert_substrate_identity(request.repo)

        if request.mode == "real":
            # A real run fails BEFORE execution, not after: the earliest safe
            # failure point is the only defensible one for a paid run.
            ev.assert_scoring_prerequisites(request.task_id)
            if not request.isolated_environment_attested:
                raise gov.RunnerRefusal(
                    gov.ISOLATED_ENVIRONMENT_NOT_VERIFIED,
                    "a counted run requires the governed isolated container/VM and "
                    "dedicated identity (TD-B19); no attestation was supplied and "
                    "the runner does not assume one",
                )
        if request.scored:
            ev.assert_scoring_prerequisites(request.task_id)

        run_id = art.derive_run_id(
            purpose=purpose.name,
            task_id=request.task_id,
            condition=request.condition,
            task_sha=expected_sha,
            substrate_hash=str(substrate["content_hash"]),
            mode=request.mode,
        )
        root = request.artifact_root or gov.default_artifact_root()
        directory = art.ArtifactDirectory(Path(root), run_id, purpose).create()
        result.run_dir = directory.run_dir

        repo_state_before = gov.repository_state(request.repo)

        # The prompt is delivered out of band and is never written into the
        # model-visible worktree (CONDITION_MATRIX.csv: task_delivery=prompt).
        prompt_path = directory.path("prompts/task_prompt.md")
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_bytes(body.read_bytes())

        readiness = gov.check_readiness(
            request.task_id,
            request.condition,
            purpose.name,
            repo=request.repo,
            private_root=request.private_root,
        )
        result.readiness = readiness
        directory.write_json("readiness.json", readiness.to_dict())

        machine.passed(
            f"{purpose.decision_id} authorises {request.task_id}/{request.condition}; "
            f"task hash verified; substrate {substrate['commit'][:12]} hashes "
            f"{str(substrate['content_hash'])[:16]}...; artifacts under "
            f"{directory.run_dir}"
        )

        # ---------------- PREPARE_WORKTREE ------------------------------ #
        machine.enter("PREPARE_WORKTREE")
        if directory.worktree.exists():
            shutil.rmtree(directory.worktree)
        prepared = pmw.prepare_model_worktree(
            pmw.PreparationRequest(
                condition=request.condition,
                source_root=request.repo,
                dest_root=directory.worktree,
                task_path=body,
                task_id=request.task_id,
            )
        )
        directory.write_json("prepared_manifest.json", prepared.manifest)
        enforcement = wt.enforce_prepared_worktree(
            root=directory.worktree,
            manifest=prepared.manifest,
            condition=request.condition,
            expected_task_sha=expected_sha,
            repo=request.repo,
        )
        machine.passed(
            f"TD-B22 runner-time enforcement passed {len(enforcement.checks)} checks: "
            f"{enforcement.entry_count} allowlisted files, architecture_delivery="
            f"{enforcement.architecture_delivery}, content_hash "
            f"{enforcement.content_hash[:16]}..."
        )

        # ---------------- CONTEXT_AUDIT --------------------------------- #
        machine.enter("CONTEXT_AUDIT")
        plan = ma.build_fresh_launch(
            prompt_path=str(prompt_path),
            workspace=str(directory.worktree),
            model_id=request.model_id,
            effort=request.effort,
            session_id=request.session_id,
            previous_session_ids=request.previous_session_ids,
            extra=request.extra_launch_args,
            require_model=(request.mode == "real"),
        )
        audit_provider = request.audit_provider or real_context_audit
        try:
            audit_result = audit_provider(
                condition=request.condition,
                run_id=run_id,
                workspace=directory.worktree,
                generated_at=request.generated_at,
                launch=plan.launch_command(),
                previous_session_ids=tuple(request.previous_session_ids),
            )
        except gov.RunnerRefusal:
            raise
        except Exception as exc:  # fail closed on any audit failure
            raise gov.RunnerRefusal(
                gov.CONTEXT_AUDIT_ERROR,
                f"the context audit could not be completed: {exc}",
            ) from exc

        if audit_result is None:
            raise gov.RunnerRefusal(
                gov.CONTEXT_AUDIT_MISSING, "the context audit produced no result"
            )
        audit_payload = audit_result.to_dict()
        report_path = directory.write_json("context_audit.json", audit_payload)
        verdict = str(
            audit_payload.get("contamination", {}).get("verdict", "UNKNOWN")
        ).upper()
        reasons = list(audit_payload.get("contamination", {}).get("reasons", []))
        audit_block = {
            "verdict": verdict if verdict in {"CLEAN", "CONTAMINATED"} else "UNKNOWN",
            "report_path": str(report_path),
            "report_sha256": art.sha256_file(report_path),
            "reason_count": len(reasons),
            "reasons_sample": [str(r) for r in reasons[:8]],
        }
        audited_argv = tuple(plan.argv)

        if verdict != "CLEAN":
            code = (
                gov.CONTEXT_AUDIT_CONTAMINATED
                if verdict == "CONTAMINATED"
                else gov.CONTEXT_AUDIT_UNKNOWN
            )
            raise gov.RunnerRefusal(
                code,
                f"context-isolation verdict is {verdict} with {len(reasons)} "
                f"reason(s); model invocation is refused. First reasons: "
                + "; ".join(str(r) for r in reasons[:3]),
            )
        machine.passed(
            f"context audit CLEAN; report {report_path.name} "
            f"({audit_block['report_sha256'][:16]}...)"
        )

        # ---------------- BUILD_FRESH_LAUNCH ---------------------------- #
        machine.enter("BUILD_FRESH_LAUNCH")
        final_plan = ma.build_fresh_launch(
            prompt_path=str(prompt_path),
            workspace=str(directory.worktree),
            model_id=request.model_id,
            effort=request.effort,
            session_id=request.session_id,
            previous_session_ids=request.previous_session_ids,
            extra=request.extra_launch_args,
            require_model=(request.mode == "real"),
        )
        if tuple(final_plan.argv) != tuple(audited_argv or ()):
            raise gov.RunnerRefusal(
                gov.LAUNCH_COMMAND_DIVERGED_FROM_AUDIT,
                "the launch the audit certified and the launch about to be used "
                "differ; a certified audit must describe the actual command",
            )
        plan = final_plan
        directory.write_json("launch_manifest.json", plan.launch_manifest())
        machine.passed(
            f"fresh launch built and re-verified: {plan.session_handling}; "
            f"model status {plan.model_status}; executable={plan.executable}"
        )

        # ---------------- MODEL_INVOCATION ------------------------------ #
        machine.enter("MODEL_INVOCATION")
        adapter = ma.ModelInvocationAdapter(
            mode=request.mode,
            process_launcher=request.process_launcher or ma._refusing_launcher,
            registry_primary_model=gov.primary_model(),
            governed_ids=tuple(gov.governed_model_ids()),
        )
        invocation = adapter.invoke(plan)
        if invocation.invoked:
            machine.passed(f"model process completed: {invocation.status}")
        else:
            machine.skipped(
                "DRY_RUN_NO_INVOKE",
                "no model process was started; this is a dry run and no paid "
                "execution occurred",
            )

        # ---------------- MODEL_IDENTITY_VALIDATION --------------------- #
        machine.enter("MODEL_IDENTITY_VALIDATION")
        if not invocation.invoked:
            identity = ma.readback_not_performed(request.model_id)
            machine.skipped(
                identity.status,
                "no runtime evidence exists, so no readback is validated and none "
                "is fabricated (Q1 remains unvalidated in live runtime)",
            )
        else:
            evidence = invocation.runtime_evidence
            if evidence is None and invocation.runtime_evidence_path:
                evidence = ma.load_runtime_evidence(invocation.runtime_evidence_path)
            identity = ma.validate_model_identity(
                request.model_id, evidence, strict=True
            )
            machine.passed(f"resolved model id {identity.resolved!r} matches request")

        # ---------------- CAPTURE_WORKTREE ------------------------------ #
        machine.enter("CAPTURE_WORKTREE")
        gov.assert_canonical_repository_unchanged(repo_state_before, request.repo)
        if not invocation.invoked:
            machine.skipped(
                "DRY_RUN_NO_MODEL_EDITS",
                "no model process ran, so there is no model-modified worktree to "
                "capture; the canonical repository is verified unchanged",
            )
        else:
            capture = wt.capture_post_run_worktree(
                worktree=directory.worktree,
                capture_root=directory.worktree_post_run,
                prepared_manifest=prepared.manifest,
                repo=request.repo,
                repository_state_before=repo_state_before,
            )
            machine.passed(
                f"captured {capture.entry_count} files; "
                f"{len(capture.added)} added / {len(capture.modified)} modified / "
                f"{len(capture.deleted)} deleted"
            )

        # ---------------- POST_RUN_EVALUATION --------------------------- #
        machine.enter("POST_RUN_EVALUATION")
        evaluation = ev.build_evaluation_plan(
            request.task_id,
            snapshot=Path(capture.capture_root) if capture else None,
            coding_worktree=directory.worktree,
            repo=request.repo,
        )
        if request.scored or request.mode == "real":
            ev.assert_scoring_prerequisites(request.task_id)
            machine.passed("evaluation channels ready")
        else:
            machine.skipped(
                "DRY_RUN_NO_SCORING",
                "nothing is scored in a dry run; the evaluation boundary is "
                "reported with its blockers: "
                + ", ".join(str(c.code) for c in evaluation.blockers),
            )

        # ---------------- RECORD_ARTIFACTS ------------------------------ #
        machine.enter("RECORD_ARTIFACTS")
        record = _build_record(
            request=request,
            purpose=purpose,
            run_id=run_id,
            expected_sha=expected_sha,
            machine=machine,
            directory=directory,
            enforcement=enforcement,
            audit_block=audit_block,
            plan=plan,
            invocation=invocation,
            identity=identity,
            capture=capture,
            evaluation=evaluation,
            readiness=result.readiness,
            outcome={
                "status": "DRY_RUN_COMPLETE" if request.mode == "dry-run" else "COMPLETE",
                "code": None,
                "detail": (
                    "every safe pre-launch state was executed and enforced; no "
                    "model was invoked"
                    if request.mode == "dry-run"
                    else "the run completed"
                ),
                "is_result": False,
                "scored": False,
            },
        )
        result.record_path = art.write_run_record(directory, record)
        result.record = record
        machine.passed(f"run record written to {result.record_path}")

        # ---------------- COMPLETE -------------------------------------- #
        machine.enter("COMPLETE")
        machine.passed("orchestration complete; nothing was scored and no gate moved")

    except gov.RunnerRefusal as refusal:
        machine.refuse(refusal.code, refusal.message)
        result.refusal_code = refusal.code
        result.refusal_detail = refusal.message
        if directory is not None and purpose is not None:
            try:
                record = _build_record(
                    request=request,
                    purpose=purpose,
                    run_id=directory.run_id,
                    expected_sha=expected_sha,
                    machine=machine,
                    directory=directory,
                    enforcement=enforcement,
                    audit_block=audit_block,
                    plan=plan,
                    invocation=invocation,
                    identity=identity,
                    capture=capture,
                    evaluation=evaluation,
                    readiness=result.readiness,
                    outcome={
                        "status": (
                            "DRY_RUN_REFUSED"
                            if request.mode == "dry-run"
                            else "REFUSED"
                        ),
                        "code": refusal.code,
                        "detail": refusal.message,
                        "is_result": False,
                        "scored": False,
                    },
                )
                result.record_path = art.write_run_record(directory, record)
                result.record = record
            except gov.RunnerRefusal:  # pragma: no cover - record of a record
                pass
    finally:
        if directory is not None and not request.keep_worktree:
            shutil.rmtree(directory.worktree, ignore_errors=True)

    return result


def _build_record(
    *,
    request: RunRequest,
    purpose: gov.RunPurpose,
    run_id: str,
    expected_sha: str,
    machine: StateMachine,
    directory: art.ArtifactDirectory,
    enforcement: Optional[wt.WorktreeEnforcement],
    audit_block: Dict[str, object],
    plan: Optional[ma.LaunchPlan],
    invocation: ma.ModelInvocationOutcome,
    identity: ma.ModelIdentityValidation,
    capture: Optional[wt.WorktreeCapture],
    evaluation: Optional[ev.EvaluationPlan],
    readiness: Optional[gov.ReadinessReport],
    outcome: Dict[str, object],
) -> Dict[str, object]:
    blockers: List[Dict[str, str]] = []
    if readiness is not None:
        blockers = [
            {"code": str(p.code), "detail": p.detail} for p in readiness.blocked
        ]

    launch_block: Dict[str, object] = {
        "argv": list(plan.argv) if plan else [],
        "env_keys": sorted(plan.environment()) if plan else [],
        "executable": bool(plan.executable) if plan else False,
        "requested_model_id": plan.model_id if plan else request.model_id,
        "model_status": plan.model_status if plan else gov.MODEL_SELECTION_REQUIRED,
        "effort_input": plan.effort_input if plan else request.effort,
        "session_handling": plan.session_handling if plan else "not built",
        "manifest_path": (
            str(directory.path("launch_manifest.json"))
            if directory.path("launch_manifest.json").exists()
            else None
        ),
    }

    invocation_block = invocation.to_dict()
    invocation_block.update(
        {"started_at": None, "ended_at": None, "wall_clock_seconds": None}
    )

    artifacts: Dict[str, str] = {}
    for name in (
        "readiness.json",
        "prepared_manifest.json",
        "context_audit.json",
        "launch_manifest.json",
        "prompts/task_prompt.md",
    ):
        path = directory.path(name)
        if path.is_file():
            artifacts[name] = art.sha256_file(path)

    return art.build_run_record(
        purpose=purpose,
        run_id=run_id,
        task_id=request.task_id,
        task_sha256=expected_sha,
        condition=request.condition,
        mode=request.mode,
        state_log=machine.log,
        model={
            "requested_model_id": request.model_id,
            "resolved_model_id": identity.resolved,
            "effort_input": request.effort,
            "selection_status": (
                plan.model_status if plan else gov.MODEL_SELECTION_REQUIRED
            ),
        },
        environment=art.environment_block(
            isolated_environment_verified=request.isolated_environment_attested
        ),
        worktree={
            "enforcement": enforcement.to_dict() if enforcement else {},
            "prepared_root": str(directory.worktree),
            "prepared_manifest_path": str(directory.path("prepared_manifest.json")),
            "content_hash": enforcement.content_hash if enforcement else "",
        },
        context_audit=audit_block,
        fresh_launch=launch_block,
        invocation=invocation_block,
        model_identity=identity.to_dict(),
        post_run_capture=capture.to_dict() if capture else None,
        evaluation=evaluation.to_dict() if evaluation else {},
        manifest_freeze=ev.freeze_status_report(request.task_id),
        artifacts=artifacts,
        prerequisite_blockers=blockers,
        outcome=outcome,
        generated_at=request.generated_at,
        repo=request.repo,
    )


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Study-v2 governed execution runner (no model is invoked).",
    )
    p.add_argument("--task", required=True, help="Public task id, e.g. PT08.")
    p.add_argument("--condition", required=True, help="Condition, e.g. C1.")
    p.add_argument(
        "--run-purpose",
        default=None,
        help="Governed run purpose. REQUIRED: an unmarked run fails closed.",
    )
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Execute every safe pre-launch state and never start a model.",
    )
    mode.add_argument(
        "--check-readiness",
        action="store_true",
        help="Report the prerequisite status for the authorised run and exit.",
    )
    mode.add_argument(
        "--real-run",
        action="store_true",
        help=(
            "Attempt a real invocation. Fails closed while primary_model is null "
            "(TD-B03) and while the hidden acceptance and manifest freeze "
            "prerequisites are outstanding."
        ),
    )
    p.add_argument("--model", default=None, help="Exact governed model id (real runs).")
    p.add_argument("--effort", default=None, help="--effort value, recorded as input.")
    p.add_argument("--artifact-root", default=None, help="Artifact root (scratch/tmp).")
    p.add_argument("--generated-at", default="unspecified", help="Caller-supplied stamp.")
    p.add_argument("--private-root", default=None, help="Private evaluator repo (READ ONLY).")
    p.add_argument("--session-id", default=None, help="A fresh, previously unused id.")
    p.add_argument(
        "--previous-session-id", action="append", default=[],
        help="A session id to reject on reuse (repeatable).",
    )
    p.add_argument(
        "--scored", action="store_true",
        help="Assert the run is to be scored; refuses while prerequisites are open.",
    )
    p.add_argument(
        "--isolated-environment-attested", action="store_true",
        help="Attest the governed isolated container/identity (TD-B19).",
    )
    p.add_argument("--json", action="store_true", help="Emit machine-readable output.")
    return p


def _print_readiness(report: gov.ReadinessReport) -> None:
    print(f"readiness — {report.purpose} / {report.task_id} / {report.condition}")
    for item in report.prerequisites:
        mark = "PASS   " if item.status == gov.PASS else "BLOCKED"
        print(f"  [{mark}] {item.item}" + (f"  <{item.code}>" if item.code else ""))
        print(f"           {item.detail}")
    print(
        f"  => run_eligible={report.run_eligible} "
        f"({len(report.passed)} pass, {len(report.blocked)} blocked)"
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        if args.check_readiness:
            report = gov.check_readiness(
                args.task,
                args.condition,
                args.run_purpose,
                private_root=Path(args.private_root) if args.private_root else None,
            )
            if args.json:
                print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
            else:
                _print_readiness(report)
            return 0 if report.run_eligible else 1

        request = RunRequest(
            task_id=args.task,
            condition=args.condition,
            run_purpose=args.run_purpose,
            mode="dry-run" if args.dry_run else "real",
            artifact_root=Path(args.artifact_root) if args.artifact_root else None,
            model_id=args.model,
            effort=args.effort,
            session_id=args.session_id,
            previous_session_ids=tuple(args.previous_session_id),
            generated_at=args.generated_at,
            private_root=Path(args.private_root) if args.private_root else None,
            scored=args.scored,
            isolated_environment_attested=args.isolated_environment_attested,
        )
        outcome = run(request)
    except gov.RunnerRefusal as refusal:
        print(f"REFUSED {refusal.code}: {refusal.message}", file=sys.stderr)
        return 1

    if args.json:
        print(
            json.dumps(
                {
                    "states": outcome.machine.log,
                    "refusal_code": outcome.refusal_code,
                    "record_path": str(outcome.record_path) if outcome.record_path else None,
                    "run_dir": str(outcome.run_dir) if outcome.run_dir else None,
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(f"run — {args.task} / {args.condition} / {args.run_purpose} [{request.mode}]")
        for entry in outcome.machine.log:
            code = f"  <{entry['code']}>" if entry.get("code") else ""
            print(f"  {entry['result']:<8} {entry['state']}{code}")
            if entry.get("detail"):
                print(f"           {entry['detail']}")
        if outcome.run_dir:
            print(f"  artifacts: {outcome.run_dir}")
        if outcome.refusal_code:
            print(f"  => REFUSED {outcome.refusal_code}", file=sys.stderr)
        else:
            print("  => dry run complete; no model was invoked and nothing was scored")

    return 0 if outcome.ok else 1


if __name__ == "__main__":
    sys.exit(main())
