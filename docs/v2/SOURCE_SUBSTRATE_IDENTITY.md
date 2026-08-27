# docs/v2 — Source-Substrate Identity

Status: **development record for study v2**. Names the exact bytes every
condition's model-visible worktree is built from, and records every change to
them. Development artifact only: it freezes no benchmark configuration and
authorizes no paid model run. The protocol remains **PRE-FREEZE**.

Mechanism: [`../../experiments/v2/harness/prepare_model_worktree.py`](../../experiments/v2/harness/prepare_model_worktree.py).
Identity: [`../../experiments/v2/harness/substrate_identity.py`](../../experiments/v2/harness/substrate_identity.py).
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

## 2. How identity is computed

Identity is the **content hash** of a *commit*, computed from **committed Git
blob bytes**. Algorithm id: **`git-blob-sha256-v2`**.

Given a commit:

1. **Enumerate** the allowlisted paths from that commit's tree — not from the
   filesystem, so an untracked or modified working tree cannot influence it.
2. **Order** them ascending by their **UTF-8 encoded bytes**, so the order is
   identical on every platform and under every locale.
3. **Retrieve** each path's exact blob bytes from the object database.
4. **Frame** and hash with SHA-256, feeding in order:

   ```
   DOMAIN
   u64be(entry_count)
   for each entry:  u64be(len(path_utf8)) ‖ path_utf8 ‖ u64be(len(blob)) ‖ blob
   ```

   where `DOMAIN` is the ASCII bytes `afci-bench/substrate-content-hash/v2\n`
   and `u64be` is an unsigned 64-bit big-endian integer.
5. The identity is the lowercase hex digest.

Every variable-length field is length-prefixed, so no combination of path and
content can be re-cut into a different sequence of entries that hashes the same.
The entry count is bound in, so a truncated enumeration cannot collide with a
complete one. The domain string separates this digest from any other SHA-256
over the same material.

**The blob bytes are hashed exactly as committed. No normalisation is applied**
— CRLF inside a committed blob is hashed as CRLF. That is deliberate: the hash
must describe what is stored, not what a particular checkout produced.

### Why this replaced the previous procedure

The previous identity hashed the **working tree**. That made the recorded value
a property of one person's checkout rather than of the repository, and the
independent architecture-neutral-substrate review found the consequence: the
recorded hash passed on the machine it was computed on and **failed on a fresh
clone of the very same commit**. Git materialises the same blob differently
depending on `core.autocrlf`, `core.eol` and the `eol=` attributes, and a
checkout is not re-materialised when those attributes later change, so one
commit had two different "identities" depending on where you stood:

| Commit `c514d697`, old working-tree procedure | Result |
|---|---|
| CRLF working tree (Windows, `core.autocrlf=true`, checked out before `eol=lf` existed) | `361d0fe5bd97ed9f273d52d5ca4cba2a6400e128038c3c3b6e7025ca6ff7bc04` — **superseded** |
| LF working tree (fresh clone of the same commit) | `dee8c40c6b1c2fbda907d2bf16112b8684feca96d6510d57ee31e6a323830928` — **superseded** |

Both values are withdrawn. Neither was ever an identity of the repository; they
were two answers to a question the old procedure could not answer. Under
`git-blob-sha256-v2` that same commit `c514d697` has exactly one identity,
`40f38174a612c5abdc09376fb86bff327b2bc1e7cda59120c11cdb500b10a5ce`, from any
checkout.

Guarantees, each asserted by a test rather than claimed:

- the identity is computed from committed Git blob bytes;
- it does not depend on checkout EOL conversion;
- **`core.autocrlf` cannot change the result** (`true`, `false` and `input` are
  all exercised, as are LF and CRLF materialisations of the same commit);
- **a fresh clone must reproduce the recorded value**, and does.

### Relationship to the snapshot manifest `content_hash`

These are two different measurements and are **no longer the same construction**;
an earlier version of this document claimed they were directly comparable, and
that claim is withdrawn along with the procedure that produced it.

| | Canonical substrate identity | Snapshot manifest `content_hash` |
|---|---|---|
| Hashes | committed blob bytes at a commit | the bytes actually materialised into a prepared worktree |
| Answers | "which substrate is this?" | "what did this preparation actually copy?" |
| Depends on the checkout | no | **yes**, by design — it describes a materialisation |
| Authoritative identity | **yes** | no |

