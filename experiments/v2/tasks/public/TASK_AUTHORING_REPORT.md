# AFCI-Bench v2 - Public Task Authoring Report

Status: **candidate** pilot task materials - authored, repaired, and amended (PT06), NOT approved, NOT frozen. The scientific protocol remains **PRE-FREEZE**. No benchmark run, paid model call, or task-count freeze accompanies this report.

## What was authored

- Six primary pilot task candidates (PT01-PT06) and two pre-declared reserve candidates (PR01-PR02).
- Each public task body states functional requirements and observable behaviour only; the single visible validation command is `npm run ci:agent`.
- Every hidden evaluator package for these candidates is stored **only** in a separate local private evaluator repository and is absent from this public repository.

## Coverage

The six primary candidates were selected, before any model outcome existed, to collectively span the pre-declared coverage areas recorded in the private selection policy and coverage matrix. The per-candidate coverage mapping is a hidden design detail and is withheld from this public report.

## Repairs applied after independent public review

An independent review of the first authored suite found four task defects that would have invalidated the resulting evidence, plus two fairness gaps. All are repaired here. **Every repaired task body has a new SHA-256** (see the inventory below).

| Task | Defect found | Repair |
| --- | --- | --- |
| PT06 | **Impossible at the frozen base.** It asked to standardise not-found handling "across order endpoints" while forbidding new endpoints - but the base substrate has no endpoint that addresses an order by identifier and no 404 path at all, so no conforming solution existed. | **Rewritten** against the endpoint that does exist: `POST /orders`. Superseded by the PT06 amendment below, which removed the remaining externally untestable part of that rewrite. |
| PT04 | **Partly unsatisfiable.** It required log records for "any order-read endpoint" and for "a failing read", but the only read endpoint at the base is `GET /health`, which has no failure path. | **Rewritten** onto traffic that exists. New title: *Emit structured request and error logs for order creation*. It now targets `POST /orders` and names every asserted key: `correlationId`, `method`, `path`, `statusCode`, `status`, `operation`, `latencyMs` on the request record, and `correlationId`, `errorType`, `message` on the error record, which must carry no `stack` key. |
| PT02 | **Undefined response wire format.** "a JSON body containing the customer identifier, the array of matching orders, and the number of orders returned" named no keys, so a correct implementation could still fail on a guessed name. | Response body pinned to exactly `{ "customerId", "orders", "count" }`, with `count` equal to the number of elements in `orders`, the empty case pinned, and array order explicitly **not** part of the required behaviour (validation must be order-independent). |
| PT03 | **Undefined request wire format.** "a target status in its JSON body" named no key, so the grader could not even drive the endpoint. Its observability criterion ("visible on a later read") also had no read endpoint at the base. | Request body pinned to exactly `{ "status": "<value>" }`; the five accepted values are listed explicitly; every status code and `error` value is pinned; persistence is now observed by repeating the request, which needs no endpoint the task does not create. |
| PR01 | **Demonstrating example already passed.** Its only worked example (three items at 15.33 summing to 45.99) is already exact at the base and is already asserted by an existing visible test, so a model would see nothing to fix. | Example replaced with one that exposes the real defect: unit prices `0.10`, `0.10`, `0.70` return `0.8999999999999999` today and must return exactly `0.90`. |
| PR02 | Same unobservable "later fetch" criterion as PT03. | Persistence is now observed by repeating the (idempotent) cancel request. Error values pinned. |

## Error-contract values (binding on private evaluator packages)

Public tasks now state every response key, request key, status code and asserted `error` value, so no hidden test can enforce an unstated string. The pinned vocabulary is:

| Situation | HTTP status | `error` value |
| --- | --- | --- |
| Order not found | 404 | `NotFoundError` |
| Malformed or unknown input (including unparseable JSON) | 400 | `ValidationError` |
| Forbidden state transition | 409 | `ConflictError` |

