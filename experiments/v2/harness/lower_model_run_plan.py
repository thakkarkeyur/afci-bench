#!/usr/bin/env python3
"""The frozen 18-run schedule for the ``AFCI_LOWER_MODEL_PILOT``.

The design
----------
9 **blocks**, one per (task, repetition)::

    {PT01, PT04, PT07} x {R1, R2, R3}

Each block holds exactly **one C1 and one C4** run, which is what makes the
analysis paired: the two runs in a block differ in the condition and in nothing
else — same task, same repetition index, same reset state, same model, same
runtime, same budget, same substrate.

There is **one reset state**, and that is the design rather than an omission.
The Sonnet efficiency pilot crossed ``NON_RESET`` and ``RESET``; this pilot
isolates MODEL CAPABILITY as the moderator, and a difference found while two
factors moved would be attributable to either. The reset state is still carried
on every row and in every run id, because a row that simply omitted it would be
indistinguishable from a row written before reset-aware identity existed.

Two orders are randomised, both deterministically:

* **within a block**, which condition runs first, so a drift over the session —
  a warming cache, a changing service, an operator getting tired — cannot land
  systematically on one arm;
* **across blocks**, so the tasks are interleaved rather than run in three long
  homogeneous stretches.

Why not ``random.Random``
-------------------------
Because "deterministic" has to mean deterministic on someone else's machine, in
five years, on a different Python. Every ordering here is a **sort by SHA-256 of
a seeded string**, which is defined by the hash and nothing else.

Why the execution plan lives here too
-------------------------------------
The efficiency pilot split its schedule from its execution plan because the
second existed to describe a RESTART: an aborted attempt, a replacement, and the
proof that the two ran the same science. This pilot has no restart to describe.
Its execution plan is simply the schedule plus the identities it derives, so
splitting it across two modules would create two places for one fact to live.

What the preflight is for
-------------------------
Attempt 1 of the efficiency pilot discovered a deterministic run-id collision at
scientific sequence 9 — by executing into it, after the model had run and after
an earlier observation's record was already gone. Every identity in this
schedule is derivable with no model, no process and no cost, so
:func:`preflight` derives all 18 up front and refuses the WHOLE execution on a
single duplicate, a single occupied destination, a single overlap with the
Sonnet pilot's artifacts, or a single non-isolated root.

This module builds and checks the plan. It does not run it, it invokes no model,
and it creates no directories.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import efficiency_run_plan as erp
import execution_attempt as ea
import reset_budget as rb
import run_artifacts as art
import run_governance as gov

#: The frozen seed. Changing it changes the schedule, which is why it is a
#: recorded constant rather than a parameter with a default.
SEED = "AFCI_LOWER_MODEL_PILOT_V1_20260917"

RUN_PURPOSE = "AFCI_LOWER_MODEL_PILOT"
DECISION_ID = "SL-V2-LOWER-MODEL-01"

TASKS: Tuple[str, ...] = ("PT01", "PT04", "PT07")
CONDITIONS: Tuple[str, ...] = ("C1", "C4")
#: ONE arm, named rather than iterated, so a second one cannot be added by
#: widening a tuple somewhere else.
RESET_STATE = rb.NON_RESET
REPETITIONS: Tuple[int, ...] = (1, 2, 3)

#: This purpose's first and only execution. It is INFRASTRUCTURE PROVENANCE: it
#: separates this execution's artifacts from any other's and touches no task, no
#: condition, no budget, no metric and no threshold.
EXECUTION_ATTEMPT = 1

#: The run mode a counted pilot observation executes in.
COUNTED_MODE = "real"

#: 3 tasks x 3 repetitions...
EXPECTED_BLOCKS = len(TASKS) * len(REPETITIONS)
#: ...each carrying one C1 and one C4.
EXPECTED_RUNS = EXPECTED_BLOCKS * len(CONDITIONS)

#: Where the committed artifacts live, repository-relative.
RUN_PLAN_PATH = "docs/v2/AFCI_LOWER_MODEL_PILOT_RUN_PLAN.json"
EXECUTION_PLAN_PATH = "docs/v2/AFCI_LOWER_MODEL_PILOT_EXECUTION_PLAN.json"

#: The five values that ARE the scientific schedule. Everything else in a plan
#: artifact is infrastructure.
SCIENTIFIC_PROJECTION_FIELDS: Tuple[str, ...] = (
    "sequence", "task_id", "condition", "reset_state", "repetition",
)


def _key(*parts: object) -> str:
    return hashlib.sha256("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()


def block_id(task: str, repetition: int) -> str:
    return f"{task}|R{repetition}"


def pinned_model_id() -> str:
    """The exact model id, READ from the registry rather than restated here.

    A schedule that carried its own copy of the model id could disagree with the
    registry the runner checks every repetition against, and the disagreement
    would only surface on the run that hit it.
    """
    model = gov.diagnostic_primary_model(RUN_PURPOSE)
    if not model:
        raise gov.RunnerRefusal(
            gov.PRIMARY_MODEL_NOT_SELECTED,
            f"MODEL_REGISTRY.yml pins no exact_model_id for {RUN_PURPOSE}; a "
            "schedule never invents one",
        )
    return model


def pinned_runtime_version() -> str:
    """The live-validated CLI version, read from the registry for the same reason."""
    _q1, _q8, validated = gov.live_runtime_validation(RUN_PURPOSE)
    if not validated or validated == "unrecorded":
        raise gov.RunnerRefusal(
            gov.DIAGNOSTIC_RUNTIME_VERSION_MISMATCH,
            f"MODEL_REGISTRY.yml records no live-validated runtime version for "
            f"{RUN_PURPOSE}",
        )
    return validated


@dataclass(frozen=True)
class PlannedRun:
    sequence: int
    block_id: str
    task_id: str
    condition: str
    reset_state: str
    repetition: int
    position_in_block: int
    max_turns: int

    def to_dict(self) -> Dict[str, object]:
        return {
            "sequence": self.sequence,
            "block_id": self.block_id,
            "task_id": self.task_id,
            "condition": self.condition,
            "reset_state": self.reset_state,
            "repetition": self.repetition,
            "position_in_block": self.position_in_block,
            "max_turns": self.max_turns,
            "run_purpose": RUN_PURPOSE,
            "is_result": False,
            "scored": False,
        }


def build_blocks(seed: str = SEED) -> List[Dict[str, object]]:
    """The 9 paired blocks, in their deterministic execution order."""
    blocks = []
    for task in TASKS:
        for rep in REPETITIONS:
            bid = block_id(task, rep)
            ordered = sorted(CONDITIONS, key=lambda c: _key(seed, "cond", bid, c))
            blocks.append(
                {
                    "block_id": bid,
                    "task_id": task,
                    "reset_state": RESET_STATE,
                    "repetition": rep,
                    "condition_order": ordered,
                    "order_key": _key(seed, "block", bid),
                }
            )
    blocks.sort(key=lambda b: b["order_key"])
    return blocks


def build_plan(seed: str = SEED, repo: Path = gov.REPO) -> Dict[str, object]:
    """The full 18-run plan, with the identity of everything it pins."""
    blocks = build_blocks(seed)
    budget = rb.budget_block(
        run_purpose=RUN_PURPOSE, reset_state=RESET_STATE, repo=repo
    )
    runs: List[PlannedRun] = []
    sequence = 0
    for block in blocks:
        for position, condition in enumerate(block["condition_order"], start=1):
            sequence += 1
            runs.append(
                PlannedRun(
                    sequence=sequence,
                    block_id=str(block["block_id"]),
                    task_id=str(block["task_id"]),
                    condition=str(condition),
                    reset_state=RESET_STATE,
                    repetition=int(block["repetition"]),
                    position_in_block=position,
                    max_turns=budget["max_turns"],
                )
            )

    return {
        "record": "afci-bench/v2/afci-lower-model-pilot-run-plan",
        "authority": DECISION_ID,
        "budget_authority": DECISION_ID,
        "run_purpose": RUN_PURPOSE,
        "seed": seed,
        "ordering_method": (
            "sort by SHA-256 of a seeded string; no language RNG is used, so the "
            "schedule is reproducible on any machine and any Python"
        ),
        "tasks": list(TASKS),
        "conditions": list(CONDITIONS),
        "reset_states": [RESET_STATE],
        "reset_arm_authorised": False,
        "repetitions": list(REPETITIONS),
        "block_count": len(blocks),
        "run_count": len(runs),
        "model_id": pinned_model_id(),
        "runtime_version": pinned_runtime_version(),
        "task_sha256": {t: gov.expected_task_sha256(t) for t in TASKS},
        "architecture_context_sha256": gov.architecture_context_sha256(repo),
        "non_reset_max_turns": budget["max_turns"],
        "measures_architecture_quality": True,
        "measures_efficiency": True,
        "channels_combined_into_one_score": False,
        "pools_with_sonnet_efficiency_pilot": False,
        "is_result": False,
        "scored": False,
        "enters_confirmatory_dataset": False,
        "blocks": [
            {k: v for k, v in b.items() if k != "order_key"} for b in blocks
        ],
        "runs": [r.to_dict() for r in runs],
    }


def serialise(plan: Dict[str, object]) -> str:
    return json.dumps(plan, indent=2, sort_keys=True) + "\n"


def plan_sha256(plan: Dict[str, object]) -> str:
    """The plan's identity: a hash of its canonical serialisation."""
    return hashlib.sha256(serialise(plan).encode("utf-8")).hexdigest()


