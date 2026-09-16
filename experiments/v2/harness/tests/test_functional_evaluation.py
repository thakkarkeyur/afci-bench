"""``SL-V2-EFF-FUNC-01``: the post-run functional-validity channel.

What is asserted here, and what deliberately is not
---------------------------------------------------
**Asserted:** that ``FUNCTIONAL_VALID`` is derived from the semantic counts and
cannot be supplied; that a non-semantic failure is recorded, reported and does
not flip the verdict; that every failure mode is written into the record as a
coded error rather than silently omitted; that the run record's schema gained
the block *optionally*, so every record written before it stays valid; that
``POST_RUN_EVALUATION`` invokes the private scorer only after a finished process
and a captured worktree; and that no hidden evaluator material can reach a run
record.

**Not asserted:** any hidden acceptance semantics. This module authors no
fixture, names no acceptance case identifier, and reads no hidden test. The
suites, their cases and their assertions live in the private evaluator
repository, where their own validation exercises them against real candidates.

No model is invoked.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

import functional_evaluation as fe
import run_artifacts as art
import run_evaluation as ev
import run_governance as gov
import run_v2

REPO = Path(__file__).resolve().parents[4]
DECISION = REPO / "docs" / "v2" / "AFCI_EFFICIENCY_PILOT_FUNCTIONAL_VALIDITY_DECISION.md"
PILOT_DECISION = REPO / "docs" / "v2" / "AFCI_EFFICIENCY_PILOT_DECISION.md"
PURPOSE = "AFCI_EFFICIENCY_PILOT"


def _counts(**overrides) -> dict:
    """A complete, VALID semantic tally, so each test perturbs exactly one thing."""
    block = {
        "executed": True,
        "semantic_case_count_expected": 4,
        "semantic_case_count_executed": 4,
        "semantic_pass_count": 4,
        "semantic_fail_count": 0,
        "semantic_error_count": 0,
        "nonsemantic_case_count_expected": 3,
        "nonsemantic_case_count_executed": 3,
        "nonsemantic_pass_count": 3,
        "nonsemantic_fail_count": 0,
        "nonsemantic_error_count": 0,
        "missing_case_ids": [],
        "missing_semantic_case_ids": [],
        "duplicate_case_ids": [],
        "runtime_error": None,
    }
    block.update(overrides)
    return block


# --------------------------------------------------------------------------- 1
# The derivation


def test_a_complete_semantic_pass_is_the_only_valid_shape():
    assert fe.derive_functional_valid(_counts()) is True


@pytest.mark.parametrize(
    "overrides",
    [
        {"semantic_case_count_executed": 3},
        {"semantic_pass_count": 3},
        {"semantic_fail_count": 1},
        {"semantic_error_count": 1},
        {"missing_semantic_case_ids": ["<one declared case>"]},
        {"runtime_error": {"code": "X", "detail": "y"}},
        {"semantic_case_count_expected": 0, "semantic_case_count_executed": 0,
         "semantic_pass_count": 0},
    ],
    ids=[
        "a case did not execute",
        "a case did not pass",
        "a case failed",
        "a case errored",
        "a case is missing",
        "the evaluation errored",
        "no semantic case is declared at all",
    ],
)
def test_every_clause_of_the_derivation_is_load_bearing(overrides):
    assert fe.derive_functional_valid(_counts(**overrides)) is False


@pytest.mark.parametrize(
    "overrides",
    [
        {"nonsemantic_fail_count": 3, "nonsemantic_pass_count": 0},
        {"nonsemantic_error_count": 1, "nonsemantic_pass_count": 2},
        {"nonsemantic_case_count_executed": 0, "nonsemantic_pass_count": 0},
    ],
    ids=["every restraint case failed", "a restraint case errored",
         "no restraint case executed"],
)
def test_no_non_semantic_count_can_flip_the_verdict(overrides):
    """§2.1: non-semantic cases are recorded and reported, and decide nothing."""
    assert fe.derive_functional_valid(_counts(**overrides)) is True


def test_the_semantic_pass_non_semantic_fail_shape_is_valid_and_still_visible():
    """The shape no candidate worktree can produce, checked where it can be.

    A restraint case issues NO request, so no candidate worktree can make one
    fail — which is exactly why it may not decide validity. The combination is
    therefore exercised at the layer that would have to handle it: a run in which
    every semantic case passed and a non-semantic case did not is VALID, and the
    non-semantic failure is still there to be read.
    """
    block = _counts(nonsemantic_pass_count=2, nonsemantic_fail_count=1)
    assert fe.derive_functional_valid(block) is True
    assert block["nonsemantic_fail_count"] == 1


def test_the_derivation_takes_no_verdict_as_input():
    """A supplied verdict is not a parameter; it is not even reachable."""
    import inspect

    parameters = list(inspect.signature(fe.derive_functional_valid).parameters)
    assert parameters == ["counts"]
    # and supplying one inside the counts changes nothing
    assert fe.derive_functional_valid(_counts(functional_valid=False)) is True
    assert fe.derive_functional_valid(
        _counts(semantic_fail_count=1, functional_valid=True)
    ) is False


@pytest.mark.parametrize(
    "bad", [None, "4", 4.0, True, -1], ids=["null", "string", "float", "bool", "negative"]
)
def test_a_count_that_is_not_a_whole_number_fails_closed(bad):
    with pytest.raises(gov.RunnerRefusal) as exc:
        fe.derive_functional_valid(_counts(semantic_pass_count=bad))
    assert exc.value.code == fe.FUNCTIONAL_EVALUATOR_MALFORMED_RESULT


# --------------------------------------------------------------------------- 2
# Folding a private result into the block


def _result(**overrides) -> dict:
    result = {
        "record": "afci-bench/v2/functional-evaluation",
        "schema_version": "1.0.0",
        "executed": True,
        "evaluator_task": "PT07",
        "evaluator_version": "1.0.0",
        "evaluator_runtime_sha256": "0" * 64,
        "evaluator_suite_sha256": "1" * 64,
        "functional_valid": True,
    }
    result.update(_counts())
    result.update(overrides)
    return result


def _fold(result: dict, task: str = "PT07") -> dict:
    return fe._block_from_result(task, result, {"exit_status": 0})


def test_a_scored_result_becomes_a_block_whose_verdict_is_re_derived():
    block = _fold(_result())
    assert block["functional_valid"] is True
    assert block["executed"] is True
    assert block["functional_valid_is_derived"] is True
    assert block["authority"] == "SL-V2-EFF-FUNC-01"


def test_a_scorer_verdict_that_disagrees_with_its_own_counts_records_neither():
    block = _fold(_result(functional_valid=True, semantic_pass_count=3,
                          semantic_fail_count=1))
    assert block["functional_valid"] is False
    assert block["runtime_error"]["code"] == fe.FUNCTIONAL_VALID_NOT_DERIVABLE


def test_a_result_for_another_task_is_never_re_attributed():
    block = _fold(_result(evaluator_task="PT01"))
    assert block["functional_valid"] is False
    assert block["runtime_error"]["code"] == fe.FUNCTIONAL_EVALUATOR_MALFORMED_RESULT


def test_a_result_missing_a_count_fails_closed():
    result = _result()
    del result["semantic_pass_count"]
    block = _fold(result)
    assert block["functional_valid"] is False
    assert block["runtime_error"]["code"] == fe.FUNCTIONAL_EVALUATOR_MALFORMED_RESULT


def test_a_result_claiming_both_an_error_and_a_pass_records_neither():
    block = _fold(_result(runtime_error={"code": "X", "detail": "y"},
                          functional_valid=False))
    assert block["functional_valid"] is False


def test_an_unexecuted_result_is_never_valid():
    block = _fold(_result(executed=False))
    assert block["functional_valid"] is False


# --------------------------------------------------------------------------- 3
# The private invocation boundary


def test_an_absent_worktree_is_recorded_rather_than_guessed(tmp_path):
    block = fe.evaluate_preserved_worktree(
        "PT01", None, result_path=tmp_path / "r.json"
    )
    assert block["executed"] is False
    assert block["functional_valid"] is False
    assert block["runtime_error"]["code"] == fe.FUNCTIONAL_EVALUATION_NO_WORKTREE


def test_an_absent_private_scorer_is_recorded_rather_than_substituted(tmp_path):
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    block = fe.evaluate_preserved_worktree(
        "PT01", candidate,
        result_path=tmp_path / "r.json",
        private_root=tmp_path / "no-such-private-root",
    )
    assert block["runtime_error"]["code"] == fe.FUNCTIONAL_EVALUATOR_UNAVAILABLE
    assert block["functional_valid"] is False


def _stub_private_root(tmp_path: Path, body: str) -> Path:
    root = tmp_path / "stub-private"
    (root / "scripts").mkdir(parents=True)
    (root / "scripts" / "score_worktree.py").write_text(
        body, encoding="utf-8", newline="\n"
    )
    return root


STUB_EMITS = """
import argparse, json, sys
p = argparse.ArgumentParser()
p.add_argument("--task"); p.add_argument("--worktree"); p.add_argument("--out")
a = p.parse_args()
open(a.out, "w", encoding="utf-8").write(json.dumps(%s))
sys.exit(%s)
"""


def test_a_scorer_that_writes_no_result_fails_closed(tmp_path):
    root = _stub_private_root(tmp_path, "import sys\nsys.exit(3)\n")
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    block = fe.evaluate_preserved_worktree(
        "PT01", candidate, result_path=tmp_path / "r.json", private_root=root
    )
    assert block["runtime_error"]["code"] == fe.FUNCTIONAL_EVALUATOR_NO_RESULT
    assert block["functional_valid"] is False
    assert block["scorer"]["exit_status"] == 3


def test_a_scorer_that_writes_unparseable_output_fails_closed(tmp_path):
    root = _stub_private_root(
        tmp_path,
        "import argparse\n"
        "p = argparse.ArgumentParser()\n"
        "p.add_argument('--task'); p.add_argument('--worktree'); p.add_argument('--out')\n"
        "a = p.parse_args()\n"
        "open(a.out, 'w', encoding='utf-8').write('{not json')\n",
    )
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    block = fe.evaluate_preserved_worktree(
        "PT01", candidate, result_path=tmp_path / "r.json", private_root=root
    )
    assert block["runtime_error"]["code"] == fe.FUNCTIONAL_EVALUATOR_MALFORMED_RESULT


def test_a_scorer_that_hangs_is_an_error_and_never_a_failing_candidate(tmp_path):
    root = _stub_private_root(tmp_path, "import time\ntime.sleep(30)\n")
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    block = fe.evaluate_preserved_worktree(
        "PT01", candidate, result_path=tmp_path / "r.json",
        private_root=root, timeout_seconds=2,
    )
    assert block["runtime_error"]["code"] == fe.FUNCTIONAL_EVALUATOR_TIMEOUT
    assert block["scorer"]["timed_out"] is True
    assert block["functional_valid"] is False


def test_a_scorer_result_naming_hidden_material_is_refused_not_recorded(tmp_path):
    leaking = dict(_result(evaluator_task="PT01"))
    leaking["detail"] = "failed in tasks/PT01/hidden_tests/some.acceptance.spec.ts"
    root = _stub_private_root(tmp_path, STUB_EMITS % (repr(leaking), 0))
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    with pytest.raises(gov.RunnerRefusal) as exc:
        fe.evaluate_preserved_worktree(
            "PT01", candidate, result_path=tmp_path / "r.json", private_root=root
        )
    assert exc.value.code == fe.FUNCTIONAL_EVALUATION_HIDDEN_PATH_LEAKED


def test_the_leak_sweep_actually_detects_each_fragment_it_names():
    """Guard the guard: an inert sweep would pass every leak silently."""
    for fragment in fe.HIDDEN_MATERIAL_FRAGMENTS:
        assert fe.hidden_material_leaks({"a": [f"x/{fragment}/y"]}) == [fragment]
    assert fe.hidden_material_leaks(_result()) == []


def test_a_clean_scorer_result_produces_a_block_with_no_hidden_material(tmp_path):
    root = _stub_private_root(
        tmp_path, STUB_EMITS % (repr(_result(evaluator_task="PT01")), 0)
    )
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    block = fe.evaluate_preserved_worktree(
        "PT01", candidate, result_path=tmp_path / "r.json", private_root=root
    )
    assert block["functional_valid"] is True
    assert fe.hidden_material_leaks(block) == []
    assert block["scorer"]["stdout_quarantined"] is True
    assert block["scorer"]["stderr_quarantined"] is True
    # the console output is measured and digested, never carried
    assert "stdout" not in block["scorer"] and "stderr" not in block["scorer"]


# --------------------------------------------------------------------------- 4
# POST_RUN_EVALUATION actually invokes it


class _Capture:
    def __init__(self, root: Path) -> None:
        self.capture_root = str(root)


class _Invocation:
    def __init__(self, invoked: bool) -> None:
        self.invoked = invoked


class _Directory:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.written = {}

    def path(self, name: str) -> Path:
        return self.root / name

    def write_json(self, name: str, payload) -> Path:
        self.written[name] = payload
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload), encoding="utf-8", newline="\n")
        return target


def _block(tmp_path, *, purpose_name, invoked, capture, private_root=None):
    purpose = gov.resolve_run_purpose(purpose_name)
    request = run_v2.RunRequest(
        task_id="PT01", condition="C1", run_purpose=purpose_name,
        private_root=private_root, functional_evaluation_timeout_seconds=30,
    )
    return run_v2._functional_evaluation_block(
        purpose=purpose,
        request=request,
        invocation=_Invocation(invoked),
        capture=capture,
        directory=_Directory(tmp_path),
    )


def test_a_purpose_with_no_functional_authority_gets_no_block(tmp_path):
    """Every earlier purpose's record is unchanged: no block, not an empty one."""
    assert _block(
        tmp_path, purpose_name="PT08_DIFFICULTY_DIAGNOSTIC", invoked=False, capture=None
    ) is None
    assert gov.resolve_run_purpose(
        "PT08_DIFFICULTY_DIAGNOSTIC"
    ).functional_evaluation_authority is None
    assert gov.resolve_run_purpose(
        "INSTRUMENT_QUALIFICATION_DIAGNOSTIC"
    ).functional_evaluation_authority is None


