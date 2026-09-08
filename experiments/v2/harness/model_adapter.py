#!/usr/bin/env python3
"""Fresh-process launch construction and the model-identity contract.

Three separable jobs, deliberately kept apart:

1. :func:`build_fresh_launch` — turn a run request into the exact argv and
   environment a genuinely **fresh** Claude process would be started with. It
   refuses every session-restoration mechanism (``--resume``, ``--continue``,
   ``--from-pr``, a reused ``--session-id``) and refuses ``--fallback-model``,
   which would let another model answer for the pinned one
   (``MODEL_EXECUTION_CONTROLS.md`` §3.1). The session guard is not
   reimplemented: the built argv is re-checked through
   :func:`context_audit.check_session_flags`, the frozen guard the reset
   protocol names.

2. :class:`ModelInvocationAdapter` — the smallest invocation boundary current
   governance needs. It **selects no model, and has no fallback**. In dry-run
   mode it never creates a process. In real mode it refuses before any process
   could be created unless a governed exact model id is supplied *and*
   ``MODEL_REGISTRY.yml`` records a selected ``primary_model`` — which it does
   not (``primary_model: null``, ``TD-B03`` open), so real invocation is
   unreachable in this repository today. The actual spawn is delegated to an
   injected ``process_launcher``; the default launcher refuses.

3. :func:`validate_model_identity` / :func:`validate_invalid_model_id_rejection`
   — the ``Q1`` readback contract and the ``Q8`` invalid-id rejection path
   (``MODEL_EXECUTION_CONTROLS.md`` §7; ``TD-B21``). Both consume runtime
   evidence; neither invents any. A dry run records the readback as
   **not performed**, never as passed.

No model is invoked and no benchmark task is executed by this module.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import context_audit as ca
import run_governance as gov

#: Flags a fresh experimental process may never carry, mapped to the refusal
#: code the runner reports. ``RESTORATION_FLAGS`` is imported from the frozen
#: guard rather than restated, so the two can never drift apart.
_RESTORATION_CODES: Dict[str, str] = {
    "--resume": gov.SESSION_RESUME_REJECTED,
    "-r": gov.SESSION_RESUME_REJECTED,
    "--continue": gov.SESSION_CONTINUE_REJECTED,
    "-c": gov.SESSION_CONTINUE_REJECTED,
    "--from-pr": gov.SESSION_RESUME_REJECTED,
}

#: Never set for a controlled run: it would let a different model answer without
#: the pinned one ever being used (MODEL_EXECUTION_CONTROLS §3.1 / §7 Q9).
_FORBIDDEN_LAUNCH_FLAGS: Dict[str, str] = {
    "--fallback-model": gov.FALLBACK_MODEL_REJECTED,
}

#: Environment every counted run pins. The isolation variables are supplied by
#: ``context_audit.make_sterile_env``; these are the determinism controls
#: MODEL_EXECUTION_CONTROLS §6 rule 4 requires.
GOVERNED_ENV: Dict[str, str] = {
    "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
    "DISABLE_AUTOUPDATER": "1",
    "CLAUDE_CODE_DISABLE_WORKFLOWS": "1",
}


@dataclass(frozen=True)
class LaunchPlan:
    """A fresh-process launch: argv, environment, and whether it may be run."""

    argv: Tuple[str, ...]
    env: Tuple[Tuple[str, str], ...]
    executable: bool
    model_id: Optional[str]
    model_status: str
    effort_input: Optional[str]
    session_handling: str

    def environment(self) -> Dict[str, str]:
        return dict(self.env)

    def launch_command(self) -> ca.LaunchCommand:
        """The audit's view of this plan (``source='argv'``: runner-built)."""
        return ca.LaunchCommand(argv=self.argv, source="argv")

    def to_dict(self) -> dict:
        return {
            "argv": list(self.argv),
            "env_keys": sorted(dict(self.env)),
            "executable": self.executable,
            "requested_model_id": self.model_id,
            "model_status": self.model_status,
            "effort_input": self.effort_input,
            "session_handling": self.session_handling,
        }

    def launch_manifest(self) -> dict:
        """The ``ART-LAUNCH`` payload: argv only, no values beyond flags."""
        return {"argv": list(self.argv)}


def _assert_no_restoration(tokens: Sequence[str]) -> None:
    for token in tokens:
        flag = token.partition("=")[0]
        code = _RESTORATION_CODES.get(flag)
        if code is not None:
            raise gov.RunnerRefusal(
                code,
                f"{flag} restores or reuses a previous session; every counted run "
                "starts a genuinely fresh process (RESET_PROTOCOL.md §2 step 7)",
            )
        forbidden = _FORBIDDEN_LAUNCH_FLAGS.get(flag)
        if forbidden is not None:
            raise gov.RunnerRefusal(
                forbidden,
                f"{flag} is never set for a controlled run: another model could "
                "answer for the pinned one and the substitution would not be a "
                "recorded control (MODEL_EXECUTION_CONTROLS §3.1)",
            )


