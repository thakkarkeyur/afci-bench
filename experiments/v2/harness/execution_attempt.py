#!/usr/bin/env python3
"""``SL-V2-EFF-ABORT-01`` / ``SL-V2-EFF-RESTART-01`` — execution attempts.

What an execution attempt is
----------------------------
One pass through the frozen 36-row ``AFCI_EFFICIENCY_PILOT`` schedule. Attempt 1
was ABORTED after 9 rows because :func:`run_artifacts.derive_run_id` omitted the
reset state, so the two arms of every cell derived one run id and one artifact
directory: **18 collisions across the 36 rows**. Attempt 2 is the replacement.

An attempt is **infrastructure provenance and nothing else**. It separates one
execution's artifacts from another's so a replacement cannot land on an aborted
one's evidence. It does not appear in any task body, condition, budget,
checkpoint predicate, metric, threshold or analysis, and the scientific schedule
it executes is identical row for row to the one Attempt 1 executed — which this
module proves mechanically rather than asserting (:func:`projection_problems`).

Why the preflight refuses before row 1
--------------------------------------
Attempt 1 discovered its collision at scientific sequence 9, by hitting it: the
model had already been invoked, the task had already been delivered, and the
earlier observation's record was already gone. The identities of all 36 rows are
derivable with no model, no process and no cost, so there is no defensible
reason to learn this from an execution. :func:`preflight` derives every identity
up front and refuses the WHOLE execution on a single duplicate.

No model is invoked by this module, and it creates no directories: a preflight
that wrote into the destinations it is checking would be the defect it exists to
prevent.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import efficiency_run_plan as erp
import reset_budget as rb
import run_artifacts as art
import run_governance as gov

#: The Study-Lead decisions this module implements.
ABORT_DECISION = "SL-V2-EFF-ABORT-01"
RESTART_DECISION = "SL-V2-EFF-RESTART-01"

#: The aborted execution. Its artifacts declared NO execution attempt, because
#: the field did not exist when they were written — so Attempt 1's ids are the
#: legacy form and are reconstructed here rather than re-derived with an attempt
#: of 1, which would describe directories that have never existed.
ABORTED_ATTEMPT = 1

#: The replacement execution authorised by ``SL-V2-EFF-RESTART-01``.
REPLACEMENT_ATTEMPT = 2

#: Where the replacement execution's plan artifact lives, repository-relative.
#: It is a SEPARATE file from the scientific schedule. The schedule is frozen and
#: keeps its hash; this carries the attempt, the identity algorithm version and
#: the artifact namespace, which are infrastructure and legitimately change.
REPLACEMENT_PLAN_PATH = (
    "docs/v2/AFCI_EFFICIENCY_PILOT_ATTEMPT_2_EXECUTION_PLAN.json"
)

#: The scientific schedule's frozen identity, restated so a drift is mechanical.
ORIGINAL_SCIENTIFIC_PLAN_SHA256 = (
    "0038cd8b563ea804f4887d21cb37ceddb3a8f7632c4dd2315c260d3a9af95767"
)

#: The five values that ARE the scientific schedule. Everything else in a plan
#: artifact is infrastructure, and a replacement is required to reproduce these
#: exactly, in this order, row for row.
SCIENTIFIC_PROJECTION_FIELDS: Tuple[str, ...] = (
    "sequence", "task_id", "condition", "reset_state", "repetition",
)

#: The run mode a counted pilot observation executes in. Named rather than
#: inlined because it is part of the identity a preflight derives, and a
#: preflight that silently checked ``dry-run`` identities would certify
#: directories no observation will ever use.
COUNTED_MODE = "real"


# --------------------------------------------------------------------------- #
# The attempt namespace
# --------------------------------------------------------------------------- #
def attempt_namespace(execution_attempt: int) -> str:
    """The directory segment one execution's artifacts live under.

    Relative, not absolute. ``SL-V2-EFF-RESTART-01`` requires the *root* to be
    outside the operator's profile; it does not, and cannot portably, require a
    particular drive letter. The invariant is the isolation, and the namespace
    is what makes two executions disjoint under whatever root satisfies it.
    """
    attempt = art.normalise_execution_attempt(execution_attempt)
    if attempt is None:
        raise gov.RunnerRefusal(
            gov.EXECUTION_ATTEMPT_INVALID,
            "an artifact namespace is a property of a declared execution "
            "attempt; None declares none and never means attempt 1",
        )
    return f"attempt-{attempt}"


def attempt_artifact_root(base: Path, execution_attempt: int) -> Path:
    """The artifact root for one execution, under an operator-chosen base."""
    return Path(base) / attempt_namespace(execution_attempt)


# --------------------------------------------------------------------------- #
# The scientific projection (PART L)
# --------------------------------------------------------------------------- #
def scientific_projection(plan: Dict[str, object]) -> List[Tuple[object, ...]]:
    """The ordered (sequence, task, condition, reset state, repetition) rows."""
    rows = plan.get("runs")
    if not isinstance(rows, list):
        raise gov.RunnerRefusal(
            gov.EFFICIENCY_RUN_PLAN_INVALID,
            f"the plan carries no run list; got {type(rows).__name__}",
        )
    return [tuple(row.get(f) for f in SCIENTIFIC_PROJECTION_FIELDS) for row in rows]


def projection_problems(
    replacement: Dict[str, object], original: Dict[str, object]
) -> List[Tuple[str, str]]:
    """Prove a replacement executes the SAME science, row for row.

    Compared as an ordered projection rather than as a set, because the order is
    part of the design: the within-block condition order and the across-block
    interleave are what stop a session-long drift landing systematically on one
    arm. A replacement that ran the same 36 rows in a different order would be a
    different experiment wearing the same summary statistics.
    """
    problems: List[Tuple[str, str]] = []
    want = scientific_projection(original)
    got = scientific_projection(replacement)
    if len(got) != len(want):
        problems.append((
            gov.EFFICIENCY_RUN_PLAN_INVALID,
            f"the replacement carries {len(got)} rows against the original's "
            f"{len(want)}",
        ))
        return problems
    for index, (a, b) in enumerate(zip(want, got), start=1):
        if a != b:
            problems.append((
                gov.EFFICIENCY_RUN_PLAN_INVALID,
                f"row {index} of the replacement is {b}, and the original's is "
                f"{a}; the scientific schedule is not re-randomised and not "
                "reordered by a restart",
            ))
    return problems


# --------------------------------------------------------------------------- #
# Whole-schedule identity derivation (PART I)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class RowIdentity:
    """One scheduled row's derived artifact identity. No side effects."""

    sequence: int
    block_id: str
    task_id: str
    condition: str
    reset_state: str
    repetition: int
    run_id: str
    artifact_dir: str

    def to_dict(self) -> Dict[str, object]:
        return {
            "sequence": self.sequence,
            "block_id": self.block_id,
            "task_id": self.task_id,
            "condition": self.condition,
            "reset_state": self.reset_state,
            "repetition": self.repetition,
            "run_id": self.run_id,
            "artifact_dir": self.artifact_dir,
        }


