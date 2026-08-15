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
could read the rule set, which would flatten the primary C4-vs-C1 contrast on the
**dependency-direction violation rate per applicable frozen opportunity** (E1).
**No result collected on such a worktree would be interpretable.**

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

#### Adjudication — `.eslintrc.agent.json` naming the boundary rule

`.eslintrc.agent.json` names `@nx/enforce-module-boundaries` in order to set it
to `"off"`. The independent architecture-neutral-substrate review examined this
explicitly and its disposition is **ACCEPTABLE STRUCTURAL/TOOLING INFORMATION** —
**not** an unresolved leakage blocker. It is recorded here so the judgement is
auditable rather than implicit:

- **No source/target pair is disclosed.** The file carries no `depConstraints`,
  no `sourceTag`, no `onlyDependOnLibsWithTags` and no layer names. A reader
  learns that a module-boundary lint rule exists in the npm ecosystem — which is
  true of any Nx workspace — and nothing about which direction is legal here.
- **The `off` state is what keeps enforcement away from the model.** Setting the
  rule to `"off"` is the mechanism that prevents live architecture enforcement
  from reaching the model through `npm run ci:agent`. Removing the line would not
  hide anything; it would either re-enable the rule (feeding the model the
  answers it is being scored on) or leave the config depending on the excluded
  root `.eslintrc.json`. Neutralising it would therefore *damage* the control.
- **It is byte-identical across conditions.** The file is a single allowlisted
  root file copied verbatim into C1–C4, so it cannot differentiate the arms.
- **It is pre-existing and stable.** This is the agent-visible config the model
  has always been given; it is unchanged by the `TD-B23` and `TD-B38`
  remediations.

The JSON scan reads string **values**, not keys, for exactly this reason: keys
are structural, and scanning them would flag the one file the policy allows to
name the rule it switches off. Tests assert both that the file is present in
every prepared worktree and that no file in `W` states a dependency constraint.

### Structural signal vs. stated rule — the line the baseline must not cross

`TD-B23` found the substrate on the wrong side of this line: `apps/api/src/app.ts`
carried a worked forbidden-import example and the sentence *"apps/api can depend
on features, but should not depend on core directly"*, and `libs/infra/` and
`libs/features/` restated the same directions. Every condition read them,
including C1. The baseline was therefore **partly guided**, which is a floor
effect on the primary C4-vs-C1 contrast, not a design feature. Those comments have
been neutralised; `scan_source_comment_disclosures()` now keeps them out.

The distinction the baseline is held to:

| Allowed in every condition (**structural signal**) | Forbidden outside C3/C4 (**stated rule**) |
|---|---|
| directory names (`apps/api`, `libs/core`, ...) | "api cannot import core" |
| nx `scope:*` project tags | "this layer may only depend on ..." |
| `@afci-bench/*` path aliases in `tsconfig.base.json` | a worked boundary-violation example |
| the existing import edges and the code itself | a commented-out forbidden import |
| comments describing behaviour, algorithms, data semantics, framework quirks or maintainability | a named rule id (`AR-DEP-00n`), or a dependency choice justified as "a deliberate architectural choice" |

A C1 model may still **infer** the intended architecture by reading the code —
that inference is exactly the D3 signal the design wants to measure. What it may
no longer do is **read the answer** in prose. C3 and C4 continue to receive the
controlled architecture treatment through their own channels, so the contrast
between "infer it from structure" and "be told it" is restored rather than
removed.

### Second threat class — knowing the experiment exists (`TD-B38`)

Everything above is about the substrate **coaching the answer**. There is a
second, independent way for model-visible bytes to spoil the baseline: telling
the model that it is **inside an experiment at all**.

The independent architecture-neutral-substrate review found the substrate had
been made rule-neutral while remaining experiment-aware. `package.json`
described the workspace as the "Architecture-First Context Injection Benchmark"
and exposed `oracle:test` / `oracle:typecheck`; `.gitattributes` named
"AFCI-Bench study v2", the canonical architecture context and its delivery to
"the repository-instruction conditions". None of that states which dependency
direction is legal, so the `TD-B23` detector was right not to flag it — and it is
still disqualifying. A C1 model that reads it knows architecture is the scored
construct, that a treatment exists, that other conditions get it, and that a
hidden oracle will grade the result. Those are **demand characteristics**: the
baseline stops behaving like a baseline for reasons that have nothing to do with
the code in front of it.

The two classes are kept separate — separate detector, separate refusal code,
separate decision record — because neither subsumes the other and a failure
should say which one it is.

| Allowed in every condition | Forbidden in every condition (**experiment awareness**) |
|---|---|
| ordinary uses of `architecture`, `test`, `condition`, `context`, `benchmark` in application prose | "AFCI", "AFCI-Bench", "study v2" |
| the `@afci-bench/*` npm scope as an opaque package identifier | "Architecture-First Context Injection" spelled out |
| a `description` naming what the application does | a description naming the study or the benchmark |
| `ci`, `ci:agent`, `lint`, `typecheck`, `test`, `build`, `serve` | a script named or pointing at an oracle, evaluator or `experiments/v2/**` |
| a file explaining what it does | prose naming the canonical architecture context, the conditions, the treatment, or the repository-instruction delivery |

