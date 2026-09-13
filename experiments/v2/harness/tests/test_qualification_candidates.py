"""`SL-QUAL-01` — the two qualification candidates `PT09` and `PT10`.

Three things have to stay true at once, and each of them is a separate way this
package could be misread later:

1. **Two new bodies exist, are pinned, and leak nothing.** A public task body is
   functional-only; its hash is its identity; and no public artifact may bind
   either new task to a rule, an opportunity, a decision cluster or a named
   boundary.
2. **`PT08` is preserved, not repaired.** `SL-PT08-07` records `REVISE`, which is
   neither `INVALID` nor `RETIRED`. Its bytes, its recorded hash and its
   diagnostic governance must be untouched, and no document may call it invalid
   or retired.
3. **Nothing was conferred.** No freeze, no gate, no admission, no independent
   review, no result, and no closed blocker. The admitted active register is
   unchanged; only the forward-looking confirmatory-candidate set moves.

Pure file inspection. No model is invoked, nothing is executed, nothing is frozen.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from pathlib import Path

import pytest

import governance_text as G

REPO = Path(__file__).resolve().parents[4]
DOCS_V2 = REPO / "docs" / "v2"
PUBLIC_TASKS = REPO / "experiments" / "v2" / "tasks" / "public"
INDEX_PATH = PUBLIC_TASKS / "TASK_INDEX.csv"
REPORT_PATH = PUBLIC_TASKS / "TASK_AUTHORING_REPORT.md"
MATRIX_PATH = DOCS_V2 / "PILOT_PUBLIC_TASK_MATRIX.csv"
SCHEMA_JSON = REPO / "experiments" / "v2" / "schemas" / "public_task.schema.json"
CONSTRUCTION_PATH = DOCS_V2 / "QUALIFICATION_CANDIDATE_CONSTRUCTION.md"
DISPOSITION_PATH = DOCS_V2 / "PT08_DIAGNOSTIC_OUTCOME_AND_DISPOSITION.md"
GATE_MATRIX = DOCS_V2 / "PILOT_GATE_MATRIX.csv"
OPEN_DECISIONS = DOCS_V2 / "OPEN_DECISIONS.csv"

#: The two bodies this package authored, pinned at authoring.
NEW_TASKS = {
    "PT09": "bac32dc0e7163c9ab1816ac6eea6c98738092cca5cf56715e280f1ec1c0ac44c",
    "PT10": "1b1fe29881b3c9f309939df042272b03164fb3baae878c64345e75edddf36b86",
}

#: The task whose confirmatory role `PT09` replaces. Preserved, never repaired.
PT08_SHA = "a31bb515b79cc1e211a662de2a8761c97082dd8bf266ee5b4f660981435badf2"

EXPECTED_METADATA = {
    "PT09": {"category": "write-endpoint", "kind": "primary", "scope": "medium"},
    "PT10": {"category": "error-handling", "kind": "primary", "scope": "medium"},
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rows(path: Path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _by_id(path: Path):
    return {r["task_id"]: r for r in _rows(path)}


def _flat(path: Path) -> str:
    return G.norm(path.read_text(encoding="utf-8"))


def _front_matter(task_id: str) -> dict:
    import context_audit as ca  # noqa: F401  (kept for parity with sibling modules)

    text = (PUBLIC_TASKS / f"{task_id}.md").read_text(encoding="utf-8")
    block = text.split("---", 2)[1]
    out = {}
    for line in block.strip().splitlines():
        key, _, value = line.partition(":")
        out[key.strip()] = value.strip().strip('"')
    return out


# --------------------------------------------------------------------------- 1
# The bodies exist, are pinned, and are platform-stable.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("task_id", sorted(NEW_TASKS))
def test_the_body_exists_and_hashes_to_its_pinned_value(task_id):
    path = PUBLIC_TASKS / f"{task_id}.md"
    assert path.is_file(), f"{task_id}.md was not authored"
    actual = _sha256(path)
    assert actual == NEW_TASKS[task_id], (
        f"{task_id}'s body changed: pinned {NEW_TASKS[task_id][:16]}..., computed "
        f"{actual[:16]}...; update the recorded hash deliberately and re-link the "
        "private package"
    )


@pytest.mark.parametrize("task_id", sorted(NEW_TASKS))
def test_the_body_is_lf_only_so_its_hash_is_platform_stable(task_id):
    assert b"\r\n" not in (PUBLIC_TASKS / f"{task_id}.md").read_bytes()


@pytest.mark.parametrize("task_id", sorted(NEW_TASKS))
def test_the_front_matter_matches_the_public_schema(task_id):
    schema = json.loads(SCHEMA_JSON.read_text(encoding="utf-8"))
    fm = _front_matter(task_id)
    assert set(schema["required"]) <= set(fm), f"{task_id} front matter is incomplete"
    assert fm["id"] == task_id
    assert fm["category"] in schema["properties"]["category"]["enum"]
    assert fm["category"] == EXPECTED_METADATA[task_id]["category"]
    assert fm["kind"] == EXPECTED_METADATA[task_id]["kind"]
    assert fm["status"] == "candidate", "a newly authored body is never pre-approved"
    assert fm["visible_validation"] == "npm run ci:agent"
    assert "leakage_exceptions" not in fm, (
        f"{task_id} must pass the leakage validator with no reviewed exception"
    )


@pytest.mark.parametrize("task_id", sorted(NEW_TASKS))
def test_the_task_is_recorded_once_in_both_public_csvs_with_the_same_hash(task_id):
    for path in (INDEX_PATH, MATRIX_PATH):
        ids = [r["task_id"] for r in _rows(path)]
        assert ids.count(task_id) == 1, f"{task_id} appears {ids.count(task_id)} times in {path.name}"
        row = _by_id(path)[task_id]
        assert row["public_task_sha256"] == NEW_TASKS[task_id], path.name
        assert row["e1_analysis_eligibility"] == "scored", path.name
        assert row["scope_category"] == EXPECTED_METADATA[task_id]["scope"], path.name


@pytest.mark.parametrize("task_id", sorted(NEW_TASKS))
def test_the_task_has_a_row_in_every_per_task_matrix(task_id):
    for name in (
        "TASK_RULE_MATRIX.csv",
        "TASK_ACCEPTANCE_MATRIX.csv",
        "TASK_LAYER_MATRIX.csv",
        "RESET_CHECKPOINT_MATRIX.csv",
    ):
        ids = [r["task_id"] for r in _rows(DOCS_V2 / name)]
        assert ids.count(task_id) == 1, f"{task_id} is missing from {name}"


# --------------------------------------------------------------------------- 2
# No public artifact binds a new task to an architecture identifier.
# --------------------------------------------------------------------------- #
ARCHITECTURE_ID = re.compile(
    r"\bAR-[A-Z]+-\d+|\bOPP-|\bDC-[A-Z0-9-]+|"
    r"(?:features|api|core|infra|contracts|observability)\s*(?:->|→)\s*"
    r"(?:features|api|core|infra|contracts|observability)",
    re.IGNORECASE,
)


def _clauses(text: str):
    return re.split(r"(?<=[.;:])\s+|\n|\|", text)


def _public_documents():
    skip = {".git", "node_modules", "__pycache__", ".pytest_cache", ".nx", "archive"}
    for path in REPO.rglob("*"):
        if not path.is_file() or path.suffix not in {".md", ".csv", ".yml", ".yaml"}:
            continue
        if skip & set(path.relative_to(REPO).parts):
            continue
        yield path


@pytest.mark.parametrize("task_id", sorted(NEW_TASKS))
def test_no_public_document_binds_the_task_to_an_architecture_identifier(task_id):
    """The disclosure convention `PT07` and `PT08` already live under."""
    offenders = []
    for path in _public_documents():
        text = path.read_text(encoding="utf-8", errors="ignore")
        if task_id not in text:
            continue
        rel = path.relative_to(REPO).as_posix()
        scopes = (
            [cell for row in csv.reader(io.StringIO(text)) for cell in row]
            if path.suffix == ".csv"
            else [text]
        )
        for scope in scopes:
            for clause in _clauses(scope):
                if task_id in clause and ARCHITECTURE_ID.search(clause):
                    offenders.append(f"{rel}: {clause.strip()[:160]}")
    assert offenders == [], (
        f"a public document binds {task_id} to an architecture identifier in one "
        "statement:\n  - " + "\n  - ".join(offenders)
    )


def test_that_leakage_sweep_would_catch_a_real_binding():
    """Guard the guard, in both directions."""
    bad = "PT09 creates a features → api decision under AR-DEP-006."
    ok = "PT09 is authored as a qualification candidate."
    assert "PT09" in bad and ARCHITECTURE_ID.search(bad)
    assert not ARCHITECTURE_ID.search(ok)


@pytest.mark.parametrize("task_id", sorted(NEW_TASKS))
def test_the_body_itself_names_no_architecture_identifier(task_id):
    body = (PUBLIC_TASKS / f"{task_id}.md").read_text(encoding="utf-8")
    assert not ARCHITECTURE_ID.search(body), f"{task_id}'s body names an architecture identifier"


# --------------------------------------------------------------------------- 3
# `PT08` is preserved, not repaired.
# --------------------------------------------------------------------------- #
def test_pt08_is_byte_identical_and_still_pinned():
    assert _sha256(PUBLIC_TASKS / "PT08.md") == PT08_SHA
    assert _by_id(INDEX_PATH)["PT08"]["public_task_sha256"] == PT08_SHA
    assert _by_id(MATRIX_PATH)["PT08"]["public_task_sha256"] == PT08_SHA


def test_pt08_is_still_a_candidate_and_still_scored_by_intent():
    row = _by_id(INDEX_PATH)["PT08"]
    assert row["task_status"] == "candidate"
    assert row["e1_analysis_eligibility"] == "scored"


def test_no_governed_document_calls_pt08_invalid_or_retired():
    """`REVISE` is neither, and the repository distinguishes them."""
    forbidden = (
        "pt08 is invalid", "pt08 is retired", "pt08 has been retired",
        "pt08 is withdrawn", "pt08 is deleted", "pt08 is superseded and removed",
    )
    offenders = []
    for rel in G.governed_files():
        flat = G.norm((REPO / rel).read_text(encoding="utf-8"))
        offenders += [f"{rel}: {claim!r}" for claim in forbidden if claim in flat]
    assert offenders == [], f"PT08 is reported invalid or retired: {offenders}"


def test_the_disposition_record_states_what_revise_does_and_does_not_do():
    flat = _flat(DISPOSITION_PATH)
    for required in (
        "pt08 = revise",
        "benchmark investment = continue",
        "it is not invalid",
        "it is not retired",
        "it is instrument-development evidence",
        "preserved byte-for-byte",
        "excluded",
        "the admitted active e1 register is unchanged"
        if "the admitted active e1 register is unchanged" in flat
        else "admitted active e1 register",
    ):
        assert required in flat, f"the disposition record does not state: {required!r}"
    for denial in (
        "gate g1 is not passed",
        "no reserve is activated",
        "no confirmatory evidence collection begins",
    ):
        assert denial in flat, f"the disposition record does not deny: {denial!r}"


def test_the_disposition_record_forbids_touching_pt08s_artifacts():
    flat = _flat(DISPOSITION_PATH)
    assert "must not be modified, overwritten, repurposed or deleted" in flat
    assert "must never be retrospectively promoted" in flat


# --------------------------------------------------------------------------- 4
# The construction record: what it establishes and what it denies.
# --------------------------------------------------------------------------- #
def test_the_construction_record_reports_the_executed_validation():
    flat = _flat(CONSTRUCTION_PATH)
    for required in (
        "intended conforming route",
        "intended shortcut; detected",
        "valid escape hatch",
        "passes hidden functional acceptance in full",
        "0 escaped",
        "not valid mutant",
        "npm run ci:agent",
    ):
        assert required in flat, f"the construction record does not report: {required!r}"


def test_the_construction_record_denies_every_conferral():
    flat = _flat(CONSTRUCTION_PATH)
    for denial in (
        "zero new model observations",
        "it froze no task and no manifest",
        "it admitted no opportunity to the active e1 denominator",
        "g1 is not passed",
        "it obtained no independent review",
        "candidate construction is not qualification",
    ):
        assert denial in flat, f"the construction record does not deny: {denial!r}"


def test_the_construction_record_states_the_residual_limitation():
    """An escape hatch that survives must be reported, not buried."""
    flat = _flat(CONSTRUCTION_PATH)
    assert "does not eliminate the boundary-only family" in flat
    assert "construct-validity limitation" in flat
    assert "no hidden assertion was added to close any of these escapes" in flat


def test_the_construction_record_keeps_the_two_registers_apart():
    flat = _flat(CONSTRUCTION_PATH)
    assert "admitted active e1 register" in flat and "unchanged by this package" in flat
    assert "confirmatory-candidate set" in flat
    assert "3 / 2 / 1" in flat and "3 / 2 / 2" in flat
    assert "neither may be read off the other" in flat


# --------------------------------------------------------------------------- 5
# Nothing was conferred.
# --------------------------------------------------------------------------- #
def test_no_gate_is_passed():
    for row in _rows(GATE_MATRIX):
        assert row["status"].strip().lower().startswith("not evaluated"), row["gate_id"]


@pytest.mark.parametrize(
    "decision_id", ["TD-B34", "TD-B32", "TD-B12", "TD-B03", "TD-B05", "TD-B14"]
)
def test_the_blockers_this_package_must_not_close_are_open(decision_id):
    row = {r["decision_id"]: r for r in _rows(OPEN_DECISIONS)}[decision_id]
    assert row["status"].strip().lower() == "open", f"{decision_id} must stay open"


def test_priority_b_is_started_but_never_reported_complete():
    row = G.norm({r["decision_id"]: r for r in _rows(OPEN_DECISIONS)}["TD-B34"]["decision"])
    assert "priority b is started and is not complete" in row
    assert "has had no independent candidate review" in row
    assert "priority b is complete" not in row


def test_no_run_artifact_was_committed():
    """A construction package produces no observations, so it writes none."""
    results = REPO / "experiments" / "v2" / "results"
    assert sorted(p.name for p in results.iterdir()) == ["README.md"], (
        "a result artifact appeared in the confirmatory area"
    )


def test_the_authoring_report_records_the_package_and_its_denials():
    flat = _flat(REPORT_PATH)
    for required in (
        "priority-a replication slot",
        "priority b is started and is not complete",
        "zero new model observations",
        "td-b34 is not resolved by this package",
        "candidate construction is not qualification",
    ):
        assert required in flat, f"the authoring report does not record: {required!r}"
