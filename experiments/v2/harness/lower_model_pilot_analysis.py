#!/usr/bin/env python3
"""``SL-V2-LOWER-MODEL-01``: the frozen analysis of the lower-model pilot.

Why this exists before the data does
------------------------------------
The Sonnet efficiency pilot was, for a while, **executable and not analysable**:
its cost figures would have existed and the gate that admits them would not have
been computable. That was caught in time and it is not repeated here. This module
is written, executed against synthetic records and committed **while zero
lower-model observations exist**, so the question "can this pilot's output
actually be read?" is answered before a single paid run is spent on it.

What it reads
-------------
Run records, and nothing else. It never invokes a model, never scores anything,
and never consults an artifact the runner did not write.

**Only ``AFCI_LOWER_MODEL_PILOT`` records.** A record from any other purpose is a
refusal, not a filter — which is what makes "never pooled with the Sonnet pilot"
a property of the code rather than a promise in a document. The Sonnet comparison
in :func:`compare_with_sonnet` is assembled from the *stored evidence package*,
side by side, and the two are never summed, averaged or modelled together.

Two channels, never collapsed
-----------------------------
`§10` measures architecture quality and efficiency separately and `§11.3` forbids
combining them. That is structural here: :func:`architecture_summary` and
:func:`efficiency_summary` share no input beyond the block list, neither reads
the other's output, and :func:`decide` evaluates the two continuation signals
**independently** — either one suffices, and neither can compensate for the other.

One deliberate asymmetry between them, from `§11.2`: architecture is reported over
**all** runs, because a run that violated the architecture is still a run that
violated it; efficiency is reported over **functionally-valid pairs only**,
because a cost figure from a run that did not work is not a cheaper way of doing
the task. The functionally-valid architecture subset is reported alongside, so a
reader can see both, and neither is presented as the other.

No p-values. No confidence intervals. No confirmatory effect claim.
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import efficiency_pilot_analysis as epa

#: The ONE purpose this analysis reads.
RUN_PURPOSE = "AFCI_LOWER_MODEL_PILOT"
DECISION_RECORD = "docs/v2/AFCI_LOWER_MODEL_PILOT_DECISION.md"

#: The purpose this analysis must NEVER pool with, named so the refusal can say
#: what it is refusing rather than only that it refused.
SONNET_RUN_PURPOSE = "AFCI_EFFICIENCY_PILOT"

TASKS: Tuple[str, ...] = ("PT01", "PT04", "PT07")
CONDITIONS: Tuple[str, ...] = ("C1", "C4")
RESET_STATE = "NON_RESET"
REPETITIONS: Tuple[int, ...] = (1, 2, 3)

#: 3 tasks x 3 repetitions, each holding one C1 and one C4 run.
EXPECTED_BLOCKS = len(TASKS) * len(REPETITIONS)
EXPECTED_RUNS = EXPECTED_BLOCKS * len(CONDITIONS)

# --------------------------------------------------------------------------- #
# §12 — the frozen continuation rule, as data
#
# Every threshold below is quoted from the record, and a test asserts each one
# appears in it verbatim, so a drift between this module and the adjudication is
# a mechanical failure rather than a reading.
# --------------------------------------------------------------------------- #
#: §12.1.3 / §12.2.1. The functional guardrail, shared by BOTH signals: the C4
#: functionally-valid count may be at most this far below C1's.
FUNCTIONAL_GUARDRAIL_MAX_DEFICIT = 1

#: §12.1.2. A task improves when its C4 target-violation run count is STRICTLY
#: lower than its C1 count, and this many of the three tasks must improve.
QUALITY_TASK_MAJORITY = 2

#: §12.2.2. Any ONE of these suffices. The comparisons are NOT uniform - the
#: token threshold is strict and the other two are inclusive - because that is
#: how the record states them, and rounding them to one convention would move a
#: frozen bar after the fact.
EFFICIENCY_MEDIAN_TOKEN_RATIO = 1.00
EFFICIENCY_MEDIAN_EXPLORATION_RATIO = 0.80
EFFICIENCY_MEDIAN_TOTAL_TOOL_RATIO = 0.85

QUALITY_SIGNAL = "QUALITY SIGNAL"
EFFICIENCY_SIGNAL = "EFFICIENCY SIGNAL"
EXPANSION_AUTHORISED = "EXPANSION AUTHORISED"
NO_EXPANSION = "DO NOT EXPAND THE SYNTHETIC LOWER-MODEL MATRIX AUTOMATICALLY"

#: §12.3. What a null result does NOT foreclose, stated in the report so a reader
#: never has to infer it from the absence of a sentence.
OPEN_SOURCE_STUDY_STATEMENT = (
    "A separate open-source repository complexity study may still proceed, "
    "because repository complexity is an independent moderator and this pilot "
    "measures nothing about it. That study is a distinct future experiment and "
    "is NOT authorised by this record or by this outcome."
)

#: §10.3 / §11.2. The paired efficiency endpoints, C4/C1, lower better for C4.
PRIMARY_ENDPOINT = "TOTAL_INPUT_TOKENS"
SECONDARY_ENDPOINTS: Tuple[str, ...] = (
    "MODEL_WALL_SECONDS",
    "TOTAL_TOOL_CALLS",
    "EXPLORATION_CALLS",
    "UNIQUE_FILES_READ",
    "EDIT_AND_WRITE_CALLS",
    "TOTAL_OUTPUT_TOKENS",
    "CI_COMMAND_RUNS",
    "TEST_COMMAND_RUNS",
)

#: The endpoints the continuation rule reads, mapped to their §12.2.2 thresholds
#: and comparison. Kept as data so :func:`decide` cannot use a different bar from
#: the one documented here.
EFFICIENCY_SIGNAL_ENDPOINTS: Tuple[Tuple[str, float, str], ...] = (
    (PRIMARY_ENDPOINT, EFFICIENCY_MEDIAN_TOKEN_RATIO, "<"),
    ("EXPLORATION_CALLS", EFFICIENCY_MEDIAN_EXPLORATION_RATIO, "<="),
    ("TOTAL_TOOL_CALLS", EFFICIENCY_MEDIAN_TOTAL_TOOL_RATIO, "<="),
)

#: §10.1. Every architecture field a run record carries, read and never derived.
ARCHITECTURE_COUNTS: Tuple[str, ...] = (
    "architecture_applicable_opportunity_count",
    "architecture_violated_opportunity_count",
    "raw_architecture_violation_count",
)

#: The one place each verdict may come from, named so a reader can check that
#: nothing else was consulted.
FUNCTIONAL_VALIDITY_SOURCE = "record.functional_evaluation.functional_valid"
ARCHITECTURE_SOURCE = "record.architecture_evaluation"
ARCHITECTURE_NEVER_INFERRED_FROM = (
    "the functional verdict",
    "CI success",
    "model prose",
    "the number of files changed",
    "any efficiency metric",
)

ARCHITECTURE_SCORED = "SCORED"
ARCHITECTURE_UNSCORED = "UNSCORED"

#: §13. The stored Sonnet evidence, read rather than restated. The pilot's own
#: record quotes ONE number (the NON_RESET median token ratio) and defers every
#: other value to this package, so nothing here can go stale against it.
SONNET_PAIRS_CSV = (
    "study-results/05_efficiency_attempt_2_completed/attempt2_primary_pairs.csv"
)
SONNET_RATIOS_CSV = (
    "study-results/05_efficiency_attempt_2_completed/attempt2_endpoint_ratios.csv"
)

#: §13. Stated wherever the comparison is, because a reader must not have to
#: notice it themselves.
SONNET_COMPARISON_ASYMMETRY = (
    "The claude-sonnet-5 efficiency pilot produced NO architecture measurement "
    "at all under its frozen cost-only governance, so the quality channel has no "
    "Sonnet counterpart and the quality comparison is LOWER-MODEL ONLY. Only the "
    "efficiency channel is comparable across the two models."
)
NEVER_POOLED = (
    "Sonnet and lower-model records are NEVER pooled into one treatment "
    "estimate. They are two separate experiments on two separate models, and one "
    "number covering both would be an estimate of nothing. What is reported is "
    "within-Sonnet C4/C1, within-lower-model C4/C1, and the direction and "
    "magnitude of the difference, described rather than tested."
)


class AnalysisRefusal(RuntimeError):
    """A fail-closed analysis refusal. ``code`` is machine-readable."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