The detector matches only **contextual combinations**, never bare topic words: a
comment may say "the architecture of this module favours composition" or "a quick
benchmark showed this loop is not hot" and must pass. A blanket keyword ban would
be unusable against real source and is explicitly not the policy.

**Residual, accepted and recorded:** the `@afci-bench/*` workspace scope remains
in `tsconfig.base.json` and in the imports of `apps/` and `libs/`. Removing it
means editing application source and re-identifying the substrate, so it is out
of scope for the awareness remediation and is recorded in `TD-B38` rather than
silently accepted. With the description gone it is an opaque npm scope that
states no benchmark, condition, treatment or oracle.

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
| `ARCHITECTURE_COMMENT_DISCLOSURE` | a model-visible source comment states a dependency rule (`TD-B23`/`TD-B24`) |
| `EXPERIMENT_AWARENESS_DISCLOSURE` | model-visible content reveals the benchmark, a condition, the treatment or the oracle (`TD-B38`) |
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

### 5.1 Source-comment disclosure sweep (`TD-B24`)

The sweep above matches **names**. A file called `app.ts` is innocuous by name and
may still state the rule in its first comment, which is precisely how the `TD-B23`
disclosure survived. `scan_source_comment_disclosures()` therefore reads the prose
the model can see:

| File kind | What is read |
|---|---|
| `.ts`, `.tsx`, `.mts`, `.cts`, `.js`, `.jsx`, `.mjs`, `.cjs` | line and block comments, with string, template and regex literals skipped so quoted text is not mistaken for prose |
| `.json` | string **values** only — keys are structural, and scanning them would flag `.eslintrc.agent.json` for naming the rule it switches off |
| `.gitattributes`, `.nvmrc`, `.npmrc`, `.editorconfig`, `.yml`, `.yaml`, `.sh`, `.toml`, `.ini`, `.cfg` | `#` comments |
| `.md`, `.markdown`, `.txt`, `.rst` | full text |

A comment is a violation only when it states a rule, in one of four forms: a
**worked violation example**; a **commented-out workspace-package import**; a
**named rule or opportunity id**; or a **prohibition/exclusivity claim**
("must not import", "may only depend on", "avoid importing") **paired with a named
layer**. The pairing requirement is what keeps the audit narrow: "do not import
this module at runtime" and "we avoid importing lodash here" name no layer and
pass, while "infra must not import core" does not.

C3's single approved repository-instruction file is exempt, because that file **is**
the architecture payload; scanning it would refuse the condition it implements.
Every other file in every condition is scanned, C1's baseline included.

Regression fixtures — including the verbatim bytes removed from the three leaking
files, and a negative fixture of the comments the substrate keeps — live in
[`../../experiments/v2/leakage_fixtures/`](../../experiments/v2/leakage_fixtures/).

### 5.2 Experiment-awareness sweep (`TD-B38`)

`scan_experiment_awareness()` runs alongside §5.1 and refuses with
`EXPERIMENT_AWARENESS_DISCLOSURE`. Two things differ from the comment sweep, and
both were forced by how the historical leaks were actually written:

- **It reads the whole file, not only comment regions.** The `package.json`
  disclosures were a `description` value and two npm *script names* — JSON keys
  and values. A comment-only sweep would have missed all three.
- **It flattens wrapped prose before matching.** The `.gitattributes` header
  split "the canonical architecture / context" across two lines, so a
  line-by-line scan sees two harmless fragments and matches neither. Runs of
  whitespace, including a newline plus the next line's indentation and comment
  leader, collapse to a single space; a `*` counts as a comment leader only when
  whitespace follows, so `*.png binary` keeps its glob.

Detected classes: the study's own name (`AFCI`, `AFCI-Bench`, `study v2`); the
expanded construct ("Architecture-First Context Injection"); the canonical
architecture context or architecture-context treatment; the
repository-instruction delivery mechanism; a hidden oracle or evaluator, or an
oracle paired with scoring; condition labels appearing together (`C1/C2`,
`condition C3`); a named treatment/control arm; the token-matched guidance; a
benchmark/study framed with a participant, condition, arm, protocol, harness,
oracle or treatment; and any path into `experiments/v<n>`.

The `@afci-bench/*` scope is masked before matching, because it is retained
structural identity rather than prose — see the residual note in §3. Prose that
spells out "AFCI-Bench" without the `@scope/` form is still caught.

C3's approved instruction file is exempt on the same basis as §5.1: it **is** the
treatment. C1 and C2 have no exempt path at all.

Regression fixtures are the **verbatim** pre-remediation `package.json` and
`.gitattributes`, alongside negative fixtures of innocent application vocabulary,
in [`../../experiments/v2/leakage_fixtures/`](../../experiments/v2/leakage_fixtures/).

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
sweep, the deterministic manifest, and ten proofs — no architecture
context/catalog/lint rules in C1 or C2; C3 carries only its approved persistent
payload; C4 carries none; C3 and C4 payload bytes identical; source folders and
implicit clues intact; `npm run ci:agent` verified to pass inside a prepared
snapshot; private evaluator paths and hidden material refused; an unexpected
explicit architecture file fails closed; deterministic hashed manifest; and
(**PROOF 10**, `TD-B23`/`TD-B24`) the model-visible source comments state no
dependency rule — the verbatim historical leak is detected, ordinary
implementation prose is not, and the real prepared C1 and C2 snapshots are clean.

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
