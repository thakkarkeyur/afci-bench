#!/usr/bin/env python3
"""The LIVE structured-stream launcher, and the controlled phase-A stop.

Why this exists
---------------
:class:`model_adapter.RealClaudeCodeLauncher` starts a real process correctly
and refuses correctly, but it uses ``subprocess.run``: the entire stream is
buffered until the child exits and only then parsed. That is adequate for a run
nobody has to interrupt, and it makes a *reset* impossible. A reset has to
decide, while the model is still working, that a predefined predicate has become
true — which means the events have to arrive as they are produced.

This module is that launcher. It keeps every refusal
:class:`~model_adapter.RealClaudeCodeLauncher` makes — the same pinned model,
the same disposable worktree, the same sterile environment and profile, the same
subscription OAuth, the same argv-list/``shell=False`` invocation, the same
redaction, the same model readback — and changes only WHEN the events are read.

It is used for ordinary runs too, so a non-reset repetition and a reset
repetition differ in the reset and in nothing else. A launcher used only for
resets would make "was it a reset?" and "which launcher ran it?" the same
question.

Safe interruption
-----------------
The checkpoint callback is consulted **after** each event has been persisted,
never before. So the evidence for a stop is on disk before the stop happens,
and a process killed at a bad moment still leaves a complete record of the
events that justified it.

The callback decides; this module does not. It is handed the event and its
index, it answers "stop" or "continue", and it is the ONLY thing that can stop
a run early. Nothing in this module inspects task content, condition, prose,
scores or results.

Termination is reported, never dressed up
-----------------------------------------
Windows has no ``SIGINT``-to-a-child that Python can send directly, so the
child is created in its **own process group** (``CREATE_NEW_PROCESS_GROUP``)
and stopped with ``CTRL_BREAK_EVENT``, which is the clean interruption the
platform actually supports. If it does not exit within the grace period, the
stop **escalates** — and the escalation is recorded under its own name
(``TERMINATED_PROCESS_TREE``), never relabelled as a graceful one. A stop that
cannot be completed at all is a refusal: a run whose process may still be
editing the worktree is not an observation.

No model is selected here, and nothing is scored.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import model_adapter as ma
import run_governance as gov

#: How a phase-A process ended. Each is a distinct fact, and one is never
#: written in place of another.
COMPLETED_NATURALLY = "COMPLETED_NATURALLY"
STOPPED_AT_CHECKPOINT = "STOPPED_AT_CHECKPOINT"
MAX_TURNS_REACHED = "MAX_TURNS_REACHED"
PROCESS_FAILED = "PROCESS_FAILED"

#: How the process was actually made to stop. ``NOT_TERMINATED`` is the honest
#: answer for a process that ended on its own.
NOT_TERMINATED = "NOT_TERMINATED"
CTRL_BREAK_PROCESS_GROUP = "CTRL_BREAK_PROCESS_GROUP"
SIGINT_PROCESS_GROUP = "SIGINT_PROCESS_GROUP"
TERMINATED_PROCESS_TREE = "TERMINATED_PROCESS_TREE"

#: The runtime's terminal result subtype when the turn ceiling fires. Read from
#: the installed Claude Code 2.1.229 implementation, not from the help text:
#: the internal ``max_turns_reached`` attachment is CONSUMED by the headless
#: translator and never appears on the wire, so this is the only signal there is.
MAX_TURNS_RESULT_SUBTYPE = "error_max_turns"

#: Seconds to wait for a clean interruption before escalating.
GRACE_SECONDS = 20.0

#: Seconds to wait for the escalated kill before refusing.
KILL_SECONDS = 20.0


@dataclass
class StreamOutcome:
    """What one live-streamed process produced."""

    invoked: bool
    status: str
    exit_status: Optional[int]
    events: List[dict]
    event_count: int
    runtime_evidence_path: str
    stderr_path: str
    termination_method: str
    completion: str
    stopped_early: bool
    stop_event_index: Optional[int]
    wall_seconds: float
    detail: str = ""
    terminal_result: Optional[dict] = None

    @property
    def max_turns_reached(self) -> bool:
        return (
            isinstance(self.terminal_result, dict)
            and self.terminal_result.get("subtype") == MAX_TURNS_RESULT_SUBTYPE
        )

    def to_dict(self) -> Dict[str, object]:
        return {
            "invoked": self.invoked,
            "status": self.status,
            "exit_status": self.exit_status,
            "runtime_evidence_path": self.runtime_evidence_path,
            "stderr_path": self.stderr_path,
            "event_count": self.event_count,
            "termination_method": self.termination_method,
            "completion": self.completion,
            "stopped_early": self.stopped_early,
            "stop_event_index": self.stop_event_index,
            "max_turns_reached": self.max_turns_reached,
            "wall_clock_seconds": round(self.wall_seconds, 3),
            "detail": self.detail,
        }

    def as_invocation_outcome(self) -> ma.ModelInvocationOutcome:
        """The shape the existing state machine already knows how to consume."""
        return ma.ModelInvocationOutcome(
            invoked=self.invoked,
            status=self.status,
            exit_status=self.exit_status,
            runtime_evidence_path=self.runtime_evidence_path,
            runtime_evidence=self.events,
            detail=self.detail,
        )


#: The callback signature: ``(index, event) -> True`` means "stop after this
#: event". Anything else continues.
CheckpointCallback = Callable[[int, dict], bool]

#: An optional sink every event is offered, in order, after it is persisted.
#: This is how metric collectors see a run live instead of re-reading a file.
EventSink = Callable[[int, dict], None]


def _creation_flags() -> int:
    """Put the child in its own process group so it can be signalled alone."""
    if sys.platform == "win32":
        return subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
    return 0


def _popen_kwargs() -> Dict[str, object]:
    if sys.platform == "win32":
        return {"creationflags": _creation_flags()}
    # POSIX: a new session gives the same "signal the child alone" property.
    return {"start_new_session": True}


@dataclass
class LiveClaudeCodeLauncher:
    """Start a fresh Claude Code process and read its stream as it is produced.

    Every refusal :class:`model_adapter.RealClaudeCodeLauncher` makes is made
    here too, by delegating to the same ``_assert_launchable``: the checks are
    not restated, so the two launchers cannot drift into disagreeing about what
    is safe to start.
    """

    executable: str
    cwd: Path
    env: Dict[str, str]
    evidence_path: Path
    governed_root: Optional[Path] = None
    canonical_repo: Optional[Path] = None
    config_dir: Optional[Path] = None
    timeout_seconds: int = 1800
    #: Consulted after each persisted event. ``None`` means the run is never
    #: interrupted, which is what a NON_RESET run and a phase-B run want.
    checkpoint: Optional[CheckpointCallback] = None
    event_sinks: Sequence[EventSink] = field(default_factory=tuple)
    grace_seconds: float = GRACE_SECONDS
    kill_seconds: float = KILL_SECONDS

    # -- refusals --------------------------------------------------------- #
    def _assert_launchable(self, plan: ma.LaunchPlan) -> None:
        """The frozen pre-launch refusals, reused rather than reimplemented."""
        ma.RealClaudeCodeLauncher(
            executable=self.executable,
            cwd=self.cwd,
            env=self.env,
            evidence_path=self.evidence_path,
            governed_root=self.governed_root,
            canonical_repo=self.canonical_repo,
            config_dir=self.config_dir,
            timeout_seconds=self.timeout_seconds,
        )._assert_launchable(plan)

    def _prompt_text(self, plan: ma.LaunchPlan) -> Optional[str]:
        if plan.prompt_delivery != "stdin":
            return None
        if not plan.prompt_path or not Path(plan.prompt_path).is_file():
            raise gov.RunnerRefusal(
                gov.MODEL_WORKTREE_NOT_LAUNCHABLE,
                "the launch delivers the task over stdin but no prompt file "
                "exists; a run must never be started with an empty task",
            )
        text = Path(plan.prompt_path).read_text(encoding="utf-8")
        if not text.strip():
            raise gov.RunnerRefusal(
                gov.MODEL_WORKTREE_NOT_LAUNCHABLE,
                "the task prompt is empty; refusing to spend a run on it",
            )
        return text

    # -- termination ------------------------------------------------------ #
    def _stop(self, proc: "subprocess.Popen[str]") -> Tuple[str, bool]:
        """Stop the child at a safe boundary. Returns ``(method, stopped)``.

        Escalation is explicit and ordered, and each rung is named in the
        returned method so the record never claims a graceful stop it did not
        get:

        1. **Clean interruption** of the child's own process group —
           ``CTRL_BREAK_EVENT`` on Windows, ``SIGINT`` elsewhere. The child was
           created in its own group precisely so this reaches it and nothing
           else.
        2. **Tree termination** if it has not exited within the grace period.
           ``taskkill /T /F`` on Windows because ``Popen.kill`` would leave any
           surviving grandchild running; ``SIGKILL`` to the process group
           elsewhere.

        Neither rung touches the worktree. Nothing here deletes, reverts or
        restores a file, so whatever the model had already written is exactly
        what is there afterwards.
        """
        if proc.poll() is not None:
            return NOT_TERMINATED, True

        method = (
            CTRL_BREAK_PROCESS_GROUP if sys.platform == "win32"
            else SIGINT_PROCESS_GROUP
        )
        try:
            if sys.platform == "win32":
                os.kill(proc.pid, signal.CTRL_BREAK_EVENT)  # type: ignore[attr-defined]
            else:
                os.killpg(os.getpgid(proc.pid), signal.SIGINT)
        except (OSError, ProcessLookupError, ValueError):
            # The signal could not even be delivered. Fall straight through to
            # escalation rather than waiting out a grace period for nothing.
            pass
        else:
            try:
                proc.wait(timeout=self.grace_seconds)
                return method, True
            except subprocess.TimeoutExpired:
                pass

        method = TERMINATED_PROCESS_TREE
        try:
            if sys.platform == "win32":
                subprocess.run(  # noqa: S603 - argv list, shell=False
                    ["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                    capture_output=True,
                    check=False,
                    shell=False,
                )
            else:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (OSError, ProcessLookupError, ValueError):
            pass
        try:
            proc.wait(timeout=self.kill_seconds)
            return method, True
        except subprocess.TimeoutExpired:
            return method, False

    # -- invocation ------------------------------------------------------- #
    def __call__(self, plan: ma.LaunchPlan) -> StreamOutcome:
        self._assert_launchable(plan)
        stdin_text = self._prompt_text(plan)

        argv = [self.executable, *list(plan.argv)[1:]]
        evidence = Path(self.evidence_path)
        evidence.parent.mkdir(parents=True, exist_ok=True)
        stderr_path = evidence.with_suffix(".stderr.txt")

        events: List[dict] = []
        stderr_chunks: List[str] = []
        stop_index: Optional[int] = None
        started = time.monotonic()

        proc = subprocess.Popen(  # noqa: S603 - argv list, shell=False by construction
            argv,
            cwd=str(Path(self.cwd).resolve()),
            env=dict(self.env),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            # PINNED, not inherited, for exactly the reason the buffered
            # launcher pins it: text mode alone encodes stdin with the process
            # locale, which on this host is cp1252, and a task body containing
            # any character outside it raised UnicodeEncodeError while WRITING
            # THE PROMPT -- so the model received empty stdin, emitted no
            # system.init, and the repetition was invalid. The task bodies are
            # UTF-8 and the runtime speaks UTF-8.
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            shell=False,
            **_popen_kwargs(),
        )

        def _write_stdin() -> None:
            try:
                if proc.stdin is not None:
                    if stdin_text:
                        proc.stdin.write(stdin_text)
                    proc.stdin.close()
            except (BrokenPipeError, ValueError, OSError):
                pass

        def _drain_stderr() -> None:
            try:
                if proc.stderr is not None:
                    for line in proc.stderr:
                        stderr_chunks.append(line)
            except (ValueError, OSError):
                pass

        # The prompt is written from its own thread and stderr drained from
        # another, so neither pipe can fill and deadlock the stdout reader that
        # the checkpoint depends on.
        writer = threading.Thread(target=_write_stdin, daemon=True)
        draining = threading.Thread(target=_drain_stderr, daemon=True)
        writer.start()
        draining.start()

        termination_method = NOT_TERMINATED
        stopped_cleanly = True
        timed_out = False

        with evidence.open("w", encoding="utf-8", newline="\n") as sink:
            try:
                for raw in proc.stdout or ():
                    line = raw.strip()
                    if line:
                        try:
                            event = json.loads(line)
                        except ValueError:
                            event = None
                        if isinstance(event, dict):
                            event = redact_event(event)
                            index = len(events)
                            events.append(event)
                            # PERSIST FIRST. The evidence for a stop is on disk
                            # before the stop happens, so an interrupted run
                            # still explains itself.
                            sink.write(json.dumps(event, sort_keys=True) + "\n")
                            sink.flush()
                            for emit in self.event_sinks:
                                emit(index, event)
                            if self.checkpoint is not None and self.checkpoint(
                                index, event
                            ):
                                stop_index = index
                                break
                    if time.monotonic() - started > self.timeout_seconds:
                        timed_out = True
                        break
            finally:
                if stop_index is not None or timed_out:
                    termination_method, stopped_cleanly = self._stop(proc)
                try:
                    proc.wait(timeout=self.kill_seconds)
                except subprocess.TimeoutExpired:
                    termination_method, stopped_cleanly = self._stop(proc)

        writer.join(timeout=5)
        draining.join(timeout=5)
        elapsed = time.monotonic() - started

        stderr_text = ma.redact("".join(stderr_chunks))
        stderr_path.write_text(stderr_text, encoding="utf-8", newline="\n")

        if not stopped_cleanly:
            # FAIL CLOSED. A process that may still be editing the worktree
            # makes the worktree unreadable as evidence, and a run whose
            # evidence cannot be read is not an observation.
            raise gov.RunnerRefusal(
                gov.RESET_PHASE_PROCESS_NOT_STOPPED,
                f"the model process (pid {proc.pid}) could not be stopped after "
                f"{termination_method}; the worktree may still be changing and "
                "the repetition is invalid rather than partial",
            )

        if timed_out:
            raise gov.RunnerRefusal(
                gov.MODEL_PROCESS_FAILED,
                f"the model process exceeded {self.timeout_seconds}s and was "
                f"stopped ({termination_method}); the repetition is invalid "
                "rather than partial",
            )

        terminal = terminal_result(events)
        exit_status = proc.returncode
        completion, status = _classify(
            stopped_early=stop_index is not None,
            terminal=terminal,
            exit_status=exit_status,
        )
        init = ma.first_init_event(events)
        return StreamOutcome(
            invoked=True,
            status=status,
            exit_status=exit_status,
            events=events,
            event_count=len(events),
            runtime_evidence_path=str(evidence),
            stderr_path=str(stderr_path),
            termination_method=termination_method,
            completion=completion,
            stopped_early=stop_index is not None,
            stop_event_index=stop_index,
            wall_seconds=elapsed,
            terminal_result=terminal,
            detail=(
                f"exit={exit_status}; {len(events)} structured event(s) in "
                f"{elapsed:.1f}s; completion={completion}; "
                f"termination={termination_method}; runtime "
                f"{(init or {}).get('claude_code_version', 'unreported')}; "
                f"stderr {len(stderr_text)} char(s)"
            ),
        )


def redact_event(value):
    """Redact credential-shaped material WITHOUT breaking the event's structure.

    The buffered launcher redacts the raw stdout text and then parses it, which
    is safe for a bare token but not for a key/value pair: the pattern that
    masks ``"access_token": "..."`` replaces the whole pair, so the surviving
    line is no longer valid JSON and the event is silently dropped. Dropping a
    redacted event loses evidence, and losing evidence to protect a secret that
    is not in this harness's possession anyway is the wrong trade.

    So the structure is walked and only the LEAVES are masked. Keys are left
    alone — a key is a field name, never a secret — and a redacted event is
    still a well-formed event with one value replaced.
    """
    if isinstance(value, str):
        return ma.redact(value)
    if isinstance(value, dict):
        return {k: redact_event(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_event(v) for v in value]
    return value


def terminal_result(events: Sequence[dict]) -> Optional[dict]:
    """The last ``result`` event, which is the runtime's own verdict on the run."""
    for event in reversed(list(events)):
        if isinstance(event, dict) and event.get("type") == "result":
            return event
    return None


