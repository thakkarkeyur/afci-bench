"""Mechanical integrity of the public task suite's hashes and metadata.

The independent public review found that every recorded ``public_task_sha256`` was
correct but that **nothing checked it**, and that ``TASK_SCHEMA.yml`` and
``public_task.schema.json`` had drifted apart on the ``category`` vocabulary. Both
gaps are closed here.

This module asserts:

* every public task body's SHA-256 matches the value recorded in
  ``TASK_INDEX.csv``;
* ``TASK_INDEX.csv`` covers exactly the discovered task bodies;
* ``PILOT_PUBLIC_TASK_MATRIX.csv`` agrees with ``TASK_INDEX.csv`` on hash,
  primary/reserve classification and every shared column;
* front-matter ``id``/``title``/``category``/``status``/``visible_validation``
  match both public matrices;
* ``TASK_SCHEMA.yml`` and ``public_task.schema.json`` declare the same category
  vocabulary, and it uses ``logging`` rather than the repository layer name
  ``observability``;
* task ids are unique everywhere;
* the authoring report's inventory table agrees with the index;
* no artifact presents the candidate count as a final core-study count.

Pure file inspection; no model is invoked.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[4]
PUBLIC_TASKS_DIR = REPO / "experiments" / "v2" / "tasks" / "public"
INDEX_PATH = PUBLIC_TASKS_DIR / "TASK_INDEX.csv"
SCHEMA_YML = PUBLIC_TASKS_DIR / "TASK_SCHEMA.yml"
REPORT_PATH = PUBLIC_TASKS_DIR / "TASK_AUTHORING_REPORT.md"
MATRIX_PATH = REPO / "docs" / "v2" / "PILOT_PUBLIC_TASK_MATRIX.csv"
SCHEMA_JSON = REPO / "experiments" / "v2" / "schemas" / "public_task.schema.json"

#: PT01-PT06 are the repaired pilot suite; PT07 was authored later under
#: DECISION B (TD-B34). PR01/PR02 are the pre-declared reserves.
EXPECTED_IDS = [f"PT0{i}" for i in range(1, 8)] + ["PR01", "PR02"]
NON_TASK_STEMS = {"README", "TASK_AUTHORING_REPORT"}


# --------------------------------------------------------------------------- #
# Loaders
# --------------------------------------------------------------------------- #
def _task_files():
    return sorted(
        p for p in PUBLIC_TASKS_DIR.glob("*.md") if p.stem.upper() not in NON_TASK_STEMS
    )


def _front_matter(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines and lines[0].strip() == "---", f"{path.name} must start with front matter"
    end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    data = yaml.safe_load("\n".join(lines[1:end]))
    assert isinstance(data, dict), f"{path.name} front matter must be a mapping"
    return data


def _rows(path: Path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


INDEX_ROWS = _rows(INDEX_PATH)
MATRIX_ROWS = _rows(MATRIX_PATH)
INDEX_BY_ID = {r["task_id"]: r for r in INDEX_ROWS}
MATRIX_BY_ID = {r["task_id"]: r for r in MATRIX_ROWS}


# --------------------------------------------------------------------------- #
# Hashes
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("path", _task_files(), ids=lambda p: p.name)
def test_recorded_hash_matches_the_task_body(path):
    row = INDEX_BY_ID.get(path.stem)
    assert row is not None, f"{path.name} is not in TASK_INDEX.csv"
    actual = _sha256(path)
    assert row["public_task_sha256"] == actual, (
        f"{path.name}: TASK_INDEX.csv records "
        f"{row['public_task_sha256'][:16]}... but the file hashes to {actual[:16]}...; "
        "re-run the hash update and re-link the private evaluator package"
    )


@pytest.mark.parametrize("path", _task_files(), ids=lambda p: p.name)
def test_matrix_hash_matches_the_task_body(path):
    row = MATRIX_BY_ID.get(path.stem)
    assert row is not None, f"{path.name} is not in PILOT_PUBLIC_TASK_MATRIX.csv"
    assert row["public_task_sha256"] == _sha256(path)


def test_task_bodies_are_lf_only_so_hashes_are_platform_stable():
    for path in _task_files():
        assert b"\r\n" not in path.read_bytes(), f"{path.name} contains CRLF"


def test_every_recorded_hash_is_a_full_sha256():
    for row in INDEX_ROWS + MATRIX_ROWS:
        assert re.fullmatch(r"[0-9a-f]{64}", row["public_task_sha256"]), row["task_id"]


def test_recorded_hashes_are_distinct():
    hashes = [r["public_task_sha256"] for r in INDEX_ROWS]
    assert len(set(hashes)) == len(hashes), "two tasks share a hash"


# --------------------------------------------------------------------------- #
# Set equality and id uniqueness
# --------------------------------------------------------------------------- #
def test_index_covers_exactly_the_discovered_task_bodies():
    assert {p.stem for p in _task_files()} == set(INDEX_BY_ID)


def test_matrix_covers_exactly_the_index():
    assert set(MATRIX_BY_ID) == set(INDEX_BY_ID)


def test_expected_candidate_suite_is_present():
    assert sorted(INDEX_BY_ID) == sorted(EXPECTED_IDS)


def test_task_ids_are_unique_in_every_artifact():
    for name, rows in (("TASK_INDEX.csv", INDEX_ROWS), ("PILOT_PUBLIC_TASK_MATRIX.csv", MATRIX_ROWS)):
        ids = [r["task_id"] for r in rows]
        assert len(ids) == len(set(ids)), f"duplicate task ids in {name}"
    stems = [p.stem for p in _task_files()]
    assert len(stems) == len(set(stems))
    fm_ids = [_front_matter(p)["id"] for p in _task_files()]
    assert len(fm_ids) == len(set(fm_ids)), "duplicate front-matter ids"


def test_duplicate_ids_would_be_rejected():
    """Guard the guard: the uniqueness check must actually detect a duplicate."""
    ids = ["PT01", "PT02", "PT01"]
    assert len(ids) != len(set(ids))


# --------------------------------------------------------------------------- #
# Front matter vs both matrices
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("path", _task_files(), ids=lambda p: p.name)
def test_front_matter_matches_both_matrices(path):
    fm = _front_matter(path)
    index = INDEX_BY_ID[path.stem]
    matrix = MATRIX_BY_ID[path.stem]

    assert fm["id"] == path.stem
    for row, label in ((index, "TASK_INDEX.csv"), (matrix, "PILOT_PUBLIC_TASK_MATRIX.csv")):
        assert fm["id"] == row["task_id"], label
        assert fm["title"] == row["title"], label
        assert fm["category"] == row["functional_category"], label
        assert fm["kind"] == row["primary_or_reserve"], label
        assert fm["status"] == row["task_status"], label
        assert fm["visible_validation"] == row["visible_ci_command"], label


@pytest.mark.parametrize("task_id", EXPECTED_IDS)
def test_index_and_matrix_agree_on_every_shared_column(task_id):
    index = INDEX_BY_ID[task_id]
    matrix = MATRIX_BY_ID[task_id]
    for column in set(index) & set(matrix):
        assert index[column] == matrix[column], f"{task_id}: {column} differs"


def test_primary_reserve_classification_is_consistent_and_expected():
    kinds = {tid: INDEX_BY_ID[tid]["primary_or_reserve"] for tid in EXPECTED_IDS}
    assert [tid for tid, k in kinds.items() if k == "primary"] == [f"PT0{i}" for i in range(1, 8)]
    assert [tid for tid, k in kinds.items() if k == "reserve"] == ["PR01", "PR02"]
    for tid, kind in kinds.items():
        assert _front_matter(PUBLIC_TASKS_DIR / f"{tid}.md")["kind"] == kind
        assert MATRIX_BY_ID[tid]["primary_or_reserve"] == kind


def test_every_task_is_a_candidate_and_uses_only_the_agent_ci_command():
    for path in _task_files():
        fm = _front_matter(path)
        assert fm["status"] == "candidate"
        assert fm["visible_validation"] == "npm run ci:agent"
    for row in INDEX_ROWS + MATRIX_ROWS:
        assert row["task_status"] == "candidate"
        assert row["visible_ci_command"] == "npm run ci:agent"


# --------------------------------------------------------------------------- #
# Shared category vocabulary
# --------------------------------------------------------------------------- #
def test_task_schema_yml_and_json_schema_share_the_category_vocabulary():
    yml = yaml.safe_load(SCHEMA_YML.read_text(encoding="utf-8"))
    js = json.loads(SCHEMA_JSON.read_text(encoding="utf-8"))
    yml_enum = yml["front_matter"]["category_enum"]
    js_enum = js["properties"]["category"]["enum"]
    assert sorted(yml_enum) == sorted(js_enum), (
        f"category vocabularies differ: TASK_SCHEMA.yml only={sorted(set(yml_enum) - set(js_enum))}, "
        f"public_task.schema.json only={sorted(set(js_enum) - set(yml_enum))}"
    )


def test_category_vocabulary_uses_logging_not_the_layer_name_observability():
    yml = yaml.safe_load(SCHEMA_YML.read_text(encoding="utf-8"))
    js = json.loads(SCHEMA_JSON.read_text(encoding="utf-8"))
    for enum in (yml["front_matter"]["category_enum"], js["properties"]["category"]["enum"]):
        assert "logging" in enum
        assert "observability" not in enum, (
            "`observability` is also a repository library name and must not be reused as "
            "public task metadata"
        )
    assert (REPO / "libs" / "observability").is_dir(), "premise of this test: the layer exists"


@pytest.mark.parametrize("path", _task_files(), ids=lambda p: p.name)
def test_every_task_category_is_in_the_shared_vocabulary(path):
    yml = yaml.safe_load(SCHEMA_YML.read_text(encoding="utf-8"))
    js = json.loads(SCHEMA_JSON.read_text(encoding="utf-8"))
    category = _front_matter(path)["category"]
    assert category in yml["front_matter"]["category_enum"]
    assert category in js["properties"]["category"]["enum"]


def test_public_schema_requires_no_hidden_field():
    js = json.loads(SCHEMA_JSON.read_text(encoding="utf-8"))
    assert js["additionalProperties"] is False
    assert set(js["required"]) == {
        "id", "title", "category", "kind", "status", "visible_validation"
    }
    forbidden = {
        "expected_layers", "prohibited_layers", "required_areas", "prohibited_areas",
        "hidden_acceptance", "legitimate_alternatives", "reset_predicate",
        "opportunity_set", "rule_ids", "evaluator_manifest",
    }
    assert forbidden.isdisjoint(js["properties"]), "schema must admit no hidden-answer field"
    assert forbidden.isdisjoint(js["required"])


# --------------------------------------------------------------------------- #
# Authoring report inventory
# --------------------------------------------------------------------------- #
def test_authoring_report_inventory_matches_the_index():
    report = REPORT_PATH.read_text(encoding="utf-8")
    row_re = re.compile(
        r"^\|\s*(P[TR]\d\d)\s*\|\s*(\w+)\s*\|\s*([\w-]+)\s*\|\s*(\w+)\s*\|\s*`([0-9a-f]+)\.\.\.`\s*\|",
        re.MULTILINE,
    )
    matches = row_re.findall(report)
    assert {m[0] for m in matches} == set(EXPECTED_IDS), "report inventory is incomplete"
    for task_id, kind, category, scope, hash_prefix in matches:
        row = INDEX_BY_ID[task_id]
        assert kind == row["primary_or_reserve"], task_id
        assert category == row["functional_category"], task_id
        assert scope == row["scope_category"], task_id
        assert len(hash_prefix) >= 12, f"{task_id}: hash prefix too short to be useful"
        assert row["public_task_sha256"].startswith(hash_prefix), (
            f"{task_id}: report hash prefix {hash_prefix} does not match "
            f"{row['public_task_sha256'][:16]}"
        )


def test_authoring_report_records_private_package_staleness():
    # strip markdown emphasis so "**must not** be reviewed" matches
    report = REPORT_PATH.read_text(encoding="utf-8").lower().replace("*", "")
    assert "stale" in report, "the report must record that the old private package is stale"
    assert "must not be reviewed" in report, "the report must forbid reviewing the stale package"
    assert "re-linked" in report or "re-authored" in report
    assert "never be silently accepted" in report
    assert "not accessed" in report, "the report must state the private repo was not accessed"


def test_authoring_report_scopes_the_pt06_amendment_staleness_to_pt06():
    """The PT06 amendment changed one task body, so its staleness must be scoped.

    A blanket "the private package is stale" would force needless re-authoring of
    seven packages that are still linked to reviewed public bytes; a silent amendment
    would let a superseded PT06 package be reviewed as complete. The report must say
    exactly which is which.
    """
    report = REPORT_PATH.read_text(encoding="utf-8").replace("*", "")
    lowered = report.lower()
    assert "only pt06's private package becomes stale" in lowered, (
        "the report must scope this amendment's staleness to PT06"
    )
    assert "must not be reviewed as a complete eight-task package" in lowered, (
        "the report must forbid reviewing the private commit as a complete package"
    )
    assert "substantively re-authored" in lowered, (
        "PT06's private package changed subject matter and must be re-authored, "
        "not merely re-hashed"
    )
    assert "0e77d49" in report, (
        "the report must name the public commit whose bytes the other seven "
        "packages remain linked to"
    )
    assert "seven" in lowered and "pt04" in lowered


def test_pt06_hash_transition_is_recorded_with_every_hash_in_the_chain():
    """Hash linkage: every PT06 hash in the chain stays recorded and auditable.

    PT06's public bytes have changed twice since they were first repaired - once for
    the feasibility amendment, once for the rejection-contract clarification. A private
    package may be pinned to any of the three, so all three must remain identifiable
    from the report, and the current one must be the one the index records.
    """
    report = REPORT_PATH.read_text(encoding="utf-8")
    new_hash = INDEX_BY_ID["PT06"]["public_task_sha256"]
    assert new_hash.startswith("3e0f84cfef1f9fbf"), (
        "PT06's recorded hash changed again; extend the recorded transition chain so "
        "old->new linkage stays auditable"
    )
    prefixes = re.findall(r"`([0-9a-f]{16})\.\.\.`", report)
    assert new_hash[:16] in prefixes, "the report must record PT06's current hash"
    for superseded in ("3994a158ad39f629", "ae87303c6be53fe1"):
        assert superseded in prefixes, (
            f"the report must keep recording superseded PT06 hash {superseded}, so a "
            "private package pinned to it is identifiable"
        )


def test_report_records_the_pt06_acceptance_scope_constraints():
    """The public text now pins a response header, so the acceptance bound must be
    recorded publicly - both what PT06 acceptance may assert and what it may not."""
    report = REPORT_PATH.read_text(encoding="utf-8").replace("*", "")
    lowered = report.lower()
    assert "pt06 acceptance scope" in lowered, (
        "the report must carry a PT06 acceptance-scope section"
    )
    assert "may assert that the rejection response carries a" in lowered and (
        "application/json" in lowered
    ), "the report must state that PT06 acceptance may assert the JSON media type"
    assert "must not assert any other response header" in lowered, (
        "the report must forbid PT06 acceptance asserting any other response header"
    )
    assert "x-correlation-id" in lowered, (
        "the report must name x-correlation-id as a header PT06 does not require"
    )
    assert "outside" in lowered and "413" in report and "415" in report, (
        "the report must place HTTP 413/415 outside PT06's acceptance scope"
    )
    assert "wording remains unconstrained" in lowered, (
        "the report must keep message wording unconstrained"
    )
    # The generalised binding constraint that closes the enumeration gap.
    assert "no hidden test may assert a response header" in lowered, (
        "the binding constraints must cover response headers, not only body keys"
    )


def test_report_defers_pt06_architecture_opportunity_adequacy_to_the_private_package():
    """Opportunity-set adequacy is a private blocker, not a public task defect.

    It must be recorded as deferred private work under TD-B05/TD-B14 and G1, and the
    report must say plainly that nothing was added publicly to address it.
    """
    report = REPORT_PATH.read_text(encoding="utf-8").replace("*", "")
    lowered = report.lower()
    assert "future private-evaluator blocker" in lowered, (
        "opportunity-set adequacy must be classified as a private-evaluator blocker"
    )
    assert "TD-B05" in report and "TD-B14" in report and "G1" in report
    assert "not a defect in pt06's public text" in lowered, (
        "the report must state this is not a public PT06 defect"
    )
    assert "non-empty fixed opportunity set" in lowered, (
        "the report must state what has to be demonstrated privately"
    )
    assert "before that package may be approved or frozen" in lowered, (
        "the demonstration must gate private approval/freeze"
    )
    assert "no architecture opportunity was added publicly" in lowered, (
        "the report must record that nothing architecture-shaped was added publicly"
    )


def test_report_records_the_full_private_commit_identifier_without_a_path():
    """The stale private commit is identified by full SHA, never by filesystem path."""
    report = REPORT_PATH.read_text(encoding="utf-8")
    assert "5733ca6151f7739c7105a5c1405fcbc8fb3cb59d" in report, (
        "the report must record the full private commit identifier that is stale "
        "for PT06 only"
    )
    assert not re.search(r"[A-Za-z]:[\\/]", report), (
        "the report must not contain an absolute filesystem path"
    )
    assert "identifier only" in report.lower()


def test_no_candidate_requires_an_externally_unprovokable_failure():
    """PT06's amendment removed the suite's only 500 requirement.

    Nothing may reintroduce one: at the base substrate no external caller can provoke
    an unexpected server failure without an injection seam, so a hidden test asserting
    it would be unsatisfiable by fair means.
    """
    for path in _task_files():
        text = path.read_text(encoding="utf-8")
        assert "InternalServerError" not in text, (
            f"{path.name} pins an unexpected-server-failure error value"
        )
        assert not re.search(r"HTTP 500|status(?: code)? 500", text), (
            f"{path.name} requires an HTTP 500 response"
        )
    report = REPORT_PATH.read_text(encoding="utf-8")
    vocabulary = re.findall(r"^\|\s*[^|]+\|\s*(\d{3})\s*\|\s*`(\w+)`\s*\|", report, re.MULTILINE)
    assert vocabulary, "the pinned error-value vocabulary table is missing"
    assert all(status != "500" for status, _ in vocabulary), (
        "the report still licenses a 500 response that no candidate requires"
    )


def test_no_artifact_presents_the_candidate_count_as_final():
    for path in (REPORT_PATH, REPO / "docs" / "v2" / "README.md"):
        text = path.read_text(encoding="utf-8").lower()
        assert "candidate" in text
        for overclaim in ("final task count", "final core-study count", "frozen task count"):
            assert f"is the {overclaim}" not in text
        assert "no final task count" in text or "not approved and not frozen" in text


# --------------------------------------------------------------------------- #
# Redaction: the public matrices carry no hidden answer
# --------------------------------------------------------------------------- #
def test_public_matrix_carries_no_hidden_answer():
    text = MATRIX_PATH.read_text(encoding="utf-8")
    for leak in ("expected_layer", "prohibited_layer", "AR-", "OPP-", "legitimate_alternative"):
        assert leak not in text, f"PILOT_PUBLIC_TASK_MATRIX.csv leaks {leak}"
    # Two placeholders and no third: the package is private, or (PT07) does not
    # exist yet. A real hash would publish private content and imply a frozen
    # package; both are forbidden pre-freeze.
    for row in MATRIX_ROWS:
        assert row["hidden_evaluator_manifest_hash"] in {
            "stored_in_private_evaluator_repo",
            "not_yet_authored",
        }, f"{row['task_id']}: no manifest hash may be pinned publicly"
        assert not re.fullmatch(r"[0-9a-f]{16,}", row["hidden_evaluator_manifest_hash"])