def write_plan(path: Path, seed: str = SEED, repo: Path = gov.REPO) -> Tuple[Path, str]:
    plan = build_plan(seed, repo)
    body = serialise(plan)
    Path(path).write_text(body, encoding="utf-8", newline="\n")
    return Path(path), hashlib.sha256(body.encode("utf-8")).hexdigest()


def load_plan(repo: Path = gov.REPO) -> Dict[str, object]:
    path = Path(repo) / RUN_PLAN_PATH
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise gov.RunnerRefusal(
            gov.EFFICIENCY_RUN_PLAN_INVALID,
            f"the committed run plan at {path} is missing or unreadable: {exc}",
        ) from exc


def plan_problems(plan: Dict[str, object], repo: Path = gov.REPO) -> List[str]:
    """Everything wrong with a plan. Empty means it is the frozen schedule.

    The counts are checked, but so is the SHAPE: 9 blocks each holding exactly
    one C1 and one C4 is what makes the analysis paired, and a plan that merely
    had 18 rows could satisfy the count while pairing nothing.
    """
    problems: List[str] = []
    if plan.get("seed") != SEED:
        problems.append(f"seed is {plan.get('seed')!r}, not {SEED!r}")
    if plan.get("run_purpose") != RUN_PURPOSE:
        problems.append(f"run_purpose is {plan.get('run_purpose')!r}")

    blocks = plan.get("blocks")
    runs = plan.get("runs")
    if not isinstance(blocks, list) or len(blocks) != EXPECTED_BLOCKS:
        problems.append(
            f"expected {EXPECTED_BLOCKS} blocks, got "
            f"{len(blocks) if isinstance(blocks, list) else blocks!r}"
        )
        return problems
    if not isinstance(runs, list) or len(runs) != EXPECTED_RUNS:
        problems.append(
            f"expected {EXPECTED_RUNS} runs, got "
            f"{len(runs) if isinstance(runs, list) else runs!r}"
        )
        return problems

    by_block: Dict[str, List[dict]] = {}
    for run in runs:
        by_block.setdefault(str(run.get("block_id")), []).append(run)
    if len(by_block) != EXPECTED_BLOCKS:
        problems.append(f"runs span {len(by_block)} blocks, not {EXPECTED_BLOCKS}")
    for bid, rows in sorted(by_block.items()):
        conditions = sorted(str(r.get("condition")) for r in rows)
        if conditions != ["C1", "C4"]:
            problems.append(f"block {bid} holds conditions {conditions}, not [C1, C4]")
        if len({str(r.get("task_id")) for r in rows}) != 1:
            problems.append(f"block {bid} spans more than one task")
        if len({int(r.get("repetition", 0)) for r in rows}) != 1:
            problems.append(f"block {bid} spans more than one repetition")

    # The single arm, asserted per row rather than only in the header. A header
    # that said NON_RESET over rows that did not would still derive reset-aware
    # identities for an arm nothing froze an allowance for.
    off_arm = sorted(
        {str(r.get("reset_state")) for r in runs if r.get("reset_state") != RESET_STATE}
    )
    if off_arm:
        problems.append(
            f"rows carry reset states {off_arm}; {DECISION_ID} authorises "
            f"{RESET_STATE} only"
        )
    if plan.get("reset_states") != [RESET_STATE]:
        problems.append(f"reset_states is {plan.get('reset_states')!r}")

    sequences = [int(r.get("sequence", -1)) for r in runs]
    if sequences != list(range(1, EXPECTED_RUNS + 1)):
        problems.append(f"run sequence numbers are not 1..{EXPECTED_RUNS} in order")

    ceiling = rb.turn_budget(
        run_purpose=RUN_PURPOSE, reset_state=RESET_STATE, repo=repo
    ).max_turns
    wrong = sorted({r.get("max_turns") for r in runs if r.get("max_turns") != ceiling})
    if wrong:
        problems.append(
            f"rows carry turn ceilings {wrong}; {DECISION_ID} freezes {ceiling}, "
            "identically for both conditions"
        )

    for task, sha in (plan.get("task_sha256") or {}).items():
        try:
            expected = gov.expected_task_sha256(str(task))
        except gov.RunnerRefusal as exc:
            problems.append(exc.message)
            continue
        if sha != expected:
            problems.append(f"{task} plan hash {sha!r} != index hash {expected!r}")
    if plan.get("architecture_context_sha256") != gov.architecture_context_sha256(repo):
        problems.append("the plan's architecture context hash is not the current one")

    # Re-derived from the registry, never taken from the plan on trust.
    try:
        if plan.get("model_id") != pinned_model_id():
            problems.append(
                f"the plan pins model {plan.get('model_id')!r}; the registry pins "
                f"{pinned_model_id()!r}"
            )
        if plan.get("runtime_version") != pinned_runtime_version():
            problems.append(
                f"the plan pins runtime {plan.get('runtime_version')!r}; the "
                f"registry records {pinned_runtime_version()!r} as live-validated"
            )
    except gov.RunnerRefusal as exc:
        problems.append(exc.message)

    for flag in (
        "is_result", "scored", "enters_confirmatory_dataset",
        "channels_combined_into_one_score", "pools_with_sonnet_efficiency_pilot",
        "reset_arm_authorised",
    ):
        if plan.get(flag) is not False:
            problems.append(f"{flag} is {plan.get(flag)!r}, not false")
    for flag in ("measures_architecture_quality", "measures_efficiency"):
        if plan.get(flag) is not True:
            problems.append(f"{flag} is {plan.get(flag)!r}, not true")
    return problems


