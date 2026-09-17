#!/usr/bin/env python3
"""``SL-V2-EFF-ELIG-01`` — the PILOT-SCOPED architecture-corpus exemption.

WHAT THIS MODULE HOLDS THE EXEMPTION TO. An exemption is only defensible if it
is narrower than the rule it narrows, so every test here is really one of two
questions:

* does the exemption actually apply when, and ONLY when, its eight pre-data
  conditions hold? and
* does anything OUTSIDE ``AFCI_EFFICIENCY_PILOT`` move because of it?

The second answer must be *nothing*, and it is asserted rather than asserted of:
every other registered purpose is checked for the exemption field, the
confirmatory path is checked directly, and the gate and register rows are read
back out of the public authorities.

Every fixture is synthetic and lives under ``tmp_path``. Nothing here reads the
real private repository except the tests that say so, nothing writes into it, no
model is invoked, nothing is scored, and no pilot observation is produced.
"""
from __future__ import annotations

import dataclasses
import json
import subprocess
import sys
from pathlib import Path

import pytest

HARNESS = Path(__file__).resolve().parents[1]
if str(HARNESS) not in sys.path:
    sys.path.insert(0, str(HARNESS))

import run_governance as gov  # noqa: E402
import run_v2  # noqa: E402

PURPOSE = "AFCI_EFFICIENCY_PILOT"
AUTHORITY = "SL-V2-EFF-ELIG-01"
RECORD = gov.REPO / "docs" / "v2" / "AFCI_EFFICIENCY_PILOT_ELIGIBILITY_DECISION.md"
TASKS = ("PT01", "PT04", "PT07")
CONDITIONS = ("C1", "C4")

#: A target that is deliberately NOT any real task's. These fixtures exist to
#: exercise the CHECK, and binding a real task id to a real rule id in the public
#: repository is the disclosure the whole suite is built to prevent.
FIXTURE_RULE = "AR-DEP-002"
FIXTURE_SOURCE = "contracts"
FIXTURE_TARGET = "core"