def _classify(
    *, stopped_early: bool, terminal: Optional[dict], exit_status: Optional[int]
) -> Tuple[str, str]:
    """``(completion, status)`` for a finished process.

    The one judgement worth stating: a run that hit the turn ceiling exits
    **1**, because the headless entry point ends with
    ``exit(result.is_error ? 1 : 0)`` and ``error_max_turns`` sets ``is_error``.
    That exit code is NOT a process failure — it is the ceiling working — and a
    launcher that read it as one would invalidate every run that used its full
    allowance.
    """
    if stopped_early:
        return STOPPED_AT_CHECKPOINT, "PROCESS_STOPPED_AT_CHECKPOINT"
    subtype = (terminal or {}).get("subtype")
    if subtype == MAX_TURNS_RESULT_SUBTYPE:
        return MAX_TURNS_REACHED, "PROCESS_COMPLETED_MAX_TURNS"
    if exit_status == 0:
        return COMPLETED_NATURALLY, "PROCESS_COMPLETED"
    return PROCESS_FAILED, "PROCESS_FAILED"


def load_events(path) -> List[dict]:
    """Re-read a persisted event stream, in order, skipping nothing silently."""
    events: List[dict] = []
    with open(str(path), "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if isinstance(event, dict):
                events.append(event)
    return events
