#!/usr/bin/env python3
"""The AFCI efficiency pilot's FROZEN analysis, executed rather than described.

What this is
------------
``docs/v2/AFCI_EFFICIENCY_PILOT_DECISION.md`` §10 and §11 froze this pilot's
pairing, its endpoints and its decision rule **before any observation existed**.
This module is that text as code and nothing more. It invents no endpoint,
relaxes no threshold, adds no test and reports no p-value, confidence interval
or effect estimate — a pilot of three repetitions supports none of them.

What changed, and what did not
------------------------------
``SL-V2-EFF-FUNC-01`` supplied the one input §10.1 and §11.0 needed and did not
have: a per-run ``FUNCTIONAL_VALID``. This module reads it from exactly one
place — ``record.functional_evaluation.functional_valid`` — and from nowhere
else. It is **never** inferred from CI success, from model prose, from an exit
status, from an architecture score, or from how many files changed. The
thresholds, the endpoints, the pairing and the rule are byte-for-byte the frozen
ones.

Architecture
------------
None is produced, and none is read. ``AFCI_EFFICIENCY_PILOT`` is a **cost-only**
purpose under its own frozen governance: the report states that in place of an
architecture result, which is a reporting correction rather than an endpoint.
No continuation threshold depends on architecture, so none moves.

Usage
-----
::

    python experiments/v2/analysis/efficiency_pilot_analysis.py \\
        --records <dir of run_record.json> --out report.json

    # computability self-check over SYNTHETIC records; reads no observation
    python experiments/v2/analysis/efficiency_pilot_analysis.py --self-check
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

RUN_PURPOSE = "AFCI_EFFICIENCY_PILOT"
DECISION_RECORD = "docs/v2/AFCI_EFFICIENCY_PILOT_DECISION.md"
#: The decision that aborted execution attempt 1 and excluded it wholesale.
ABORT_DECISION = "SL-V2-EFF-ABORT-01"
FUNCTIONAL_VALIDITY_RECORD = (
    "docs/v2/AFCI_EFFICIENCY_PILOT_FUNCTIONAL_VALIDITY_DECISION.md"
)

TASKS: Tuple[str, ...] = ("PT01", "PT04", "PT07")
CONDITIONS: Tuple[str, ...] = ("C1", "C4")
RESET_STATES: Tuple[str, ...] = ("NON_RESET", "RESET")
REPETITIONS: Tuple[int, ...] = (1, 2, 3)

#: 3 tasks x 2 reset states x 3 repetitions. Each holds one C1 and one C4 run.
EXPECTED_BLOCKS = len(TASKS) * len(RESET_STATES) * len(REPETITIONS)
EXPECTED_RUNS = EXPECTED_BLOCKS * len(CONDITIONS)

#: §11.0. Below this, no efficiency claim of any kind is made.
MINIMUM_ELIGIBLE_PAIRS = 12
#: §11.1.2 / §11.2.2 / §11.3.1 — the functional guardrail.
MAX_C4_FUNCTIONAL_DEFICIT = 1
STRONG_GO_MEDIAN_TOKEN_RATIO = 0.90
STRONG_GO_C4_CHEAPER_FRACTION = 0.60
STRONG_GO_TASK_MAJORITY = 2
QUALIFIED_GO_MEDIAN_TOKEN_RATIO = 1.10
QUALIFIED_GO_ALTERNATIVES: Tuple[Tuple[str, float], ...] = (
    ("MODEL_WALL_SECONDS", 0.85),
    ("EXPLORATION_CALLS", 0.75),
    ("TOTAL_TOOL_CALLS", 0.80),
)
RESET_SPECIFIC_GO_MEDIAN_TOKEN_RATIO = 1.10

STRONG_GO = "STRONG GO"
QUALIFIED_GO = "QUALIFIED GO"
RESET_SPECIFIC_GO = "RESET-SPECIFIC GO"
NO_SIGNAL = "STOP — NO EFFICIENCY SIGNAL JUSTIFIES FULL-SUITE EXPANSION"
INCONCLUSIVE = "PILOT INCONCLUSIVE — INSUFFICIENT PAIRED FUNCTIONAL DATA"

#: §10.2. The primary endpoint. Lower is better for C4.
PRIMARY_ENDPOINT = "TOTAL_INPUT_TOKENS"

#: §10.3. Same pairing, same direction. ``non_reset_only`` carries §9.2's
#: limitation: a RESET run's phase A is interrupted before its terminal result
#: event, so its output total is withheld rather than understated.
SECONDARY_ENDPOINTS: Tuple[Tuple[str, bool], ...] = (
    ("MODEL_WALL_SECONDS", False),
    ("TOTAL_TOOL_CALLS", False),
    ("EXPLORATION_CALLS", False),
    ("UNIQUE_FILES_READ", False),
    ("TOTAL_OUTPUT_TOKENS", True),
    ("EDIT_AND_WRITE_CALLS", False),
    ("TEST_COMMAND_RUNS", False),
    ("CI_COMMAND_RUNS", False),
)

#: §10.4. Reset recovery, per (task x repetition x condition).
RESET_OVERHEAD_ENDPOINTS: Tuple[str, ...] = (
    "TOTAL_INPUT_TOKENS",
    "MODEL_WALL_SECONDS",
    "EXPLORATION_CALLS",
    "TOTAL_TOOL_CALLS",
)

ARCHITECTURE_STATEMENT = (
    "Not produced by AFCI_EFFICIENCY_PILOT under its frozen cost-only "
    "governance. Existing pre-data legal/violating architecture validation was "
    "used only for eligibility. No live-run architecture treatment inference is "
    "made."
)

#: The one place a functional verdict may come from, named so a reader can check
#: that nothing else was consulted.
FUNCTIONAL_VALIDITY_SOURCE = "record.functional_evaluation.functional_valid"
FUNCTIONAL_VALIDITY_NEVER_INFERRED_FROM = (
    "CI success",
    "model prose",
    "exit status alone",
    "any architecture score or violation value",
    "the number of files changed",
)

FUNCTIONAL_VALID = "VALID"
FUNCTIONAL_INVALID = "INVALID"
FUNCTIONAL_MISSING = "MISSING"


class AnalysisRefusal(RuntimeError):
    """A fail-closed analysis refusal. ``code`` is machine-readable."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


