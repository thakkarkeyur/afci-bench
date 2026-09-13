#!/usr/bin/env python3
"""The post-run evaluation boundary: what the runner may hand to an evaluator.

Two channels, kept separate because the study requires them separated
(``EXPERIMENTAL_CI_POLICY.md`` §1; ``HIDDEN_EVALUATOR_BOUNDARY.md``): functional
hidden acceptance and architecture opportunity scoring. Neither result is an
input to the other, and neither runs inside the model's workspace.

This module is an **orchestration boundary only**:

* it does **not** author or contain a hidden acceptance fixture, and it refuses
  to accept or score a run whose hidden acceptance is not validated. Every
  package except ``PT08`` remains ``draft_unvalidated`` (``TD-B05``/``TD-B32``)
  and fails with ``<task>_HIDDEN_ACCEPTANCE_NOT_VALIDATED``. ``PT08``'s hidden
  acceptance is now recorded ``status=validated``, so that one channel is READY
  — which is **not** a freeze and **not** run eligibility: the manifest-freeze
  gate below is a separate, still-blocking check;
* it does **not** reimplement the architecture oracle. It builds the command for
  the governed out-of-band CLI at ``experiments/v2/oracle/src/cli.ts``, which
  already refuses a non-frozen manifest, and it refuses first, on the public
  lifecycle record, so a scored run cannot even reach the oracle while the
  manifest is unfrozen;
* it **freezes nothing**, validates nothing, and passes no gate.

The freeze gate is deliberately checked *before* execution rather than before
scoring. Failing at the earliest possible point is strictly safer than failing
after a paid run has already happened.

No model is invoked and no benchmark task is executed.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import evaluator_mount as em
import run_governance as gov

#: The governed out-of-band architecture oracle. Referenced, never duplicated.
ORACLE_CLI = "experiments/v2/oracle/src/cli.ts"
ORACLE_TSCONFIG = "experiments/v2/oracle/tsconfig.json"

#: The ONLY fields a diagnostic-scoped frozen mount may differ from the shipped
#: manifest in. Both are lifecycle fields. Every semantic field — the task
#: binding, the opportunity set, the dependency policy, the layer map, the
#: evaluator hashes and the eligibility classification — is byte-identical, and
#: a test asserts the difference set rather than trusting this comment.
DIAGNOSTIC_FROZEN_MANIFEST_LIFECYCLE_FIELDS: Tuple[str, ...] = (
    "status",
    "manifest_version",
)

#: The suffix the derived lifecycle version carries, so a mount can never be
#: mistaken for the shipped manifest by version string alone.
DIAGNOSTIC_FROZEN_VERSION_SUFFIX = "-diagnostic-frozen"

DIAGNOSTIC_FROZEN_MANIFEST_NOT_DERIVABLE = "DIAGNOSTIC_FROZEN_MANIFEST_NOT_DERIVABLE"
DIAGNOSTIC_FROZEN_MANIFEST_MOUNT_REFUSED = "DIAGNOSTIC_FROZEN_MANIFEST_MOUNT_REFUSED"


@dataclass
class EvaluationChannel:
    """One evaluation channel's readiness and, when built, its command."""

    channel: str
    status: str
    code: Optional[str]
    detail: str
    command: Optional[List[str]] = None

    @property
    def ready(self) -> bool:
        return self.status == "READY"

    def to_dict(self) -> dict:
        return {
            "channel": self.channel,
            "status": self.status,
            "code": self.code,
            "detail": self.detail,
            "command": list(self.command) if self.command else None,
        }


@dataclass
class EvaluationPlan:
    """The full post-run evaluation boundary for one run."""

    task_id: str
    channels: List[EvaluationChannel] = field(default_factory=list)

    @property
    def blockers(self) -> List[EvaluationChannel]:
        return [c for c in self.channels if not c.ready]

    @property
    def ready(self) -> bool:
        return not self.blockers

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "ready": self.ready,
            "channel_separation": (
                "functional acceptance and architecture scoring are evaluated "
                "independently; neither result is an input to the other"
            ),
            "channels": [c.to_dict() for c in self.channels],
        }