def test_the_pilot_purpose_carries_the_authority_and_produces_no_architecture():
    purpose = gov.resolve_run_purpose(PURPOSE)
    assert purpose.functional_evaluation_authority == "SL-V2-EFF-FUNC-01"
    assert purpose.produces_architecture_result is False
    for name, other in gov.RUN_PURPOSES.items():
        if name != PURPOSE:
            assert other.produces_architecture_result is True, name


def test_no_finished_process_means_no_score_and_no_inference(tmp_path):
    block = _block(tmp_path, purpose_name=PURPOSE, invoked=False, capture=None)
    assert block["runtime_error"]["code"] == fe.FUNCTIONAL_EVALUATION_NO_WORKTREE
    assert block["functional_valid"] is False


def test_a_finished_process_without_a_capture_is_not_scored(tmp_path):
    block = _block(tmp_path, purpose_name=PURPOSE, invoked=True, capture=None)
    assert block["runtime_error"]["code"] == fe.FUNCTIONAL_EVALUATION_NO_WORKTREE


def test_a_finished_process_with_a_capture_really_invokes_the_scorer(tmp_path):
    """The point of Part F: the runner RUNS the scorer, it does not plan one.

    Proved by a stub scorer that records the arguments it was handed: the run
    must reach it, and it must be handed the PRESERVED capture rather than the
    live coding worktree.
    """
    marker = tmp_path / "invoked.json"
    root = _stub_private_root(
        tmp_path,
        "import argparse, json, sys\n"
        "p = argparse.ArgumentParser()\n"
        "p.add_argument('--task'); p.add_argument('--worktree'); p.add_argument('--out')\n"
        "a = p.parse_args()\n"
        f"open({str(marker)!r}, 'w', encoding='utf-8').write("
        "json.dumps({'task': a.task, 'worktree': a.worktree}))\n"
        "open(a.out, 'w', encoding='utf-8').write(json.dumps("
        f"{_result(evaluator_task='PT01')!r}))\n",
    )
    capture_root = tmp_path / "worktree_post_run"
    capture_root.mkdir()
    block = _block(
        tmp_path, purpose_name=PURPOSE, invoked=True,
        capture=_Capture(capture_root), private_root=root,
    )
    handed = json.loads(marker.read_text(encoding="utf-8"))
    assert handed["task"] == "PT01"
    assert Path(handed["worktree"]) == capture_root.resolve()
    assert block["functional_valid"] is True
    assert (tmp_path / "functional_evaluation.json").is_file()


