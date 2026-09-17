"""The frozen 18-run `AFCI_LOWER_MODEL_PILOT` schedule, and its preflight.

What this file pins:

  * 9 paired blocks, 18 runs, one `C1` and one `C4` per block, one arm;
  * the schedule is a pure function of a recorded seed and uses no language RNG,
    so it is reproducible on another machine and another Python;
  * the committed artifacts hash to what this module builds;
  * all 18 run ids and all 18 artifact directories are distinct;
  * NONE of them coincides with anything the claude-sonnet-5 efficiency pilot
    minted, across BOTH of its executions;
  * the preflight refuses a whole execution on any single defect, rather than
    discovering it at row 9 by executing into it;
  * nothing has been executed.

No model is invoked, nothing is written outside pytest's temporary directory.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[4]
HARNESS = REPO / "experiments" / "v2" / "harness"
sys.path.insert(0, str(HARNESS))

import execution_attempt as ea  # noqa: E402
import lower_model_run_plan as lmp  # noqa: E402
import reset_budget as rb  # noqa: E402
import run_artifacts as art  # noqa: E402
import run_governance as gov  # noqa: E402

PLAN_PATH = REPO / lmp.RUN_PLAN_PATH
EXECUTION_PATH = REPO / lmp.EXECUTION_PLAN_PATH

#: The roots the execution plan commits to. Outside the operator profile, and a
#: NEW namespace: no efficiency-pilot artifact lives under either.
ARTIFACT_ROOT = Path(r"D:\afci-runs\lower-model-pilot")
STERILE_BASE = Path(r"D:\afci-sterile\lower-model-pilot")


@pytest.fixture(scope="module")
def plan():
    return lmp.load_plan(REPO)


@pytest.fixture(scope="module")
def execution():
    return lmp.load_execution_plan(REPO)


# --------------------------------------------------------------------------- 1
# Shape
# --------------------------------------------------------------------------- #
def test_the_committed_plan_validates(plan):
    assert lmp.plan_problems(plan, REPO) == []


def test_the_shape_is_nine_paired_blocks_of_two(plan):
    assert plan["block_count"] == 9
    assert plan["run_count"] == 18
    by_block = {}
    for run in plan["runs"]:
        by_block.setdefault(run["block_id"], []).append(run)
    assert len(by_block) == 9
    for bid, rows in by_block.items():
        assert sorted(r["condition"] for r in rows) == ["C1", "C4"], bid
        assert len({r["task_id"] for r in rows}) == 1, bid
        assert len({r["repetition"] for r in rows}) == 1, bid


def test_every_task_appears_in_three_blocks(plan):
    counts = {}
    for block in plan["blocks"]:
        counts[block["task_id"]] = counts.get(block["task_id"], 0) + 1
    assert counts == {"PT01": 3, "PT04": 3, "PT07": 3}


def test_the_matrix_is_balanced_across_both_arms_of_the_condition(plan):
    per_cell = {}
    for run in plan["runs"]:
        key = (run["task_id"], run["condition"])
        per_cell[key] = per_cell.get(key, 0) + 1
    assert set(per_cell.values()) == {3}
    assert len(per_cell) == 6


def test_there_is_exactly_one_reset_arm_and_every_row_carries_it(plan):
    assert plan["reset_states"] == [rb.NON_RESET]
    assert plan["reset_arm_authorised"] is False
    assert {r["reset_state"] for r in plan["runs"]} == {rb.NON_RESET}


def test_every_row_carries_the_same_frozen_ceiling(plan):
    assert {r["max_turns"] for r in plan["runs"]} == {64}


def test_the_plan_pins_the_registry_model_and_runtime(plan):
    assert plan["model_id"] == gov.diagnostic_primary_model(lmp.RUN_PURPOSE)
    assert plan["model_id"] == "claude-haiku-4-5-20251001"
    assert plan["runtime_version"] == gov.live_runtime_validation(lmp.RUN_PURPOSE)[2]


def test_the_plan_pins_the_approved_task_and_architecture_hashes(plan):
    for task in ("PT01", "PT04", "PT07"):
        assert plan["task_sha256"][task] == gov.expected_task_sha256(task)
    assert plan["architecture_context_sha256"] == gov.architecture_context_sha256(REPO)
    # The MAD hash the whole study is pinned to, restated so a drift is caught
    # here as well as by the run-time check.
    assert plan["architecture_context_sha256"] == (
        "bf6f32b162a23b851596d8b489d938bef10d0b8616a50dcc039873d12ffa7a4d"
    )


def test_the_plan_carries_the_firewall_and_both_channels(plan):
    assert plan["is_result"] is False
    assert plan["scored"] is False
    assert plan["enters_confirmatory_dataset"] is False
    assert plan["measures_architecture_quality"] is True
    assert plan["measures_efficiency"] is True
    assert plan["channels_combined_into_one_score"] is False
    assert plan["pools_with_sonnet_efficiency_pilot"] is False


# --------------------------------------------------------------------------- 2
# Determinism
# --------------------------------------------------------------------------- #
def test_the_committed_file_is_exactly_what_this_module_builds(plan):
    built = lmp.build_plan(lmp.SEED, REPO)
    assert lmp.serialise(built) == lmp.serialise(plan)
    on_disk = hashlib.sha256(PLAN_PATH.read_bytes()).hexdigest()
    assert on_disk == lmp.plan_sha256(built)


def test_the_schedule_is_a_pure_function_of_the_seed():
    first = lmp.build_plan(lmp.SEED, REPO)
    second = lmp.build_plan(lmp.SEED, REPO)
    assert lmp.serialise(first) == lmp.serialise(second)


def test_a_different_seed_produces_a_different_order():
    other = lmp.build_plan(lmp.SEED + "-x", REPO)
    assert lmp.projection_sha256(other) != lmp.projection_sha256(
        lmp.build_plan(lmp.SEED, REPO)
    )


def test_no_language_rng_is_used():
    """Checked against the CODE, not the prose.

    The module's own docstring explains why ``random.Random`` is not used, so a
    substring search over the whole file would flag the explanation. What must be
    absent is the import and the calls.
    """
    source = (HARNESS / "lower_model_run_plan.py").read_text(encoding="utf-8")
    code = [
        line for line in source.splitlines()
        if not line.lstrip().startswith("#")
    ]
    joined = "\n".join(code)
    assert not re.search(r"^\s*import\s+random\b", joined, re.MULTILINE)
    assert not re.search(r"^\s*from\s+random\s+import\b", joined, re.MULTILINE)
    assert "random.shuffle(" not in joined
    assert "random.Random(" not in joined
    assert "random.sample(" not in joined
    # ...and the ordering really is the documented one.
    assert "hashlib.sha256" in joined


def test_both_orders_are_actually_randomised(plan):
    """A schedule that merely LOOKED shuffled would satisfy every count above."""
    # Within blocks: C1 is not always first.
    firsts = {
        run["condition"] for run in plan["runs"] if run["position_in_block"] == 1
    }
    assert firsts == {"C1", "C4"}, firsts

    # Across blocks: the tasks are interleaved. The bar is exact rather than
    # arbitrary — three homogeneous stretches, which is what an UNSHUFFLED
    # schedule would produce, has exactly 2 task transitions — and no task's
    # blocks are contiguous.
    order = [run["task_id"] for run in plan["runs"]]
    transitions = sum(1 for a, b in zip(order, order[1:]) if a != b)
    assert transitions > 2, order
    for task in ("PT01", "PT04", "PT07"):
        positions = [i for i, t in enumerate(order) if t == task]
        assert positions[-1] - positions[0] > len(positions) - 1, (
            f"{task}'s six runs are contiguous: {positions}"
        )


def test_the_file_is_lf_only_so_its_hash_is_platform_stable():
    assert b"\r\n" not in PLAN_PATH.read_bytes()
    assert b"\r\n" not in EXECUTION_PATH.read_bytes()


# --------------------------------------------------------------------------- 3
# Identity
# --------------------------------------------------------------------------- #
def test_all_eighteen_identities_are_distinct(plan):
    identities = lmp.derive_schedule_identities(
        plan, artifact_root=ARTIFACT_ROOT, repo=REPO
    )
    assert len(identities) == 18
    assert len({i.run_id for i in identities}) == 18
    assert len({i.artifact_dir for i in identities}) == 18
    assert lmp.identity_problems(identities) == []


def test_the_identity_seed_carries_every_field_that_distinguishes_a_row(plan):
    """Attempt 1 of the efficiency pilot was aborted because one field was
    missing from this seed. The check is structural, not historical."""
    identities = lmp.derive_schedule_identities(
        plan, artifact_root=ARTIFACT_ROOT, repo=REPO
    )
    by_cell = {
        (i.task_id, i.condition, i.repetition): i.run_id for i in identities
    }
    assert len(by_cell) == 18
    # Changing any one field changes the id.
    base = dict(
        purpose=lmp.RUN_PURPOSE, task_id="PT01", condition="C1",
        task_sha=gov.expected_task_sha256("PT01"),
        substrate_hash=gov.SUBSTRATE_CONTENT_HASH, mode="real",
        repetition=1, reset_state=rb.NON_RESET, execution_attempt=1,
    )
    reference = art.derive_run_id(**base)
    for field, value in (
        ("condition", "C4"), ("repetition", 2), ("task_id", "PT04"),
        ("execution_attempt", 2), ("mode", "dry-run"),
    ):
        changed = dict(base)
        changed[field] = value
        if field == "task_id":
            changed["task_sha"] = gov.expected_task_sha256("PT04")
        assert art.derive_run_id(**changed) != reference, field


def test_no_identity_coincides_with_the_sonnet_efficiency_pilot(plan):
    identities = lmp.derive_schedule_identities(
        plan, artifact_root=ARTIFACT_ROOT, repo=REPO
    )
    assert lmp.sonnet_overlap_problems(identities, REPO) == []
    prior = set(lmp.sonnet_pilot_run_ids(REPO))

    # The prior set is real, and covers BOTH executions of that pilot. It holds
    # 54 rather than 72 ids for 72 rows, and that shortfall IS the defect that
    # aborted Attempt 1: its identity algorithm omitted the reset state, so its
    # 36 rows minted only 18 distinct ids. Attempt 2's 36 are all distinct.
    assert len(prior) == 54, len(prior)
    assert prior.isdisjoint({i.run_id for i in identities})
    assert all(i.run_id not in prior for i in identities)


def test_the_run_purpose_is_what_makes_the_two_pilots_disjoint():
    """Not the root, and not the attempt: the purpose is in the seed itself."""
    common = dict(
        task_id="PT01", condition="C1",
        task_sha=gov.expected_task_sha256("PT01"),
        substrate_hash=gov.SUBSTRATE_CONTENT_HASH, mode="real",
        repetition=1, reset_state=rb.NON_RESET, execution_attempt=1,
    )
    assert art.derive_run_id(purpose=lmp.RUN_PURPOSE, **common) != art.derive_run_id(
        purpose=ea.erp.RUN_PURPOSE, **common
    )


def test_every_run_id_is_readable_and_names_its_row(plan):
    identities = lmp.derive_schedule_identities(
        plan, artifact_root=ARTIFACT_ROOT, repo=REPO
    )
    for identity in identities:
        assert identity.run_id.startswith("afci-lower-model-pilot-")
        assert identity.task_id.lower() in identity.run_id
        assert identity.condition.lower() in identity.run_id
        assert f"r{identity.repetition}" in identity.run_id
        assert "non-reset" in identity.run_id
        assert "-a1-" in identity.run_id


# --------------------------------------------------------------------------- 4
# The execution plan
# --------------------------------------------------------------------------- #
def test_the_execution_plan_matches_the_schedule(execution, plan):
    assert execution["run_purpose"] == lmp.RUN_PURPOSE
    assert execution["scientific_plan_sha256"] == lmp.plan_sha256(plan)
    assert execution["scientific_projection_sha256"] == lmp.projection_sha256(plan)
    assert execution["seed"] == plan["seed"]
    assert execution["run_count"] == 18
    assert execution["model_id"] == plan["model_id"]
    assert execution["non_reset_max_turns"] == plan["non_reset_max_turns"]


def test_the_execution_plan_records_eighteen_unique_destinations(execution):
    identities = execution["identities"]
    assert len(identities) == 18
    assert len({i["run_id"] for i in identities}) == 18
    assert len({i["artifact_dir"] for i in identities}) == 18


def test_the_execution_plan_commits_to_isolated_roots_outside_the_profile(execution):
    assert execution["artifact_root"] == str(ARTIFACT_ROOT)
    assert execution["sterile_base"] == str(STERILE_BASE)
    for root in (ARTIFACT_ROOT, STERILE_BASE):
        assert art.execution_root_isolation_problems(root) == [], root
    # A NEW namespace: no efficiency-pilot root is reused.
    assert "attempt-2" not in execution["artifact_root"]
    assert "afci-runs" in execution["artifact_root"]


def test_the_execution_plan_carries_the_firewall(execution):
    assert execution["is_result"] is False
    assert execution["scored"] is False
    assert execution["enters_confirmatory_dataset"] is False
    assert execution["reuses_any_sonnet_pilot_observation"] is False
    assert execution["overlapping_sonnet_run_ids"] == 0


def test_the_committed_execution_plan_is_what_this_module_builds(execution):
    built = lmp.build_execution_plan(
        artifact_root=ARTIFACT_ROOT, sterile_base=STERILE_BASE, repo=REPO
    )
    assert lmp.serialise(built) == lmp.serialise(execution)


# --------------------------------------------------------------------------- 5
# The preflight
# --------------------------------------------------------------------------- #
def test_the_preflight_passes_for_the_committed_schedule():
    report = lmp.preflight(
        artifact_root=ARTIFACT_ROOT, sterile_base=STERILE_BASE, repo=REPO
    )
    assert report.eligible, report.problems
    assert report.row_count if hasattr(report, "row_count") else True
    payload = report.to_dict()
    assert payload["row_count"] == 18
    assert payload["unique_run_ids"] == 18
    assert payload["unique_artifact_dirs"] == 18
    assert payload["model_invoked"] is False
    assert payload["substantive_observations"] == 0
    assert {c["check"] for c in payload["checks"]} == {
        "committed_scientific_schedule",
        "unique_identities",
        "no_overlap_with_the_sonnet_efficiency_pilot",
        "session_allocation",
        "isolated_execution_roots",
        "destinations_unoccupied",
    }
    assert all(c["status"] == "PASS" for c in payload["checks"]), payload["checks"]


def test_the_preflight_refuses_a_schedule_with_a_duplicated_row(plan):
    """The defect that aborted Attempt 1 of the efficiency pilot, injected here."""
    broken = json.loads(json.dumps(plan))
    broken["runs"][1] = json.loads(json.dumps(broken["runs"][0]))
    broken["runs"][1]["sequence"] = 2
    report = lmp.preflight(
        artifact_root=ARTIFACT_ROOT, sterile_base=STERILE_BASE, repo=REPO,
        plan=broken,
    )
    assert not report.eligible
    assert any(
        code == gov.EFFICIENCY_SCHEDULE_IDENTITY_COLLISION
        for code, _ in report.problems
    ), report.problems


def test_the_preflight_refuses_an_occupied_destination(tmp_path, plan):
    identities = lmp.derive_schedule_identities(
        plan, artifact_root=tmp_path / "runs", repo=REPO
    )
    occupied = Path(identities[7].artifact_dir)
    occupied.mkdir(parents=True)
    (occupied / "run_record.json").write_text("{}", encoding="utf-8")
    report = lmp.preflight(
        artifact_root=tmp_path / "runs", sterile_base=tmp_path / "sterile", repo=REPO
    )
    assert not report.eligible
    assert any(
        code == gov.ARTIFACT_IDENTITY_COLLISION_PREINVOCATION
        for code, _ in report.problems
    ), report.problems


def test_the_preflight_refuses_a_root_under_the_operator_profile(tmp_path):
    report = lmp.preflight(
        artifact_root=Path.home() / "afci-runs-under-profile",
        sterile_base=tmp_path / "sterile",
        repo=REPO,
        check_occupancy=False,
    )
    assert not report.eligible
    assert any(
        code == gov.ARTIFACT_ROOT_NOT_ISOLATED for code, _ in report.problems
    ), report.problems


def test_the_preflight_refuses_a_pre_declared_session_id(plan):
    broken = json.loads(json.dumps(plan))
    broken["runs"][3]["session_id"] = "a-session-someone-chose-in-advance"
    report = lmp.preflight(
        artifact_root=ARTIFACT_ROOT, sterile_base=STERILE_BASE, repo=REPO,
        plan=broken,
    )
    assert not report.eligible
    assert any(code == gov.SESSION_ID_REUSED for code, _ in report.problems)


def test_the_preflight_allocates_one_session_per_row_and_no_phases(plan):
    slots = lmp.session_slots(plan)
    assert len(slots) == 18
    assert all(phase is None for _, phase in slots)
    assert lmp.session_allocation_problems(plan) == []


def test_the_preflight_creates_nothing(tmp_path):
    root = tmp_path / "never-created"
    lmp.preflight(
        artifact_root=root, sterile_base=tmp_path / "sterile-never", repo=REPO
    )
    assert not root.exists()
    assert not (tmp_path / "sterile-never").exists()


# --------------------------------------------------------------------------- 6
# Nothing has run
# --------------------------------------------------------------------------- #
def test_no_destination_in_the_committed_execution_plan_exists(execution):
    existing = [
        i["artifact_dir"] for i in execution["identities"]
        if Path(i["artifact_dir"]).exists()
    ]
    assert existing == [], f"an execution has begun: {existing}"


def test_the_plan_validation_refuses_a_drifted_committed_file(tmp_path, plan):
    drifted = json.loads(json.dumps(plan))
    drifted["seed"] = "AFCI_LOWER_MODEL_PILOT_V2_SOMETHING_ELSE"
    problems = lmp.plan_problems(drifted, REPO)
    assert any("seed is" in p for p in problems), problems


def test_the_plan_validation_refuses_a_second_reset_arm(plan):
    drifted = json.loads(json.dumps(plan))
    drifted["runs"][0]["reset_state"] = rb.RESET
    problems = lmp.plan_problems(drifted, REPO)
    assert any("authorises NON_RESET only" in p for p in problems), problems