def functional_acceptance_channel(
    task_id: str, *, acceptance_matrix: Path = gov.ACCEPTANCE_MATRIX
) -> EvaluationChannel:
    """Refuse hidden acceptance until the public authority says it is validated."""
    if gov.hidden_acceptance_is_validated(task_id, acceptance_matrix):
        return EvaluationChannel(
            channel="functional_hidden_acceptance",
            status="READY",
            code=None,
            detail=(
                f"TASK_ACCEPTANCE_MATRIX.csv records {task_id}'s hidden acceptance "
                "as validated; the fixture itself stays in the private evaluator "
                "repository and is never materialised into the coding worktree"
            ),
        )
    return EvaluationChannel(
        channel="functional_hidden_acceptance",
        status="BLOCKED",
        code=gov.hidden_acceptance_refusal_code(task_id),
        detail=(
            f"{task_id}'s hidden functional acceptance is draft_unvalidated and its "
            "package is status=review: it has never been reference-pass / "
            "reference-fail / mutation validated, and the required independent "
            "review of that validation has not happened (TD-B05/TD-B32). The "
            "runner refuses to accept or score a run against it, and this package "
            "authors no fixture"
        ),
    )


def architecture_scoring_channel(
    task_id: str,
    *,
    snapshot: Optional[Path] = None,
    manifest_mount: Optional[Path] = None,
    coding_worktree: Optional[Path] = None,
    repo: Path = gov.REPO,
    acceptance_matrix: Path = gov.ACCEPTANCE_MATRIX,
    condition: Optional[str] = None,
    run_purpose: Optional[str] = None,
) -> EvaluationChannel:
    """Point at the governed oracle; refuse while the manifest is not frozen.

    The oracle command is built only when a snapshot and an externally mounted
    manifest are supplied *and* the applicable freeze holds. The mount is checked
    against the evaluator-mount boundary so a manifest can never be placed
    where the coding model could read it.

    ``condition`` and ``run_purpose`` are what let ``SL-PT08-06``'s
    diagnostic-scoped freeze satisfy the gate for the one authorised triple. A
    caller that supplies neither gets the suite-wide answer alone, which is the
    fail-closed reading and is exactly what every other task and purpose gets.
    """
    freeze_state = gov.manifest_freeze_state(
        task_id,
        condition=condition,
        run_purpose=run_purpose,
        acceptance_matrix=acceptance_matrix,
    )
    if not freeze_state["effective_for_this_purpose"]:
        return EvaluationChannel(
            channel="architecture_opportunity_scoring",
            status="BLOCKED",
            code=gov.MANIFEST_NOT_FROZEN,
            detail=(
                f"{task_id}'s evaluator manifest is status=review and NOT frozen. A "
                "real scored run may not proceed: the frozen opportunity set is the "
                "E1 denominator, and an unfrozen one is a candidate rather than a "
                "demonstrated denominator (TD-B05/TD-B14/TD-B32, gate G1). The "
                "runner reports this and freezes nothing"
            ),
        )
    if snapshot is None or manifest_mount is None:
        return EvaluationChannel(
            channel="architecture_opportunity_scoring",
            status="BLOCKED",
            code=gov.MANIFEST_NOT_FROZEN,
            detail="no post-run snapshot and/or externally mounted manifest supplied",
        )
    if coding_worktree is not None and em.evaluator_mount_rejected(
        coding_worktree, manifest_mount
    ):
        return EvaluationChannel(
            channel="architecture_opportunity_scoring",
            status="BLOCKED",
            code=gov.CANONICAL_REPOSITORY_EXECUTION_REFUSED,
            detail=(
                f"the evaluator mount {manifest_mount} is inside the coding "
                f"worktree {coding_worktree}; it must be mounted outside it "
                "(EVALUATOR_MOUNT_POLICY.md)"
            ),
        )
    return EvaluationChannel(
        channel="architecture_opportunity_scoring",
        status="READY",
        code=None,
        detail=(
            "delegated to the governed out-of-band oracle; this runner implements "
            "no scoring semantics of its own"
        ),
        command=[
            "npx",
            "ts-node",
            "--project",
            str(Path(repo) / ORACLE_TSCONFIG),
            str(Path(repo) / ORACLE_CLI),
            "--snapshot",
            str(snapshot),
            "--manifest",
            str(manifest_mount),
        ],
    )