def derive_schedule_identities(
    plan: Dict[str, object],
    *,
    execution_attempt: Optional[int],
    artifact_root: Path,
    mode: str = COUNTED_MODE,
    repo: Path = gov.REPO,
    include_reset_state: bool = True,
) -> List[RowIdentity]:
    """Derive every scheduled row's run id and artifact directory.

    ``include_reset_state=False`` reproduces the PRE-REPAIR derivation, which is
    how Attempt 1's real directory names are reconstructed. It is not a fallback
    and no run may use it: it exists so the disjointness check compares against
    what is actually on disk rather than against a plausible reconstruction.
    """
    substrate = gov.SUBSTRATE_CONTENT_HASH
    root = Path(artifact_root)
    identities: List[RowIdentity] = []
    for row in plan.get("runs") or []:
        task_id = str(row["task_id"])
        state = str(row["reset_state"])
        run_id = art.derive_run_id(
            purpose=erp.RUN_PURPOSE,
            task_id=task_id,
            condition=str(row["condition"]),
            task_sha=gov.expected_task_sha256(task_id),
            substrate_hash=substrate,
            mode=mode,
            repetition=int(row["repetition"]),
            reset_state=state if include_reset_state else None,
            execution_attempt=execution_attempt,
        )
        identities.append(
            RowIdentity(
                sequence=int(row["sequence"]),
                block_id=str(row["block_id"]),
                task_id=task_id,
                condition=str(row["condition"]),
                reset_state=state,
                repetition=int(row["repetition"]),
                run_id=run_id,
                artifact_dir=str(root / run_id),
            )
        )
    return identities