def summary(plan: Dict[str, object]) -> str:
    rows = plan.get("runs") or []
    lines = [
        f"seed {plan.get('seed')}  blocks {plan.get('block_count')}  "
        f"runs {plan.get('run_count')}  model {plan.get('model_id')}",
    ]
    for run in rows:
        lines.append(
            f"  {run['sequence']:>2}. {run['task_id']} {run['condition']} "
            f"{run['reset_state']:<9} R{run['repetition']} "
            f"(block {run['block_id']}, position {run['position_in_block']})"
        )
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# The scientific projection
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


def projection_sha256(plan: Dict[str, object]) -> str:
    """The identity of the SCIENCE alone, free of every infrastructure field."""
    body = json.dumps(
        [list(row) for row in scientific_projection(plan)], indent=2, sort_keys=True
    ) + "\n"
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Whole-schedule identity derivation
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
    artifact_root: Path,
    execution_attempt: Optional[int] = EXECUTION_ATTEMPT,
    mode: str = COUNTED_MODE,
    repo: Path = gov.REPO,
) -> List[RowIdentity]:
    """Derive every scheduled row's run id and artifact directory."""
    substrate = gov.SUBSTRATE_CONTENT_HASH
    root = Path(artifact_root)
    identities: List[RowIdentity] = []
    for row in plan.get("runs") or []:
        task_id = str(row["task_id"])
        run_id = art.derive_run_id(
            purpose=RUN_PURPOSE,
            task_id=task_id,
            condition=str(row["condition"]),
            task_sha=gov.expected_task_sha256(task_id),
            substrate_hash=substrate,
            mode=mode,
            repetition=int(row["repetition"]),
            reset_state=str(row["reset_state"]),
            execution_attempt=execution_attempt,
        )
        identities.append(
            RowIdentity(
                sequence=int(row["sequence"]),
                block_id=str(row["block_id"]),
                task_id=task_id,
                condition=str(row["condition"]),
                reset_state=str(row["reset_state"]),
                repetition=int(row["repetition"]),
                run_id=run_id,
                artifact_dir=str(root / run_id),
            )
        )
    return identities


