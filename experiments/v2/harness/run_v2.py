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
It **selects no model**. ``MODEL_REGISTRY.yml`` still records
``primary_model: null`` and ``TD-B03`` is still open, so a real invocation is
reachable only for a run purpose the registry pins a model for, by name, and is
refused before any process could be created for every other. It chooses no
sample size, validates no hidden acceptance, freezes nothing and passes no gate.
It produces no result: the run-record schema pins ``is_result: false`` and
``scored: false`` and refuses a record that says otherwise.

``--dry-run`` executes every safe pre-launch step and never starts a model
process.

**It does invoke a model**, for a purpose that authorises one. That sentence
used to read "it is not a model invoker", which was true when it was written and
stopped being true when ``SL-PT08-05`` pinned a model for the PT08 diagnostic
and its three repetitions ran through this module. It is corrected rather than
softened: a reader deciding whether this file can spend money should not have to
work that out from somewhere else.

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

The reset, and why it does not add a state
------------------------------------------
A purpose may declare a ``reset_state`` (``SL-V2-EFF-01`` is the first that
does). ``NON_RESET`` runs the machine above unchanged, one process. ``RESET``
runs :mod:`reset_orchestration` from inside ``MODEL_INVOCATION``: phase A, the
handoff, phase B.

The states are deliberately NOT extended for it. The machine's order is a
contract that existing records were written against, and a reset is not a
different orchestration — it is one invocation performed in two halves. So the
two-phase structure, including phase B's own mandatory context audit, lives in
the module that owns it and is recorded in the run record's ``reset`` block,
where a reader finds both phases side by side rather than interleaved into a
state log that would no longer describe either.

``reset_state`` is never defaulted. A purpose that declares one and is handed
none is refused, because the two arms are the experimental factor and picking
one by omission would assign half the design by accident.

Usage
-----
::

    python experiments/v2/harness/run_v2.py --check-readiness \\
        --task PT08 --condition C1 --run-purpose PT08_DIFFICULTY_DIAGNOSTIC

    python experiments/v2/harness/run_v2.py --dry-run \\
        --task PT08 --condition C1 --run-purpose PT08_DIFFICULTY_DIAGNOSTIC

A reset-aware purpose must declare its arm::

    python experiments/v2/harness/run_v2.py --dry-run \\
        --task PT01 --condition C4 --run-purpose AFCI_EFFICIENCY_PILOT \\
        --reset-state RESET --repetition 1

Neither of those starts a model process.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

