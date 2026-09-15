#!/usr/bin/env python3
"""The AFCI efficiency pilot's reset orchestration, budget and metrics.

Every test here is NON-LIVE. No model process is started, nothing is scored, and
no pilot observation is produced: the launcher is a fake that replays a scripted
event stream and the context audit is injected. What is exercised is the
orchestration — which processes are started, with what, in what order, and what
is refused — which is exactly the part a live run would be the worst way to test.

Organised as the freeze requires:

* 1-16   the two-phase structure and the frozen budget
* 17-24  the checkpoint predicate, and what may NOT trigger it
* 25-34  preservation, phase isolation and backward compatibility
* 35-36  the two regressions this package must not undo
* O1-O9  the metric extractor, validated against real recorded shapes
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import pytest

HARNESS = Path(__file__).resolve().parents[1]
if str(HARNESS) not in sys.path:
    sys.path.insert(0, str(HARNESS))

import checkpoint_detector as cd  # noqa: E402
import condition_prompt as cp  # noqa: E402
import efficiency_metrics as em  # noqa: E402
import efficiency_run_plan as rp  # noqa: E402
import model_adapter as ma  # noqa: E402
import reset_budget as rb  # noqa: E402
import reset_orchestration as ro  # noqa: E402
import run_artifacts as art  # noqa: E402
import run_governance as gov  # noqa: E402
import stream_launcher as sl  # noqa: E402

PURPOSE = "AFCI_EFFICIENCY_PILOT"
MODEL = "claude-sonnet-5"
RUNTIME = "2.1.229"
CI = "npm run ci:agent"


# --------------------------------------------------------------------------- #
# Event builders — the shapes the runtime really emits, kept in one place.
# --------------------------------------------------------------------------- #
def init_event(version: str = RUNTIME, model: str = MODEL) -> dict:
    return {
        "type": "system",
        "subtype": "init",
        "claude_code_version": version,
        "model": model,
        "skills": [],
        "slash_commands": [],
        "plugins": [],
        "mcp_servers": [],
    }


def assistant(blocks: Sequence[dict], mid: str, usage: Optional[dict] = None) -> dict:
    return {
        "type": "assistant",
        "message": {
            "id": mid,
            "role": "assistant",
            "content": list(blocks),
            "usage": usage
            or {
                "input_tokens": 1,
                "cache_creation_input_tokens": 100,
                "cache_read_input_tokens": 1000,
                "output_tokens": 2,
            },
        },
    }


def tool_use(name: str, tid: str, **payload) -> dict:
    return {"type": "tool_use", "id": tid, "name": name, "input": dict(payload)}


def tool_result(tid: str, *, is_error: bool = False, content: str = "ok") -> dict:
    return {
        "type": "user",
        "message": {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tid,
                    "is_error": is_error,
                    "content": content,
                }
            ],
        },
    }


def result_event(
    *,
    subtype: str = "success",
    input_tokens: int = 10,
    cache_creation: int = 2000,
    cache_read: int = 50000,
    output_tokens: int = 500,
    cost: float = 0.25,
    model: str = MODEL,
    num_turns: int = 5,
) -> dict:
    return {
        "type": "result",
        "subtype": subtype,
        "is_error": subtype != "success",
        "num_turns": num_turns,
        "duration_ms": 1000,
        "duration_api_ms": 900,
        "session_id": "sess",
        "stop_reason": None,
        "permission_denials": [],
        "usage": {
            "input_tokens": input_tokens,
            "cache_creation_input_tokens": cache_creation,
            "cache_read_input_tokens": cache_read,
            "output_tokens": output_tokens,
            "cache_creation": {
                # A BREAKDOWN of cache_creation_input_tokens, summing to it
                # exactly — the shape observed on every real artifact.
                "ephemeral_1h_input_tokens": cache_creation // 2,
                "ephemeral_5m_input_tokens": cache_creation - cache_creation // 2,
            },
        },
        "modelUsage": {
            model: {
                "inputTokens": input_tokens,
                "cacheCreationInputTokens": cache_creation,
                "cacheReadInputTokens": cache_read,
                "outputTokens": output_tokens,
                "costUSD": cost,
                "canonicalModel": model,
                "provider": "firstParty",
            }
        },
        "total_cost_usd": cost,
    }


#: A phase-A stream that edits, then runs ci:agent, then would keep going.
def phase_a_stream() -> List[dict]:
    return [
        init_event(),
        assistant([tool_use("Read", "t1", file_path="/w/apps/api/src/app.ts")], "m1"),
        tool_result("t1"),
        assistant([tool_use("Edit", "t2", file_path="/w/apps/api/src/app.ts")], "m2"),
        tool_result("t2"),
        assistant([tool_use("Bash", "t3", command=CI)], "m3"),
        tool_result("t3", is_error=True, content="1 failing test"),
        # Never reached: the checkpoint stops the stream at the event above.
        assistant([tool_use("Edit", "t4", file_path="/w/apps/api/src/app.ts")], "m4"),
        tool_result("t4"),
        result_event(),
    ]


def phase_b_stream() -> List[dict]:
    return [
        init_event(),
        assistant([tool_use("Read", "u1", file_path="/w/apps/api/src/app.ts")], "n1"),
        tool_result("u1"),
        assistant([tool_use("Write", "u2", file_path="/w/libs/core/src/x.ts")], "n2"),
        tool_result("u2"),
        assistant([tool_use("Bash", "u3", command=CI)], "n3"),
        tool_result("u3", content="all green"),
        result_event(input_tokens=5, cache_creation=1000, cache_read=20000,
                     output_tokens=300, cost=0.1),
    ]


# --------------------------------------------------------------------------- #
# Fakes
# --------------------------------------------------------------------------- #
class FakeAudit:
    def __init__(self, verdict: str = "CLEAN") -> None:
        self.verdict = verdict

    def to_dict(self) -> dict:
        return {"contamination": {"verdict": self.verdict, "reasons": []}}


class AuditProvider:
    """Records every audit it was asked for, and answers with a scripted verdict."""

    def __init__(self, verdicts: Optional[Sequence[str]] = None) -> None:
        self.verdicts = list(verdicts or [])
        self.calls: List[dict] = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        verdict = self.verdicts.pop(0) if self.verdicts else "CLEAN"
        return FakeAudit(verdict)


class FakeLauncher:
    """Replays a scripted stream through the real checkpoint plumbing.

    Deliberately NOT a stub that returns a canned outcome: it runs the caller's
    checkpoint callback over the events in order and stops where the callback
    says to, which is the behaviour under test.
    """

    #: Every launcher the factory built, in construction order.
    instances: List["FakeLauncher"] = []

    def __init__(self, scripts: List[List[dict]]):
        self.scripts = scripts
        self.built: List[dict] = []
        self.plans: List[ma.LaunchPlan] = []
        self.files_written: List[Path] = []

    def factory(self, **kwargs):
        launcher = _FakeInstance(self, kwargs, self.scripts.pop(0))
        self.built.append(kwargs)
        return launcher


class _FakeInstance:
    def __init__(self, owner: FakeLauncher, kwargs: dict, events: List[dict]) -> None:
        self.owner = owner
        self.kwargs = kwargs
        self.events = events

    def __call__(self, plan: ma.LaunchPlan) -> sl.StreamOutcome:
        self.owner.plans.append(plan)
        evidence = Path(self.kwargs["evidence_path"])
        evidence.parent.mkdir(parents=True, exist_ok=True)
        checkpoint = self.kwargs.get("checkpoint")
        kept: List[dict] = []
        stop_index: Optional[int] = None
        for index, event in enumerate(self.events):
            kept.append(event)
            if checkpoint is not None and checkpoint(index, event):
                stop_index = index
                break
        evidence.write_text(
            "\n".join(json.dumps(e, sort_keys=True) for e in kept) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        # Simulate the model's edits surviving the stop: a real phase A leaves
        # files behind, and the orchestration refuses an empty worktree.
        cwd = Path(self.kwargs["cwd"])
        cwd.mkdir(parents=True, exist_ok=True)
        marker = cwd / f"written_by_{plan.session_id_marker}.txt"
        marker.write_text("model output\n", encoding="utf-8")
        self.owner.files_written.append(marker)

        terminal = sl.terminal_result(kept)
        completion, status = sl._classify(
            stopped_early=stop_index is not None,
            terminal=terminal,
            exit_status=0 if terminal else 0,
        )
        return sl.StreamOutcome(
            invoked=True,
            status=status,
            exit_status=0,
            events=kept,
            event_count=len(kept),
            runtime_evidence_path=str(evidence),
            stderr_path=str(evidence.with_suffix(".stderr.txt")),
            termination_method=(
                sl.CTRL_BREAK_PROCESS_GROUP if stop_index is not None
                else sl.NOT_TERMINATED
            ),
            completion=completion,
            stopped_early=stop_index is not None,
            stop_event_index=stop_index,
            wall_seconds=1.0,
            terminal_result=terminal,
        )


# A LaunchPlan carries no session id field of its own; the tests need one to
# name the fake's output file, so it is derived from the argv the plan holds.
def _session_id_marker(self: ma.LaunchPlan) -> str:
    argv = list(self.argv)
    if "--session-id" in argv:
        return argv[argv.index("--session-id") + 1][:8]
    return "nosession"


ma.LaunchPlan.session_id_marker = property(_session_id_marker)  # type: ignore[attr-defined]


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    work = tmp_path / "worktree"
    work.mkdir()
    (work / "package.json").write_text("{}", encoding="utf-8")
    return work


@pytest.fixture
def credential(tmp_path: Path) -> Path:
    path = tmp_path / ".credentials.json"
    path.write_text('{"fake": true}', encoding="utf-8")
    return path


def make_inputs(
    tmp_path: Path,
    workspace: Path,
    credential: Path,
    *,
    condition: str = "C1",
    task_id: str = "PT01",
    scripts: Optional[List[List[dict]]] = None,
    audit: Optional[AuditProvider] = None,
) -> tuple:
    fake = FakeLauncher(scripts or [phase_a_stream(), phase_b_stream()])
    provider = audit or AuditProvider()
    inputs = ro.ResetInputs(
        run_purpose=PURPOSE,
        task_id=task_id,
        task_sha256=gov.expected_task_sha256(task_id),
        task_body=gov.public_task_path(task_id).read_bytes(),
        condition=condition,
        model_id=MODEL,
        runtime_version=RUNTIME,
        worktree=workspace,
        artifact_dir=tmp_path / "artifacts",
        sterile_base=tmp_path / "sterile",
        credential_source=credential,
        launcher_executable="claude",
        canonical_repo=gov.REPO,
        governed_root=tmp_path,
        permission_mode=ma.DIAGNOSTIC_PERMISSION_MODE,
        tools=ma.DIAGNOSTIC_TOOLS,
        allowed_tools=ma.bash_allow_rule(CI),
        launcher_factory=fake.factory,
        audit_provider=provider,
    )
    return inputs, fake, provider


# =========================================================================== #
# 1-16. The two-phase structure and the frozen budget
# =========================================================================== #
def test_01_non_reset_launches_exactly_one_process():
    budget = rb.turn_budget(run_purpose=PURPOSE, reset_state=rb.NON_RESET)
    assert budget.phase is None
    block = rb.budget_block(run_purpose=PURPOSE, reset_state=rb.NON_RESET)
    assert block["single_process"] is True
    assert block["pre_reset_turn_limit"] is None


def test_02_reset_launches_exactly_two_processes(tmp_path, workspace, credential):
    inputs, fake, _ = make_inputs(tmp_path, workspace, credential)
    outcome = ro.run_reset(inputs)
    assert outcome.status == ro.RESET_COMPLETE
    assert len(fake.built) == 2, "a reset is two processes, never one and never three"


def test_03_phase_session_ids_differ(tmp_path, workspace, credential):
    inputs, _, _ = make_inputs(tmp_path, workspace, credential)
    outcome = ro.run_reset(inputs)
    assert outcome.phase_a.session_id != outcome.phase_b.session_id
    assert outcome.to_dict()["fresh_phase_b_session"] is True


def test_04_phase_b_gets_a_fresh_profile(tmp_path, workspace, credential):
    inputs, _, _ = make_inputs(tmp_path, workspace, credential)
    outcome = ro.run_reset(inputs)
    assert outcome.phase_a.profile_dir != outcome.phase_b.profile_dir
    assert outcome.phase_a.home_dir != outcome.phase_b.home_dir
    assert outcome.to_dict()["fresh_phase_b_profile"] is True


def test_05_no_resume_appears_in_either_phase(tmp_path, workspace, credential):
    inputs, fake, _ = make_inputs(tmp_path, workspace, credential)
    ro.run_reset(inputs)
    for plan in fake.plans:
        argv = list(plan.argv)
        assert "--resume" not in argv and "-r" not in argv
        assert "--from-pr" not in argv
    assert ro.ResetOutcome(status="x").to_dict()["resume_used"] is False


def test_06_no_continue_appears_in_either_phase(tmp_path, workspace, credential):
    inputs, fake, _ = make_inputs(tmp_path, workspace, credential)
    ro.run_reset(inputs)
    for plan in fake.plans:
        argv = list(plan.argv)
        assert "--continue" not in argv and "-c" not in argv
        assert "--no-session-persistence" in argv


def test_07_both_phases_run_in_the_same_worktree(tmp_path, workspace, credential):
    inputs, fake, _ = make_inputs(tmp_path, workspace, credential)
    outcome = ro.run_reset(inputs)
    assert outcome.phase_a.worktree == outcome.phase_b.worktree
    assert outcome.to_dict()["same_worktree_across_reset"] is True
    assert {str(Path(k["cwd"]).resolve()) for k in fake.built} == {
        str(workspace.resolve())
    }


def test_08_the_conversation_is_not_transferred(tmp_path, workspace, credential):
    """Phase B's prompt carries the task, and NOTHING phase A said or did."""
    inputs, fake, _ = make_inputs(tmp_path, workspace, credential)
    ro.run_reset(inputs)
    phase_b_prompt = (tmp_path / "artifacts" / "prompts" / "phase_b_prompt.md").read_text(
        encoding="utf-8"
    )
    assert cp.CONTINUATION_WORDING in phase_b_prompt
    for leaked in ("t1", "t2", "t3", "1 failing test", "app.ts"):
        assert leaked not in phase_b_prompt, f"phase A detail {leaked!r} leaked forward"
    assert ro.ResetOutcome(status="x").to_dict()["conversation_reused"] is False
    assert ro.ResetOutcome(status="x").to_dict()[
        "phase_a_summarised_into_phase_b"
    ] is False