# --------------------------------------------------------------------------- 5
# The record schema


SCHEMA = json.loads(
    (Path(art.SCHEMA_PATH)).read_text(encoding="utf-8")
)


def test_the_block_is_optional_so_older_records_stay_valid():
    assert "functional_evaluation" in SCHEMA["properties"]
    assert "functional_evaluation" not in SCHEMA["required"]
    assert SCHEMA["additionalProperties"] is False


def test_the_schema_pins_the_quarantine_the_block_carries():
    block = SCHEMA["properties"]["functional_evaluation"]
    assert block["properties"]["architecture_scored"]["const"] is False
    assert block["properties"]["authority"]["const"] == "SL-V2-EFF-FUNC-01"
    assert block["properties"]["functional_valid_is_derived"]["const"] is True
    assert (
        block["properties"]["nonsemantic_cases_do_not_determine_validity"]["const"]
        is True
    )
    for field in fe.REQUIRED_COUNTS:
        assert field in block["required"], field
        assert block["properties"][field]["minimum"] == 0


def _record(purpose_name=PURPOSE, **kwargs):
    purpose = gov.resolve_run_purpose(purpose_name)
    return art.build_run_record(
        purpose=purpose,
        run_id="r", task_id="PT01", task_sha256="a" * 64, condition="C1",
        mode="dry-run", state_log=[],
        model={
            "requested_model_id": None, "resolved_model_id": None,
            "effort_input": None, "selection_status": gov.MODEL_SELECTION_REQUIRED,
        },
        environment=art.environment_block(),
        worktree={
            "enforcement": {}, "prepared_root": "", "prepared_manifest_path": "",
            "content_hash": "",
        },
        context_audit={
            "verdict": "UNKNOWN", "report_path": "", "report_sha256": "",
            "reason_count": 0,
        },
        fresh_launch={
            "argv": [], "executable": False, "session_handling": "not built",
            "manifest_path": None,
        },
        invocation={
            "invoked": False, "status": "NOT_REACHED", "exit_status": None,
            "runtime_evidence_path": None,
        },
        model_identity={
            "status": "NOT_PERFORMED", "requested_model_id": None,
            "resolved_model_id": None,
        },
        post_run_capture=None, evaluation={}, manifest_freeze={}, artifacts={},
        prerequisite_blockers=[],
        outcome={
            "status": "DRY_RUN_COMPLETE", "code": None, "detail": "",
            "is_result": False, "scored": False,
        },
        **kwargs,
    )


