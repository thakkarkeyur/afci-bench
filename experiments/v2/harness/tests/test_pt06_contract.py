"""PT06's public rejection contract is fully determined and bounded.

An independent review of the PT06 feasibility amendment found two under-determinations
in its public text. Neither invalidated the amendment, but either could have let a
solution satisfy every stated criterion and still fail acceptance - the exact failure
mode a public task body exists to prevent:

1. **The declared response media type was implied, not stated.** "The response body is
   JSON - never HTML, never empty" constrains the payload, not the media type the
   response declares. A serialised envelope sent as a plain string is a parseable JSON
   body under a ``text/html`` media type: conforming to the letter, yet failing any
   check that reads the response as JSON.
2. **The covered rejections were unbounded.** An unqualified "a rejected
   ``POST /orders`` request answers with HTTP 400" was reachably false at the base,
   which answers an over-large body HTTP 413 and an unsupported charset HTTP 415. Under
   the broad reading a solution must remap those; under the narrow reading it must not.

This module pins the closed contract so neither can silently reopen: the media type is
required, no other response header is, the covered failure kinds are exactly two, the
unrelated transport/parser rejections are explicitly outside scope, and no unbounded
"every rejected request" wording survives.

It asserts what PT06 *states*, never how a solution should be built: no file, no
placement, no mechanism. Pure file inspection; no model is invoked and no benchmark
runs.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[4]
PUBLIC_TASKS_DIR = REPO / "experiments" / "v2" / "tasks" / "public"
PT06_PATH = PUBLIC_TASKS_DIR / "PT06.md"
INDEX_PATH = PUBLIC_TASKS_DIR / "TASK_INDEX.csv"
MATRIX_PATH = REPO / "docs" / "v2" / "PILOT_PUBLIC_TASK_MATRIX.csv"
REPORT_PATH = PUBLIC_TASKS_DIR / "TASK_AUTHORING_REPORT.md"
TASKS_ROOT = REPO / "experiments" / "v2" / "tasks"

#: The eight candidates this module's PT06 amendment was written against, plus
#: PT07, authored later under DECISION B (TD-B34). The count is pinned so a stray
#: or duplicated body is caught; changing it must be a deliberate authoring act.
EXPECTED_PUBLIC_TASK_COUNT = 9


@pytest.fixture(scope="module")
def pt06() -> str:
    return PT06_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def body(pt06: str) -> str:
    """PT06 with its front matter removed."""
    lines = pt06.splitlines(keepends=True)
    assert lines[0].strip() == "---"
    end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    return "".join(lines[end + 1:])


def _flat(text: str) -> str:
    """Collapse hard-wrapped prose, so an assertion never depends on where a line
    happens to break."""
    return " ".join(text.split())


# --------------------------------------------------------------------------- #
# 1. The JSON response media type is required explicitly
# --------------------------------------------------------------------------- #
def test_pt06_requires_an_application_json_response_media_type(pt06):
    """Stated as a response-header requirement, not inferable from "the body is JSON"."""
    lowered = pt06.lower()
    assert "content-type" in lowered, "PT06 must name the Content-Type response header"
    assert "media type" in lowered, (
        "PT06 must speak about the response *media type*, so the requirement cannot be "
        "read as a statement about the body payload alone"
    )
    assert re.search(
        r"media type (?:is|begins with) `?application/json`?", _flat(pt06), re.IGNORECASE
    ), "PT06 must require a response media type of application/json"


def test_the_media_type_requirement_is_prefix_based_not_an_exact_header_string(pt06):
    """``application/json; charset=utf-8`` must satisfy it, so a solution is not forced
    to suppress the charset parameter the framework adds."""
    assert "begins with" in _flat(pt06).lower(), (
        "the media-type requirement must be prefix-based ('begins with'), otherwise an "
        "exact-header reading would reject application/json; charset=utf-8"
    )
    assert "charset" in pt06.lower(), (
        "PT06 must say a parameter such as ; charset=utf-8 may follow the media type"
    )


def test_both_covered_kinds_carry_the_media_type_requirement(pt06):
    """Not just the shared preamble: each completion criterion carries it too."""
    criteria = pt06.split("## Functional completion criteria", 1)
    assert len(criteria) == 2, "PT06 must keep a functional completion criteria section"
    tail = _flat(criteria[1])
    occurrences = len(
        re.findall(r"media type begins with `application/json`", tail, re.IGNORECASE)
    )
    assert occurrences >= 2, (
        "each of PT06's two covered rejection kinds must carry the media-type "
        f"requirement in the completion criteria; found {occurrences}"
    )


# --------------------------------------------------------------------------- #
# 2. No other response header is required
# --------------------------------------------------------------------------- #
def test_pt06_requires_no_response_header_other_than_content_type(pt06):
    lowered = _flat(pt06).lower()
    assert "no response header other than `content-type`" in lowered, (
        "PT06 must state that no response header other than Content-Type is part of "
        "its required behaviour, so no unstated header can be enforced"
    )


def test_pt06_does_not_pin_the_correlation_id_response_header(pt06):
    """``correlationId`` is a required *body* key; the header of the same name is not
    part of PT06's required behaviour and must not be pinned as one."""
    assert "correlationId" in pt06, "the body key must still be required"
    assert not re.search(
        r"`?x-correlation-id`?\s+(?:response\s+)?header\s+(?:must|is required|has to)",
        pt06,
        re.IGNORECASE,
    ), "PT06 must not require the x-correlation-id response header"
    assert not re.search(
        r"(?:must|has to)\s+(?:also\s+)?(?:set|return|carry)\s+(?:the\s+)?`?x-correlation-id`?",
        pt06,
        re.IGNORECASE,
    ), "PT06 must not require the x-correlation-id response header"