# --------------------------------------------------------------------------- #
# One observation
# --------------------------------------------------------------------------- #
class Observation:
    """One run record, read only for the fields the frozen analysis names.

    The efficiency metric reader is REUSED from the Sonnet pilot's analysis
    rather than reimplemented. That is deliberate and load-bearing: §13 compares
    the two pilots' ratios, and two readers of the same record fields could drift
    apart and make the comparison one between measurement conventions instead of
    between models.
    """

    def __init__(self, record: Dict[str, object], source: str = "<memory>") -> None:
        self.source = source
        self.record = record
        purpose = (record.get("run_purpose") or {}).get("name")
        if purpose != RUN_PURPOSE:
            raise AnalysisRefusal(
                "RECORD_IS_NOT_A_LOWER_MODEL_OBSERVATION",
                f"{source}: run_purpose is {purpose!r}; this analysis reads "
                f"{RUN_PURPOSE} records only. A {SONNET_RUN_PURPOSE} record is "
                "refused here rather than filtered out, because pooling the two "
                "would estimate nothing",
            )
        self.task_id = str(record.get("task_id") or "")
        self.condition = str(record.get("condition") or "")
        self.repetition = record.get("repetition")
        self.efficiency: Dict[str, object] = record.get("efficiency") or {}
        self.reset_state = str(
            (record.get("reset") or {}).get("reset_state")
            or self.efficiency.get("reset_state")
            or ""
        )
        self.functional_status, self.functional_valid = self._functional(record)
        (
            self.architecture_status,
            self.architecture,
            self.target_violated,
        ) = self._architecture(record)

    @staticmethod
    def _functional(record: Dict[str, object]) -> Tuple[str, bool]:
        """Read the verdict from the ONE place, or report that it is absent."""
        block = record.get("functional_evaluation")
        if not isinstance(block, dict) or "functional_valid" not in block:
            return epa.FUNCTIONAL_MISSING, False
        valid = block.get("functional_valid")
        if not isinstance(valid, bool):
            return epa.FUNCTIONAL_MISSING, False
        return (epa.FUNCTIONAL_VALID if valid else epa.FUNCTIONAL_INVALID), valid

    @staticmethod
    def _architecture(
        record: Dict[str, object],
    ) -> Tuple[str, Dict[str, object], Optional[bool]]:
        """Read the architecture counts, or report that the run was not scored.

        ``UNSCORED`` and "scored, zero violations" are different facts and this
        keeps them apart. An unscored run contributes to NO architecture count in
        either direction — it is excluded and reported as excluded, never folded
        in as a clean run, because "nobody measured this" is not evidence that
        the architecture held.
        """
        block = record.get("architecture_evaluation")
        if not isinstance(block, dict) or not block.get("architecture_scored"):
            return ARCHITECTURE_UNSCORED, {}, None
        counts: Dict[str, object] = {}
        for field in ARCHITECTURE_COUNTS:
            value = block.get(field)
            if not isinstance(value, int) or isinstance(value, bool):
                return ARCHITECTURE_UNSCORED, {}, None
            counts[field] = value
        target = block.get("target_opportunity_violated")
        return (
            ARCHITECTURE_SCORED,
            counts,
            target if isinstance(target, bool) else None,
        )

    @property
    def block_key(self) -> Tuple[str, object]:
        return (self.task_id, self.repetition)

    def metric(self, name: str) -> Optional[float]:
        return epa._metric(self.efficiency, name)

    def to_dict(self) -> Dict[str, object]:
        return {
            "source": self.source,
            "task_id": self.task_id,
            "condition": self.condition,
            "reset_state": self.reset_state,
            "repetition": self.repetition,
            "functional_status": self.functional_status,
            "functional_valid": self.functional_valid,
            "architecture_status": self.architecture_status,
            "target_opportunity_violated": self.target_violated,
            **self.architecture,
        }