def build_evaluation_plan(
    task_id: str,
    *,
    snapshot: Optional[Path] = None,
    manifest_mount: Optional[Path] = None,
    coding_worktree: Optional[Path] = None,
    repo: Path = gov.REPO,
    acceptance_matrix: Path = gov.ACCEPTANCE_MATRIX,
    condition: Optional[str] = None,
    run_purpose: Optional[str] = None,
) -> EvaluationPlan:
    return EvaluationPlan(
        task_id=task_id,
        channels=[
            functional_acceptance_channel(task_id, acceptance_matrix=acceptance_matrix),
            architecture_scoring_channel(
                task_id,
                snapshot=snapshot,
                manifest_mount=manifest_mount,
                coding_worktree=coding_worktree,
                repo=repo,
                acceptance_matrix=acceptance_matrix,
                condition=condition,
                run_purpose=run_purpose,
            ),
        ],
    )


def assert_scoring_prerequisites(
    task_id: str,
    *,
    acceptance_matrix: Path = gov.ACCEPTANCE_MATRIX,
    condition: Optional[str] = None,
    run_purpose: Optional[str] = None,
    model_id: Optional[str] = None,
    cli_version: Optional[str] = None,
    context_verdict: Optional[str] = None,
    session_id: Optional[str] = None,
    previous_session_ids=(),
    launch_argv=(),
    require_execution_evidence: bool = False,
    require_context_verdict: Optional[bool] = None,
) -> None:
    """Refuse a scored run before execution. Never bypassed, never downgraded.

    Called from ``PRECHECK`` so a real diagnostic fails *before* a model is
    launched rather than after, and called again before any result would be
    accepted so an out-of-band caller cannot skip the first check.

    ``SL-PT08-06``'s scoped freeze can satisfy the freeze gate for exactly one
    (task, condition, purpose) triple. It waives nothing else: when the scoped
    route is the one in force, the per-repetition conditions it does not waive —
    the exact model id, the live-validated runtime version, a CLEAN context
    audit, no resume, no continuation and no session reuse — are checked here
    too, and ``require_execution_evidence`` makes an unsupplied one a refusal
    rather than a silence.
    """
    acceptance = functional_acceptance_channel(task_id, acceptance_matrix=acceptance_matrix)
    if not acceptance.ready:
        raise gov.RunnerRefusal(acceptance.code or gov.HIDDEN_ACCEPTANCE_NOT_VALIDATED,
                                acceptance.detail)

    state = gov.manifest_freeze_state(
        task_id,
        condition=condition,
        run_purpose=run_purpose,
        acceptance_matrix=acceptance_matrix,
    )
    if not state["effective_for_this_purpose"]:
        problems = state["diagnostic_freeze_problems"]
        raise gov.RunnerRefusal(
            gov.MANIFEST_NOT_FROZEN,
            f"{task_id}'s applicable manifest is not frozen and no "
            "diagnostic-scoped freeze applies; a real scored run may not proceed "
            "and the runner freezes nothing"
            + (
                ": " + "; ".join(f"<{p['code']}> {p['detail']}" for p in problems[:3])
                if problems
                else ""
            ),
        )

    if not state["diagnostic_frozen"]:
        return  # the suite-wide freeze is in force; no scoped conditions apply

    freeze = gov.diagnostic_freeze_for(
        gov.resolve_run_purpose(run_purpose), task_id, condition
    )
    if freeze is None:  # pragma: no cover - state said otherwise; fail closed
        raise gov.RunnerRefusal(
            gov.DIAGNOSTIC_FREEZE_MISSING,
            f"{task_id}/{condition} reported a scoped freeze that could not be "
            "resolved; a freeze that cannot be re-derived is not a freeze",
        )
    problems = gov.diagnostic_freeze_execution_problems(
        freeze,
        model_id=model_id,
        cli_version=cli_version,
        context_verdict=context_verdict,
        session_id=session_id,
        previous_session_ids=previous_session_ids,
        launch_argv=launch_argv,
        require_all=require_execution_evidence,
        require_context_verdict=require_context_verdict,
    )
    if problems:
        code, detail = problems[0]
        raise gov.RunnerRefusal(
            code,
            f"{freeze.authority} does not waive this: {detail}"
            + (
                f" (and {len(problems) - 1} further problem(s))"
                if len(problems) > 1
                else ""
            ),
        )