def test_09_c1_phase_a_carries_no_architecture(tmp_path, workspace, credential):
    inputs, _, _ = make_inputs(tmp_path, workspace, credential, condition="C1")
    outcome = ro.run_reset(inputs)
    assert outcome.phase_a.prompt_manifest["architecture_sha256_delivered"] is None
    prompt = (tmp_path / "artifacts" / "prompts" / "phase_a_prompt.md").read_text(
        encoding="utf-8"
    )
    assert cp.ARCHITECTURE_HEADER not in prompt


def test_10_c1_phase_b_carries_no_architecture(tmp_path, workspace, credential):
    inputs, _, _ = make_inputs(tmp_path, workspace, credential, condition="C1")
    outcome = ro.run_reset(inputs)
    assert outcome.phase_b.prompt_manifest["architecture_sha256_delivered"] is None
    prompt = (tmp_path / "artifacts" / "prompts" / "phase_b_prompt.md").read_text(
        encoding="utf-8"
    )
    assert cp.ARCHITECTURE_HEADER not in prompt


def test_11_c4_phase_a_carries_the_exact_architecture_hash(
    tmp_path, workspace, credential
):
    inputs, _, _ = make_inputs(tmp_path, workspace, credential, condition="C4")
    outcome = ro.run_reset(inputs)
    assert outcome.phase_a.prompt_manifest["architecture_sha256_delivered"] == (
        gov.architecture_context_sha256()
    )