def test_a_record_without_the_block_omits_it_entirely_and_validates():
    record = _record()
    assert "functional_evaluation" not in record
    art.validate_run_record(record, SCHEMA)


def test_a_record_with_the_block_validates():
    record = _record(functional_evaluation=_fold(_result(evaluator_task="PT01"), "PT01"))
    art.validate_run_record(record, SCHEMA)
    assert record["functional_evaluation"]["functional_valid"] is True


def test_a_hand_edited_verdict_cannot_be_written_into_a_record():
    """The derivation is a property of the RECORD, not only of the module."""
    block = _fold(_result(evaluator_task="PT01"), "PT01")
    block["functional_valid"] = False  # a hand edit, in either direction
    with pytest.raises(gov.RunnerRefusal) as exc:
        _record(functional_evaluation=block)
    assert exc.value.code == fe.FUNCTIONAL_VALID_NOT_DERIVABLE

    block = fe.not_executed("PT01", "X", "y")
    block["functional_valid"] = True
    with pytest.raises(gov.RunnerRefusal) as exc:
        _record(functional_evaluation=block)
    assert exc.value.code == fe.FUNCTIONAL_VALID_NOT_DERIVABLE


def test_the_firewall_is_still_derived_from_the_purpose_beside_the_new_block():
    record = _record(functional_evaluation=_fold(_result(evaluator_task="PT01"), "PT01"))
    for flag in gov.FIREWALL_FIELDS:
        assert record["run_purpose"][flag] is False
    assert record["outcome"]["is_result"] is False
    assert record["outcome"]["scored"] is False


