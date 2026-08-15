# experiments/v2/leakage_fixtures — model-visible leakage regression fixtures

Fixtures for the two **model-visible leakage audits** in
`prepare_model_worktree`, both exercised by
`experiments/v2/harness/tests/test_model_worktree_preparation.py`:

| Audit | Function | Threat class |
| --- | --- | --- |
| architecture-rule disclosure | `scan_source_comment_disclosures` | the substrate **states the scored rule** (`TD-B23`/`TD-B24`) |
| experiment awareness | `scan_experiment_awareness` | the substrate **reveals the experiment** (`TD-B38`) |

The two are deliberately separate. The first is about coaching the answer: a
comment stating a scored dependency rule hands C1 the finding it is meant to be
measured on. The second is about demand characteristics: metadata announcing
AFCI-Bench, a canonical architecture context, other conditions or a hidden
oracle tells C1 nothing about which dependency direction is legal, yet still
tells it that architecture is the scored construct. Neither subsumes the other,
so a fixture is filed under the class it actually belongs to.

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
`ALLOWED_TREES`, so nothing here can enter a model-visible worktree. Every file
ends in `.fixture` so no nx project lints them, `tsc` does not compile them and
npm never reads the `package.json` fixture as a manifest. They are outside
`experiments/v2/tasks/`, so the public-task leakage validator does not scan them
either. The awareness fixtures reproduce disclosures that were *already public*
in this repository's history, so preserving them reveals nothing a reader of the
git log could not already see — and keeping the exact bytes is what makes the
regression proof real rather than a paraphrase.

## Positive fixtures — each MUST be detected

| File | Historical source | Discloses |
| --- | --- | --- |
| `td_b23_api_core_boundary.ts.fixture` | `apps/api/src/app.ts` lines 12-17 | the `api -> core` prohibition, an architecture-CI consequence, and a worked commented-out forbidden import |
| `td_b23_infra_core_avoidance.ts.fixture` | `libs/infra/src/index.ts` lines 4-5 | the `infra -> core` prohibition, justified as a deliberate architectural choice |
| `td_b23_features_reexport_rationale.ts.fixture` | `libs/features/src/index.ts` line 15 | the `api -> core` prohibition restated from the `features` side |

## Positive fixtures — experiment awareness (`TD-B38`)

Verbatim model-visible bytes from commit `c514d697`, the last commit before the
awareness remediation. Each MUST be detected by `find_experiment_awareness`.

| File | Historical source | Discloses |
| --- | --- | --- |
| `td_b38_package_metadata.json.fixture` | root `package.json` | `description` expanding "Architecture-First Context Injection Benchmark", and the `oracle:test` / `oracle:typecheck` scripts pointing at `experiments/v2/oracle` |
| `td_b38_gitattributes_prose.fixture` | root `.gitattributes` | "AFCI-Bench study v2", the canonical architecture context, and its delivery "identically to the repository-instruction conditions" |

The `.gitattributes` fixture is also the reason the awareness scan flattens
wrapped prose before matching: "the canonical architecture / context" is split
across lines 3 and 4 there, so a line-by-line scan sees two harmless fragments
and matches neither.

## Negative fixtures — MUST NOT be detected

| File | Guards against |
| --- | --- |
| `neutral_implementation_comments.ts.fixture` | flagging retained prose that names layers, modules and imports while stating no rule |
| `neutral_awareness_vocabulary.ts.fixture` | flagging ordinary application uses of `architecture`, `test`, `condition`, `context`, `benchmark`, `arm`, `control`, `evaluate` |
| `neutral_package_metadata.json.fixture` | regression on the remediated `package.json` |
| `neutral_gitattributes.fixture` | regression on the remediated `.gitattributes` |

A scanner that flags any line in these files is over-broad. The awareness audit
in particular must never become a blanket ban on generic words: it matches only
*contextual combinations* — the study's own name, an expanded construct, a
condition label beside another condition label, an oracle beside scoring, or a
path into the experiment tree — never a bare topic word.

Note that `neutral_awareness_vocabulary.ts.fixture` deliberately carries no
explanatory preamble listing the trigger words. An earlier draft did, and the
audit correctly flagged the preamble itself: a sentence enumerating "benchmark,
study, oracle, ... scored" reads as experiment framing regardless of intent. The
fixture is pure application source so it tests the detector rather than the
commentary around it.

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
