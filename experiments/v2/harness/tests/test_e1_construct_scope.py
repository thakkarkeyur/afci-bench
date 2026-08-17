"""Load-bearing pin on the **normative E1 construct definition**.

An independent mutation review showed that the construct could be rewritten to
"broad architectural conformance across all architecture rules and all layer
pairs" while the whole public suite stayed green. Nothing asserted what E1 *is*;
the existing checks only looked for a limitation sentence somewhere nearby, and a
document-wide grep is satisfied by any occurrence anywhere in the file.

This module scopes every assertion to the **actual normative definition**:

* ``RESEARCH_QUESTIONS.md`` — the ``CON-AC`` construct-definition section, which is
  where the construct is defined for the study;
* ``STATISTICAL_ANALYSIS_PLAN.md`` §2.2 — where the measured space is defined;
* ``STATISTICAL_ANALYSIS_PLAN.md`` §2 — the endpoint table's narrowing note;
* ``ORACLE_TRACEABILITY.csv`` ``OT-AC-VIOL`` — the machine-readable E1 row.

Two independent nets are used, because either alone can be worked around:

1. the definitional wording is pinned **verbatim inside its own section**, so a
   broadened definition must delete it to install itself; and
2. within those same sections, any sentence that *affirms* one of the broadening
   phrases (rather than ruling it out) fails — so the wording cannot be widened
   by addition either.

Pure file inspection; no model is invoked and no benchmark runs.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[4]
DOCS_V2 = REPO / "docs" / "v2"

RQ_PATH = DOCS_V2 / "RESEARCH_QUESTIONS.md"
SAP_PATH = DOCS_V2 / "STATISTICAL_ANALYSIS_PLAN.md"
TRACE_PATH = DOCS_V2 / "ORACLE_TRACEABILITY.csv"
CLAIMS_PATH = DOCS_V2 / "CLAIMS_CONSTRUCTS_METRICS.csv"

#: The construct E1 measures, and the space it is measured over. These two
#: fragments are the definition; if either disappears the construct has been
#: silently redefined.
E1_CONSTRUCT = "layered dependency-direction conformance"
E1_MEASURED_SPACE = (
    "pre-registered task-creatable dependency decisions represented by the "
    "canonical substrate and task suite"
)

#: Ways the construct could be widened into something E1 does not measure. Each
#: may appear in the normative sections **only** as something being ruled out.
BROADENING_PHRASES = (
    "all architecture rules",
    "all layer pairs",
    "broad architectural conformance",
    "broad or general architectural conformance",
    "general architectural conformance",
    "general architecture quality",
    "architectural integrity",
)

#: Markers that make an occurrence a limitation rather than a claim.
NEGATION_MARKERS = (
    "not ",
    "never",
    "nothing wider",
    "no e1 result",
    "must not",
    "does not",
    "rather than",
    "beyond",
    "is broader",
)

_HEADING_RE = re.compile(r"(?m)^(#{1,6})[ \t]+(.+?)[ \t]*$")


def _norm(raw: str) -> str:
    raw = raw.replace("*", "").replace("`", "")
    raw = re.sub(r"(?m)^\s*>\s?", "", raw)
    return re.sub(r"\s+", " ", raw).strip().lower()


def _sections(path: Path) -> dict[str, str]:
    """Each markdown heading mapped to its body, ending at the next same-or-higher heading."""
    text = path.read_text(encoding="utf-8")
    heads = list(_HEADING_RE.finditer(text))
    out: dict[str, str] = {}
    for i, head in enumerate(heads):
        level = len(head.group(1))
        end = len(text)
        for nxt in heads[i + 1 :]:
            if len(nxt.group(1)) <= level:
                end = nxt.start()
                break
        out[_norm(head.group(2))] = text[head.end() : end]
    return out


def _section_starting_with(path: Path, prefix: str) -> str:
    matches = {k: v for k, v in _sections(path).items() if k.startswith(prefix.lower())}
    assert len(matches) == 1, (
        f"{path.name} must carry exactly one section headed {prefix!r}, found {sorted(matches)}"
    )
    return next(iter(matches.values()))


def _sentences(body: str) -> list[str]:
    """Normalised sentences of a markdown body.

    Splitting on markdown blocks alone is too coarse — a broadened definition could
    hide in a paragraph that negates something else — so blocks are split further at
    sentence boundaries, taking care not to break section references (``§2.1``) or
    ellipsised rule ranges (``AR-DEP-001…006``).
    """
    blocks: list[str] = []
    current: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            if current:
                blocks.append(" ".join(current))
                current = []
            continue
        if re.match(r"^(?:[-*+]\s+|\d+\.\s+|\|)", stripped) and current:
            blocks.append(" ".join(current))
            current = []
        current.append(stripped)
    if current:
        blocks.append(" ".join(current))

    out: list[str] = []
    for block in blocks:
        normalised = _norm(block)
        if not normalised:
            continue
        # a sentence ends at '.', ';' or ':' followed by whitespace and a letter,
        # but never inside a numeric reference such as "2.1" or "0.70"
        out.extend(
            part.strip()
            for part in re.split(r"(?<=[.;:])\s+(?=[a-z(])", normalised)
            if part.strip()
        )
    return out


# --------------------------------------------------------------------------- #
# The normative sections. Named here so a renamed heading fails loudly rather
# than silently disabling every assertion below.
# --------------------------------------------------------------------------- #
def _con_ac_section() -> str:
    return _section_starting_with(RQ_PATH, "con-ac — layered dependency-direction conformance")


def _sap_generalisation_section() -> str:
    return _section_starting_with(SAP_PATH, "2.2 what an e1 result generalises to")


def _sap_endpoints_section() -> str:
    return _section_starting_with(SAP_PATH, "2. endpoints")


NORMATIVE_SECTIONS = {
    "RESEARCH_QUESTIONS.md CON-AC": _con_ac_section,
    "STATISTICAL_ANALYSIS_PLAN.md 2.2": _sap_generalisation_section,
}


# --------------------------------------------------------------------------- 1
# The construct is what it says it is.


def test_the_con_ac_heading_still_names_the_narrow_construct():
    """The construct's own heading is part of the definition."""
    # "con-ac —", not "con-ac", so the sibling CON-ACB heading is not swept in
    headings = [k for k in _sections(RQ_PATH) if re.match(r"con-ac\s*[—-]", k)]
    assert len(headings) == 1, f"expected exactly one CON-AC heading, found {headings}"
    heading = headings[0]
    assert E1_CONSTRUCT in heading, (
        f"CON-AC must remain '{E1_CONSTRUCT}'; the heading now reads {heading!r}"
    )
    assert "directly measured" in heading