def identity_problems(identities: Sequence[RowIdentity]) -> List[Tuple[str, str]]:
    """Every duplicate run id and duplicate artifact directory in a schedule."""
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
                    f"R{first.repetition}) and sequence {identity.sequence} "
                    f"({identity.task_id}/{identity.condition}/"
                    f"R{identity.repetition}) derive one {label}: {value}",
                ))
            else:
                seen[value] = identity
    return problems


def sonnet_pilot_run_ids(repo: Path = gov.REPO) -> Sequence[str]:
    """Every run id the claude-sonnet-5 efficiency pilot has ever minted.

    BOTH of its executions: the aborted Attempt 1, whose artifacts carry the
    pre-repair legacy identity form, and the completed Attempt 2. Reconstructed
    from the committed efficiency schedule rather than read off a disk that may
    have been tidied, so the disjointness statement holds even where the
    artifacts no longer do.
    """
    scientific = erp.load_plan(repo)
    ids = {
        identity.run_id
        for identity in ea.attempt_1_identities(
            scientific, artifact_root=Path("/unused"), repo=repo
        )
    }
    ids |= {
        identity.run_id
        for identity in ea.derive_schedule_identities(
            scientific,
            execution_attempt=ea.REPLACEMENT_ATTEMPT,
            artifact_root=Path("/unused"),
            repo=repo,
        )
    }
    return sorted(ids)


