"""Tests for the public-task leakage validator.

Covers Part E of the pre-execution design-review reconciliation (a functional
task passes; obvious and subtle leakage fail; architecture hints in acceptance
criteria fail; a justified exception passes; an unjustified exception fails;
v1/v0 tasks are never scanned) plus the hardening required by the independent
public review of the pilot task package:

* ``D1`` — front-matter values and keys are scanned (they are not safe just for
  being YAML);
* ``D2`` — hard-leak phrases split across a hard line break are detected;
* ``D3`` — every prohibited leakage family is covered, not only architecture
  words: prescribed repository paths, source filenames, hidden-test clues,
  reset/checkpoint clues, condition names, opportunity/rule ids,
  evaluator/oracle clues, expected implementations, legitimate alternatives, and
  required/prohibited placement;
* ``D4`` — recursive discovery, an explicit extension allowlist, rejection of
  task-like files with unsupported extensions, and TASK_INDEX.csv reconciliation;
* ``D5`` — exceptions must carry pattern id, exact location, justification,
  reviewer and approval state, and fail closed otherwise.

Each ``test_regression_*`` reproduces a bypass that the independent review
demonstrated against the previous validator. Pure file inspection; no model is
invoked.
"""
from pathlib import Path

import pytest

import validate_public_tasks as v

TERMS = v.load_terms()
REPO = Path(__file__).resolve().parents[4]
TASKS_DIR = REPO / "experiments" / "v2" / "tasks"
INDEX_PATH = TASKS_DIR / "public" / "TASK_INDEX.csv"
EXPECTED_TASKS = {f"PT0{i}.md" for i in range(1, 7)} | {"PR01.md", "PR02.md"}


def check(text: str) -> v.TaskValidation:
    return v.validate_task_text(text, TERMS)


def hard_ids(result: v.TaskValidation) -> set:
    return {f.term_id for f in result.hard_leaks}


# --------------------------------------------------------------------------- #
# 1. functional-only task passes
# --------------------------------------------------------------------------- #
FUNCTIONAL_ONLY = """# Task: Retrieve an order by id

Implement an endpoint that returns a single order by its id.

- When the order exists, respond with HTTP 200 and the order as JSON.
- When no order matches the id, respond with HTTP 404 and an error message.
- The response must include the order total computed from its items.

## Acceptance criteria
- Requesting an existing id returns the order with the correct total.
- Requesting an unknown id returns HTTP 404.
"""


def test_functional_only_task_passes():
    result = check(FUNCTIONAL_ONLY)
    assert result.ok, [f.__dict__ for f in result.findings]
    assert result.findings == []


# --------------------------------------------------------------------------- #
# 2. obvious leakage fails
# --------------------------------------------------------------------------- #
def test_obvious_leakage_fails():
    text = (
        "# Task: Add cancellation\n\n"
        "Cancel an order. Follow the MAD and respect the existing module boundaries.\n"
    )
    result = check(text)
    assert not result.ok
    assert "HL-MAD" in hard_ids(result)
    assert "HL-BOUNDARIES" in hard_ids(result)


# --------------------------------------------------------------------------- #
# 3. subtle leakage fails
# --------------------------------------------------------------------------- #
def test_subtle_leakage_fails():
    text = (
        "# Task: Add a repository port\n\n"
        "Add the new repository port to the contracts layer and keep the "
        "dependency direction inward.\n"
    )
    result = check(text)
    assert not result.ok
    assert "HL-DEP-DIRECTION" in hard_ids(result)
    assert "HL-LAYER-PRESCRIPTIVE" in hard_ids(result)


# --------------------------------------------------------------------------- #
# 4. architecture hints in acceptance criteria fail
# --------------------------------------------------------------------------- #
def test_architecture_hint_in_acceptance_criteria_fails():
    text = (
        "# Task: Move validation\n\n"
        "Move the validation helper so it can be reused.\n\n"
        "## Acceptance criteria\n"
        "- The core module must not import from the features module.\n"
        "- Existing tests still pass.\n"
    )
    result = check(text)
    assert not result.ok
    assert "HL-DEP-DIRECTION" in hard_ids(result)
    assert any("import" in f.line_text.lower() for f in result.hard_leaks)