def test_12_c4_phase_b_re_injects_the_same_architecture_hash(
    tmp_path, workspace, credential
):
    inputs, _, _ = make_inputs(tmp_path, workspace, credential, condition="C4")
    outcome = ro.run_reset(inputs)
    a = outcome.phase_a.prompt_manifest["architecture_sha256_delivered"]
    b = outcome.phase_b.prompt_manifest["architecture_sha256_delivered"]
    assert a == b == gov.architecture_context_sha256()


def test_13_phase_a_max_turns_is_32(tmp_path, workspace, credential):
    inputs, fake, _ = make_inputs(tmp_path, workspace, credential)
    outcome = ro.run_reset(inputs)
    assert outcome.phase_a.max_turns == 32
    argv = list(fake.plans[0].argv)
    assert argv[argv.index("--max-turns") + 1] == "32"


def test_14_phase_b_max_turns_is_32(tmp_path, workspace, credential):
    inputs, fake, _ = make_inputs(tmp_path, workspace, credential)
    outcome = ro.run_reset(inputs)
    assert outcome.phase_b.max_turns == 32
    argv = list(fake.plans[1].argv)
    assert argv[argv.index("--max-turns") + 1] == "32"


def test_15_non_reset_max_turns_is_64():
    assert rb.turn_budget(
        run_purpose=PURPOSE, reset_state=rb.NON_RESET
    ).max_turns == 64
    assert rb.NON_RESET_MAX_TURNS == rb.PRE_RESET_MAX_TURNS + rb.POST_RESET_MAX_TURNS


@pytest.mark.parametrize("consumed", [0, 1, 17, 31, 32])
def test_16_post_allowance_never_depends_on_phase_a_consumption(consumed):
    """32, whatever phase A spent. The allowance is frozen; use is observational."""
    budget = rb.turn_budget(
        run_purpose=PURPOSE, reset_state=rb.RESET, phase=rb.PHASE_B
    )
    assert budget.max_turns == 32
    # There is no parameter through which consumption could reach it.
    assert "consumed" not in rb.turn_budget.__code__.co_varnames
    assert rb.budget_block(run_purpose=PURPOSE, reset_state=rb.RESET)[
        "unused_pre_reset_transfers"
    ] is False


# =========================================================================== #
# 17-24. The checkpoint predicate, and what may NOT trigger it
# =========================================================================== #
def test_17_the_detector_uses_the_exact_selected_predicate():
    assert cd.FALLBACK_CHECKPOINT_PREDICATE == (
        "The first agent-initiated `npm run ci:agent` invocation after at least "
        "one implementation edit to the working tree."
    )
    assert cd.CHECKPOINT_AUTHORITY == "SL-V2-EFF-CHK-01"
    # One predicate for all three instruments; no per-task variant exists.
    assert cd.CHECKPOINT_TASKS == ("PT01", "PT04", "PT07")


def test_18_an_edit_must_precede_the_matching_ci_invocation():
    """ci:agent BEFORE any edit is the agent looking at a red baseline."""
    events = [
        init_event(),
        assistant([tool_use("Bash", "b0", command=CI)], "m0"),
        tool_result("b0"),
        assistant([tool_use("Edit", "e1", file_path="/w/a.ts")], "m1"),
        tool_result("e1"),
        assistant([tool_use("Bash", "b1", command=CI)], "m2"),
        tool_result("b1"),
    ]
    evidence = cd.detect_over(events, ci_command=CI)
    assert evidence.checkpoint_reached is True
    # It fired on the SECOND invocation, the first one after an edit.
    assert evidence.matching_ci_agent_tool_use_id == "b1"