def identity_problems(identities: Sequence[RowIdentity]) -> List[Tuple[str, str]]:
    """Every duplicate run id and duplicate artifact directory in a schedule.

    Reported in full rather than first-only. An operator about to spend 36 paid
    runs needs the whole list; Attempt 1's operator got one collision at a time,
    by executing into it.
    """
    problems: List[Tuple[str, str]] = []
    for label, key in (("run id", "run_id"), ("artifact directory", "artifact_dir")):
        seen: Dict[str, RowIdentity] = {}
        for identity in identities:
            value = getattr(identity, key)
            if value in seen:
                first = seen[value]
                problems.append((
                    gov.EFFICIENCY_SCHEDULE_IDENTITY_COLLISION,
                    f"sequence {first.sequence} ({first.task_id}/{first.condition}/"
                    f"{first.reset_state}/R{first.repetition}) and sequence "
                    f"{identity.sequence} ({identity.task_id}/{identity.condition}/"
                    f"{identity.reset_state}/R{identity.repetition}) derive one "
                    f"{label}: {value}",
                ))
            else:
                seen[value] = identity
    return problems


def overlap_problems(
    replacement: Sequence[RowIdentity], aborted: Sequence[RowIdentity]
) -> List[Tuple[str, str]]:
    """Refuse any identity the replacement shares with the aborted execution."""
    problems: List[Tuple[str, str]] = []
    prior_ids = {i.run_id for i in aborted}
    prior_dirs = {Path(i.artifact_dir).name for i in aborted}
    for identity in replacement:
        if identity.run_id in prior_ids:
            problems.append((
                gov.EFFICIENCY_SCHEDULE_IDENTITY_COLLISION,
                f"sequence {identity.sequence} derives run id {identity.run_id}, "
                f"which Attempt {ABORTED_ATTEMPT} already minted; a replacement "
                "never writes into an aborted execution's identity",
            ))
        if Path(identity.artifact_dir).name in prior_dirs:
            problems.append((
                gov.EFFICIENCY_SCHEDULE_IDENTITY_COLLISION,
                f"sequence {identity.sequence} derives artifact directory name "
                f"{Path(identity.artifact_dir).name}, which Attempt "
                f"{ABORTED_ATTEMPT} already used",
            ))
    return problems


def occupancy_problems(
    identities: Sequence[RowIdentity],
) -> List[Tuple[str, str]]:
    """Refuse a schedule whose destinations are already occupied on disk.

    The per-run ownership guard catches this too, but it catches it one row at a
    time and after the previous rows have run. An execution whose row 30 is
    already occupied is not an execution that should start at row 1.
    """
    problems: List[Tuple[str, str]] = []
    for identity in identities:
        path = Path(identity.artifact_dir)
        if not path.exists():
            continue
        entries = sorted(p.name for p in path.iterdir()) if path.is_dir() else []
        problems.append((
            gov.ARTIFACT_IDENTITY_COLLISION_PREINVOCATION,
            f"sequence {identity.sequence}'s destination {path} already exists "
            f"and holds {entries[:8] or 'no entries'}; a replacement execution "
            "begins in unoccupied directories and never reclaims one",
        ))
    return problems


# --------------------------------------------------------------------------- #
# Session identity (PART I)
# --------------------------------------------------------------------------- #
#: Phase slots a schedule allocates: one per NON_RESET row, two per RESET row.
def session_slots(plan: Dict[str, object]) -> List[Tuple[int, Optional[str]]]:
    """Every (sequence, phase) a model session will be minted for."""
    slots: List[Tuple[int, Optional[str]]] = []
    for row in plan.get("runs") or []:
        sequence = int(row["sequence"])
        if str(row["reset_state"]) == rb.RESET:
            slots.extend((sequence, phase) for phase in rb.PHASES)
        else:
            slots.append((sequence, None))
    return slots


