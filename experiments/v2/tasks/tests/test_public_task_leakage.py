"""Tests for the public-task architecture-leakage validator.

Covers Part E of the pre-execution design-review reconciliation: a functional
task passes; obvious and subtle leakage fail; architecture hints in acceptance
criteria fail; a justified exception passes; an unjustified exception fails; and
v1/v0 tasks are never scanned. Pure file inspection; no model is invoked.
"""
from pathlib import Path

import pytest

import validate_public_tasks as v

TERMS = v.load_terms()


def check(text: str) -> v.TaskValidation:
    return v.validate_task_text(text, TERMS)


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
    ids = {f.term_id for f in result.hard_leaks}
    assert "HL-MAD" in ids
    assert "HL-BOUNDARIES" in ids


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
    ids = {f.term_id for f in result.hard_leaks}
    assert "HL-DEP-DIRECTION" in ids
    assert "HL-LAYER-PRESCRIPTIVE" in ids


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
    hard = result.hard_leaks
    assert any(f.term_id == "HL-DEP-DIRECTION" for f in hard)
    # the offending line is inside the acceptance-criteria section
    assert any("import" in f.line_text.lower() for f in hard)


# --------------------------------------------------------------------------- #
# 5. justified exception passes
# --------------------------------------------------------------------------- #
JUSTIFIED = """---
leakage_exceptions:
  - id: RR-LAYER
    match: "caching layer"
    justification: "Refers to a functional in-memory caching layer for repeated lookups, not a repository architecture layer."
    reviewer: "oracle-designer"
---
# Task: Speed up repeated lookups

Add an in-memory caching layer so repeated lookups of the same id are fast.

## Acceptance criteria
- A second lookup of the same id does not recompute the result.
"""


def test_justified_exception_passes():
    result = check(JUSTIFIED)
    # the only finding is the ambiguous review-required "layer" term, and it is
    # covered by a valid reviewed exception
    assert result.hard_leaks == []
    assert result.exception_errors == []
    layer_findings = [f for f in result.findings if f.term_id == "RR-LAYER"]
    assert layer_findings and all(f.covered for f in layer_findings)
    assert result.ok


# --------------------------------------------------------------------------- #
# 6. unjustified exception fails
# --------------------------------------------------------------------------- #
UNJUSTIFIED = """---
leakage_exceptions:
  - id: RR-LAYER
    match: "caching layer"
    justification: ""
    reviewer: ""
---
# Task: Speed up repeated lookups

Add an in-memory caching layer so repeated lookups of the same id are fast.
"""


def test_unjustified_exception_fails():
    result = check(UNJUSTIFIED)
    assert not result.ok
    assert result.exception_errors, "an exception without justification/reviewer must be flagged"
    assert result.uncovered_reviews, "the review-required finding must remain uncovered"


def test_exception_cannot_cover_a_hard_leak():
    text = """---
leakage_exceptions:
  - id: HL-MAD
    justification: "we really want to mention the MAD"
    reviewer: "someone"
---
# Task: Do the thing

Follow the MAD exactly.
"""
    result = check(text)
    assert not result.ok
    # targeting a hard-leak id is itself a governance error, and the hard leak remains
    assert any("hard-leak" in e for e in result.exception_errors)
    assert any(f.term_id == "HL-MAD" for f in result.hard_leaks)


# --------------------------------------------------------------------------- #
# v1/v0 protection + discovery
# --------------------------------------------------------------------------- #
def test_v1_and_v0_paths_are_refused():
    assert v.is_v1_path("archive/v1/tasks/T01.md")
    assert v.is_v1_path("experiments/tasks_v0/T01_get_order_by_id.md")
    assert v.is_v1_path(Path("d:/PhD/Code/afci-bench/archive/v1/REFERENCE_MANIFEST.yml"))
    assert not v.is_v1_path("experiments/v2/tasks/T01.md")


def test_discovery_excludes_readme(tmp_path):
    (tmp_path / "README.md").write_text("# tasks readme with the word architecture", encoding="utf-8")
    (tmp_path / "T01_functional.md").write_text(FUNCTIONAL_ONLY, encoding="utf-8")
    found = v.discover_public_tasks(tmp_path)
    names = {p.name for p in found}
    assert "README.md" not in names
    assert "T01_functional.md" in names


def test_real_tasks_dir_has_no_public_tasks_yet():
    # only README.md exists under experiments/v2/tasks today
    assert v.discover_public_tasks() == []