No candidate pins an unexpected-server-failure status or `error` value any more: the
PT06 amendment below removed the only such requirement, because no external caller
can provoke that failure at the base substrate without an injection seam. A hidden
test may therefore not assert a 500 response for any candidate in this suite.

Binding constraints on every private evaluator package built for these candidates:

1. Where a task pins an `error` value, the hidden acceptance test asserts that exact string.
2. Where a task explicitly does **not** pin a value - the `errorType` of PT04's error-log record is the only such case in this suite - the hidden acceptance test may assert **only** that the value is a non-empty string. It may assert the HTTP status, the presence of a non-empty `error`, and the presence of a non-empty `message`, and nothing more.
3. `message` is free text everywhere; no hidden test may assert its wording.
4. `correlationId` remains present on every error body, exactly as the base substrate already returns it. A visible test in the repository asserts it, so removing it would break `npm run ci:agent`; the two documented failure keys are `error` and `message`.
5. Where a task states that ordering is not part of the required behaviour (PT02's `orders` array), hidden validation **must** be order-independent.
6. No hidden test may assert a key, string, status code or ordering that the public task body does not state.

## PT06 amendment: every required behaviour is externally testable

A further review of the repaired suite found that PT06 still required one behaviour
that **no external caller can provoke** against the unchanged source substrate: a
failure that is not caused by invalid input, answered with HTTP 500 and `error`
`InternalServerError`. At the base substrate the create-order path has no such
externally reachable failure. Validating it would have required a failure-injection
hook, a test-only route, a special header, an environment flag or another
implementation-specific seam in the source substrate - none of which exists, and
none of which may be introduced, because a seam authored for validation is itself a
design answer and would contaminate the substrate every condition shares.

PT06 is therefore re-scoped to behaviour that is reachable through the public
interface only. New title: *Return a consistent validation-error envelope for order
creation*. It still targets `POST /orders` and still asks for **one** rejection
envelope, but both of its failure kinds are now externally triggerable:

| Required behaviour | How an external caller triggers it | Status at the base |
| --- | --- | --- |
| HTTP 400 + `error` `ValidationError` + non-empty `message` + non-empty `correlationId` for input that fails the existing validation | send a create-order request with an empty `customerId`, an empty `items` array, or an `items` entry whose `quantity` is not positive | already the behaviour; must be preserved |
| The same HTTP 400 body for a body that cannot be parsed as JSON | send an unparseable body with `Content-Type: application/json` | answered 400, but as an HTML error page with none of the three keys - this is the change the task requires |
| HTTP 201 and the existing response body on success | send a valid create-order request | already the behaviour; must be preserved |

The removed HTTP 500 requirement is **not** replaced by an internal-failure
requirement of any other kind. No private test may induce a storage, logging or
other internal failure to grade PT06, and no private test may assert a 500 response.

Three concrete semantic-invalid cases are named publicly, all of them existing
validation rules of the current create-order input - no new domain rule was invented
to create a test case:

1. `customerId` present but empty (`""`), with an otherwise valid `items` entry.
2. `items` present but empty (`[]`), with an otherwise valid `customerId`.
3. An `items` entry whose `quantity` is not a positive number (for example `0`).

Feasibility was verified against the unchanged substrate rather than assumed, in two
ways.

**A committed static contract test**,
`experiments/v2/harness/tests/test_pt06_feasibility.py`, asserts the substrate
preconditions that make each required behaviour externally reachable: `POST /orders`
is registered; JSON body parsing is enabled for it, so an unparseable body is
externally submittable; the three semantic-invalid cases above are existing
validation rules, each reachable from the create-order input; the create-order
rejection path builds the three-key envelope with `error` `ValidationError` and HTTP
400; the success path answers HTTP 201; **no** JSON-parse-failure branch and **no**
response-shaping error handler exist yet, so the unparseable-JSON body cannot yet
receive that envelope and the task therefore requires a genuine implementation
change; and neither PT06's text nor the substrate contains a failure-injection hook,
test-only route, special header or environment flag seam. The test also pins that
PT06 requires no unprovokable failure (no 500 requirement, no
`InternalServerError`, no induced internal failure) and no new endpoint. It is pure
file inspection; no model and no benchmark run is involved.

**An out-of-tree runtime probe** (run against the unchanged substrate from a scratch
directory, committed nowhere, changing no repository file) confirmed the observed
behaviour the static test reasons about: empty `customerId`, empty `items` and
`quantity: 0` each answer HTTP 400 `application/json` with
`{"error":"ValidationError","message":<non-empty>,"correlationId":<non-empty>}`; an
unparseable body sent as `application/json` answers HTTP 400 with
`Content-Type: text/html`, an HTML error page, none of the three keys and no
correlation-id response header; and a valid request answers HTTP 201 with the
existing response body. The two failure kinds are therefore **not** already
identical in every required respect.

The task's scope classification (`medium`) and its single visible validation command
(`npm run ci:agent`) are unchanged.

PT06's SHA-256 changed with this amendment
(`3994a158ad39f629...` -> `ae87303c6be53fe1...`). **No other task body changed**, so
every other pinned public-task hash recorded at public commit `0e77d49` still holds.

## Feasibility against the frozen base substrate

Every candidate was re-checked against the base substrate rather than against an assumed one. The base exposes exactly two endpoints (`GET /health`, `POST /orders`), has no 404 handling, and stubs the repository read paths at the composition root. Each task either targets behaviour that exists or creates the endpoint it describes, and no completion criterion depends on an endpoint the task neither has nor creates.

Since the PT06 amendment, a second feasibility bar also holds for every candidate: **no completion criterion depends on a failure that an external caller cannot provoke** through the public interface. PT06 was the only candidate that failed this bar, and it no longer does.

## Leakage validation

The public-task leakage validator (`experiments/v2/tasks/validate_public_tasks.py`, terms in `docs/v2/TASK_LEAKAGE_TERMS.yml`) was run over every authored public task body. Result: **OK for every task** (no hard leak; no uncovered review-required term; no reviewed exceptions were needed), with a hardened validator that now also scans front matter, detects hard-wrapped phrases, covers all twelve prohibited leakage families, discovers task bodies recursively, and reconciles them against `TASK_INDEX.csv`.

A clean result means **no detected leakage**. It is not proof of scientific validity. This advances TD-B17 for the authored draft suite; **TD-B17 remains open** pending independent review at freeze.

## Public task inventory

| Task | Kind | Category | Scope | Public task SHA-256 |
| --- | --- | --- | --- | --- |
| PT01 | primary | read-endpoint | small | `6c938822fe19cd6e...` |
| PT02 | primary | list-endpoint | medium | `ec4b60057708b20c...` |
| PT03 | primary | write-endpoint | medium | `cbfce1ca232cb9b6...` |
| PT04 | primary | logging | medium | `f349b150b1d8fe56...` |
| PT05 | primary | calculation | medium | `f6efc772e76d6c28...` |
| PT06 | primary | error-handling | medium | `ae87303c6be53fe1...` |
| PR01 | reserve | calculation | small | `0e1527bce4149883...` |
| PR02 | reserve | write-endpoint | medium | `e89a4aab236813c0...` |

Relative to the suite recorded before the repair package, only PT05 is byte-identical
and the other seven changed. Relative to public commit `0e77d49`, **only PT06
changed**: it carries the amended body above, and the other seven bodies are
byte-identical to their `0e77d49` bytes.

## Private evaluator package staleness (mandatory)

The private evaluator commit that was created against the **hashes recorded before the
repair package** is **stale** and must be treated as such:

- it **must not** be reviewed, approved, frozen, or used for Stage 0 or any pilot;
- every private per-task manifest, hidden acceptance plan, fixed opportunity set, expected/prohibited area set, legitimate-alternative list and reset predicate must be **re-authored or re-linked** against the new public task hashes above - PT04 and PT06 changed subject matter entirely, so their hidden packages must be re-authored, not merely re-hashed;
- a private manifest hash must **never** be silently accepted against a changed public task: the pinned public-task hash is part of the package's identity, and a mismatch is a hard failure, not a warning;
- re-linking may only happen **after** this public work package is independently approved, so the hashes it pins are the approved ones;
- the oracle continues to refuse to score a non-frozen manifest (`MANIFEST_NOT_FROZEN`).

### Staleness introduced by the PT06 amendment (scope: PT06 only)

A private evaluator commit was subsequently created against the public task bytes of
public commit `0e77d49` (private commit `5733ca6`). The PT06 amendment above changes
**only** PT06's public bytes, so its effect on that private commit is exactly scoped:

- **only PT06's private package becomes stale** because of this amendment;
- the **seven** packages other than PT06 - PT04 among them - remain linked to the
  public task bytes that were independently reviewed at public commit `0e77d49`, which
  are byte-identical to the bytes recorded here, so they need no re-linking for this
  amendment;
- PT06's private package must be **substantively re-authored**, not merely re-hashed:
  its subject matter changed again (the unexpected-server-failure requirement is gone
  and the rejection envelope now covers the unparseable-JSON path), so its hidden
  acceptance plan, expected/prohibited areas, fixed opportunity set,
  legitimate-alternative list and reset predicate must all be reconsidered against the
  amended public text;
- re-authoring may only happen **after** this public amendment is independently
  approved, so the hash it pins (`ae87303c6be53fe1...`) is the approved one;
- private commit `5733ca6` **must not be reviewed as a complete eight-task package**
  until PT06 is updated. Reviewing it as complete would review a PT06 package built
  against superseded public bytes;
- as before, a private manifest hash must never be silently accepted against a changed
  public task, and every private manifest remains status `review` (not frozen).

The private evaluator repository was **not** accessed, inspected, or modified while producing this report or this amendment. Its filesystem location is deliberately not recorded in any public file, and no private manifest, hidden plan or other private content is reproduced here - the private commit identifier above is an identifier only.

## Model-visible worktree isolation

The review also found that the coding model's worktree was the whole repository, which placed `docs/v2/ARCHITECTURE_CONTEXT.md` and `docs/v2/ARCHITECTURE_RULE_CATALOG.yml` inside every condition's workspace including the C1 baseline. An allowlist-first, fail-closed preparation mechanism now builds the model-visible worktree from the source substrate only (`docs/v2/MODEL_VISIBLE_WORKTREE_POLICY.md`, `experiments/v2/harness/prepare_model_worktree.py`). Runner-time enforcement is the new blocking decision **TD-B22** and is **not** implemented.

## What was deliberately NOT done

- No task was selected, rejected, or difficulty-tuned using any observed or expected AFCI advantage (CRITICAL_DESIGN_DECISIONS D3/D10).
- No candidate task was implemented; no reference or expected solution exists in this repository. PT06 in particular was **not** implemented as part of its amendment.
- **No validation seam was added to the source substrate.** No failure-injection hook, test-only route, special header, environment flag or other implementation-specific seam was introduced to make any requirement observable; `apps/` and `libs/` are byte-identical to their state at public commit `0e77d49`.
- No hidden acceptance test or hidden evaluator answer was added publicly.
- **No final task count**, repetition count, run count, model, or numerical budget was selected. The eight candidates are candidates, not a core-study task set.
- No hidden evaluator package was frozen; the oracle continues to refuse to score a review-status package (`MANIFEST_NOT_FROZEN`).
- Task-specific oracle validity, hidden-acceptance validation, reset checkpoint review, and benchmark discrimination remain open (G1/G2 not passed).