def session_allocation_problems(
    plan: Dict[str, object],
    *,
    session_id_factory: Callable[[], str] = lambda: str(uuid.uuid4()),
) -> List[Tuple[str, str]]:
    """Prove the schedule's session allocation admits no reuse.

    What this checks, precisely, because the distinction matters: it does NOT
    predict the session ids the execution will use. Those are minted at launch
    by :mod:`reset_orchestration`, and a preflight that printed ids and called
    them "the session ids" would be describing sessions that never existed.

    What it proves is that the ALLOCATION POLICY cannot produce a reused
    identity: every row allocates its own slots, a ``RESET`` row allocates
    exactly two and they are distinct, a ``NON_RESET`` row allocates exactly one,
    and drawing one identity per slot from the governed factory yields as many
    distinct identities as there are slots. Reuse is separately refused at launch
    (``RESET_PHASE_SESSION_REUSED``); this is the schedule-level statement that
    nothing in the plan asks for it.
    """
    problems: List[Tuple[str, str]] = []
    slots = session_slots(plan)
    if len(set(slots)) != len(slots):
        problems.append((
            gov.RESET_PHASE_SESSION_REUSED,
            "the schedule allocates one session slot to two rows",
        ))

    by_sequence: Dict[int, List[Optional[str]]] = {}
    for sequence, phase in slots:
        by_sequence.setdefault(sequence, []).append(phase)
    for row in plan.get("runs") or []:
        sequence = int(row["sequence"])
        phases = by_sequence.get(sequence, [])
        if str(row["reset_state"]) == rb.RESET:
            if sorted(p for p in phases if p) != sorted(rb.PHASES):
                problems.append((
                    gov.RESET_PHASE_SESSION_REUSED,
                    f"RESET sequence {sequence} allocates phases {phases}, not "
                    f"{list(rb.PHASES)}",
                ))
        elif phases != [None]:
            problems.append((
                gov.RESET_PHASE_SESSION_REUSED,
                f"NON_RESET sequence {sequence} allocates {phases}; it is one "
                "process and has no phases",
            ))

    minted = [session_id_factory() for _ in slots]
    if len(set(minted)) != len(slots):
        problems.append((
            gov.RESET_PHASE_SESSION_REUSED,
            f"the governed session factory produced {len(set(minted))} distinct "
            f"identities for {len(slots)} slots; a slot would reuse another's "
            "session",
        ))
    if any(not value for value in minted):
        problems.append((
            gov.RESET_PHASE_SESSION_REUSED,
            "the governed session factory produced an empty identity",
        ))

    declared = [
        int(row["sequence"])
        for row in plan.get("runs") or []
        if row.get("session_id")
    ]
    if declared:
        problems.append((
            gov.SESSION_ID_REUSED,
            f"rows {declared} carry a pre-declared session id; every session is "
            "minted fresh at launch and none is scheduled in advance",
        ))
    return problems


# --------------------------------------------------------------------------- #
# The replacement execution plan artifact (PART F / PART L)
# --------------------------------------------------------------------------- #
def build_execution_plan(
    *,
    execution_attempt: int = REPLACEMENT_ATTEMPT,
    artifact_root: Path,
    sterile_base: Path,
    seed: str = erp.SEED,
    repo: Path = gov.REPO,
) -> Dict[str, object]:
    """The replacement execution's plan: the frozen science plus provenance.

    The scientific half is the committed schedule VERBATIM — it is loaded, not
    rebuilt, so this artifact cannot quietly re-randomise anything — and the
    infrastructure half is the attempt, the identity algorithm and the derived
    identities. Their separation is the point: a reader can hash the projection
    and compare it with Attempt 1's without reading a word of prose.
    """
    scientific = erp.load_plan(repo)
    problems = erp.plan_problems(scientific, repo)
    if problems:
        raise gov.RunnerRefusal(
            gov.EFFICIENCY_RUN_PLAN_INVALID,
            "the committed scientific schedule does not validate: "
            + "; ".join(problems[:4]),
        )
    identities = derive_schedule_identities(
        scientific,
        execution_attempt=execution_attempt,
        artifact_root=artifact_root,
        repo=repo,
    )
    return {
        "record": "afci-bench/v2/afci-efficiency-pilot-execution-plan",
        "authority": RESTART_DECISION,
        "supersedes_execution_attempt": ABORTED_ATTEMPT,
        "superseded_by": None,
        "abort_authority": ABORT_DECISION,
        "run_purpose": erp.RUN_PURPOSE,
        "execution_attempt": art.normalise_execution_attempt(execution_attempt),
        "artifact_namespace": attempt_namespace(execution_attempt),
        "artifact_root": str(Path(artifact_root)),
        "sterile_base": str(Path(sterile_base)),
        "run_id_algorithm_version": art.IDENTITY_ALGORITHM_RESET_AWARE,
        "run_id_fields": [
            "run_purpose", "task_id", "condition", "task_sha256",
            "substrate_content_hash", "mode", "repetition", "reset_state",
            "execution_attempt",
        ],
        "mode": COUNTED_MODE,
        "original_scientific_plan_path": erp.RUN_PLAN_PATH,
        "original_scientific_plan_sha256": erp.plan_sha256(scientific),
        "scientific_projection_sha256": projection_sha256(scientific),
        # Restated from the scientific schedule, never re-chosen here.
        "seed": scientific["seed"],
        "tasks": scientific["tasks"],
        "conditions": scientific["conditions"],
        "reset_states": scientific["reset_states"],
        "repetitions": scientific["repetitions"],
        "block_count": scientific["block_count"],
        "run_count": scientific["run_count"],
        "model_id": scientific["model_id"],
        "runtime_version": scientific["runtime_version"],
        "task_sha256": scientific["task_sha256"],
        "architecture_context_sha256": scientific["architecture_context_sha256"],
        "pre_reset_max_turns": scientific["pre_reset_max_turns"],
        "post_reset_max_turns": scientific["post_reset_max_turns"],
        "non_reset_max_turns": scientific["non_reset_max_turns"],
        "is_result": False,
        "scored": False,
        "enters_confirmatory_dataset": False,
        "reuses_any_attempt_1_observation": False,
        "identities": [i.to_dict() for i in identities],
    }


