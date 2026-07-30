"""PT06 feasibility: every required behaviour is externally testable at the base.

PT06 previously required a failure that is *not* caused by invalid input to answer
HTTP 500 with ``error`` ``InternalServerError``. No external caller can provoke such
a failure against the unchanged source substrate, so validating it would have needed
a failure-injection hook, a test-only route, a special header, an environment flag or
another implementation-specific seam - and a seam authored for validation is itself a
design answer that would contaminate the substrate every condition shares. PT06 is
re-scoped to the rejection envelope of ``POST /orders``, which is reachable through
the public interface only.

This module asserts the substrate preconditions that make each required behaviour
externally reachable, and the two properties that keep the task honest: that it is
**not already satisfied**, and that it needs **no** injection seam.

* ``POST /orders`` is registered.
* JSON body parsing is enabled for it, so an unparseable JSON body is externally
  submittable and is rejected before the route body runs.
* Each semantic-invalid case PT06 names publicly is an existing validation rule,
  reachable from the current create-order input.
* The create-order rejection path already answers HTTP 400 with the three-key
  envelope and ``error`` exactly ``ValidationError``, through the framework's JSON
  response helper - so the ``application/json`` media type PT06 pins is an
  already-satisfied property of that path and only has to be preserved there.
* The success path already answers HTTP 201, so "unchanged on success" is meaningful.
* No JSON-parse-failure branch and no response-shaping error handler exist yet, so
  the unparseable-JSON body cannot yet receive that envelope: the task requires a
  genuine implementation change and the two failure kinds are not already identical.
* Neither PT06's text nor the substrate carries an injection seam, and PT06 requires
  no unprovokable failure and no new endpoint.

Pure file inspection. No model is invoked, no benchmark runs, and this module asserts
nothing about *how* a solution should be structured - only that the behaviour PT06
requires is externally observable at the base.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[4]
API_APP = REPO / "apps" / "api" / "src" / "app.ts"
CORE = REPO / "libs" / "core" / "src" / "index.ts"
FEATURES = REPO / "libs" / "features" / "src" / "index.ts"
CONTRACTS = REPO / "libs" / "contracts" / "src" / "index.ts"
PT06 = REPO / "experiments" / "v2" / "tasks" / "public" / "PT06.md"

ENVELOPE_KEYS = ("error", "message", "correlationId")

#: Each publicly named semantic-invalid case, with the substrate evidence that the
#: rule already exists. (public phrase in PT06, file, regex proving the rule.)
SEMANTIC_CASES = (
    (
        "empty customerId",
        "`customerId` present but empty",
        CORE,
        r"customerId\.trim\(\)\s*===\s*''",
    ),
    (
        "empty items array",
        "`items` present but empty",
        CORE,
        r"items\.length\s*===\s*0",
    ),
    (
        "non-positive quantity",
        "`quantity` is not a positive number",
        CORE,
        r"item\.quantity\s*<=\s*0",
    ),
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def app_src() -> str:
    return _text(API_APP)


@pytest.fixture(scope="module")
def pt06() -> str:
    return _text(PT06)


# --------------------------------------------------------------------------- #
# 1. The endpoint PT06 targets exists
# --------------------------------------------------------------------------- #
def test_post_orders_endpoint_exists(app_src):
    assert re.search(r"""\.post\(\s*['"]/orders['"]""", app_src), (
        "PT06 targets POST /orders; the base substrate no longer registers it"
    )


def test_pt06_targets_that_endpoint_and_creates_no_new_one(pt06):
    assert "POST /orders" in pt06
    assert "No new endpoint" in pt06, (
        "PT06 must keep stating that no new endpoint is required"
    )


# --------------------------------------------------------------------------- #
# 2. Malformed JSON is externally submittable
# --------------------------------------------------------------------------- #
def test_json_body_parsing_is_enabled_so_an_unparseable_body_is_submittable(app_src):
    """A JSON body parser is installed for the request pipeline.

    This is what makes PT06's second failure kind externally triggerable with nothing
    but an HTTP request: a caller sends an unparseable body with
    ``Content-Type: application/json`` and the parse fails before the route body runs.
    """
    assert re.search(r"express\.json\(\)", app_src), (
        "no JSON body parsing is enabled; an unparseable JSON body would not be "
        "rejected at parse time and PT06's second failure kind would be unreachable"
    )


def test_pt06_states_the_malformed_json_case_with_the_json_content_type(pt06):
    assert "not parseable JSON" in pt06
    assert "Content-Type: application/json" in pt06


# --------------------------------------------------------------------------- #
# 3. Every publicly named semantic-invalid case is an existing rule
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "label,public_phrase,source,rule_re",
    SEMANTIC_CASES,
    ids=[c[0] for c in SEMANTIC_CASES],
)
def test_named_semantic_case_is_an_existing_validation_rule(
    label, public_phrase, source, rule_re, pt06
):
    assert public_phrase in pt06, f"PT06 no longer names the {label} case"
    assert re.search(rule_re, _text(source)), (
        f"PT06 names the {label} case, but the base substrate has no such validation "
        "rule; a public task may not invent a domain rule to create a test case"
    )