# --------------------------------------------------------------------------- #
# 5. D5 — exception governance
# --------------------------------------------------------------------------- #
APPROVED_EXCEPTION = """---
id: PT99
title: "Speed up repeated lookups"
leakage_exceptions:
  - id: RR-LAYER
    location: "body:14"
    match: "caching layer"
    justification: "Refers to a functional in-memory caching layer for repeated lookups, not a repository architecture layer."
    reviewer: "oracle-designer"
    approved: true
---
# Task: Speed up repeated lookups

Add an in-memory caching layer so repeated lookups of the same id are fast.

## Acceptance criteria
- A second lookup of the same id does not recompute the result.
"""


def test_approved_exception_passes():
    result = check(APPROVED_EXCEPTION)
    assert result.hard_leaks == []
    assert result.exception_errors == []
    layer_findings = [f for f in result.findings if f.term_id == "RR-LAYER"]
    assert layer_findings and all(f.covered for f in layer_findings)
    assert result.ok


def test_exception_without_approval_fails_closed():
    text = APPROVED_EXCEPTION.replace("approved: true", "approved: false")
    result = check(text)
    assert not result.ok
    assert any("not approved" in e for e in result.exception_errors)
    assert result.uncovered_reviews


def test_exception_without_location_fails_closed():
    text = APPROVED_EXCEPTION.replace('    location: "body:14"\n', "")
    result = check(text)
    assert not result.ok
    assert any("no exact location" in e for e in result.exception_errors)
    assert result.uncovered_reviews


def test_exception_with_wrong_location_does_not_cover():
    text = APPROVED_EXCEPTION.replace('location: "body:14"', 'location: "body:999"')
    result = check(text)
    assert not result.ok
    assert result.exception_errors == []
    assert result.uncovered_reviews, "an exception must not cover a finding elsewhere"


def test_unjustified_exception_fails():
    text = APPROVED_EXCEPTION.replace(
        '    justification: "Refers to a functional in-memory caching layer for repeated lookups, not a repository architecture layer."\n',
        '    justification: ""\n',
    )
    result = check(text)
    assert not result.ok
    assert any("justification" in e for e in result.exception_errors)


def test_exception_without_reviewer_fails():
    text = APPROVED_EXCEPTION.replace('    reviewer: "oracle-designer"\n', '    reviewer: ""\n')
    result = check(text)
    assert not result.ok
    assert any("reviewer" in e for e in result.exception_errors)


def test_exception_cannot_cover_a_hard_leak():
    text = """---
id: PT98
leakage_exceptions:
  - id: HL-MAD
    location: "body:8"
    justification: "we really want to mention the MAD"
    reviewer: "someone"
    approved: true
---
# Task: Do the thing

Follow the MAD exactly.
"""
    result = check(text)
    assert not result.ok
    assert any("hard-leak" in e for e in result.exception_errors)
    assert "HL-MAD" in hard_ids(result)


# --------------------------------------------------------------------------- #
# REGRESSION D1 — front matter is scanned
# --------------------------------------------------------------------------- #
FRONT_MATTER_LEAK = """---
id: PT97
title: "Add the repository port to the contracts layer; core must not import infra"
category: read-endpoint
kind: primary
status: candidate
visible_validation: "npm run ci:agent"
notes_for_reviewer: "Follow the MAD. The port must live in libs/contracts."
---

## Objective

Return an order by its id.
"""


def test_regression_front_matter_hard_leak_is_detected():
    """Previously: front matter was never scanned, so this returned ok=True with
    zero findings."""
    result = check(FRONT_MATTER_LEAK)
    assert not result.ok, "front-matter leakage must fail"
    ids = hard_ids(result)
    assert "HL-MAD" in ids
    assert "HL-DEP-DIRECTION" in ids
    assert "HL-REPO-PATH" in ids
    assert all(f.location.startswith("front-matter:") for f in result.hard_leaks)


def test_front_matter_nested_and_list_values_are_scanned():
    text = """---
id: PT96
title: "Return an order"
review_notes:
  - "harmless note"
  - "second note: keep the domain layer free of infrastructure imports"
meta:
  inner:
    hint: "Follow the MAD."
---

## Objective

Return an order by its id.
"""
    result = check(text)
    assert not result.ok
    assert "HL-MAD" in hard_ids(result)
    assert any("review_notes[1]" in f.location for f in result.findings)
    assert any("meta.inner.hint" in f.location for f in result.hard_leaks)


def test_exception_justification_text_is_not_itself_scanned():
    """A justification must be able to quote the term it excepts."""
    result = check(APPROVED_EXCEPTION)
    assert not any("leakage_exceptions" in f.location for f in result.findings)


