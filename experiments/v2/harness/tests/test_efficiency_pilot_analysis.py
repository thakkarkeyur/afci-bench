"""The FROZEN efficiency-pilot analysis, and the verdict it now has an input for.

``SL-V2-EFF-01`` §10 and §11 froze the pairing, the endpoints and the decision
rule before any observation existed. ``SL-V2-EFF-FUNC-01`` supplied the one input
they needed and did not have. This module asserts three separate things:

1. **The frozen text is still the implemented text.** Every threshold, every
   endpoint and every clause is checked against the decision record itself, so a
   drift in either direction is a failure rather than a reading.
2. **Functional validity comes from one place.** The pairing gate reads
   ``record.functional_evaluation.functional_valid`` and refuses to infer it from
   CI success, prose, an exit status, an architecture score or a file count.
3. **The analysis is computable.** Over 36 SYNTHETIC records it produces
   functional-valid counts, eligible pairs, token ratios, secondary ratios,
   reset overhead and a decision — which is exactly what could not be produced
   before, and is the blocker this package exists to clear.

Every record here is a fixture. No observation is read, none is created, and no
model is invoked.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[4]
HARNESS = REPO / "experiments" / "v2" / "harness"

import efficiency_pilot_analysis as an  # noqa: E402

DECISION = REPO / "docs" / "v2" / "AFCI_EFFICIENCY_PILOT_DECISION.md"
SCRIPT = HARNESS / "efficiency_pilot_analysis.py"


def _flat(path: Path) -> str:
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- 1
# The implemented analysis is the frozen one


def test_the_design_constants_match_the_frozen_record():
    text = _flat(DECISION)
    assert an.EXPECTED_BLOCKS == 18 and an.EXPECTED_RUNS == 36
    assert "A **block** is (task × reset state × repetition): 18 of them" in text
    assert "| blocks | 18 |" in text and "| runs | 36 |" in text
    assert an.TASKS == ("PT01", "PT04", "PT07")
    assert an.CONDITIONS == ("C1", "C4")
    assert an.RESET_STATES == ("NON_RESET", "RESET")


def test_every_threshold_is_the_frozen_threshold():
    text = _flat(DECISION)
    assert an.MINIMUM_ELIGIBLE_PAIRS == 12
    assert "At least 12 of the 18 blocks must have both conditions functionally valid" in text
    assert an.MAX_C4_FUNCTIONAL_DEFICIT == 1
    assert "no more than 1 lower than `C1`'s" in text
    assert an.STRONG_GO_MEDIAN_TOKEN_RATIO == 0.90
    assert "overall median `TOKEN_RATIO` ≤ **0.90**" in text
    assert an.STRONG_GO_C4_CHEAPER_FRACTION == 0.60
    assert "fewer tokens in ≥ **60%** of eligible pairs" in text
    assert an.STRONG_GO_TASK_MAJORITY == 2
    assert "≥ **2 of 3** tasks have a task-median `TOKEN_RATIO` < 1" in text
    assert an.QUALIFIED_GO_MEDIAN_TOKEN_RATIO == 1.10
    assert an.RESET_SPECIFIC_GO_MEDIAN_TOKEN_RATIO == 1.10
    assert dict(an.QUALIFIED_GO_ALTERNATIVES) == {
        "MODEL_WALL_SECONDS": 0.85,
        "EXPLORATION_CALLS": 0.75,
        "TOTAL_TOOL_CALLS": 0.80,
    }
    assert "`MODEL_WALL_SECONDS` ratio ≤ **0.85**" in text
    assert "`EXPLORATION_CALLS` ratio ≤ **0.75**" in text
    assert "`TOTAL_TOOL_CALLS` ratio ≤ **0.80**" in text


def test_the_endpoints_are_the_frozen_endpoints():
    text = _flat(DECISION)
    assert an.PRIMARY_ENDPOINT == "TOTAL_INPUT_TOKENS"
    assert "TOKEN_RATIO = C4 TOTAL_INPUT_TOKENS / C1 TOTAL_INPUT_TOKENS" in text
    named = [e for e, _ in an.SECONDARY_ENDPOINTS]
    assert named == [
        "MODEL_WALL_SECONDS", "TOTAL_TOOL_CALLS", "EXPLORATION_CALLS",
        "UNIQUE_FILES_READ", "TOTAL_OUTPUT_TOKENS", "EDIT_AND_WRITE_CALLS",
        "TEST_COMMAND_RUNS", "CI_COMMAND_RUNS",
    ]
    assert "`EDIT_CALLS + WRITE_CALLS`" in text
    assert dict(an.SECONDARY_ENDPOINTS)["TOTAL_OUTPUT_TOKENS"] is True, (
        "§9.2: a RESET run withholds its output total, so that endpoint is "
        "NON_RESET blocks only"
    )
    assert "(`NON_RESET` blocks only, §9.2)" in text
    assert an.RESET_OVERHEAD_ENDPOINTS == (
        "TOTAL_INPUT_TOKENS", "MODEL_WALL_SECONDS", "EXPLORATION_CALLS",
        "TOTAL_TOOL_CALLS",
    )
    assert "RESET_OVERHEAD_RATIO = RESET / NON_RESET" in text


def test_the_outcomes_are_worded_as_the_record_words_them():
    text = DECISION.read_text(encoding="utf-8")
    assert an.INCONCLUSIVE in text
    assert an.NO_SIGNAL in text
    for outcome in (an.STRONG_GO, an.QUALIFIED_GO, an.RESET_SPECIFIC_GO):
        assert outcome in text


def test_the_analysis_reports_no_inferential_statistic():
    report = an.analyse(an.synthetic_records())
    assert report["no_p_values"] and report["no_confidence_intervals"]
    assert report["no_effect_estimate"]
    assert report["is_result"] is False and report["confirmatory"] is False


# --------------------------------------------------------------------------- 2
# Functional validity comes from ONE place


def _one(**overrides):
    records = an.synthetic_records()
    record = records[0]
    record.update(overrides)
    return an.Observation(record)


def test_the_verdict_is_read_from_the_functional_evaluation_block():
    assert an.FUNCTIONAL_VALIDITY_SOURCE == (
        "record.functional_evaluation.functional_valid"
    )
    assert _one().functional_valid is True
    assert _one(
        functional_evaluation={"functional_valid": False}
    ).functional_status == an.FUNCTIONAL_INVALID


@pytest.mark.parametrize(
    "block",
    [None, {}, {"functional_valid": "yes"}, {"functional_valid": 1}, "true"],
    ids=["absent", "empty", "a string", "an int", "not an object"],
)
def test_an_unreadable_verdict_is_missing_and_never_valid(block):
    observation = _one(functional_evaluation=block)
    assert observation.functional_status == an.FUNCTIONAL_MISSING
    assert observation.functional_valid is False


def test_validity_is_never_inferred_from_anything_else():
    """A run that looks successful in every other way is still not valid."""
    observation = _one(
        functional_evaluation=None,
        outcome={"status": "COMPLETE", "code": None, "is_result": False,
                 "scored": False},
        invocation={"invoked": True, "exit_status": 0},
        post_run_capture={"added": ["a.ts"], "modified": ["b.ts"], "deleted": []},
    )
    assert observation.functional_valid is False
    source = SCRIPT.read_text(encoding="utf-8")
    for forbidden in ("ci_command_runs and", "exit_status ==", "architecture_score"):
        assert forbidden not in source
    for named in an.FUNCTIONAL_VALIDITY_NEVER_INFERRED_FROM:
        assert named in source


def test_a_record_from_another_purpose_is_refused_rather_than_analysed():
    records = an.synthetic_records()
    records[0]["run_purpose"]["name"] = "PT08_DIFFICULTY_DIAGNOSTIC"
    with pytest.raises(an.AnalysisRefusal) as exc:
        an.analyse(records)
    assert exc.value.code == "RECORD_IS_NOT_A_PILOT_OBSERVATION"


# --------------------------------------------------------------------------- 3
# §10.1 Pairing


def test_thirty_six_records_form_eighteen_blocks_each_holding_one_c1_and_one_c4():
    report = an.analyse(an.synthetic_records())
    assert report["blocks"]["observed"] == 18
    assert report["blocks"]["eligible"] == 18
    assert all(row["complete"] for row in report["blocks"]["rows"])


def test_a_pair_is_ineligible_unless_both_of_its_runs_are_valid():
    for condition in ("C1", "C4"):
        records = an.synthetic_records(
            invalid=(("PT04", "RESET", condition, 2),)
        )
        report = an.analyse(records)
        assert report["blocks"]["eligible"] == 17
        broken = [
            r for r in report["blocks"]["rows"]
            if (r["task_id"], r["reset_state"], r["repetition"])
            == ("PT04", "RESET", 2)
        ][0]
        assert broken["eligible"] is False
        assert "did not work" in broken["ineligible_reason"]


def test_an_ineligible_pair_contributes_to_no_ratio():
    report = an.analyse(an.synthetic_records(invalid=(("PT01", "NON_RESET", "C4", 1),)))
    assert report["primary_endpoint"]["n"] == 17
    assert all(
        (row["task_id"], row["reset_state"], row["repetition"])
        != ("PT01", "NON_RESET", 1)
        for row in report["primary_endpoint"]["pairs"]
    )


def test_a_duplicated_arm_is_reported_rather_than_silently_resolved():
    records = an.synthetic_records()
    records.append(json.loads(json.dumps(records[0])))
    report = an.analyse(records)
    duplicated = [r for r in report["blocks"]["rows"] if r["duplicated_conditions"]]
    assert len(duplicated) == 1
    assert duplicated[0]["eligible"] is False


# --------------------------------------------------------------------------- 4
# §10.2 / §10.3 / §10.4 Ratios


def test_the_primary_endpoint_is_c4_over_c1_and_lower_is_better_for_c4():
    report = an.analyse(an.synthetic_records(c4_input_ratio=0.5))
    assert report["primary_endpoint"]["endpoint"] == "TOTAL_INPUT_TOKENS"
    assert report["primary_endpoint"]["median"] == pytest.approx(0.5, abs=0.02)
    assert report["primary_endpoint"]["c4_lower_count"] == 18


def test_the_output_token_endpoint_uses_non_reset_blocks_only():
    report = an.analyse(an.synthetic_records())
    output = report["secondary_endpoints"]["TOTAL_OUTPUT_TOKENS"]
    assert output["non_reset_only"] is True
    assert output["n"] == 9, "nine NON_RESET blocks, and no RESET block"
    assert {row["reset_state"] for row in output["pairs"]} == {"NON_RESET"}


def test_an_undefined_ratio_is_dropped_and_counted_rather_than_invented():
    records = an.synthetic_records()
    for record in records:
        if record["condition"] == "C1" and record["task_id"] == "PT01":
            record["efficiency"]["usage"]["TOTAL_INPUT_TOKENS"] = 0
    report = an.analyse(records)
    assert report["primary_endpoint"]["n"] == 12
    assert len(report["primary_endpoint"]["undefined_pairs"]) == 6


def test_reset_overhead_is_computed_per_task_repetition_and_condition():
    report = an.analyse(an.synthetic_records())
    for endpoint in an.RESET_OVERHEAD_ENDPOINTS:
        rows = report["reset_overhead"][endpoint]["rows"]
        # 3 tasks x 3 repetitions x 2 conditions
        assert len(rows) == 18, endpoint
        assert all(row["ratio"] > 1 for row in rows), (
            "the synthetic RESET arm is constructed dearer, so the ratio must "
            "exceed one; an inverted ratio would mean RESET/NON_RESET was "
            "computed the other way round"
        )


def test_reset_overhead_ignores_a_run_that_did_not_work():
    report = an.analyse(an.synthetic_records(invalid=(("PT01", "RESET", "C4", 1),)))
    rows = report["reset_overhead"]["TOTAL_INPUT_TOKENS"]["rows"]
    assert not [
        r for r in rows
        if (r["task_id"], r["repetition"], r["condition"]) == ("PT01", 1, "C4")
    ]


# --------------------------------------------------------------------------- 5
# §11 The decision rule


def _decision(records):
    return an.analyse(records)["decision"]


def test_below_twelve_eligible_pairs_the_outcome_is_inconclusive():
    seven = tuple(
        (task, reset_state, "C4", repetition)
        for task in an.TASKS
        for reset_state in an.RESET_STATES
        for repetition in an.REPETITIONS
    )[:7]
    decision = _decision(an.synthetic_records(c4_input_ratio=0.5, invalid=seven))
    assert decision["outcome"] == an.INCONCLUSIVE
    assert decision["rule"] == "11.0"
    assert decision["efficiency_claim_made"] is False


def test_exactly_twelve_eligible_pairs_clears_the_minimum():
    six = tuple(
        (task, reset_state, "C4", repetition)
        for task in an.TASKS
        for reset_state in an.RESET_STATES
        for repetition in an.REPETITIONS
    )[:6]
    report = an.analyse(an.synthetic_records(c4_input_ratio=0.5, invalid=six))
    assert report["blocks"]["eligible"] == 12
    assert report["decision"]["rule"] != "11.0"


def test_a_clearly_cheaper_c4_reaches_strong_go():
    decision = _decision(an.synthetic_records(c4_input_ratio=0.5))
    assert decision["outcome"] == an.STRONG_GO
    assert decision["rule"] == "11.1"
    assert all(clause["satisfied"] for clause in decision["clauses"])


def test_a_clearly_dearer_c4_reaches_no_signal():
    decision = _decision(an.synthetic_records(c4_input_ratio=1.3))
    assert decision["outcome"] == an.NO_SIGNAL
    assert decision["rule"] == "11.4"
    assert decision["efficiency_claim_made"] is False


def test_the_functional_guardrail_can_block_a_favourable_cost_picture():
    """§11.1.2: C4 may be at most one functional-valid run behind C1.

    Three C4 runs invalidated leaves 15 eligible pairs — over the §11.0 minimum —
    with a token picture that would otherwise qualify. The guardrail is what must
    stop it, so this is the test that would catch the guardrail being dropped.
    """
    decision = _decision(
        an.synthetic_records(
            c4_input_ratio=0.5,
            invalid=(
                ("PT01", "NON_RESET", "C4", 1),
                ("PT04", "NON_RESET", "C4", 1),
                ("PT07", "NON_RESET", "C4", 1),
            ),
        )
    )
    assert decision["outcome"] == an.NO_SIGNAL
    guardrails = [
        c for c in decision["clauses"] if "functional guardrail" in c["clause"]
    ]
    assert guardrails and not any(c["satisfied"] for c in guardrails)


def test_a_one_run_deficit_does_not_trip_the_guardrail():
    decision = _decision(
        an.synthetic_records(
            c4_input_ratio=0.5, invalid=(("PT01", "NON_RESET", "C4", 1),)
        )
    )
    assert decision["outcome"] == an.STRONG_GO


def test_the_rules_are_evaluated_in_order_and_the_first_match_wins():
    """A picture that satisfies 11.2 but not 11.1 must report 11.2, not 11.4."""
    records = an.synthetic_records(c4_input_ratio=1.0)
    for record in records:
        if record["condition"] == "C4":
            # tokens flat, wall clock much better: the QUALIFIED GO shape
            record["efficiency"]["timing"]["MODEL_WALL_SECONDS"] = 300.0
    decision = _decision(records)
    assert decision["outcome"] == an.QUALIFIED_GO
    assert decision["rule"] == "11.2"
    assert [q["endpoint"] for q in decision["qualifying_endpoints"]] == [
        "MODEL_WALL_SECONDS"
    ]


def test_reset_specific_go_is_reachable_when_neither_rule_above_matches():
    """§11.3: C4 recovers from a reset more cheaply, and is otherwise level.

    The improvement is deliberately confined to the RESET arm and deliberately
    modest, so the overall medians stay above every §11.1 and §11.2 ceiling.
    That is the only shape §11.3 exists for; if this test passed with a bigger
    improvement it would be testing §11.2 by another name.
    """
    records = an.synthetic_records(c4_input_ratio=1.0)
    for record in records:
        if record["condition"] == "C4" and record["reset"]["reset_state"] == "RESET":
            usage, tools, timing = (
                record["efficiency"]["usage"],
                record["efficiency"]["tools"],
                record["efficiency"]["timing"],
            )
            usage["TOTAL_INPUT_TOKENS"] = int(usage["TOTAL_INPUT_TOKENS"] * 0.95)
            timing["MODEL_WALL_SECONDS"] = timing["MODEL_WALL_SECONDS"] * 0.90
            tools["EXPLORATION_CALLS"] = int(tools["EXPLORATION_CALLS"] * 0.90)
            tools["TOTAL_TOOL_CALLS"] = int(tools["TOTAL_TOOL_CALLS"] * 0.95)
    decision = _decision(records)
    assert decision["outcome"] == an.RESET_SPECIFIC_GO
    assert decision["rule"] == "11.3"
    assert all(clause["satisfied"] for clause in decision["clauses"])


# --------------------------------------------------------------------------- 6
# Architecture reporting consistency


def test_the_report_states_that_no_architecture_result_is_produced():
    report = an.analyse(an.synthetic_records())
    architecture = report["architecture"]
    assert architecture["produced"] is False
    assert architecture["e1_contribution"] is None
    assert architecture["thresholds_depending_on_architecture"] == []
    assert architecture["statement"] == (
        "Not produced by AFCI_EFFICIENCY_PILOT under its frozen cost-only "
        "governance. Existing pre-data legal/violating architecture validation "
        "was used only for eligibility. No live-run architecture treatment "
        "inference is made."
    )


def test_no_clause_of_the_decision_rule_reads_an_architecture_value():
    report = an.analyse(an.synthetic_records())
    for clause in report["decision"]["clauses"]:
        assert "architect" not in clause["clause"].lower()
        assert "violation" not in clause["clause"].lower()


# --------------------------------------------------------------------------- 7
# Computability — the blocker this package clears


def test_the_self_check_computes_every_frozen_quantity_over_synthetic_records():
    report = an.self_check()
    assert report["synthetic_only"] is True
    assert report["observations_read"] == 0
    assert report["computable"] is True
    for name, scenario in report["scenarios"].items():
        assert scenario["records"] == 36, name
        assert scenario["blocks_observed"] == 18, name
        assert scenario["functional_valid_counts"].keys() == {"C1", "C4"}, name
        assert scenario["reset_overhead_computed"] == sorted(
            an.RESET_OVERHEAD_ENDPOINTS
        ), name
        assert scenario["decision"] in {
            an.STRONG_GO, an.QUALIFIED_GO, an.RESET_SPECIFIC_GO,
            an.NO_SIGNAL, an.INCONCLUSIVE,
        }, name
    computed = report["scenarios"]["all_valid_c4_cheaper"]
    assert computed["token_ratio_median"] is not None
    assert computed["token_ratio_n"] == 18
    assert all(v is not None for v in computed["secondary_medians"].values())


def test_the_self_check_runs_as_a_command_and_reads_no_observation(tmp_path):
    out = tmp_path / "self-check.json"
    done = subprocess.run(
        [sys.executable, str(SCRIPT), "--self-check", "--out", str(out)],
        capture_output=True, text=True,
    )
    assert done.returncode == 0, done.stderr
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["computable"] is True
    assert report["observations_read"] == 0


def test_the_analysis_reads_records_from_disk(tmp_path):
    for index, record in enumerate(an.synthetic_records()):
        directory = tmp_path / f"run-{index:02d}"
        directory.mkdir()
        (directory / "run_record.json").write_text(
            json.dumps(record), encoding="utf-8", newline="\n"
        )
    out = tmp_path / "report.json"
    done = subprocess.run(
        [sys.executable, str(SCRIPT), "--records", str(tmp_path), "--out", str(out)],
        capture_output=True, text=True,
    )
    assert done.returncode == 0, done.stderr
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["observations"]["supplied"] == 36
    assert report["blocks"]["eligible"] == 18


def test_the_pilot_still_holds_no_observation():
    """The whole analysis is pre-data, and this is the mechanical proof of it."""
    results = REPO / "experiments" / "v2" / "results"
    assert sorted(p.name for p in results.iterdir()) == ["README.md"]