# --------------------------------------------------------------------------- #
# One observation
# --------------------------------------------------------------------------- #
def _metric(efficiency: Dict[str, object], name: str) -> Optional[float]:
    """One endpoint, read from the measurement block and never recomputed.

    ``EDIT_AND_WRITE_CALLS`` is the one derived endpoint §10.3 names as a sum;
    it is summed here rather than stored, because the harness records the two
    counts it actually observed.
    """
    usage = efficiency.get("usage") or {}
    tools = efficiency.get("tools") or {}
    timing = efficiency.get("timing") or {}
    if name == "EDIT_AND_WRITE_CALLS":
        edits, writes = tools.get("EDIT_CALLS"), tools.get("WRITE_CALLS")
        if edits is None or writes is None:
            return None
        return float(edits) + float(writes)
    for source in (usage, tools, timing):
        if name in source:
            value = source[name]
            return None if value is None else float(value)
    return None


class Observation:
    """One run record, read only for the fields the frozen analysis names."""

    def __init__(self, record: Dict[str, object], source: str = "<memory>") -> None:
        self.source = source
        self.record = record
        purpose = (record.get("run_purpose") or {}).get("name")
        if purpose != RUN_PURPOSE:
            raise AnalysisRefusal(
                "RECORD_IS_NOT_A_PILOT_OBSERVATION",
                f"{source}: run_purpose is {purpose!r}; this analysis reads "
                f"{RUN_PURPOSE} records only and never re-purposes another",
            )
        self.task_id = str(record.get("task_id") or "")
        self.condition = str(record.get("condition") or "")
        self.repetition = record.get("repetition")
        efficiency = record.get("efficiency") or {}
        self.efficiency: Dict[str, object] = efficiency
        self.reset_state = str(
            (record.get("reset") or {}).get("reset_state")
            or efficiency.get("reset_state")
            or ""
        )
        self.functional_status, self.functional_valid = self._functional(record)

    @staticmethod
    def _functional(record: Dict[str, object]) -> Tuple[str, bool]:
        """Read the verdict from the ONE place, or report that it is absent.

        A record with no functional evaluation is ``MISSING``, never ``False``
        dressed as a measurement: "this run did not work" and "nobody scored
        this run" are different facts and the report keeps them apart. Both are
        ineligible, because a pair is eligible only when both runs are *known*
        to have worked.
        """
        block = record.get("functional_evaluation")
        if not isinstance(block, dict) or "functional_valid" not in block:
            return FUNCTIONAL_MISSING, False
        valid = block.get("functional_valid")
        if not isinstance(valid, bool):
            return FUNCTIONAL_MISSING, False
        return (FUNCTIONAL_VALID if valid else FUNCTIONAL_INVALID), valid

    @property
    def block_key(self) -> Tuple[str, str, object]:
        return (self.task_id, self.reset_state, self.repetition)

    def metric(self, name: str) -> Optional[float]:
        return _metric(self.efficiency, name)

    def to_dict(self) -> Dict[str, object]:
        return {
            "source": self.source,
            "task_id": self.task_id,
            "condition": self.condition,
            "reset_state": self.reset_state,
            "repetition": self.repetition,
            "functional_status": self.functional_status,
            "functional_valid": self.functional_valid,
        }


