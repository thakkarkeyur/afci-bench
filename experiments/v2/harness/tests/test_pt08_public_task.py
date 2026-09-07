"""Governance tests for `PT08`, the priority-A replication task authored in public.

`PT08` — *Apply a caller-declared maximum total to order creation* — is the public
body of `CAND-A1`, the priority-A replication candidate whose contract decisions
were pinned before any prose existed and whose focused independent remediation
re-review returned **APPROVE — public authoring may begin**. This module asserts the
properties that make authoring it a *legible, bounded* act rather than a drift, in
two directions at once.

WHAT MUST BE TRUE
-----------------
* the body exists, validates against the public task schema, is `primary`, and is
  indexed exactly once with the hash of the bytes on disk;
* it contains no leakage, judged by the repository's own validator with the
  repository's own terms — neither is weakened here — and no reviewed exception;
* every wire decision the pre-authoring record pinned is actually stated in the
  public text: the carrier is a **query parameter** and not a header; absence
  preserves existing behaviour; zero is valid; negative, empty, non-numeric,
  `NaN`/`Infinity` and repeated values are invalid with the **existing** `400`
  `ValidationError` body; equality is accepted; above the ceiling is `409`
  `OrderValueLimitExceeded` with **exactly** three body keys; existing body
  validation keeps its answer; and no new monetary rule is introduced;
* the numeric spellings the record did **not** pin are left genuinely unspecified;
* every registry that must list every public task carries exactly one consistent
  `PT08` row.

WHAT HAS SINCE BECOME TRUE
--------------------------
`PT08`'s public authoring has been **independently reviewed and approved**, its
**private evaluator package authored** and **approved on a discharged conditional
independent review**, and its architecture opportunity **admitted** by a separately
recorded governance step. So the active accounting is **6** opportunities over
**3** decision clusters at depths **3 / 2 / 1**, and the priority-A cluster carries
**two** observations — which stay **pseudo-replicates** of one shared decision.

WHAT MUST STAY FALSE
--------------------
`PT08` is **not** frozen, **not** run-ready and **not** E1 run-eligible; its
manifest is `status=review`; its hidden functional acceptance is
**`draft_unvalidated`** and has never been runtime-validated; `TD-B34` stays open
and blocking; priority B is **not started**; `G1` is not passed; **no** result,
violation value or power value exists; and the protocol is still PRE-FREEZE. The
nine bodies authored before it are byte-identical.

No `PT08` implementation is written or tested here, and no hidden acceptance is
implemented. Pure file and ``git`` inspection; no model is invoked and no benchmark
runs.
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

PT08_PATH = PUBLIC_TASKS_DIR / "PT08.md"
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
GATE_MATRIX = DOCS_V2 / "PILOT_GATE_MATRIX.csv"
RECORD_PATH = DOCS_V2 / "CAND_A1_PREAUTHORING_DECISION.md"
POLICY_PATH = DOCS_V2 / "TASK_AUTHORING_POLICY.md"
FEASIBILITY_PATH = DOCS_V2 / "DEPENDENCY_TASK_FEASIBILITY.md"
BOUNDARY_PATH = DOCS_V2 / "HIDDEN_EVALUATOR_BOUNDARY.md"
SUBSTRATE_IDENTITY = DOCS_V2 / "SOURCE_SUBSTRATE_IDENTITY.md"
DOCS_V2_README = DOCS_V2 / "README.md"

#: The canonical, experiment-neutral source substrate every condition shares.
CANONICAL_SUBSTRATE_COMMIT = "630d3180af0d02a86330dfb599f559e78df65e94"
CANONICAL_SUBSTRATE_CONTENT_HASH = (
    "0198d76c189f38589e872cab4305527c08e86ef736e1550e428e05f9178060f3"
)

PT08_SHA256 = "a31bb515b79cc1e211a662de2a8761c97082dd8bf266ee5b4f660981435badf2"
PT08_TITLE = "Apply a caller-declared maximum total to order creation"

#: The nine bodies that existed before `PT08`. Authoring a task may not touch one.
PRE_EXISTING_HASHES = {
    "PT01": "6c938822fe19cd6e87942a6ee24ec8f604c0883da1b7f80d45216be35d7c9c39",
    "PT02": "ec4b60057708b20cb95e51f000671aab40afc8c55c0bc75850922a5f65841a77",
    "PT03": "cbfce1ca232cb9b6b53e0b4d202d6acee7415b50af8386c1f3bd2147089b4c21",
    "PT04": "f349b150b1d8fe5676fed8460b1840b988ee2bb0a78b1966ef82ae9ce9c8a9b5",
    "PT05": "f6efc772e76d6c287e0c71daaa93c7e1d9e62e72a1b37878df70113269ed27b3",
    "PT06": "3e0f84cfef1f9fbf97e3cd31b6704c3a0fb172b04b5e7bc33ea39927b1c8e0f2",
    "PT07": "557caed09420354efbc823c8b72e54b0760ac72847aba0d9c07d99e37ff7d2d7",
    "PR01": "0e1527bce41498836bb57b802d4566251d6fcfed4cca13fe59e6a97330f02302",
    "PR02": "e89a4aab236813c082f9152db779b8bbfb298148a51a8435a1e2bf38330caa83",
}

#: Eligibility of the nine, which authoring `PT08` must not touch.
PRE_EXISTING_ELIGIBILITY = {
    "PT01": "scored", "PT02": "scored", "PT03": "scored", "PT04": "scored",
    "PT05": "functional-only", "PT06": "functional-only", "PT07": "scored",
    "PR01": "inactive-reserve", "PR02": "inactive-reserve",
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

#: The CURRENT active private state, after PT08's opportunity was admitted.
ACTIVE_OPPORTUNITIES = 6
ACTIVE_CLUSTERS = 3
CLUSTER_DEPTHS = "3 / 2 / 1"

#: The state as recorded before that admission, kept as its own constant so the
#: preserved history can be asserted without any test reading it as current.
PRE_ADMISSION_OPPORTUNITIES = 5
PRE_ADMISSION_CLUSTER_DEPTHS = "3 / 1 / 1"


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


def _pt08_flat() -> str:
    """Normalised `PT08` body: emphasis and backticks dropped, wrapping collapsed."""
    raw = _body(PT08_PATH).replace("*", "").replace("`", "")
    return re.sub(r"\s+", " ", raw).lower()


def _task_files():
    return sorted(
        p for p in PUBLIC_TASKS_DIR.glob("*.md") if re.fullmatch(r"(?:PT|PR)\d{2}", p.stem)
    )


def _git(*args) -> str:
    return subprocess.run(
        ["git", *args], cwd=str(REPO), capture_output=True, text=True, check=True
    ).stdout.strip()


# --------------------------------------------------------------------------- 1
# PART Q.1/Q.2/Q.4 — the body exists, is indexed once, and hashes correctly.


def test_pt08_exists_and_is_the_only_new_body():
    assert PT08_PATH.is_file(), "PT08.md was not authored"
    stems = {p.stem for p in _task_files()}
    assert stems == set(PRE_EXISTING_HASHES) | {"PT08"}, (
        f"exactly one new task body is expected, found {sorted(stems)}"
    )


def test_pt08_is_in_the_task_index_exactly_once():
    ids = [r["task_id"] for r in _rows(INDEX_PATH)]
    assert ids.count("PT08") == 1, f"PT08 appears {ids.count('PT08')} times in TASK_INDEX.csv"
    assert len(ids) == len(PRE_EXISTING_HASHES) + 1 == 10


def test_pt08_hash_is_correct_in_the_file_and_in_both_public_csvs():
    actual = _sha256(PT08_PATH)
    assert actual == PT08_SHA256, (
        f"PT08's body changed: pinned {PT08_SHA256[:16]}..., computed {actual[:16]}...; "
        "update the recorded hash deliberately and re-link any private package"
    )
    assert _by_id(INDEX_PATH)["PT08"]["public_task_sha256"] == PT08_SHA256
    assert _by_id(MATRIX_PATH)["PT08"]["public_task_sha256"] == PT08_SHA256


def test_pt08_body_is_lf_only_so_its_hash_is_platform_stable():
    assert b"\r\n" not in PT08_PATH.read_bytes(), "PT08.md contains CRLF"


def test_pt08_front_matter_matches_the_public_schema():
    import context_audit as ca

    schema = json.loads(_text(SCHEMA_JSON))
    fm = _front_matter(PT08_PATH)
    errors = ca.validate_against_schema(fm, schema)
    assert errors == [], f"PT08 front-matter schema errors: {errors}"
    assert fm["id"] == "PT08"
    assert fm["title"] == PT08_TITLE
    assert fm["category"] == "write-endpoint"
    assert fm["kind"] == "primary"
    assert fm["status"] == "candidate"
    assert fm["visible_validation"] == "npm run ci:agent"
    # the schema stays closed: authoring a task may not add a hidden-answer field
    assert schema["additionalProperties"] is False
    assert set(fm) <= {
        "id", "title", "category", "kind", "status", "visible_validation",
        "leakage_exceptions",
    }
    assert "leakage_exceptions" not in fm, "PT08 needs no reviewed leakage exception"
    # and its category comes from the shared vocabulary, unchanged by this authoring
    yml_enum = yaml.safe_load(_text(SCHEMA_YML))["front_matter"]["category_enum"]
    js_enum = schema["properties"]["category"]["enum"]
    assert fm["category"] in yml_enum and fm["category"] in js_enum
    assert sorted(yml_enum) == sorted(js_enum), "the two category vocabularies drifted"


# --------------------------------------------------------------------------- 2
# PART Q.3 — the nine earlier bodies, hashes and eligibilities are untouched.


@pytest.mark.parametrize("task_id", sorted(PRE_EXISTING_HASHES))
def test_no_pre_existing_task_body_or_hash_changed(task_id):
    path = PUBLIC_TASKS_DIR / f"{task_id}.md"
    expected = PRE_EXISTING_HASHES[task_id]
    assert _sha256(path) == expected, f"{task_id}.md changed while authoring PT08"
    assert _by_id(INDEX_PATH)[task_id]["public_task_sha256"] == expected
    assert _by_id(MATRIX_PATH)[task_id]["public_task_sha256"] == expected


@pytest.mark.parametrize("task_id", sorted(PRE_EXISTING_ELIGIBILITY))
def test_no_pre_existing_eligibility_or_kind_changed(task_id):
    expected = PRE_EXISTING_ELIGIBILITY[task_id]
    for path in (INDEX_PATH, MATRIX_PATH):
        row = _by_id(path)[task_id]
        assert row["e1_analysis_eligibility"] == expected, f"{task_id} in {path.name}"
        assert row["task_status"] == "candidate", f"{task_id} in {path.name}"
    kind = "reserve" if task_id.startswith("PR") else "primary"
    assert _by_id(INDEX_PATH)[task_id]["primary_or_reserve"] == kind


def test_pt04_is_not_rewritten_by_the_replication_authoring():
    """The other instrument in the same cluster must be untouched, not rebalanced."""
    assert _sha256(PUBLIC_TASKS_DIR / "PT04.md") == PRE_EXISTING_HASHES["PT04"]
    row = _by_id(INDEX_PATH)["PT04"]
    assert row["functional_category"] == "logging"
    assert row["e1_analysis_eligibility"] == "scored"
    assert row["title"] == "Emit structured request and error logs for order creation"


# --------------------------------------------------------------------------- 3
# PART Q.5-Q.8 / Q.28 — what public authoring did NOT confer.


def test_pt08_is_not_frozen_and_pins_no_manifest_hash():
    matrix = _by_id(MATRIX_PATH)["PT08"]
    assert matrix["task_status"] == "candidate"
    assert _by_id(INDEX_PATH)["PT08"]["task_status"] == "candidate"
    assert matrix["hidden_evaluator_manifest_hash"] == "stored_in_private_evaluator_repo", (
        "PT08's private package now exists, so its rows carry the withheld "
        "placeholder every other packaged candidate carries; a real hash would "
        "publish private content and would also imply a frozen package"
    )
    assert not re.fullmatch(r"[0-9a-f]{16,}", matrix["hidden_evaluator_manifest_hash"])
    for path in (ACCEPTANCE_MATRIX, LAYER_MATRIX, RULE_MATRIX):
        row = _by_id(path)["PT08"]
        assert row["status"] == "candidate-not-frozen", path.name
        values = ",".join(row.values())
        assert "stored_in_private_evaluator_repo" in values, path.name
        assert "not_yet_authored" not in values, (
            f"{path.name}: PT08's private package exists; 'not_yet_authored' is stale"
        )


def test_pt08_is_not_presented_as_run_ready_frozen_or_validated():
    """The over-claims that stay false, each excluded from the public rows.

    Two of the four this once policed — "no private package" and "review pending" —
    have become true statements about the past and false ones about the present, so
    they are asserted absent here and their history is checked in
    :func:`test_the_public_record_keeps_the_pre_admission_reading_as_history`.
    """
    reason = _by_id(MATRIX_PATH)["PT08"]["e1_eligibility_reason"].lower()
    assert "not run-ready" in reason
    assert "not frozen" in reason
    assert "draft_unvalidated" in reason
    assert "gate g1 is not passed" in reason
    assert "records intent only and never a demonstrated denominator" in reason
    for overclaim in ("run-ready:", "frozen opportunity set is demonstrated",
                      "hidden acceptance is validated", "g1 is passed"):
        assert overclaim not in reason, f"PT08's reason over-claims: {overclaim!r}"
    for stale in ("public-authoring review of this body is pending",
                  "no private evaluator package and no manifest exists for it"):
        assert stale not in reason, f"PT08's reason is stale: {stale!r}"


def test_the_public_rows_record_pt08_like_every_other_packaged_candidate():
    """PART Q.8 / Q.28, inverted: the package exists, so the rows must withhold.

    While no package existed, `not_yet_authored` was the honest placeholder and
    `stored_in_private_evaluator_repo` would have been a false claim. The package
    exists now, so the honest placeholder is the withheld one — and a *real* hash
    still is not, because that would publish private content and imply a freeze.
    """
    checked = 0
    for path in sorted(DOCS_V2.glob("*.csv")) + [INDEX_PATH]:
        rows = _rows(path)
        if not rows or "task_id" not in rows[0]:
            continue
        for row in rows:
            if set(re.findall(r"\b(?:PT|PR)\d{2}\b", row["task_id"])) != {"PT08"}:
                continue
            joined = ",".join(v or "" for v in row.values())
            assert "not_yet_authored" not in joined, (
                f"{path.name}: PT08's package exists; 'not_yet_authored' is stale: "
                f"{joined[:160]}"
            )
            checked += 1
    assert checked >= 4, f"only {checked} PT08-only rows were checked"

    record = _flat(RECORD_PATH)
    assert "private evaluator package | authored" in record
    assert "private manifest | authored, status=review, not frozen" in record
    assert "private architecture opportunity | authored and admitted" in record


def test_the_public_record_keeps_the_pre_admission_reading_as_history():
    """Nothing superseded is erased; it is marked."""
    record = _flat(RECORD_PATH)
    assert record.count("as recorded then: absent") == 3, (
        "each of the three private-side rows must keep its pre-admission reading"
    )
    assert "as recorded then: pending" in record
    assert "as recorded then: none" in record


def test_pt08_is_not_publicly_bound_to_a_rule_or_an_opportunity():
    """The per-task mapping stays private for PT08 exactly as for every other task.

    A row that lists several tasks against the whole implemented leaf family is
    public catalog information, not a per-task binding; a row keyed to PT08 alone,
    or a single clause naming PT08 and a rule id together, is.
    """
    rule_or_opp = re.compile(r"\bAR-[A-Z]+-\d+|\bOPP-|PT08-(?:OPP|EXP)-")
    offenders = []
    for path in sorted(DOCS_V2.glob("*.csv")):
        rows = [r for r in csv.reader(open(path, newline="", encoding="utf-8")) if r]
        header = rows[0]
        key = header.index("task_id") if "task_id" in header else None
        for row in rows[1:]:
            if key is None or key >= len(row):
                continue
            if set(re.findall(r"\b(?:PT|PR)\d{2}\b", row[key])) == {"PT08"}:
                offenders += [
                    f"{path.name} per-task row: {c[:100]}" for c in row if rule_or_opp.search(c)
                ]
    for path in sorted(DOCS_V2.glob("*.md")) + [REPORT_PATH, PT08_PATH]:
        for clause in re.split(r"(?<=[.;:])\s+|\n|\|", _text(path)):
            if "PT08" in clause and rule_or_opp.search(clause):
                offenders.append(f"{path.name} same statement: {clause.strip()[:120]}")
    assert offenders == [], f"PT08 is publicly mapped to a rule or opportunity: {offenders}"


def test_that_mapping_sweep_would_actually_catch_a_binding(tmp_path):
    """Guard the guard: a real disclosure must be rejected, the record must pass."""
    rule_or_opp = re.compile(r"\bAR-[A-Z]+-\d+|\bOPP-|PT08-(?:OPP|EXP)-")
    bad = "PT08 introduces an AR-DEP-006 decision."
    ok = "One new primary task, PT08, has now been authored."
    assert rule_or_opp.search(bad) and "PT08" in bad
    assert not rule_or_opp.search(ok)


# --------------------------------------------------------------------------- 4
# PART Q.9-Q.23 — every pinned wire decision is actually in the public text.


def test_maxtotal_is_an_optional_query_parameter():
    flat = _pt08_flat()
    assert "gains one optional query parameter, maxtotal" in flat
    assert "the optional query parameter maxtotal" in flat


def test_maxtotal_is_not_a_header_and_adds_no_request_body_field():
    """PART Q.10: the carrier decision (`SL-CA1-01`) is visible in the public text.

    Every mention of a header in the body must be one of the three approved
    statements — no request header is added, no response header is required, and any
    response header the service already sets is unchanged. Anything else would be a
    header entering the required behaviour by the back door.
    """
    flat = _pt08_flat()
    assert "adds no request-body field, and it adds no request header" in flat
    allowed = (
        "it adds no request header",
        "no response header is part of this task's required behaviour",
        "any response header the service already sets keeps the behaviour it already has",
        "response headers.",  # the out-of-scope list's own bullet label
    )
    sentences = [s for s in re.split(r"(?<=[.:;])\s+", flat) if "header" in s]
    assert sentences, "the body must state its header position explicitly"
    for sentence in sentences:
        assert any(a in sentence for a in allowed), (
            f"PT08 mentions a header outside its approved statements: {sentence[:160]!r}"
        )
    for phrase in ("request header maxtotal", "header named maxtotal",
                   "x-max-total", "maxtotal header", "in a request header"):
        assert phrase not in flat, f"PT08 introduces a header carrier: {phrase!r}"


def test_absence_of_maxtotal_preserves_existing_behaviour():
    flat = _pt08_flat()
    assert "carries no maxtotal behaves exactly as it does today" in flat
    assert "the same status codes, the same response bodies and the same values" in flat
    assert "no maximum is applied" in flat


def test_zero_is_a_valid_maximum_and_is_not_treated_as_absent():
    flat = _pt08_flat()
    assert "0 is well formed" in flat
    assert "a maximum of zero is a legitimate maximum" in flat
    assert "not treated as an absent parameter" in flat
    # and both zero cases are stated as completion criteria
    assert "sent with ?maxtotal=0 answers http 409" in flat
    assert "sent with ?maxtotal=0 answers http 201" in flat


@pytest.mark.parametrize(
    "case,needle",
    [
        ("negative", "a value beginning with a minus sign"),
        ("empty", "an empty value: ?maxtotal= carries a maxtotal that is present and empty"),
        ("non-numeric", "a value that is not a numeral at all"),
        ("nan-infinity", "any spelling of nan or of infinity"),
        ("repeated", "carries maxtotal more than once"),
    ],
)
def test_every_pinned_malformed_case_is_stated_as_invalid(case, needle):
    """PART Q.13-Q.17: each malformed category, with its own sentence."""
    flat = _pt08_flat()
    assert needle in flat, f"the {case} case is not stated: {needle!r}"


def test_the_malformed_cases_answer_400_with_the_existing_validation_error_body():
    """PART Q.22: one envelope, reused, never a second validation shape."""
    flat = _pt08_flat()
    assert "rejected with http 400 and the body under a maxtotal that is not well formed" in flat
    assert 'error is exactly the string validationerror' in flat
    assert "this is the existing rejection body, reused unchanged" in flat
    assert "introduces no second rejection shape for invalid input" in flat
    assert "adds no key to that body and removes none" in flat
    # the same three keys, in order, in the pinned 400 JSON block
    block = _body(PT08_PATH).split("### A `maxTotal` that is not well formed", 1)[1]
    block = block.split("```", 2)[1]
    assert re.findall(r'"(\w+)":', block) == ["error", "message", "correlationId"]
    assert '"error": "ValidationError"' in block


def test_repeated_maxtotal_is_rejected_and_never_silently_resolved():
    flat = _pt08_flat()
    assert "?maxtotal=50&maxtotal=100" in flat
    assert "one of the repeated values must never be silently chosen and applied" in flat


def test_equality_is_accepted_and_the_maximum_is_inclusive():
    """PART Q.18: the boundary case, stated three independent ways."""
    flat = _pt08_flat()
    assert "the maximum is inclusive" in flat
    assert "t equals maxtotal | ordinary order creation, unchanged" in flat
    assert "a total exactly equal to maxtotal is accepted" in flat
    assert "equality is never a rejection" in flat
    assert re.search(
        r"\?maxtotal=50 .{1,4} the maximum exactly equal to the reported total .{1,4} "
        r"answers http 201",
        flat,
    ), "the equality criterion must be stated with its worked example"


def test_a_total_above_the_maximum_answers_409_ordervaluelimitexceeded():
    """PART Q.19/Q.20/Q.21: status, error value and a CLOSED key set."""
    flat = _pt08_flat()
    assert "t is greater than maxtotal | http 409" in flat
    assert "the request answers http 409 with a json body containing exactly" in flat
    assert "error is exactly the string ordervaluelimitexceeded" in flat
    assert "the body carries no other key: exactly those three, and no fourth" in flat
    assert "never http 400, and never error validationerror" in flat
    # the three keys, in order, and nothing else, in the pinned 409 JSON block
    limit_block = _body(PT08_PATH).split("### A total above the maximum", 1)[1]
    limit_block = limit_block.split("```", 2)[1]
    assert re.findall(r'"(\w+)":', limit_block) == ["error", "message", "correlationId"]
    assert '"error": "OrderValueLimitExceeded"' in limit_block


def test_message_wording_is_unpinned_and_correlationid_is_only_non_empty():
    flat = _pt08_flat()
    assert "its exact wording is not part of the required behaviour" in flat
    assert "correlationid is a non-empty string" in flat
    assert "this task fixes no further requirement on its value" in flat


def test_existing_body_validation_takes_precedence():
    """PART Q.23: one deterministic answer for the overlap, stated functionally."""
    flat = _pt08_flat()
    assert "an invalid request body keeps the answer it already has" in flat
    assert (
        "when the body is invalid and maxtotal is not well formed, the answer is the "
        "one the invalid body already produces on its own" in flat
    )
    assert "does not change it, replace it or suppress it" in flat
    assert "this task re-specifies none of it" in flat
    assert "never http 409, and never a successful creation" in flat
    # and the reason a rejected body cannot reach the ceiling at all
    assert "a request rejected for an invalid body is therefore never answered http 409" in flat


# --------------------------------------------------------------------------- 5
# PART Q.24 — no new money semantics.


@pytest.mark.parametrize(
    "prohibition",
    [
        "no new rounding rule",
        "no new monetary-precision rule",
        "no discount rule",
        "no currency conversion",
        "changes no line-item subtotal and no order total",
        "not rounded, re-scaled or converted before the comparison",
        "no new numeric algorithm is defined anywhere",
    ],
)
def test_pt08_introduces_no_new_monetary_rule(prohibition):
    assert prohibition in _pt08_flat(), f"PT08 no longer states: {prohibition!r}"


def test_the_comparison_is_against_the_total_the_service_already_reports():
    flat = _pt08_flat()
    assert "compared against the very total the service already computes and reports" in flat
    assert "writing t for the total the service reports for that request" in flat


def test_the_worked_examples_stay_exactly_representable():
    """PART J: PT08 must not become a floating-point or cent-exactness task.

    Its examples are integer-valued totals the unchanged substrate reports exactly,
    so no criterion can be satisfied only by repairing PR01's rounding defect, and
    none can fail on sub-cent drift.
    """
    flat = _pt08_flat()
    assert "reports a line-item subtotal of 50 and a total of 50" in flat
    assert '"quantity": 2, "unitprice": 25' in flat
    for fragile in ("0.1", "0.10", "0.7", "0.8999", "15.33", "cent-exact"):
        assert fragile not in flat, f"PT08 uses a drift-prone example: {fragile!r}"
    # and the zero case is reachable through the existing input validation
    assert "quantity 1 and unitprice 0" in flat


# --------------------------------------------------------------------------- 6
# PART Q.25 — no persistence, reset or seam requirement.


def test_pt08_requires_no_seam_no_internal_state_and_no_reset_helper():
    from test_functional_acceptance_boundary import PERSISTENCE_INTERNALS  # noqa: WPS433

    body = _body(PT08_PATH)
    for forbidden in ("LogOutput", "createApp", *PERSISTENCE_INTERNALS):
        assert forbidden not in body, f"PT08 names an application internal: {forbidden}"
    flat = _pt08_flat()
    assert "log output is not part of this task's required behaviour" in flat
    assert "no response header is part of this task's required behaviour" in flat


def test_pt08_states_no_stored_state_criterion():
    """The excluded criterion must not creep in, in either of its two roles.

    "Nothing is stored for a rejected request" is not externally observable at this
    substrate, and requiring it would also outlaw a pre-declared legitimate
    boundary-only implementation. What PT08 requires is only what a caller sees.
    """
    flat = _pt08_flat()
    assert (
        "it states nothing about what the service stores, or does not store, for a "
        "request answered http 409 or http 400" in flat
    )
    assert "every requirement in this task is a status code and a json response body" in flat
    for banned in ("no order is created", "the order must not be created",
                   "must not persist", "does not persist", "not be persisted",
                   "no internal state", "order count", "number of stored orders",
                   "leaves the stored", "side effect", "rollback"):
        assert banned not in flat, f"PT08 states a stored-state criterion: {banned!r}"


def test_the_boundary_audit_records_pt08_as_http_only():
    boundary = re.sub(r"\s+", " ", _text(BOUNDARY_PATH))
    assert re.search(r"\|\s*`PT08`\s*\|\s*HTTP only\s*\|", boundary), (
        "the boundary audit must carry a PT08 row stating HTTP only"
    )
    assert "No other seam is declared" in boundary, (
        "PT04's sink must still be the only seam declared suite-wide"
    )
    flat = _flat(BOUNDARY_PATH)
    assert "no hidden test may add a stored-state assertion" in flat


def test_the_reset_checkpoint_row_is_functional_and_claims_no_implementation():
    row = _by_id(RESET_MATRIX)["PT08"]
    assert row["condition_neutral"] == "yes"
    assert row["status"].strip().upper() == "TODO"
    definition = row["checkpoint_definition"].lower()
    assert "withheld" in definition
    assert "not yet drafted" in definition
    assert "must not rely on any assertion about internal persistence" in definition


# --------------------------------------------------------------------------- 7
# PART Q.26/Q.27 — leakage, judged by the repository's own validator and terms.


def test_pt08_passes_the_repository_leakage_validator_unweakened():
    sys.path.insert(0, str(TASKS_DIR))
    import validate_public_tasks as v  # noqa: WPS433

    terms = v.load_terms()
    assert v.term_ids(terms, "hard_leak"), "the hard-leak tier was emptied"
    assert len(v.term_ids(terms, "review_required")) >= 7

    result = v.validate_task_file(PT08_PATH, terms)
    assert result.ok, (
        f"leakage in PT08: {[f.__dict__ for f in result.findings]} / {result.exception_errors}"
    )
    assert result.findings == [], (
        "PT08 must be clean outright, not clean by way of a reviewed exception"
    )
    assert v.reconcile_with_index(v.discover(TASKS_DIR), INDEX_PATH) == []


@pytest.mark.parametrize(
    "pattern",
    [
        r"\barchitectur", r"\bdependenc", r"\bboundar", r"\blayer", r"\bmodule",
        r"\bport\b", r"\badapter", r"\buse[- ]case", r"\brepositor", r"\bcore\b",
        r"\binfra", r"\bfeatures\b", r"\bcontracts?\b", r"@afci-bench/", r"\bAR-DEP",
        r"\bOPP-", r"\bhidden test", r"\bevaluator\b", r"\boracle\b", r"\bC[1-4]\b",
        r"\bAFCI\b", r"\bscored\b", r"\bapps/", r"\blibs/", r"\bMAD\b",
        r"\bwithheld\b", r"\bcheckpoint\b", r"\bgraded\b",
        r"InternalServerError", r"HTTP 500",
    ],
)
def test_pt08_body_carries_no_hidden_design_vocabulary(pattern):
    """A second, independent reading of the same prohibition.

    The validator above is the authority; this is a deliberately blunt re-check so
    a future edit to the terms file cannot silently make PT08 leaky.
    """
    hits = [m.group(0) for m in re.finditer(pattern, _text(PT08_PATH), re.IGNORECASE)]
    assert not hits, f"PT08 leaks {pattern!r}: {hits}"


def test_no_expected_or_violating_implementation_for_pt08_is_published():
    report = _flat(REPORT_PATH)
    assert "did not publish pt08's hidden opportunity" in report
    assert "any expected violating implementation" in report
    assert not list(PUBLIC_TASKS_DIR.glob("PT08*solution*"))
    assert not list((REPO / "experiments" / "v2").rglob("*pt08*acceptance*"))


# --------------------------------------------------------------------------- 8
# The unspecified spellings are genuinely unspecified (PART H).


@pytest.mark.parametrize(
    "spelling",
    ["1e3", "0x10", "+5", ".5", "5.", "-0", "1,000", "?maxtotal[]=50"],
)
def test_unpinned_numeric_spellings_are_left_out_of_scope(spelling):
    flat = _pt08_flat()
    out_of_scope = flat.split("## out of scope", 1)[1]
    assert spelling in out_of_scope, (
        f"{spelling!r} must be named in the out-of-scope list, so no hidden test may "
        "assert an answer for it"
    )


def test_the_out_of_scope_list_states_that_no_answer_is_required_and_governs():
    flat = _pt08_flat()
    assert (
        "no particular status code and no particular response body is required for "
        "any of them" in flat
    )
    assert (
        "where a spelling listed here could also be read as falling under section 3, "
        "this list governs and the spelling is out of scope" in flat
    )
    report = _flat(REPORT_PATH)
    assert "the hidden functional evaluator may test only the publicly pinned forms" in report
    assert "the out-of-scope list governs over the invalid list where they could overlap" in report


def test_out_of_scope_transport_failures_keep_their_current_handling():
    flat = _pt08_flat()
    assert "a body that cannot be parsed as json" in flat
    assert "keep exactly the handling they have today" in flat
    assert "get /health keeps its current behaviour" in flat


# --------------------------------------------------------------------------- 9
# Registry synchronisation.


@pytest.mark.parametrize("path", TASK_REGISTRIES, ids=lambda p: p.name)
def test_every_required_registry_has_exactly_one_pt08_row(path):
    ids = [r["task_id"] for r in _rows(path)]
    assert ids.count("PT08") == 1, f"{path.name} has {ids.count('PT08')} PT08 rows"


@pytest.mark.parametrize("path", TASK_REGISTRIES, ids=lambda p: p.name)
def test_every_required_registry_covers_every_public_task(path):
    listed = {r["task_id"] for r in _rows(path)}
    expected = {p.stem for p in _task_files()}
    assert expected <= listed, f"{path.name} is missing {sorted(expected - listed)}"


def test_the_index_and_the_public_matrix_agree_on_every_shared_pt08_column():
    index = _by_id(INDEX_PATH)["PT08"]
    matrix = _by_id(MATRIX_PATH)["PT08"]
    for column in set(index) & set(matrix):
        assert index[column] == matrix[column], f"PT08: {column} differs"


def test_the_authoring_report_inventory_carries_pt08():
    report = _text(REPORT_PATH)
    assert re.search(
        r"\|\s*PT08\s*\|\s*primary\s*\|\s*write-endpoint\s*\|\s*\w+\s*\|\s*"
        r"`a31bb515b79cc1e2\.\.\.`\s*\|\s*scored\s*\|",
        report,
    ), "the public task inventory must carry a PT08 row"


def test_pt08_is_listed_as_a_scored_candidate_with_its_caveats():
    trace = {r["oracle_id"]: r for r in _rows(ORACLE_TRACE)}
    assert "PT08" in trace["OT-AC-VIOL"]["task_id"]
    private = trace["OT-TASKS-PRIVATE-SCORED"]
    assert "PT08" in private["task_id"]
    assert "stored_in_private_evaluator_repo" in private["rule_or_criterion_id"]
    assert "not_yet_authored" not in private["rule_or_criterion_id"], (
        "PT08's private package exists; the not-yet-authored mapping is stale"
    )
    notes = private["notes"].lower()
    assert "no private evaluator package of its own yet" not in notes
    assert "adds no active observation to any decision cluster" not in notes
    # what the row must say instead: one applicable opportunity, and no run
    assert "one active applicable opportunity" in notes
    assert "never a violation a success or a result" in notes
    assert "status=review and not frozen" in notes
    assert "draft_unvalidated" in notes
    assert "gate g1 is not passed" in notes


def test_the_new_error_value_is_recorded_in_the_binding_vocabulary():
    report = _text(REPORT_PATH)
    assert re.search(r"\|\s*[^|]*caller-declared maximum\s*\|\s*409\s*\|\s*`OrderValueLimitExceeded`\s*\|",
                     report), "the pinned error-value table must carry PT08's 409 value"
    flat = _flat(REPORT_PATH)
    assert "distinct from conflicterror" in flat and "validationerror" in flat


# --------------------------------------------------------------------------- 10
# PART Q.28-Q.32 — the lifecycle, the counts, and the protocol state.


def test_the_record_maps_cand_a1_to_pt08_only_at_public_authoring():
    flat = _flat(RECORD_PATH)
    assert "cand-a1 → pt08 occurs only at public authoring" in flat
    assert "public task identifier | pt08" in flat
    assert "independent public-authoring review of pt08 | passed" in flat
    assert "as recorded then: pending" in flat, (
        "the pending state must survive as history, not be erased"
    )
    policy = _flat(POLICY_PATH)
    assert "the identifier was assigned at public authoring and nowhere earlier" in policy
    report = _flat(REPORT_PATH)
    assert "the task identifier was adjudicated, not chosen" in report
    assert "the next unused primary identifier under that convention is pt08" in report


def test_the_active_private_state_is_the_admitted_one():
    """PART Q.29, after admission: 6 / 3 / 3-2-1 in the authoritative public places."""
    feasibility = _flat(FEASIBILITY_PATH)
    assert f"active e1 opportunities: {ACTIVE_OPPORTUNITIES}" in feasibility
    assert f"decision clusters: {ACTIVE_CLUSTERS}" in feasibility
    assert "the priority-a row reads 2" in feasibility
    assert f"active e1 opportunities: {PRE_ADMISSION_OPPORTUNITIES}" not in feasibility
    assert "the priority-a row still reads 1" not in feasibility, (
        "the pre-admission depth must not be restated as current"
    )
    record = _flat(RECORD_PATH)
    assert f"active `e1` opportunities are {ACTIVE_OPPORTUNITIES}".replace("`", "") in record
    assert f"cluster observation depths are {CLUSTER_DEPTHS}" in record
    report = _flat(REPORT_PATH)
    assert (
        f"{ACTIVE_OPPORTUNITIES} active e1 opportunities over 3 decision clusters "
        f"at depths {CLUSTER_DEPTHS}" in report
    )


def test_the_pre_admission_state_survives_as_marked_history():
    """PART I: nothing is rewritten. Each superseded count keeps its own marker."""
    for path, needle in (
        (FEASIBILITY_PATH, "was correctly said to add no active observation"),
        (FEASIBILITY_PATH, "the priority-a row read 1"),
        (RECORD_PATH, f"active e1 opportunities remain {PRE_ADMISSION_OPPORTUNITIES}"),
        (RECORD_PATH,
         f"cluster observation depths remain {PRE_ADMISSION_CLUSTER_DEPTHS}"),
        (RECORD_PATH, "an authored public body is not an observation"),
        (REPORT_PATH,
         f"the active set is unchanged at {PRE_ADMISSION_OPPORTUNITIES} opportunities"),
    ):
        flat = _flat(path)
        assert needle in flat, f"{path.name}: superseded statement {needle!r} was erased"
    for path in (FEASIBILITY_PATH, RECORD_PATH, REPORT_PATH):
        assert "as recorded then" in _flat(path), (
            f"{path.name} carries superseded statements with no historical marker"
        )


def test_td_b34_remains_open_and_blocking():
    row = _by_id(DECISIONS_CSV, key="decision_id")["TD-B34"]
    assert row["status"].strip().lower() == "open", (
        "admitting a replication opportunity does not resolve TD-B34"
    )
    assert row["blocking"] == "yes"
    text = row["decision"].lower()
    assert "publicly authored as the task body pt08" in text
    assert "the independent public-authoring review of pt08 has since passed" in text
    assert "the independent public-authoring review of pt08 is pending" not in text
    assert "td-b34 therefore remains open and blocking" in text
    assert "priority b is not started" in text
    report = _flat(REPORT_PATH)
    assert "td-b34 is not resolved by this package" in report
    assert "replication depth is created by an active observation" in report
    assert "td-b34 is still not resolved" in report


def test_gate_g1_is_not_passed_and_no_gate_is():
    gates = {r["gate_id"]: r["status"].strip().lower() for r in _rows(GATE_MATRIX)}
    assert "not evaluated" in gates["G1"], gates["G1"]
    for gate_id, status in gates.items():
        assert "passed" not in status, f"{gate_id} is marked passed"


def test_the_protocol_is_still_pre_freeze_and_no_result_exists():
    assert "PRE-FREEZE DRAFT" in _text(DOCS_V2_README)
    assert "PRE-FREEZE" in _text(REPORT_PATH)
    assert "PRE-FREEZE" in _text(RECORD_PATH)
    for directory in ("results", "analysis"):
        stray = [
            p.name
            for p in (REPO / "experiments" / "v2" / directory).rglob("*")
            if p.is_file() and p.name != "README.md"
        ]
        assert not stray, f"an artifact appeared in experiments/v2/{directory}: {stray}"


def test_no_blocker_was_closed_while_authoring_pt08():
    closed = {
        r["decision_id"]
        for r in _rows(DECISIONS_CSV)
        if r["status"].strip().lower() != "open"
    }
    assert closed == {"TD-B23", "TD-B24", "TD-B38", "TD-B40"}, (
        f"authoring a task changed the resolved set: {sorted(closed)}"
    )
    by_id = _by_id(DECISIONS_CSV, key="decision_id")
    for still_open in ("TD-B34", "TD-B37", "TD-B39", "TD-B05", "TD-B14", "TD-B32",
                       "TD-B26", "TD-B31"):
        assert by_id[still_open]["status"].strip().lower() == "open", still_open


# --------------------------------------------------------------------------- 11
# The substrate is untouched.


def test_no_model_visible_substrate_file_changed_since_the_canonical_substrate():
    changed = _git("diff", "--name-only", CANONICAL_SUBSTRATE_COMMIT, "HEAD").splitlines()
    substrate = [p for p in changed if p.startswith("apps/") or p.startswith("libs/")]
    assert not substrate, f"authoring PT08 touched the shared substrate: {substrate}"


def test_the_canonical_substrate_identity_is_unchanged():
    identity = _text(SUBSTRATE_IDENTITY)
    assert CANONICAL_SUBSTRATE_COMMIT in identity
    assert CANONICAL_SUBSTRATE_CONTENT_HASH in identity


# --------------------------------------------------------------------------- 12
# PART P — PT08 is functionally distinct from the tasks it must not duplicate.


def test_the_report_records_the_pt04_distinctness_without_claiming_independence():
    report = _flat(REPORT_PATH)
    assert "pt08 is a distinct functional instrument from pt04" in report
    for dimension in ("functional pressure", "observable behaviour", "grading channel",
                      "failure cases"):
        assert dimension in report, f"the PT04 comparison omits {dimension!r}"
    assert "this is not a claim of statistical independence" in report
    assert "remain pseudo-replicates" in report
    assert "pt04 is not rewritten, re-hashed, reclassified or touched in any way" in report
    assert "natural-path" in report
    assert "deliberately not in the task body" in report


@pytest.mark.parametrize(
    "guard",
    [
        "pt08 introduces no discount rule",                     # PT05
        "pt08 introduces no cent-exactness requirement",        # PR01
        "introduces no second validation shape",                # PT06
        "pt08 adds no order read, list or count surface",       # PT01/PT02
        "pt08 adds no endpoint and changes no endpoint other than the existing post /orders",  # PT07
        "pt08 adds no status-transition or cancellation behaviour",  # PT03/PR02
    ],
)
def test_every_overlap_safeguard_is_recorded(guard):
    assert guard in _flat(REPORT_PATH), f"the overlap guard is not recorded: {guard!r}"


def test_pt08_does_not_restate_another_task_in_its_own_words():
    """A paraphrase would be a duplicate instrument, not a replication.

    Judged on the observable surface each body pins: PT08's own text must not carry
    another candidate's distinctive requirement.
    """
    flat = _pt08_flat()
    for foreign in ("structured request-log record", "error-log record", "errortype",
                    "volume discount", "10% discount", "0.90", "notfounderror",
                    "conflicterror", "/orders/preview", "cancel"):
        assert foreign not in flat, f"PT08 restates another candidate's surface: {foreign!r}"