# --------------------------------------------------------------------------- #
# REGRESSION D2 — hard-wrapped leakage
# --------------------------------------------------------------------------- #
def test_regression_wrapped_dependency_direction_is_detected():
    """Previously: 'must not' / 'import' split across a hard line break escaped
    the hard-leak tier entirely."""
    text = """---
id: PT95
---

## Constraints

- The order-reading helper must not
  import the storage implementation directly.
"""
    result = check(text)
    assert not result.ok
    assert "HL-DEP-DIRECTION" in hard_ids(result)
    assert any(f.wrapped for f in result.hard_leaks)


def test_regression_wrapped_may_only_depend_is_detected():
    text = """---
id: PT94
---

## Constraints

- The domain code may only
  depend on the shared types package.
"""
    result = check(text)
    assert not result.ok
    assert "HL-DEP-DIRECTION" in hard_ids(result)


def test_same_phrase_on_one_line_is_still_detected():
    text = (
        "---\nid: PT93\n---\n\n"
        "- The helper must not import the storage implementation directly.\n"
    )
    result = check(text)
    assert "HL-DEP-DIRECTION" in hard_ids(result)
    assert not any(f.wrapped for f in result.hard_leaks), "single-line match is not 'wrapped'"


def test_normalisation_does_not_glue_unrelated_paragraphs():
    """Two separate paragraphs must not be joined into one logical unit, or the
    validator would invent phrases nobody wrote."""
    text = """---
id: PT92
---

## Objective

The reader must not
fail when the order is absent.

Import the order total from the response body when displaying it.
"""
    result = check(text)
    assert "HL-DEP-DIRECTION" not in hard_ids(result), (
        "'must not' and 'import' are in different paragraphs and must not be joined"
    )


def test_normalisation_does_not_glue_separate_list_items():
    text = """---
id: PT91
---

- The response must not
- import anything
"""
    result = check(text)
    assert "HL-DEP-DIRECTION" not in hard_ids(result)


def test_logical_units_preserve_section_boundaries():
    body = "para one line one\npara one line two\n\n## Heading\n\n- item one\n  continued\n"
    units = v.logical_units(body, 1)
    texts = [u.text for u in units]
    assert "para one line one para one line two" in texts
    assert "## Heading" in texts
    assert "- item one continued" in texts


# --------------------------------------------------------------------------- #
# REGRESSION D3 — every prohibited leakage family
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "family,text",
    [
        ("HL-REPO-PATH", "Add the lookup to libs/core/src/index.ts as well."),
        ("HL-SOURCE-FILENAME", "Wire the handler in app.ts."),
        ("HL-PLACEMENT", "The helper must be placed under the shared area."),
        ("HL-HIDDEN-TEST", "The withheld grading suite asserts the key `orders`."),
        ("HL-RESET-CLUE", "Your session is restarted at checkpoint CK-PT90-1."),
        ("HL-CONDITION-NAME", "Runs in group C4 also receive an instruction document."),
        ("HL-OPPORTUNITY-ID", "Scored opportunity set: OPP-PT90-01."),
        ("HL-EVALUATOR-CLUE", "The oracle inspects the finished patch."),
        ("HL-EXPECTED-IMPL", "The expected implementation adds a thin wrapper."),
        ("HL-LEGIT-ALT", "A legitimate alternative is to return early instead."),
    ],
)
def test_regression_every_leakage_family_is_detected(family, text):
    """Previously: only the architecture-instruction family had patterns, so all
    of these passed clean."""
    result = check(f"---\nid: PT90\n---\n\n## Notes\n\n- {text}\n")
    assert not result.ok, f"{family} not detected in {text!r}"
    assert family in hard_ids(result), f"expected {family}, got {sorted(hard_ids(result))}"


def test_regression_combined_non_architecture_leakage_fails():
    text = """---
id: PT89
---

## Notes

- The withheld grading suite asserts the response key `orders` and `count`.
- Your session is restarted once you first run `npm run ci:agent` (checkpoint CK-PT89-1).
- Runs in group C4 also receive a separate instruction document; group C1 does not.
- Scored opportunity set: OPP-PT89-01, OPP-PT89-02.
- An accepted alternative solution is a thin wrapper placed under apps/api.
"""
    result = check(text)
    assert not result.ok
    ids = hard_ids(result)
    for expected in (
        "HL-HIDDEN-TEST",
        "HL-RESET-CLUE",
        "HL-CONDITION-NAME",
        "HL-OPPORTUNITY-ID",
        "HL-REPO-PATH",
    ):
        assert expected in ids, f"missing {expected} in {sorted(ids)}"