def test_con_ac_defines_the_construct_as_dependency_direction_and_nothing_wider():
    section = _norm(_con_ac_section())
    assert "the dependency-direction rule family ar-dep-001…006" in section or (
        "the dependency-direction rule family ar-dep-001...006" in section
    ), "the definition must name the dependency-direction rule family it is limited to"
    assert "this is one facet of architecture" in section, (
        "the definition must say the construct is one facet of architecture"
    )
    assert "and nothing wider" in section, (
        "the definition's explicit upper bound must survive"
    )


def test_con_ac_measures_only_the_represented_task_creatable_decision_space():
    section = _norm(_con_ac_section())
    assert E1_MEASURED_SPACE in section, (
        "CON-AC must be measured over the pre-registered task-creatable dependency "
        "decisions represented by the canonical substrate and task suite"
    )
    assert "not over the rule family in the abstract" in section, (
        "the measured space must be distinguished from the rule family in the abstract"
    )


def test_the_statistical_plan_defines_e1_the_same_way():
    """§2.2 is the endpoint-side statement of the same construct; both must agree."""
    section = _norm(_sap_generalisation_section())
    assert f"e1's construct is {E1_CONSTRUCT}" in section, (
        f"§2.2 must define E1's construct as {E1_CONSTRUCT!r}"
    )
    assert E1_MEASURED_SPACE in section, (
        "§2.2 must measure E1 over the represented task-creatable decisions"
    )
    assert "not over the rule family in the abstract" in section


