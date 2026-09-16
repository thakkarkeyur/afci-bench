#!/usr/bin/env python3
"""``SL-V2-EFF-FUNC-01``: the post-run functional-validity channel.

What this answers
-----------------
The efficiency pilot's frozen analysis pairs a ``C1`` run with a ``C4`` run and
uses the pair only when **both were functionally valid** (
``AFCI_EFFICIENCY_PILOT_DECISION.md`` §10.1, §11.0). Until now no run record
carried such a value, so the pilot was executable and **not analysable**: the
cost figures would have existed and the gate that admits them would not have
been computable. This module is that gate's input.

What it is, exactly
-------------------
An **invocation boundary and a derivation**, and nothing else:

* it contains **no acceptance logic**. The hidden suites, their cases, their
  assertions and their pass/fail semantics live in the private evaluator
  repository and are never duplicated here, never materialised into a coding
  worktree, and never read by this process;
* it invokes the private scorer **out of band, after the model has finished**,
  against the **preserved post-run worktree** — never the live one the model was
  editing, and never the canonical repository;
* it **derives** ``functional_valid`` from the returned counts. A caller cannot
  supply the verdict: the only input is a tally, and a tally that disagrees with
  the private scorer's own derivation is a refusal rather than a tie-break.

What it deliberately does not do
--------------------------------
No architecture score, no violation value, no ``E1`` numerator or denominator,
no confirmatory result, and no gate movement. ``AFCI_EFFICIENCY_PILOT`` is a
**cost-only** purpose with a functional guardrail, and this channel is the
guardrail.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import run_governance as gov

#: The Study-Lead decision that defines ``FUNCTIONAL_VALID`` and authorises this
#: channel. A purpose that does not name it gets no functional evaluation at all.
FUNCTIONAL_EVALUATION_AUTHORITY = "SL-V2-EFF-FUNC-01"
FUNCTIONAL_EVALUATION_RECORD = (
    "docs/v2/AFCI_EFFICIENCY_PILOT_FUNCTIONAL_VALIDITY_DECISION.md"
)

#: The private entry point, private-root-relative. Referenced, never vendored.
PRIVATE_SCORER = "scripts/score_worktree.py"

#: A ceiling on one post-hoc evaluation. It is harness plumbing, not science: it
#: bounds an evaluator that hung, and a run that hits it is recorded as an error
#: rather than as a failure, so a hung evaluator can never be read as a candidate
#: that did not work.
FUNCTIONAL_EVALUATION_TIMEOUT_SECONDS = 1800

FUNCTIONAL_EVALUATION_NOT_AUTHORISED = "FUNCTIONAL_EVALUATION_NOT_AUTHORISED"
FUNCTIONAL_EVALUATOR_UNAVAILABLE = "FUNCTIONAL_EVALUATOR_UNAVAILABLE"
FUNCTIONAL_EVALUATOR_TIMEOUT = "FUNCTIONAL_EVALUATOR_TIMEOUT"
FUNCTIONAL_EVALUATOR_NO_RESULT = "FUNCTIONAL_EVALUATOR_NO_RESULT"
FUNCTIONAL_EVALUATOR_MALFORMED_RESULT = "FUNCTIONAL_EVALUATOR_MALFORMED_RESULT"
FUNCTIONAL_VALID_NOT_DERIVABLE = "FUNCTIONAL_VALID_NOT_DERIVABLE"
FUNCTIONAL_EVALUATION_NO_WORKTREE = "FUNCTIONAL_EVALUATION_NO_WORKTREE"
FUNCTIONAL_EVALUATION_HIDDEN_PATH_LEAKED = "FUNCTIONAL_EVALUATION_HIDDEN_PATH_LEAKED"

#: Every count the derivation reads. Listed so a malformed result is caught by
#: the field that is missing rather than by the exception it later causes.
REQUIRED_COUNTS: Sequence[str] = (
    "semantic_case_count_expected",
    "semantic_case_count_executed",
    "semantic_pass_count",
    "semantic_fail_count",
    "semantic_error_count",
    "nonsemantic_case_count_expected",
    "nonsemantic_case_count_executed",
    "nonsemantic_pass_count",
    "nonsemantic_fail_count",
    "nonsemantic_error_count",
)

#: Path and file fragments that would betray hidden evaluator material. The
#: structured result is swept for them before it is recorded: a channel that
#: only *promises* to withhold the suite is not a boundary.
HIDDEN_MATERIAL_FRAGMENTS: Sequence[str] = (
    "hidden_tests",
    "hidden_runtime",
    "hidden_acceptance_plan",
    ".acceptance.spec.ts",
    "evaluator_manifest.json",
    "legitimate_alternatives",
    "architecture_opportunities",
)


# --------------------------------------------------------------------------- #
# The derivation
# --------------------------------------------------------------------------- #
def derive_functional_valid(counts: Dict[str, object]) -> bool:
    """``FUNCTIONAL_VALID``, derived mechanically from the SEMANTIC tally.

    Exactly the clauses ``SL-V2-EFF-FUNC-01`` states, and no others:

    1. every declared semantic case executed;
    2. every one of them passed;
    3. none failed;
    4. none errored or returned an indeterminate status;
    5. none is missing.

    A non-semantic case appears in **no** clause. The restraint and guard cases
    are executed and recorded, and they are reported separately, because a case
    that issues no request cannot tell a working candidate from a broken one —
    so letting one decide validity would be letting the suite grade itself.

    There is no ``functional_valid`` parameter. The verdict is not an input.
    """
    expected = _count(counts, "semantic_case_count_expected")
    return bool(
        expected > 0
        and _count(counts, "semantic_case_count_executed") == expected
        and _count(counts, "semantic_pass_count") == expected
        and _count(counts, "semantic_fail_count") == 0
        and _count(counts, "semantic_error_count") == 0
        and not list(counts.get("missing_semantic_case_ids") or [])
        and not counts.get("runtime_error")
    )


def _count(counts: Dict[str, object], key: str) -> int:
    value = counts.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise gov.RunnerRefusal(
            FUNCTIONAL_EVALUATOR_MALFORMED_RESULT,
            f"the functional result's {key!r} is {value!r}; every count the "
            "derivation reads must be an integer and none is defaulted",
        )
    if value < 0:
        raise gov.RunnerRefusal(
            FUNCTIONAL_EVALUATOR_MALFORMED_RESULT,
            f"the functional result's {key!r} is negative ({value})",
        )
    return value


def hidden_material_leaks(block: object) -> List[str]:
    """Fragments of hidden evaluator material found anywhere in a structure."""
    found: List[str] = []

    def walk(node: object) -> None:
        if isinstance(node, str):
            low = node.lower()
            found.extend(f for f in HIDDEN_MATERIAL_FRAGMENTS if f in low)
        elif isinstance(node, dict):
            for key, value in node.items():
                walk(key)
                walk(value)
        elif isinstance(node, (list, tuple)):
            for item in node:
                walk(item)

    walk(block)
    return sorted(set(found))


# --------------------------------------------------------------------------- #
# Blocks
# --------------------------------------------------------------------------- #
def _base_block(task_id: str) -> Dict[str, object]:
    return {
        "record": "afci-bench/v2/functional-evaluation",
        "authority": FUNCTIONAL_EVALUATION_AUTHORITY,
        "authority_record": FUNCTIONAL_EVALUATION_RECORD,
        "executed": False,
        "evaluator_task": task_id,
        "evaluator_version": None,
        "evaluator_runtime_sha256": None,
        "evaluator_suite_sha256": None,
        "semantic_case_count_expected": 0,
        "semantic_case_count_executed": 0,
        "semantic_pass_count": 0,
        "semantic_fail_count": 0,
        "semantic_error_count": 0,
        "nonsemantic_case_count_expected": 0,
        "nonsemantic_case_count_executed": 0,
        "nonsemantic_pass_count": 0,
        "nonsemantic_fail_count": 0,
        "nonsemantic_error_count": 0,
        "missing_case_ids": [],
        "missing_semantic_case_ids": [],
        "indeterminate_case_ids": [],
        "duplicate_case_ids": [],
        "unexpected_case_ids": [],
        "runtime_error": None,
        "functional_valid": False,
        "functional_valid_derived_by": "experiments/v2/harness/functional_evaluation.py",
        "functional_valid_is_derived": True,
        "nonsemantic_cases_do_not_determine_validity": True,
        "architecture_scored": False,
        "scorer": {},
    }


def not_executed(task_id: str, code: str, detail: str,
                 **extra: object) -> Dict[str, object]:
    """A complete, fail-closed block for an evaluation that did not happen.

    Written rather than omitted. An absent block and an invalid one are
    different facts, and the frozen analysis must be able to tell "this run was
    not functionally valid" from "nobody looked".
    """
    block = _base_block(task_id)
    block["runtime_error"] = {"code": code, "detail": detail}
    block.update(extra)
    block["functional_valid"] = False
    return block


def purpose_requires_functional_evaluation(purpose: Optional[gov.RunPurpose]) -> bool:
    """True only for a purpose a Study-Lead decision put this channel on."""
    return bool(purpose is not None and purpose.functional_evaluation_authority)


# --------------------------------------------------------------------------- #
# The private invocation boundary
# --------------------------------------------------------------------------- #
def scorer_path(private_root: Optional[Path] = None) -> Path:
    root = Path(private_root) if private_root else gov.default_private_root()
    return root / PRIVATE_SCORER


def evaluate_preserved_worktree(
    task_id: str,
    worktree: Optional[Path],
    *,
    result_path: Path,
    private_root: Optional[Path] = None,
    timeout_seconds: int = FUNCTIONAL_EVALUATION_TIMEOUT_SECONDS,
    python_executable: Optional[str] = None,
) -> Dict[str, object]:
    """Score a preserved post-run worktree and return the run record's block.

    Fail-closed at every step, and every failure is RECORDED rather than raised:
    a functional evaluation that could not be performed is a run that is not
    functionally valid, which is exactly what the frozen analysis needs to see.
    The single exception is a leak — hidden evaluator material appearing in the
    structured result is a boundary breach, and the record is refused rather
    than written with the leak in it.
    """
    if worktree is None:
        return not_executed(
            task_id,
            FUNCTIONAL_EVALUATION_NO_WORKTREE,
            "no post-run worktree was preserved, so there is nothing to score; "
            "no verdict is inferred from the absence",
        )

    scorer = scorer_path(private_root)
    if not scorer.is_file():
        return not_executed(
            task_id,
            FUNCTIONAL_EVALUATOR_UNAVAILABLE,
            f"the private functional scorer is not available at {scorer}; this "
            "repository contains no acceptance logic of its own and never "
            "substitutes one",
        )

    command = [
        python_executable or sys.executable,
        str(scorer),
        "--task", task_id,
        "--worktree", str(Path(worktree).resolve()),
        "--out", str(Path(result_path)),
    ]
    Path(result_path).parent.mkdir(parents=True, exist_ok=True)

    scorer_block: Dict[str, object] = {
        "command": list(command),
        "timeout_seconds": timeout_seconds,
        # The evaluator's own console output is never read into the record: it
        # quotes the suite when the suite fails. Its SIZE and DIGEST are kept, so
        # "we discarded it" is checkable without it being disclosed.
        "stdout_quarantined": True,
        "stderr_quarantined": True,
    }

    try:
        done = subprocess.run(
            command, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return not_executed(
            task_id,
            FUNCTIONAL_EVALUATOR_TIMEOUT,
            f"the private functional scorer exceeded {timeout_seconds}s and was "
            "abandoned; an evaluator that hung is an error, never a failing "
            "candidate",
            scorer={**scorer_block, "exit_status": None, "timed_out": True},
        )

    scorer_block.update(
        {
            "exit_status": done.returncode,
            "timed_out": False,
            "stdout_bytes": len(done.stdout or ""),
            "stderr_bytes": len(done.stderr or ""),
            "stdout_sha256": _digest(done.stdout),
            "stderr_sha256": _digest(done.stderr),
        }
    )

    result_file = Path(result_path)
    if not result_file.is_file():
        return not_executed(
            task_id,
            FUNCTIONAL_EVALUATOR_NO_RESULT,
            "the private functional scorer produced no structured result; its "
            "console output is quarantined and is not read in its place",
            scorer=scorer_block,
        )
    try:
        result = json.loads(result_file.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        return not_executed(
            task_id,
            FUNCTIONAL_EVALUATOR_MALFORMED_RESULT,
            f"the structured functional result is unreadable: {type(exc).__name__}",
            scorer=scorer_block,
        )
    if not isinstance(result, dict):
        return not_executed(
            task_id,
            FUNCTIONAL_EVALUATOR_MALFORMED_RESULT,
            "the structured functional result is not an object",
            scorer=scorer_block,
        )

    leaks = hidden_material_leaks(result)
    if leaks:
        raise gov.RunnerRefusal(
            FUNCTIONAL_EVALUATION_HIDDEN_PATH_LEAKED,
            f"the structured functional result names hidden evaluator material "
            f"{leaks}; the boundary exists so that a run record can be read by "
            "anyone, and a record carrying it is refused rather than written",
        )

    return _block_from_result(task_id, result, scorer_block)


def _digest(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def _block_from_result(
    task_id: str, result: Dict[str, object], scorer_block: Dict[str, object]
) -> Dict[str, object]:
    """Fold a structured private result into the run record's block.

    The counts are copied. The verdict is **not**: it is re-derived here, and the
    private scorer's own derivation is checked against it. Two independent
    derivations that disagree mean one of them is wrong, and the honest response
    is to record neither.
    """
    reported_task = result.get("evaluator_task")
    if reported_task != task_id:
        return not_executed(
            task_id,
            FUNCTIONAL_EVALUATOR_MALFORMED_RESULT,
            f"the functional result is for {reported_task!r} and this run is "
            f"{task_id!r}; a result is never re-attributed",
            scorer=scorer_block,
        )
    missing_fields = [f for f in REQUIRED_COUNTS if f not in result]
    if missing_fields:
        return not_executed(
            task_id,
            FUNCTIONAL_EVALUATOR_MALFORMED_RESULT,
            f"the functional result omits {missing_fields}",
            scorer=scorer_block,
        )

    block = _base_block(task_id)
    for field in REQUIRED_COUNTS:
        block[field] = result[field]
    for field in (
        "evaluator_version",
        "evaluator_runtime_sha256",
        "evaluator_suite_sha256",
        "missing_case_ids",
        "missing_semantic_case_ids",
        "indeterminate_case_ids",
        "duplicate_case_ids",
        "unexpected_case_ids",
        "runtime_error",
        "assertions_per_case",
        "worktree_unchanged_during_evaluation",
        "transport",
    ):
        if field in result:
            block[field] = result[field]
    block["executed"] = bool(result.get("executed"))
    block["scorer"] = scorer_block

    try:
        derived = derive_functional_valid(block)
    except gov.RunnerRefusal as refusal:
        return not_executed(
            task_id, refusal.code, refusal.message, scorer=scorer_block
        )

    supplied = result.get("functional_valid")
    if isinstance(supplied, bool) and supplied != derived:
        return not_executed(
            task_id,
            FUNCTIONAL_VALID_NOT_DERIVABLE,
            "the private scorer's verdict and this runner's derivation disagree "
            f"(scorer={supplied}, derived={derived}); neither is recorded",
            scorer=scorer_block,
        )
    if block["executed"] and derived and block.get("runtime_error"):
        return not_executed(
            task_id,
            FUNCTIONAL_VALID_NOT_DERIVABLE,
            "the functional result reports a runtime error and a valid verdict "
            "at once; a run that errored is never functionally valid",
            scorer=scorer_block,
        )
    block["functional_valid"] = bool(derived and block["executed"])
    return block