def sonnet_overlap_problems(
    identities: Sequence[RowIdentity], repo: Path = gov.REPO
) -> List[Tuple[str, str]]:
    """Refuse any identity this pilot shares with the Sonnet efficiency pilot.

    Structurally impossible — the run purpose is part of the identity seed — and
    therefore cheap to prove, which is the point: "zero overlap with previous
    Sonnet artifacts" is a claim this pilot's readiness makes, and a claim that
    is checked is worth more than a claim that is argued.
    """
    problems: List[Tuple[str, str]] = []
    prior = set(sonnet_pilot_run_ids(repo))
    for identity in identities:
        if identity.run_id in prior:
            problems.append((
                gov.EFFICIENCY_SCHEDULE_IDENTITY_COLLISION,
                f"sequence {identity.sequence} derives run id {identity.run_id}, "
                "which the claude-sonnet-5 efficiency pilot already minted",
            ))
        if Path(identity.artifact_dir).name in prior:
            problems.append((
                gov.EFFICIENCY_SCHEDULE_IDENTITY_COLLISION,
                f"sequence {identity.sequence} derives artifact directory name "
                f"{Path(identity.artifact_dir).name}, which the efficiency pilot "
                "already used",
            ))
    return problems


def occupancy_problems(identities: Sequence[RowIdentity]) -> List[Tuple[str, str]]:
    """Refuse a schedule whose destinations are already occupied on disk."""
    problems: List[Tuple[str, str]] = []
    for identity in identities:
        path = Path(identity.artifact_dir)
        if not path.exists():
            continue
        entries = sorted(p.name for p in path.iterdir()) if path.is_dir() else []
        problems.append((
            gov.ARTIFACT_IDENTITY_COLLISION_PREINVOCATION,
            f"sequence {identity.sequence}'s destination {path} already exists "
            f"and holds {entries[:8] or 'no entries'}; an execution begins in "
            "unoccupied directories and never reclaims one",
        ))
    return problems


