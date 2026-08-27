"""Governance tests for `PT07`, the one task authored under DECISION B (`TD-B34`).

`PT07` — *Price a proposed order before it is placed* — is the public body of the
candidate that the functional-acceptance-boundary package had cleared for
authoring. This module asserts the properties that make authoring it a *legible,
bounded* act rather than a drift:

* its front matter validates against the public task schema, it is `primary`, and
  it carries the intended public eligibility (`scored`, meaning **intended for
  E1**, still PRE-FREEZE, still requiring a private evaluator package);
* its recorded SHA-256 is the hash of the bytes on disk;
* it contains no leakage, judged by the repository's own validator with the
  repository's own terms — neither is weakened here;
* every registry that must list every public task carries exactly one consistent
  `PT07` row;
* the eight pre-existing bodies and hashes are byte-identical, `PT05`/`PT06` are
  still `functional-only`, and `PR01`/`PR02` are still `inactive-reserve`;
* the public task count went up by exactly one;
* no private opportunity, forbidden target, manifest detail or expected
  implementation leaked into any public artifact for `PT07`;
* `PT07`'s contract stays inside the functional acceptance observation boundary —
  in particular it carries **no** non-persistence criterion, which was
  independently rejected as externally ungradeable;
* the model-visible substrate is untouched and the canonical substrate identity is
  unchanged;
* `DECISION B` / `TD-B34` is still **open and blocking**.

No `PT07` implementation is written or tested here, and no hidden acceptance is
implemented. Pure file and ``git`` inspection; no model is invoked and no
benchmark runs.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[4]
DOCS_V2 = REPO / "docs" / "v2"
PUBLIC_TASKS_DIR = REPO / "experiments" / "v2" / "tasks" / "public"
TASKS_DIR = REPO / "experiments" / "v2" / "tasks"

PT07_PATH = PUBLIC_TASKS_DIR / "PT07.md"
INDEX_PATH = PUBLIC_TASKS_DIR / "TASK_INDEX.csv"
REPORT_PATH = PUBLIC_TASKS_DIR / "TASK_AUTHORING_REPORT.md"
SCHEMA_YML = PUBLIC_TASKS_DIR / "TASK_SCHEMA.yml"
SCHEMA_JSON = REPO / "experiments" / "v2" / "schemas" / "public_task.schema.json"
MATRIX_PATH = DOCS_V2 / "PILOT_PUBLIC_TASK_MATRIX.csv"
ACCEPTANCE_MATRIX = DOCS_V2 / "TASK_ACCEPTANCE_MATRIX.csv"
LAYER_MATRIX = DOCS_V2 / "TASK_LAYER_MATRIX.csv"
RULE_MATRIX = DOCS_V2 / "TASK_RULE_MATRIX.csv"
RESET_MATRIX = DOCS_V2 / "RESET_CHECKPOINT_MATRIX.csv"
ORACLE_TRACE = DOCS_V2 / "ORACLE_TRACEABILITY.csv"
DECISIONS_CSV = DOCS_V2 / "OPEN_DECISIONS.csv"
SUBSTRATE_IDENTITY = DOCS_V2 / "SOURCE_SUBSTRATE_IDENTITY.md"

#: The canonical, experiment-neutral source substrate every condition shares.
CANONICAL_SUBSTRATE_COMMIT = "630d3180af0d02a86330dfb599f559e78df65e94"
CANONICAL_SUBSTRATE_CONTENT_HASH = (
    "0198d76c189f38589e872cab4305527c08e86ef736e1550e428e05f9178060f3"
)

PT07_SHA256 = "557caed09420354efbc823c8b72e54b0760ac72847aba0d9c07d99e37ff7d2d7"

#: Authored after `PT07`, under the same DECISION B, by a later package. Listed
#: apart so "authoring PT07 added exactly one body" stays a checkable claim about
#: the state at that package, while the current task set is still asserted exactly.
AUTHORED_AFTER_PT07 = {
    "PT08": "a31bb515b79cc1e211a662de2a8761c97082dd8bf266ee5b4f660981435badf2",
}

#: The eight bodies that existed before `PT07`. Authoring a task may not touch one.
PRE_EXISTING_HASHES = {
    "PT01": "6c938822fe19cd6e87942a6ee24ec8f604c0883da1b7f80d45216be35d7c9c39",
    "PT02": "ec4b60057708b20cb95e51f000671aab40afc8c55c0bc75850922a5f65841a77",
    "PT03": "cbfce1ca232cb9b6b53e0b4d202d6acee7415b50af8386c1f3bd2147089b4c21",
    "PT04": "f349b150b1d8fe5676fed8460b1840b988ee2bb0a78b1966ef82ae9ce9c8a9b5",
    "PT05": "f6efc772e76d6c287e0c71daaa93c7e1d9e62e72a1b37878df70113269ed27b3",
    "PT06": "3e0f84cfef1f9fbf97e3cd31b6704c3a0fb172b04b5e7bc33ea39927b1c8e0f2",
    "PR01": "0e1527bce41498836bb57b802d4566251d6fcfed4cca13fe59e6a97330f02302",
    "PR02": "e89a4aab236813c082f9152db779b8bbfb298148a51a8435a1e2bf38330caa83",
}

#: Every registry that must carry a row for every public task.
TASK_REGISTRIES = (
    INDEX_PATH,
    MATRIX_PATH,
    ACCEPTANCE_MATRIX,
    LAYER_MATRIX,
    RULE_MATRIX,
    RESET_MATRIX,
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _flat(path: Path) -> str:
    raw = _text(path).replace("*", "").replace("`", "")
    return re.sub(r"\s+", " ", raw).lower()


def _rows(path: Path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _by_id(path: Path, key: str = "task_id"):
    return {r[key]: r for r in _rows(path)}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _front_matter(path: Path) -> dict:
    lines = _text(path).splitlines()
    assert lines and lines[0].strip() == "---", f"{path.name} must start with front matter"
    end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    data = yaml.safe_load("\n".join(lines[1:end]))
    assert isinstance(data, dict), f"{path.name} front matter must be a mapping"
    return data


def _body(path: Path) -> str:
    lines = _text(path).splitlines(keepends=True)
    end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    return "".join(lines[end + 1 :])


def _task_files():
    return sorted(
        p
        for p in PUBLIC_TASKS_DIR.glob("*.md")
        if re.fullmatch(r"(?:PT|PR)\d{2}", p.stem)
    )


def _git(*args) -> str:
    return subprocess.run(
        ["git", *args], cwd=str(REPO), capture_output=True, text=True, check=True
    ).stdout.strip()


# --------------------------------------------------------------------------- 1
# The body exists, validates against the public schema, and is `primary`.


def test_pt07_exists_and_the_task_set_is_exactly_the_recorded_one():
    """`PT07` added exactly one body; every later body must be declared here too.

    A new task file that nobody recorded is drift, so the set is asserted exactly:
    the eight that predate `PT07`, `PT07` itself, and the bodies authored after it
    (`PT08`).
    """
    assert PT07_PATH.is_file(), "PT07.md was not authored"
    stems = {p.stem for p in _task_files()}
    assert stems == set(PRE_EXISTING_HASHES) | {"PT07"} | set(AUTHORED_AFTER_PT07), (
        f"the public task set drifted from the recorded one, found {sorted(stems)}"
    )


def test_pt07_front_matter_matches_the_public_schema():
    import context_audit as ca

    schema = json.loads(_text(SCHEMA_JSON))
    fm = _front_matter(PT07_PATH)
    errors = ca.validate_against_schema(fm, schema)
    assert errors == [], f"PT07 front-matter schema errors: {errors}"
    assert fm["id"] == "PT07"
    assert fm["title"] == "Price a proposed order before it is placed"
    assert fm["category"] == "pricing-endpoint"
    assert fm["status"] == "candidate"
    assert fm["visible_validation"] == "npm run ci:agent"
    # the schema stays closed: authoring a task may not add a hidden-answer field
    assert json.loads(_text(SCHEMA_JSON))["additionalProperties"] is False
    assert set(fm) <= {
        "id", "title", "category", "kind", "status", "visible_validation",
        "leakage_exceptions",
    }
    assert "leakage_exceptions" not in fm, "PT07 needs no reviewed leakage exception"


def test_pt07_is_a_primary_candidate_everywhere():
    assert _front_matter(PT07_PATH)["kind"] == "primary"
    assert _by_id(INDEX_PATH)["PT07"]["primary_or_reserve"] == "primary"
    assert _by_id(MATRIX_PATH)["PT07"]["primary_or_reserve"] == "primary"


def test_the_new_functional_category_is_shared_by_both_schema_files():
    yml_enum = yaml.safe_load(_text(SCHEMA_YML))["front_matter"]["category_enum"]
    js_enum = json.loads(_text(SCHEMA_JSON))["properties"]["category"]["enum"]
    assert "pricing-endpoint" in yml_enum
    assert "pricing-endpoint" in js_enum
    assert sorted(yml_enum) == sorted(js_enum), "the two category vocabularies drifted"


# --------------------------------------------------------------------------- 2
# The recorded hash is the hash of the bytes on disk.


def test_pt07_hash_is_correct_in_the_file_and_in_both_public_csvs():
    actual = _sha256(PT07_PATH)
    assert actual == PT07_SHA256, (
        f"PT07's body changed: pinned {PT07_SHA256[:16]}..., computed {actual[:16]}...; "
        "update the recorded hash deliberately and re-link any private package"
    )
    assert _by_id(INDEX_PATH)["PT07"]["public_task_sha256"] == PT07_SHA256
    assert _by_id(MATRIX_PATH)["PT07"]["public_task_sha256"] == PT07_SHA256


def test_pt07_body_is_lf_only_so_its_hash_is_platform_stable():
    assert b"\r\n" not in PT07_PATH.read_bytes(), "PT07.md contains CRLF"


# --------------------------------------------------------------------------- 3
# No leakage, judged by the repository's own validator and terms.


def test_pt07_passes_the_repository_leakage_validator_unweakened():
    sys.path.insert(0, str(TASKS_DIR))
    import validate_public_tasks as v  # noqa: WPS433

    terms = v.load_terms()
    # the validator's own term tiers must still be in force
    assert v.term_ids(terms, "hard_leak"), "the hard-leak tier was emptied"
    assert len(v.term_ids(terms, "review_required")) >= 7

    result = v.validate_task_file(PT07_PATH, terms)
    assert result.ok, (
        f"leakage in PT07: {[f.__dict__ for f in result.findings]} / {result.exception_errors}"
    )
    assert result.findings == [], (
        "PT07 must be clean outright, not clean by way of a reviewed exception"
    )
    # and it reconciles with the index, so it cannot hide from discovery
    assert v.reconcile_with_index(v.discover(TASKS_DIR), INDEX_PATH) == []


@pytest.mark.parametrize(
    "pattern",
    [
        r"\barchitectur",
        r"\bdependenc",
        r"\bboundar",
        r"\blayer",
        r"\bmodule",
        r"\bport\b",
        r"\badapter",
        r"\buse[- ]case",
        r"\brepositor",
        r"\bcore\b",
        r"\binfra",
        r"\bfeatures\b",
        r"\bcontracts?\b",
        r"@afci-bench/",
        r"\bAR-DEP",
        r"\bOPP-",
        r"\bhidden test",
        r"\bevaluator\b",
        r"\boracle\b",
        r"\bC[1-4]\b",
        r"\bAFCI\b",
        r"\bscored\b",
        r"\bapps/",
        r"\blibs/",
    ],
)
def test_pt07_body_carries_no_hidden_design_vocabulary(pattern):
    """A second, independent reading of the same prohibition.

    The validator above is the authority; this is a deliberately blunt re-check so
    a future edit to the terms file cannot silently make PT07 leaky.
    """
    hits = [m.group(0) for m in re.finditer(pattern, _text(PT07_PATH), re.IGNORECASE)]
    assert not hits, f"PT07 leaks {pattern!r}: {hits}"


# --------------------------------------------------------------------------- 4
# Public eligibility: intended for E1, PRE-FREEZE, private package still required.


def test_pt07_public_eligibility_is_scored_and_consistent():
    index = _by_id(INDEX_PATH)["PT07"]
    matrix = _by_id(MATRIX_PATH)["PT07"]
    assert index["e1_analysis_eligibility"] == "scored"
    assert matrix["e1_analysis_eligibility"] == "scored"
    assert index["task_status"] == matrix["task_status"] == "candidate"


def test_pt07_eligibility_reason_records_intent_not_a_demonstrated_denominator():
    """`scored` records INTENT. Four separate facts keep it from reading as more.

    The reason must state the approval that IS true and, independently, the three
    things that are still not: not frozen, G1 not passed, not run-eligible. Those
    are asserted apart from one another so recording the approval can never be the
    thing that relaxes the freeze statement (see test_private_state_reconciliation).
    """
    reason = _by_id(MATRIX_PATH)["PT07"]["e1_eligibility_reason"].lower()
    assert "intended for e1" in reason
    assert "pre-freeze" in reason
    assert "not_yet_frozen" in reason, (
        "the reason must say the private evaluator package is not frozen; it now "
        "exists, so 'not yet authored' would be stale"
    )
    # the package HAS been independently reviewed and approved - and that is not a
    # freeze, which the reason must say in the same breath
    assert "independently reviewed and approved" in reason, (
        "PT07's private package has been independently reviewed and approved; the "
        "reason must record it"
    )
    assert "not independently reviewed" not in reason, (
        "that claim is stale: the package HAS been independently reviewed"
    )
    assert "not a freeze" in reason and "not a gate pass" in reason, (
        "an approved package is not a frozen one; the reason must say so"
    )
    assert "gate g1 is not passed" in reason
    assert "not yet e1 run-eligible" in reason
    assert "not yet authored" not in reason, (
        "PT07's private package has been authored; that claim is stale"
    )
    assert "subject to private evaluator validation" in reason
    assert "explicit freeze of a non-zero frozen opportunity set" in reason
    assert "before any benchmark or model execution" in reason, (
        "the reason must record that authoring predates any run"
    )


def test_pt07_is_not_presented_as_frozen_or_as_carrying_an_opportunity():
    """The package now exists; what must stay false is that it is *frozen*.

    The registries previously said ``not_yet_authored``, which reconciliation
    against the private repository made stale. The invariant that still has to hold
    is the one that matters: no public row may present PT07 as frozen, and no
    public row may pin a rule, opportunity or expected area for it.
    """
    matrix = _by_id(MATRIX_PATH)["PT07"]
    assert matrix["hidden_evaluator_manifest_hash"] == "stored_in_private_evaluator_repo", (
        "the manifest hash stays withheld; publishing one would leak the frozen set"
    )
    assert matrix["task_status"] == "candidate"
    for path in (ACCEPTANCE_MATRIX, LAYER_MATRIX, RULE_MATRIX):
        row = _by_id(path)["PT07"]
        values = ",".join(row.values())
        assert "stored_in_private_evaluator_repo" in values, path.name
        assert "not_yet_authored" not in values, (
            f"{path.name}: PT07's private package exists; 'not_yet_authored' is stale"
        )
        assert row["status"] == "candidate-not-frozen", path.name
        assert "not_yet_frozen" in values.lower(), (
            f"{path.name}: the row must record that the package is not frozen"
        )


# --------------------------------------------------------------------------- 5
# Exactly one consistent PT07 row in every registry that must list every task.


@pytest.mark.parametrize("path", TASK_REGISTRIES, ids=lambda p: p.name)
def test_every_required_registry_has_exactly_one_pt07_row(path):
    ids = [r["task_id"] for r in _rows(path)]
    assert ids.count("PT07") == 1, f"{path.name} has {ids.count('PT07')} PT07 rows"


@pytest.mark.parametrize("path", TASK_REGISTRIES, ids=lambda p: p.name)
def test_every_required_registry_covers_every_public_task(path):
    listed = {r["task_id"] for r in _rows(path)}
    expected = {p.stem for p in _task_files()}
    assert expected <= listed, f"{path.name} is missing {sorted(expected - listed)}"


def test_the_index_and_the_public_matrix_agree_on_every_shared_pt07_column():
    index = _by_id(INDEX_PATH)["PT07"]
    matrix = _by_id(MATRIX_PATH)["PT07"]
    for column in set(index) & set(matrix):
        assert index[column] == matrix[column], f"PT07: {column} differs"


def test_the_authoring_report_inventory_carries_pt07():
    report = _text(REPORT_PATH)
    assert re.search(
        r"\|\s*PT07\s*\|\s*primary\s*\|\s*pricing-endpoint\s*\|\s*\w+\s*\|\s*"
        r"`557caed09420354e\.\.\.`\s*\|\s*scored\s*\|",
        report,
    ), "the public task inventory must carry a PT07 row"


def test_pt07_is_traceable_to_e1_as_an_intended_scored_candidate():
    trace = {r["oracle_id"]: r for r in _rows(ORACLE_TRACE)}
    viol = trace["OT-AC-VIOL"]
    assert "PT07" in viol["task_id"]
    assert viol["evaluator_type"] == "automated"
    private = trace["OT-TASKS-PRIVATE-SCORED"]
    assert "PT07" in private["task_id"]
    notes = private["notes"].lower()
    assert "no private evaluator package at all" not in notes, (
        "PT07's private package has been authored; that claim is stale"
    )
    assert "not independently reviewed" not in notes, (
        "that claim is stale: the package HAS been independently reviewed"
    )
    assert "independently reviewed and approved" in notes, (
        "the row must record the external independent approval of the package"
    )
    assert "not_yet_frozen" in notes, (
        "the row must record that the approved package is still not frozen"
    )
    assert "gate g1 not passed" in notes or "g1 not passed" in notes
    assert "package approval is not a freeze" in notes, (
        "approval and freeze are different facts; the row must not blur them"
    )
    assert "records intent only" in notes


# --------------------------------------------------------------------------- 6
# Nothing else moved.


@pytest.mark.parametrize("task_id", sorted(PRE_EXISTING_HASHES))
def test_no_pre_existing_task_body_or_hash_changed(task_id):
    path = PUBLIC_TASKS_DIR / f"{task_id}.md"
    expected = PRE_EXISTING_HASHES[task_id]
    assert _sha256(path) == expected, f"{task_id}.md changed while authoring PT07"
    assert _by_id(INDEX_PATH)[task_id]["public_task_sha256"] == expected
    assert _by_id(MATRIX_PATH)[task_id]["public_task_sha256"] == expected


def test_pt05_and_pt06_remain_functional_only():
    for task_id in ("PT05", "PT06"):
        assert _by_id(INDEX_PATH)[task_id]["e1_analysis_eligibility"] == "functional-only"
        assert _by_id(MATRIX_PATH)[task_id]["e1_analysis_eligibility"] == "functional-only"


def test_pr01_and_pr02_remain_inactive_reserve():
    for task_id in ("PR01", "PR02"):
        assert _by_id(INDEX_PATH)[task_id]["e1_analysis_eligibility"] == "inactive-reserve"
        assert _by_id(INDEX_PATH)[task_id]["primary_or_reserve"] == "reserve"
        assert _by_id(MATRIX_PATH)[task_id]["e1_analysis_eligibility"] == "inactive-reserve"
    report = _flat(REPORT_PATH)
    assert "no reserve was activated" in report


def test_authoring_pt07_raised_the_count_by_one_and_every_later_body_is_declared():
    """The count is pinned, and each increment has to be a deliberate authoring act.

    `PT07` took the suite from eight to nine. Each body authored afterwards is
    declared in :data:`AUTHORED_AFTER_PT07`, so the total is still exact and an
    undeclared body still fails.
    """
    expected = len(PRE_EXISTING_HASHES) + 1 + len(AUTHORED_AFTER_PT07)
    assert len(PRE_EXISTING_HASHES) + 1 == 9, "PT07 was the ninth body"
    assert len(_task_files()) == expected == 10
    assert len(_rows(INDEX_PATH)) == expected
    assert len({r["task_id"] for r in _rows(MATRIX_PATH)}) == expected
    for task_id, digest in AUTHORED_AFTER_PT07.items():
        assert _sha256(PUBLIC_TASKS_DIR / f"{task_id}.md") == digest, task_id
        assert _by_id(INDEX_PATH)[task_id]["public_task_sha256"] == digest


# --------------------------------------------------------------------------- 7
# No private opportunity information leaked for PT07.


RULE_OR_OPPORTUNITY = re.compile(r"\bAR-[A-Z]+-\d+|\bOPP-|PT07-(?:OPP|EXP)-")


def _clauses(text: str):
    """Split into the units a *binding* would have to live in.

    A public artifact may name the rule catalog and may name ``PT07``; what it may
    never do is put them in one statement. CSV cells are split out first (a row is
    one line but many independent fields), then both CSV cells and Markdown prose
    are split on sentence and clause boundaries, table pipes and line breaks.
    """
    for part in re.split(r"(?<=[.;:])\s+|\n|\|", text):
        part = part.strip()
        if part:
            yield part


def _binding_offences(path: Path):
    """Two ways a public artifact could bind ``PT07`` to a rule or opportunity.

    **Per-task row.** In a CSV whose rows are keyed by ``task_id``, a row that
    names ``PT07`` *and no other task* is that task's own mapping: no cell in it
    may carry a rule or opportunity id. This is the shape the private per-task
    mapping would take if it ever leaked into a public matrix.

    **Same statement.** Anywhere at all, a clause that names ``PT07`` may not also
    name a rule or opportunity id. This catches prose.

    A row that lists several tasks against the whole implemented leaf family is
    neither: the family enumeration is public catalog information that predates
    ``PT07``, and it asserts nothing about which rule ``PT07``'s own decision uses.
    """
    hits = []
    if path.suffix == ".csv":
        with open(path, newline="", encoding="utf-8") as fh:
            rows = [r for r in csv.reader(fh) if r]
        header = rows[0] if rows else []
        key = header.index("task_id") if "task_id" in header else None
        for row in rows[1:]:
            if key is not None and key < len(row):
                tasks = set(re.findall(r"\b(?:PT|PR)\d{2}\b", row[key]))
                if tasks == {"PT07"}:
                    hits += [
                        f"per-task row: {cell[:120]}"
                        for cell in row
                        if RULE_OR_OPPORTUNITY.search(cell)
                    ]
            cells = row
            hits += [
                f"same statement: {clause[:120]}"
                for cell in cells
                for clause in _clauses(cell)
                if "PT07" in clause and RULE_OR_OPPORTUNITY.search(clause)
            ]
        return hits
    return [
        f"same statement: {clause[:120]}"
        for clause in _clauses(_text(path))
        if "PT07" in clause and RULE_OR_OPPORTUNITY.search(clause)
    ]


def test_no_public_artifact_maps_pt07_to_a_rule_or_an_opportunity():
    """The per-task mapping is private for PT07 exactly as for every other task."""
    offenders = []
    for path in sorted(DOCS_V2.glob("*.csv")) + sorted(DOCS_V2.glob("*.md")) + [
        INDEX_PATH,
        REPORT_PATH,
        PT07_PATH,
    ]:
        offenders += [f"{path.name}: {hit}" for hit in _binding_offences(path)]
    assert not offenders, f"PT07 is publicly mapped to a rule or opportunity: {offenders}"


def test_that_mapping_sweep_would_actually_catch_a_binding(tmp_path):
    """Guard the guard: the rule must reject a real disclosure and pass the record.

    The public record legitimately enumerates the whole implemented leaf family as
    available boundary space, and separately says that ``PT07`` was authored. That
    must stay legal. Binding ``PT07`` to one rule must not.
    """
    bad = tmp_path / "bad.csv"
    bad.write_text("task_id,rule_id\nPT07,AR-DEP-005\n", encoding="utf-8")
    assert _binding_offences(bad), "a direct PT07 -> rule row must be caught"

    bad_md = tmp_path / "bad.md"
    bad_md.write_text("PT07 introduces an AR-DEP-005 decision.\n", encoding="utf-8")
    assert _binding_offences(bad_md), "a binding sentence must be caught"

    ok_md = tmp_path / "ok.md"
    ok_md.write_text(
        "Unused leaf relationships already exist (AR-DEP-002 ... AR-DEP-006). "
        "One new primary task, PT07, has now been authored.\n",
        encoding="utf-8",
    )
    assert not _binding_offences(ok_md), "the separated public record must stay legal"

    ok_csv = tmp_path / "ok.csv"
    ok_csv.write_text(
        "task_id,rule_or_criterion_id\n"
        "PT01;PT02;PT07,frozen opportunity ids (implemented leaves AR-DEP-002..006)\n",
        encoding="utf-8",
    )
    assert not _binding_offences(ok_csv), (
        "a multi-task roster against the whole implemented family is not a binding"
    )


def test_the_public_matrix_still_carries_no_hidden_answer():
    text = _text(MATRIX_PATH)
    for leak in ("expected_layer", "prohibited_layer", "AR-", "OPP-", "legitimate_alternative"):
        assert leak not in text, f"PILOT_PUBLIC_TASK_MATRIX.csv leaks {leak}"


def test_no_expected_or_violating_implementation_for_pt07_is_published():
    report = _flat(REPORT_PATH)
    for claim in (
        "did not publish pt07's hidden opportunity",
        "its forbidden target",
        "any expected violating implementation",
    ):
        assert claim in report, f"the report must record: {claim!r}"
    # and no reference solution exists anywhere in the public tree
    assert not list(PUBLIC_TASKS_DIR.glob("PT07*solution*"))
    assert not list((REPO / "experiments" / "v2").rglob("*pt07*acceptance*"))


# --------------------------------------------------------------------------- 8
# PT07 stays inside the functional acceptance observation boundary.


def test_pt07_requires_no_seam_no_internal_state_and_no_reset_helper():
    # The substrate's persistence internals are taken from the boundary module
    # rather than spelled out here: that module forbids those symbols appearing in
    # any code outside the substrate, and quoting them would make this file an
    # exception to the rule it is checking.
    from test_functional_acceptance_boundary import PERSISTENCE_INTERNALS  # noqa: WPS433

    body = _body(PT07_PATH)
    for forbidden in ("LogOutput", "createApp", *PERSISTENCE_INTERNALS):
        assert forbidden not in body, f"PT07 names an application internal: {forbidden}"
    flat = re.sub(r"\s+", " ", body).lower()
    assert "log output is not part of this task's required behaviour" in flat, (
        "PT07 must state that log output is outside it, so no seam is implied"
    )
    assert "no response header is part of this task's required behaviour" in flat


def test_pt07_states_no_non_persistence_criterion():
    """The rejected criterion must not have crept back in.

    "Previewing does not persist / creates no internal state / leaves the stored
    order count unchanged" is not externally observable at this substrate, so it
    was rejected. What PT07 requires is the observable consequence: the absent
    response fields.
    """
    flat = re.sub(r"\s+", " ", _body(PT07_PATH)).lower()
    for banned in (
        "does not persist",
        "must not persist",
        "not be persisted",
        "does not save",
        "must not save",
        "no internal state",
        "internal state",
        "order count",
        "number of stored orders",
        "leaves the stored",
        "side effect",
    ):
        assert banned not in flat, f"PT07 states a non-persistence criterion: {banned!r}"
    # ...and the observable requirement that replaces it IS present
    assert "no `id`, no `status`, no `createdat` and no `customerid`" in flat or (
        "no `id`, no `status`, no `createdat`" in flat
    ), "PT07 must require that the answer omits the created-order fields"


def test_the_boundary_audit_records_pt07_as_http_only():
    boundary = re.sub(r"\s+", " ", _text(DOCS_V2 / "HIDDEN_EVALUATOR_BOUNDARY.md"))
    assert re.search(r"\|\s*`PT07`\s*\|\s*HTTP only\s*\|", boundary), (
        "the boundary audit must carry a PT07 row stating HTTP only"
    )
    assert "rejected as externally ungradeable" in boundary
    # the declared seam register is unchanged: PT04's sink is still the only seam
    assert "No other seam is declared" in boundary


def test_the_report_records_the_rejected_criterion_and_the_overlap_guards():
    report = _flat(REPORT_PATH)
    assert "rejected as externally ungradeable" in report
    assert "an assertion about hidden persistence side effects is not" in report
    for guard in (
        "introduces no new discount rule",          # PT05
        "introduces no cent-exactness requirement",  # PR01
        "explicitly outside pt07",                   # PT06
        "adds no order read, list or count surface",  # PT01/PT02
        "logging is outside pt07",                   # PT04
    ):
        assert guard in report, f"the overlap guard is not recorded: {guard!r}"
    assert "deliberately not in the task body" in report


def test_the_reset_checkpoint_row_is_functional_and_claims_no_implementation():
    row = _by_id(RESET_MATRIX)["PT07"]
    assert row["condition_neutral"] == "yes"
    assert row["status"].strip().upper() == "TODO"
    definition = row["checkpoint_definition"].lower()
    assert "withheld" in definition
    assert "not yet drafted" in definition, (
        "the row must not imply that a private reset predicate already exists"
    )
    assert "must not rely on any assertion about internal persistence" in definition
    for leak in ("AR-", "OPP-", "expected_layer", "prohibited_layer"):
        assert leak not in _text(RESET_MATRIX), f"RESET_CHECKPOINT_MATRIX.csv leaks {leak}"


# --------------------------------------------------------------------------- 9
# The substrate and the protocol state are untouched.


def test_no_model_visible_substrate_file_changed_since_the_canonical_substrate():
    changed = _git("diff", "--name-only", CANONICAL_SUBSTRATE_COMMIT, "HEAD").splitlines()
    substrate = [p for p in changed if p.startswith("apps/") or p.startswith("libs/")]
    assert not substrate, f"authoring PT07 touched the shared substrate: {substrate}"


def test_the_canonical_substrate_identity_is_unchanged():
    identity = _text(SUBSTRATE_IDENTITY)
    assert CANONICAL_SUBSTRATE_COMMIT in identity
    assert CANONICAL_SUBSTRATE_CONTENT_HASH in identity


def test_no_benchmark_result_or_model_run_accompanies_this_package():
    results = REPO / "experiments" / "v2" / "results"
    stray = [p.name for p in results.rglob("*") if p.is_file() and p.name != "README.md"]
    assert not stray, f"a result artifact appeared: {stray}"


def test_the_protocol_is_still_pre_freeze():
    assert "PRE-FREEZE DRAFT" in _text(DOCS_V2 / "README.md")
    assert "PRE-FREEZE" in _text(REPORT_PATH)


# --------------------------------------------------------------------------- 10
# DECISION B is advanced, not discharged.


def test_decision_b_records_pt07_and_stays_open_and_blocking():
    row = _by_id(DECISIONS_CSV, key="decision_id")["TD-B34"]
    assert row["blocking"] == "yes"
    assert row["status"].strip().lower() == "open", (
        "one authored task does not resolve DECISION B"
    )
    text = row["decision"].lower()
    assert "progress (not resolution)" in text
    assert "pt07" in text
    assert "further candidate authoring is still required" in text
    assert "no power simulation may run yet" in text


def test_the_report_does_not_declare_the_suite_ready():
    report = _flat(REPORT_PATH)
    assert "td-b34 is not resolved by this package" in report
    assert "further candidate authoring is still required" in report
    assert "no power simulation should be run yet" in report
    assert "the suite is not ready" in report or "is not ready" in report


#: Blockers closed by packages unrelated to task authoring: the two substrate
#: leakage remediations, the experiment-awareness remediation, and the private
#: opportunity migration whose two residuals both completed (TD-B40). None was
#: closed by authoring a task, and TD-B40's closure in particular freezes nothing
#: and passes no gate.
CLOSED_BY_UNRELATED_PACKAGES = {"TD-B23", "TD-B24", "TD-B38", "TD-B40"}


def test_no_blocker_was_closed_while_authoring_pt07():
    closed = {
        r["decision_id"]
        for r in _rows(DECISIONS_CSV)
        if r["status"].strip().lower() != "open"
    }
    assert closed == CLOSED_BY_UNRELATED_PACKAGES, (
        "authoring a task closed a blocker: "
        f"{sorted(closed - CLOSED_BY_UNRELATED_PACKAGES)}"
    )
    # The blockers that authoring PT07 must never close, asserted by name.
    by_id = {r["decision_id"]: r for r in _rows(DECISIONS_CSV)}
    for still_open in ("TD-B34", "TD-B37", "TD-B39", "TD-B05", "TD-B14", "TD-B32"):
        assert by_id[still_open]["status"].strip().lower() == "open", (
            f"{still_open} must remain open after PT07 authoring"
        )