def projection_sha256(plan: Dict[str, object]) -> str:
    """The identity of the SCIENCE alone, free of every infrastructure field.

    This is the hash a reader compares across attempts. The plan artifacts'
    physical hashes legitimately differ — one carries an attempt and a namespace
    the other predates — and comparing those would report a difference that is
    true and irrelevant.
    """
    body = json.dumps(
        [list(row) for row in scientific_projection(plan)],
        indent=2, sort_keys=True,
    ) + "\n"
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def serialise(plan: Dict[str, object]) -> str:
    return json.dumps(plan, indent=2, sort_keys=True) + "\n"


def plan_sha256(plan: Dict[str, object]) -> str:
    return hashlib.sha256(serialise(plan).encode("utf-8")).hexdigest()


def load_execution_plan(repo: Path = gov.REPO) -> Dict[str, object]:
    path = Path(repo) / REPLACEMENT_PLAN_PATH
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise gov.RunnerRefusal(
            gov.EFFICIENCY_RUN_PLAN_INVALID,
            f"the committed replacement execution plan at {path} is missing or "
            f"unreadable: {exc}",
        ) from exc


def write_execution_plan(path: Path, plan: Dict[str, object]) -> Tuple[Path, str]:
    body = serialise(plan)
    Path(path).write_text(body, encoding="utf-8", newline="\n")
    return Path(path), hashlib.sha256(body.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# The preflight (PART I / PART P)
# --------------------------------------------------------------------------- #
@dataclass
class ExecutionPreflight:
    """Everything derivable about an execution before its first row runs."""

    execution_attempt: int
    artifact_root: str
    sterile_base: Optional[str]
    identities: List[RowIdentity] = field(default_factory=list)
    problems: List[Tuple[str, str]] = field(default_factory=list)
    checks: List[Dict[str, object]] = field(default_factory=list)

    @property
    def eligible(self) -> bool:
        return not self.problems

    def to_dict(self) -> Dict[str, object]:
        return {
            "report": "afci-bench/v2/efficiency-execution-preflight",
            "authority": RESTART_DECISION,
            "run_purpose": erp.RUN_PURPOSE,
            "execution_attempt": self.execution_attempt,
            "artifact_root": self.artifact_root,
            "sterile_base": self.sterile_base,
            "row_count": len(self.identities),
            "unique_run_ids": len({i.run_id for i in self.identities}),
            "unique_artifact_dirs": len({i.artifact_dir for i in self.identities}),
            "eligible": self.eligible,
            "problem_count": len(self.problems),
            "problems": [{"code": c, "detail": d} for c, d in self.problems],
            "checks": list(self.checks),
            "identities": [i.to_dict() for i in self.identities],
            "model_invoked": False,
            "substantive_observations": 0,
            "is_result": False,
            "scored": False,
        }


def preflight(
    *,
    execution_attempt: int = REPLACEMENT_ATTEMPT,
    artifact_root: Path,
    sterile_base: Optional[Path] = None,
    repo: Path = gov.REPO,
    isolation_home: Optional[Path] = None,
    isolation_ancestors: Optional[Sequence[Path]] = None,
    check_occupancy: bool = True,
    session_id_factory: Callable[[], str] = lambda: str(uuid.uuid4()),
    #: An alternative schedule to derive identities from. Injectable so a test
    #: can demonstrate that a duplicated row REFUSES; it cannot be used to slip
    #: a schedule past the preflight, because the committed file is hashed and
    #: shape-checked independently of whatever is passed here.
    plan: Optional[Dict[str, object]] = None,
) -> ExecutionPreflight:
    """Derive and validate a whole execution, invoking nothing and writing nothing.

    A single problem makes the whole execution ineligible. There is deliberately
    no "run the rows that are fine" mode: the failure this exists to prevent is
    an execution that got nine rows in before anyone discovered its schedule was
    unsound, and a partial execution of an unsound schedule is that same failure
    with a smaller number attached to it.
    """
    root = Path(artifact_root)
    report = ExecutionPreflight(
        execution_attempt=execution_attempt,
        artifact_root=str(root),
        sterile_base=str(sterile_base) if sterile_base is not None else None,
    )

    def record(name: str, ok: bool, detail: str) -> None:
        report.checks.append({"check": name, "status": "PASS" if ok else "FAIL",
                              "detail": detail})

    committed = erp.load_plan(repo)
    scientific = committed if plan is None else plan
    plan_problems = erp.plan_problems(scientific, repo)
    report.problems.extend(
        (gov.EFFICIENCY_RUN_PLAN_INVALID, p) for p in plan_problems
    )
    record(
        "committed_scientific_schedule",
        not plan_problems,
        f"{erp.RUN_PLAN_PATH} validates as the frozen {erp.EXPECTED_RUNS}-run "
        f"schedule" if not plan_problems else "; ".join(plan_problems[:3]),
    )

    committed_sha = hashlib.sha256(
        (Path(repo) / erp.RUN_PLAN_PATH).read_bytes()
    ).hexdigest()
    same = committed_sha == ORIGINAL_SCIENTIFIC_PLAN_SHA256
    if not same:
        report.problems.append((
            gov.EFFICIENCY_RUN_PLAN_INVALID,
            f"the committed scientific schedule hashes {committed_sha}, and "
            f"{ABORT_DECISION} pins the executed one at "
            f"{ORIGINAL_SCIENTIFIC_PLAN_SHA256}; a replacement never runs a "
            "schedule the aborted execution did not",
        ))
    record("scientific_schedule_unchanged", same, committed_sha)

    # Identity, for the replacement and for the aborted execution it must miss.
    identities = derive_schedule_identities(
        scientific, execution_attempt=execution_attempt,
        artifact_root=root, repo=repo,
    )
    report.identities = identities

    dupes = identity_problems(identities)
    report.problems.extend(dupes)
    record(
        "unique_identities",
        not dupes,
        f"{len({i.run_id for i in identities})} unique run ids and "
        f"{len({i.artifact_dir for i in identities})} unique artifact "
        f"directories across {len(identities)} rows",
    )

    aborted = attempt_1_identities(scientific, artifact_root=root, repo=repo)
    overlaps = overlap_problems(identities, aborted)
    report.problems.extend(overlaps)
    record(
        "no_overlap_with_aborted_attempt",
        not overlaps,
        f"zero of {len(identities)} identities coincide with Attempt "
        f"{ABORTED_ATTEMPT}'s {len({i.run_id for i in aborted})} minted ids",
    )

    # The replacement's schedule against the COMMITTED one. When no plan is
    # injected these are the same object and the check is trivially true; the
    # comparison is written against ``committed`` anyway so that an injected
    # schedule is measured against the frozen science rather than against itself.
    projection = projection_problems(scientific, committed)
    report.problems.extend(projection)
    record(
        "scientific_projection_preserved",
        not projection,
        f"projection sha256 {projection_sha256(committed)}",
    )

    sessions = session_allocation_problems(
        scientific, session_id_factory=session_id_factory
    )
    report.problems.extend(sessions)
    slots = session_slots(scientific)
    record(
        "session_allocation",
        not sessions,
        f"{len(slots)} session slots across {len(identities)} rows "
        f"({sum(1 for _, p in slots if p)} reset phases), all distinct",
    )

    isolation = art.execution_root_isolation_problems(
        root, home=isolation_home, ancestors=isolation_ancestors
    )
    if sterile_base is not None:
        isolation += art.execution_root_isolation_problems(
            Path(sterile_base), home=isolation_home, ancestors=isolation_ancestors
        )
    report.problems.extend(isolation)
    record(
        "isolated_execution_roots",
        not isolation,
        "artifact root and sterile base are outside the active user profile and "
        "carry no host context material on their ancestor chains"
        if not isolation
        else "; ".join(d for _, d in isolation[:3]),
    )

    if check_occupancy:
        occupied = occupancy_problems(identities)
        report.problems.extend(occupied)
        record(
            "destinations_unoccupied",
            not occupied,
            f"none of the {len(identities)} destinations exists",
        )

    return report


# --------------------------------------------------------------------------- #
# The aborted execution's evidence inventory (PART B)
# --------------------------------------------------------------------------- #
#: The evidence files a row of each arm produces, by reset state. A RESET run is
#: two processes and writes two streams; a NON_RESET run is one and writes one.
#: The distinction is also the only reliable way to attribute a run record found
#: in a directory two sequences derived, which is why it is data rather than a
#: reading of a filename.
RUNTIME_EVIDENCE_BY_ARM: Dict[str, Tuple[str, ...]] = {
    rb.NON_RESET: ("runtime_evidence.jsonl",),
    rb.RESET: (
        "phase_a_runtime_evidence.jsonl",
        "phase_b_runtime_evidence.jsonl",
    ),
}

#: Statuses an inventoried row can carry. They are NOT analysis outcomes: none
#: of them says anything about what a run cost or produced.
ROW_INTACT = "INTACT_GOVERNED_OBSERVATION"
ROW_RECORD_OVERWRITTEN = "DAMAGED_GOVERNED_RECORD_OVERWRITTEN"
ROW_POST_DELIVERY_REFUSAL = "DAMAGED_POST_DELIVERY_COLLIDING_OBSERVATION"
ROW_NOT_STARTED = "NOT_STARTED"


def _row_arm_from_record(record: Dict[str, object]) -> Optional[str]:
    """Which arm a run record describes, read from what the launch carried.

    ``reset.reset_state`` is the direct answer and is absent from exactly the
    record that matters most here: sequence 9's refusal happened in
    ``CAPTURE_WORKTREE``, two states before the reset block is assembled. The
    turn ceiling is present from ``BUILD_FRESH_LAUNCH`` onwards and is
    unambiguous — ``SL-V2-EFF-RESET-01`` gives a ``NON_RESET`` run a top-level
    ceiling of 64 and a ``RESET`` run none, because its two phases carry their
    own — so it attributes a record that never reached the reset block.
    """
    block = record.get("reset")
    if isinstance(block, dict) and block.get("reset_state") in rb.RESET_STATES:
        return str(block["reset_state"])
    launch = record.get("fresh_launch")
    if isinstance(launch, dict):
        ceiling = launch.get("max_turns")
        if ceiling == rb.NON_RESET_MAX_TURNS:
            return rb.NON_RESET
        if ceiling is None and launch.get("argv"):
            return rb.RESET
    return None


def inventory_attempt_1(
    *,
    obs_root: Path,
    log_root: Optional[Path] = None,
    rows_attempted: int,
    repo: Path = gov.REPO,
) -> Dict[str, object]:
    """Inventory the aborted execution's artifacts. Reads; never writes.

    Every field is derived from what is on disk, not from what the abort record
    says, so the inventory can CONTRADICT the narrative rather than confirm it.
    The one input that cannot come from disk is how many rows were attempted —
    a row that refused before creating anything leaves nothing to count — and it
    is a named argument for exactly that reason.

    The inventory is provenance. It is not a dataset, nothing in it is scored,
    and no row of it may enter a replacement execution's analysis.
    """
    import run_worktree as wt  # local: the inventory is the only reader

    scientific = erp.load_plan(repo)
    identities = attempt_1_identities(
        scientific, artifact_root=Path(obs_root), repo=repo
    )
    by_dir: Dict[str, List[RowIdentity]] = {}
    for identity in identities:
        by_dir.setdefault(identity.artifact_dir, []).append(identity)

    rows: List[Dict[str, object]] = []
    for identity in identities:
        if identity.sequence > rows_attempted:
            continue
        run_dir = Path(identity.artifact_dir)
        partners = [
            other.sequence
            for other in by_dir[identity.artifact_dir]
            if other.sequence != identity.sequence
        ]
        attempted_partners = [s for s in partners if s <= rows_attempted]

        evidence: Dict[str, object] = {}
        for name in RUNTIME_EVIDENCE_BY_ARM[identity.reset_state]:
            path = run_dir / name
            if path.is_file():
                evidence[name] = {
                    "sha256": art.sha256_file(path),
                    "bytes": path.stat().st_size,
                }

        record_path = run_dir / "run_record.json"
        record: Optional[Dict[str, object]] = None
        if record_path.is_file():
            record = json.loads(record_path.read_text(encoding="utf-8"))

        attributed_arm = _row_arm_from_record(record) if record else None
        record_is_this_row = bool(
            record
            and str(record.get("task_id")) == identity.task_id
            and str(record.get("condition")) == identity.condition
            and int(record.get("repetition") or 1) == identity.repetition
            and attributed_arm == identity.reset_state
        )
        completed = bool(
            record_is_this_row
            and str((record or {}).get("outcome", {}).get("status")) == "COMPLETE"
        )

        post_run = run_dir / "worktree_post_run"
        functional = run_dir / "functional_evaluation.json"

        # In a SHARED directory the runtime-evidence streams are attributable by
        # filename and everything else is not, so the undiscriminated artifacts
        # are attributed by what the surviving record says happened. A row whose
        # own record refused in CAPTURE_WORKTREE reached neither the capture nor
        # the functional evaluation, so the ones on disk are its partner's — and
        # reporting them as this row's is precisely the confusion an inventory
        # of a collision exists to prevent.
        capture_refused = bool(
            record_is_this_row
            and str((record or {}).get("outcome", {}).get("code"))
            == gov.PREPARED_WORKTREE_DIRTY
        )
        owns_capture = post_run.is_dir() and not capture_refused
        owns_functional = functional.is_file() and not capture_refused

        if not run_dir.exists():
            status = ROW_NOT_STARTED
        elif completed:
            status = ROW_INTACT
        elif record_is_this_row:
            # The record IS this row's and this row did not complete: the row
            # delivered its task and then refused on the collision.
            status = ROW_POST_DELIVERY_REFUSAL
        else:
            status = ROW_RECORD_OVERWRITTEN

        rows.append({
            "sequence": identity.sequence,
            "block_id": identity.block_id,
            "task_id": identity.task_id,
            "condition": identity.condition,
            "reset_state": identity.reset_state,
            "repetition": identity.repetition,
            "derived_run_id": identity.run_id,
            "artifact_dir": str(run_dir),
            "artifact_dir_exists": run_dir.exists(),
            "model_invoked": bool(evidence),
            "runtime_evidence": evidence,
            "governed_record_present": record_path.is_file(),
            "governed_record_intact_for_this_row": completed,
            "governed_record_attributed_to_arm": attributed_arm,
            "governed_record_sha256": (
                art.sha256_file(record_path) if record_path.is_file() else None
            ),
            "functional_evaluation_present": functional.is_file(),
            "functional_evaluation_attributable_to_this_row": owns_functional,
            "functional_evaluation_sha256": (
                art.sha256_file(functional) if functional.is_file() else None
            ),
            "captured_worktree_present": post_run.is_dir(),
            "captured_worktree_attributable_to_this_row": owns_capture,
            "captured_worktree": (
                wt.directory_content_hash(post_run) if post_run.is_dir() else None
            ),
            "artifact_dir_shared_with_attempted_row": bool(attempted_partners),
            "collision_partner_sequences": sorted(partners),
            "collision_partner_attempted": sorted(attempted_partners),
            "status": status,
        })

    logs: Dict[str, object] = {}
    if log_root is not None and Path(log_root).is_dir():
        for path in sorted(Path(log_root).glob("seq-*.log")):
            logs[path.name] = {
                "sha256": art.sha256_file(path),
                "bytes": path.stat().st_size,
            }

    intact = [r for r in rows if r["status"] == ROW_INTACT]
    damaged = [
        r for r in rows
        if r["status"] in {ROW_RECORD_OVERWRITTEN, ROW_POST_DELIVERY_REFUSAL}
    ]
    return {
        "record": "afci-bench/v2/afci-efficiency-pilot-attempt-1-evidence-inventory",
        "authority": ABORT_DECISION,
        "run_purpose": erp.RUN_PURPOSE,
        "execution_attempt": ABORTED_ATTEMPT,
        "disposition": "ABORTED_INFRASTRUCTURE_ATTEMPT",
        "run_id_algorithm_version": art.IDENTITY_ALGORITHM_LEGACY,
        "scheduled_rows": int(scientific["run_count"]),
        "rows_attempted": rows_attempted,
        "rows_not_started": int(scientific["run_count"]) - rows_attempted,
        "intact_governed_observations": len(intact),
        "damaged_observations": len(damaged),
        "intact_sequences": [r["sequence"] for r in intact],
        "damaged_sequences": [r["sequence"] for r in damaged],
        "collision_pairs_in_schedule": len(
            [d for d, members in by_dir.items() if len(members) > 1]
        ),
        # The four statements the abort turns on, restated as machine-checkable
        # values rather than left in prose.
        "comparative_analysis_performed": False,
        "token_ratio_analysis_performed": False,
        "pilot_decision_emitted": False,
        "continuation_threshold_evaluated": False,
        "excluded_from_every_efficiency_analysis": True,
        "poolable_with_replacement_execution": False,
        "any_artifact_reconstructed": False,
        "preserved_for": "audit and provenance only",
        "is_result": False,
        "scored": False,
        "rows": rows,
        "operator_logs": logs,
    }


def attempt_1_identities(
    plan: Dict[str, object], *, artifact_root: Path, repo: Path = gov.REPO
) -> List[RowIdentity]:
    """Reconstruct the identities Attempt 1 actually minted.

    Deliberately reconstructed under the PRE-REPAIR derivation — no reset state,
    no execution attempt — because that is what is on disk. Deriving them the
    new way would produce names Attempt 1 never used, and the disjointness proof
    would then be a proof about nothing.
    """
    return derive_schedule_identities(
        plan,
        execution_attempt=None,
        artifact_root=artifact_root,
        repo=repo,
        include_reset_state=False,
    )
