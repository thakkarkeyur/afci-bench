# docs/v2 — Model-Visible Worktree Policy

Status: **development policy for study v2**. Defines exactly what the coding
model's worktree may contain, per condition, and the fail-closed mechanism that
builds it. Development artifact only: it freezes no benchmark configuration,
authorizes no paid model run, and **does not** mark runner-time enforcement
complete.

Blocking decisions: **`TD-B22`** (runner-time enforcement of this policy — open),
**`TD-B16`** (agent-visible CI separation in the live runner — open), **`TD-B18`**
(byte-identical C3/C4 architecture content — open), **`TD-B19`** (isolated
container + CLEAN context audit — open). Gates: **G5** (C3-vs-C4 channel),
**G3/G4** (C4 vs C1/C2).

Mechanism: [`../../experiments/v2/harness/prepare_model_worktree.py`](../../experiments/v2/harness/prepare_model_worktree.py).
Tests: [`../../experiments/v2/harness/tests/test_model_worktree_preparation.py`](../../experiments/v2/harness/tests/test_model_worktree_preparation.py).

---

## 1. The problem this closes

An independent public review of the pilot task package found that the coding
model's worktree was defined as "the repository snapshot the model edits"
([`EVALUATOR_MOUNT_POLICY.md`](EVALUATOR_MOUNT_POLICY.md) §1) with no preparation
step. Because the whole repository was that snapshot, two explicit
architecture-answering artifacts were readable by the model in **every**
condition:

- [`ARCHITECTURE_CONTEXT.md`](ARCHITECTURE_CONTEXT.md) — the canonical
  architecture payload, i.e. the very content C3 and C4 are supposed to be the
  only conditions to receive;
- [`ARCHITECTURE_RULE_CATALOG.yml`](ARCHITECTURE_RULE_CATALOG.yml) — the
  machine-checkable rule catalog the architecture oracle scores against;

together with the architecture-enforcing `.eslintrc.json`, whose `depConstraints`
state the dependency rules directly.

[`CONDITIONS.md`](CONDITIONS.md) §3 lists a "MAD file" among C1's **prohibited
files**, so a repository-resident copy of that same content contradicted the C1
definition. A C1 model doing exactly the repository reconnaissance D3 invites
could read the rule set, which would flatten the primary C4-vs-C1 contrast on
architecture-violation rate. **No result collected on such a worktree would be
interpretable.**

## 2. Definitions

- **Model-visible worktree (`W`)** — the prepared snapshot the coding model reads
  and edits, and the only tree its `npm run ci:agent` runs against. `W` is
  **built** by the preparation mechanism; it is **not** a checkout of the whole
  repository.
- **Substrate** — the development files (`apps/`, `libs/`, build/type-check/test
  configuration) that make the task implementable and `ci:agent` runnable.
- **Context payload** — the functional task, and (per condition) the architecture
  payload or the generic-guidance payload.
- **Evaluator mount (`E`)** — unchanged, and still governed by
  [`EVALUATOR_MOUNT_POLICY.md`](EVALUATOR_MOUNT_POLICY.md): `E` is outside `W`.

## 3. Allowlist-first construction

`W` is built by **inclusion**, never by deletion. Nothing is present because it
"was not excluded", so a newly added protocol file cannot silently reach the
model.

**Allowed source trees** (copied recursively):

| Tree | Why |
|---|---|
| `apps/` | the entry service the task changes |
| `libs/` | the libraries the task changes, including their `project.json`, `tsconfig.*.json`, `jest.config.ts` and existing `*.spec.ts` |

**Allowed repository-root files:**

| File | Why |
|---|---|
| `package.json`, `package-lock.json` | dependency install and the `ci:agent` script |
| `nx.json` | task graph and target defaults |
| `tsconfig.base.json` | `npm run typecheck` and the `@afci-bench/*` path aliases |
| `jest.preset.js` | `npm run test` |
| `.eslintrc.agent.json` | the **agent-visible** lint config (`npm run lint:agent`) |
| `.nvmrc`, `.gitattributes` | environment and line-ending reproducibility |

**Denied inside an allowed tree:** every `.eslintrc.json`. The per-project
configs only `extends` the architecture-enforcing root config; `lint:agent` runs
ESLint with `--no-eslintrc --config .eslintrc.agent.json`, so they are
unnecessary, and copying them would leave a dangling pointer to the excluded rule
set. `node_modules/`, `dist/`, `coverage/`, `.nx/` and Python caches are never
copied out of a tree.

### What is therefore excluded

- [`ARCHITECTURE_CONTEXT.md`](ARCHITECTURE_CONTEXT.md) and
  [`ARCHITECTURE_RULE_CATALOG.yml`](ARCHITECTURE_RULE_CATALOG.yml);
- the whole of `docs/v2/` — every architecture, oracle, protocol and policy
  document, including this one;
- the whole of `experiments/v2/` — the oracle implementation and fixtures, the
  evaluator schemas and manifest templates, the harness, the public task suite
  and its matrices;
- `paper/` and `archive/` — the submitted paper and all historical v0/v1 task
  prompts and experiment artifacts;
- the architecture-enforcing `.eslintrc.json`;
- private evaluator mounts and any hidden test material;
- any `CLAUDE.md`, `CLAUDE.local.md`, `AGENTS.md`, `.claude/`, `.cursorrules` or
  other persistent context not approved for the condition.