A prepared C1 snapshot on a CRLF checkout therefore reports a different
`content_hash` from the canonical identity of the commit it was built from, and
that is correct: it is reporting what is on disk. What matters for condition
parity is that C1 and C2 report the **same** manifest hash as each other, which
they do, and that both are built from the substrate commit recorded here.

Known limitation, recorded rather than hidden: because the manifest hash is a
materialisation hash, the same preparation on an LF and a CRLF checkout yields
different manifest hashes. It is reproducible per environment, not across
environments, so a recorded run manifest must be compared against runs from the
same environment baseline — or against the canonical substrate identity, which is
environment-independent. This does not affect condition parity, since all four
conditions of a run are prepared on one machine from one substrate.

## 3. Substrate lineage

| | 1. Historical | 2. Intermediate | 3. **Canonical** |
|---|---|---|---|
| **Commit** | `33dba7ff8917515efe56170cfd45cb7f9e16cde4` | `15aa99f5f564b1d482843c638174c5c853dc8f1c` | `630d3180af0d02a86330dfb599f559e78df65e94` |
| **Content hash** | `c58fc41d556e3e037deb7eda5e52249c61a9dcdbef9d687bc141bef9bb2fed89` | `40f38174a612c5abdc09376fb86bff327b2bc1e7cda59120c11cdb500b10a5ce` | `0198d76c189f38589e872cab4305527c08e86ef736e1550e428e05f9178060f3` |
| **`apps/` tree** | `3efebe211db965e714d4979f80899b2ffe04b31b` | `ab458a58e0173a93385465864485ce9ef8710273` | `ab458a58e0173a93385465864485ce9ef8710273` |
| **`libs/` tree** | `70268ec6ceca6c1b4ff468dff73b23c5e02ffcec` | `1129614aaa7c293254cdfcd36f06e74245320e35` | `1129614aaa7c293254cdfcd36f06e74245320e35` |
| **File count** | 49 | 49 | 49 |
| **States a scored rule?** | yes — `TD-B23` | no | no |
| **Reveals the experiment?** | yes | yes — `TD-B38` | no |

1. **Historical substrate** `33dba7ff`. Model-visible source comments stated the
   scored dependency rules to every condition (`TD-B23`).
2. **Intermediate substrate** `15aa99f5`. Architecture-rule neutral — the
   coaching comments were removed — but still **experiment-awareness leaky**:
   `package.json` and `.gitattributes` announced the benchmark. Superseded.
3. **Canonical substrate** `630d3180`. Architecture-rule neutral *and*
   experiment-neutral. **This is the substrate every condition is built from.**

> The canonical source substrate is commit `630d3180af0d02a86330dfb599f559e78df65e94`
> — **not** the later documentation commit that records it. The pin commit
> touches no allowlisted file, so it cannot and does not change the identity
> above; that invariant is itself asserted by a test.

The `apps/` and `libs/` trees are byte-identical between the intermediate and
canonical substrates: the awareness remediation touched only two root files.

The historical content hash is the same at `33dba7ff` and at
`0e77d49c7dd5b5858297d9f7eb954060704f67ac` (the commit earlier artifacts pin as
"`apps/` and `libs/` are byte-identical to..."), because no commit between them
touched a substrate file. Any artifact pinning either is pinning the
**historical** substrate.

## 4. The intended differences

### 4.1 `33dba7ff` → `15aa99f5` — architecture-rule disclosure (`TD-B23`)

Removal and neutralisation of **architecture-revealing comments** — nothing else:

| File | Removed |
|---|---|
| `apps/api/src/app.ts` | the `api → core` prohibition, the "would fail CI" consequence, the "BOUNDARY VIOLATION EXAMPLE" heading, and the commented-out `import { Order } from '@afci-bench/core'` |
| `libs/infra/src/index.ts` | "to avoid importing from core" and "a deliberate architectural choice - infra depends on contracts, not core", replaced by a neutral note that `OrderEntity` is the adapter's own persistence-facing representation |
| `libs/features/src/index.ts` | "This allows API to depend on features without directly importing core" |

Six comment lines in three files. **No** executable change.

### 4.2 `15aa99f5` → `630d3180` — experiment awareness (`TD-B38`)

A **distinct threat class**, which is why it is recorded separately rather than
reopening `TD-B23`. `TD-B23` was the substrate *coaching the answer*. This is the
substrate *revealing the experiment*: a C1 model reading "Architecture-First
Context Injection Benchmark" learns nothing about which dependency direction is
legal, yet now knows architecture is the scored construct — and a baseline that
knows it is being scored on architecture is no longer a no-guidance baseline.