# --------------------------------------------------------------------------- 6
# Architecture reporting consistency


def test_the_pilot_reports_architecture_as_not_produced_rather_than_blocked():
    channel = ev.architecture_scoring_channel(
        "PT01", condition="C1", run_purpose=PURPOSE
    )
    assert channel.status == ev.NOT_PRODUCED
    assert channel.code == ev.ARCHITECTURE_NOT_PRODUCED_BY_THIS_PURPOSE
    assert channel.not_produced is True
    assert channel.ready is False
    assert channel.command is None, "no architecture command is built or offered"


def test_a_not_produced_channel_is_not_an_outstanding_blocker():
    plan = ev.build_evaluation_plan("PT01", condition="C1", run_purpose=PURPOSE)
    assert [c.channel for c in plan.not_produced] == [
        "architecture_opportunity_scoring"
    ]
    assert plan.blockers == []
    assert plan.to_dict()["channels_not_produced"] == [
        "architecture_opportunity_scoring"
    ]


def test_every_other_purpose_still_gets_the_suite_wide_architecture_answer():
    """The correction is scoped to the cost-only purpose and to nothing else."""
    for purpose_name in ("PT08_DIFFICULTY_DIAGNOSTIC",
                         "INSTRUMENT_QUALIFICATION_DIAGNOSTIC"):
        purpose = gov.resolve_run_purpose(purpose_name)
        task = purpose.permitted_tasks[0]
        channel = ev.architecture_scoring_channel(
            task, condition=purpose.permitted_conditions[0], run_purpose=purpose_name
        )
        assert channel.status != ev.NOT_PRODUCED
    # and a caller supplying no purpose at all still gets the fail-closed answer
    assert ev.architecture_scoring_channel("PT01").status == "BLOCKED"