# --------------------------------------------------------------------------- #
# 3. The covered failure classes are exactly two
# --------------------------------------------------------------------------- #
def test_pt06_has_a_scope_section_naming_exactly_two_covered_kinds(body):
    assert "## Scope" in body, "PT06 must carry an explicit Scope section"
    scope = body.split("## Scope", 1)[1].split("\n## ", 1)[0]
    numbered = re.findall(r"^\d+\.\s+\*\*", scope, re.MULTILINE)
    assert len(numbered) == 2, (
        f"the Scope section must enumerate exactly two covered kinds; found {len(numbered)}"
    )
    assert "and no\nothers" in scope or "and no others" in scope.replace("\n", " "), (
        "the Scope section must say the two kinds are the only covered ones"
    )


def test_the_two_covered_kinds_are_semantic_validation_and_json_parse_failure(body):
    scope = body.split("## Scope", 1)[1].split("\n## ", 1)[0]
    flat = " ".join(scope.split())
    assert "semantic input-validation failure" in flat, (
        "the first covered kind must be a semantic input-validation failure"
    )
    assert "parsed as JSON and then failed the existing input validation" in flat, (
        "the semantic kind must be scoped to a body that was parsed as JSON first"
    )
    assert "JSON parse failure" in flat, "the second covered kind must be a parse failure"
    assert "not parseable JSON" in flat
    assert "Content-Type: application/json" in flat, (
        "the parse-failure kind must be scoped to the application/json request "
        "content type, which is what makes it externally triggerable"
    )


def test_the_completion_criteria_use_the_same_bounded_wording(pt06):
    tail = _flat(pt06.split("## Functional completion criteria", 1)[1])
    assert "whose parsed body fails the existing input validation" in tail, (
        "the semantic criterion must use the bounded 'parsed body' wording"
    )
    assert "whose body is not parseable JSON, sent with" in tail, (
        "the parse-failure criterion must keep its request-content-type bound"
    )
    assert "outside **Scope**" in tail or "outside Scope" in tail.replace("**", ""), (
        "the completion criteria must refer back to the bounded Scope section"
    )


# --------------------------------------------------------------------------- #
# 4. HTTP 413 and HTTP 415 are explicitly out of scope
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("status", ["413", "415"])
def test_unrelated_parser_rejections_are_explicitly_out_of_scope(body, status):
    """Both are externally reachable at the base and answered as HTML, so leaving them
    unmentioned is what made the old text ambiguous."""
    assert status in body, f"PT06 must name HTTP {status} explicitly"
    scope = body.split("## Scope", 1)[1].split("\n## ", 1)[0]
    flat = " ".join(scope.split())
    assert status in flat, (
        f"HTTP {status} must be named in the Scope section, where it is placed outside "
        "the task"
    )
    assert "outside the scope of this task" in flat, (
        "the Scope section must say these rejections are outside the task's scope"
    )