def test_19_a_bash_tool_use_alone_does_not_trigger_the_checkpoint():
    """Stopping on the REQUEST would kill npm mid-flight."""
    detector = cd.CiAgentAfterEditDetector(ci_command=CI)
    stream = [
        init_event(),
        assistant([tool_use("Edit", "e1", file_path="/w/a.ts")], "m1"),
        tool_result("e1"),
        assistant([tool_use("Bash", "b1", command=CI)], "m2"),
    ]
    fired = [detector.observe(i, e) for i, e in enumerate(stream)]
    assert not any(fired), "the checkpoint fired before the command returned"
    assert detector.evidence.matching_ci_agent_tool_use_id == "b1"
    assert detector.evidence.matching_ci_agent_result_seen is False
    assert detector.reached is False


def test_20_the_matching_tool_result_triggers_the_checkpoint():
    detector = cd.CiAgentAfterEditDetector(ci_command=CI)
    stream = [
        init_event(),
        assistant([tool_use("Edit", "e1", file_path="/w/a.ts")], "m1"),
        tool_result("e1"),
        assistant([tool_use("Bash", "b1", command=CI)], "m2"),
        tool_result("b1"),
    ]
    fired = [detector.observe(i, e) for i, e in enumerate(stream)]
    assert fired == [False, False, False, False, True]
    assert detector.evidence.checkpoint_event_index == 4
    assert detector.evidence.matching_ci_agent_event_index == 3


@pytest.mark.parametrize(
    "command",
    [
        "npm run ci",
        "npm test",
        "npm run build",
        "npm run ci:agent:watch",
        "echo npm-run-ci:agent",
        "npm run lint",
    ],
)
def test_21_a_different_bash_command_does_not_trigger(command):
    events = [
        init_event(),
        assistant([tool_use("Edit", "e1", file_path="/w/a.ts")], "m1"),
        tool_result("e1"),
        assistant([tool_use("Bash", "b1", command=command)], "m2"),
        tool_result("b1"),
    ]
    assert cd.detect_over(events, ci_command=CI).checkpoint_reached is False


@pytest.mark.parametrize(
    "command", ["npm run ci:agent", "npm run ci:agent 2>&1", "npm  run   ci:agent"]
)
def test_21b_the_real_command_shapes_do_trigger(command):
    events = [
        init_event(),
        assistant([tool_use("Edit", "e1", file_path="/w/a.ts")], "m1"),
        tool_result("e1"),
        assistant([tool_use("Bash", "b1", command=command)], "m2"),
        tool_result("b1"),
    ]
    assert cd.detect_over(events, ci_command=CI).checkpoint_reached is True


def test_22_an_architecture_result_cannot_trigger_the_checkpoint():
    """The score is produced out of band and the detector never sees one."""
    events = [
        init_event(),
        assistant([tool_use("Edit", "e1", file_path="/w/a.ts")], "m1"),
        tool_result("e1"),
        {
            "type": "system",
            "subtype": "architecture_score",
            "violations": 0,
            "score": 1.0,
        },
        {"type": "result", "subtype": "success", "architecture_violations": 0},
    ]
    assert cd.detect_over(events, ci_command=CI).checkpoint_reached is False


def test_23_a_hidden_functional_result_cannot_trigger_the_checkpoint():
    events = [
        init_event(),
        assistant([tool_use("Edit", "e1", file_path="/w/a.ts")], "m1"),
        tool_result("e1"),
        {"type": "user", "message": {"role": "user", "content": [
            {"type": "text", "text": "acceptance_result: PASS 4/4"}
        ]}},
    ]
    assert cd.detect_over(events, ci_command=CI).checkpoint_reached is False


def test_24_model_prose_cannot_trigger_the_checkpoint():
    """A model that SAYS it ran CI has not run CI."""
    events = [
        init_event(),
        assistant([tool_use("Edit", "e1", file_path="/w/a.ts")], "m1"),
        tool_result("e1"),
        assistant(
            [{"type": "text", "text": "Now running `npm run ci:agent` to validate."}],
            "m2",
        ),
        assistant([{"type": "text", "text": "npm run ci:agent passed."}], "m3"),
    ]
    assert cd.detect_over(events, ci_command=CI).checkpoint_reached is False
    assert "text" not in "".join(cd.readable_fields())


def test_24b_the_detector_is_identical_for_c1_and_c4():
    """The condition is not an input, so it cannot be a difference."""
    import inspect

    signature = inspect.signature(cd.CiAgentAfterEditDetector.__init__)
    assert "condition" not in signature.parameters
    assert "condition" not in inspect.signature(cd.detect_over).parameters


# =========================================================================== #
# 25-34. Preservation, phase isolation and backward compatibility
# =========================================================================== #
def test_25_the_checkpoint_stop_preserves_the_worktree(
    tmp_path, workspace, credential
):
    inputs, fake, _ = make_inputs(tmp_path, workspace, credential)
    before = sorted(p.name for p in workspace.iterdir())
    outcome = ro.run_reset(inputs)
    after = sorted(p.name for p in workspace.iterdir())
    assert outcome.status == ro.RESET_COMPLETE
    assert set(before).issubset(set(after)), "the reset removed pre-existing files"
    assert len(fake.files_written) == 2
    for marker in fake.files_written:
        assert marker.is_file(), "a phase's output did not survive the handoff"


def test_26_a_second_context_audit_is_required(tmp_path, workspace, credential):
    inputs, _, provider = make_inputs(tmp_path, workspace, credential)
    outcome = ro.run_reset(inputs)
    assert len(provider.calls) == 2, "phase B was not audited"
    assert outcome.phase_a.context_audit_verdict == "CLEAN"
    assert outcome.phase_b.context_audit_verdict == "CLEAN"
    assert (tmp_path / "artifacts" / "phase_a_context_audit.json").is_file()
    assert (tmp_path / "artifacts" / "phase_b_context_audit.json").is_file()


def test_27_a_contaminated_phase_b_refuses(tmp_path, workspace, credential):
    provider = AuditProvider(["CLEAN", "CONTAMINATED"])
    inputs, _, _ = make_inputs(tmp_path, workspace, credential, audit=provider)
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        ro.run_reset(inputs)
    assert excinfo.value.code == gov.CONTEXT_AUDIT_CONTAMINATED