| File | Removed | Replaced with |
|---|---|---|
| `package.json` | `"description": "Architecture-First Context Injection Benchmark"` | `"description": "Order management service workspace"` |
| `package.json` | the `oracle:test` and `oracle:typecheck` scripts, whose names disclosed a hidden oracle and whose commands pointed at `experiments/v2/oracle` | nothing — no replacement model-visible script points at the oracle, the experiment tree or any evaluator path |
| `.gitattributes` | a header naming "AFCI-Bench study v2", the "canonical architecture context delivered identically to the repository-instruction conditions", and the committed fixtures | a neutral statement of what the file does |

Every functional Git attribute is retained unchanged: `* text=auto eol=lf` and
the eight `binary` rules. Nothing was dropped to make the file shorter.

Every script a benchmark participant needs is preserved byte-identically: `ci`,
`ci:agent`, `lint`, `lint:agent`, `typecheck`, `test`, `build`, `serve`. No
application or model-facing command referenced the two removed scripts, and the
GitHub CI workflow runs `npm run ci` and never invoked them. Maintainers run the
same public validation tools directly:

```
npx tsc -p experiments/v2/oracle/tsconfig.json --noEmit
npx jest -c experiments/v2/oracle/jest.config.js
```

**Retained by decision: the `@afci-bench/*` workspace scope.** It appears in
`tsconfig.base.json` path aliases and in the import statements of `apps/` and
`libs/`, so removing it would mean editing application source — a different
change with its own substrate implications, deliberately not smuggled into this
one. With the description gone it is an opaque npm scope that states no
benchmark, condition, treatment or oracle. Recorded as a residual finding in
`TD-B38` rather than silently accepted.

## 5. Proof the substrates are behaviourally equivalent

For `33dba7ff` → `15aa99f5`, verified with the TypeScript compiler API over the
old and new bytes of all three files:

| Check | Result |
|---|---|
| Emitted CommonJS with `removeComments: true` | **identical** |
| Full AST fingerprint (node kinds + identifiers + literals) | **identical** |
| `import` / `export` / dynamic-import / `require` edge list | **identical** |
| Raw bytes | changed (the comments) |

Comments are trivia, not AST nodes, so the second check is a structural proof
rather than a spot check.

For `15aa99f5` → `630d3180`, no source file was touched at all: `apps/` and
`libs/` are the *same trees*, so behavioural equivalence is an object-identity
fact rather than a test result. The two changed files are metadata. The
dependency graph is provably unchanged — `package-lock.json` mirrors only
`name`, `version`, `workspaces`, `dependencies` and `devDependencies`, and none
of those were touched, so the lockfile needed no edit and received none.

Independently: `npm run ci`, `npm run ci:agent`, the oracle suite and the Python
v2 suite all pass on the canonical substrate, and `npm run ci:agent` was executed
**inside a freshly prepared C1 snapshot**.

The architecture mechanism is untouched. The root `.eslintrc.json`
`depConstraints` are unchanged, and `api → core`, `infra → core` and
`features → infra` are still reported by `@nx/enforce-module-boundaries`. What
changed is that the baseline no longer *states* those rules in prose, and no
longer announces that the rules are being scored.

## 6. What did not change

Aliases, allowed dependency relationships, layer scopes, nx `scope:*` tags,
public task bodies and their hashes, task classifications, task eligibility,
runtime behaviour and application APIs are all unchanged. Every public task hash
in
[`../../experiments/v2/tasks/public/TASK_INDEX.csv`](../../experiments/v2/tasks/public/TASK_INDEX.csv)
is unaffected, because a task body is not a substrate file — the eight that existed
at this remediation, and `PT07` and then `PT08`, both authored later against this
same substrate and likewise unmovable by it (the index now holds **ten**).

## 7. Why the commit is recorded one commit later

The substrate hash covers only the 49 allowlisted files. This document lives in
`docs/v2/`, which is **excluded** from the substrate, so recording the commit
identity here cannot change the identity being recorded. Each remediation is
therefore committed as a deterministic two-commit sequence — (1) the remediation,
which fixes the content hash; (2) the pin, which names the commit that produced
it — and the content hash is the same before and after step 2. A test asserts
that every commit after `630d3180` touches zero allowlisted paths and still
computes the same identity. No history is amended.

## 8. Changing the substrate again

Any future substrate change must add a column to §3, state the intended
difference in §4, and re-establish §5. A substrate change after protocol freeze
would invalidate every run recorded against the previous identity.