# --------------------------------------------------------------------------- #
# §10.1 Pairing
# --------------------------------------------------------------------------- #
def build_blocks(observations: Sequence[Observation]) -> List[Dict[str, object]]:
    """Group observations into (task x reset state x repetition) blocks.

    A block is complete only with exactly one ``C1`` and exactly one ``C4``. Two
    records for one arm is an accounting error, not a choice to be made here, so
    it is reported and the block is left incomplete rather than resolved.
    """
    grouped: Dict[Tuple[str, str, object], Dict[str, List[Observation]]] = {}
    for obs in observations:
        arm = grouped.setdefault(obs.block_key, {c: [] for c in CONDITIONS})
        if obs.condition not in arm:
            raise AnalysisRefusal(
                "CONDITION_NOT_IN_THE_PILOT",
                f"{obs.source}: condition {obs.condition!r} is not one of "
                f"{list(CONDITIONS)}",
            )
        arm[obs.condition].append(obs)

    blocks: List[Dict[str, object]] = []
    for key in sorted(grouped, key=lambda k: (k[0], k[1], str(k[2]))):
        arms = grouped[key]
        duplicated = sorted(c for c in CONDITIONS if len(arms[c]) > 1)
        complete = all(len(arms[c]) == 1 for c in CONDITIONS)
        c1 = arms["C1"][0] if len(arms["C1"]) == 1 else None
        c4 = arms["C4"][0] if len(arms["C4"]) == 1 else None
        eligible = bool(
            complete and c1 and c4 and c1.functional_valid and c4.functional_valid
        )
        blocks.append(
            {
                "task_id": key[0],
                "reset_state": key[1],
                "repetition": key[2],
                "complete": complete,
                "duplicated_conditions": duplicated,
                "C1": c1.to_dict() if c1 else None,
                "C4": c4.to_dict() if c4 else None,
                "eligible": eligible,
                "ineligible_reason": _ineligible_reason(complete, c1, c4),
                "_c1": c1,
                "_c4": c4,
            }
        )
    return blocks


def _ineligible_reason(
    complete: bool, c1: Optional[Observation], c4: Optional[Observation]
) -> Optional[str]:
    if not complete or c1 is None or c4 is None:
        return "the block does not hold exactly one C1 and one C4 observation"
    bad = [
        f"{obs.condition} is {obs.functional_status}"
        for obs in (c1, c4)
        if not obs.functional_valid
    ]
    if bad:
        return (
            "a cost figure from a run that did not work is not a cheaper way of "
            "doing the task: " + "; ".join(bad)
        )
    return None