# --------------------------------------------------------------------------- #
# §11.1 Pairing
# --------------------------------------------------------------------------- #
def build_blocks(observations: Sequence[Observation]) -> List[Dict[str, object]]:
    """Group observations into (task x repetition) blocks.

    A block is complete only with exactly one ``C1`` and exactly one ``C4``. Two
    records for one arm is an accounting error, not a choice to be made here, so
    it is reported and the block is left incomplete rather than resolved.
    """
    grouped: Dict[Tuple[str, object], Dict[str, List[Observation]]] = {}
    for obs in observations:
        if obs.reset_state and obs.reset_state != RESET_STATE:
            raise AnalysisRefusal(
                "RESET_ARM_NOT_AUTHORISED",
                f"{obs.source}: reset_state is {obs.reset_state!r}; "
                f"{RUN_PURPOSE} authorises {RESET_STATE} only and this analysis "
                "never reads an arm the purpose does not run",
            )
        arm = grouped.setdefault(obs.block_key, {c: [] for c in CONDITIONS})
        if obs.condition not in arm:
            raise AnalysisRefusal(
                "CONDITION_NOT_IN_THE_PILOT",
                f"{obs.source}: condition {obs.condition!r} is not one of "
                f"{list(CONDITIONS)}",
            )
        arm[obs.condition].append(obs)

    blocks: List[Dict[str, object]] = []
    for key in sorted(grouped, key=lambda k: (k[0], str(k[1]))):
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
                # Carried even though this pilot runs one arm. The ratio
                # computation is REUSED from the Sonnet pilot's analysis so the
                # two produce comparable numbers, and it reads this field; a
                # block that omitted it would be silently unusable there.
                "reset_state": RESET_STATE,
                "repetition": key[1],
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
# §11.2 Functional
# --------------------------------------------------------------------------- #
def functional_summary(observations: Sequence[Observation]) -> Dict[str, object]:
    """``C1`` and ``C4`` functionally-valid counts, out of the blocks that exist."""
    per_arm: Dict[str, Dict[str, int]] = {
        c: {"valid": 0, "invalid": 0, "missing": 0, "runs": 0} for c in CONDITIONS
    }
    for obs in observations:
        arm = per_arm[obs.condition]
        arm["runs"] += 1
        if obs.functional_status == epa.FUNCTIONAL_VALID:
            arm["valid"] += 1
        elif obs.functional_status == epa.FUNCTIONAL_INVALID:
            arm["invalid"] += 1
        else:
            arm["missing"] += 1

    c1, c4 = per_arm["C1"]["valid"], per_arm["C4"]["valid"]
    deficit = c1 - c4
    return {
        "denominator": EXPECTED_BLOCKS,
        "source": FUNCTIONAL_VALIDITY_SOURCE,
        "per_arm": per_arm,
        "C1_valid": c1,
        "C4_valid": c4,
        "c4_deficit_against_c1": deficit,
        "guardrail_max_deficit": FUNCTIONAL_GUARDRAIL_MAX_DEFICIT,
        # The clause BOTH continuation signals share. A C4 arm that works less
        # often is not made acceptable by being cheaper or tidier.
        "guardrail_holds": deficit <= FUNCTIONAL_GUARDRAIL_MAX_DEFICIT,
    }


