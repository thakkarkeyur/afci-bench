#!/usr/bin/env python3
"""The REAL two-phase reset: phase A, the handoff, phase B.

What a reset is, mechanically
-----------------------------
``RESET_PROTOCOL.md`` §1 defines it as a controlled mid-task context
interruption: the first process is stopped at a predefined checkpoint, and a
new, context-free process finishes the same task on the SAME partially modified
worktree, under a total budget equal to a non-reset run's.

Every clause of that sentence is a refusal here:

* *predefined checkpoint* — the predicate is ``SL-V2-EFF-CHK-01``'s, executed by
  :mod:`checkpoint_detector`, which cannot see the condition, the architecture
  score, the hidden functional result or model prose.
* *stopped* — by :mod:`stream_launcher`, at a safe event boundary, with the
  termination method recorded under its own name.
* *new, context-free process* — a fresh process, a fresh sterile profile, a
  fresh session id, and a second context audit that must return CLEAN. No
  ``--resume``, no ``--continue``, no reused session id, no transferred
  conversation and no summary of phase A.
* *the same worktree* — phase B runs in the directory phase A left behind. It is
  not copied, restored or cleaned, and this module verifies it is the same path
  and that it was not emptied.
* *equal total budget* — ``SL-V2-EFF-RESET-01``'s 32 + 32 = 64, with the
  post-reset allowance frozen in advance and unaffected by phase-A consumption.

What CANNOT change between the phases
-------------------------------------
The model id, the runtime version, the condition, the task, and — for ``C4`` —
the exact architecture bytes. Each is checked rather than assumed, because a
reset that quietly changed one of them would produce a comparison between two
different things while looking like a comparison between two phases.

Checkpoint not reached
----------------------
If phase A exhausts its allowance without the predicate becoming true, the
observation is :data:`run_governance.RESET_CHECKPOINT_NOT_REACHED`. That is a
SUBSTANTIVE RESULT, not an error to recover from. No phase B is fabricated, no
rerun is scheduled, no budget is raised, and no alternate checkpoint is
substituted. A pilot that quietly retried until it got a reset would be
reporting the retries, not the resets.

No model is selected here, and nothing is scored.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence

import checkpoint_detector as cd
import condition_prompt as cp
import context_audit as ca
import efficiency_metrics as em
import model_adapter as ma
import reset_budget as rb
import run_governance as gov
import stream_launcher as sl

#: The outcome of a reset run. Exactly three are possible.
RESET_COMPLETE = "RESET_COMPLETE"
RESET_CHECKPOINT_NOT_REACHED = gov.RESET_CHECKPOINT_NOT_REACHED
RESET_PHASE_A_FAILED = "RESET_PHASE_A_FAILED"


@dataclass
class PhaseRecord:
    """One phase's own facts. Never merged with the other phase's."""

    phase: str
    session_id: str
    profile_dir: str
    home_dir: str
    worktree: str
    max_turns: int
    model_id: str
    runtime_version: Optional[str]
    condition: str
    task_id: str
    task_sha256: str
    prompt_manifest: Dict[str, object]
    context_audit_verdict: str
    context_audit_path: Optional[str]
    runtime_evidence_path: str
    event_count: int
    completion: str
    termination_method: str
    exit_status: Optional[int]
    turns_used: int
    hit_turn_ceiling: bool
    model_seconds: float

    def to_dict(self) -> Dict[str, object]:
        return {
            "phase": self.phase,
            "session_id": self.session_id,
            "profile_dir": self.profile_dir,
            "home_dir": self.home_dir,
            "worktree": self.worktree,
            "max_turns": self.max_turns,
            "model_id": self.model_id,
            "runtime_version": self.runtime_version,
            "condition": self.condition,
            "task_id": self.task_id,
            "task_sha256": self.task_sha256,
            "prompt_manifest": self.prompt_manifest,
            "context_audit_verdict": self.context_audit_verdict,
            "context_audit_path": self.context_audit_path,
            "runtime_evidence_path": self.runtime_evidence_path,
            "event_count": self.event_count,
            "completion": self.completion,
            "termination_method": self.termination_method,
            "exit_status": self.exit_status,
            "turns_used": self.turns_used,
            "hit_turn_ceiling": self.hit_turn_ceiling,
            "model_seconds": round(self.model_seconds, 3),
        }


@dataclass
class ResetOutcome:
    """Everything a reset run produced, phases kept distinct throughout."""

    status: str
    reset_state: str = rb.RESET
    phase_a: Optional[PhaseRecord] = None
    phase_b: Optional[PhaseRecord] = None
    checkpoint: Dict[str, object] = field(default_factory=dict)
    handoff_seconds: Optional[float] = None
    detail: str = ""
    phase_a_events: List[dict] = field(default_factory=list)
    phase_b_events: List[dict] = field(default_factory=list)

    @property
    def checkpoint_reached(self) -> bool:
        return bool(self.checkpoint.get("checkpoint_reached"))

    def to_dict(self) -> Dict[str, object]:
        a = self.phase_a
        b = self.phase_b
        return {
            "reset_state": self.reset_state,
            "status": self.status,
            "detail": self.detail,
            "budget_authority": rb.SL_V2_EFF_RESET_01,
            "checkpoint_authority": cd.CHECKPOINT_AUTHORITY,
            "checkpoint_id": self.checkpoint.get("checkpoint_id"),
            "checkpoint_hash": self.checkpoint.get("checkpoint_hash"),
            "checkpoint_reached": self.checkpoint_reached,
            "checkpoint_event_index": self.checkpoint.get("checkpoint_event_index"),
            "checkpoint_evidence": self.checkpoint,
            "phase_a_session_id": a.session_id if a else None,
            "phase_b_session_id": b.session_id if b else None,
            "phase_a_model": a.model_id if a else None,
            "phase_b_model": b.model_id if b else None,
            "phase_a_runtime": a.runtime_version if a else None,
            "phase_b_runtime": b.runtime_version if b else None,
            "phase_a_context_audit": a.context_audit_verdict if a else None,
            "phase_b_context_audit": b.context_audit_verdict if b else None,
            "phase_a_termination_method": a.termination_method if a else None,
            "pre_reset_turn_limit": a.max_turns if a else rb.PRE_RESET_MAX_TURNS,
            "post_reset_turn_limit": b.max_turns if b else rb.POST_RESET_MAX_TURNS,
            "pre_reset_turns_used": a.turns_used if a else None,
            "post_reset_turns_used": b.turns_used if b else None,
            "reset_handoff_seconds": (
                None if self.handoff_seconds is None else round(self.handoff_seconds, 3)
            ),
            # Stated as facts rather than left to be inferred from an absence.
            "fresh_phase_b_process": b is not None,
            "fresh_phase_b_profile": bool(
                a and b and a.profile_dir != b.profile_dir
            ),
            "fresh_phase_b_session": bool(a and b and a.session_id != b.session_id),
            "resume_used": False,
            "continue_used": False,
            "conversation_reused": False,
            "phase_a_summarised_into_phase_b": False,
            "same_worktree_across_reset": bool(a and b and a.worktree == b.worktree),
            "phases": {
                "A": a.to_dict() if a else None,
                "B": b.to_dict() if b else None,
            },
        }


#: What a caller must supply. Everything is an input; nothing is discovered.
@dataclass
class ResetInputs:
    run_purpose: str
    task_id: str
    task_sha256: str
    task_body: bytes
    condition: str
    model_id: str
    runtime_version: str
    worktree: Path
    artifact_dir: Path
    sterile_base: Optional[Path]
    credential_source: Path
    launcher_executable: str
    canonical_repo: Path
    governed_root: Path
    permission_mode: str
    tools: Sequence[str]
    allowed_tools: Sequence[str]
    generated_at: str = "unspecified"
    repo: Path = gov.REPO
    launch_timeout_seconds: int = 1800
    #: Injected so tests can drive the whole orchestration without a process.
    launcher_factory: Optional[Callable[..., object]] = None
    audit_provider: Optional[Callable[..., ca.AuditResult]] = None
    session_id_factory: Callable[[], str] = lambda: str(uuid.uuid4())


def _runtime_version(events: Sequence[dict]) -> Optional[str]:
    init = ma.first_init_event(list(events))
    value = (init or {}).get("claude_code_version")
    return value if isinstance(value, str) else None


def _worktree_entry_count(worktree: Path) -> int:
    return sum(1 for _ in Path(worktree).rglob("*") if _.is_file())


def run_reset(inputs: ResetInputs) -> ResetOutcome:
    """Execute one RESET observation end to end, failing closed throughout."""
    budget_a = rb.turn_budget(
        run_purpose=inputs.run_purpose, reset_state=rb.RESET, phase=rb.PHASE_A,
        repo=inputs.repo,
    )
    budget_b = rb.turn_budget(
        run_purpose=inputs.run_purpose, reset_state=rb.RESET, phase=rb.PHASE_B,
        repo=inputs.repo,
    )
    ci_command = gov.visible_ci_command(inputs.task_id)
    detector = cd.CiAgentAfterEditDetector(ci_command=ci_command)

    # ---------------- PHASE A ------------------------------------------- #
    phase_a, outcome_a = _run_phase(
        inputs,
        phase=rb.PHASE_A,
        max_turns=budget_a.max_turns,
        prompt=cp.compose_task_prompt(
            inputs.condition, inputs.task_body, repo=inputs.repo
        ),
        prompt_name="phase_a_prompt.md",
        evidence_name="phase_a_runtime_evidence.jsonl",
        audit_name="phase_a_context_audit.json",
        previous_session_ids=(),
        checkpoint=detector.observe,
    )

    checkpoint = dict(detector.to_dict())
    checkpoint["checkpoint_hash"] = hashlib.sha256(
        f"{checkpoint['checkpoint_id']}|{checkpoint['predicate']}".encode("utf-8")
    ).hexdigest()

    if outcome_a.completion == sl.PROCESS_FAILED:
        return ResetOutcome(
            status=RESET_PHASE_A_FAILED,
            phase_a=phase_a,
            checkpoint=checkpoint,
            detail=(
                f"phase A ended as {outcome_a.completion} with exit "
                f"{outcome_a.exit_status}; the observation is invalid rather "
                "than partial and no phase B is started"
            ),
            phase_a_events=list(outcome_a.events),
        )

    if not detector.reached:
        # THE substantive non-reset-completing observation. Recorded exactly as
        # it happened and never repaired: no phase B, no rerun, no larger
        # budget, no alternate checkpoint.
        return ResetOutcome(
            status=RESET_CHECKPOINT_NOT_REACHED,
            phase_a=phase_a,
            checkpoint=checkpoint,
            detail=(
                f"phase A used {phase_a.turns_used} of its {budget_a.max_turns} "
                "turns without the selected checkpoint becoming true "
                f"(hit_turn_ceiling={phase_a.hit_turn_ceiling}). This is a "
                "substantive observation; no phase B is fabricated and no rerun "
                "is scheduled"
            ),
            phase_a_events=list(outcome_a.events),
        )

    # ---------------- HANDOFF -------------------------------------------- #
    handoff_started = time.monotonic()

    if phase_a.termination_method == sl.NOT_TERMINATED and outcome_a.stopped_early:
        raise gov.RunnerRefusal(  # pragma: no cover - launcher guarantees otherwise
            gov.RESET_PHASE_PROCESS_NOT_STOPPED,
            "the checkpoint was reached but no termination was recorded; a "
            "phase A that may still be running cannot hand over a worktree",
        )

    entries_before = _worktree_entry_count(inputs.worktree)
    if entries_before == 0:
        raise gov.RunnerRefusal(
            gov.RESET_WORKTREE_NOT_PRESERVED,
            f"the worktree {inputs.worktree} is empty after phase A; the reset "
            "preserves the partially modified repository and never restores or "
            "cleans it",
        )

    handoff_seconds = time.monotonic() - handoff_started

    # ---------------- PHASE B -------------------------------------------- #
    phase_b, outcome_b = _run_phase(
        inputs,
        phase=rb.PHASE_B,
        max_turns=budget_b.max_turns,
        prompt=cp.compose_continuation_prompt(
            inputs.condition, inputs.task_body, repo=inputs.repo
        ),
        prompt_name="phase_b_prompt.md",
        evidence_name="phase_b_runtime_evidence.jsonl",
        audit_name="phase_b_context_audit.json",
        previous_session_ids=(phase_a.session_id,),
        checkpoint=None,
    )

    _assert_phases_consistent(phase_a, phase_b)

    entries_after = _worktree_entry_count(inputs.worktree)
    if entries_after < entries_before:
        # Phase B may ADD and may EDIT. A net loss of files is the shape a
        # restore or a clean would leave, so it is refused rather than noted.
        raise gov.RunnerRefusal(
            gov.RESET_WORKTREE_NOT_PRESERVED,
            f"the worktree held {entries_before} files at the handoff and "
            f"{entries_after} after phase B; the reset never removes the work "
            "phase A left behind",
        )

    return ResetOutcome(
        status=RESET_COMPLETE,
        phase_a=phase_a,
        phase_b=phase_b,
        checkpoint=checkpoint,
        handoff_seconds=handoff_seconds,
        detail=(
            f"phase A stopped at event {checkpoint['checkpoint_event_index']} by "
            f"{phase_a.termination_method}; phase B ran in a fresh process, a "
            "fresh profile and a fresh session on the same worktree with no "
            "resume, no continuation and no transferred conversation"
        ),
        phase_a_events=list(outcome_a.events),
        phase_b_events=list(outcome_b.events),
    )


def _run_phase(
    inputs: ResetInputs,
    *,
    phase: str,
    max_turns: int,
    prompt: str,
    prompt_name: str,
    evidence_name: str,
    audit_name: str,
    previous_session_ids: Sequence[str],
    checkpoint,
):
    """Start, audit and run ONE phase. Each phase builds its own of everything."""
    artifact = Path(inputs.artifact_dir)
    artifact.mkdir(parents=True, exist_ok=True)

    manifest = cp.assert_architecture_payload(
        inputs.condition, prompt, repo=inputs.repo, where=f"phase {phase}"
    )
    prompt_path = artifact / "prompts" / prompt_name
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(prompt, encoding="utf-8", newline="\n")

    session_id = inputs.session_id_factory()
    if session_id in set(previous_session_ids):
        raise gov.RunnerRefusal(
            gov.RESET_PHASE_SESSION_REUSED,
            f"phase {phase} was given session id {session_id}, which phase A "
            "already used; a reused id is session reuse whatever else is fresh",
        )

    # A SEPARATE sterile profile per phase. Phase B must not inherit phase A's
    # configuration directory: that directory is where a runtime would keep a
    # session, a transcript or a shell snapshot, and reusing it would leave a
    # channel the reset is supposed to have closed.
    sterile = ca.make_sterile_env(
        f"{inputs.task_id.lower()}-{inputs.condition.lower()}-reset-{phase.lower()}",
        base_dir=inputs.sterile_base,
        credential_source=inputs.credential_source,
        launchable=True,
    )

    plan = ma.build_fresh_launch(
        prompt_path=str(prompt_path),
        workspace=str(inputs.worktree),
        model_id=inputs.model_id,
        session_id=session_id,
        previous_session_ids=previous_session_ids,
        sterile_env=sterile.env,
        require_model=True,
        sterile=True,
        permission_mode=inputs.permission_mode,
        tools=inputs.tools,
        allowed_tools=inputs.allowed_tools,
        max_turns=max_turns,
    )

    # The frozen session guard, applied to THIS phase's argv. Phase B is
    # checked against phase A's id, so the one mechanism that could turn a
    # reset back into a continuation is refused at the point it would happen.
    violations = ca.check_session_flags(list(plan.argv), set(previous_session_ids))
    if violations:
        raise gov.RunnerRefusal(
            gov.RESET_PHASE_CONVERSATION_REUSED,
            f"phase {phase}'s launch restores or reuses a session: "
            + "; ".join(violations),
        )

    audit_provider = inputs.audit_provider
    if audit_provider is None:
        def audit_provider(**kwargs):  # noqa: ANN001 - local default
            roots = ca.ScanRoots.discover(
                workspace=Path(inputs.worktree),
                home=sterile.temp_home,
                config_dir=sterile.config_dir,
            )
            return ca.audit(
                condition=ca.CONDITIONS[inputs.condition],
                roots=roots,
                env=sterile.env,
                launch=plan.launch_command(),
                require_launch=True,
                previous_session_ids=tuple(previous_session_ids),
                run_id=kwargs.get("run_id", ""),
                generated_at=inputs.generated_at,
                account_policy_adjudication=True,
                credential_path=sterile.credential_path,
                verify_profile=True,
            )

    # EVERY phase is audited. Phase B's audit is not a formality: it is the only
    # thing that can catch a profile that carried something forward, and a reset
    # whose second half started contaminated is not a reset.
    audit = audit_provider(
        condition=inputs.condition,
        run_id=f"{inputs.task_id}-{inputs.condition}-reset-{phase}",
        workspace=Path(inputs.worktree),
        generated_at=inputs.generated_at,
        launch=plan.launch_command(),
        previous_session_ids=tuple(previous_session_ids),
    )
    payload = audit.to_dict()
    verdict = str(payload.get("contamination", {}).get("verdict", "UNKNOWN")).upper()
    audit_path = artifact / audit_name
    audit_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if verdict != "CLEAN":
        raise gov.RunnerRefusal(
            gov.CONTEXT_AUDIT_CONTAMINATED
            if verdict == "CONTAMINATED"
            else gov.RESET_PHASE_CONTEXT_AUDIT_MISSING,
            f"phase {phase}'s context audit returned {verdict}; a reset phase "
            "never starts from a context that has not been shown clean",
        )

    factory = inputs.launcher_factory or sl.LiveClaudeCodeLauncher
    launcher = factory(
        executable=inputs.launcher_executable,
        cwd=Path(inputs.worktree),
        env=plan.environment(),
        evidence_path=artifact / evidence_name,
        governed_root=Path(inputs.governed_root),
        canonical_repo=Path(inputs.canonical_repo),
        config_dir=sterile.config_dir,
        timeout_seconds=inputs.launch_timeout_seconds,
        checkpoint=checkpoint,
    )
    started = time.monotonic()
    outcome = launcher(plan)
    model_seconds = time.monotonic() - started

    record = PhaseRecord(
        phase=phase,
        session_id=session_id,
        profile_dir=str(sterile.config_dir),
        home_dir=str(sterile.temp_home),
        worktree=str(Path(inputs.worktree).resolve()),
        max_turns=max_turns,
        model_id=inputs.model_id,
        runtime_version=_runtime_version(outcome.events),
        condition=inputs.condition,
        task_id=inputs.task_id,
        task_sha256=inputs.task_sha256,
        prompt_manifest=manifest,
        context_audit_verdict=verdict,
        context_audit_path=str(audit_path),
        runtime_evidence_path=outcome.runtime_evidence_path,
        event_count=outcome.event_count,
        completion=outcome.completion,
        termination_method=outcome.termination_method,
        exit_status=outcome.exit_status,
        turns_used=em.turns_used(outcome.events),
        hit_turn_ceiling=em.hit_turn_ceiling(outcome.events),
        model_seconds=model_seconds,
    )
    return record, outcome


def _assert_phases_consistent(a: PhaseRecord, b: PhaseRecord) -> None:
    """The five things a reset may never change, each with its own refusal."""
    if a.model_id != b.model_id:
        raise gov.RunnerRefusal(
            gov.RESET_PHASE_MODEL_CHANGED,
            f"phase A ran {a.model_id!r} and phase B ran {b.model_id!r}; a reset "
            "interrupts a run, it does not switch models mid-observation",
        )
    if a.runtime_version and b.runtime_version and a.runtime_version != b.runtime_version:
        raise gov.RunnerRefusal(
            gov.RESET_PHASE_RUNTIME_CHANGED,
            f"phase A reported runtime {a.runtime_version!r} and phase B "
            f"{b.runtime_version!r}; the two halves of one observation must run "
            "on the same runtime",
        )
    if a.condition != b.condition:
        raise gov.RunnerRefusal(
            gov.RESET_PHASE_CONDITION_CHANGED,
            f"phase A ran {a.condition} and phase B ran {b.condition}",
        )
    if a.task_id != b.task_id or a.task_sha256 != b.task_sha256:
        raise gov.RunnerRefusal(
            gov.RESET_PHASE_TASK_CHANGED,
            f"phase A ran {a.task_id}@{a.task_sha256[:12]} and phase B ran "
            f"{b.task_id}@{b.task_sha256[:12]}; the reset finishes the SAME task",
        )
    delivered_a = a.prompt_manifest.get("architecture_sha256_delivered")
    delivered_b = b.prompt_manifest.get("architecture_sha256_delivered")
    if delivered_a != delivered_b:
        raise gov.RunnerRefusal(
            gov.RESET_PHASE_ARCHITECTURE_CHANGED,
            f"phase A delivered architecture {delivered_a!r} and phase B "
            f"{delivered_b!r}; C4 re-injects the EXACT same bytes and C1 "
            "receives none in either phase",
        )
    if a.session_id == b.session_id:
        raise gov.RunnerRefusal(
            gov.RESET_PHASE_SESSION_REUSED,
            "both phases carry the same session id; phase B is a new session",
        )
    if a.profile_dir == b.profile_dir:
        raise gov.RunnerRefusal(
            gov.RESET_PHASE_PROFILE_REUSED,
            "both phases share a sterile profile directory; phase B builds its "
            "own, so nothing a runtime wrote during phase A is visible to it",
        )
    if a.worktree != b.worktree:
        raise gov.RunnerRefusal(
            gov.RESET_WORKTREE_NOT_PRESERVED,
            f"phase A worked in {a.worktree} and phase B in {b.worktree}; the "
            "reset preserves the partially modified repository, so both phases "
            "are the same directory",
        )