def test_27b_a_contaminated_phase_a_refuses_before_phase_b(
    tmp_path, workspace, credential
):
    provider = AuditProvider(["CONTAMINATED"])
    inputs, fake, _ = make_inputs(tmp_path, workspace, credential, audit=provider)
    with pytest.raises(gov.RunnerRefusal):
        ro.run_reset(inputs)
    assert fake.built == [], "a process was started after a contaminated audit"


def _phase(**overrides) -> ro.PhaseRecord:
    base = dict(
        phase="A", session_id="s-a", profile_dir="/cfg/a", home_dir="/home/a",
        worktree="/w", max_turns=32, model_id=MODEL, runtime_version=RUNTIME,
        condition="C4", task_id="PT01", task_sha256="a" * 64,
        prompt_manifest={"architecture_sha256_delivered": "x" * 64},
        context_audit_verdict="CLEAN", context_audit_path=None,
        runtime_evidence_path="/e", event_count=1, completion="x",
        termination_method="y", exit_status=0, turns_used=1,
        hit_turn_ceiling=False, model_seconds=1.0,
    )
    base.update(overrides)
    return ro.PhaseRecord(**base)


def test_28_the_model_cannot_change_between_phases():
    a = _phase()
    b = _phase(phase="B", session_id="s-b", profile_dir="/cfg/b",
               model_id="claude-opus-5")
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        ro._assert_phases_consistent(a, b)
    assert excinfo.value.code == gov.RESET_PHASE_MODEL_CHANGED


def test_29_the_runtime_cannot_change_between_phases():
    a = _phase()
    b = _phase(phase="B", session_id="s-b", profile_dir="/cfg/b",
               runtime_version="2.1.224")
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        ro._assert_phases_consistent(a, b)
    assert excinfo.value.code == gov.RESET_PHASE_RUNTIME_CHANGED


def test_30_the_condition_cannot_change_between_phases():
    a = _phase()
    b = _phase(phase="B", session_id="s-b", profile_dir="/cfg/b", condition="C1")
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        ro._assert_phases_consistent(a, b)
    assert excinfo.value.code == gov.RESET_PHASE_CONDITION_CHANGED


def test_31_the_task_cannot_change_between_phases():
    a = _phase()
    for override in ({"task_id": "PT04"}, {"task_sha256": "b" * 64}):
        b = _phase(phase="B", session_id="s-b", profile_dir="/cfg/b", **override)
        with pytest.raises(gov.RunnerRefusal) as excinfo:
            ro._assert_phases_consistent(a, b)
        assert excinfo.value.code == gov.RESET_PHASE_TASK_CHANGED


def test_31b_the_architecture_payload_cannot_change_between_phases():
    a = _phase()
    b = _phase(phase="B", session_id="s-b", profile_dir="/cfg/b",
               prompt_manifest={"architecture_sha256_delivered": "z" * 64})
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        ro._assert_phases_consistent(a, b)
    assert excinfo.value.code == gov.RESET_PHASE_ARCHITECTURE_CHANGED


def test_31c_a_reused_session_or_profile_refuses():
    a = _phase()
    same_session = _phase(phase="B", profile_dir="/cfg/b")
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        ro._assert_phases_consistent(a, same_session)
    assert excinfo.value.code == gov.RESET_PHASE_SESSION_REUSED

    same_profile = _phase(phase="B", session_id="s-b")
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        ro._assert_phases_consistent(a, same_profile)
    assert excinfo.value.code == gov.RESET_PHASE_PROFILE_REUSED


def test_31d_a_different_worktree_refuses():
    a = _phase()
    b = _phase(phase="B", session_id="s-b", profile_dir="/cfg/b", worktree="/other")
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        ro._assert_phases_consistent(a, b)
    assert excinfo.value.code == gov.RESET_WORKTREE_NOT_PRESERVED


def test_32_checkpoint_not_reached_produces_the_right_state(
    tmp_path, workspace, credential
):
    """Phase A exhausts its allowance without ever running ci:agent."""
    never = [
        init_event(),
        assistant([tool_use("Read", "r1", file_path="/w/a.ts")], "m1"),
        tool_result("r1"),
        assistant([tool_use("Edit", "e1", file_path="/w/a.ts")], "m2"),
        tool_result("e1"),
        result_event(subtype="error_max_turns", num_turns=33),
    ]
    inputs, fake, _ = make_inputs(
        tmp_path, workspace, credential, scripts=[never, phase_b_stream()]
    )
    outcome = ro.run_reset(inputs)
    assert outcome.status == gov.RESET_CHECKPOINT_NOT_REACHED
    assert outcome.checkpoint_reached is False
    assert outcome.phase_b is None
    assert len(fake.built) == 1, "a phase B was fabricated"
    block = outcome.to_dict()
    assert block["phase_b_session_id"] is None
    assert block["post_reset_turns_used"] is None
    # The frozen post-reset allowance is still REPORTED: it was frozen in
    # advance and does not become undefined because phase B never happened.
    assert block["post_reset_turn_limit"] == 32
    assert outcome.phase_a.hit_turn_ceiling is True


def test_33_there_is_no_automatic_rerun(tmp_path, workspace, credential):
    """A checkpoint-not-reached outcome is returned, never retried."""
    never = [
        init_event(),
        assistant([tool_use("Edit", "e1", file_path="/w/a.ts")], "m1"),
        tool_result("e1"),
        result_event(subtype="error_max_turns", num_turns=33),
    ]
    inputs, fake, provider = make_inputs(
        tmp_path, workspace, credential, scripts=[never]
    )
    outcome = ro.run_reset(inputs)
    assert outcome.status == gov.RESET_CHECKPOINT_NOT_REACHED
    assert len(fake.built) == 1 and len(provider.calls) == 1
    # No larger budget was requested on the way out.
    assert outcome.phase_a.max_turns == rb.PRE_RESET_MAX_TURNS