def build_fresh_launch(
    *,
    prompt_path: str,
    workspace: str,
    model_id: Optional[str] = None,
    effort: Optional[str] = None,
    session_id: Optional[str] = None,
    previous_session_ids: Iterable[str] = (),
    sterile_env: Optional[Dict[str, str]] = None,
    extra: Sequence[str] = (),
    require_model: bool = True,
) -> LaunchPlan:
    """Build the fresh-process launch for one run, failing closed.

    ``require_model=False`` is the dry-run path: the plan is built so its
    structure can be inspected, it is marked ``executable=False``, and the model
    slot reports :data:`run_governance.MODEL_SELECTION_REQUIRED`. **No model is
    substituted, and no alias is guessed.**
    """
    _assert_no_restoration(extra)

    previous = set(previous_session_ids)
    if session_id is not None and session_id in previous:
        raise gov.RunnerRefusal(
            gov.SESSION_ID_REUSED,
            f"--session-id {session_id} has been used before; a reused session id "
            "is session reuse whatever else the command says",
        )

    argv: List[str] = ["claude", "-p", "--no-session-persistence"]
    model_status = "PINNED"
    if model_id:
        argv += ["--model", model_id]
    elif require_model:
        raise gov.RunnerRefusal(
            gov.MODEL_SELECTION_REQUIRED,
            "a real invocation requires an explicit governed exact model id; the "
            "runner never selects a model, never uses an alias and never falls "
            "back (TD-B03 / D10)",
        )
    else:
        model_status = gov.MODEL_SELECTION_REQUIRED

    if effort:
        argv += ["--effort", effort]
    # stream-json is the readback channel Q1 must be validated against; it is
    # requested as an input, never treated as evidence that a readback exists.
    argv += ["--output-format", "stream-json", "--verbose"]
    argv += ["--add-dir", workspace]
    if session_id is not None:
        argv += ["--session-id", session_id]
    argv += list(extra)
    argv += ["--", f"@{prompt_path}"]

    # Independent second gate: the frozen guard the reset protocol names.
    violations = ca.check_session_flags(argv, previous)
    if violations:
        raise gov.RunnerRefusal(
            gov.SESSION_RESUME_REJECTED,
            "the frozen session guard rejected the built launch: "
            + "; ".join(violations),
        )

    env = dict(GOVERNED_ENV)
    if sterile_env:
        env.update(sterile_env)

    return LaunchPlan(
        argv=tuple(argv),
        env=tuple(sorted(env.items())),
        executable=bool(model_id),
        model_id=model_id,
        model_status=model_status,
        effort_input=effort,
        session_handling=(
            "fresh process; --no-session-persistence; no --resume/--continue/"
            "--from-pr; " + ("fresh --session-id" if session_id else "no session id")
        ),
    )


# --------------------------------------------------------------------------- #
# Invocation adapter
# --------------------------------------------------------------------------- #
def _refusing_launcher(plan: LaunchPlan) -> "ModelInvocationOutcome":  # pragma: no cover
    raise gov.RunnerRefusal(
        gov.REAL_INVOCATION_NOT_ENABLED,
        "no process launcher is configured; this repository ships no path that "
        "can start a paid model run, and one must be supplied deliberately",
    )


@dataclass
class ModelInvocationOutcome:
    """What an invocation produced. ``invoked=False`` is a first-class result."""

    invoked: bool
    status: str
    exit_status: Optional[int] = None
    runtime_evidence_path: Optional[str] = None
    runtime_evidence: Optional[dict] = None
    detail: str = ""

    def to_dict(self) -> dict:
        return {
            "invoked": self.invoked,
            "status": self.status,
            "exit_status": self.exit_status,
            "runtime_evidence_path": self.runtime_evidence_path,
            "detail": self.detail,
        }


