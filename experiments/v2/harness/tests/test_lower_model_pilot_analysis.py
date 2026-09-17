"""`SL-V2-LOWER-MODEL-01`: the frozen analysis is COMPUTABLE before any data.

The Sonnet pilot was briefly executable and not analysable - its cost figures
would have existed and the gate admitting them would not have been computable.
This file is what stops that repeating: it proves, on SYNTHETIC records only,
that the lower-model pilot's output can actually be read, that the continuation
rule responds to the data in both directions, and that the two channels never
reach into each other.

Nothing here is an observation, an estimate or a prediction. Every record is
fabricated in memory, and none is written anywhere.
"""
import json
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[4]
HARNESS = REPO / "experiments" / "v2" / "harness"
sys.path.insert(0, str(HARNESS))

import efficiency_pilot_analysis as epa  # noqa: E402
import lower_model_pilot_analysis as lma  # noqa: E402
import lower_model_run_plan as lmp  # noqa: E402
import run_governance as gov  # noqa: E402

RECORD = REPO / "docs" / "v2" / "AFCI_LOWER_MODEL_PILOT_DECISION.md"


def _flat() -> str:
    return re.sub(r"\s+", " ", RECORD.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- 1
# Computability
# --------------------------------------------------------------------------- #
def test_the_analysis_is_computable_on_synthetic_records():
    report = lma.self_check(REPO)
    assert report["computable"], report["cases"]
    assert report["substantive_observations"] == 0
    assert "SYNTHETIC ONLY" in report["records_used"]
    assert report["is_result"] is False and report["scored"] is False


def test_the_self_check_exercises_both_directions():
    """An analysis that only ever ran on a favourable fabrication would show it
    produces a number, not that the number responds to the data."""
    report = lma.self_check(REPO)
    outcomes = {case["case"]: case["signals"] for case in report["cases"]}
    assert len(outcomes) == 4
    assert any(signals for signals in outcomes.values())
    assert any(not signals for signals in outcomes.values())


def test_a_full_synthetic_set_produces_the_frozen_shape():
    report = lma.analyse(lma.synthetic_records(), repo=REPO)
    assert report["observation_count"] == 18
    assert report["block_count"] == 9
    assert report["complete_blocks"] == 9
    assert report["expected_runs"] == 18 == lmp.EXPECTED_RUNS
    assert report["expected_blocks"] == 9 == lmp.EXPECTED_BLOCKS
    assert report["run_purpose"] == lmp.RUN_PURPOSE
    for flag in (
        "is_result", "scored", "enters_confirmatory_e1_analysis",
        "enters_treatment_effect_analysis", "enters_power_estimation",
    ):
        assert report[flag] is False, flag


# --------------------------------------------------------------------------- 2
# The two channels never read each other
# --------------------------------------------------------------------------- #
def test_architecture_is_reported_over_all_runs_not_only_eligible_pairs():
    """A run that violated the architecture is still a run that violated it."""
    report = lma.analyse(
        lma.synthetic_records(c4_functional_valid=False), repo=REPO
    )
    architecture = report["architecture"]
    # No pair is eligible...
    assert report["efficiency"]["eligible_pairs"] == 0
    # ...and the architecture counts are nonetheless complete.
    assert architecture["overall"]["C1"]["runs"] == 9
    assert architecture["overall"]["C4"]["runs"] == 9
    assert architecture["overall"]["C1"]["target_violation_runs"] == 9
    assert architecture["functionally_valid_pairs_only"]["C1"]["runs"] == 0


def test_efficiency_is_reported_over_functionally_valid_pairs_only():
    """A cost figure from a run that did not work is not a cheaper way."""
    report = lma.analyse(
        lma.synthetic_records(c4_functional_valid=False), repo=REPO
    )
    assert report["efficiency"]["eligible_pairs"] == 0
    primary = report["efficiency"]["endpoints"][lma.PRIMARY_ENDPOINT]
    assert primary["median"] is None
    assert report["efficiency"]["scope"] == "functionally-valid pairs only"


def test_the_quality_signal_can_hold_while_the_efficiency_signal_does_not():
    """The case the two-channel design exists for. A composite would hide it."""
    report = lma.analyse(
        lma.synthetic_records(
            c4_token=150000.0, exploration_ratio=1.5, tool_ratio=1.5
        ),
        repo=REPO,
    )
    decision = report["decision"]
    assert decision["quality_signal"] is True
    assert decision["efficiency_signal"] is False
    assert decision["expansion_authorised"] is True
    assert decision["signals_held"] == [lma.QUALITY_SIGNAL]
    assert decision["channels_combined_into_one_score"] is False


def test_the_efficiency_signal_can_hold_while_the_quality_signal_does_not():
    report = lma.analyse(
        lma.synthetic_records(c1_violations=0, c4_violations=0), repo=REPO
    )
    decision = report["decision"]
    assert decision["quality_signal"] is False
    assert decision["efficiency_signal"] is True
    assert decision["signals_held"] == [lma.EFFICIENCY_SIGNAL]


def test_an_architecture_value_never_moves_a_functional_verdict():
    """Change only the architecture counts; the functional tally must not move."""
    clean = lma.analyse(lma.synthetic_records(c4_violations=0), repo=REPO)
    dirty = lma.analyse(lma.synthetic_records(c4_violations=1), repo=REPO)
    assert clean["functional"] == dirty["functional"]
    assert (
        clean["efficiency"]["endpoints"][lma.PRIMARY_ENDPOINT]["median"]
        == dirty["efficiency"]["endpoints"][lma.PRIMARY_ENDPOINT]["median"]
    )
    assert (
        clean["architecture"]["overall"]["C4"]["target_violation_runs"]
        != dirty["architecture"]["overall"]["C4"]["target_violation_runs"]
    )


def test_an_efficiency_value_never_moves_an_architecture_count():
    cheap = lma.analyse(lma.synthetic_records(c4_token=10.0), repo=REPO)
    dear = lma.analyse(lma.synthetic_records(c4_token=10_000_000.0), repo=REPO)
    assert cheap["architecture"] == dear["architecture"]


# --------------------------------------------------------------------------- 3
# The functional guardrail, shared by both signals
# --------------------------------------------------------------------------- #
def test_a_broken_c4_arm_is_not_rescued_by_being_cheaper_or_tidier():
    report = lma.analyse(
        lma.synthetic_records(c4_functional_valid=False, c4_token=1.0), repo=REPO
    )
    decision = report["decision"]
    assert decision["expansion_authorised"] is False
    assert decision["signals_held"] == []
    assert report["functional"]["guardrail_holds"] is False
    assert decision["outcome"] == lma.NO_EXPANSION


def test_the_guardrail_tolerates_exactly_one_fewer_valid_c4_run():
    records = lma.synthetic_records()
    # Break ONE C4 run: a deficit of exactly 1 is permitted by both signals.
    for record in records:
        if record["condition"] == "C4":
            record["functional_evaluation"]["functional_valid"] = False
            break
    report = lma.analyse(records, repo=REPO)
    assert report["functional"]["c4_deficit_against_c1"] == 1
    assert report["functional"]["guardrail_holds"] is True
    assert report["decision"]["expansion_authorised"] is True


def test_the_guardrail_refuses_two_fewer_valid_c4_runs():
    records = lma.synthetic_records()
    broken = 0
    for record in records:
        if record["condition"] == "C4" and broken < 2:
            record["functional_evaluation"]["functional_valid"] = False
            broken += 1
    report = lma.analyse(records, repo=REPO)
    assert report["functional"]["c4_deficit_against_c1"] == 2
    assert report["functional"]["guardrail_holds"] is False
    assert report["decision"]["expansion_authorised"] is False


# --------------------------------------------------------------------------- 4
# The quality signal's own clauses
# --------------------------------------------------------------------------- #
def test_a_single_improved_task_does_not_carry_the_quality_signal():
    """Fewer violations OVERALL is not enough; §12.1.2 needs 2 of 3 tasks."""
    records = lma.synthetic_records(c1_violations=0, c4_violations=0)
    for record in records:
        if record["task_id"] != "PT01":
            continue
        violated = record["condition"] == "C1"
        record["architecture_evaluation"].update(
            {
                "architecture_violated_opportunity_count": int(violated),
                "raw_architecture_violation_count": int(violated),
                "target_opportunity_violated": violated,
            }
        )
    report = lma.analyse(records, repo=REPO)
    architecture = report["architecture"]
    assert architecture["c4_has_fewer_target_violation_runs_overall"] is True
    assert architecture["tasks_improved"] == ["PT01"]
    assert architecture["tasks_improved_count"] == 1
    assert report["decision"]["quality_signal"] is False


def test_an_unscored_run_is_never_counted_as_a_clean_one():
    """'Nobody measured this' is not evidence that the architecture held."""
    records = lma.synthetic_records()
    for record in records:
        if record["condition"] == "C1":
            record["architecture_evaluation"] = {
                "architecture_scored": False,
                "architecture_applicable_opportunity_count": None,
                "architecture_violated_opportunity_count": None,
                "raw_architecture_violation_count": None,
                "target_opportunity_violated": None,
            }
    report = lma.analyse(records, repo=REPO)
    c1 = report["architecture"]["overall"]["C1"]
    assert c1["runs"] == 9
    assert c1["scored_runs"] == 0
    assert c1["unscored_runs"] == 9
    # Excluded from every count, in both directions.
    assert c1["target_violation_runs"] == 0
    assert c1["applicable_opportunities"] == 0
    # ...and with nothing to beat, C4 cannot show FEWER violation runs.
    assert report["architecture"]["c4_has_fewer_target_violation_runs_overall"] is False


# --------------------------------------------------------------------------- 5
# The thresholds are the record's
# --------------------------------------------------------------------------- #
def test_every_threshold_appears_verbatim_in_the_authorising_record():
    flat = _flat()
    assert "median `TOKEN_RATIO` **< 1.00**" in flat
    assert "median `EXPLORATION_RATIO` **\u2264 0.80**" in flat
    assert "median `TOTAL_TOOL_RATIO` **\u2264 0.85**" in flat
    assert "at least 2 of the 3 tasks" in flat
    assert "no more than 1 below" in flat
    assert lma.NO_EXPANSION in flat


def test_the_module_constants_match_those_thresholds():
    assert lma.EFFICIENCY_MEDIAN_TOKEN_RATIO == 1.00
    assert lma.EFFICIENCY_MEDIAN_EXPLORATION_RATIO == 0.80
    assert lma.EFFICIENCY_MEDIAN_TOTAL_TOOL_RATIO == 0.85
    assert lma.QUALITY_TASK_MAJORITY == 2
    assert lma.FUNCTIONAL_GUARDRAIL_MAX_DEFICIT == 1
    # The token bar is STRICT and the other two are INCLUSIVE, because that is
    # how the record states them. Rounding them to one convention would move a
    # frozen bar after the fact.
    comparisons = {e: c for e, _, c in lma.EFFICIENCY_SIGNAL_ENDPOINTS}
    assert comparisons["TOTAL_INPUT_TOKENS"] == "<"
    assert comparisons["EXPLORATION_CALLS"] == "<="
    assert comparisons["TOTAL_TOOL_CALLS"] == "<="


@pytest.mark.parametrize(
    "ratio,expected", [(0.999, True), (1.0, False), (1.001, False)]
)
def test_the_token_bar_is_strict(ratio, expected):
    report = lma.analyse(
        lma.synthetic_records(
            c1_token=100000.0, c4_token=100000.0 * ratio,
            c1_violations=0, c4_violations=0,
            exploration_ratio=1.0, tool_ratio=1.0,
        ),
        repo=REPO,
    )
    assert report["decision"]["efficiency_signal"] is expected


@pytest.mark.parametrize("ratio,expected", [(0.80, True), (0.801, False)])
def test_the_exploration_bar_is_inclusive(ratio, expected):
    report = lma.analyse(
        lma.synthetic_records(
            c4_token=200000.0, c1_violations=0, c4_violations=0,
            exploration_ratio=ratio, tool_ratio=1.0,
        ),
        repo=REPO,
    )
    assert report["decision"]["efficiency_signal"] is expected


# --------------------------------------------------------------------------- 6
# Never pooled with the Sonnet pilot
# --------------------------------------------------------------------------- #
def test_a_sonnet_record_is_refused_rather_than_filtered_out():
    """Pooling is prevented by the code, not by a promise in a document."""
    record = lma.synthetic_records()[0]
    record["run_purpose"]["name"] = "AFCI_EFFICIENCY_PILOT"
    with pytest.raises(lma.AnalysisRefusal) as excinfo:
        lma.analyse([record], repo=REPO)
    assert excinfo.value.code == "RECORD_IS_NOT_A_LOWER_MODEL_OBSERVATION"


def test_a_reset_arm_record_is_refused():
    record = lma.synthetic_records()[0]
    record["reset"]["reset_state"] = "RESET"
    record["efficiency"]["reset_state"] = "RESET"
    with pytest.raises(lma.AnalysisRefusal) as excinfo:
        lma.analyse([record], repo=REPO)
    assert excinfo.value.code == "RESET_ARM_NOT_AUTHORISED"


def test_the_sonnet_reference_is_read_from_the_stored_package():
    reference = lma.sonnet_non_reset_reference(REPO)
    assert reference["available"] is True
    assert reference["source"] == lma.SONNET_PAIRS_CSV
    assert reference["run_purpose"] == "AFCI_EFFICIENCY_PILOT"
    assert reference["model"] == "claude-sonnet-5"
    assert reference["reset_state"] == "NON_RESET"
    # The NON_RESET subset is the right comparison: this pilot runs that arm and
    # only that arm, and the package's headline medians span both arms.
    assert reference["paired_n"] == 9
    assert reference["median_token_ratio"] == 1.5582


def test_the_records_single_quoted_sonnet_number_matches_the_stored_package():
    """The record quotes ONE Sonnet number; it must be the package's own."""
    reference = lma.sonnet_non_reset_reference(REPO)
    assert str(reference["median_token_ratio"]) in _flat()


def test_the_comparison_is_side_by_side_and_states_its_asymmetry():
    report = lma.analyse(lma.synthetic_records(), repo=REPO)
    comparison = report["sonnet_comparison"]
    assert comparison["pooled"] is False
    assert comparison["test_performed"] == "none"
    assert comparison["interaction_estimated"] == "none"
    assert comparison["quality_channel_comparable"] is False
    assert comparison["efficiency_channel_comparable"] is True
    assert "LOWER-MODEL ONLY" in comparison["asymmetry"]
    assert comparison["within_sonnet"]["model"] == "claude-sonnet-5"
    assert comparison["within_lower_model"]["run_purpose"] == lma.RUN_PURPOSE
    # Two ratios, reported beside each other, and a described difference.
    assert comparison["difference_lower_model_minus_sonnet"] is not None
    assert "LOWER" in comparison["direction"] or "HIGHER" in comparison["direction"]


# --------------------------------------------------------------------------- 7
# No inferential machinery
# --------------------------------------------------------------------------- #
def test_the_report_promises_no_p_values_or_intervals():
    decision = lma.analyse(lma.synthetic_records(), repo=REPO)["decision"]
    assert decision["p_values"] == "none"
    assert decision["confidence_intervals"] == "none"
    assert decision["confirmatory_effect_claim"] == "none"
    assert decision["frozen_before_any_observation"] is True


def test_the_module_imports_no_statistical_test_machinery():
    """Checked against imports and calls, not against prose.

    The module declares `"p_values": "none"` in its own report, so a bare
    substring sweep would flag the very statement that promises there are none.
    """
    source = (HARNESS / "lower_model_pilot_analysis.py").read_text(encoding="utf-8")
    low = source.lower()
    for banned in ("scipy", "statsmodels", "sklearn", "numpy"):
        assert not re.search(rf"^\s*(import|from)\s+{banned}\b", low, re.MULTILINE), banned
    for banned in ("ttest", "wilcoxon", "mannwhitney", "bootstrap", "pvalue",
                   "confint", "stdev", "variance"):
        assert f"{banned}(" not in low, banned
    # The one statistics call it does make, and the only one it needs.
    assert "statistics.median(" in low


def test_a_null_outcome_does_not_foreclose_the_open_source_study():
    decision = lma.analyse(
        lma.synthetic_records(
            c4_token=150000.0, c1_violations=0, c4_violations=0,
            exploration_ratio=1.5, tool_ratio=1.5,
        ),
        repo=REPO,
    )["decision"]
    assert decision["expansion_authorised"] is False
    assert "independent moderator" in decision["open_source_study"]
    assert "NOT authorised" in decision["open_source_study"]


# --------------------------------------------------------------------------- 8
# The metric reader is shared, so the two pilots are comparable
# --------------------------------------------------------------------------- #
def test_the_efficiency_metrics_are_read_by_the_same_code_as_the_sonnet_pilot():
    """Two readers of the same fields could drift and make §13 a comparison
    between measurement conventions instead of between models."""
    source = (HARNESS / "lower_model_pilot_analysis.py").read_text(encoding="utf-8")
    assert "epa._metric" in source
    assert "def _metric" not in source
    assert lma.PRIMARY_ENDPOINT == epa.PRIMARY_ENDPOINT


def test_no_lower_model_observation_exists_for_this_analysis_to_read():
    """The state this package must leave behind."""
    root = Path(r"D:\afci-runs\lower-model-pilot")
    found = sorted(p.name for p in root.glob("*")) if root.exists() else []
    assert found == [], f"a lower-model observation exists: {found}"
    assert gov.RUN_PURPOSES[lma.RUN_PURPOSE].repetitions == 3