# --------------------------------------------------------------------------- 7
# The decision record


def _flat(path: Path) -> str:
    import re

    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))


def test_the_decision_record_states_the_definition_and_the_exclusion():
    text = _flat(DECISION)
    assert "SL-V2-EFF-FUNC-01" in text
    assert "validated hidden runtime" in text
    assert "preserved candidate worktree" in text
    assert "missing, unexecuted, indeterminate or errored" in text
    assert "determines `FUNCTIONAL_VALID` | **no**" in text
    assert "enters the paired-functional-valid eligibility gate | **no**" in text
    assert "record.functional_evaluation.functional_valid" in text


def test_the_decision_record_publishes_counts_and_not_case_identifiers():
    """The identities stay private, exactly as PT08's guard case's does."""
    import re

    text = DECISION.read_text(encoding="utf-8")
    assert "| `PT01` | 4 | 0 |" in text
    assert "| `PT04` | 4 | 0 |" in text
    assert "| `PT07` | 4 | 3 |" in text
    assert not re.search(r"PT\d{2}-AC-\d{2}", text), (
        "a hidden acceptance case identifier must not be published"
    )


def test_no_public_file_names_a_hidden_acceptance_case_identifier():
    """The whole public tree, not only the record this package wrote."""
    import re

    pattern = re.compile(r"\bPT\d{2}-AC-\d{2}\b")
    skip = {"node_modules", ".git", "__pycache__", ".nx", ".pytest_cache",
            "archive", "dist", "coverage"}
    offenders = []
    for path in REPO.rglob("*"):
        if not path.is_file() or skip & set(path.relative_to(REPO).parts):
            continue
        if path.suffix not in {".md", ".csv", ".json", ".yml", ".yaml", ".py", ".ts"}:
            continue
        if path == Path(__file__):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if pattern.search(text):
            offenders.append(path.relative_to(REPO).as_posix())
    assert not offenders, f"hidden acceptance case identifiers published: {offenders}"