# --------------------------------------------------------------------------- #
# §11.2 Architecture
# --------------------------------------------------------------------------- #
def architecture_summary(
    observations: Sequence[Observation],
    blocks: Sequence[Dict[str, object]],
) -> Dict[str, object]:
    """Architecture counts by task and overall, per arm.

    Reported over ALL runs. A run that violated the architecture is still a run
    that violated it, and restricting this to functionally-valid pairs would
    quietly discard the violations most likely to matter. The functionally-valid
    subset is computed alongside and reported as its own figure.
    """
    overall = _architecture_tally(observations)
    by_task = {
        task: _architecture_tally([o for o in observations if o.task_id == task])
        for task in TASKS
    }

    paired: List[Observation] = []
    for block in blocks:
        if block["eligible"]:
            paired.extend([block["_c1"], block["_c4"]])

    improved = sorted(
        task
        for task in TASKS
        if by_task[task]["C4"]["target_violation_runs"]
        < by_task[task]["C1"]["target_violation_runs"]
    )
    return {
        "source": ARCHITECTURE_SOURCE,
        "never_inferred_from": list(ARCHITECTURE_NEVER_INFERRED_FROM),
        "scope": "ALL runs, scored or not; unscored runs are excluded and counted",
        "overall": overall,
        "by_task": by_task,
        "functionally_valid_pairs_only": _architecture_tally(paired),
        "c4_has_fewer_target_violation_runs_overall": (
            overall["C4"]["target_violation_runs"]
            < overall["C1"]["target_violation_runs"]
        ),
        "tasks_improved": improved,
        "tasks_improved_count": len(improved),
        "task_majority_required": QUALITY_TASK_MAJORITY,
    }