# --------------------------------------------------------------------------- #
# SL-PT08-06 — the diagnostic-scoped frozen manifest mount
# --------------------------------------------------------------------------- #
def shipped_manifest_path(
    task_id: str, private_root: Optional[Path] = None
) -> Path:
    """The SHIPPED private evaluator manifest. Read-only, never rewritten."""
    root = Path(private_root) if private_root else gov.default_private_root()
    path = root / "tasks" / task_id / "evaluator_manifest.json"
    if not path.is_file():
        raise gov.RunnerRefusal(
            DIAGNOSTIC_FROZEN_MANIFEST_NOT_DERIVABLE,
            f"the shipped {task_id} evaluator manifest is not available at {path}; "
            "a scoped mount is derived from the shipped package or not at all",
        )
    return path


def derive_diagnostic_frozen_manifest(
    task_id: str,
    *,
    authority: str,
    private_root: Optional[Path] = None,
) -> Tuple[Dict[str, object], Dict[str, object]]:
    """Derive the scoped frozen manifest, and the proof of what it changed.

    The out-of-band oracle scores only a manifest whose ``status`` is exactly
    ``frozen``. The shipped manifest is ``status=review`` and **stays** that way:
    it is read, never written, and the suite-wide lifecycle is untouched.

    What comes back is a derived object differing in exactly
    :data:`DIAGNOSTIC_FROZEN_MANIFEST_LIFECYCLE_FIELDS` and nothing else, plus a
    provenance block naming the authority, both hashes and the difference set —
    so a reader verifies the claim instead of believing it. The same shape the
    already-approved private validation corpus uses for its own labelled cases.
    """
    path = shipped_manifest_path(task_id, private_root)
    raw = path.read_bytes()
    try:
        shipped = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise gov.RunnerRefusal(
            DIAGNOSTIC_FROZEN_MANIFEST_NOT_DERIVABLE,
            f"the shipped {task_id} evaluator manifest is unreadable: {exc}",
        ) from exc

    version = str(shipped.get("manifest_version", ""))
    base = version[: -len("-review")] if version.endswith("-review") else version
    derived = dict(shipped)
    derived["status"] = "frozen"
    derived["manifest_version"] = base + DIAGNOSTIC_FROZEN_VERSION_SUFFIX

    differing = sorted(
        k for k in set(shipped) | set(derived) if shipped.get(k) != derived.get(k)
    )
    if differing != sorted(DIAGNOSTIC_FROZEN_MANIFEST_LIFECYCLE_FIELDS):
        raise gov.RunnerRefusal(
            DIAGNOSTIC_FROZEN_MANIFEST_NOT_DERIVABLE,
            f"the derivation would change {differing}; a scoped mount may differ "
            f"from the shipped manifest in "
            f"{sorted(DIAGNOSTIC_FROZEN_MANIFEST_LIFECYCLE_FIELDS)} only, and "
            "changes no task, evaluator or opportunity semantics",
        )

    body = json.dumps(derived, indent=2, sort_keys=True).encode("utf-8")
    provenance = {
        "record": "afci-bench/v2/diagnostic-scoped-frozen-manifest",
        "authority": authority,
        "task_id": task_id,
        "shipped_manifest_path": str(path),
        "shipped_manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "shipped_manifest_status": shipped.get("status"),
        "shipped_manifest_version": version,
        "derived_manifest_sha256": hashlib.sha256(body).hexdigest(),
        "derived_manifest_status": derived["status"],
        "derived_manifest_version": derived["manifest_version"],
        "fields_changed": differing,
        "semantic_fields_changed": [],
        "shipped_manifest_modified": False,
        "public_lifecycle_row_modified": False,
        "suite_frozen": False,
        "global_gate_g1_passed": False,
        "committed_anywhere": False,
    }
    return derived, provenance


