#!/usr/bin/env python3
"""The frozen 36-run schedule for the ``AFCI_EFFICIENCY_PILOT``.

The design
----------
18 **blocks**, one per (task, reset state, repetition)::

    {PT01, PT04, PT07} x {NON_RESET, RESET} x {R1, R2, R3}

Each block holds exactly **one C1 and one C4** run, which is what makes the
analysis paired: the two runs in a block differ in the condition and in nothing
else — same task, same reset state, same repetition index, same model, same
runtime, same budget, same substrate.

Two orders are randomised, both deterministically:

* **within a block**, which condition runs first, so a drift over the session —
  a warming cache, a changing service, an operator getting tired — cannot land
  systematically on one arm;
* **across blocks**, so the tasks and reset states are interleaved rather than
  run in three long homogeneous stretches.

Why not ``random.Random``
-------------------------
Because "deterministic" has to mean deterministic on someone else's machine, in
five years, on a different Python. ``random.shuffle``'s output is a property of
an implementation, not of a specification. Every ordering here is instead a
**sort by SHA-256 of a seeded string**, which is defined by the hash and nothing
else and can be recomputed by hand if it ever has to be.

This module builds the plan. It does not run it.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import reset_budget as rb
import run_governance as gov

#: The frozen seed. Changing it changes the schedule, which is why it is a
#: recorded constant rather than a parameter with a default.
SEED = "AFCI_EFFICIENCY_PILOT_V1_20260914"

RUN_PURPOSE = "AFCI_EFFICIENCY_PILOT"
TASKS: Tuple[str, ...] = ("PT01", "PT04", "PT07")
CONDITIONS: Tuple[str, ...] = ("C1", "C4")
RESET_STATES: Tuple[str, ...] = (rb.NON_RESET, rb.RESET)
REPETITIONS: Tuple[int, ...] = (1, 2, 3)

#: 3 tasks x 2 reset states x 3 repetitions.
EXPECTED_BLOCKS = len(TASKS) * len(RESET_STATES) * len(REPETITIONS)
#: ...each carrying one C1 and one C4.
EXPECTED_RUNS = EXPECTED_BLOCKS * len(CONDITIONS)

#: Where the committed schedule lives, repository-relative.
RUN_PLAN_PATH = "docs/v2/AFCI_EFFICIENCY_PILOT_RUN_PLAN.json"


def _key(*parts: object) -> str:
    return hashlib.sha256("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()


def block_id(task: str, reset_state: str, repetition: int) -> str:
    return f"{task}|{reset_state}|R{repetition}"


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
    pre_reset_turn_limit: object
    post_reset_turn_limit: object

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
            "pre_reset_turn_limit": self.pre_reset_turn_limit,
            "post_reset_turn_limit": self.post_reset_turn_limit,
            "run_purpose": RUN_PURPOSE,
            "is_result": False,
            "scored": False,
        }


def build_blocks(seed: str = SEED) -> List[Dict[str, object]]:
    """The 18 paired blocks, in their deterministic execution order."""
    blocks = []
    for task in TASKS:
        for state in RESET_STATES:
            for rep in REPETITIONS:
                bid = block_id(task, state, rep)
                ordered = sorted(CONDITIONS, key=lambda c: _key(seed, "cond", bid, c))
                blocks.append(
                    {
                        "block_id": bid,
                        "task_id": task,
                        "reset_state": state,
                        "repetition": rep,
                        "condition_order": ordered,
                        "order_key": _key(seed, "block", bid),
                    }
                )
    blocks.sort(key=lambda b: b["order_key"])
    return blocks


def build_plan(seed: str = SEED, repo: Path = gov.REPO) -> Dict[str, object]:
    """The full 36-run plan, with the identity of everything it pins."""
    blocks = build_blocks(seed)
    runs: List[PlannedRun] = []
    sequence = 0
    for block in blocks:
        state = str(block["reset_state"])
        budget = rb.budget_block(
            run_purpose=RUN_PURPOSE, reset_state=state, repo=repo
        )
        for position, condition in enumerate(block["condition_order"], start=1):
            sequence += 1
            runs.append(
                PlannedRun(
                    sequence=sequence,
                    block_id=str(block["block_id"]),
                    task_id=str(block["task_id"]),
                    condition=str(condition),
                    reset_state=state,
                    repetition=int(block["repetition"]),
                    position_in_block=position,
                    max_turns=budget["max_turns"],
                    pre_reset_turn_limit=budget["pre_reset_turn_limit"],
                    post_reset_turn_limit=budget["post_reset_turn_limit"],
                )
            )

    plan = {
        "record": "afci-bench/v2/afci-efficiency-pilot-run-plan",
        "authority": "SL-V2-EFF-01",
        "budget_authority": rb.SL_V2_EFF_RESET_01,
        "checkpoint_authority": "SL-V2-EFF-CHK-01",
        "run_purpose": RUN_PURPOSE,
        "seed": seed,
        "ordering_method": (
            "sort by SHA-256 of a seeded string; no language RNG is used, so the "
            "schedule is reproducible on any machine and any Python"
        ),
        "tasks": list(TASKS),
        "conditions": list(CONDITIONS),
        "reset_states": list(RESET_STATES),
        "repetitions": list(REPETITIONS),
        "block_count": len(blocks),
        "run_count": len(runs),
        "model_id": "claude-sonnet-5",
        "runtime_version": "2.1.229",
        "task_sha256": {t: gov.expected_task_sha256(t) for t in TASKS},
        "architecture_context_sha256": gov.architecture_context_sha256(repo),
        "pre_reset_max_turns": rb.PRE_RESET_MAX_TURNS,
        "post_reset_max_turns": rb.POST_RESET_MAX_TURNS,
        "non_reset_max_turns": rb.NON_RESET_MAX_TURNS,
        "is_result": False,
        "scored": False,
        "enters_confirmatory_dataset": False,
        "blocks": [
            {k: v for k, v in b.items() if k != "order_key"} for b in blocks
        ],
        "runs": [r.to_dict() for r in runs],
    }
    return plan


def plan_sha256(plan: Dict[str, object]) -> str:
    """The plan's identity: a hash of its canonical serialisation."""
    return hashlib.sha256(serialise(plan).encode("utf-8")).hexdigest()