def _architecture_tally(observations: Sequence[Observation]) -> Dict[str, object]:
    tally: Dict[str, object] = {}
    for condition in CONDITIONS:
        arm = [o for o in observations if o.condition == condition]
        scored = [o for o in arm if o.architecture_status == ARCHITECTURE_SCORED]
        tally[condition] = {
            "runs": len(arm),
            "scored_runs": len(scored),
            "unscored_runs": len(arm) - len(scored),
            "target_violation_runs": sum(1 for o in scored if o.target_violated),
            "applicable_opportunities": sum(
                int(o.architecture["architecture_applicable_opportunity_count"])
                for o in scored
            ),
            "violated_opportunities": sum(
                int(o.architecture["architecture_violated_opportunity_count"])
                for o in scored
            ),
            "raw_violations": sum(
                int(o.architecture["raw_architecture_violation_count"])
                for o in scored
            ),
        }
    return tally


# --------------------------------------------------------------------------- #
# §11.2 Efficiency
# --------------------------------------------------------------------------- #
def efficiency_summary(blocks: Sequence[Dict[str, object]]) -> Dict[str, object]:
    """Paired ``C4/C1`` ratios over the functionally-valid pairs only."""
    endpoints: Dict[str, object] = {}
    for endpoint in (PRIMARY_ENDPOINT,) + SECONDARY_ENDPOINTS:
        endpoints[endpoint] = epa.paired_ratios(blocks, endpoint)
    return {
        "scope": "functionally-valid pairs only",
        "direction": "C4 / C1; lower is better for C4",
        "primary": PRIMARY_ENDPOINT,
        "eligible_pairs": sum(1 for b in blocks if b["eligible"]),
        "endpoints": endpoints,
    }


def _median_of(summary: Dict[str, object], endpoint: str) -> Optional[float]:
    block = (summary.get("endpoints") or {}).get(endpoint) or {}
    value = block.get("median")
    return None if value is None else float(value)


# --------------------------------------------------------------------------- #
# §12 The frozen continuation rule
# --------------------------------------------------------------------------- #
def _clause(name: str, satisfied: bool, detail: str) -> Dict[str, object]:
    return {"clause": name, "satisfied": bool(satisfied), "detail": detail}


