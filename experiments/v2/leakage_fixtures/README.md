# experiments/v2/leakage_fixtures — source-comment leakage regression fixtures

Fixtures for the **model-visible source-comment leakage audit**
(`prepare_model_worktree.scan_source_comment_disclosures`, exercised by
`experiments/v2/harness/tests/test_model_worktree_preparation.py`).

Background: `TD-B23` recorded that model-visible TypeScript comments in the
shared substrate explicitly stated scored dependency rules to **every**
condition, including the no-guidance C1 baseline, and `TD-B24` recorded that the
worktree leakage sweep matched only file basenames and directory names, so it
could never have detected them. The comments were neutralised in
`apps/api/src/app.ts`, `libs/infra/src/index.ts` and `libs/features/src/index.ts`;
these fixtures preserve the **exact removed bytes** so the repaired scanner is
proved against the real historical leak rather than a paraphrase of it.

## Why these are not a leak themselves

They live under `experiments/`, which is in `FORBIDDEN_DIR_NAMES` and is not in
`ALLOWED_TREES`, so nothing here can enter a model-visible worktree. They use the
`.ts.fixture` extension so no nx project lints them and `tsc` does not compile
them. They are outside `experiments/v2/tasks/`, so the public-task leakage
validator does not scan them either.

## Positive fixtures — each MUST be detected

| File | Historical source | Discloses |
| --- | --- | --- |
| `td_b23_api_core_boundary.ts.fixture` | `apps/api/src/app.ts` lines 12-17 | the `api -> core` prohibition, an architecture-CI consequence, and a worked commented-out forbidden import |
| `td_b23_infra_core_avoidance.ts.fixture` | `libs/infra/src/index.ts` lines 4-5 | the `infra -> core` prohibition, justified as a deliberate architectural choice |
| `td_b23_features_reexport_rationale.ts.fixture` | `libs/features/src/index.ts` line 15 | the `api -> core` prohibition restated from the `features` side |

## Negative fixture — MUST NOT be detected

`neutral_implementation_comments.ts.fixture` collects the comments the substrate
**keeps**: comments that name layers, modules and imports while stating no rule.
A scanner that flags any line in this file is over-broad and would strip the
ordinary implementation prose that keeps the substrate realistic.

## Known and accepted over-breadth

The detector treats a bare layer word (`core`, `infra`, `api`, ...) as an
architectural subject, because the historical leak used exactly that form
(`api cannot import core directly`). A comment that pairs an import prohibition
with one of those words in its ordinary English sense — "the core algorithm
avoids importing the whole dataset" — would therefore be refused. That is a
deliberate fail-closed bias for a 49-file controlled substrate in which those
words *are* the layer names: the refusal message names the file, line and matched
phrase, so an author can neutralise the wording or record a reviewed exception.
Loosening it would forfeit the required detections above.