def test_the_decision_record_changes_no_frozen_science():
    text = _flat(DECISION)
    for row in (
        "any hidden acceptance assertion | **UNCHANGED**",
        "the set of hidden acceptance cases | **UNCHANGED**",
        "the MAD | **UNCHANGED**, byte-identical",
        "reset checkpoints and the 32/32/64 budgets | **UNCHANGED**",
        "the permission allowlist | **UNCHANGED**",
        "token, time and tool metric definitions | **UNCHANGED**",
        "§11 continuation thresholds | **UNCHANGED**",
        "model and runtime configuration | **UNCHANGED**",
        "architecture scoring | **NOT ENABLED**",
        "confirmatory `E1` | **NOT RE-ENABLED**",
    ):
        assert row in text, row


def test_the_decision_record_leaves_every_gate_where_it_found_it():
    text = _flat(DECISION)
    for row in (
        "gate `G1` | **NOT PASSED**",
        "gate `G2` | **NOT PASSED**",
        "`TD-B32` (global) | **OPEN**",
        "`TD-B34` | **OPEN**",
        "`TD-B39` | **OPEN**",
        "`TD-B42` | **OPEN**",
        "`TD-B01` / `TD-B11` | **OPEN**",
        "`TD-B12` / `G6` | **OPEN**",
        "`TD-B03` | **OPEN**",
        "suite freeze | **false**",
        "independent review | **NOT OBTAINED AND NOT CLAIMED**",
    ):
        assert row in text, row


def test_the_decision_is_recorded_before_any_observation_exists():
    """Mechanical, not prose: the pilot's own result and analysis areas are bare."""
    results = REPO / "experiments" / "v2" / "results"
    present = sorted(p.name for p in results.iterdir() if p.name != "README.md")
    assert present == [], f"an efficiency observation exists: {present}"
    assert "ZERO" in _flat(DECISION)


def test_the_pilot_decision_still_carries_the_phrase_this_record_defines():
    """If §10.1/§11.0 were reworded, this definition would be defining nothing."""
    text = _flat(PILOT_DECISION)
    assert "A pair is **eligible** only if **both** of its runs are functionally valid" in text
    assert "At least 12 of the 18 blocks must have both conditions functionally valid" in text


def test_the_runner_names_the_private_scorer_and_vendors_no_acceptance_logic():
    assert fe.PRIVATE_SCORER == "scripts/score_worktree.py"
    source = (
        REPO / "experiments" / "v2" / "harness" / "functional_evaluation.py"
    ).read_text(encoding="utf-8")
    for forbidden in ("supertest", "describe(", "expect(", "toEqual", "jest"):
        assert forbidden not in source, (
            f"{forbidden!r} in the public channel would be acceptance logic"
        )


@pytest.mark.skipif(
    not (REPO.parent / "afci-bench-evaluator-private" / "scripts").is_dir(),
    reason="private evaluator repository not present",
)
def test_the_private_scorer_this_runner_calls_actually_exists():
    scorer = fe.scorer_path()
    assert scorer.is_file(), f"the named private entry point is missing: {scorer}"
    done = subprocess.run(
        [sys.executable, str(scorer), "--help"], capture_output=True, text=True
    )
    assert done.returncode == 0
    assert "--worktree" in done.stdout and "--out" in done.stdout