def session_slots(plan: Dict[str, object]) -> List[Tuple[int, Optional[str]]]:
    """Every (sequence, phase) a model session will be minted for.

    One per row. This pilot runs no reset, so no row allocates two.
    """
    return [(int(row["sequence"]), None) for row in plan.get("runs") or []]


def session_allocation_problems(
    plan: Dict[str, object],
    *,
    session_id_factory: Callable[[], str] = lambda: str(uuid.uuid4()),
) -> List[Tuple[str, str]]:
    """Prove the schedule's session allocation admits no reuse.

    It does NOT predict the session ids the execution will use — those are
    minted at launch, and a preflight that printed ids and called them "the
    session ids" would be describing sessions that never existed. It proves the
    POLICY cannot produce a reused identity.
    """
    problems: List[Tuple[str, str]] = []
    slots = session_slots(plan)
    if len(set(slots)) != len(slots):
        problems.append((
            gov.RESET_PHASE_SESSION_REUSED,
            "the schedule allocates one session slot to two rows",
        ))
    if len(slots) != EXPECTED_RUNS:
        problems.append((
            gov.RESET_PHASE_SESSION_REUSED,
            f"the schedule allocates {len(slots)} session slots for "
            f"{EXPECTED_RUNS} rows",
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
        int(row["sequence"]) for row in plan.get("runs") or [] if row.get("session_id")
    ]
    if declared:
        problems.append((
            gov.SESSION_ID_REUSED,
            f"rows {declared} carry a pre-declared session id; every session is "
            "minted fresh at launch and none is scheduled in advance",
        ))
    return problems


# --------------------------------------------------------------------------- #
# The execution plan artifact
# --------------------------------------------------------------------------- #
def build_execution_plan(
    *,
    artifact_root: Path,
    sterile_base: Path,
    execution_attempt: int = EXECUTION_ATTEMPT,
    seed: str = SEED,
    repo: Path = gov.REPO,
) -> Dict[str, object]:
    """The execution plan: the frozen science plus the identities it derives.

    The scientific half is the committed schedule VERBATIM — loaded, not rebuilt,
    so this artifact cannot quietly re-randomise anything — and the
    infrastructure half is the attempt, the identity algorithm and the derived
    identities. Their separation is the point: a reader can hash the projection
    and compare it with the schedule's without reading a word of prose.
    """
    scientific = load_plan(repo)
    problems = plan_problems(scientific, repo)
    if problems:
        raise gov.RunnerRefusal(
            gov.EFFICIENCY_RUN_PLAN_INVALID,
            "the committed scientific schedule does not validate: "
            + "; ".join(problems[:4]),
        )
    identities = derive_schedule_identities(
        scientific,
        artifact_root=artifact_root,
        execution_attempt=execution_attempt,
        repo=repo,
    )
    return {
        "record": "afci-bench/v2/afci-lower-model-pilot-execution-plan",
        "authority": DECISION_ID,
        "run_purpose": RUN_PURPOSE,
        "execution_attempt": art.normalise_execution_attempt(execution_attempt),
        "artifact_namespace": f"attempt-{execution_attempt}",
        "artifact_root": str(Path(artifact_root)),
        "sterile_base": str(Path(sterile_base)),
        "run_id_algorithm_version": art.IDENTITY_ALGORITHM_RESET_AWARE,
        "run_id_fields": [
            "run_purpose", "task_id", "condition", "task_sha256",
            "substrate_content_hash", "mode", "repetition", "reset_state",
            "execution_attempt",
        ],
        "mode": COUNTED_MODE,
        "scientific_plan_path": RUN_PLAN_PATH,
        "scientific_plan_sha256": plan_sha256(scientific),
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
        "non_reset_max_turns": scientific["non_reset_max_turns"],
        "is_result": False,
        "scored": False,
        "enters_confirmatory_dataset": False,
        "reuses_any_sonnet_pilot_observation": False,
        "overlapping_sonnet_run_ids": 0,
        "identities": [i.to_dict() for i in identities],
    }


def execution_plan_sha256(plan: Dict[str, object]) -> str:
    return hashlib.sha256(serialise(plan).encode("utf-8")).hexdigest()


def write_execution_plan(path: Path, plan: Dict[str, object]) -> Tuple[Path, str]:
    body = serialise(plan)
    Path(path).write_text(body, encoding="utf-8", newline="\n")
    return Path(path), hashlib.sha256(body.encode("utf-8")).hexdigest()


def load_execution_plan(repo: Path = gov.REPO) -> Dict[str, object]:
    path = Path(repo) / EXECUTION_PLAN_PATH
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise gov.RunnerRefusal(
            gov.EFFICIENCY_RUN_PLAN_INVALID,
            f"the committed execution plan at {path} is missing or unreadable: {exc}",
        ) from exc


# --------------------------------------------------------------------------- #
# The preflight
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
            "report": "afci-bench/v2/lower-model-execution-preflight",
            "authority": DECISION_ID,
            "run_purpose": RUN_PURPOSE,
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
    artifact_root: Path,
    sterile_base: Optional[Path] = None,
    execution_attempt: int = EXECUTION_ATTEMPT,
    repo: Path = gov.REPO,
    isolation_home: Optional[Path] = None,
    isolation_ancestors: Optional[Sequence[Path]] = None,
    check_occupancy: bool = True,
    session_id_factory: Callable[[], str] = lambda: str(uuid.uuid4()),
    plan: Optional[Dict[str, object]] = None,
) -> ExecutionPreflight:
    """Derive and validate a whole execution, invoking nothing and writing nothing.

    A single problem makes the whole execution ineligible. There is deliberately
    no "run the rows that are fine" mode: a partial execution of an unsound
    schedule is the failure this exists to prevent, with a smaller number
    attached to it.
    """
    root = Path(artifact_root)
    report = ExecutionPreflight(
        execution_attempt=execution_attempt,
        artifact_root=str(root),
        sterile_base=str(sterile_base) if sterile_base is not None else None,
    )

    def record(name: str, ok: bool, detail: str) -> None:
        report.checks.append(
            {"check": name, "status": "PASS" if ok else "FAIL", "detail": detail}
        )

    committed = load_plan(repo)
    scientific = committed if plan is None else plan
    schedule_problems = plan_problems(scientific, repo)
    report.problems.extend(
        (gov.EFFICIENCY_RUN_PLAN_INVALID, p) for p in schedule_problems
    )
    record(
        "committed_scientific_schedule",
        not schedule_problems,
        f"{RUN_PLAN_PATH} validates as the frozen {EXPECTED_RUNS}-run schedule"
        if not schedule_problems
        else "; ".join(schedule_problems[:3]),
    )

    identities = derive_schedule_identities(
        scientific,
        artifact_root=root,
        execution_attempt=execution_attempt,
        repo=repo,
    )
    report.identities = identities

    dupes = identity_problems(identities)
    report.problems.extend(dupes)
    record(
        "unique_identities",
        not dupes,
        f"{len({i.run_id for i in identities})} unique run ids and "
        f"{len({i.artifact_dir for i in identities})} unique artifact directories "
        f"across {len(identities)} rows",
    )

    overlaps = sonnet_overlap_problems(identities, repo)
    report.problems.extend(overlaps)
    record(
        "no_overlap_with_the_sonnet_efficiency_pilot",
        not overlaps,
        f"zero of {len(identities)} identities coincide with the efficiency "
        f"pilot's {len(sonnet_pilot_run_ids(repo))} minted ids across both of its "
        "executions",
    )

    sessions = session_allocation_problems(
        scientific, session_id_factory=session_id_factory
    )
    report.problems.extend(sessions)
    record(
        "session_allocation",
        not sessions,
        f"{len(session_slots(scientific))} session slots across "
        f"{len(identities)} rows (no reset phases), all distinct",
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


if __name__ == "__main__":  # pragma: no cover - operator convenience
    built = build_plan()
    print(summary(built))
    print("plan sha256:", plan_sha256(built))
    print("projection sha256:", projection_sha256(built))
