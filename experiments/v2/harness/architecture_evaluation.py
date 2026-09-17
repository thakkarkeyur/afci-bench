#!/usr/bin/env python3
"""``SL-V2-LOWER-MODEL-01``: the post-run ARCHITECTURE-quality channel.

What this answers
-----------------
The lower-capability-model pilot asks two independent questions, and the first
of them is a quality question: **does supplying the architecture context reduce
architecture violations under a weaker model?** Until now no run record carried
an architecture value at all — the efficiency pilot was explicitly COST-ONLY —
so that question was not computable from any artifact this harness produced.
This module is the input to it.

What it is, exactly
-------------------
An **invocation boundary and a derivation**, and nothing else. It is the
architecture counterpart of :mod:`functional_evaluation`, and it is deliberately
built the same way:

* it contains **no scoring logic**. The architecture oracle, the frozen
  per-task decision, the rule catalog's applicability and the opportunity
  accounting live in the public oracle and the private evaluator, and are never
  duplicated here;
* it invokes the private scorer **out of band, after the model has finished**,
  against the **preserved post-run worktree** — never the live one the model was
  editing, and never the canonical repository;
* it **derives** ``architecture_violation_present`` from the returned counts. A
  caller cannot supply the verdict, and a scorer whose own target-violation
  boolean disagrees with the counts is a refusal rather than a tie-break.

The two channels never meet
---------------------------
Architecture scoring is separate from functional scoring in both directions. No
value here can move a functional verdict, and no functional verdict can move a
value here. They are written into different blocks of the run record, derived by
different modules, produced by different private entry points, and the frozen
analysis reads them for different questions. A single combined score would hide
exactly the case this pilot exists to find — architecture quality improving
while token cost rises.

What the coding model sees
--------------------------
**Nothing of this.** The scorer runs after the model's process has ended. The
model is never given the architecture scorer, its rules, the hidden opportunity
definitions, the target rule identities or any other hidden evaluator material,
and none of it is present in its prepared worktree or its prompt. The private
scorer returns counts, a boolean and a one-way digest; this module sweeps the
structured result for private identifiers and **refuses to write a record** that
carries one.

What this is not
----------------
No ``E1`` numerator, no ``E1`` denominator, no confirmatory result and no gate
movement. The measurement is a **descriptive, non-confirmatory** endpoint of one
quarantined pilot.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import functional_evaluation as fe
import run_governance as gov

#: The Study-Lead decision that authorises this channel. A purpose that does not
#: name it gets no architecture evaluation at all.
ARCHITECTURE_EVALUATION_AUTHORITY = "SL-V2-LOWER-MODEL-01"
ARCHITECTURE_EVALUATION_RECORD = "docs/v2/AFCI_LOWER_MODEL_PILOT_DECISION.md"

#: The private entry point, private-root-relative. Referenced, never vendored.
PRIVATE_SCORER = "scripts/score_architecture.py"

#: A ceiling on one post-hoc scoring. Harness plumbing, not science: it bounds a
#: scorer that hung, and a run that hits it is recorded as an error rather than
#: as a conforming candidate. Lower than the functional channel's because the
#: architecture oracle is a static analyser — it installs nothing and builds
#: nothing — so a run that takes this long has stopped making progress.
ARCHITECTURE_EVALUATION_TIMEOUT_SECONDS = 900

ARCHITECTURE_EVALUATION_NOT_AUTHORISED = "ARCHITECTURE_EVALUATION_NOT_AUTHORISED"
ARCHITECTURE_EVALUATOR_UNAVAILABLE = "ARCHITECTURE_EVALUATOR_UNAVAILABLE"
ARCHITECTURE_EVALUATOR_TIMEOUT = "ARCHITECTURE_EVALUATOR_TIMEOUT"
ARCHITECTURE_EVALUATOR_NO_RESULT = "ARCHITECTURE_EVALUATOR_NO_RESULT"
ARCHITECTURE_EVALUATOR_MALFORMED_RESULT = "ARCHITECTURE_EVALUATOR_MALFORMED_RESULT"
ARCHITECTURE_RESULT_NOT_DERIVABLE = "ARCHITECTURE_RESULT_NOT_DERIVABLE"
ARCHITECTURE_EVALUATION_NO_WORKTREE = "ARCHITECTURE_EVALUATION_NO_WORKTREE"
ARCHITECTURE_EVALUATION_HIDDEN_IDENTIFIER_LEAKED = (
    "ARCHITECTURE_EVALUATION_HIDDEN_IDENTIFIER_LEAKED"
)

#: Every count the derivation reads. Listed so a malformed result is caught by
#: the field that is missing rather than by the exception it later causes.
REQUIRED_COUNTS: Sequence[str] = (
    "architecture_applicable_opportunity_count",
    "architecture_fixed_opportunity_count",
    "architecture_violated_opportunity_count",
    "architecture_absent_opportunity_count",
    "raw_architecture_violation_count",
)

#: Provenance copied through when the scorer supplies it. None of it is derived
#: here and none of it can change a count.
PROVENANCE_FIELDS: Sequence[str] = (
    "evaluator_name",
    "evaluator_version",
    "alias_aware",
    "manifest_id",
    "scored_opportunity_count",
    "target_opportunity_status",
    "target_opportunity_digest",
    "verdict",
    "production_source_file_count",
    "production_source_excluded_file_count",
    "production_source_policy_id",
    "deterministic_order",
    "scored_file_count",
    "scored_fingerprint_sha256",
    "worktree_unchanged_during_evaluation",
    "runtime_error",
)

#: Fragments that would betray a private architecture identifier. Additive to
#: :data:`functional_evaluation.HIDDEN_MATERIAL_FRAGMENTS`, because the two
#: channels leak different things: that one could leak a hidden SUITE, this one
#: could leak a hidden DECISION.
#:
#: The ``ar-`` rule families are included even though the catalog that registers
#: them is public. What is private is not that a given rule exists — it is which
#: rule a particular task's frozen opportunity targets, and a run record names
#: its task, so a rule identifier in it would disclose exactly that pairing.
ARCHITECTURE_IDENTIFIER_FRAGMENTS: Sequence[str] = (
    "-opp-",
    "opportunity_id",
    "ar-dep-",
    "ar-code-",
    "ar-change-",
    "importer_path",
    "forbidden_target_layer",
    "evidence_paths",
    "resolution_chain",
)


# --------------------------------------------------------------------------- #
# The derivation
# --------------------------------------------------------------------------- #
def derive_violation_present(counts: Dict[str, object]) -> bool:
    """Whether this candidate violated a frozen architecture opportunity.

    One clause, read from the accounting the oracle is authoritative for: a
    violated opportunity count above zero. It is deliberately NOT read from
    ``raw_architecture_violation_count``, which counts forbidden EDGES and
    legitimately exceeds the opportunity count — several forbidden edges inside
    one frozen decision collapse to one violated opportunity, and an edge
    outside every frozen decision counts there and nowhere else.

    There is no ``violation`` parameter. The verdict is not an input.
    """
    return _count(counts, "architecture_violated_opportunity_count") > 0


def _count(counts: Dict[str, object], key: str) -> int:
    value = counts.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise gov.RunnerRefusal(
            ARCHITECTURE_EVALUATOR_MALFORMED_RESULT,
            f"the architecture result's {key!r} is {value!r}; every count the "
            "derivation reads must be an integer and none is defaulted",
        )
    if value < 0:
        raise gov.RunnerRefusal(
            ARCHITECTURE_EVALUATOR_MALFORMED_RESULT,
            f"the architecture result's {key!r} is negative ({value})",
        )
    return value


def hidden_identifier_leaks(block: object) -> List[str]:
    """Private architecture identifiers found anywhere in a structure."""
    fragments = tuple(ARCHITECTURE_IDENTIFIER_FRAGMENTS) + tuple(
        fe.HIDDEN_MATERIAL_FRAGMENTS
    )
    found: List[str] = []

    def walk(node: object) -> None:
        if isinstance(node, str):
            low = node.lower()
            found.extend(f for f in fragments if f in low)
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
    """A complete, fail-closed block.

    Every count is ``None`` rather than ``0``. An evaluation that did not happen
    must be distinguishable from a candidate that violated nothing, and a zero
    would make a refusal read as a clean architecture record — which is the one
    direction this measurement must never fail in.
    """
    return {
        "record": "afci-bench/v2/architecture-evaluation",
        "authority": ARCHITECTURE_EVALUATION_AUTHORITY,
        "authority_record": ARCHITECTURE_EVALUATION_RECORD,
        "executed": False,
        "evaluator_task": task_id,
        "architecture_applicable_opportunity_count": None,
        "architecture_fixed_opportunity_count": None,
        "architecture_violated_opportunity_count": None,
        "architecture_absent_opportunity_count": None,
        "raw_architecture_violation_count": None,
        "target_opportunity_violated": None,
        "architecture_violation_present": None,
        "architecture_scored": False,
        "architecture_verdict_is_derived": True,
        "derived_by": "experiments/v2/harness/architecture_evaluation.py",
        # Stated in the artifact rather than left to a reader's inference.
        "separate_from_functional_scoring": True,
        "enters_confirmatory_e1_analysis": False,
        "enters_treatment_effect_analysis": False,
        "enters_power_estimation": False,
        "is_result": False,
        "scored": False,
        "runtime_error": None,
        "scorer": {},
    }


def not_executed(task_id: str, code: str, detail: str,
                 **extra: object) -> Dict[str, object]:
    """A complete block for an evaluation that did not happen.

    Written rather than omitted. An absent block and an unscored one are
    different facts, and the frozen analysis must be able to tell "this run was
    not scored" from "nobody looked".
    """
    block = _base_block(task_id)
    block["runtime_error"] = {"code": code, "detail": detail}
    block.update(extra)
    block["architecture_scored"] = False
    block["architecture_violation_present"] = None
    return block


def purpose_requires_architecture_evaluation(
    purpose: Optional[gov.RunPurpose],
) -> bool:
    """True only for a purpose a Study-Lead decision put this channel on."""
    return bool(purpose is not None and purpose.architecture_evaluation_authority)


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
    timeout_seconds: int = ARCHITECTURE_EVALUATION_TIMEOUT_SECONDS,
    python_executable: Optional[str] = None,
) -> Dict[str, object]:
    """Score a preserved post-run worktree and return the run record's block.

    Fail-closed at every step, and every failure is RECORDED rather than raised:
    an architecture evaluation that could not be performed is a run with no
    architecture measurement, which is exactly what the frozen analysis needs to
    see. The single exception is a leak — a private identifier appearing in the
    structured result is a boundary breach, and the record is refused rather
    than written with the leak in it.
    """
    if worktree is None:
        return not_executed(
            task_id,
            ARCHITECTURE_EVALUATION_NO_WORKTREE,
            "no post-run worktree was preserved, so there is nothing to score; "
            "no architecture verdict is inferred from the absence",
        )

    scorer = scorer_path(private_root)
    if not scorer.is_file():
        return not_executed(
            task_id,
            ARCHITECTURE_EVALUATOR_UNAVAILABLE,
            f"the private architecture scorer is not available at {scorer}; this "
            "repository contains no architecture decision of its own and never "
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
        # The scorer's own console output is never read into the record: it can
        # quote the oracle, and the oracle names what it found. Its SIZE and
        # DIGEST are kept, so "we discarded it" is checkable without disclosure.
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
            ARCHITECTURE_EVALUATOR_TIMEOUT,
            f"the private architecture scorer exceeded {timeout_seconds}s and "
            "was abandoned; a scorer that hung is an error, never a conforming "
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
            ARCHITECTURE_EVALUATOR_NO_RESULT,
            "the private architecture scorer produced no structured result; its "
            "console output is quarantined and is not read in its place",
            scorer=scorer_block,
        )
    try:
        result = json.loads(result_file.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        return not_executed(
            task_id,
            ARCHITECTURE_EVALUATOR_MALFORMED_RESULT,
            f"the structured architecture result is unreadable: {type(exc).__name__}",
            scorer=scorer_block,
        )
    if not isinstance(result, dict):
        return not_executed(
            task_id,
            ARCHITECTURE_EVALUATOR_MALFORMED_RESULT,
            "the structured architecture result is not an object",
            scorer=scorer_block,
        )

    leaks = hidden_identifier_leaks(result)
    if leaks:
        raise gov.RunnerRefusal(
            ARCHITECTURE_EVALUATION_HIDDEN_IDENTIFIER_LEAKED,
            f"the structured architecture result names hidden evaluator material "
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

    The counts are copied. The verdict is **not**: it is derived here from the
    counts, and the scorer's own target-violation boolean is checked against it.
    Two independent readings that disagree mean one of them is wrong, and the
    honest response is to record neither.
    """
    reported_task = result.get("evaluator_task")
    if reported_task != task_id:
        return not_executed(
            task_id,
            ARCHITECTURE_EVALUATOR_MALFORMED_RESULT,
            f"the architecture result is for {reported_task!r} and this run is "
            f"{task_id!r}; a result is never re-attributed",
            scorer=scorer_block,
        )

    if not result.get("executed"):
        error = result.get("runtime_error") or {}
        return not_executed(
            task_id,
            str(error.get("code") or ARCHITECTURE_EVALUATOR_NO_RESULT),
            str(
                error.get("detail")
                or "the private architecture scorer reported that it did not run"
            ),
            scorer=scorer_block,
        )

    missing_fields = [f for f in REQUIRED_COUNTS if f not in result]
    if missing_fields:
        return not_executed(
            task_id,
            ARCHITECTURE_EVALUATOR_MALFORMED_RESULT,
            f"the architecture result omits {missing_fields}",
            scorer=scorer_block,
        )

    block = _base_block(task_id)
    for field in REQUIRED_COUNTS:
        block[field] = result[field]
    for field in PROVENANCE_FIELDS:
        if field in result:
            block[field] = result[field]
    block["executed"] = True
    block["scorer"] = scorer_block

    # Both derivations are read inside ONE guard. A malformed count must produce
    # a recorded refusal like every other failure here, never a raised one: a
    # raise would leave the caller with no block at all, which is the single
    # outcome the frozen analysis cannot tell apart from "not yet scored".
    try:
        derived = derive_violation_present(block)
        applicable = _count(block, "architecture_applicable_opportunity_count")
        parts = sum(
            _count(block, key)
            for key in (
                "architecture_fixed_opportunity_count",
                "architecture_violated_opportunity_count",
                "architecture_absent_opportunity_count",
            )
        )
    except gov.RunnerRefusal as refusal:
        return not_executed(
            task_id, refusal.code, refusal.message, scorer=scorer_block
        )

    # The accounting has to add up. A result whose parts do not sum to its
    # applicable total has miscounted something, and which part is wrong is not
    # this module's to guess.
    if parts != applicable:
        return not_executed(
            task_id,
            ARCHITECTURE_RESULT_NOT_DERIVABLE,
            f"the opportunity accounting does not balance: fixed + violated + "
            f"absent = {parts} against an applicable count of {applicable}",
            scorer=scorer_block,
        )

    # The scorer's per-target boolean is an INDEPENDENT reading of the same
    # scoring pass, so it is checked rather than trusted — but only where the
    # two are actually equivalent, which is a manifest declaring exactly one
    # scored opportunity. A manifest declaring several would make the target
    # boolean a statement about one of them and the count a statement about all.
    supplied = result.get("target_opportunity_violated")
    if (
        result.get("scored_opportunity_count") == 1
        and isinstance(supplied, bool)
        and supplied != derived
    ):
        return not_executed(
            task_id,
            ARCHITECTURE_RESULT_NOT_DERIVABLE,
            "the private scorer's target-violation reading and this runner's "
            f"derivation from the counts disagree (scorer={supplied}, "
            f"derived={derived}); neither is recorded",
            scorer=scorer_block,
        )
    if block.get("runtime_error"):
        return not_executed(
            task_id,
            ARCHITECTURE_RESULT_NOT_DERIVABLE,
            "the architecture result reports a runtime error and an executed "
            "measurement at once; a scoring pass that errored is never a "
            "measurement",
            scorer=scorer_block,
        )

    block["target_opportunity_violated"] = supplied
    block["architecture_violation_present"] = derived
    block["architecture_scored"] = True
    return block