def test_34_old_diagnostic_records_still_validate():
    """A record written before this package must validate UNCHANGED.

    Built the way the earlier purposes build one — no reset block, no efficiency
    block, no allowlist, no turn ceiling — and validated against the schema this
    package edited.
    """
    purpose = gov.RUN_PURPOSES["PT08_DIFFICULTY_DIAGNOSTIC"]
    record = art.build_run_record(
        purpose=purpose,
        run_id="legacy",
        task_id="PT08",
        task_sha256="c" * 64,
        condition="C1",
        mode="dry-run",
        state_log=[{"state": "PRECHECK", "result": "PASS", "code": None, "detail": ""}],
        model={
            "requested_model_id": None, "resolved_model_id": None,
            "effort_input": None, "selection_status": "X",
        },
        environment=art.environment_block(),
        worktree={"enforcement": {}, "prepared_root": "", "prepared_manifest_path": "",
                  "content_hash": ""},
        context_audit={"verdict": "CLEAN", "report_path": None,
                       "report_sha256": None, "reason_count": 0},
        fresh_launch={"argv": [], "executable": False, "session_handling": "x",
                      "manifest_path": None},
        invocation={"invoked": False, "status": "X", "exit_status": None,
                    "runtime_evidence_path": None},
        model_identity={"status": "X", "requested_model_id": None,
                        "resolved_model_id": None},
        post_run_capture=None,
        evaluation={},
        manifest_freeze={},
        artifacts={},
        prerequisite_blockers=[],
        outcome={"status": "DRY_RUN_COMPLETE", "code": None, "detail": "",
                 "is_result": False, "scored": False},
    )
    assert "reset" not in record, "a legacy record grew a reset block"
    assert "efficiency" not in record
    art.validate_run_record(record)  # refuses rather than warns


def test_34b_a_pilot_record_validates_with_both_new_blocks():
    purpose = gov.RUN_PURPOSES[PURPOSE]
    record = art.build_run_record(
        purpose=purpose,
        run_id="pilot",
        task_id="PT01",
        task_sha256=gov.expected_task_sha256("PT01"),
        condition="C4",
        mode="real",
        repetition=2,
        state_log=[{"state": "PRECHECK", "result": "PASS", "code": None, "detail": ""}],
        model={
            "requested_model_id": MODEL, "resolved_model_id": MODEL,
            "effort_input": None, "selection_status": "PINNED",
        },
        environment=art.environment_block(observed_cli_version=RUNTIME),
        worktree={"enforcement": {}, "prepared_root": "", "prepared_manifest_path": "",
                  "content_hash": ""},
        context_audit={"verdict": "CLEAN", "report_path": None,
                       "report_sha256": None, "reason_count": 0},
        fresh_launch={
            "argv": [], "executable": True, "session_handling": "x",
            "manifest_path": None,
            "allowed_tools": list(ma.bash_allow_rule(CI)),
            "tools": list(ma.DIAGNOSTIC_TOOLS),
            "max_turns": None,
        },
        invocation={
            "invoked": True, "status": "RESET_COMPLETE", "exit_status": 0,
            "runtime_evidence_path": "/e", "termination_method": "CTRL_BREAK",
            "completion": "STOPPED_AT_CHECKPOINT", "stopped_early": True,
            "stop_event_index": 6, "max_turns_reached": False, "event_count": 7,
        },
        model_identity={"status": "VALIDATED", "requested_model_id": MODEL,
                        "resolved_model_id": MODEL},
        post_run_capture=None,
        evaluation={},
        manifest_freeze={},
        artifacts={},
        prerequisite_blockers=[],
        outcome={"status": "COMPLETE", "code": None, "detail": "",
                 "is_result": False, "scored": False},
        reset=ro.ResetOutcome(
            status=ro.RESET_COMPLETE,
            checkpoint={"checkpoint_id": cd.CHECKPOINT_ID, "checkpoint_reached": True},
        ).to_dict(),
        efficiency={"reset_state": rb.RESET, "usage": {"TOTAL_INPUT_TOKENS": 1}},
    )
    assert record["reset"]["reset_state"] == rb.RESET
    assert record["efficiency"]["usage"]["TOTAL_INPUT_TOKENS"] == 1
    art.validate_run_record(record)


# =========================================================================== #
# 35-36. The two regressions this package must not undo
# =========================================================================== #
def test_35_streaming_delivers_utf8_including_a_unicode_arrow(tmp_path):
    """The prompt is UTF-8 whatever the host locale says.

    The regression this pins: text mode alone encodes stdin with the process
    locale, which on this host is cp1252, so a task body containing an arrow
    raised UnicodeEncodeError while WRITING THE PROMPT — the model then received
    empty stdin, emitted no system.init, and the repetition was invalid.
    """
    body = "Implement the mapping A → B, costing €5 — see “spec”.\n"
    prompt = cp.compose_task_prompt("C1", body.encode("utf-8"))
    assert prompt == body
    path = tmp_path / "p.md"
    path.write_text(prompt, encoding="utf-8", newline="\n")
    assert path.read_text(encoding="utf-8") == body
    assert "→" in path.read_text(encoding="utf-8")
    # The launcher pins the encoding rather than inheriting it.
    source = (HARNESS / "stream_launcher.py").read_text(encoding="utf-8")
    assert 'encoding="utf-8"' in source
    with pytest.raises(UnicodeEncodeError):
        body.encode("cp1252")


def test_35b_c4_prompt_survives_a_unicode_round_trip(tmp_path):
    body = "Handle the ↔ case.\n"
    prompt = cp.compose_task_prompt("C4", body.encode("utf-8"))
    path = tmp_path / "p4.md"
    path.write_text(prompt, encoding="utf-8", newline="\n")
    reread = path.read_text(encoding="utf-8")
    assert cp.architecture_payload_sha256(reread) == gov.architecture_context_sha256()
    assert reread.endswith(body)


def test_36_the_real_run_completion_line_stays_correct():
    """The sentence reports the OBSERVATION, never the intention."""
    import run_v2

    class Outcome:
        def __init__(self, record):
            self.record = record

    invoked = Outcome({"invocation": {"invoked": True}, "outcome": {"scored": False}})
    assert run_v2.completion_line(invoked, "real") == (
        "real run complete; a model process was invoked and nothing was scored"
    )
    not_invoked = Outcome({"invocation": {"invoked": False}, "outcome": {"scored": False}})
    assert run_v2.completion_line(not_invoked, "dry-run") == (
        "dry run complete; no model was invoked and nothing was scored"
    )
    assert "NO model process was started" in run_v2.completion_line(not_invoked, "real")


def test_36b_the_repetition_identity_fix_stays_intact():
    ids = {
        art.derive_run_id(
            purpose=PURPOSE, task_id="PT01", condition="C1",
            task_sha="a" * 64, substrate_hash="b" * 64, mode="real", repetition=r,
        )
        for r in (1, 2, 3)
    }
    assert len(ids) == 3, "two repetitions of one cell derived the same run id"