def decide(
    functional: Dict[str, object],
    architecture: Dict[str, object],
    efficiency: Dict[str, object],
) -> Dict[str, object]:
    """Evaluate the two continuation signals INDEPENDENTLY.

    Either one authorises expansion. Neither compensates for the other, and they
    are never combined into a score: a pilot where architecture improved and
    tokens rose modestly is exactly the case this design exists to be able to
    see, and a composite would report it as a wash.
    """
    guardrail = bool(functional["guardrail_holds"])
    guardrail_detail = (
        f"C4 valid {functional['C4_valid']} vs C1 valid {functional['C1_valid']}; "
        f"deficit {functional['c4_deficit_against_c1']} <= "
        f"{FUNCTIONAL_GUARDRAIL_MAX_DEFICIT}"
    )

    # ---- §12.1 quality ---------------------------------------------------- #
    fewer = bool(architecture["c4_has_fewer_target_violation_runs_overall"])
    majority = architecture["tasks_improved_count"] >= QUALITY_TASK_MAJORITY
    quality_clauses = [
        _clause(
            "12.1.1 C4 has fewer target architecture-violation runs overall",
            fewer,
            f"C4 {architecture['overall']['C4']['target_violation_runs']} vs "
            f"C1 {architecture['overall']['C1']['target_violation_runs']}",
        ),
        _clause(
            f"12.1.2 improvement in at least {QUALITY_TASK_MAJORITY} of "
            f"{len(TASKS)} tasks",
            majority,
            f"improved: {architecture['tasks_improved'] or 'none'}",
        ),
        _clause("12.1.3 functional guardrail", guardrail, guardrail_detail),
    ]
    quality = all(c["satisfied"] for c in quality_clauses)

    # ---- §12.2 efficiency -------------------------------------------------- #
    triggers = []
    for endpoint, threshold, comparison in EFFICIENCY_SIGNAL_ENDPOINTS:
        median = _median_of(efficiency, endpoint)
        if median is None:
            met = False
            detail = f"median {endpoint} is undefined; no eligible pair produced one"
        else:
            met = median < threshold if comparison == "<" else median <= threshold
            detail = f"median {endpoint} {median:.4f} {comparison} {threshold:.2f}"
        triggers.append(
            {**_clause(f"12.2.2 {endpoint}", met, detail), "median": median,
             "threshold": threshold, "comparison": comparison}
        )
    any_trigger = any(t["satisfied"] for t in triggers)
    efficiency_clauses = [
        _clause("12.2.1 functional guardrail", guardrail, guardrail_detail),
        _clause("12.2.2 at least one endpoint threshold met", any_trigger,
                "; ".join(t["detail"] for t in triggers)),
    ]
    efficiency_signal = all(c["satisfied"] for c in efficiency_clauses)

    signals = [
        name
        for name, held in ((QUALITY_SIGNAL, quality),
                           (EFFICIENCY_SIGNAL, efficiency_signal))
        if held
    ]
    authorised = bool(signals)
    return {
        "authority": "SL-V2-LOWER-MODEL-01",
        "frozen_before_any_observation": True,
        "quality_signal": quality,
        "quality_clauses": quality_clauses,
        "efficiency_signal": efficiency_signal,
        "efficiency_clauses": efficiency_clauses,
        "efficiency_triggers": triggers,
        "signals_held": signals,
        "expansion_authorised": authorised,
        "outcome": f"{EXPANSION_AUTHORISED} - {' + '.join(signals)}"
        if authorised
        else NO_EXPANSION,
        "channels_combined_into_one_score": False,
        "open_source_study": OPEN_SOURCE_STUDY_STATEMENT,
        "p_values": "none",
        "confidence_intervals": "none",
        "confirmatory_effect_claim": "none",
    }