def _public_head() -> str:
    return subprocess.run(
        ["git", "-C", str(gov.REPO), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def _validation_block(task_id: str) -> dict:
    """A clean architecture-validation block: every condition 2-6 satisfied."""
    return {
        "record_id": f"PRIVATE-{task_id}-ARCHITECTURE-VALIDATION-001",
        "task_id": task_id,
        "state": "VALIDATED",
        "public_task_sha256": gov.expected_task_sha256(task_id),
        "hidden_functional_acceptance_validated": True,
        "functional_acceptance_enforces_architecture": False,
        "target": {
            "opportunity_id": "FIXTURE-OPPORTUNITY",
            "rule_id": FIXTURE_RULE,
            "source_layer": FIXTURE_SOURCE,
            "forbidden_target_layer": FIXTURE_TARGET,
        },
        "legal_reference": {
            "hidden_functional_acceptance": "PASS",
            "semantic_failed_cases": [],
            "architecture_status": "SATISFIED",
            "applicable_opportunity_count": 1,
            "violated_opportunity_count": 0,
            "raw_violation_count": 0,
            "detected_rule_id": FIXTURE_RULE,
            "detected_source_layer": FIXTURE_SOURCE,
            "detected_target_layer": None,
        },
        "violating_reference": {
            "hidden_functional_acceptance": "PASS",
            "semantic_failed_cases": [],
            "architecture_status": "VIOLATION",
            "applicable_opportunity_count": 1,
            "violated_opportunity_count": 1,
            "raw_violation_count": 1,
            "detected_rule_id": FIXTURE_RULE,
            "detected_source_layer": FIXTURE_SOURCE,
            "detected_target_layer": FIXTURE_TARGET,
        },
    }


def _sync_block(task_id: str) -> dict:
    return {
        "record_id": f"PRIVATE-PUBLIC-SYNC-PREFREEZE-{task_id}-001",
        "state": "SATISFIED",
        "verified_public_sha": _public_head(),
    }


def _private_root(
    tmp_path: Path,
    task_id: str,
    *,
    validation: object = "clean",
    sync: bool = True,
    corpus: bool = False,
) -> Path:
    """A synthetic private root carrying exactly what the test intends.

    ``validation`` takes ``"clean"``, ``None`` (the block is absent entirely) or
    a dict, which is used verbatim so a mutation test can break one field.
    """
    root = tmp_path / "private"
    task_dir = root / "tasks" / task_id
    task_dir.mkdir(parents=True)
    (task_dir / "public_linkage.json").write_text(
        json.dumps({"public_task_sha256": gov.expected_task_sha256(task_id)}),
        encoding="utf-8",
    )
    record: dict = {"task_id": task_id}
    if sync:
        record["public_synchronisation_required_before_freeze"] = _sync_block(task_id)
    if validation == "clean":
        record["architecture_validation"] = _validation_block(task_id)
    elif validation is not None:
        record["architecture_validation"] = validation
    (task_dir / f"{task_id.lower()}_package_record.json").write_text(
        json.dumps(record, indent=2), encoding="utf-8"
    )
    if corpus:
        (root / "scripts").mkdir(parents=True, exist_ok=True)
        (root / "scripts" / f"{task_id.lower()}_corpus.py").write_text("", encoding="utf-8")
        (root / "spec").mkdir(parents=True, exist_ok=True)
        (root / "spec" / "pilot_spec.py").write_text("", encoding="utf-8")
    return root


def _mutated(task_id: str, path: tuple, value: object) -> dict:
    """The clean validation block with exactly one field changed."""
    block = _validation_block(task_id)
    node = block
    for key in path[:-1]:
        node = node[key]
    if value is ...:
        node.pop(path[-1], None)
    else:
        node[path[-1]] = value
    return block


def _status(report: gov.ReadinessReport, item: str) -> str:
    return next(p.status for p in report.prerequisites if p.item == item)


def _codes(report: gov.ReadinessReport) -> set:
    return {str(p.code) for p in report.blocked}


# --------------------------------------------------------------------------- #
# 1. The authority, re-derived from the record rather than trusted
# --------------------------------------------------------------------------- #
#: Every purpose that carries an architecture-corpus exemption, and the AUTHORITY
#: that granted it. A mapping rather than a single name, because a second pilot
#: has since been authorised — and a mapping is what keeps the check fail-closed:
#: a purpose absent from it must carry NONE, and a purpose present in it must
#: carry exactly the authority written here and not some other purpose's.
EXEMPTED_PURPOSES = {
    PURPOSE: AUTHORITY,
    # SL-V2-LOWER-MODEL-01 took the same question on its own facts, in its own
    # record, against the same eight conditions. It did NOT inherit this one:
    # SL-V2-EFF-ELIG-01 is scoped to the purpose it names, and an exemption that
    # could be inherited would not be scoped at all.
    "AFCI_LOWER_MODEL_PILOT": "SL-V2-LOWER-MODEL-01",
}


def test_only_an_authorised_pilot_carries_an_exemption_and_only_its_own():
    """The fail-closed default, asserted over every registered purpose.

    This is the test that would fail if a later package gave a confirmatory
    purpose an exemption by copying a pilot's registration — and, now that two
    exemptions exist, it is also the test that would fail if one pilot were
    quietly pointed at the other's authority or the other's record.
    """
    for name, purpose in gov.RUN_PURPOSES.items():
        expected = EXEMPTED_PURPOSES.get(name)
        assert purpose.architecture_corpus_exemption == expected, (
            f"{name} carries exemption {purpose.architecture_corpus_exemption!r}, "
            f"not {expected!r}"
        )
        if expected is None:
            assert purpose.architecture_corpus_exemption_record is None
            assert purpose.architecture_corpus_exemption_pins == ()
        else:
            # An exemption only exists where its OWN record puts it, so the
            # record a purpose names must be the one whose table names it back.
            governed = gov._table_values(
                gov._section(
                    purpose.corpus_exemption_record_path(gov.REPO).read_text(
                        encoding="utf-8"
                    ),
                    purpose.architecture_corpus_exemption_heading,
                )
            )
            assert governed.get("decision_id") == expected, name
            assert governed.get("run_purpose") == name, name


def test_an_exempted_purpose_is_never_confirmatory_or_result_bearing():
    """Condition 7, asserted structurally over every exemption that exists.

    The exemption is defensible only because the architecture measurement it
    unblocks is descriptive. A confirmatory or result-bearing purpose holding one
    would be the exact widening the scoping exists to prevent.
    """
    for name in EXEMPTED_PURPOSES:
        purpose = gov.RUN_PURPOSES[name]
        assert not purpose.confirmatory, name
        assert not purpose.result_bearing, name
        assert purpose.firewall_flags() == {f: False for f in gov.FIREWALL_FIELDS}


def test_the_exemption_table_is_re_derived_from_the_record():
    purpose = gov.resolve_run_purpose(PURPOSE)
    governed = gov._table_values(
        gov._section(
            RECORD.read_text(encoding="utf-8"),
            purpose.architecture_corpus_exemption_heading,
        )
    )
    assert governed, "the eligibility rule table is absent from the record"
    for key, want in purpose.architecture_corpus_exemption_pins:
        assert governed[key] == want, f"{key}: record={governed[key]!r} runner={want!r}"


def test_a_record_that_claimed_a_global_waiver_is_refused(tmp_path, monkeypatch):
    """The narrowing must stay a narrowing, or the exemption stops existing."""
    purpose = gov.resolve_run_purpose(PURPOSE)
    drifted = tmp_path / "drifted.md"
    drifted.write_text(
        RECORD.read_text(encoding="utf-8").replace(
            "| `architecture_corpus_requirement_waived_globally` | `false` |",
            "| `architecture_corpus_requirement_waived_globally` | `true` |",
        ),
        encoding="utf-8",
    )
    widened = dataclasses.replace(
        purpose, architecture_corpus_exemption_record=str(drifted)
    )
    problems = gov.architecture_corpus_exemption_problems(
        widened, "PT01", _private_root(tmp_path, "PT01")
    )
    assert any("waived_globally" in p for p in problems), problems


def test_an_absent_exemption_record_is_refused(tmp_path):
    purpose = dataclasses.replace(
        gov.resolve_run_purpose(PURPOSE),
        architecture_corpus_exemption_record="docs/v2/DOES_NOT_EXIST.md",
    )
    problems = gov.architecture_corpus_exemption_problems(
        purpose, "PT01", _private_root(tmp_path, "PT01")
    )
    assert problems and "is not available" in problems[0]


# --------------------------------------------------------------------------- #
# 2. The exemption applies when, and only when, the eight conditions hold
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("task", ("PT01", "PT04"))
@pytest.mark.parametrize("condition", CONDITIONS)
def test_the_pilot_may_proceed_without_a_corpus_when_the_validation_exists(
    tmp_path, task, condition
):
    """Part D's first proof, through the REAL readiness report.

    Not ``PASS``: the corpus genuinely does not exist. ``N/A`` says the
    requirement does not apply to this purpose, which is the true statement.
    """
    root = _private_root(tmp_path, task, corpus=False)
    report = gov.check_readiness(task, condition, PURPOSE, private_root=root)
    assert gov.ARCHITECTURE_CORPUS_NOT_AVAILABLE not in _codes(report)
    assert _status(report, "architecture_corpus_availability") == gov.NOT_APPLICABLE
    assert _status(report, "pilot_architecture_validation") == gov.PASS
    assert _codes(report) == {gov.CONTEXT_AUDIT_UNKNOWN}, (
        "the only blocker left must be the context verdict, which a later state "
        "resolves"
    )


def test_a_present_corpus_still_reports_pass_rather_than_the_exemption(tmp_path):
    """The exemption is a fallback, never a replacement for real evidence."""
    root = _private_root(tmp_path, "PT01", corpus=True)
    report = gov.check_readiness("PT01", "C1", PURPOSE, private_root=root)
    assert _status(report, "architecture_corpus_availability") == gov.PASS


def test_the_clean_fixture_is_not_vacuous(tmp_path):
    """Guard the guard: if the clean fixture were rejected, every mutation
    below would 'pass' for the wrong reason."""
    assert gov.architecture_corpus_exemption_problems(
        gov.resolve_run_purpose(PURPOSE), "PT01", _private_root(tmp_path, "PT01")
    ) == []


# --------------------------------------------------------------------------- #
# 3. Each missing piece of evidence BLOCKS
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "label,mutation",
    [
        # Condition 2 — the legal reference passes hidden functional acceptance.
        ("missing legal-reference validation", (("legal_reference",), ...)),
        ("legal reference fails functional acceptance",
         (("legal_reference", "hidden_functional_acceptance"), "FAIL")),
        ("legal reference failed a semantic case",
         (("legal_reference", "semantic_failed_cases"), ["X-AC-01"])),
        # Condition 3 — it creates the opportunity and violates nothing.
        ("legal reference's target opportunity is not applicable",
         (("legal_reference", "applicable_opportunity_count"), 0)),
        ("legal reference records a target violation",
         (("legal_reference", "violated_opportunity_count"), 1)),
        ("legal reference is scored VIOLATION",
         (("legal_reference", "architecture_status"), "VIOLATION")),
        # Condition 4 — the violating reference is FUNCTIONALLY CORRECT.
        ("missing target-violating validation", (("violating_reference",), ...)),
        ("violating reference fails functional acceptance",
         (("violating_reference", "hidden_functional_acceptance"), "FAIL")),
        # Condition 5 — the scorer detects the EXACT intended violation.
        ("undetected target violation",
         (("violating_reference", "architecture_status"), "SATISFIED")),
        ("violation detected but not counted",
         (("violating_reference", "violated_opportunity_count"), 0)),
        ("a DIFFERENT rule was detected",
         (("violating_reference", "detected_rule_id"), "AR-DEP-004")),
        ("a DIFFERENT source layer was detected",
         (("violating_reference", "detected_source_layer"), "features")),
        ("a DIFFERENT forbidden target was detected",
         (("violating_reference", "detected_target_layer"), "infra")),
        # Condition 6 — functional acceptance leaves architecture alone.
        ("functional acceptance enforces architecture",
         (("functional_acceptance_enforces_architecture",), True)),
        # Condition 1, as the private record restates it.
        ("missing functional runtime validation",
         (("hidden_functional_acceptance_validated",), False)),
        # The record's own integrity.
        ("the record is not VALIDATED", (("state",), "DRAFT")),
        ("the record is bound to other task bytes",
         (("public_task_sha256",), "0" * 64)),
        ("the target rule is not in the public catalog",
         (("target", "rule_id"), "AR-NOT-A-REAL-RULE-001")),
        ("the target rule is the umbrella",
         (("target", "rule_id"), gov.UMBRELLA_RULE_ID)),
        ("the target declares no source layer", (("target", "source_layer"), "")),
        ("the target block is absent", (("target",), ...)),
    ],
)
def test_every_missing_or_wrong_piece_of_evidence_blocks(tmp_path, label, mutation):
    path, value = mutation
    root = _private_root(tmp_path, "PT01", validation=_mutated("PT01", path, value))
    problems = gov.architecture_corpus_exemption_problems(
        gov.resolve_run_purpose(PURPOSE), "PT01", root
    )
    assert problems, f"MUTATION ESCAPED: {label}"

    report = gov.check_readiness("PT01", "C1", PURPOSE, private_root=root)
    assert gov.PILOT_ARCHITECTURE_VALIDATION_NOT_AVAILABLE in _codes(report), label
    assert gov.ARCHITECTURE_CORPUS_NOT_AVAILABLE in _codes(report), (
        f"{label}: the corpus prerequisite must fall back to BLOCKED, never to N/A"
    )
    assert report.run_eligible is False, label


def test_an_absent_validation_block_blocks(tmp_path):
    root = _private_root(tmp_path, "PT01", validation=None)
    report = gov.check_readiness("PT01", "C1", PURPOSE, private_root=root)
    assert gov.PILOT_ARCHITECTURE_VALIDATION_NOT_AVAILABLE in _codes(report)
    assert gov.ARCHITECTURE_CORPUS_NOT_AVAILABLE in _codes(report)


def test_an_absent_private_repository_is_not_a_pass(tmp_path):
    """Absence of evidence is never evidence, in either direction."""
    ok, _detail, problems = gov.private_architecture_validation_state(
        "PT01", tmp_path / "nothing-here"
    )
    assert ok is False and problems


# --------------------------------------------------------------------------- #
# 4. Missing package sync still blocks, and the exemption does not touch it
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("task", TASKS)
def test_missing_package_sync_still_blocks(tmp_path, task):
    """The exemption narrows ONE prerequisite. The other one is untouched."""
    root = _private_root(tmp_path, task, sync=False)
    report = gov.check_readiness(task, "C1", PURPOSE, private_root=root)
    assert gov.PRIVATE_PUBLIC_SYNC_PROPAGATION_REQUIRED_BEFORE_FREEZE in _codes(report)
    assert report.run_eligible is False
    # ...and it blocks a real run rather than being merely reported.
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        run_v2._assert_readiness_permits_a_real_run(report)
    assert excinfo.value.code == (
        gov.PRIVATE_PUBLIC_SYNC_PROPAGATION_REQUIRED_BEFORE_FREEZE
    )


def test_a_sync_record_citing_an_unknown_commit_discharges_nothing(tmp_path):
    root = tmp_path / "private"
    task_dir = root / "tasks" / "PT01"
    task_dir.mkdir(parents=True)
    (task_dir / "pt01_package_record.json").write_text(
        json.dumps({
            "public_synchronisation_required_before_freeze": {
                "record_id": "X", "state": "SATISFIED",
                "verified_public_sha": "0" * 40,
            }
        }),
        encoding="utf-8",
    )
    ok, detail = gov.private_sync_prefreeze_state("PT01", root)
    assert ok is False and "not an ancestor" in detail


# --------------------------------------------------------------------------- #
# 5. Nothing outside this purpose moves
# --------------------------------------------------------------------------- #
def test_a_confirmatory_purpose_still_requires_its_corpus(tmp_path):
    """Part D's confirmatory proof, both ways round.

    A purpose that names no exemption gets a problem for that reason alone, and
    a purpose that somehow named one while being confirmatory or result-bearing
    fails condition 7.
    """
    pilot = gov.resolve_run_purpose(PURPOSE)
    root = _private_root(tmp_path, "PT01")

    no_authority = dataclasses.replace(pilot, architecture_corpus_exemption=None)
    problems = gov.architecture_corpus_exemption_problems(no_authority, "PT01", root)
    assert problems and "names no architecture-corpus exemption authority" in problems[0]

    for field, value in (("confirmatory", True), ("result_bearing", True)):
        promoted = dataclasses.replace(pilot, **{field: value})
        problems = gov.architecture_corpus_exemption_problems(promoted, "PT01", root)
        assert any("condition 7" in p for p in problems), (field, problems)


def test_a_purpose_without_the_exemption_reports_the_corpus_blocker_unchanged(tmp_path):
    """The pre-existing behaviour, byte for byte, for every other purpose."""
    ok, detail = gov.private_architecture_corpus_available(
        "PT09", tmp_path, "scripts/qualification_corpus.py"
    )
    assert ok is False and "architecture corpus is not available" in detail
    report = gov.check_readiness(
        "PT09", "C1", "INSTRUMENT_QUALIFICATION_DIAGNOSTIC", private_root=tmp_path
    )
    assert gov.ARCHITECTURE_CORPUS_NOT_AVAILABLE in _codes(report)
    assert [p.item for p in report.prerequisites].count(
        "pilot_architecture_validation"
    ) == 0, "a purpose with no exemption must not gain the exemption item"


def test_the_exemption_never_claims_a_gate_or_a_register(tmp_path):
    """Condition 8, and everything §5 of the record says it does not do."""
    report = gov.check_readiness(
        "PT01", "C1", PURPOSE, private_root=_private_root(tmp_path, "PT01")
    )
    # G1 stays NOT APPLICABLE-and-not-passed, exactly as before this package.
    g1 = next(p for p in report.prerequisites if p.item == "suite_wide_gate_g1")
    assert g1.status == gov.NOT_APPLICABLE
    assert "NOT PASSED" in g1.detail and "NOT close TD-B34" in g1.detail

    firewall = gov.governed_firewall_from_record(
        gov.resolve_run_purpose(PURPOSE).firewall_record_path(),
        gov.resolve_run_purpose(PURPOSE).firewall_heading,
    )
    for flag in gov.FIREWALL_FIELDS:
        assert firewall[flag] is False


def test_the_blocking_decision_rows_are_unchanged():
    """TD-B32, TD-B34 and TD-B39 are read back out of the public register."""
    for decision_id in ("TD-B32", "TD-B34", "TD-B39", "TD-B01", "TD-B11",
                        "TD-B12", "TD-B03", "TD-B42"):
        assert gov.decision_is_open(decision_id), f"{decision_id} is no longer open"


def test_the_record_does_not_claim_any_of_the_things_it_must_not():
    flat = " ".join(RECORD.read_text(encoding="utf-8").lower().split())
    for claim in ("g1 is passed", "g2 is passed", "td-b32 is closed",
                  "td-b34 is closed", "td-b39 is closed", "the suite is frozen"):
        assert claim not in flat, f"the record claims {claim!r}"
    for required in ("passes no gate", "unchanged and required",
                     "not done, not waived and not reduced in scope"):
        assert required in flat, f"the record does not say {required!r}"


def test_the_record_leaks_no_per_task_architecture_identity():
    """The disclosure convention every other public record lives under."""
    text = RECORD.read_text(encoding="utf-8")
    import re
    assert not re.search(r"\bAR-[A-Z]+-\d+|\bOPP-|\bDC-[A-Z0-9-]+", text), (
        "the eligibility record names an architecture identifier"
    )
    assert not re.search(
        r"(?:features|api|core|infra|contracts|observability)\s*(?:->|→)\s*"
        r"(?:features|api|core|infra|contracts|observability)",
        text, re.IGNORECASE,
    ), "the eligibility record renders a layer edge"


def test_the_readiness_probe_declares_the_reset_arm_it_audits(monkeypatch):
    """A reset-aware purpose refuses a run that does not declare its arm.

    ``--check-readiness --live-context-audit`` runs a real dry run so the audited
    environment is the one a repetition would launch in. It did not pass the arm
    on, so for this purpose the probe refused in ``PRECHECK`` and the verdict
    came back ``UNKNOWN`` — which reads as *the environment is not clean* when
    what happened is that the audit never ran. The arm is threaded, never
    defaulted: a purpose that needs one and is given none still refuses.
    """
    seen = {}

    def _fake_run(request):
        seen["reset_state"] = request.reset_state
        return run_v2.RunResult(
            machine=None,
            record={"context_audit": {"verdict": "CLEAN"}},
        )

    monkeypatch.setattr(run_v2, "run", _fake_run)
    args = run_v2._build_parser().parse_args([
        "--task", "PT01", "--condition", "C1", "--run-purpose", PURPOSE,
        "--reset-state", "RESET", "--check-readiness",
    ])
    assert run_v2.live_context_verdict(args) == "CLEAN"
    assert seen["reset_state"] == "RESET"

    args = run_v2._build_parser().parse_args([
        "--task", "PT01", "--condition", "C1", "--run-purpose", PURPOSE,
        "--check-readiness",
    ])
    run_v2.live_context_verdict(args)
    assert seen["reset_state"] is None, (
        "an absent arm must stay absent so the purpose's own refusal fires"
    )


def test_no_efficiency_observation_exists_when_this_rule_is_recorded():
    """The pre-data proof, mechanical rather than prose."""
    for name in ("results", "analysis"):
        directory = gov.REPO / "experiments" / "v2" / name
        assert sorted(p.name for p in directory.iterdir()) == ["README.md"]
    runs = list(
        gov.default_artifact_root().glob(f"{PURPOSE.lower().replace('_', '-')}*")
    )
    assert runs == [], f"a pilot observation exists: {runs}"