import condition_prompt as cp  # noqa: E402
import context_audit as ca  # noqa: E402
import efficiency_metrics as em  # noqa: E402
import model_adapter as ma  # noqa: E402
import prepare_model_worktree as pmw  # noqa: E402
import reset_budget as rb  # noqa: E402
import reset_orchestration as ro  # noqa: E402
import run_artifacts as art  # noqa: E402
import run_evaluation as ev  # noqa: E402
import run_governance as gov  # noqa: E402
import run_worktree as wt  # noqa: E402
import stream_launcher as sl  # noqa: E402

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
    #: SL-RUNID-01. The 1-based repetition index. ``None`` means "not declared" and
    #: resolves to the governed default of 1; the record says which it was. Two
    #: repetitions of one (purpose, task, condition, task sha, substrate, mode)
    #: now derive DIFFERENT run ids, so a multi-repetition run no longer depends
    #: on the caller handing each repetition its own --artifact-root.
    repetition: Optional[int] = None
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
    #: SL-PT08-04 sterile-execution inputs. All default to the pre-existing
    #: behaviour, so a caller that supplies none of them gets exactly the run it
    #: got before this package.
    sterile_base: Optional[Path] = None
    credential_source: Optional[Path] = None
    launcher_executable: Optional[str] = None
    permission_mode: Optional[str] = None
    tools: Sequence[str] = ()
    launch_timeout_seconds: int = 1800
    #: SL-V2-EFF-01 / SL-V2-EFF-RESET-01 inputs. ``reset_state=None`` means the
    #: purpose declares no reset state, which is every purpose that existed
    #: before this package: those runs are unchanged and carry no reset block.
    reset_state: Optional[str] = None
    #: The PERMISSION allowlist, distinct from ``tools``. Empty by default, so a
    #: caller that does not freeze one gets exactly the permissions the earlier
    #: diagnostics ran under.
    allowed_tools: Sequence[str] = ()
    #: The agentic-turn ceiling. ``None`` means no purpose freezes one, and the
    #: launch carries no ``--max-turns`` at all.
    max_turns: Optional[int] = None


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
    sterile: Optional[ca.SterileEnv] = None,
    runtime_init_event: Optional[dict] = None,
) -> ca.AuditResult:
    """The real, unweakened audit. This is the default and only production path.

    ``sterile`` is the environment the run will ACTUALLY launch in. Passing it is
    what makes the audit an observation of the real launch rather than of a
    look-alike built for the occasion: the same HOME, the same configuration
    directory and the same variables are scanned, judged and then used.
    """
    sterile = sterile or ca.make_sterile_env(run_id, base_dir=base_tmp)
    roots = ca.ScanRoots.discover(
        workspace=Path(workspace),
        home=sterile.temp_home,
        config_dir=sterile.config_dir,
    )
    diagnostic = sterile.credential_path is not None
    return ca.audit(
        condition=ca.CONDITIONS[condition],
        roots=roots,
        env=sterile.env,
        launch=launch,
        require_launch=True,
        previous_session_ids=previous_session_ids,
        run_id=run_id,
        generated_at=generated_at,
        account_policy_adjudication=diagnostic,
        credential_path=sterile.credential_path,
        verify_profile=diagnostic,
        runtime_init_event=runtime_init_event,
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
    sterile: Optional[ca.SterileEnv] = None
    reset_block: Optional[Dict[str, object]] = None
    efficiency_block: Optional[Dict[str, object]] = None
    reset_outcome: Optional[ro.ResetOutcome] = None
    run_started = time.monotonic()

    def build_plan() -> ma.LaunchPlan:
        """The launch, built from one place so the audited and used argv cannot
        drift apart through a forgotten argument."""
        return ma.build_fresh_launch(
            prompt_path=str(prompt_path),
            workspace=str(directory.worktree),
            model_id=request.model_id,
            effort=request.effort,
            session_id=request.session_id,
            previous_session_ids=request.previous_session_ids,
            sterile_env=sterile.env if sterile else None,
            extra=request.extra_launch_args,
            require_model=(request.mode == "real"),
            sterile=request.credential_source is not None,
            permission_mode=request.permission_mode,
            tools=request.tools,
            allowed_tools=request.allowed_tools,
            max_turns=request.max_turns,
        )

    try:
        # ---------------- PRECHECK -------------------------------------- #
        machine.enter("PRECHECK")
        purpose = gov.resolve_run_purpose(request.run_purpose)
        gov.assert_task_and_condition_permitted(
            purpose, request.task_id, request.condition
        )
        # Replaced, not relaxed. The predecessor asserted "delivery == none" for
        # every run, which was right while every authorised purpose was a
        # baseline-only diagnostic. A C4 run under a C1-only authority is still
        # refused, with the same code; what is now permitted is a C4 run under an
        # authority that names C4.
        gov.assert_architecture_delivery_authorised(purpose, request.condition)
        reset_state = _resolve_reset_state(purpose, request)
        if reset_state is not None and request.mode == "real":
            _assert_frozen_launch_configuration(purpose, request, reset_state)

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
            # failure point is the only defensible one for a paid run. Under a
            # diagnostic-scoped freeze the per-repetition conditions it does NOT
            # waive are required here too, so an unsupplied model id or runtime
            # version refuses before a process could be created.
            ev.assert_scoring_prerequisites(
                request.task_id,
                condition=request.condition,
                run_purpose=purpose.name,
                model_id=request.model_id,
                cli_version=gov.live_runtime_validation(purpose.name)[2],
                session_id=request.session_id,
                previous_session_ids=request.previous_session_ids,
                require_execution_evidence=True,
                # The audit has not run yet. CONTEXT_AUDIT runs next and refuses
                # on anything but CLEAN before a process could be created, and
                # POST_RUN_EVALUATION re-asserts with the observed verdict.
                require_context_verdict=False,
            )
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
            repetition=request.repetition,
        )
        root = request.artifact_root or gov.default_artifact_root()
        directory = art.ArtifactDirectory(Path(root), run_id, purpose).create()
        result.run_dir = directory.run_dir

        repo_state_before = gov.repository_state(request.repo)

        # ONE sterile environment per run, built here and then used for every
        # later step: it is what the audit inspects AND what the process is
        # started in. Building a second one for the launch would make the audit
        # a description of something that never ran.
        sterile = ca.make_sterile_env(
            run_id,
            base_dir=request.sterile_base,
            credential_source=request.credential_source,
            launchable=request.credential_source is not None,
        )

        # The prompt is delivered out of band and is never written into the
        # model-visible worktree (CONDITION_MATRIX.csv: task_delivery=prompt).
        #
        # For a condition whose architecture_delivery is 'none' this is the task
        # body verbatim, byte for byte, exactly as before. For C4 it is the
        # approved architecture payload as primary context followed by the same
        # verbatim body — the prompt_injection delivery the worktree policy
        # already defines — and the payload it actually carries is re-hashed and
        # checked against the approved document before anything is started.
        prompt_text = cp.compose_task_prompt(
            request.condition, body.read_bytes(), repo=request.repo
        )
        prompt_manifest = cp.assert_architecture_payload(
            request.condition, prompt_text, repo=request.repo, where="task prompt"
        )
        prompt_path = directory.path("prompts/task_prompt.md")
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(prompt_text, encoding="utf-8", newline="\n")
        directory.write_json("prompt_manifest.json", prompt_manifest)

        readiness = gov.check_readiness(
            request.task_id,
            request.condition,
            purpose.name,
            repo=request.repo,
            private_root=request.private_root,
        )
        result.readiness = readiness
        directory.write_json("readiness.json", readiness.to_dict())

        if request.mode == "real":
            _assert_readiness_permits_a_real_run(readiness)

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
                # None for a no-architecture arm, and the approved payload for
                # one that receives it. C4's delivery is prompt_injection, so
                # supplying it here writes NO file into the model's worktree —
                # it records the payload's hash in the prepared manifest, which
                # is what lets the worktree enforcement verify that the arm got
                # what the record says it got.
                architecture_text=gov.architecture_payload_for(
                    request.condition, request.repo
                ),
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
        plan = build_plan()
        audit_provider = request.audit_provider or real_context_audit
        audit_kwargs = dict(
            condition=request.condition,
            run_id=run_id,
            workspace=directory.worktree,
            generated_at=request.generated_at,
            launch=plan.launch_command(),
            previous_session_ids=tuple(request.previous_session_ids),
        )
        if request.audit_provider is None:
            # Only the production auditor understands the sterile environment;
            # an injected test provider keeps its original signature.
            audit_kwargs["sterile"] = sterile
        try:
            audit_result = audit_provider(**audit_kwargs)
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
        final_plan = build_plan()
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
        launcher = request.process_launcher
        stream_outcome: Optional[sl.StreamOutcome] = None
        if launcher is None and request.mode == "real" and request.launcher_executable:
            # The LIVE launcher, for reset and non-reset alike. A launcher used
            # only for resets would make "was this a reset?" and "which launcher
            # ran it?" the same question, and the two must stay separable.
            launcher = sl.LiveClaudeCodeLauncher(
                executable=request.launcher_executable,
                cwd=directory.worktree,
                env=plan.environment(),
                evidence_path=directory.path("runtime_evidence.jsonl"),
                governed_root=directory.run_dir,
                canonical_repo=request.repo,
                config_dir=sterile.config_dir if sterile else None,
                timeout_seconds=request.launch_timeout_seconds,
                checkpoint=None,  # a NON_RESET run is never interrupted
            )
        adapter = ma.ModelInvocationAdapter(
            mode=request.mode,
            process_launcher=launcher or ma._refusing_launcher,
            # A diagnostic-scoped selection satisfies this slot without touching
            # the global registry: primary_model stays null and TD-B03 stays open.
            registry_primary_model=(
                gov.primary_model()
                or gov.diagnostic_primary_model(purpose.name if purpose else None)
            ),
            governed_ids=tuple(gov.governed_model_ids()),
        )

        if reset_state == rb.RESET and request.mode == "real":
            adapter.assert_real_invocation_permitted(plan.model_id)
            reset_outcome = ro.run_reset(
                ro.ResetInputs(
                    run_purpose=purpose.name,
                    task_id=request.task_id,
                    task_sha256=expected_sha,
                    task_body=body.read_bytes(),
                    condition=request.condition,
                    model_id=str(request.model_id),
                    runtime_version=gov.live_runtime_validation(purpose.name)[2],
                    worktree=directory.worktree,
                    artifact_dir=directory.run_dir,
                    sterile_base=request.sterile_base,
                    credential_source=Path(str(request.credential_source)),
                    launcher_executable=str(request.launcher_executable),
                    canonical_repo=request.repo,
                    governed_root=directory.run_dir,
                    permission_mode=str(request.permission_mode),
                    tools=tuple(request.tools),
                    allowed_tools=tuple(request.allowed_tools),
                    generated_at=request.generated_at,
                    repo=request.repo,
                    launch_timeout_seconds=request.launch_timeout_seconds,
                )
            )
            reset_block = reset_outcome.to_dict()
            invocation = ma.ModelInvocationOutcome(
                invoked=True,
                status=reset_outcome.status,
                exit_status=(
                    reset_outcome.phase_b.exit_status
                    if reset_outcome.phase_b
                    else (
                        reset_outcome.phase_a.exit_status
                        if reset_outcome.phase_a
                        else None
                    )
                ),
                runtime_evidence_path=(
                    reset_outcome.phase_a.runtime_evidence_path
                    if reset_outcome.phase_a
                    else None
                ),
                # BOTH phases' events. The model-identity readback then covers
                # the whole observation rather than its first half, so a phase B
                # that somehow resolved a different model is caught by the
                # existing Q1 check as an AMBIGUOUS readback instead of passing
                # unexamined.
                runtime_evidence=(
                    list(reset_outcome.phase_a_events)
                    + list(reset_outcome.phase_b_events)
                ),
                detail=reset_outcome.detail,
            )
            machine.passed(
                f"two-phase reset: {reset_outcome.status}; "
                f"checkpoint_reached={reset_outcome.checkpoint_reached}"
            )
        else:
            invocation = adapter.invoke(plan)
            if isinstance(invocation, sl.StreamOutcome):
                stream_outcome = invocation
                invocation = stream_outcome.as_invocation_outcome()
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
            condition=request.condition,
            run_purpose=purpose.name,
        )
        if request.scored or request.mode == "real":
            # Re-asserted against what was actually OBSERVED, not against what
            # was requested: the runtime's own reported version and the audit
            # verdict the run really got.
            observed_cli = None
            init = ma.first_init_event(invocation.runtime_evidence)
            if init:
                observed_cli = init.get("claude_code_version")
            ev.assert_scoring_prerequisites(
                request.task_id,
                condition=request.condition,
                run_purpose=purpose.name,
                model_id=identity.resolved or request.model_id,
                cli_version=observed_cli,
                context_verdict=audit_block.get("verdict"),
                session_id=request.session_id,
                previous_session_ids=request.previous_session_ids,
                launch_argv=plan.argv if plan else (),
                require_execution_evidence=True,
            )
            machine.passed("evaluation channels ready")
        else:
            machine.skipped(
                "DRY_RUN_NO_SCORING",
                "nothing is scored in a dry run; the evaluation boundary is "
                "reported with its blockers: "
                + ", ".join(str(c.code) for c in evaluation.blockers),
            )

        # The efficiency block is derived AFTER evaluation so TOTAL_RUN_SECONDS
        # and EVALUATION_SECONDS are real durations rather than estimates, and
        # it is built only for a purpose that declares a reset state: no earlier
        # record grows a block it never had.
        if reset_state is not None and invocation.invoked:
            efficiency_block = _efficiency_block(
                reset_state=reset_state,
                request=request,
                reset_outcome=reset_outcome,
                stream_outcome=stream_outcome,
                invocation=invocation,
                run_started=run_started,
            )
        if reset_state is not None and reset_block is None:
            reset_block = _declared_reset_block(
                request, purpose, reset_state, stream_outcome, invocation
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
            reset=reset_block,
            efficiency=efficiency_block,
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
                    reset=reset_block,
                    efficiency=efficiency_block,
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


#: Purposes that declare a reset state. A purpose absent from this mapping runs
#: exactly as it did before this package: no reset state, no reset block, no
#: efficiency block, no turn ceiling and no permission allowlist.
RESET_AWARE_PURPOSES: Dict[str, Sequence[str]] = {
    "AFCI_EFFICIENCY_PILOT": rb.RESET_STATES,
}


def _resolve_reset_state(
    purpose: gov.RunPurpose, request: RunRequest
) -> Optional[str]:
    """The run's reset state, or ``None`` for a purpose that has none.

    Fails closed both ways. A reset-aware purpose that is handed no reset state
    is refused rather than defaulted to ``NON_RESET``: the two arms are the
    experimental factor, and silently picking one would assign half the design
    by omission. A purpose that is NOT reset-aware and is handed a reset state
    is refused too, because it has no frozen allowance to run under.
    """
    states = RESET_AWARE_PURPOSES.get(purpose.name)
    if states is None:
        if request.reset_state is not None:
            raise gov.RunnerRefusal(
                gov.RESET_NOT_AUTHORISED_FOR_PURPOSE,
                f"{purpose.name} declares no reset state; "
                f"{request.reset_state!r} was supplied and no authority freezes "
                "an allowance for it",
            )
        return None
    if request.reset_state is None:
        raise gov.RunnerRefusal(
            gov.RESET_STATE_INVALID,
            f"{purpose.name} crosses every cell with {list(states)}; a run must "
            "declare which one it is and never defaults to either",
        )
    return rb.assert_reset_state(request.reset_state)


#: Blockers a REAL run may still carry into ``PRECHECK``, because the very next
#: state resolves them fail-closed and resolving them earlier is not possible.
#:
#: Exactly one qualifies: the context-isolation verdict. A readiness report has
#: not run the audit and truthfully reports the verdict as not demonstrated;
#: ``CONTEXT_AUDIT`` runs it moments later and refuses on anything but CLEAN
#: before a process could be created.
_BLOCKERS_RESOLVED_BY_A_LATER_STATE: Sequence[str] = (
    gov.CONTEXT_AUDIT_UNKNOWN,
    gov.CONTEXT_AUDIT_CONTAMINATED,
)


def _assert_readiness_permits_a_real_run(readiness: gov.ReadinessReport) -> None:
    """Refuse a paid run whose own readiness report says it is not eligible.

    This closes a fail-OPEN. The readiness report was computed, written to
    ``readiness.json`` and recorded in ``prerequisite_blockers`` — and then not
    acted on. A run could therefore spend real money while the artifact beside
    it said, correctly, that its prerequisites were unmet. It never happened,
    because every purpose executed so far had them met; that is luck, not a
    control.

    Reported all at once rather than one at a time: an operator preparing a
    36-run session needs the whole list, not the first item thirty-six times.
    """
    outstanding = [
        item
        for item in readiness.blocked
        if str(item.code) not in _BLOCKERS_RESOLVED_BY_A_LATER_STATE
    ]
    if not outstanding:
        return
    detail = "; ".join(f"<{item.code}> {item.item}: {item.detail}" for item in outstanding)
    raise gov.RunnerRefusal(
        str(outstanding[0].code),
        f"{len(outstanding)} run-eligibility prerequisite(s) are unmet and a real "
        f"run is refused before a process could be created: {detail}",
    )


def _assert_frozen_launch_configuration(
    purpose: gov.RunPurpose, request: RunRequest, reset_state: str
) -> None:
    """Refuse a real run whose launch is not the one the authority froze.

    This exists because the alternative fails OPEN, which is the wrong direction
    for both values it checks:

    * a missing turn ceiling would let one repetition run without any allowance
      at all while every other repetition in the same cell ran under 64, and the
      record would show nothing wrong;
    * a missing permission allowlist would reproduce, exactly, the defect
      `SL-V2-EFF-01` §5 was written about — the governed CI command refused in
      every attempt, and the run measuring the refusal.

    Both are compared against what the purpose FREEZES, re-derived rather than
    restated, so a caller cannot satisfy the check by passing something that
    merely looks plausible.
    """
    expected_tools = _frozen_allowed_tools(purpose.name, request.task_id)
    if tuple(request.allowed_tools) != tuple(expected_tools):
        raise gov.RunnerRefusal(
            gov.DIAGNOSTIC_FREEZE_RECORD_INCONSISTENT,
            f"{purpose.decision_id} freezes the permission allowlist "
            f"{list(expected_tools)} for {request.task_id}; the run supplies "
            f"{list(request.allowed_tools)}. A run without it is refused the "
            "governed CI command and measures the refusal",
        )
    expected_turns = _frozen_max_turns(purpose.name, reset_state)
    if request.max_turns != expected_turns:
        raise gov.RunnerRefusal(
            gov.RESET_BUDGET_NOT_FROZEN,
            f"{reset_state} under {purpose.name} carries a frozen ceiling of "
            f"{expected_turns!r}; the run supplies {request.max_turns!r}. The "
            "runner never runs an allowance it was not given",
        )


def _declared_reset_block(
    request: RunRequest,
    purpose: gov.RunPurpose,
    reset_state: str,
    stream_outcome: Optional[sl.StreamOutcome],
    invocation: ma.ModelInvocationOutcome,
) -> Dict[str, object]:
    """The reset block a run carries when no two-phase orchestration ran.

    That covers two different situations and they are recorded as two different
    things rather than collapsed:

    * a **NON_RESET** run, which really was one process. ``reset_state:
      NON_RESET`` is a positive statement about it, not the absence of a reset
      block, which a later reader could read as "nobody recorded it".
    * a **RESET** run that never reached invocation — a dry run. It keeps
      ``reset_state: RESET``, because that is the arm it was assigned to, and
      says plainly that no phase happened. Writing ``NON_RESET`` here would
      label a run as the other arm of the experiment on the strength of it not
      having started.
    """
    block = rb.budget_block(
        run_purpose=purpose.name,
        reset_state=reset_state,
        repo=request.repo,
    )
    if reset_state == rb.NON_RESET:
        detail = "one process, one session, one profile; no interruption"
        status = stream_outcome.completion if stream_outcome else (
            invocation.status if invocation.invoked else "NOT_INVOKED"
        )
    else:
        detail = (
            "assigned to the RESET arm; no phase was executed, so no checkpoint "
            "was evaluated and no phase A or phase B exists"
        )
        status = "NOT_INVOKED"
    block.update(
        {
            "status": status,
            "checkpoint_reached": None,
            "checkpoint_id": None,
            "checkpoint_hash": None,
            "phase_a_session_id": None,
            "phase_b_session_id": None,
            "pre_reset_turns_used": None,
            "post_reset_turns_used": None,
            "resume_used": False,
            "continue_used": False,
            "conversation_reused": False,
            "phase_a_summarised_into_phase_b": False,
            "detail": detail,
        }
    )
    return block


def _efficiency_block(
    *,
    reset_state: str,
    request: RunRequest,
    reset_outcome: Optional[ro.ResetOutcome],
    stream_outcome: Optional[sl.StreamOutcome],
    invocation: ma.ModelInvocationOutcome,
    run_started: float,
) -> Optional[Dict[str, object]]:
    """Measure the observation, failing closed rather than reporting zeros."""
    ci_command = gov.visible_ci_command(request.task_id)
    total = time.monotonic() - run_started

    if reset_state == rb.RESET:
        if reset_outcome is None or reset_outcome.phase_b is None:
            # A reset that produced no phase B produced no reset observation to
            # measure. Phase A's own usage is still recorded, because it was
            # really spent and a pilot that reported it as nothing would
            # understate what the checkpoint-not-reached outcome cost.
            if reset_outcome is None or not reset_outcome.phase_a_events:
                return None
            usage = em.extract_usage(
                reset_outcome.phase_a_events,
                expected_model_id=request.model_id,
                where="RESET phase A (no phase B)",
                allow_partial=True,
            )
            tools = em.extract_tool_metrics(
                reset_outcome.phase_a_events, ci_command=ci_command
            )
            timing = em.Timing(
                phase_a_seconds=reset_outcome.phase_a.model_seconds
                if reset_outcome.phase_a
                else None,
                total_run_seconds=total,
            )
            return {
                "reset_state": rb.RESET,
                "status": reset_outcome.status,
                "complete": False,
                "TURNS_USED": em.turns_used(reset_outcome.phase_a_events),
                "usage": usage.to_dict(),
                "tools": tools.to_dict(),
                "timing": timing.to_dict(),
                "phases": {"A": {"usage": usage.to_dict(), "tools": tools.to_dict()}},
            }
        timing = em.Timing(
            phase_a_seconds=reset_outcome.phase_a.model_seconds
            if reset_outcome.phase_a
            else None,
            phase_b_seconds=reset_outcome.phase_b.model_seconds,
            reset_handoff_seconds=reset_outcome.handoff_seconds,
            total_run_seconds=total,
        )
        measurement = em.aggregate_reset(
            reset_outcome.phase_a_events,
            reset_outcome.phase_b_events,
            model_id=request.model_id,
            ci_command=ci_command,
            timing=timing,
        )
        payload = measurement.to_dict()
        payload["status"] = reset_outcome.status
        payload["complete"] = True
        return payload

    events = invocation.runtime_evidence or []
    timing = em.Timing(
        phase_a_seconds=stream_outcome.wall_seconds if stream_outcome else None,
        total_run_seconds=total,
    )
    measurement = em.measure_non_reset(
        events, model_id=request.model_id, ci_command=ci_command, timing=timing
    )
    payload = measurement.to_dict()
    payload["status"] = (
        stream_outcome.completion if stream_outcome else invocation.status
    )
    payload["complete"] = True
    return payload


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
    reset: Optional[Dict[str, object]] = None,
    efficiency: Optional[Dict[str, object]] = None,
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
        "allowed_tools": list(plan.allowed_tools) if plan else list(request.allowed_tools),
        "tools": list(plan.tools) if plan else list(request.tools),
        "max_turns": plan.max_turns if plan else request.max_turns,
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
        "prompt_manifest.json",
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
        repetition=request.repetition,
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
        manifest_freeze=ev.freeze_status_report(
            request.task_id,
            condition=request.condition,
            run_purpose=purpose.name,
        ),
        artifacts=artifacts,
        prerequisite_blockers=blockers,
        outcome=outcome,
        generated_at=request.generated_at,
        repo=request.repo,
        reset=reset,
        efficiency=efficiency,
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
    p.add_argument(
        "--repetition", type=int, default=None,
        help=(
            "SL-RUNID-01: the 1-based repetition index (R1/R2/R3...). It enters the "
            "run id, so repetitions of one task/condition no longer collide and "
            "no longer need a separate --artifact-root each. Omitted means 1, "
            "recorded as not declared."
        ),
    )
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
    p.add_argument(
        "--live-context-audit", action="store_true",
        help=(
            "Readiness only: PERFORM the real context audit and use the verdict "
            "it actually returns. It is never an assertion flag - the audit is "
            "run, and a CONTAMINATED or UNKNOWN verdict blocks exactly as it "
            "would in a run. No model process is started."
        ),
    )
    p.add_argument("--credential", default=None, help="Subscription credential file.")
    p.add_argument("--claude-executable", default=None, help="Claude Code executable.")
    p.add_argument("--sterile-base", default=None, help="Base dir for sterile profiles.")
    p.add_argument(
        "--permission-mode", default=None,
        help="Permission mode; the frozen diagnostic value when omitted.",
    )
    p.add_argument(
        "--tool", action="append", default=[],
        help="Allowed tool (repeatable); the frozen diagnostic set when omitted.",
    )
    p.add_argument(
        "--launch-timeout-seconds", type=int, default=1800,
        help="Wall-clock ceiling for one repetition.",
    )
    p.add_argument(
        "--reset-state", default=None, choices=list(rb.RESET_STATES),
        help=(
            "SL-V2-EFF-01: which arm of the reset factor this run is. REQUIRED "
            "for a reset-aware purpose and refused for any other; it never "
            "defaults, because defaulting would assign half the design by "
            "omission."
        ),
    )
    p.add_argument(
        "--allowed-tool", action="append", default=[],
        help=(
            "A permission allowlist rule, repeatable (e.g. 'Bash(npm run "
            "ci:agent)'). DISTINCT from --tool: --tool says which tools exist, "
            "this says which uses of them are pre-approved. Omitted means the "
            "purpose's frozen allowlist, or none."
        ),
    )
    p.add_argument(
        "--max-turns", type=int, default=None,
        help=(
            "SL-V2-EFF-RESET-01's agentic-turn ceiling. Omitted means the "
            "purpose's frozen allowance, or no ceiling at all."
        ),
    )
    p.add_argument("--json", action="store_true", help="Emit machine-readable output.")
    return p


def _frozen_allowed_tools(run_purpose: Optional[str], task_id: str) -> Sequence[str]:
    """The permission allowlist a purpose freezes, or nothing at all.

    ``AFCI_EFFICIENCY_PILOT`` freezes an allowlist for exactly one command: the
    governed CI surface the task body already tells the model to use. It was
    added because the earlier configuration refused that command in all 44
    attempts across every executed live run, so a benchmark that told a model to
    validate its work was measuring the refusal. Every other purpose keeps the
    configuration it ran under, which is no allowlist.
    """
    if run_purpose != "AFCI_EFFICIENCY_PILOT":
        return ()
    try:
        command = gov.visible_ci_command(task_id)
    except gov.RunnerRefusal:
        return ()
    return ma.bash_allow_rule(command) if command else ()


def _frozen_max_turns(
    run_purpose: Optional[str], reset_state: Optional[str]
) -> Optional[int]:
    """The turn ceiling a purpose freezes for this arm, or ``None``.

    A ``RESET`` run gets no top-level ceiling: its two phases carry their own,
    and putting phase A's on the outer launch would suggest the whole run had
    32 turns rather than 32 + 32.
    """
    if run_purpose != "AFCI_EFFICIENCY_PILOT" or reset_state is None:
        return None
    if reset_state == rb.RESET:
        return None
    return rb.turn_budget(
        run_purpose=run_purpose, reset_state=reset_state
    ).max_turns


def live_context_verdict(args) -> str:
    """Run the REAL pre-launch audit and report the verdict it returned.

    Implemented as a dry run so the audited environment is the one a repetition
    would actually launch in — the same prepared worktree, the same sterile
    profile, the same launch command — rather than a look-alike built for the
    readiness report. No model process is started.
    """
    root = Path(args.artifact_root) if args.artifact_root else gov.default_artifact_root()
    probe = run(
        RunRequest(
            task_id=args.task,
            condition=args.condition,
            run_purpose=args.run_purpose,
            mode="dry-run",
            artifact_root=root / "readiness-context-audit",
            private_root=Path(args.private_root) if args.private_root else None,
            sterile_base=Path(args.sterile_base) if args.sterile_base else None,
            credential_source=Path(args.credential) if args.credential else None,
            keep_worktree=False,
        )
    )
    if probe.record and probe.record.get("context_audit"):
        return str(probe.record["context_audit"].get("verdict", "UNKNOWN"))
    return "UNKNOWN"


def completion_line(outcome: RunResult, mode: str) -> str:
    """The terminal's one-line summary of a completed run.

    Derived from what the run RECORDED, never from the mode alone. The runner
    previously printed the dry-run sentence unconditionally, so a successful
    ``--real-run`` -- a run in which a model process really did start and really
    did spend a paid turn -- announced on the terminal that "no model was
    invoked". The artifacts were right and only the sentence was wrong, which is
    the dangerous shape of that defect: an operator reading the terminal would
    have described the evidence to a reviewer exactly backwards.

    ``invoked`` is read from the invocation block rather than inferred from
    ``mode`` so the sentence reports the observation instead of the intention.
    """
    invoked = False
    scored = False
    if outcome.record:
        invocation = outcome.record.get("invocation") or {}
        invoked = bool(invocation.get("invoked"))
        scored = bool((outcome.record.get("outcome") or {}).get("scored"))
    scoring = "something was scored" if scored else "nothing was scored"

    if not invoked:
        if mode == "dry-run":
            return f"dry run complete; no model was invoked and {scoring}"
        # Real mode that reached COMPLETE without starting a process. The runner
        # refuses before this today, so it is reported rather than described.
        return f"run complete; NO model process was started and {scoring}"
    return f"real run complete; a model process was invoked and {scoring}"


def _print_readiness(report: gov.ReadinessReport) -> None:
    print(f"readiness — {report.purpose} / {report.task_id} / {report.condition}")
    for item in report.prerequisites:
        mark = {gov.PASS: "PASS   ", gov.NOT_APPLICABLE: "N/A    "}.get(
            item.status, "BLOCKED"
        )
        print(f"  [{mark}] {item.item}" + (f"  <{item.code}>" if item.code else ""))
        print(f"           {item.detail}")
    print(
        f"  => run_eligible={report.run_eligible} "
        f"({len(report.passed)} pass, {len(report.blocked)} blocked, "
        f"{len(report.not_applicable)} n/a)"
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
                context_verdict=(
                    live_context_verdict(args) if args.live_context_audit else None
                ),
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
            repetition=args.repetition,
            artifact_root=Path(args.artifact_root) if args.artifact_root else None,
            model_id=args.model,
            effort=args.effort,
            session_id=args.session_id,
            previous_session_ids=tuple(args.previous_session_id),
            generated_at=args.generated_at,
            private_root=Path(args.private_root) if args.private_root else None,
            scored=args.scored,
            isolated_environment_attested=args.isolated_environment_attested,
            sterile_base=Path(args.sterile_base) if args.sterile_base else None,
            credential_source=Path(args.credential) if args.credential else None,
            launcher_executable=args.claude_executable,
            permission_mode=args.permission_mode or ma.DIAGNOSTIC_PERMISSION_MODE,
            tools=tuple(args.tool) or ma.DIAGNOSTIC_TOOLS,
            launch_timeout_seconds=args.launch_timeout_seconds,
            reset_state=args.reset_state,
            allowed_tools=(
                tuple(args.allowed_tool)
                or _frozen_allowed_tools(args.run_purpose, args.task)
            ),
            max_turns=(
                args.max_turns
                if args.max_turns is not None
                else _frozen_max_turns(args.run_purpose, args.reset_state)
            ),
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
            print(f"  => {completion_line(outcome, request.mode)}")

    return 0 if outcome.ok else 1


if __name__ == "__main__":
    sys.exit(main())