def test_out_of_scope_rejections_keep_their_current_behaviour(body):
    scope = body.split("## Scope", 1)[1].split("\n## ", 1)[0]
    flat = " ".join(scope.split())
    assert "keeps its current status code and its current response body" in flat, (
        "out-of-scope rejections must be pinned as unchanged"
    )
    assert "None of them has to answer HTTP 400" in flat, (
        "PT06 must state that out-of-scope rejections need not answer HTTP 400"
    )
    assert "none of them has to carry `error` `ValidationError`" in flat, (
        "PT06 must state that out-of-scope rejections need not carry ValidationError"
    )


def test_no_out_of_scope_rejection_is_required_to_carry_the_envelope(body):
    """Guard against a future edit that quietly pulls 413/415 back in."""
    for status in ("413", "415"):
        assert not re.search(
            rf"HTTP {status}[^.]{{0,80}}(?:must|has to)\s+(?:answer|return|carry)\s+"
            rf"(?:HTTP\s+)?400",
            body,
            re.IGNORECASE,
        ), f"PT06 must not require an HTTP {status} rejection to become HTTP 400"


# --------------------------------------------------------------------------- #
# 5. No unbounded "every rejected request" wording survives
# --------------------------------------------------------------------------- #
#: Formulations that would re-open the contract to every possible rejection.
UNBOUNDED_PHRASES = (
    "a rejected `post /orders` request answers",
    "every rejected",
    "all rejected",
    "any rejected request",
    "each rejected request",
    "every kind of rejected",
    "each kind of rejected request",
    "both of the following are rejected requests",
    "both kinds of rejected request",
    "nothing beyond the rejection response",
    "every `post /orders` failure",
    "every order-creation failure",
    "every failure response",
)


@pytest.mark.parametrize("phrase", UNBOUNDED_PHRASES, ids=lambda p: p[:34])
def test_no_unbounded_rejection_wording_remains(pt06, phrase):
    assert phrase not in pt06.lower(), (
        f"PT06 carries unbounded rejection wording ({phrase!r}); every statement about "
        "the rejection contract must be bounded to the two kinds named in Scope"
    )


def test_every_contract_statement_is_bounded_to_the_named_scope(pt06):
    """The envelope-defining statements must each cite the bounded Scope."""
    assert _flat(pt06).lower().count("named in **scope**") >= 5, (
        "the user-visible behaviour, the outputs, the error behaviour and the "
        "constraints must each bind themselves to the two kinds named in Scope"
    )


def test_the_task_still_pins_the_behaviour_it_always_pinned(pt06):
    """Bounding the scope must not have dropped a requirement."""
    assert "HTTP 400" in pt06
    assert "`error` is exactly the string `ValidationError`" in pt06
    assert "`message` is a non-empty string" in pt06
    assert "`correlationId` is a non-empty string" in pt06
    assert re.search(r"HTTP\s*\n?\s*201", pt06), "success must still be pinned to 201"
    assert "unchanged" in pt06.lower()
    for key in ("error", "message", "correlationId"):
        assert f'"{key}"' in pt06, f"the {key} key must stay in the pinned envelope"


# --------------------------------------------------------------------------- #
# 6. Still architecture-neutral and still leakage-clean
# --------------------------------------------------------------------------- #
def test_pt06_passes_the_public_leakage_validator():
    """Run the real validator, not a re-implementation of it."""
    import sys

    sys.path.insert(0, str(TASKS_ROOT))
    try:
        import validate_public_tasks as validator
    finally:
        sys.path.pop(0)

    result = validator.validate_task_file(PT06_PATH, validator.load_terms())
    assert result.ok, (
        "PT06 leaks: "
        + "; ".join(
            f"{f.location} [{f.term_id}] {f.text!r}"
            for f in (result.hard_leaks + result.uncovered_reviews)
        )
        + "".join(result.exception_errors)
    )