@dataclass
class ModelInvocationAdapter:
    """The smallest model-command boundary current governance requires."""

    mode: str = "dry-run"
    process_launcher: Callable[[LaunchPlan], ModelInvocationOutcome] = _refusing_launcher
    registry_primary_model: Optional[str] = None
    governed_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.mode not in {"dry-run", "real"}:
            raise gov.RunnerRefusal(
                gov.REAL_INVOCATION_NOT_ENABLED,
                f"unknown invocation mode {self.mode!r}",
            )

    # -- validation ------------------------------------------------------- #
    def assert_real_invocation_permitted(self, model_id: Optional[str]) -> None:
        """Refuse a real invocation unless a model is genuinely selected.

        Two independent conditions, because they fail for different reasons:
        the caller must pass an exact governed id, **and** the Study Lead must
        have selected a primary model. Neither substitutes for the other, and
        neither is defaulted.
        """
        if self.registry_primary_model is None:
            raise gov.RunnerRefusal(
                gov.PRIMARY_MODEL_NOT_SELECTED,
                "MODEL_REGISTRY.yml records primary_model: null (TD-B03 open). A "
                "real invocation is refused; the runner does not pick Sonnet, "
                "Opus or any other model, and has no fallback",
            )
        if not model_id:
            raise gov.RunnerRefusal(
                gov.MODEL_SELECTION_REQUIRED,
                "a real invocation requires an explicit exact model id",
            )
        if self.governed_ids and model_id not in self.governed_ids:
            raise gov.RunnerRefusal(
                gov.MODEL_ID_NOT_GOVERNED,
                f"{model_id!r} is not a governed exact model id "
                f"{list(self.governed_ids)}",
            )

    # -- invocation ------------------------------------------------------- #
    def invoke(self, plan: LaunchPlan) -> ModelInvocationOutcome:
        """Dry-run never starts a process; real mode fails closed before it can."""
        if self.mode == "dry-run":
            return ModelInvocationOutcome(
                invoked=False,
                status="DRY_RUN_NO_INVOKE",
                detail=(
                    "dry-run: the launch command was built and validated and no "
                    "model process was started. Model status: "
                    f"{plan.model_status}"
                ),
            )
        self.assert_real_invocation_permitted(plan.model_id)
        if not plan.executable:
            raise gov.RunnerRefusal(
                gov.MODEL_SELECTION_REQUIRED,
                "the launch plan is not executable; it carries no pinned model",
            )
        return self.process_launcher(plan)


# --------------------------------------------------------------------------- #
# Q1 — resolved-model-id readback
# --------------------------------------------------------------------------- #
@dataclass
class ModelIdentityValidation:
    status: str
    requested: Optional[str]
    resolved: Optional[str]
    detail: str
    sources: List[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return self.status == "VALIDATED"

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "requested_model_id": self.requested,
            "resolved_model_id": self.resolved,
            "evidence_sources": list(self.sources),
            "detail": self.detail,
        }


def extract_resolved_model_ids(evidence) -> List[Tuple[str, str]]:
    """Return ``(source, model id)`` pairs from approved runtime evidence.

    The approved sources are the headless ``system.init`` event's ``model`` and
    the ``modelUsage`` map (``MODEL_EXECUTION_CONTROLS`` §3.1). Nothing else is
    read as a readback, so an id echoed back from the request cannot be mistaken
    for one the runtime reported.
    """
    found: List[Tuple[str, str]] = []
    events: List[dict] = []
    if isinstance(evidence, dict):
        events = [evidence]
    elif isinstance(evidence, list):
        events = [e for e in evidence if isinstance(e, dict)]

    for event in events:
        if event.get("type") == "system" and event.get("subtype") == "init":
            model = event.get("model")
            if isinstance(model, str) and model:
                found.append(("system.init.model", model))
        usage = event.get("modelUsage")
        if isinstance(usage, dict):
            for key in usage:
                if isinstance(key, str) and key:
                    found.append(("modelUsage", key))
        nested = event.get("result")
        if isinstance(nested, dict):
            found.extend(extract_resolved_model_ids(nested))
    return found


def load_runtime_evidence(path) -> object:
    """Load ``stream-json``/``json`` runtime output; JSONL is read line by line."""
    text = str(path)
    with open(text, "r", encoding="utf-8") as fh:
        raw = fh.read()
    raw = raw.strip()
    if not raw:
        return []
    try:
        return json.loads(raw)
    except ValueError:
        events = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except ValueError:
                continue
        return events


def validate_model_identity(
    requested: Optional[str], evidence, *, strict: bool = True
) -> ModelIdentityValidation:
    """Compare the requested model id against the runtime readback (``Q1``).

    Missing, mismatched or ambiguous readback all invalidate the run. Nothing is
    inferred: if the evidence carries no approved readback field, the result is
    :data:`run_governance.MODEL_READBACK_MISSING`, never a pass.
    """
    pairs = extract_resolved_model_ids(evidence)
    distinct = sorted({model for _, model in pairs})
    sources = sorted({source for source, _ in pairs})

    if not distinct:
        result = ModelIdentityValidation(
            status=gov.MODEL_READBACK_MISSING,
            requested=requested,
            resolved=None,
            detail=(
                "the runtime evidence carries no system.init model and no "
                "modelUsage entry; the resolved model id cannot be read back, so "
                "the run is invalid (MODEL_EXECUTION_CONTROLS §7 Q1)"
            ),
            sources=sources,
        )
    elif len(distinct) > 1:
        result = ModelIdentityValidation(
            status=gov.MODEL_READBACK_AMBIGUOUS,
            requested=requested,
            resolved=None,
            detail=f"the runtime reported several distinct model ids: {distinct}",
            sources=sources,
        )
    elif requested is None or distinct[0] != requested:
        result = ModelIdentityValidation(
            status=gov.MODEL_READBACK_MISMATCH,
            requested=requested,
            resolved=distinct[0],
            detail=(
                f"requested {requested!r} but the runtime resolved "
                f"{distinct[0]!r}; the run is invalid"
            ),
            sources=sources,
        )
    else:
        result = ModelIdentityValidation(
            status="VALIDATED",
            requested=requested,
            resolved=distinct[0],
            detail=f"the runtime resolved exactly {distinct[0]!r} as requested",
            sources=sources,
        )

    if strict and not result.valid:
        raise gov.RunnerRefusal(result.status, result.detail)
    return result