def serialise(plan: Dict[str, object]) -> str:
    return json.dumps(plan, indent=2, sort_keys=True) + "\n"


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

    The counts are checked, but so is the SHAPE: 18 blocks each holding exactly
    one C1 and one C4 is what makes the analysis paired, and a plan that merely
    had 36 rows could satisfy the count while pairing nothing.
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
        if len({str(r.get("reset_state")) for r in rows}) != 1:
            problems.append(f"block {bid} spans more than one reset state")
        if len({int(r.get("repetition", 0)) for r in rows}) != 1:
            problems.append(f"block {bid} spans more than one repetition")

    sequences = [int(r.get("sequence", -1)) for r in runs]
    if sequences != list(range(1, EXPECTED_RUNS + 1)):
        problems.append("run sequence numbers are not 1..36 in order")

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

    for flag in ("is_result", "scored", "enters_confirmatory_dataset"):
        if plan.get(flag) is not False:
            problems.append(f"{flag} is {plan.get(flag)!r}, not false")
    return problems


def summary(plan: Dict[str, object]) -> str:
    rows = plan.get("runs") or []
    lines = [
        f"seed {plan.get('seed')}  blocks {plan.get('block_count')}  "
        f"runs {plan.get('run_count')}",
    ]
    for run in rows:
        lines.append(
            f"  {run['sequence']:>2}. {run['task_id']} {run['condition']} "
            f"{run['reset_state']:<9} R{run['repetition']} "
            f"(block {run['block_id']}, position {run['position_in_block']})"
        )
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover - operator convenience
    plan = build_plan()
    print(summary(plan))
    print("plan sha256:", plan_sha256(plan))