# =========================================================================== #
# O1-O9. The metric extractor (Part O)
# =========================================================================== #
def test_o1_usage_extraction_is_exact():
    events = [init_event(), result_event()]
    usage = em.extract_usage(events, expected_model_id=MODEL)
    assert usage.input_tokens == 10
    assert usage.cache_creation_input_tokens == 2000
    assert usage.cache_read_input_tokens == 50000
    assert usage.output_tokens == 500
    assert usage.total_input_tokens == 10 + 2000 + 50000
    assert usage.cost_usd == 0.25
    assert usage.source == em.SOURCE_TERMINAL_RESULT


def test_o2_the_ephemeral_subcomponents_are_never_added():
    """They are a BREAKDOWN of cache_creation_input_tokens, not extra tokens."""
    event = result_event()
    breakdown = event["usage"]["cache_creation"]
    assert sum(breakdown.values()) == event["usage"]["cache_creation_input_tokens"]
    usage = em.extract_usage([init_event(), event], expected_model_id=MODEL)
    assert usage.total_input_tokens == (
        event["usage"]["input_tokens"]
        + event["usage"]["cache_creation_input_tokens"]
        + event["usage"]["cache_read_input_tokens"]
    )
    naive = usage.total_input_tokens + sum(breakdown.values())
    assert usage.total_input_tokens != naive
    assert em.FORBIDDEN_USAGE_SUBCOMPONENTS == (
        "cache_creation.ephemeral_1h_input_tokens",
        "cache_creation.ephemeral_5m_input_tokens",
    )


def test_o3_the_model_usage_mirror_is_checked():
    good = em.extract_usage([result_event()], expected_model_id=MODEL)
    assert good.model_usage_mirror_consistent is True

    bad = result_event()
    bad["modelUsage"][MODEL]["cacheReadInputTokens"] = 1
    checked = em.extract_usage([bad], expected_model_id=MODEL)
    assert checked.model_usage_mirror_consistent is False
    # `usage` stays authoritative: the mirror disagreeing is REPORTED, not obeyed.
    assert checked.cache_read_input_tokens == 50000


def test_o4_unknown_event_types_are_preserved():
    events = [init_event(), {"type": "brand_new_event_type"}, result_event()]
    measurement = em.measure_non_reset(events, model_id=MODEL)
    assert measurement.to_dict()["unknown_event_types"] == ["brand_new_event_type"]


def test_o5_tool_events_are_classified():
    events = [
        init_event(),
        assistant([tool_use("Read", "a", file_path="/w/a.ts")], "m1"),
        tool_result("a"),
        assistant([tool_use("Read", "b", file_path="/w/a.ts")], "m2"),
        tool_result("b"),
        assistant([tool_use("Grep", "c", pattern="x", path="/w/libs")], "m3"),
        tool_result("c"),
        assistant([tool_use("Glob", "d", pattern="*.ts", path="/w/apps")], "m4"),
        tool_result("d"),
        assistant([tool_use("Edit", "e", file_path="/w/b.ts")], "m5"),
        tool_result("e"),
        assistant([tool_use("Edit", "f", file_path="/w/b.ts")], "m6"),
        tool_result("f"),
        assistant([tool_use("Write", "g", file_path="/w/c.ts")], "m7"),
        tool_result("g"),
        assistant([tool_use("Bash", "h", command=CI)], "m8"),
        tool_result("h", is_error=True),
        assistant([tool_use("Bash", "i", command="npm test")], "m9"),
        tool_result("i"),
        result_event(),
    ]
    tools = em.extract_tool_metrics(events, ci_command=CI)
    assert tools.read_calls == 2
    assert tools.grep_calls == 1 and tools.glob_calls == 1
    assert tools.edit_calls == 2 and tools.write_calls == 1
    assert tools.bash_calls == 2
    assert tools.total_tool_calls == 9
    assert tools.exploration_calls == 4
    assert tools.unique_files_read == 1
    assert tools.repeated_file_reads == 1
    assert tools.unique_files_modified == 2
    assert tools.files_reedited == 1
    assert tools.ci_command_runs == 1
    assert tools.test_command_runs == 1
    assert tools.failed_test_or_ci_cycles == 1


def test_o6_windows_paths_are_normalised_to_one_spelling():
    spellings = [
        r"D:\w\apps\api\src\app.ts",
        "D:/w/apps/api/src/app.ts",
        "d:/w/apps/api/src/app.ts",
        "D:/w//apps/api/src/app.ts",
    ]
    normalised = {em.normalise_path(s) for s in spellings}
    assert normalised == {"d:/w/apps/api/src/app.ts"}
    events = [init_event()]
    for index, spelling in enumerate(spellings):
        events.append(
            assistant([tool_use("Read", f"t{index}", file_path=spelling)], f"m{index}")
        )
        events.append(tool_result(f"t{index}"))
    events.append(result_event())
    tools = em.extract_tool_metrics(events, ci_command=CI)
    assert tools.read_calls == 4
    assert tools.unique_files_read == 1
    assert tools.repeated_file_reads == 3
    # Case is otherwise preserved: two genuinely different names stay two.
    assert em.normalise_path("/w/App.ts") != em.normalise_path("/w/app.ts")


def test_o7_reset_phases_aggregate_and_are_preserved():
    a = [init_event(), assistant([], "m1"), result_event(
        input_tokens=1, cache_creation=10, cache_read=100, output_tokens=7, cost=0.01)]
    b = [init_event(), assistant([], "n1"), result_event(
        input_tokens=2, cache_creation=20, cache_read=200, output_tokens=9, cost=0.02)]
    measurement = em.aggregate_reset(a, b, model_id=MODEL)
    payload = measurement.to_dict()
    assert payload["usage"]["TOTAL_INPUT_TOKENS"] == (1 + 10 + 100) + (2 + 20 + 200)
    assert payload["usage"]["TOTAL_OUTPUT_TOKENS"] == 16
    assert payload["usage"]["cost_usd"] == pytest.approx(0.03)
    assert payload["TURNS_USED"] == 2
    assert payload["phases"]["A"]["usage"]["TOTAL_INPUT_TOKENS"] == 111
    assert payload["phases"]["B"]["usage"]["TOTAL_INPUT_TOKENS"] == 222