def readback_not_performed(requested: Optional[str]) -> ModelIdentityValidation:
    """The dry-run record: not performed, and never reported as validated."""
    return ModelIdentityValidation(
        status="NOT_PERFORMED_DRY_RUN",
        requested=requested,
        resolved=None,
        detail=(
            "no model process was started, so no readback exists. This is "
            "recorded as not performed; it is never recorded as validated, and "
            "no readback value is fabricated"
        ),
    )


# --------------------------------------------------------------------------- #
# Q8 — invalid-model-id rejection
# --------------------------------------------------------------------------- #
@dataclass
class InvalidModelIdProbe:
    """A controlled ``Q8`` probe: does the runtime REJECT an unknown model id?"""

    invalid_model_id: str
    status: str
    detail: str
    exit_status: Optional[int] = None
    resolved_model_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "invalid_model_id": self.invalid_model_id,
            "status": self.status,
            "exit_status": self.exit_status,
            "resolved_model_id": self.resolved_model_id,
            "detail": self.detail,
        }


def build_invalid_model_id_probe(
    invalid_model_id: str, *, prompt_path: str, workspace: str
) -> LaunchPlan:
    """Build (never run) the launch used to test invalid-id rejection.

    Exposed so Stage-0 runtime testing has a governed, reproducible command
    instead of an ad-hoc one. Building it performs no request.
    """
    if not invalid_model_id or invalid_model_id in gov.governed_model_ids():
        raise gov.RunnerRefusal(
            gov.MODEL_ID_NOT_GOVERNED,
            f"{invalid_model_id!r} is not usable as a Q8 probe: the probe id must "
            "be one the registry does NOT govern",
        )
    return build_fresh_launch(
        prompt_path=prompt_path,
        workspace=workspace,
        model_id=invalid_model_id,
        require_model=True,
    )


def validate_invalid_model_id_rejection(
    invalid_model_id: str,
    *,
    exit_status: Optional[int],
    evidence=None,
) -> InvalidModelIdProbe:
    """Judge a ``Q8`` observation. No observation means NOT VALIDATED.

    Rejection means a non-zero exit **and** no readback claiming the invalid id
    ran. A zero exit, or a readback that silently degraded to another model, is
    a failure of the control, not a pass.
    """
    if exit_status is None:
        return InvalidModelIdProbe(
            invalid_model_id=invalid_model_id,
            status=gov.Q8_INVALID_MODEL_ID_NOT_VALIDATED_LIVE,
            detail=(
                "no live Q8 observation exists; invalid-model-id rejection stays "
                "a dry-run blocker under TD-B21 and is not asserted here"
            ),
        )
    resolved = sorted({m for _, m in extract_resolved_model_ids(evidence or [])})
    if exit_status == 0:
        return InvalidModelIdProbe(
            invalid_model_id=invalid_model_id,
            status="Q8_NOT_REJECTED",
            exit_status=exit_status,
            resolved_model_id=resolved[0] if resolved else None,
            detail=(
                "the runtime accepted an unrecognised model id; it did not fail "
                "closed, so the model control is unsound"
            ),
        )
    if resolved:
        return InvalidModelIdProbe(
            invalid_model_id=invalid_model_id,
            status="Q8_SILENTLY_DEGRADED",
            exit_status=exit_status,
            resolved_model_id=resolved[0],
            detail=(
                f"the runtime reported resolved model {resolved[0]!r} for an "
                "unrecognised request: the id was substituted rather than rejected"
            ),
        )
    return InvalidModelIdProbe(
        invalid_model_id=invalid_model_id,
        status="Q8_REJECTED",
        exit_status=exit_status,
        detail=(
            f"the runtime rejected {invalid_model_id!r} with exit status "
            f"{exit_status} and reported no resolved model"
        ),
    )