### What deliberately stays visible (D3)

Folder names, nx `scope:*` project tags, the `@afci-bench/*` path aliases, the
existing source code and the existing visible tests all remain. The **implicit**
architectural tension must stay real and discoverable from the substrate itself —
that is the whole point of the design. What is removed is only the **explicit
statement of the rules** and the evaluation machinery.

One residual, accepted, pre-existing disclosure: `.eslintrc.agent.json` names
`@nx/enforce-module-boundaries` in order to set it to `"off"`. It carries no
`depConstraints`, `sourceTag` or `onlyDependOnLibsWithTags`, so it states no
dependency rule. This is the agent-visible config the model has always been
given; the tests assert both that it is present and that no file in `W` states a
dependency constraint.

## 4. Condition behaviour

The functional task is **always** delivered out of band (the prompt) and is never
written into `W`. Only the context differs between conditions.

| Condition | Architecture payload | Delivery | Persistent file in `W` | Generic guidance |
|---|---|---|---|---|
| **C1** | none | — | none | none |
| **C2** | none | — | none | approved generic guidance, prompt-injected (not persisted) |
| **C3** | the approved payload | persistent repository-instruction file | exactly one (`CLAUDE.md`) | none |
| **C4** | the same approved **bytes** | explicit prompt injection | **none** | none |

Fail-closed refusals (each has a machine-readable code):

| Code | Condition |
|---|---|
| `UNKNOWN_CONDITION` | condition is not one of C1–C4 |
| `ARCH_PAYLOAD_NOT_ALLOWED` | an architecture payload was supplied for C1 or C2 |
| `ARCH_PAYLOAD_REQUIRED` | C3 or C4 was prepared without the payload |
| `ARCH_PAYLOAD_EMPTY` | the payload is blank |
| `GUIDANCE_PAYLOAD_REQUIRED` | C2 was prepared without generic guidance |
| `GUIDANCE_PAYLOAD_NOT_ALLOWED` | generic guidance was supplied outside C2 |
| `EVALUATOR_MATERIAL_REJECTED` | a source path points at private evaluator or hidden material |
| `TASK_MISSING` | the public task body does not exist |
| `DEST_NOT_EMPTY` | the destination worktree already has content |
| `EMPTY_SUBSTRATE` | the allowlist matched nothing |
| `UNEXPECTED_ARCHITECTURE_FILE` | the finished snapshot contains an explicit architecture artifact |
| `SETUP_CONTAMINATED` | the finished snapshot contains evaluator material or unapproved persistent context |

A refusal is never downgraded to a pass, and a refusal leaves no partial
worktree behind.

## 5. Post-construction sweep (fail-closed backstop)

After copying, `assert_snapshot_clean()` sweeps the finished snapshot and refuses
on: the explicit architecture artifacts; `docs/`, `experiments/`, `paper/`,
`archive/`, `hidden/`, `hidden_tests/`, `.claude/` or an evaluator-mount
directory; any artifact name from
[`HIDDEN_EVALUATOR_BOUNDARY.md`](HIDDEN_EVALUATOR_BOUNDARY.md) §4; and any
persistent-context file other than the single instruction file the condition
approves. The allowlist makes these unreachable by construction; the sweep is the
belt-and-braces check that fails closed if the allowlist is ever widened
carelessly.

## 6. Snapshot manifest

Every preparation emits a deterministic manifest: `condition`, `task_id`,
`task_sha256`, `task_delivery`, `architecture_delivery`, `architecture_sha256`,
`architecture_persistent_path`, `generic_guidance_delivery`,
`generic_guidance_sha256`, the allowlist actually applied, every included path
with its SHA-256 and byte count (sorted), an `entry_count`, and a `content_hash`
over the whole set. **No timestamps** are recorded, so two preparations of the
same substrate produce byte-identical manifests and any drift is detectable.

`architecture_sha256` is what makes the C3/C4 byte-identity requirement
(`TD-B18`, gate G5) mechanically checkable: the same payload hash must appear on
both, with different `architecture_delivery` values.

The manifest also carries `runner_enforcement: "not implemented (TD-B22)"`.

## 7. Status — what is and is not done

**Delivered and tested here:** the allowlist-first preparation mechanism, the
per-condition payload contract, the fail-closed refusals, the post-construction
sweep, the deterministic manifest, and nine proofs — no architecture
context/catalog/lint rules in C1 or C2; C3 carries only its approved persistent
payload; C4 carries none; C3 and C4 payload bytes identical; source folders and
implicit clues intact; `npm run ci:agent` verified to pass inside a prepared
snapshot; private evaluator paths and hidden material refused; an unexpected
explicit architecture file fails closed; deterministic hashed manifest.

**Not done — explicitly open:**

- the **live model runner** does not exist (`TD-B02`), so nothing enforces this
  policy at run time. That enforcement is **`TD-B22`** and is **open**.
- the approved architecture payload is **not frozen** and its C3/C4 hash parity is
  **not recorded** (`TD-B18`).
- the approved C2 generic-guidance payload is **not authored** and not
  token-matched (`TD-B08`).
- container/identity isolation and the CLEAN context audit for every counted run
  remain **`TD-B19`**.

No run may be counted until `TD-B22` is closed. The protocol remains
**PRE-FREEZE**.
