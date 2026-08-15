# docs/v2 — Source-Substrate Identity

Status: **development record for study v2**. Names the exact bytes every
condition's model-visible worktree is built from, and records every change to
them. Development artifact only: it freezes no benchmark configuration and
authorizes no paid model run. The protocol remains **PRE-FREEZE**.

Mechanism: [`../../experiments/v2/harness/prepare_model_worktree.py`](../../experiments/v2/harness/prepare_model_worktree.py).
Policy: [`MODEL_VISIBLE_WORKTREE_POLICY.md`](MODEL_VISIBLE_WORKTREE_POLICY.md).
Test: `experiments/v2/harness/tests/test_source_substrate_identity.py`.

---

## 1. What the substrate is

The **source substrate** is the set of files the allowlist copies into the
model-visible worktree: `apps/**` and `libs/**` (minus every per-project
`.eslintrc.json`), plus `package.json`, `package-lock.json`, `nx.json`,
`tsconfig.base.json`, `jest.preset.js`, `.eslintrc.agent.json`, `.nvmrc` and
`.gitattributes` — **49 files**. It is byte-identical across C1–C4 by
construction; only the context payload differs.

## 2. Substrate identity

Identity is the **content hash**: SHA-256 over the sorted `"<path> <sha256>\n"`
lines of those 49 files. This is the same construction as the snapshot
`content_hash` in the preparation manifest, so a recorded substrate identity and
a recorded run manifest are directly comparable. It is computed from file bytes,
not from git, so it is stable across clones, platforms and history rewrites.

| | Old substrate | New substrate |
|---|---|---|
| **Commit** | `33dba7ff8917515efe56170cfd45cb7f9e16cde4` | `15aa99f5f564b1d482843c638174c5c853dc8f1c` |
| **Content hash** | `2ec1079efd468ebc46a688e21b342c514ca60930221874c5f3dd9831afcb6123` | `361d0fe5bd97ed9f273d52d5ca4cba2a6400e128038c3c3b6e7025ca6ff7bc04` |
| **`apps/` tree** | `3efebe211db965e714d4979f80899b2ffe04b31b` | `ab458a58e0173a93385465864485ce9ef8710273` |
| **`libs/` tree** | `70268ec6ceca6c1b4ff468dff73b23c5e02ffcec` | `1129614aaa7c293254cdfcd36f06e74245320e35` |
| **File count** | 49 | 49 |

The content hash is the authoritative identity; the git identifiers are recorded
for provenance. The new content hash was fixed by the remediation commit
`15aa99f5` and is **unchanged** by this pin commit, which touches no substrate
file — that is what makes the two-commit sequence in §6 deterministic. Verified
independently: a C1 worktree prepared by `prepare_model_worktree.py` from this
substrate reports exactly this value as its snapshot `content_hash`.

The old substrate content hash is identical at commit `33dba7ff` and at commit
`0e77d49c7dd5b5858297d9f7eb954060704f67ac` (the commit earlier artifacts pin as
"`apps/` and `libs/` are byte-identical to..."), because no commit between them
touched a substrate file. Any artifact that pins either of those commits is
pinning the **old** substrate.

## 3. The only intended difference

Removal and neutralisation of **architecture-revealing comments** — nothing else.
`TD-B23` recorded that model-visible source comments stated scored dependency
rules to every condition, including the no-guidance C1 baseline:

| File | Removed |
|---|---|
| `apps/api/src/app.ts` | the `api → core` prohibition, the "would fail CI" consequence, the "BOUNDARY VIOLATION EXAMPLE" heading, and the commented-out `import { Order } from '@afci-bench/core'` |
| `libs/infra/src/index.ts` | "to avoid importing from core" and "a deliberate architectural choice - infra depends on contracts, not core", replaced by a neutral note that `OrderEntity` is the adapter's own persistence-facing representation |
| `libs/features/src/index.ts` | "This allows API to depend on features without directly importing core" |

Six comment lines in three files. **No** executable change.

## 4. Proof the two substrates are behaviourally equivalent

Verified with the TypeScript compiler API over the old and new bytes of all three
files:

| Check | Result |
|---|---|
| Emitted CommonJS with `removeComments: true` | **identical** |
| Full AST fingerprint (node kinds + identifiers + literals) | **identical** |
| `import` / `export` / dynamic-import / `require` edge list | **identical** |
| Raw bytes | changed (the comments) |

Comments are trivia, not AST nodes, so the second check is a structural proof
rather than a spot check. Independently: `npm run ci`, `npm run ci:agent`, the
oracle suite and the Python v2 suite all pass on the new substrate, and
`npm run ci:agent` was executed **inside a freshly prepared C1 snapshot**.

The architecture mechanism is untouched. The root `.eslintrc.json`
`depConstraints` are unchanged, and `api → core`, `infra → core` and
`features → infra` were each re-probed against the new substrate and are still
reported by `@nx/enforce-module-boundaries`. What changed is that the baseline no
longer *states* those rules in prose.

## 5. What did not change

Aliases, allowed dependency relationships, layer scopes, nx `scope:*` tags,
public task bodies and their hashes, task classifications, runtime behaviour and
application APIs are all unchanged. All eight public task hashes in
[`../../experiments/v2/tasks/public/TASK_INDEX.csv`](../../experiments/v2/tasks/public/TASK_INDEX.csv)
are unaffected, because a task body is not a substrate file.

## 6. Why the commit is recorded one commit later

The substrate hash covers only the 49 files above. This document lives in
`docs/v2/`, which is **excluded** from the substrate, so recording the commit
identity here cannot change the identity being recorded. The remediation is
therefore committed in a deterministic two-commit sequence — (1) the source-comment
remediation, which fixes the content hash; (2) this pin, which names the commit
that produced it — and the content hash is the same before and after step 2. No
history is amended.

## 7. Changing the substrate again

Any future substrate change must add a row to §2, state the intended difference
in §3, and re-establish §4. A substrate change after protocol freeze would
invalidate every run recorded against the previous identity.