def write_diagnostic_frozen_manifest_mount(
    task_id: str,
    mount_dir: Path,
    *,
    condition: str,
    run_purpose: str,
    coding_worktree: Optional[Path] = None,
    private_root: Optional[Path] = None,
    repo: Path = gov.REPO,
    acceptance_matrix: Path = gov.ACCEPTANCE_MATRIX,
) -> Tuple[Path, Dict[str, object]]:
    """Materialise the scoped mount, refusing every location it may not occupy.

    Refused, in order: a triple with no authorised scoped freeze; a mount inside
    the canonical repository; a mount inside the private evaluator repository;
    and a mount inside the coding worktree, which is the boundary
    ``EVALUATOR_MOUNT_POLICY.md`` exists to hold.
    """
    state = gov.manifest_freeze_state(
        task_id,
        condition=condition,
        run_purpose=run_purpose,
        acceptance_matrix=acceptance_matrix,
    )
    if not state["diagnostic_frozen"]:
        problems = state["diagnostic_freeze_problems"]
        raise gov.RunnerRefusal(
            gov.DIAGNOSTIC_FREEZE_NOT_AUTHORISED,
            f"no diagnostic-scoped freeze authorises {task_id}/{condition}/"
            f"{run_purpose}, so no scoped mount may be derived"
            + (
                ": " + "; ".join(f"<{p['code']}> {p['detail']}" for p in problems[:3])
                if problems
                else ""
            ),
        )

    mount = Path(mount_dir).resolve()
    private = (Path(private_root) if private_root else gov.default_private_root()).resolve()
    for name, forbidden in (("canonical", Path(repo).resolve()), ("private", private)):
        if mount == forbidden or forbidden in mount.parents:
            raise gov.RunnerRefusal(
                DIAGNOSTIC_FROZEN_MANIFEST_MOUNT_REFUSED,
                f"the scoped mount {mount} is inside the {name} repository; a "
                "derived mount lives in a disposable directory outside both",
            )
    if coding_worktree is not None and em.evaluator_mount_rejected(
        Path(coding_worktree), mount
    ):
        raise gov.RunnerRefusal(
            DIAGNOSTIC_FROZEN_MANIFEST_MOUNT_REFUSED,
            f"the scoped mount {mount} is inside the coding worktree "
            f"{coding_worktree}; it must be mounted outside it "
            "(EVALUATOR_MOUNT_POLICY.md)",
        )

    authority = str(state["diagnostic_freeze_authority"])
    derived, provenance = derive_diagnostic_frozen_manifest(
        task_id, authority=authority, private_root=private_root
    )
    mount.mkdir(parents=True, exist_ok=True)
    target = mount / f"{task_id}.diagnostic-frozen.evaluator_manifest.json"
    target.write_text(
        json.dumps(derived, indent=2, sort_keys=True), encoding="utf-8", newline="\n"
    )
    provenance["mount_path"] = str(target)
    (mount / f"{task_id}.diagnostic-frozen.provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True), encoding="utf-8", newline="\n"
    )
    return target, provenance


def freeze_status_report(
    task_id: str,
    *,
    acceptance_matrix: Path = gov.ACCEPTANCE_MATRIX,
    condition: Optional[str] = None,
    run_purpose: Optional[str] = None,
) -> Dict[str, object]:
    """Report the manifest lifecycle without changing it (``--dry-run`` view).

    ``manifest_frozen`` keeps its existing suite-wide meaning and is reported
    beside, never merged with, the ``SL-PT08-06`` scoped state.
    """
    state = gov.manifest_freeze_state(
        task_id,
        condition=condition,
        run_purpose=run_purpose,
        acceptance_matrix=acceptance_matrix,
    )
    row = gov.acceptance_matrix_row(task_id, acceptance_matrix)
    effective = bool(state["effective_for_this_purpose"])
    return {
        "task_id": task_id,
        # The suite-wide lifecycle answer, unchanged in meaning and in value.
        "manifest_frozen": state["global_frozen"],
        "suite_frozen": False,
        "global_gate_g1_passed": False,
        # The SL-PT08-06 scoped answer, reported separately.
        "diagnostic_scoped_frozen": state["diagnostic_frozen"],
        "diagnostic_freeze_authority": state["diagnostic_freeze_authority"],
        "diagnostic_freeze": state["diagnostic_freeze"],
        "effective_for_this_purpose": effective,
        "code": None if effective else gov.MANIFEST_NOT_FROZEN,
        "public_lifecycle_status": row.get("status", ""),
        "inspected_only": True,
        "changed_by_this_runner": False,
    }