def test_terms_file_covers_every_required_family():
    ids = {t.id for t in TERMS}
    required = {
        "HL-MAD", "HL-BOUNDARIES", "HL-FOLLOW-ARCH", "HL-EXISTING-PATTERN",
        "HL-DEP-DIRECTION", "HL-LAYER-PRESCRIPTIVE", "HL-CONTRACT-PORT-PLACEMENT",
        "HL-ARCH-ACCEPTANCE", "HL-REPO-PATH", "HL-SOURCE-FILENAME", "HL-PLACEMENT",
        "HL-HIDDEN-TEST", "HL-RESET-CLUE", "HL-CONDITION-NAME", "HL-OPPORTUNITY-ID",
        "HL-EVALUATOR-CLUE", "HL-EXPECTED-IMPL", "HL-LEGIT-ALT",
    }
    assert required <= ids, f"missing leakage families: {sorted(required - ids)}"
    assert len(v.term_ids(TERMS, "review_required")) >= 7


# --------------------------------------------------------------------------- #
# REGRESSION D4 — discovery and index reconciliation
# --------------------------------------------------------------------------- #
def test_v1_and_v0_paths_are_refused():
    assert v.is_v1_path("archive/v1/tasks/T01.md")
    assert v.is_v1_path("experiments/tasks_v0/T01_get_order_by_id.md")
    assert v.is_v1_path(Path("d:/PhD/Code/afci-bench/archive/v1/REFERENCE_MANIFEST.yml"))
    assert not v.is_v1_path("experiments/v2/tasks/T01.md")


def test_discovery_excludes_readme_and_the_authoring_report(tmp_path):
    (tmp_path / "README.md").write_text("# tasks readme mentioning architecture", encoding="utf-8")
    pub = tmp_path / "public"
    pub.mkdir()
    (pub / "TASK_AUTHORING_REPORT.md").write_text(
        "# report naming validate_public_tasks.py and the oracle", encoding="utf-8"
    )
    (pub / "PT01.md").write_text(FUNCTIONAL_ONLY, encoding="utf-8")
    names = {p.name for p in v.discover_public_tasks(tmp_path)}
    assert names == {"PT01.md"}


def test_regression_nested_task_files_cannot_escape_scanning(tmp_path):
    """Previously: discovery was a non-recursive two-glob, so nested task bodies
    were never scanned."""
    leaky = "Follow the MAD.\n"
    (tmp_path / "public").mkdir()
    (tmp_path / "public" / "PT01.md").write_text(FUNCTIONAL_ONLY, encoding="utf-8")
    (tmp_path / "public" / "primary").mkdir()
    (tmp_path / "public" / "primary" / "PT07.md").write_text(leaky, encoding="utf-8")
    (tmp_path / "primary").mkdir()
    (tmp_path / "primary" / "PT08.md").write_text(leaky, encoding="utf-8")
    (tmp_path / "reserve").mkdir()
    (tmp_path / "reserve" / "PR09.md").write_text(leaky, encoding="utf-8")

    found = {p.name for p in v.discover_public_tasks(tmp_path)}
    assert {"PT01.md", "PT07.md", "PT08.md", "PR09.md"} <= found
    for p in v.discover_public_tasks(tmp_path):
        if p.name != "PT01.md":
            assert not v.validate_task_file(p, TERMS).ok, f"{p} should have failed"


def test_regression_task_like_file_with_unsupported_extension_is_rejected(tmp_path):
    """Previously: a task body saved as .markdown or .txt was silently skipped."""
    pub = tmp_path / "public"
    pub.mkdir()
    (pub / "PT01.md").write_text(FUNCTIONAL_ONLY, encoding="utf-8")
    (pub / "PT10.markdown").write_text("Follow the MAD.\n", encoding="utf-8")
    (pub / "PT11.txt").write_text("Follow the MAD.\n", encoding="utf-8")
    discovery = v.discover(tmp_path)
    assert {p.name for p in discovery.tasks} == {"PT01.md"}
    assert len(discovery.rejections) == 2
    assert any("PT10.markdown" in r for r in discovery.rejections)
    assert any("PT11.txt" in r for r in discovery.rejections)


