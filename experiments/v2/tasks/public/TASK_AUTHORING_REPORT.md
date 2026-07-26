# AFCI-Bench v2 - Public Task Authoring Report

Status: **candidate** pilot task materials - authored and repaired, NOT approved, NOT frozen. The scientific protocol remains **PRE-FREEZE**. No benchmark run, paid model call, or task-count freeze accompanies this report.

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
| PT06 | **Impossible at the frozen base.** It asked to standardise not-found handling "across order endpoints" while forbidding new endpoints - but the base substrate has no endpoint that addresses an order by identifier and no 404 path at all, so no conforming solution existed. | **Rewritten** against the endpoint that does exist. New title: *Return a consistent error envelope for order-creation failures*. It now targets `POST /orders`, pins HTTP 400 + `ValidationError` for invalid input (including an unparseable JSON body, which today is answered with a non-JSON default error) and HTTP 500 + `InternalServerError` for a failure that is not caused by invalid input (today such a failure is reported as HTTP 400 `ValidationError`). |
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
| Unexpected server failure | 500 | `InternalServerError` |

Binding constraints on every private evaluator package built for these candidates:

1. Where a task pins an `error` value, the hidden acceptance test asserts that exact string.
2. Where a task explicitly does **not** pin a value - the `errorType` of PT04's error-log record is the only such case in this suite - the hidden acceptance test may assert **only** that the value is a non-empty string. It may assert the HTTP status, the presence of a non-empty `error`, and the presence of a non-empty `message`, and nothing more.
3. `message` is free text everywhere; no hidden test may assert its wording.
4. `correlationId` remains present on every error body, exactly as the base substrate already returns it. A visible test in the repository asserts it, so removing it would break `npm run ci:agent`; the two documented failure keys are `error` and `message`.
5. Where a task states that ordering is not part of the required behaviour (PT02's `orders` array), hidden validation **must** be order-independent.
6. No hidden test may assert a key, string, status code or ordering that the public task body does not state.

## Feasibility against the frozen base substrate

Every candidate was re-checked against the base substrate rather than against an assumed one. The base exposes exactly two endpoints (`GET /health`, `POST /orders`), has no 404 handling, and stubs the repository read paths at the composition root. Each task either targets behaviour that exists or creates the endpoint it describes, and no completion criterion depends on an endpoint the task neither has nor creates.

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
| PT06 | primary | error-handling | medium | `3994a158ad39f629...` |
| PR01 | reserve | calculation | small | `0e1527bce4149883...` |
| PR02 | reserve | write-endpoint | medium | `e89a4aab236813c0...` |

Only PT05 is byte-identical to the previously recorded suite; the other seven changed.

## Private evaluator package staleness (mandatory)

The private evaluator commit that was created against the **previous** public task hashes is **stale** and must be treated as such:

- it **must not** be reviewed, approved, frozen, or used for Stage 0 or any pilot;
- every private per-task manifest, hidden acceptance plan, fixed opportunity set, expected/prohibited area set, legitimate-alternative list and reset predicate must be **re-authored or re-linked** against the new public task hashes above - PT04 and PT06 changed subject matter entirely, so their hidden packages must be re-authored, not merely re-hashed;
- a private manifest hash must **never** be silently accepted against a changed public task: the pinned public-task hash is part of the package's identity, and a mismatch is a hard failure, not a warning;
- re-linking may only happen **after** this public work package is independently approved, so the hashes it pins are the approved ones;
- the oracle continues to refuse to score a non-frozen manifest (`MANIFEST_NOT_FROZEN`).

The private evaluator repository was **not** accessed, inspected, or modified while producing this report. Its filesystem location is deliberately not recorded in any public file.

## Model-visible worktree isolation

The review also found that the coding model's worktree was the whole repository, which placed `docs/v2/ARCHITECTURE_CONTEXT.md` and `docs/v2/ARCHITECTURE_RULE_CATALOG.yml` inside every condition's workspace including the C1 baseline. An allowlist-first, fail-closed preparation mechanism now builds the model-visible worktree from the source substrate only (`docs/v2/MODEL_VISIBLE_WORKTREE_POLICY.md`, `experiments/v2/harness/prepare_model_worktree.py`). Runner-time enforcement is the new blocking decision **TD-B22** and is **not** implemented.

## What was deliberately NOT done

- No task was selected, rejected, or difficulty-tuned using any observed or expected AFCI advantage (CRITICAL_DESIGN_DECISIONS D3/D10).
- No candidate task was implemented; no reference or expected solution exists in this repository.
- No hidden acceptance test or hidden evaluator answer was added publicly.
- **No final task count**, repetition count, run count, model, or numerical budget was selected. The eight candidates are candidates, not a core-study task set.
- No hidden evaluator package was frozen; the oracle continues to refuse to score a review-status package (`MANIFEST_NOT_FROZEN`).
- Task-specific oracle validity, hidden-acceptance validation, reset checkpoint review, and benchmark discrimination remain open (G1/G2 not passed).