# --------------------------------------------------------------------------- #
# §13 The Sonnet comparison — descriptive, side by side, never pooled
# --------------------------------------------------------------------------- #
def sonnet_non_reset_reference(repo: Path) -> Dict[str, object]:
    """The Sonnet pilot's NON_RESET ratios, READ from the stored package.

    Derived from its per-pair table rather than copied from prose, so this cannot
    go stale against the evidence it names. The NON_RESET subset is the right
    comparison: this pilot runs that arm and only that arm, and the package's
    headline medians span both arms.
    """
    import csv

    path = Path(repo) / SONNET_PAIRS_CSV
    try:
        with path.open("r", encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
    except OSError as exc:
        return {"available": False, "detail": f"cannot read {SONNET_PAIRS_CSV}: {exc}"}

    ratios = [
        float(r["ratio_C4_over_C1"])
        for r in rows
        if r.get("reset_state") == RESET_STATE and r.get("ratio_C4_over_C1")
    ]
    if not ratios:
        return {"available": False, "detail": f"no {RESET_STATE} pairs in {path.name}"}
    return {
        "available": True,
        "source": SONNET_PAIRS_CSV,
        "run_purpose": SONNET_RUN_PURPOSE,
        "model": "claude-sonnet-5",
        "reset_state": RESET_STATE,
        "paired_n": len(ratios),
        "median_token_ratio": round(statistics.median(ratios), 4),
        "endpoint": PRIMARY_ENDPOINT,
    }


def compare_with_sonnet(
    efficiency: Dict[str, object], repo: Path
) -> Dict[str, object]:
    """Within-Sonnet C4/C1 beside within-lower-model C4/C1. Never pooled."""
    sonnet = sonnet_non_reset_reference(repo)
    mine = _median_of(efficiency, PRIMARY_ENDPOINT)
    theirs = sonnet.get("median_token_ratio") if sonnet.get("available") else None

    if mine is None or theirs is None:
        direction = "not computable"
        difference = None
    else:
        difference = round(mine - theirs, 4)
        direction = (
            "the lower model shows a LOWER C4/C1 token ratio than Sonnet"
            if mine < theirs
            else "the lower model shows a HIGHER C4/C1 token ratio than Sonnet"
            if mine > theirs
            else "the two models show the same C4/C1 token ratio"
        )
    return {
        "method": "descriptive; two within-model ratios reported side by side",
        "pooled": False,
        "never_pooled_statement": NEVER_POOLED,
        "asymmetry": SONNET_COMPARISON_ASYMMETRY,
        "quality_channel_comparable": False,
        "efficiency_channel_comparable": True,
        "within_sonnet": sonnet,
        "within_lower_model": {
            "run_purpose": RUN_PURPOSE,
            "reset_state": RESET_STATE,
            "paired_n": efficiency.get("eligible_pairs"),
            "median_token_ratio": None if mine is None else round(mine, 4),
            "endpoint": PRIMARY_ENDPOINT,
        },
        "difference_lower_model_minus_sonnet": difference,
        "direction": direction,
        "test_performed": "none",
        "interaction_estimated": "none",
    }


# --------------------------------------------------------------------------- #
# The report
# --------------------------------------------------------------------------- #
def analyse(
    records: Sequence[Dict[str, object]],
    *,
    sources: Optional[Sequence[str]] = None,
    repo: Path = Path(__file__).resolve().parents[3],
) -> Dict[str, object]:
    """The whole frozen analysis, from run records alone."""
    labels = list(sources) if sources else ["<memory>"] * len(records)
    observations = [
        Observation(record, labels[i] if i < len(labels) else "<memory>")
        for i, record in enumerate(records)
    ]
    blocks = build_blocks(observations)
    functional = functional_summary(observations)
    architecture = architecture_summary(observations, blocks)
    efficiency = efficiency_summary(blocks)
    decision = decide(functional, architecture, efficiency)
    return {
        "report": "afci-bench/v2/lower-model-pilot-analysis",
        "authority": "SL-V2-LOWER-MODEL-01",
        "authority_record": DECISION_RECORD,
        "run_purpose": RUN_PURPOSE,
        "reset_state": RESET_STATE,
        "expected_runs": EXPECTED_RUNS,
        "expected_blocks": EXPECTED_BLOCKS,
        "observation_count": len(observations),
        "block_count": len(blocks),
        "complete_blocks": sum(1 for b in blocks if b["complete"]),
        "functional": functional,
        "architecture": architecture,
        "efficiency": efficiency,
        "decision": decision,
        "sonnet_comparison": compare_with_sonnet(efficiency, repo),
        "blocks": [
            {k: v for k, v in b.items() if not k.startswith("_")} for b in blocks
        ],
        "is_result": False,
        "scored": False,
        "enters_confirmatory_e1_analysis": False,
        "enters_treatment_effect_analysis": False,
        "enters_power_estimation": False,
    }


# --------------------------------------------------------------------------- #
# Computability, proved with SYNTHETIC records only
# --------------------------------------------------------------------------- #
def synthetic_records(
    *,
    c1_token: float = 100000.0,
    c4_token: float = 90000.0,
    c1_violations: int = 1,
    c4_violations: int = 0,
    c4_functional_valid: bool = True,
    exploration_ratio: float = 0.5,
    tool_ratio: float = 0.5,
) -> List[Dict[str, object]]:
    """A full 18-record set, fabricated in memory and never written.

    It exists to prove the analysis is COMPUTABLE before any paid run is spent on
    producing records it might not be able to read. Every value is invented; none
    of it is an observation, an estimate, a prediction or a placeholder for one.
    """
    records: List[Dict[str, object]] = []
    for task in TASKS:
        for rep in REPETITIONS:
            for condition in CONDITIONS:
                is_c4 = condition == "C4"
                tokens = c4_token if is_c4 else c1_token
                explore = 40.0 * (exploration_ratio if is_c4 else 1.0)
                tools = 60.0 * (tool_ratio if is_c4 else 1.0)
                violations = c4_violations if is_c4 else c1_violations
                valid = c4_functional_valid if is_c4 else True
                records.append(
                    {
                        "run_purpose": {
                            "name": RUN_PURPOSE,
                            "decision_id": "SL-V2-LOWER-MODEL-01",
                            "confirmatory": False,
                        },
                        "task_id": task,
                        "condition": condition,
                        "repetition": rep,
                        "reset": {"reset_state": RESET_STATE},
                        "efficiency": {
                            "reset_state": RESET_STATE,
                            "usage": {
                                "TOTAL_INPUT_TOKENS": tokens,
                                "TOTAL_OUTPUT_TOKENS": tokens / 50.0,
                            },
                            "tools": {
                                "TOTAL_TOOL_CALLS": tools,
                                "EXPLORATION_CALLS": explore,
                                "UNIQUE_FILES_READ": explore / 2.0,
                                "EDIT_CALLS": 5.0,
                                "WRITE_CALLS": 1.0,
                                "CI_COMMAND_RUNS": 1.0,
                                "TEST_COMMAND_RUNS": 1.0,
                            },
                            "timing": {"MODEL_WALL_SECONDS": tokens / 1000.0},
                        },
                        "functional_evaluation": {"functional_valid": valid},
                        "architecture_evaluation": {
                            "architecture_scored": True,
                            "architecture_applicable_opportunity_count": 1,
                            "architecture_violated_opportunity_count": violations,
                            "raw_architecture_violation_count": violations,
                            "target_opportunity_violated": bool(violations),
                        },
                    }
                )
    return records


def self_check(repo: Path = Path(__file__).resolve().parents[3]) -> Dict[str, object]:
    """Prove the analysis computes, on synthetic records, in both directions.

    Both directions matters. An analysis that only ever ran against a favourable
    fabrication would demonstrate that it produces a number, not that the number
    responds to the data — and the continuation rule is the thing that must
    respond.
    """
    cases = []

    strong = analyse(synthetic_records(), repo=repo)
    cases.append(
        {
            "case": "C4 better on every channel",
            "expansion_authorised": strong["decision"]["expansion_authorised"],
            "signals": strong["decision"]["signals_held"],
            "expected": [QUALITY_SIGNAL, EFFICIENCY_SIGNAL],
        }
    )

    null = analyse(
        synthetic_records(
            c4_token=150000.0, c1_violations=0, c4_violations=0,
            exploration_ratio=1.5, tool_ratio=1.5,
        ),
        repo=repo,
    )
    cases.append(
        {
            "case": "C4 worse on cost, no architecture difference",
            "expansion_authorised": null["decision"]["expansion_authorised"],
            "signals": null["decision"]["signals_held"],
            "expected": [],
        }
    )

    # The case the two-channel design exists for: architecture improves while
    # tokens rise. A composite score would report this as a wash.
    quality_only = analyse(
        synthetic_records(c4_token=150000.0, exploration_ratio=1.5, tool_ratio=1.5),
        repo=repo,
    )
    cases.append(
        {
            "case": "architecture improves, cost rises",
            "expansion_authorised": quality_only["decision"]["expansion_authorised"],
            "signals": quality_only["decision"]["signals_held"],
            "expected": [QUALITY_SIGNAL],
        }
    )

    # The guardrail: a C4 arm that works less often is not rescued by cheapness.
    broken = analyse(
        synthetic_records(c4_functional_valid=False), repo=repo
    )
    cases.append(
        {
            "case": "C4 functionally invalid throughout",
            "expansion_authorised": broken["decision"]["expansion_authorised"],
            "signals": broken["decision"]["signals_held"],
            "expected": [],
        }
    )

    ok = all(case["signals"] == case["expected"] for case in cases)
    return {
        "report": "afci-bench/v2/lower-model-pilot-analysis-self-check",
        "authority": "SL-V2-LOWER-MODEL-01",
        "computable": ok,
        "cases": cases,
        "records_used": "SYNTHETIC ONLY; fabricated in memory and never written",
        "substantive_observations": 0,
        "is_result": False,
        "scored": False,
    }


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv: Optional[Sequence[str]] = None) -> int:  # pragma: no cover
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("records", nargs="*", help="run_record.json paths.")
    parser.add_argument("--self-check", action="store_true",
                        help="Prove computability on synthetic records only.")
    args = parser.parse_args(argv)

    if args.self_check or not args.records:
        report = self_check()
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["computable"] else 1

    paths = [Path(p) for p in args.records]
    records, sources = [], []
    for path in paths:
        records.append(json.loads(path.read_text(encoding="utf-8")))
        sources.append(str(path))
    print(json.dumps(analyse(records, sources=sources), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