def test_the_clarification_added_no_architecture_or_placement_wording(pt06):
    """A belt-and-braces read of the terms that matter most for this task's subject."""
    lowered = pt06.lower()
    for forbidden in (
        "middleware",
        "error handler",
        "error-handling middleware",
        "layer",
        "boundary",
        "dependency",
        "module",
        "architecture",
        "apps/",
        "libs/",
        "src/",
        "@afci-bench",
        ".ts",
        "oracle",
        "evaluator",
        "hidden test",
        "checkpoint",
    ):
        assert forbidden not in lowered, (
            f"PT06 must stay architecture-neutral and placement-free; found {forbidden!r}"
        )


def test_pt06_still_exposes_only_the_agent_ci_command(pt06):
    assert "npm run ci:agent" in pt06
    for other in ("npm run ci\n", "npm run test", "npm run lint", "npm run typecheck"):
        assert other not in pt06, f"PT06 exposes a second validation command: {other!r}"


def test_pt06_is_still_a_candidate_and_not_frozen(pt06):
    lines = pt06.splitlines()
    end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    fm = yaml.safe_load("\n".join(lines[1:end]))
    assert fm["status"] == "candidate", "PT06 must remain a candidate, never frozen here"
    assert fm["id"] == "PT06"
    assert fm["visible_validation"] == "npm run ci:agent"


# --------------------------------------------------------------------------- #
# 7. Hash / index / matrix / report references agree
# --------------------------------------------------------------------------- #
def test_pt06_hash_agrees_across_every_public_reference():
    actual = hashlib.sha256(PT06_PATH.read_bytes()).hexdigest()
    index = INDEX_PATH.read_text(encoding="utf-8")
    matrix = MATRIX_PATH.read_text(encoding="utf-8")
    report = REPORT_PATH.read_text(encoding="utf-8")

    assert f",{actual}," in index, "TASK_INDEX.csv does not record PT06's actual hash"
    assert f",{actual}," in matrix, (
        "PILOT_PUBLIC_TASK_MATRIX.csv does not record PT06's actual hash"
    )
    assert f"`{actual[:16]}...`" in report, (
        "the authoring report does not record PT06's actual hash prefix"
    )
    assert b"\r\n" not in PT06_PATH.read_bytes(), (
        "PT06 must stay LF-only so its hash is platform-stable"
    )


def test_the_other_seven_task_hashes_are_untouched_by_this_change():
    """Recorded independently of the index, so a wrong edit to both cannot hide."""
    expected = {
        "PT01": "6c938822fe19cd6e87942a6ee24ec8f604c0883da1b7f80d45216be35d7c9c39",
        "PT02": "ec4b60057708b20cb95e51f000671aab40afc8c55c0bc75850922a5f65841a77",
        "PT03": "cbfce1ca232cb9b6b53e0b4d202d6acee7415b50af8386c1f3bd2147089b4c21",
        "PT04": "f349b150b1d8fe5676fed8460b1840b988ee2bb0a78b1966ef82ae9ce9c8a9b5",
        "PT05": "f6efc772e76d6c287e0c71daaa93c7e1d9e62e72a1b37878df70113269ed27b3",
        "PR01": "0e1527bce41498836bb57b802d4566251d6fcfed4cca13fe59e6a97330f02302",
        "PR02": "e89a4aab236813c082f9152db779b8bbfb298148a51a8435a1e2bf38330caa83",
    }
    for task_id, want in expected.items():
        path = PUBLIC_TASKS_DIR / f"{task_id}.md"
        got = hashlib.sha256(path.read_bytes()).hexdigest()
        assert got == want, (
            f"{task_id} changed; this work package amends PT06 only "
            f"(recorded {want[:16]}..., found {got[:16]}...)"
        )


# --------------------------------------------------------------------------- #
# 8. Exactly the recorded number of public tasks
# --------------------------------------------------------------------------- #
def test_exactly_the_recorded_public_tasks_are_discovered():
    import sys

    sys.path.insert(0, str(TASKS_ROOT))
    try:
        import validate_public_tasks as validator
    finally:
        sys.path.pop(0)

    discovery = validator.discover(TASKS_ROOT)
    assert not discovery.rejections, discovery.rejections
    assert len(discovery.tasks) == EXPECTED_PUBLIC_TASK_COUNT, (
        f"expected {EXPECTED_PUBLIC_TASK_COUNT} public tasks, discovered "
        f"{[p.name for p in discovery.tasks]}"
    )
    errors = validator.reconcile_with_index(discovery, INDEX_PATH)
    assert not errors, errors