def test_at_least_two_semantic_cases_are_named(pt06):
    named = [c for c in SEMANTIC_CASES if c[1] in pt06]
    assert len(named) >= 2, (
        "PT06 must publicly name at least two externally triggerable semantic-invalid "
        f"cases; found {len(named)}"
    )


def test_the_named_rules_are_reachable_from_the_create_order_input():
    """The rules are applied to the create-order request, not merely present."""
    features = _text(FEATURES)
    assert "validateCustomerId(input.customerId)" in features
    assert "validateOrderItems(input.items)" in features
    contracts = _text(CONTRACTS)
    for field in ("customerId", "items", "quantity"):
        assert field in contracts, f"{field} is not part of the public request shape"


# --------------------------------------------------------------------------- #
# 4. The semantic-validation envelope exists; the malformed-JSON one does not
# --------------------------------------------------------------------------- #
def test_semantic_rejection_already_answers_400_with_the_three_key_envelope(app_src):
    assert "'ValidationError'" in app_src or '"ValidationError"' in app_src
    assert re.search(r"\.status\(400\)", app_src)
    for key in ENVELOPE_KEYS:
        assert key in app_src, f"the rejection body has no {key} key at the base"


def test_the_semantic_rejection_already_declares_a_json_media_type(app_src):
    """PT06 pins a JSON response media type; on the preserved path it already holds.

    The create-order rejection is sent through the framework's JSON response helper,
    which declares an ``application/json`` media type. So the media-type requirement
    PT06 states is satisfied already for the semantic-validation kind and only has to
    be *preserved* there - it invents no behaviour the substrate cannot produce. This
    asserts an existing property of the base, not a way to build the other path.
    """
    assert re.search(r"\.status\(400\)\.json\(", app_src), (
        "the create-order rejection no longer answers through the JSON response "
        "helper, so PT06's application/json media-type requirement would no longer "
        "be an already-satisfied property of the preserved path"
    )


def test_pt06_states_the_json_media_type_requirement(pt06):
    """The requirement is public, so no unstated media type can be enforced."""
    assert "application/json" in pt06
    assert "Content-Type" in pt06
    assert "media type" in pt06.lower(), (
        "PT06 must state the response media-type requirement in words, not leave it "
        "implicit in 'the body is JSON'"
    )


def test_the_envelope_keys_are_the_public_response_shape():
    contracts = _text(CONTRACTS)
    for key in ENVELOPE_KEYS:
        assert key in contracts, (
            f"{key} is not part of the public error response shape, so PT06 would be "
            "requiring an unstated key"
        )


def test_no_parse_failure_branch_exists_yet(app_src):
    """Premise of the task: nothing turns a parse failure into the envelope.

    A body-parser failure is raised before the route body runs, and the substrate has
    no branch that inspects it. Were such a branch present, PT06 would risk being
    already satisfied.
    """
    for marker in ("entity.parse.failed", "SyntaxError", "body-parser"):
        assert marker not in app_src, (
            f"the substrate already inspects a parse failure ({marker}); re-check "
            "whether PT06 is still an unsatisfied requirement"
        )


