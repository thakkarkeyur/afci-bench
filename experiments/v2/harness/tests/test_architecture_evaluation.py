"""`SL-V2-LOWER-MODEL-01` - the post-run ARCHITECTURE-quality channel.

What this file pins:

  * the channel is OFF for every purpose no Study-Lead decision put it on;
  * the verdict is DERIVED from the opportunity accounting and can never be
    supplied — by the private scorer, by a caller, or by a hand-assembled record;
  * every failure is RECORDED with null counts rather than raised or zeroed, so
    "nobody measured this" can never be read as "this candidate violated
    nothing";
  * a private identifier appearing in the structured result is REFUSED, not
    written;
  * the architecture channel and the functional channel never read each other;
  * the real channel runs end to end against a real prepared worktree.

No model is invoked.
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[4]
HARNESS = REPO / "experiments" / "v2" / "harness"
sys.path.insert(0, str(HARNESS))

import architecture_evaluation as ae  # noqa: E402
import functional_evaluation as fe  # noqa: E402
import prepare_model_worktree as pmw  # noqa: E402
import run_artifacts as art  # noqa: E402
import run_governance as gov  # noqa: E402

PURPOSE = "AFCI_LOWER_MODEL_PILOT"
AUTHORITY = "SL-V2-LOWER-MODEL-01"

#: A complete, well-formed scorer result for a conforming candidate.
CLEAN_RESULT = {
    "record": "afci-bench/private/architecture-evaluation-result",
    "authority": AUTHORITY,
    "evaluator_task": "PT01",
    "executed": True,
    "evaluator_name": "dependency-direction",
    "evaluator_version": "1.0.0",
    "alias_aware": True,
    "manifest_id": "EM-PT01-CORPUS",
    "scored_opportunity_count": 1,
    "architecture_applicable_opportunity_count": 1,
    "architecture_fixed_opportunity_count": 1,
    "architecture_violated_opportunity_count": 0,
    "architecture_absent_opportunity_count": 0,
    "raw_architecture_violation_count": 0,
    "target_opportunity_violated": False,
    "target_opportunity_status": "SATISFIED",
    "target_opportunity_digest": "0" * 64,
    "verdict": "CONFORMANT",
    "deterministic_order": True,
    "scored_file_count": 41,
    "scored_fingerprint_sha256": "1" * 64,
    "worktree_unchanged_during_evaluation": True,
    "runtime_error": None,
}

VIOLATING_RESULT = {
    **CLEAN_RESULT,
    "architecture_fixed_opportunity_count": 0,
    "architecture_violated_opportunity_count": 1,
    "raw_architecture_violation_count": 2,
    "target_opportunity_violated": True,
    "target_opportunity_status": "VIOLATION",
    "verdict": "VIOLATIONS",
}


def _stub_scorer(tmp_path: Path, payload, exit_status: int = 0) -> Path:
    """A fake private scorer that writes ``payload`` and exits.

    Used so the BOUNDARY can be tested independently of the evaluator: the
    private scorer's own correctness is executed in the private repository, and
    duplicating it here would test the copy rather than the contract.
    """
    root = tmp_path / "fake-private"
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    body = payload if isinstance(payload, str) else json.dumps(payload)
    (root / "scripts" / "score_architecture.py").write_text(
        "import json, sys\n"
        "out = sys.argv[sys.argv.index('--out') + 1]\n"
        f"open(out, 'w', encoding='utf-8').write({body!r})\n"
        f"raise SystemExit({exit_status})\n",
        encoding="utf-8",
    )
    return root


def _evaluate(tmp_path, payload, task="PT01", exit_status=0, worktree=None):
    private = _stub_scorer(tmp_path, payload, exit_status)
    candidate = worktree if worktree is not None else tmp_path / "worktree_post_run"
    Path(candidate).mkdir(parents=True, exist_ok=True)
    return ae.evaluate_preserved_worktree(
        task,
        Path(candidate),
        result_path=tmp_path / "architecture_evaluation_result.json",
        private_root=private,
    )


# --------------------------------------------------------------------------- 1
# The channel is off unless a decision turned it on
# --------------------------------------------------------------------------- #
def test_the_channel_is_off_for_every_unauthorised_purpose():
    for name, purpose in gov.RUN_PURPOSES.items():
        expected = name == PURPOSE
        assert ae.purpose_requires_architecture_evaluation(purpose) is expected, name


def test_the_channel_is_off_for_no_purpose_at_all():
    assert ae.purpose_requires_architecture_evaluation(None) is False


# --------------------------------------------------------------------------- 2
# The derivation
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "violated,expected", [(0, False), (1, True), (2, True), (7, True)]
)
def test_the_verdict_is_derived_from_the_violated_opportunity_count(violated, expected):
    counts = {"architecture_violated_opportunity_count": violated}
    assert ae.derive_violation_present(counts) is expected


def test_the_verdict_is_not_derived_from_the_raw_edge_count():
    """Several forbidden edges inside one frozen decision are ONE violated
    opportunity, and an edge outside every frozen decision is none of them."""
    counts = {
        "architecture_violated_opportunity_count": 0,
        "raw_architecture_violation_count": 9,
    }
    assert ae.derive_violation_present(counts) is False


def test_there_is_no_way_to_supply_the_verdict():
    assert "violation" not in ae.derive_violation_present.__code__.co_varnames[:1]
    assert ae.derive_violation_present.__code__.co_argcount == 1


@pytest.mark.parametrize("bad", [None, "1", 1.5, True, -1])
def test_a_non_integer_or_negative_count_is_refused(bad):
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        ae.derive_violation_present(
            {"architecture_violated_opportunity_count": bad}
        )
    assert excinfo.value.code == ae.ARCHITECTURE_EVALUATOR_MALFORMED_RESULT


# --------------------------------------------------------------------------- 3
# Fail-closed: null, never zero
# --------------------------------------------------------------------------- #
def test_an_absent_worktree_is_recorded_with_null_counts(tmp_path):
    block = ae.evaluate_preserved_worktree(
        "PT01", None, result_path=tmp_path / "r.json",
        private_root=_stub_scorer(tmp_path, CLEAN_RESULT),
    )
    assert block["executed"] is False
    assert block["architecture_scored"] is False
    assert block["runtime_error"]["code"] == ae.ARCHITECTURE_EVALUATION_NO_WORKTREE
    # The distinction the whole design exists for.
    assert block["architecture_violated_opportunity_count"] is None
    assert block["architecture_violation_present"] is None
    assert block["target_opportunity_violated"] is None


def test_an_absent_scorer_is_recorded_rather_than_substituted(tmp_path):
    (tmp_path / "wt").mkdir()
    block = ae.evaluate_preserved_worktree(
        "PT01", tmp_path / "wt", result_path=tmp_path / "r.json",
        private_root=tmp_path / "no-private-repo-here",
    )
    assert block["executed"] is False
    assert block["runtime_error"]["code"] == ae.ARCHITECTURE_EVALUATOR_UNAVAILABLE
    assert block["architecture_applicable_opportunity_count"] is None


def test_a_scorer_that_wrote_nothing_is_recorded(tmp_path):
    private = tmp_path / "fake-private"
    (private / "scripts").mkdir(parents=True)
    (private / "scripts" / "score_architecture.py").write_text(
        "raise SystemExit(3)\n", encoding="utf-8"
    )
    (tmp_path / "wt").mkdir()
    block = ae.evaluate_preserved_worktree(
        "PT01", tmp_path / "wt", result_path=tmp_path / "r.json",
        private_root=private,
    )
    assert block["runtime_error"]["code"] == ae.ARCHITECTURE_EVALUATOR_NO_RESULT
    assert block["architecture_scored"] is False


def test_an_unreadable_result_is_recorded(tmp_path):
    block = _evaluate(tmp_path, "{ not json")
    assert block["runtime_error"]["code"] == ae.ARCHITECTURE_EVALUATOR_MALFORMED_RESULT
    assert block["architecture_scored"] is False


def test_a_result_for_another_task_is_never_re_attributed(tmp_path):
    block = _evaluate(tmp_path, {**CLEAN_RESULT, "evaluator_task": "PT07"}, task="PT01")
    assert block["evaluator_task"] == "PT01"
    assert block["runtime_error"]["code"] == ae.ARCHITECTURE_EVALUATOR_MALFORMED_RESULT
    assert block["architecture_scored"] is False


def test_a_scorer_refusal_is_carried_through_with_its_own_code(tmp_path):
    refusal = {
        "record": "afci-bench/private/architecture-evaluation-result",
        "authority": AUTHORITY,
        "evaluator_task": "PT01",
        "executed": False,
        "runtime_error": {
            "code": "ARCHITECTURE_ENGINE_UNAVAILABLE",
            "detail": "the oracle runtime is not available",
        },
    }
    block = _evaluate(tmp_path, refusal, exit_status=3)
    assert block["architecture_scored"] is False
    assert block["runtime_error"]["code"] == "ARCHITECTURE_ENGINE_UNAVAILABLE"
    assert block["architecture_violation_present"] is None


def test_a_missing_count_is_refused_rather_than_defaulted(tmp_path):
    incomplete = {k: v for k, v in CLEAN_RESULT.items()}
    del incomplete["raw_architecture_violation_count"]
    block = _evaluate(tmp_path, incomplete)
    assert block["runtime_error"]["code"] == ae.ARCHITECTURE_EVALUATOR_MALFORMED_RESULT
    assert block["architecture_scored"] is False


@pytest.mark.parametrize(
    "field",
    [
        "architecture_applicable_opportunity_count",
        "architecture_fixed_opportunity_count",
        "architecture_absent_opportunity_count",
        "architecture_violated_opportunity_count",
    ],
)
def test_a_malformed_count_is_RECORDED_and_never_raised(tmp_path, field):
    """A raise would leave the caller with no block, which is the one outcome
    the frozen analysis cannot tell apart from 'not yet scored'."""
    block = _evaluate(tmp_path, {**CLEAN_RESULT, field: "one"})
    assert block["architecture_scored"] is False
    assert block["runtime_error"]["code"] == ae.ARCHITECTURE_EVALUATOR_MALFORMED_RESULT
    assert block["architecture_violation_present"] is None


def test_accounting_that_does_not_balance_is_refused(tmp_path):
    block = _evaluate(
        tmp_path,
        {**CLEAN_RESULT, "architecture_applicable_opportunity_count": 3},
    )
    assert block["runtime_error"]["code"] == ae.ARCHITECTURE_RESULT_NOT_DERIVABLE
    assert block["architecture_scored"] is False


def test_a_scorer_whose_target_boolean_contradicts_its_counts_is_refused(tmp_path):
    """Two independent readings of one scoring pass that disagree mean one is
    wrong, and the honest response is to record neither."""
    block = _evaluate(
        tmp_path, {**CLEAN_RESULT, "target_opportunity_violated": True}
    )
    assert block["runtime_error"]["code"] == ae.ARCHITECTURE_RESULT_NOT_DERIVABLE
    assert block["architecture_scored"] is False
    assert block["architecture_violation_present"] is None


def test_a_timeout_is_an_error_and_never_a_conforming_candidate(tmp_path):
    private = tmp_path / "fake-private"
    (private / "scripts").mkdir(parents=True)
    (private / "scripts" / "score_architecture.py").write_text(
        "import time\ntime.sleep(30)\n", encoding="utf-8"
    )
    (tmp_path / "wt").mkdir()
    block = ae.evaluate_preserved_worktree(
        "PT01", tmp_path / "wt", result_path=tmp_path / "r.json",
        private_root=private, timeout_seconds=1,
    )
    assert block["runtime_error"]["code"] == ae.ARCHITECTURE_EVALUATOR_TIMEOUT
    assert block["architecture_scored"] is False
    assert block["scorer"]["timed_out"] is True


# --------------------------------------------------------------------------- 4
# The happy paths
# --------------------------------------------------------------------------- #
def test_a_conforming_candidate_is_recorded_as_scored_and_clean(tmp_path):
    block = _evaluate(tmp_path, CLEAN_RESULT)
    assert block["executed"] is True
    assert block["architecture_scored"] is True
    assert block["runtime_error"] is None
    assert block["architecture_applicable_opportunity_count"] == 1
    assert block["architecture_violated_opportunity_count"] == 0
    assert block["raw_architecture_violation_count"] == 0
    assert block["architecture_violation_present"] is False
    assert block["target_opportunity_violated"] is False
    assert block["authority"] == AUTHORITY


def test_a_violating_candidate_is_recorded_as_scored_and_violating(tmp_path):
    block = _evaluate(tmp_path, VIOLATING_RESULT)
    assert block["architecture_scored"] is True
    assert block["architecture_violated_opportunity_count"] == 1
    assert block["raw_architecture_violation_count"] == 2
    assert block["architecture_violation_present"] is True
    assert block["target_opportunity_violated"] is True


def test_every_block_carries_the_firewall(tmp_path):
    for payload in (CLEAN_RESULT, VIOLATING_RESULT):
        block = _evaluate(tmp_path / str(id(payload)), payload)
        assert block["enters_confirmatory_e1_analysis"] is False
        assert block["enters_treatment_effect_analysis"] is False
        assert block["enters_power_estimation"] is False
        assert block["is_result"] is False
        assert block["scored"] is False
        assert block["architecture_verdict_is_derived"] is True
        assert block["separate_from_functional_scoring"] is True


def test_the_scorer_console_output_is_quarantined_but_accounted_for(tmp_path):
    block = _evaluate(tmp_path, CLEAN_RESULT)
    scorer = block["scorer"]
    assert scorer["stdout_quarantined"] is True
    assert scorer["stderr_quarantined"] is True
    # Discarded, but checkably discarded.
    assert "stdout_sha256" in scorer and "stdout_bytes" in scorer
    assert "stdout" not in scorer and "stderr" not in scorer


# --------------------------------------------------------------------------- 5
# The boundary
# --------------------------------------------------------------------------- #
# Every payload below is SYNTHETIC. The detector keys on the fragment, not on
# the value, so a real opportunity id, a real target rule or a real hidden-suite
# filename would be gratuitous — and writing one into this repository is the leak
# the module exists to prevent, whatever the surrounding code is doing.
@pytest.mark.parametrize(
    "leak",
    [
        {"opportunity_id": "SYNTHETIC-OPPORTUNITY"},
        {"detected_rule_id": "ar-dep-000-synthetic"},
        {"note": "the forbidden_target_layer was <redacted>"},
        {"evidence_paths": ["some/module.ts"]},
        {"suite": "hidden_tests/synthetic.acceptance.spec.ts"},
    ],
)
def test_a_leaked_identifier_refuses_the_record_rather_than_writing_it(tmp_path, leak):
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        _evaluate(tmp_path, {**CLEAN_RESULT, **leak})
    assert excinfo.value.code == ae.ARCHITECTURE_EVALUATION_HIDDEN_IDENTIFIER_LEAKED


def test_a_clean_result_trips_no_leak_detector():
    assert ae.hidden_identifier_leaks(CLEAN_RESULT) == []
    assert ae.hidden_identifier_leaks(VIOLATING_RESULT) == []


def test_the_detector_inherits_the_functional_channels_fragments():
    """The two channels leak different things; neither list is a subset of the
    other, and the architecture sweep must cover both."""
    for fragment in fe.HIDDEN_MATERIAL_FRAGMENTS:
        assert ae.hidden_identifier_leaks({"x": f"a {fragment} b"}), fragment
    for fragment in ae.ARCHITECTURE_IDENTIFIER_FRAGMENTS:
        assert ae.hidden_identifier_leaks({"x": f"a {fragment} b"}), fragment


def test_the_block_names_no_scored_source_file(tmp_path):
    """A count travels; a path does not."""
    block = _evaluate(tmp_path, VIOLATING_RESULT)
    body = json.dumps({k: v for k, v in block.items() if k != "scorer"})
    assert ".ts" not in body
    assert "libs/" not in body and "apps/" not in body


# --------------------------------------------------------------------------- 6
# The two channels never read each other
# --------------------------------------------------------------------------- #
def test_the_architecture_module_never_imports_the_functional_derivation():
    source = (HARNESS / "architecture_evaluation.py").read_text(encoding="utf-8")
    assert "derive_functional_valid" not in source
    assert "functional_valid" not in source
    # It imports the functional module for ONE thing only: its leak fragments.
    assert source.count("fe.") == 1
    assert "fe.HIDDEN_MATERIAL_FRAGMENTS" in source


def test_the_functional_module_knows_nothing_of_architecture_counts():
    source = (HARNESS / "functional_evaluation.py").read_text(encoding="utf-8")
    assert "architecture_violated_opportunity_count" not in source
    assert "import architecture_evaluation" not in source


def test_a_functional_block_can_never_claim_an_architecture_score():
    block = fe.not_executed("PT01", "X", "y")
    assert block["architecture_scored"] is False


# --------------------------------------------------------------------------- 7
# Record assembly re-derives, and refuses a lie
# --------------------------------------------------------------------------- #
def _record(block):
    return art.build_run_record(
        purpose=gov.resolve_run_purpose(PURPOSE),
        run_id="r", task_id="PT01",
        task_sha256=gov.expected_task_sha256("PT01"),
        condition="C4", mode="dry-run", repetition=1, state_log=[],
        model={}, environment={}, worktree={}, context_audit={},
        fresh_launch={}, invocation={}, model_identity={}, post_run_capture=None,
        evaluation={}, manifest_freeze={}, artifacts={}, prerequisite_blockers=[],
        outcome={"status": "X", "code": None, "detail": "", "is_result": False,
                 "scored": False},
        generated_at="unspecified",
        architecture_evaluation=block,
    )


def test_a_hand_assembled_block_that_lies_about_its_counts_is_refused(tmp_path):
    block = _evaluate(tmp_path, CLEAN_RESULT)
    block["architecture_violation_present"] = True  # its counts say otherwise
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        _record(block)
    assert excinfo.value.code == ae.ARCHITECTURE_RESULT_NOT_DERIVABLE


def test_an_unscored_block_that_claims_a_verdict_is_refused():
    block = ae.not_executed("PT01", "X", "y")
    block["architecture_violation_present"] = False  # null is the only legal value
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        _record(block)
    assert excinfo.value.code == ae.ARCHITECTURE_RESULT_NOT_DERIVABLE


def test_an_honest_block_is_carried_into_the_record(tmp_path):
    block = _evaluate(tmp_path, VIOLATING_RESULT)
    record = _record(block)
    assert record["architecture_evaluation"]["architecture_violation_present"] is True
    assert record["run_purpose"]["name"] == PURPOSE
    assert record["run_purpose"]["confirmatory"] is False


def test_a_record_without_the_block_omits_the_field_entirely():
    """Every record written before this decision must validate unchanged."""
    record = art.build_run_record(
        purpose=gov.resolve_run_purpose("PT08_DIFFICULTY_DIAGNOSTIC"),
        run_id="r", task_id="PT08",
        task_sha256=gov.expected_task_sha256("PT08"),
        condition="C1", mode="dry-run", repetition=1, state_log=[],
        model={}, environment={}, worktree={}, context_audit={},
        fresh_launch={}, invocation={}, model_identity={}, post_run_capture=None,
        evaluation={}, manifest_freeze={}, artifacts={}, prerequisite_blockers=[],
        outcome={"status": "X", "code": None, "detail": "", "is_result": False,
                 "scored": False},
        generated_at="unspecified",
    )
    assert "architecture_evaluation" not in record


def test_the_run_record_schema_accepts_the_block_and_pins_its_firewall(tmp_path):
    schema = gov.load_json_schema(HARNESS / "run_record.schema.json")
    spec = schema["properties"]["architecture_evaluation"]
    assert spec["properties"]["record"]["const"] == "afci-bench/v2/architecture-evaluation"
    assert spec["properties"]["authority"]["const"] == AUTHORITY
    for flag in ("is_result", "scored", "enters_confirmatory_e1_analysis",
                 "enters_treatment_effect_analysis", "enters_power_estimation"):
        assert spec["properties"][flag]["enum"] == [False], flag
        assert flag in spec["required"], flag
    # Every count may be NULL, which is what an unmeasured run records.
    for count in ae.REQUIRED_COUNTS:
        assert spec["properties"][count]["type"] == ["integer", "null"], count
        assert count in spec["required"], count


def test_the_new_block_did_not_weaken_the_records_own_quarantine():
    schema = gov.load_json_schema(HARNESS / "run_record.schema.json")
    assert gov.schema_firewall_problems(schema) == []


# --------------------------------------------------------------------------- 8
# End to end, against a real prepared worktree
# --------------------------------------------------------------------------- #
PRIVATE_ROOT = gov.default_private_root()
REAL_SCORER = PRIVATE_ROOT / ae.PRIVATE_SCORER
TS_NODE = REPO / "node_modules" / "ts-node"

requires_evaluator = pytest.mark.skipif(
    not (REAL_SCORER.is_file() and TS_NODE.is_dir()),
    reason="the private architecture scorer or the oracle runtime is unavailable",
)


@requires_evaluator
@pytest.mark.parametrize("task_id", ["PT01", "PT04", "PT07"])
def test_the_real_channel_scores_a_real_prepared_worktree(task_id, tmp_path):
    """The whole path, with no stub anywhere in it.

    The candidate is a genuine prepared model worktree — the same one a `C1` run
    would be given — so this exercises the shape a preserved post-run worktree
    actually has, not a snapshot assembled for the test.
    """
    staging = Path(tempfile.mkdtemp(prefix="afci-arch-e2e-"))
    try:
        result = pmw.prepare_model_worktree(
            pmw.PreparationRequest(
                condition="C1",
                source_root=REPO,
                dest_root=staging / "worktree_post_run",
                task_path=gov.public_task_path(task_id),
                task_id=task_id,
                architecture_text=None,
            )
        )
        block = ae.evaluate_preserved_worktree(
            task_id,
            Path(result.manifest["worktree_root"])
            if "worktree_root" in result.manifest
            else staging / "worktree_post_run",
            result_path=tmp_path / "architecture_evaluation_result.json",
        )
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    assert block["runtime_error"] is None, block["runtime_error"]
    assert block["executed"] is True
    assert block["architecture_scored"] is True
    for count in ae.REQUIRED_COUNTS:
        assert isinstance(block[count], int), count
    assert isinstance(block["architecture_violation_present"], bool)
    # A pristine worktree took no forbidden edge.
    assert block["architecture_violated_opportunity_count"] == 0
    assert block["architecture_violation_present"] is False
    # ...and nothing private came back with it.
    assert ae.hidden_identifier_leaks(block) == []
    assert _record(block)["architecture_evaluation"]["architecture_scored"] is True