def test_discovery_skips_the_tests_directory(tmp_path):
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "PT01.md").write_text("Follow the MAD.\n", encoding="utf-8")
    assert v.discover_public_tasks(tmp_path) == []


def _index(tmp_path, ids):
    pub = tmp_path / "public"
    pub.mkdir(exist_ok=True)
    header = "task_id,title\n"
    (pub / "TASK_INDEX.csv").write_text(
        header + "".join(f"{i},t\n" for i in ids), encoding="utf-8"
    )
    return pub / "TASK_INDEX.csv"


def _task(pub, task_id):
    (pub / f"{task_id}.md").write_text(
        f"---\nid: {task_id}\n---\n\n## Objective\n\nReturn an order.\n", encoding="utf-8"
    )


def test_index_reconciliation_accepts_a_matching_set(tmp_path):
    index = _index(tmp_path, ["PT01", "PT02"])
    _task(index.parent, "PT01")
    _task(index.parent, "PT02")
    assert v.reconcile_with_index(v.discover(tmp_path), index) == []


def test_index_reconciliation_rejects_missing_indexed_task(tmp_path):
    index = _index(tmp_path, ["PT01", "PT02"])
    _task(index.parent, "PT01")
    errors = v.reconcile_with_index(v.discover(tmp_path), index)
    assert any("no discovered task file" in e and "PT02" in e for e in errors)


def test_index_reconciliation_rejects_unindexed_task(tmp_path):
    index = _index(tmp_path, ["PT01"])
    _task(index.parent, "PT01")
    _task(index.parent, "PT02")
    errors = v.reconcile_with_index(v.discover(tmp_path), index)
    assert any("not in TASK_INDEX.csv" in e and "PT02" in e for e in errors)


def test_index_reconciliation_rejects_duplicate_index_ids(tmp_path):
    index = _index(tmp_path, ["PT01", "PT01"])
    _task(index.parent, "PT01")
    errors = v.reconcile_with_index(v.discover(tmp_path), index)
    assert any("duplicate task ids" in e for e in errors)


def test_index_reconciliation_rejects_duplicate_front_matter_ids(tmp_path):
    index = _index(tmp_path, ["PT01"])
    pub = index.parent
    _task(pub, "PT01")
    nested = pub / "extra"
    nested.mkdir()
    (nested / "PT01.md").write_text(
        "---\nid: PT01\n---\n\n## Objective\n\nReturn an order.\n", encoding="utf-8"
    )
    errors = v.reconcile_with_index(v.discover(tmp_path), index)
    assert any("duplicate task id" in e for e in errors)


def test_index_reconciliation_rejects_filename_id_mismatch(tmp_path):
    index = _index(tmp_path, ["PT01"])
    (index.parent / "PT01.md").write_text(
        "---\nid: PT99\n---\n\n## Objective\n\nReturn an order.\n", encoding="utf-8"
    )
    errors = v.reconcile_with_index(v.discover(tmp_path), index)
    assert any("does not match filename stem" in e for e in errors)


def test_index_reconciliation_surfaces_unsupported_extension_rejections(tmp_path):
    index = _index(tmp_path, ["PT01"])
    _task(index.parent, "PT01")
    (index.parent / "PT02.txt").write_text("Follow the MAD.\n", encoding="utf-8")
    errors = v.reconcile_with_index(v.discover(tmp_path), index)
    assert any("unsupported extension" in e for e in errors)


# --------------------------------------------------------------------------- #
# The real authored suite
# --------------------------------------------------------------------------- #
def test_authored_public_task_suite_is_discovered_and_leakage_free():
    discovery = v.discover(TASKS_DIR)
    names = {p.name for p in discovery.tasks}
    assert names == EXPECTED_TASKS, f"unexpected task set: {sorted(names)}"
    assert discovery.rejections == []
    for p in discovery.tasks:
        result = v.validate_task_file(p, TERMS)
        assert result.ok, f"leakage in {p}: {[f.__dict__ for f in result.findings]} / {result.exception_errors}"


def test_authored_suite_reconciles_with_the_task_index():
    assert v.reconcile_with_index(v.discover(TASKS_DIR), INDEX_PATH) == []


def test_authoring_report_is_not_counted_as_a_task():
    names = {p.name for p in v.discover(TASKS_DIR).tasks}
    assert "TASK_AUTHORING_REPORT.md" not in names
    assert len(names) == 8


def test_cli_exit_code_is_zero_for_the_authored_suite():
    assert v.main([]) == 0