def test_o7b_an_interrupted_phase_a_yields_exact_input_and_no_output():
    """The primary endpoint survives interruption; the secondary honestly does not."""
    complete = [init_event(), assistant([], "m1", usage={
        "input_tokens": 3, "cache_creation_input_tokens": 30,
        "cache_read_input_tokens": 300, "output_tokens": 2,
    }), result_event(input_tokens=3, cache_creation=30, cache_read=300,
                     output_tokens=900)]
    full = em.extract_usage(complete, expected_model_id=MODEL)
    partial = em.extract_partial_usage(complete[:-1])
    assert partial.total_input_tokens == full.total_input_tokens
    assert partial.output_tokens is None and partial.cost_usd is None
    assert partial.source == em.SOURCE_PER_MESSAGE_PARTIAL

    interrupted = complete[:-1]
    aggregate = em.aggregate_reset(interrupted, complete, model_id=MODEL)
    assert aggregate.usage.total_input_tokens == 333 + 333
    assert aggregate.usage.total_output_tokens is None, (
        "a partial output sum was reported as a total"
    )


def test_o8_missing_and_malformed_usage_fail_closed():
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        em.extract_usage([init_event()])
    assert excinfo.value.code == gov.EFFICIENCY_USAGE_MISSING

    no_usage = {"type": "result", "subtype": "success"}
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        em.extract_usage([no_usage])
    assert excinfo.value.code == gov.EFFICIENCY_USAGE_MISSING

    for bad in ("x", None, -1, 1.5, True):
        event = result_event()
        event["usage"]["cache_read_input_tokens"] = bad
        with pytest.raises(gov.RunnerRefusal) as excinfo:
            em.extract_usage([event])
        assert excinfo.value.code == gov.EFFICIENCY_USAGE_MALFORMED, bad

    # An interrupted stream with no assistant usage at all is invalid, not free.
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        em.extract_partial_usage([init_event()])
    assert excinfo.value.code == gov.EFFICIENCY_USAGE_MISSING


def test_o9_secrets_are_redacted_without_breaking_the_event():
    event = {
        "type": "system",
        "subtype": "error",
        "message": "auth failed for sk-ant-abcdefghijklmnop",
        "nested": {"access_token": "sk-ant-zzzzzzzzzzzzzzzz", "keep": 5},
        "list": ["Bearer abcdefghijklmnop"],
    }
    redacted = sl.redact_event(event)
    body = json.dumps(redacted)
    assert "sk-ant-abcdefghijklmnop" not in body
    assert "sk-ant-zzzzzzzzzzzzzzzz" not in body
    assert "[REDACTED]" in body
    # The STRUCTURE survives: a redacted event is still a readable event.
    assert redacted["type"] == "system"
    assert redacted["nested"]["keep"] == 5
    assert "access_token" in redacted["nested"], "a key was destroyed, not a value"
    assert json.loads(json.dumps(redacted)) == redacted


def test_o10_turns_used_is_derived_not_read_from_num_turns():
    """`num_turns` means two different things; neither is turns-used."""
    events = [
        init_event(),
        assistant([], "m1"),
        assistant([], "m1"),   # the same message, streamed twice
        assistant([], "m2"),
        result_event(num_turns=99),
    ]
    assert em.turns_used(events) == 2
    ceiling = [init_event(), assistant([], "m1"),
               result_event(subtype="error_max_turns", num_turns=2)]
    assert em.turns_used(ceiling) == 1
    assert em.hit_turn_ceiling(ceiling) is True
    assert em.hit_turn_ceiling(events) is False


# =========================================================================== #
# The frozen run plan
# =========================================================================== #
def test_plan_is_18_paired_blocks_and_36_runs():
    plan = rp.load_plan()
    assert rp.plan_problems(plan) == []
    assert plan["block_count"] == 18 and plan["run_count"] == 36
    assert plan["seed"] == "AFCI_EFFICIENCY_PILOT_V1_20260914"


def test_plan_is_deterministic_and_matches_the_committed_file():
    rebuilt = rp.build_plan()
    committed = rp.load_plan()
    assert rp.plan_sha256(rebuilt) == rp.plan_sha256(committed)
    assert rp.plan_sha256(rp.build_plan()) == rp.plan_sha256(rp.build_plan())


def test_plan_uses_no_language_rng():
    """Reproducible on another machine, another Python, or by hand.

    Asserted behaviourally rather than by grepping the source, which would only
    prove the module does not MENTION a shuffle — its docstring says exactly why
    it does not use one. What is checked instead is that the module holds no RNG
    and that a block's order key is recomputable from the seed with nothing but
    a hash function.
    """
    import hashlib

    assert "random" not in vars(rp), "the plan module holds a random module"
    blocks = rp.build_blocks()
    for block in blocks:
        expected = hashlib.sha256(
            f"{rp.SEED}|block|{block['block_id']}".encode("utf-8")
        ).hexdigest()
        assert block["order_key"] == expected
        for condition in rp.CONDITIONS:
            assert condition in block["condition_order"]
    # And the block order really is that key's order.
    assert [b["order_key"] for b in blocks] == sorted(b["order_key"] for b in blocks)


def test_plan_covers_every_cell_exactly_once():
    plan = rp.load_plan()
    cells = [
        (r["task_id"], r["condition"], r["reset_state"], r["repetition"])
        for r in plan["runs"]
    ]
    assert len(cells) == len(set(cells)) == 36
    expected = {
        (t, c, s, r)
        for t in rp.TASKS for c in rp.CONDITIONS
        for s in rp.RESET_STATES for r in rp.REPETITIONS
    }
    assert set(cells) == expected


def test_plan_carries_the_frozen_hashes():
    plan = rp.load_plan()
    assert plan["architecture_context_sha256"] == (
        "bf6f32b162a23b851596d8b489d938bef10d0b8616a50dcc039873d12ffa7a4d"
    )
    assert plan["task_sha256"]["PT01"] == (
        "6c938822fe19cd6e87942a6ee24ec8f604c0883da1b7f80d45216be35d7c9c39"
    )
    assert plan["task_sha256"]["PT04"] == (
        "f349b150b1d8fe5676fed8460b1840b988ee2bb0a78b1966ef82ae9ce9c8a9b5"
    )
    assert plan["task_sha256"]["PT07"] == (
        "557caed09420354efbc823c8b72e54b0760ac72847aba0d9c07d99e37ff7d2d7"
    )


def test_both_condition_orders_occur_across_the_blocks():
    """Within-block order is randomised, so neither arm is always first."""
    plan = rp.load_plan()
    firsts = [b["condition_order"][0] for b in plan["blocks"]]
    assert set(firsts) == {"C1", "C4"}
    assert 4 <= firsts.count("C1") <= 14, firsts.count("C1")