def test_the_endpoint_table_note_keeps_e1_narrowed():
    section = _norm(_sap_endpoints_section())
    assert f"e1 measures {E1_CONSTRUCT} only" in section, (
        "the endpoint section must state that E1 measures the narrow construct only"
    )
    assert "e1 does not directly measure contract ownership" in section
    assert "must not describe e1 as broad or general architectural conformance" in section


def test_the_machine_readable_e1_row_carries_the_same_construct():
    with open(TRACE_PATH, newline="", encoding="utf-8") as fh:
        rows = {r["oracle_id"]: r for r in csv.DictReader(fh)}
    row = rows["OT-AC-VIOL"]
    assert row["construct"] == "CON-AC"
    notes = _norm(row["notes"])
    assert f"measures {E1_CONSTRUCT} only" in notes, (
        "the E1 traceability row must name the narrow construct"
    )
    assert "never broad or general architectural conformance" in notes


def test_the_primary_claims_still_forbid_the_broad_restatement():
    with open(CLAIMS_PATH, newline="", encoding="utf-8") as fh:
        rows = {r["claim_id"]: r for r in csv.DictReader(fh)}
    for claim_id in ("CL01", "CL02", "CL03"):
        row = rows[claim_id]
        assert row["construct"] == "CON-AC", claim_id
        risk = _norm(row["unsupported_claim_risk"])
        assert "must not be generalised beyond the represented task-creatable" in risk, claim_id
    # CL01 is the primary C4-vs-C1 claim and carries the full restatement guard
    cl01 = _norm(rows["CL01"]["unsupported_claim_risk"])
    assert "must not be restated as" in cl01
    assert "broad architectural conformance" in cl01
    # and the guardrail claim that records the narrowing must stay CON-ACB
    cl15 = rows["CL15"]
    assert cl15["construct"] == "CON-ACB"
    assert "deliberately not directly measured by e1" in _norm(cl15["direct_metric"])


# --------------------------------------------------------------------------- 2
# It cannot be widened by addition either.


@pytest.mark.parametrize("label", sorted(NORMATIVE_SECTIONS))
def test_no_normative_sentence_affirms_a_broadened_construct(label):
    """Every broadening phrase in a normative section must be something ruled out.

    This is the half that catches widening-by-addition: a new sentence claiming E1
    covers all architecture rules would carry no negation and fails here, even
    though the pinned definition above is still present.
    """
    section = NORMATIVE_SECTIONS[label]()
    offenders = []
    for sentence in _sentences(section):
        for phrase in BROADENING_PHRASES:
            if phrase not in sentence:
                continue
            if not any(marker in sentence for marker in NEGATION_MARKERS):
                offenders.append((phrase, sentence))
    assert not offenders, (
        f"{label} affirms a broadened E1 construct rather than ruling it out: {offenders}"
    )


@pytest.mark.parametrize("label", sorted(NORMATIVE_SECTIONS))
def test_the_generalisation_limit_is_stated_in_the_normative_section_itself(label):
    """Not merely somewhere in the file — in the section that defines the construct."""
    section = _norm(NORMATIVE_SECTIONS[label]())
    assert (
        "generalise directly to the represented dependency-decision families, not "
        "automatically to all architecture rules or all layer pairs" in section
    ), f"{label} must carry the generalisation limit inside the definition itself"
    assert "construct-validity limitation" in section, (
        f"{label} must record the breadth ceiling as a construct-validity limitation"
    )


def test_the_narrowing_never_becomes_a_broadening():
    """The CON-ACB dimensions stay outside E1 in both normative locations."""
    con_ac = _norm(_con_ac_section())
    sap = _norm(_sap_generalisation_section())
    assert "it does not broaden con-ac" in con_ac
    assert "this does not broaden e1" in sap
    for dimension in (
        "contract ownership",
        "port / interface placement" if "port / interface placement" in con_ac else "port",
        "observability completeness",
        "duplicated logic",
    ):
        assert dimension in con_ac, f"{dimension} must stay listed as outside E1"
