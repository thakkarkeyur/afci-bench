#!/usr/bin/env python3
"""The post-run evaluation boundary: what the runner may hand to an evaluator.

Two channels, kept separate because the study requires them separated
(``EXPERIMENTAL_CI_POLICY.md`` §1; ``HIDDEN_EVALUATOR_BOUNDARY.md``): functional
hidden acceptance and architecture opportunity scoring. Neither result is an
input to the other, and neither runs inside the model's workspace.

This module is an **orchestration boundary only**:

* it does **not** author or contain a hidden acceptance fixture, and it refuses
  to accept or score a run whose hidden acceptance is not validated —
  ``PT08``'s remains ``draft_unvalidated`` (``TD-B05``/``TD-B32``), so a real
  ``PT08`` diagnostic fails with ``PT08_HIDDEN_ACCEPTANCE_NOT_VALIDATED``;
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

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import evaluator_mount as em
import run_governance as gov

#: The governed out-of-band architecture oracle. Referenced, never duplicated.
ORACLE_CLI = "experiments/v2/oracle/src/cli.ts"
ORACLE_TSCONFIG = "experiments/v2/oracle/tsconfig.json"


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
) -> EvaluationChannel:
    """Point at the governed oracle; refuse while the manifest is not frozen.

    The oracle command is built only when a snapshot and an externally mounted
    manifest are supplied *and* the manifest is frozen. The mount is checked
    against the evaluator-mount boundary so a manifest can never be placed
    where the coding model could read it.
    """
    if not gov.manifest_is_frozen(task_id, acceptance_matrix):
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
            ),
        ],
    )


def assert_scoring_prerequisites(
    task_id: str, *, acceptance_matrix: Path = gov.ACCEPTANCE_MATRIX
) -> None:
    """Refuse a scored run before execution. Never bypassed, never downgraded.

    Called from ``PRECHECK`` so a real diagnostic fails *before* a model is
    launched rather than after, and called again before any result would be
    accepted so an out-of-band caller cannot skip the first check.
    """
    acceptance = functional_acceptance_channel(task_id, acceptance_matrix=acceptance_matrix)
    if not acceptance.ready:
        raise gov.RunnerRefusal(acceptance.code or gov.HIDDEN_ACCEPTANCE_NOT_VALIDATED,
                                acceptance.detail)
    if not gov.manifest_is_frozen(task_id, acceptance_matrix):
        raise gov.RunnerRefusal(
            gov.MANIFEST_NOT_FROZEN,
            f"{task_id}'s applicable manifest is not frozen; a real scored run may "
            "not proceed and the runner freezes nothing",
        )


def freeze_status_report(
    task_id: str, *, acceptance_matrix: Path = gov.ACCEPTANCE_MATRIX
) -> Dict[str, object]:
    """Report the manifest lifecycle without changing it (``--dry-run`` view)."""
    frozen = gov.manifest_is_frozen(task_id, acceptance_matrix)
    row = gov.acceptance_matrix_row(task_id, acceptance_matrix)
    return {
        "task_id": task_id,
        "manifest_frozen": frozen,
        "code": None if frozen else gov.MANIFEST_NOT_FROZEN,
        "public_lifecycle_status": row.get("status", ""),
        "inspected_only": True,
        "changed_by_this_runner": False,
    }