def test_no_response_shaping_error_handler_exists_yet(app_src):
    """No four-argument error handler is registered, so a parse failure is answered by
    the framework default rather than by the service's own body."""
    four_arg = re.search(
        r"\(\s*\w+\s*:\s*\w+[^)]*,\s*\w+\s*:\s*\w+[^)]*,\s*\w+\s*:\s*\w+[^)]*,"
        r"\s*\w+\s*:\s*\w+[^)]*\)\s*=>",
        app_src,
    )
    assert four_arg is None, (
        "an error handler already shapes failure responses; re-check whether the "
        "malformed-JSON body already receives the envelope"
    )
    assert "app.use(" in app_src, "premise: the request pipeline is composed with app.use"


def test_the_error_handler_guard_would_detect_one():
    """Guard the guard: the four-argument check must not be vacuously true."""
    pattern = re.compile(
        r"\(\s*\w+\s*:\s*\w+[^)]*,\s*\w+\s*:\s*\w+[^)]*,\s*\w+\s*:\s*\w+[^)]*,"
        r"\s*\w+\s*:\s*\w+[^)]*\)\s*=>",
    )
    handler = (
        "app.use((err: Error, req: Request, res: Response, next: NextFunction) => {"
    )
    route = "app.post('/orders', async (req: Request, res: Response) => {"
    assert pattern.search(handler), "the guard would miss a real error handler"
    assert pattern.search(route) is None, "the guard would misfire on an ordinary route"


def test_the_two_failure_kinds_are_not_already_identical(app_src):
    """The 400 envelope is built inside the create-order route body only.

    The route body is never entered when body parsing fails, so today the two failure
    kinds cannot already agree in every required respect: exactly one of them produces
    the envelope. This is the change PT06 asks for.
    """
    route = re.search(
        r"""\.post\(\s*['"]/orders['"][\s\S]*?\n  \}\);""", app_src
    )
    assert route is not None, "could not locate the create-order route body"
    body = route.group(0)
    assert "ValidationError" in body, (
        "the 400 envelope is no longer built inside the create-order route body; "
        "re-derive whether the malformed-JSON path already shares it"
    )


# --------------------------------------------------------------------------- #
# 5. Success behaviour exists and can be preserved
# --------------------------------------------------------------------------- #
def test_successful_creation_exists_and_is_pinned_as_unchanged(app_src, pt06):
    assert re.search(r"\.status\(201\)", app_src), (
        "no successful create-order response exists, so 'unchanged on success' would "
        "be unverifiable"
    )
    assert "201" in pt06
    assert "unchanged" in pt06.lower()


# --------------------------------------------------------------------------- #
# 6. No hidden internal failure injection is needed or requested
# --------------------------------------------------------------------------- #
def test_pt06_requires_no_failure_an_external_caller_cannot_provoke(pt06):
    for forbidden in ("500", "InternalServerError"):
        assert forbidden not in pt06, (
            f"PT06 mentions {forbidden}; an unexpected-server-failure requirement is "
            "not externally triggerable at the base substrate"
        )
    lowered = pt06.lower()
    for forbidden in (
        "storage failure",
        "while the order is being stored",
        "internal failure",
        "injection",
        "test-only",
        "environment flag",
        "environment variable",
    ):
        assert forbidden not in lowered, f"PT06 leans on an internal seam: {forbidden}"


def test_the_substrate_carries_no_validation_seam(app_src):
    """No seam was added to make PT06 observable."""
    for seam in ("process.env", "__test", "x-force-", "x-fail", "failNext", "throwOn"):
        assert seam not in app_src, (
            f"the create-order composition carries a possible validation seam ({seam})"
        )


def test_pt06_exposes_only_the_agent_ci_command(pt06):
    assert "npm run ci:agent" in pt06
    for other in ("npm run ci\n", "npm run test", "npm run lint", "npm run typecheck"):
        assert other not in pt06, f"PT06 exposes a second validation command: {other!r}"