# --------------------------------------------------------------------------- #
# §10.2 / §10.3 Paired ratios
# --------------------------------------------------------------------------- #
def _ratio(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    """``C4 / C1``, or ``None`` when the pair cannot produce one.

    A zero or absent denominator yields ``None`` rather than an exception or a
    substituted value: an undefined ratio is dropped from its endpoint and
    counted, so a reader sees the denominator rather than a number invented for
    it.
    """
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def paired_ratios(
    blocks: Sequence[Dict[str, object]], endpoint: str, *, non_reset_only: bool = False
) -> Dict[str, object]:
    """Every eligible block's ``C4/C1`` ratio for one endpoint."""
    rows: List[Dict[str, object]] = []
    undefined: List[Dict[str, object]] = []
    for block in blocks:
        if not block["eligible"]:
            continue
        if non_reset_only and block["reset_state"] != "NON_RESET":
            continue
        c1, c4 = block["_c1"], block["_c4"]
        value = _ratio(c4.metric(endpoint), c1.metric(endpoint))
        row = {
            "task_id": block["task_id"],
            "reset_state": block["reset_state"],
            "repetition": block["repetition"],
            "C1": c1.metric(endpoint),
            "C4": c4.metric(endpoint),
            "ratio": value,
        }
        (rows if value is not None else undefined).append(row)
    values = [float(r["ratio"]) for r in rows]
    per_task = {
        task: _median([float(r["ratio"]) for r in rows if r["task_id"] == task])
        for task in TASKS
    }
    return {
        "endpoint": endpoint,
        "non_reset_only": non_reset_only,
        "pairs": rows,
        "undefined_pairs": undefined,
        "n": len(values),
        "median": _median(values),
        "task_medians": per_task,
        "tasks_improving": sorted(
            task for task, median in per_task.items()
            if median is not None and median < 1
        ),
        "c4_lower_count": len([v for v in values if v < 1]),
        "c4_lower_fraction": (len([v for v in values if v < 1]) / len(values))
        if values
        else None,
    }


def _median(values: Sequence[float]) -> Optional[float]:
    return statistics.median(values) if values else None


# --------------------------------------------------------------------------- #
# §10.4 Reset recovery
# --------------------------------------------------------------------------- #
def reset_overhead(observations: Sequence[Observation]) -> Dict[str, object]:
    """``RESET / NON_RESET`` per (task x repetition x condition).

    Computed over FUNCTIONALLY VALID observations only, for the same reason
    §10.1 pairs only valid runs: the cost of a run that did not work is not the
    cost of doing the task, and that is as true of a reset arm as of a pair.
    """
    by_cell: Dict[Tuple[str, object, str], Dict[str, Observation]] = {}
    for obs in observations:
        if not obs.functional_valid:
            continue
        cell = by_cell.setdefault((obs.task_id, obs.repetition, obs.condition), {})
        cell[obs.reset_state] = obs

    endpoints: Dict[str, object] = {}
    for endpoint in RESET_OVERHEAD_ENDPOINTS:
        rows: List[Dict[str, object]] = []
        for key in sorted(by_cell, key=lambda k: (k[0], str(k[1]), k[2])):
            cell = by_cell[key]
            if "RESET" not in cell or "NON_RESET" not in cell:
                continue
            value = _ratio(
                cell["RESET"].metric(endpoint), cell["NON_RESET"].metric(endpoint)
            )
            if value is None:
                continue
            rows.append(
                {
                    "task_id": key[0],
                    "repetition": key[1],
                    "condition": key[2],
                    "ratio": value,
                }
            )
        per_task_condition = {
            f"{task}/{condition}": _median(
                [
                    float(r["ratio"])
                    for r in rows
                    if r["task_id"] == task and r["condition"] == condition
                ]
            )
            for task in TASKS
            for condition in CONDITIONS
        }
        endpoints[endpoint] = {
            "rows": rows,
            "task_condition_medians": per_task_condition,
            "tasks_where_c4_overhead_is_lower": sorted(
                task
                for task in TASKS
                if _both(per_task_condition, task)
                and per_task_condition[f"{task}/C4"] < per_task_condition[f"{task}/C1"]
            ),
        }
    return endpoints


def _both(medians: Dict[str, Optional[float]], task: str) -> bool:
    return (
        medians.get(f"{task}/C1") is not None
        and medians.get(f"{task}/C4") is not None
    )


# --------------------------------------------------------------------------- #
# §11 The frozen decision rule
# --------------------------------------------------------------------------- #
def _clause(name: str, satisfied: bool, detail: str) -> Dict[str, object]:
    return {"clause": name, "satisfied": bool(satisfied), "detail": detail}


def decide(
    *,
    eligible_pairs: int,
    functional_valid_counts: Dict[str, int],
    primary: Dict[str, object],
    secondary: Dict[str, Dict[str, object]],
    overhead: Dict[str, object],
) -> Dict[str, object]:
    """Evaluate §11 in order. The first rule that matches is the outcome."""
    guardrail = (
        functional_valid_counts["C1"] - functional_valid_counts["C4"]
        <= MAX_C4_FUNCTIONAL_DEFICIT
    )
    guardrail_detail = (
        f"C1 functional-valid {functional_valid_counts['C1']}/18, C4 "
        f"{functional_valid_counts['C4']}/18; C4 may be at most "
        f"{MAX_C4_FUNCTIONAL_DEFICIT} lower"
    )
    minimum = _clause(
        "11.0 at least 12 of the 18 blocks are paired functionally valid",
        eligible_pairs >= MINIMUM_ELIGIBLE_PAIRS,
        f"{eligible_pairs} of {EXPECTED_BLOCKS} blocks are eligible; "
        f"{MINIMUM_ELIGIBLE_PAIRS} are required",
    )
    if not minimum["satisfied"]:
        return {
            "outcome": INCONCLUSIVE,
            "rule": "11.0",
            "clauses": [minimum],
            "efficiency_claim_made": False,
        }

    median = primary["median"]
    fraction = primary["c4_lower_fraction"]
    strong = [
        minimum,
        _clause("11.1.2 functional guardrail", guardrail, guardrail_detail),
        _clause(
            "11.1.3 overall median TOKEN_RATIO <= 0.90",
            median is not None and median <= STRONG_GO_MEDIAN_TOKEN_RATIO,
            f"median TOKEN_RATIO = {median}",
        ),
        _clause(
            "11.1.4 C4 uses fewer tokens in >= 60% of eligible pairs",
            fraction is not None and fraction >= STRONG_GO_C4_CHEAPER_FRACTION,
            f"C4 cheaper in {primary['c4_lower_count']} of {primary['n']} pairs",
        ),
        _clause(
            "11.1.5 >= 2 of 3 tasks have a task-median TOKEN_RATIO < 1",
            len(primary["tasks_improving"]) >= STRONG_GO_TASK_MAJORITY,
            f"tasks improving: {primary['tasks_improving']}",
        ),
    ]
    if all(c["satisfied"] for c in strong):
        return {
            "outcome": STRONG_GO,
            "rule": "11.1",
            "clauses": strong,
            "efficiency_claim_made": True,
        }

    qualifying: List[Dict[str, object]] = []
    for endpoint, ceiling in QUALIFIED_GO_ALTERNATIVES:
        block = secondary.get(endpoint) or {}
        endpoint_median = block.get("median")
        if endpoint_median is not None and endpoint_median <= ceiling:
            qualifying.append(
                {
                    "endpoint": endpoint,
                    "ceiling": ceiling,
                    "median": endpoint_median,
                    "tasks_improving": block.get("tasks_improving") or [],
                }
            )
    directional = [
        q for q in qualifying
        if len(q["tasks_improving"]) >= STRONG_GO_TASK_MAJORITY
    ]
    qualified = [
        minimum,
        _clause("11.2.2 functional guardrail", guardrail, guardrail_detail),
        _clause(
            "11.2.3 overall median TOKEN_RATIO <= 1.10",
            median is not None and median <= QUALIFIED_GO_MEDIAN_TOKEN_RATIO,
            f"median TOKEN_RATIO = {median}",
        ),
        _clause(
            "11.2.4 at least one secondary endpoint meets its ceiling",
            bool(qualifying),
            f"qualifying endpoints: {[q['endpoint'] for q in qualifying]}",
        ),
        _clause(
            "11.2.5 a qualifying endpoint improves directionally in >= 2 of 3 tasks",
            bool(directional),
            f"directionally qualifying endpoints: "
            f"{[q['endpoint'] for q in directional]}",
        ),
    ]
    if all(c["satisfied"] for c in qualified):
        return {
            "outcome": QUALIFIED_GO,
            "rule": "11.2",
            "clauses": qualified,
            "qualifying_endpoints": qualifying,
            "efficiency_claim_made": True,
        }

    token_overhead = (overhead.get(PRIMARY_ENDPOINT) or {}).get(
        "tasks_where_c4_overhead_is_lower"
    ) or []
    wall = (overhead.get("MODEL_WALL_SECONDS") or {}).get(
        "tasks_where_c4_overhead_is_lower"
    ) or []
    exploration = (overhead.get("EXPLORATION_CALLS") or {}).get(
        "tasks_where_c4_overhead_is_lower"
    ) or []
    either = sorted(set(wall) | set(exploration))
    reset_specific = [
        _clause("11.3.1 functional guardrail", guardrail, guardrail_detail),
        _clause(
            "11.3.2 overall TOKEN_RATIO <= 1.10",
            median is not None and median <= RESET_SPECIFIC_GO_MEDIAN_TOKEN_RATIO,
            f"median TOKEN_RATIO = {median}",
        ),
        _clause(
            "11.3.3 C4 has lower token reset-overhead in >= 2 of 3 tasks",
            len(token_overhead) >= STRONG_GO_TASK_MAJORITY,
            f"tasks: {token_overhead}",
        ),
        _clause(
            "11.3.4 C4 has lower MODEL_WALL_SECONDS or EXPLORATION_CALLS reset "
            "overhead in >= 2 of 3 tasks",
            len(either) >= STRONG_GO_TASK_MAJORITY,
            f"MODEL_WALL_SECONDS: {wall}; EXPLORATION_CALLS: {exploration}",
        ),
    ]
    if all(c["satisfied"] for c in reset_specific):
        return {
            "outcome": RESET_SPECIFIC_GO,
            "rule": "11.3",
            "clauses": reset_specific,
            "efficiency_claim_made": True,
        }

    return {
        "outcome": NO_SIGNAL,
        "rule": "11.4",
        "clauses": strong + qualified + reset_specific,
        "efficiency_claim_made": False,
    }


# --------------------------------------------------------------------------- #
# The report
# --------------------------------------------------------------------------- #
#: ``SL-V2-EFF-ABORT-01``. The aborted execution attempt, whose observations may
#: never enter an efficiency analysis. Its records declare NO execution attempt,
#: because the field did not exist when they were written, so absence is the
#: signature this refuses on rather than the value 1.
ABORTED_EXECUTION_ATTEMPT = 1

#: The replacement execution authorised by ``SL-V2-EFF-RESTART-01``. Restated
#: here rather than imported: this module reads run records and nothing else, so
#: it depends on no harness module and runs anywhere a record set does. A test
#: asserts it equals ``execution_attempt.REPLACEMENT_ATTEMPT``, so the
#: restatement is checked rather than trusted.
REPLACEMENT_EXECUTION_ATTEMPT = 2

ANALYSIS_SPANS_EXECUTION_ATTEMPTS = "ANALYSIS_SPANS_EXECUTION_ATTEMPTS"
ANALYSIS_INCLUDES_ABORTED_ATTEMPT = "ANALYSIS_INCLUDES_ABORTED_ATTEMPT"


def assert_single_execution_attempt(
    records: Sequence[Dict[str, object]], sources: Sequence[str]
) -> Optional[int]:
    """Refuse a record set that pools executions, or includes the aborted one.

    ``SL-V2-EFF-ABORT-01`` excludes execution attempt 1 wholesale and forbids
    pooling it with the replacement. That exclusion was a sentence in a decision
    record, and a sentence is not a control: ``load_records`` recurses into
    whatever directory it is handed, and the two executions' artifact roots are
    siblings. An operator pointing the analysis one level too high would have
    pooled an aborted execution with its replacement, silently, and the report
    would have looked entirely normal.

    Two refusals:

    * records disagreeing about which execution they belong to. A pilot analysis
      is paired WITHIN a block, and blocks measured in different executions are
      not pairs;
    * any record from the aborted attempt, recognised by its silence: a real
      pilot record written after this decision declares its attempt, and one
      that declares none was written before the repair — which is to say, by the
      execution that was aborted.

    A ``dry-run`` record declares no attempt either and is not an observation;
    it is ignored here and excluded on its own terms elsewhere.
    """
    attempts: Dict[Optional[int], List[str]] = {}
    for record, source in zip(records, sources):
        if str(record.get("mode")) != "real":
            continue
        if str(record.get("run_purpose", {}).get("name")) != RUN_PURPOSE:
            continue
        attempts.setdefault(record.get("execution_attempt"), []).append(source)

    if not attempts:
        return None
    if len(attempts) > 1:
        raise AnalysisRefusal(
            ANALYSIS_SPANS_EXECUTION_ATTEMPTS,
            "the supplied records span more than one execution attempt "
            + "; ".join(
                f"{attempt!r}: {len(paths)} record(s) e.g. {paths[0]}"
                for attempt, paths in sorted(
                    attempts.items(), key=lambda kv: (kv[0] is not None, kv[0])
                )
            )
            + f". {ABORT_DECISION} forbids pooling executions",
        )
    (attempt, paths), = attempts.items()
    if attempt is None:
        raise AnalysisRefusal(
            ANALYSIS_INCLUDES_ABORTED_ATTEMPT,
            f"{len(paths)} record(s) declare no execution attempt, e.g. "
            f"{paths[0]}. Those were written before the run-id repair, by the "
            f"execution {ABORT_DECISION} aborted, and are excluded wholesale "
            "from every efficiency analysis",
        )
    if attempt == ABORTED_EXECUTION_ATTEMPT:
        raise AnalysisRefusal(
            ANALYSIS_INCLUDES_ABORTED_ATTEMPT,
            f"{len(paths)} record(s) declare execution attempt "
            f"{ABORTED_EXECUTION_ATTEMPT}, which {ABORT_DECISION} aborted and "
            "excluded wholesale",
        )
    return int(attempt)


def analyse(records: Sequence[Dict[str, object]], *,
            sources: Optional[Sequence[str]] = None) -> Dict[str, object]:
    """The whole frozen analysis for a set of pilot run records."""
    names = list(sources) if sources else ["<memory>"] * len(records)
    execution_attempt = assert_single_execution_attempt(records, names)
    observations = [
        Observation(record, source=name) for record, name in zip(records, names)
    ]
    blocks = build_blocks(observations)
    eligible = [b for b in blocks if b["eligible"]]

    functional_valid_counts = {
        condition: len(
            [o for o in observations if o.condition == condition and o.functional_valid]
        )
        for condition in CONDITIONS
    }
    functional_status_counts = {
        condition: {
            status: len(
                [
                    o
                    for o in observations
                    if o.condition == condition and o.functional_status == status
                ]
            )
            for status in (FUNCTIONAL_VALID, FUNCTIONAL_INVALID, FUNCTIONAL_MISSING)
        }
        for condition in CONDITIONS
    }

    primary = paired_ratios(blocks, PRIMARY_ENDPOINT)
    secondary = {
        endpoint: paired_ratios(blocks, endpoint, non_reset_only=non_reset_only)
        for endpoint, non_reset_only in SECONDARY_ENDPOINTS
    }
    overhead = reset_overhead(observations)
    decision = decide(
        eligible_pairs=len(eligible),
        functional_valid_counts=functional_valid_counts,
        primary=primary,
        secondary=secondary,
        overhead=overhead,
    )

    return {
        "record": "afci-bench/v2/efficiency-pilot-analysis",
        "run_purpose": RUN_PURPOSE,
        # SL-V2-EFF-ABORT-01: which single execution these observations came
        # from. Recorded so a report says on its face that it pooled nothing.
        "execution_attempt": execution_attempt,
        "aborted_execution_attempt_excluded": ABORTED_EXECUTION_ATTEMPT,
        "frozen_by": "SL-V2-EFF-01",
        "frozen_record": DECISION_RECORD,
        "functional_validity_authority": "SL-V2-EFF-FUNC-01",
        "functional_validity_record": FUNCTIONAL_VALIDITY_RECORD,
        "functional_validity_source": FUNCTIONAL_VALIDITY_SOURCE,
        "functional_validity_never_inferred_from": list(
            FUNCTIONAL_VALIDITY_NEVER_INFERRED_FROM
        ),
        "observations": {
            "expected": EXPECTED_RUNS,
            "supplied": len(observations),
            "by_condition": {
                c: len([o for o in observations if o.condition == c])
                for c in CONDITIONS
            },
            "rows": [o.to_dict() for o in observations],
        },
        "functional_valid_counts": functional_valid_counts,
        "functional_status_counts": functional_status_counts,
        "blocks": {
            "expected": EXPECTED_BLOCKS,
            "observed": len(blocks),
            "eligible": len(eligible),
            "rows": [
                {k: v for k, v in b.items() if not k.startswith("_")} for b in blocks
            ],
        },
        "primary_endpoint": primary,
        "secondary_endpoints": secondary,
        "reset_overhead": overhead,
        "decision": decision,
        "architecture": {
            "produced": False,
            "statement": ARCHITECTURE_STATEMENT,
            "thresholds_depending_on_architecture": [],
            "e1_contribution": None,
        },
        "no_p_values": True,
        "no_confidence_intervals": True,
        "no_effect_estimate": True,
        "is_result": False,
        "confirmatory": False,
    }


def load_records(paths: Sequence[Path]) -> Tuple[List[Dict[str, object]], List[str]]:
    """Read ``run_record.json`` files from files and/or directories."""
    files: List[Path] = []
    for path in paths:
        path = Path(path)
        if path.is_dir():
            files.extend(sorted(path.rglob("run_record.json")))
        elif path.is_file():
            files.append(path)
        else:
            raise AnalysisRefusal(
                "RECORD_PATH_NOT_FOUND", f"no such record path: {path}"
            )
    records, sources = [], []
    for file in files:
        records.append(json.loads(file.read_text(encoding="utf-8")))
        sources.append(str(file))
    return records, sources


# --------------------------------------------------------------------------- #
# The computability self-check
# --------------------------------------------------------------------------- #
def synthetic_records(
    *,
    c4_input_ratio: float = 0.8,
    invalid: Sequence[Tuple[str, str, str, int]] = (),
    omit_functional_block: Sequence[Tuple[str, str, str, int]] = (),
) -> List[Dict[str, object]]:
    """36 SYNTHETIC records, for proving the analysis is computable.

    These are fixtures, not observations. They carry the firewall flags a real
    record carries, they are never written into ``results/``, and nothing here
    is an efficiency measurement of anything: the numbers are constructed so the
    arithmetic has something to chew on, and the module that reads them cannot
    tell the difference — which is the point of the check.
    """
    invalid_set = set(invalid)
    omit_set = set(omit_functional_block)
    records: List[Dict[str, object]] = []
    for task_index, task in enumerate(TASKS):
        for reset_state in RESET_STATES:
            for repetition in REPETITIONS:
                for condition in CONDITIONS:
                    key = (task, reset_state, condition, repetition)
                    scale = 1.0 if condition == "C1" else c4_input_ratio
                    base = 100_000 + 1_000 * task_index + 100 * repetition
                    # A reset run is two phases, so it costs more on every
                    # endpoint rather than on tokens alone. Applied to all of
                    # them so §10.4's overhead ratios have something to measure
                    # and an inverted RESET/NON_RESET would be visible.
                    reset_factor = 1.4 if reset_state == "RESET" else 1.0
                    scale = scale * reset_factor
                    valid = key not in invalid_set
                    record = {
                        "schema_version": "1.0.0",
                        "record_kind": "runner_run_record",
                        "run_id": (
                            f"synthetic-{task.lower()}-{condition.lower()}-"
                            f"{reset_state.lower()}-r{repetition}"
                        ),
                        "run_purpose": {
                            "name": RUN_PURPOSE,
                            "decision_id": "SL-V2-EFF-01",
                            "confirmatory": False,
                            "confirmatory_eligible": False,
                            "enters_confirmatory_dataset": False,
                            "enters_confirmatory_e1_analysis": False,
                            "enters_treatment_effect_analysis": False,
                            "enters_power_estimation": False,
                        },
                        "task_id": task,
                        "condition": condition,
                        "repetition": repetition,
                        # A fixture that omitted these would leave the
                        # execution-attempt guard unexercised by the very check
                        # whose job is to prove the analysis is computable.
                        "mode": "real",
                        "execution_attempt": REPLACEMENT_EXECUTION_ATTEMPT,
                        "reset": {"reset_state": reset_state},
                        "efficiency": {
                            "reset_state": reset_state,
                            "usage": {
                                "TOTAL_INPUT_TOKENS": int(base * scale),
                                # §9.2: a RESET run's phase A is interrupted
                                # before its terminal result event, so the
                                # output total is withheld rather than guessed.
                                "TOTAL_OUTPUT_TOKENS": (
                                    None
                                    if reset_state == "RESET"
                                    else int(9_000 * scale)
                                ),
                            },
                            "tools": {
                                "TOTAL_TOOL_CALLS": int(80 * scale),
                                "EXPLORATION_CALLS": int(40 * scale),
                                "UNIQUE_FILES_READ": int(20 * scale),
                                "EDIT_CALLS": int(10 * scale),
                                "WRITE_CALLS": int(4 * scale),
                                "TEST_COMMAND_RUNS": int(6 * scale),
                                "CI_COMMAND_RUNS": int(4 * scale),
                            },
                            "timing": {"MODEL_WALL_SECONDS": 600.0 * scale},
                        },
                        "outcome": {"is_result": False, "scored": False},
                    }
                    if key not in omit_set:
                        record["functional_evaluation"] = {
                            "record": "afci-bench/v2/functional-evaluation",
                            "authority": "SL-V2-EFF-FUNC-01",
                            "executed": True,
                            "evaluator_task": task,
                            "semantic_case_count_expected": 4,
                            "semantic_case_count_executed": 4,
                            "semantic_pass_count": 4 if valid else 3,
                            "semantic_fail_count": 0 if valid else 1,
                            "semantic_error_count": 0,
                            "nonsemantic_case_count_expected": (
                                3 if task == "PT07" else 0
                            ),
                            "nonsemantic_case_count_executed": (
                                3 if task == "PT07" else 0
                            ),
                            "nonsemantic_pass_count": 3 if task == "PT07" else 0,
                            "nonsemantic_fail_count": 0,
                            "nonsemantic_error_count": 0,
                            "missing_case_ids": [],
                            "missing_semantic_case_ids": [],
                            "duplicate_case_ids": [],
                            "runtime_error": None,
                            "functional_valid": valid,
                        }
                    records.append(record)
    return records


def self_check() -> Dict[str, object]:
    """Prove the frozen analysis computes over 36 records carrying verdicts.

    It reads NO observation and creates none: every input is synthetic. What it
    establishes is computability — that the pairing, the counts, the primary and
    secondary ratios, the reset overhead and the decision rule all produce values
    once a run record carries ``functional_evaluation.functional_valid``, which
    is exactly what was missing before ``SL-V2-EFF-FUNC-01``.
    """
    scenarios = {
        # C4 much cheaper and every run valid: the rule must be able to reach
        # its most favourable branch, or a favourable pilot could not be read.
        "all_valid_c4_cheaper": synthetic_records(c4_input_ratio=0.8),
        # C4 dearer: the rule must also be able to reach its least favourable
        # branch, or the analysis would only be able to say yes.
        "all_valid_c4_dearer": synthetic_records(c4_input_ratio=1.3),
        # Seven blocks unusable: 11.0's minimum must actually bind.
        "insufficient_paired_data": synthetic_records(
            c4_input_ratio=0.8,
            invalid=tuple(
                (task, reset_state, "C4", repetition)
                for task in TASKS
                for reset_state in RESET_STATES
                for repetition in REPETITIONS
            )[:7],
        ),
        # A record with no functional block at all: MISSING must be visible and
        # must not be counted as valid.
        "one_record_unscored": synthetic_records(
            c4_input_ratio=0.8, omit_functional_block=(("PT01", "NON_RESET", "C1", 1),)
        ),
    }
    out: Dict[str, object] = {
        "record": "afci-bench/v2/efficiency-pilot-analysis-self-check",
        "synthetic_only": True,
        "observations_read": 0,
        "scenarios": {},
    }
    for name, records in scenarios.items():
        report = analyse(records)
        out["scenarios"][name] = {
            "records": len(records),
            # Present so the self-check demonstrates the SL-V2-EFF-ABORT-01
            # pooling guard running, rather than merely not tripping.
            "execution_attempt": report["execution_attempt"],
            "blocks_observed": report["blocks"]["observed"],
            "blocks_eligible": report["blocks"]["eligible"],
            "functional_valid_counts": report["functional_valid_counts"],
            "functional_status_counts": report["functional_status_counts"],
            "token_ratio_median": report["primary_endpoint"]["median"],
            "token_ratio_n": report["primary_endpoint"]["n"],
            "secondary_medians": {
                endpoint: block["median"]
                for endpoint, block in report["secondary_endpoints"].items()
            },
            "reset_overhead_computed": sorted(report["reset_overhead"]),
            "decision": report["decision"]["outcome"],
            "decision_rule": report["decision"]["rule"],
        }
    out["computable"] = all(
        scenario["blocks_observed"] == EXPECTED_BLOCKS
        and scenario["decision"] is not None
        for scenario in out["scenarios"].values()
    )
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "The frozen AFCI efficiency pilot analysis (SL-V2-EFF-01 §10/§11), "
            "using SL-V2-EFF-FUNC-01's per-run functional verdict."
        )
    )
    parser.add_argument(
        "--records", nargs="*", default=[],
        help="run_record.json files and/or directories holding them.",
    )
    parser.add_argument("--out", default=None, help="Write the report here.")
    parser.add_argument(
        "--self-check", action="store_true",
        help="Prove computability over SYNTHETIC records. Reads no observation.",
    )
    args = parser.parse_args(argv)

    try:
        if args.self_check:
            report = self_check()
        elif args.records:
            records, sources = load_records([Path(p) for p in args.records])
            report = analyse(records, sources=sources)
        else:
            parser.error("supply --records or --self-check")
            return 2
    except AnalysisRefusal as refusal:
        print(f"REFUSED <{refusal.code}> {refusal.message}", file=sys.stderr)
        return 1

    body = json.dumps(report, indent=2, sort_keys=True, default=str)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body + "\n", encoding="utf-8", newline="\n")
        print(f"report written to {out}")
    else:
        print(body)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
