# SL-V2-BACKSTAGE-PILOT-01 — the Backstage real-repository architecture pilot

Status: **Study-Lead decision, PRE-DATA and NON-CONFIRMATORY.** It authorises an
18-observation pilot on a real open-source repository, freezes everything that
pilot will run under, and freezes how its output will be read. **Zero Backstage
observations exist at the moment it is written.** No run has been executed, no
result row exists, and no treatment estimate has been computed.

It passes no gate. It selects no primary model. `TD-B03` remains **OPEN** and
`primary_model` in the model registry stays `null`. The suite is **not** frozen.

Authority: `SL-V2-BACKSTAGE-PILOT-01`
Run purpose: `AFCI_BACKSTAGE_PILOT`
Committed schedule: `afci-bench-evaluator-private/backstage/AFCI_BACKSTAGE_PILOT_RUN_PLAN.json`

---

## 1. Why Backstage, and what this pilot asks

Every AFCI result so far was measured on the synthetic AFCI-Bench substrate: 6
projects, ~1.2k TypeScript LOC, 23 external dependencies. Three completed
packages on that substrate found the same thing from different directions:

| Package | Architecture channel | Outcome |
| --- | --- | --- |
| `V2_PT08_DIAGNOSTIC` | 1 applicable opportunity per run, **0 violated** | architecture FLOOR |
| `V2_PT09_QUALIFICATION` | target violation in **0/3** | FAIL / architecture floor |
| `V2_LOWER_MODEL_PILOT` | **0/9 C1 and 0/9 C4** target-violation runs | architecture FLOOR |

The architecture channel could not discriminate, in either arm, under two
different models. The registry already carries the standing hypothesis for
why — `OPEN_SOURCE_COMPLEXITY_STUDY`, "test whether the synthetic substrate's
architecture legibility masks an AFCI effect". On a 6-project repository the
right home for a new construct is close to unambiguous, so a model has little
opportunity to place it wrongly and architecture context has little to add.

**This pilot asks whether the effect appears once the repository is genuinely
ambiguous:**

> Does governed architecture context reduce wrong architectural placement in a
> large, ambiguous, real-world repository, while preserving functional
> correctness?

That is the **primary** question, and it is a question about architecture
quality. Efficiency is a **secondary, trade-off** question: what token, time,
cost and exploration overhead or saving accompanies any architecture benefit.

**AFCI is not required to be cheaper for the architecture signal to be
scientifically meaningful.** The efficiency channel cannot veto the architecture
decision, and the two are never combined into one score.

Backstage supplies the ambiguity the synthetic substrate lacks:

| Dimension | AFCI-Bench | Backstage at this substrate |
| --- | --- | --- |
| workspace packages | 6 | **203** |
| TypeScript/TSX LOC | ~1.2k | **~769k** |
| external npm dependencies | 23 | **519** |
| files in the model-visible export | — | **10,364** |
| package roles in use | n/a | 11 (`backend-plugin-module` 74, `web-library` 29, `node-library` 27, `frontend-plugin` 23, `common-library` 20, `backend-plugin` 17, …) |

A plugin in Backstage is routinely spread across five or more packages
(`-backend`, `-node`, `-common`, `-react`, `-backend-module-*`), each with its
own role and its own permitted dependents. Choosing among them is a real
decision that a competent engineer can get wrong, and that is exactly the
decision this pilot measures.

---

## 2. Substrate and contamination cutoff

| Field | Value |
| --- | --- |
| Repository | Backstage (`github.com/backstage/backstage`) |
| Frozen substrate commit | `f285f6e46ba57d30c5be8448fd018b960d7d4748` |
| Commit date | 2025-12-08 |
| Version at that commit | `v1.46.0-next.1` |
| Model-visible export tree hash | `4dfadc101db1c9f29b82934db25def67a93a2563` |
| Node | 20.20.2 |
| Yarn | 4.8.1 (`nodeLinker: node-modules`) |
| Python (evaluator) | 3.14.4 |

**Contamination cutoff.** The Claude auto-loaded instruction surfaces
(`CLAUDE.md`, `AGENTS.md`, `.claude/`) first appear on Backstage's `master`
after **2026-02-15**. The frozen substrate predates that boundary, and this was
verified rather than assumed: at `f285f6e` those three paths **do not exist**.
The only agent-instruction surfaces that do exist are `.cursor/` and
`.github/copilot-instructions.md`, and both are removed from the export.

`f285f6e` is additionally the newest pre-boundary commit that still declares
`engines.node: "20 || 22"`, so it runs on the installed Node 20.20.2 with no
toolchain change. **Node 22 is not installed and the substrate is not changed.**

**The three tasks are re-posed at this substrate, not replayed at their own
parent commits.** All three historical PRs land after `f285f6e` (T1 by one day,
T2 by ~2.5 months, T5 by ~9 months), and T2's and T5's parent commits sit past
the contamination boundary. The substrate is therefore a *pre-feature* state for
all three. Compatibility was verified per task; see §4.

**Model-visible export.** Produced by `git archive <commit>`, never by copying a
working tree, so the absence of `.git`, of future history and of the historical
solution is structural rather than asserted. Removed when present: `.git`,
`.claude`, `CLAUDE.md`, `AGENTS.md`, `.cursor`, `.github/copilot-instructions.md`,
`.github/instructions`, `.github/prompts`, `.aider.conf.yml`, `.windsurfrules`,
`.continue`, `.codeium`.

---

## 3. The model, the runtime, and effort

### 3.1 Frozen configuration

| Field | Value |
| --- | --- |
| Requested selector | `claude-sonnet-5` (the exact id, never an alias) |
| Resolved model id | `claude-sonnet-5` |
| Runtime | Claude Code CLI **2.1.229** |
| Authentication | subscription OAuth (`apiKeySource: "none"`) |
| `ANTHROPIC_API_KEY` | unset |
| Fallback model | none; `--fallback-model` is refused by the launcher |
| **Effort** | **`high`, pinned with `--effort high`** |
| Permission mode | `acceptEdits` |
| Reset state | `NON_RESET` only |
| Turn ceiling | 64 (`--max-turns 64`) |

### 3.2 Effort is now a fully qualified control, and that is new

`MODEL_EXECUTION_CONTROLS.md` classified effort as **pinnable but NOT
recordable**, and therefore *unsuitable as a control*, on the strength of a
negative-existence claim tagged `[dry-run-required]` (its §7 Q4, with Q2 asking
which of two environment variables is real). Both questions are **resolved here,
for CLI 2.1.229, by evidence rather than by assumption.**

**Read-only enumeration of the installed runtime binary** establishes the
mechanism:

* effort reaches the API as `output_config.effort`;
* if the model rejects it the runtime logs
  `[effort] model <id> rejected output_config.effort; latching unsupported and
  retrying without it`, emits `tengu_effort_unsupported_retry`, and latches the
  model as effort-unsupported;
* the effort-capability predicate denies effort to `claude-3-*`,
  `claude-opus-4-0`, `claude-opus-4-1`, `claude-sonnet-4-0`, `claude-sonnet-4-5`
  and `claude-haiku-4-5`. **`claude-sonnet-5` is not denied**, and only `max`
  and `xhigh` carry additional per-model gates — `high` carries none;
* the two environment variables are **not** two spellings of one input.
  `CLAUDE_CODE_EFFORT_LEVEL` is read as an **input**. `CLAUDE_EFFORT` is an
  **output**, documented in the binary as "Active effort level for the current
  turn … **after any silent downgrade for the selected model**", exposed to hook
  commands and to Bash tool child processes;
* the hook payload schema carries the same value as `effort.level`, "Present for
  hooks that fire within a tool-use context … on a model that supports the
  effort parameter; absent for session-lifecycle hooks and models without effort
  support".

**One infrastructure-only probe** then verified it live — disposable directory,
no Backstage content, no task, no MAD, not study data:

| Observation | Result |
| --- | --- |
| `system.init.model` | `claude-sonnet-5` |
| `modelUsage` key / `canonicalModel` | `claude-sonnet-5` / `claude-sonnet-5`, `provider: firstParty` |
| `claude_code_version` | `2.1.229` |
| `apiKeySource` | `none` |
| `PreToolUse` hook payload | `"effort": {"level": "high"}` |
| `PostToolUse` hook payload | `"effort": {"level": "high"}` |
| `CLAUDE_EFFORT` in the Bash child process | `high` |
| `CLAUDE_CODE_EFFORT_LEVEL` in the child | empty — so `high` came from the flag, not from inherited environment |
| effort-rejection warning in the debug log | **absent** |
| `--max-turns` | accepted |

Because `CLAUDE_EFFORT` and `effort.level` are defined as the value **after any
silent downgrade**, reading back `high` is positive evidence that HIGH was
actually applied, not merely that it was requested.

**Consequence for the launch configuration.** The readback arrives through a
hook, and `--safe-mode` disables hooks — verified, not assumed: with
`--safe-mode` the hook did not fire at all, and without it a hook supplied
through `--settings` fired normally even under `--setting-sources ""`. This
pilot therefore **drops `--safe-mode`** and reconstructs its isolation
explicitly: `--setting-sources ""` (no user, project or local settings, so the
operator's own `model: opus[1m]` and `effortLevel: xhigh` cannot leak),
`--settings <governed provenance file outside the workspace>` carrying only the
effort-provenance hook, `--strict-mcp-config` with no MCP config,
`--disable-slash-commands`, a fixed tool allowlist excluding subagents and web
access, `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`, and a model-visible export from
which every agent-instruction surface has been removed.

The provenance settings file lives **outside** the model's workspace, so no
`.claude/` directory is ever created inside the tree the model can see.

**Thinking.** Not an experimental factor. There is no `--think`/`--reason` flag
on 2.1.229; a hidden `--max-thinking-tokens` exists and is **not used**. On a
model that supports effort, thinking rides on the effort level. The probe
recorded `output_tokens_details.thinking_tokens` in the result payload, and that
field is captured per observation as observed runtime state rather than as a
control.

**A run whose `effort.level` readback is absent or is not `high` is
INDETERMINATE**, not "assumed default". It is excluded and re-run, per
`EFFORT_GOVERNANCE.md`.

### 3.3 The frozen provenance artifacts

| File | SHA-256 |
| --- | --- |
| `runtime/effort_provenance_settings.json` | `f84897714ad6f9a9792e06f3701655becee19346d21391bb672c24d14b20e499` |
| `runtime/record_effort.js` | `a447bb7455286180772727029f35371af0554371139a4cfc653c2668484bf111` |

The settings file registers the recorder on `PreToolUse`, `PostToolUse` and
`Stop` with the matcher `"*"`. That the wildcard matches every tool is not an
assumption: the runtime's matcher predicate returns true when the matcher is
absent or `"*"`.

The recorder writes one JSON line per firing to the path in
`AFCI_RUN_PROVENANCE`, carrying the payload's `effort.level`, whether that field
was present at all, `CLAUDE_EFFORT`, and `CLAUDE_CODE_EFFORT_LEVEL` — the last
so that an inherited input value can never be mistaken for a readback. It always
exits 0 and never edits: a provenance recorder that could fail a tool call would
be a treatment, not an instrument.

It was exercised offline against synthetic payloads: a tool-use payload yields
`effort_level = "high"` with `effort_field_present = true`, and a
session-lifecycle payload yields `effort_level = null` with
`effort_field_present = false` — so *absent* and *downgraded* are distinguishable
in the record rather than collapsed into one value.

---

## 4. The three tasks

All three were validated as instruments before this decision was written, and
re-validated immediately before the freeze. The oracles are **placement-agnostic
by construction**: they discover the construct the task asked for by runtime
identity (`getRegistrations()` diffed against a frozen substrate baseline of 39
extension point ids and 25 permission names) and never import it from a package,
so functional validity cannot depend on where the candidate put anything.

| Task | Subject | Applicable opportunity |
| --- | --- | --- |
| **T1** | pluggable Kubernetes HTTP routes | one new backend extension point through which a module contributes or replaces the HTTP router |
| **T2** | customizable Slack message rendering | one new backend extension point through which an integrator supplies a renderer for the message body |
| **T5** | authorize incremental-ingestion endpoints | new permission definitions so the HTTP endpoints can be authorized |

Each task has **one** pre-specified architectural placement/ownership
opportunity. The exact expected ownership location and the task-specific hidden
scorer mapping were frozen before execution and are retained in the private
evaluator repository to prevent solution leakage; they are deliberately not
published here, and nothing in this decision depends on their disclosure.

### 4.1 Frozen model-facing task statements

Sanitized, condition-neutral, and **byte-identical between C1 and C4**.

| Task | File | Bytes | Words | Est. tokens | SHA-256 |
| --- | --- | --- | --- | --- | --- |
| T1 | `tasks/T1_TASK.md` | 4,684 | 733 | ~1,170 | `c3033787506fa7d30e909638ce64f407fbe9a89a26fb4d84eaf52222a0f8385b` |
| T2 | `tasks/T2_TASK.md` | 4,546 | 713 | ~1,134 | `60dc08a133c47433e01eb62d96b09e52239e632e8f93df9662a09b46f8a1f32f` |
| T5 | `tasks/T5_TASK.md` | 4,864 | 757 | ~1,214 | `8db333264895b3d6df869adf27cc419c9adbd696da065cead8bbae610d62ba3d` |

The "How to validate your work" block is **byte-identical across all three
statements**, so the gate cannot differ by task any more than it differs by
condition.

Each statement specifies **every behaviour the hidden functional oracle checks**
— because a placement-agnostic oracle is not contract-free, and a case the task
never stated would be measuring the model's guessing rather than its work — and
specifies **nothing about architectural placement**.

An automated check asserts that none of the three contains: the expected or the
target-violating package name, any concrete `@backstage/*` package name, any
`plugins/` or `packages/` path, the solution construct ids, the words
`node-library` / `common-library` / `backend-plugin-module`, or any oracle
vocabulary. All three pass with zero hits.

What each statement does communicate:

* **T1** — an extension point registered by the Kubernetes backend plugin takes
  a **router factory**; the factory receives an options object carrying
  `getDefault()`, which returns the default router; the factory returns the
  router that is mounted; mounting `getDefault()` inside preserves every
  existing route, omitting it replaces them; unused, behaviour is unchanged.
* **T2** — an extension point registered by the Slack notifications module takes
  a **renderer**; the renderer receives the notification payload and returns the
  Block Kit blocks used as the message body, used as-is; **at most one** renderer
  may be installed and a second installation throws; unused, the built-in
  section + context layout is unchanged.
* **T5** — **exactly two** new permissions; `GET`/`HEAD` governed by the read
  one, every mutating method by the manage one, every endpoint covered; the read
  permission carries `attributes.action: 'read'`; `DENY` yields **403** before
  any database access; `ALLOW` leaves every payload unchanged; an adopter's
  permission policy must be able to decide on both.

### 4.2 Controlled reference validation — re-run at the freeze

Both controlled references per task were re-applied to the substrate worktree
immediately before this freeze, scored, and reverted.

| Task | Reference | Functional | applicable | violated | `target_violation` | Matches expectation |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | LEGAL | PASS | 1 | 0 | `false` | yes |
| T1 | TARGET-VIOLATING | PASS | 1 | 1 | `true` | yes |
| T2 | LEGAL | PASS | 1 | 0 | `false` | yes |
| T2 | TARGET-VIOLATING | PASS | 1 | 1 | `true` | yes |
| T5 | LEGAL | PASS | 1 | 0 | `false` | yes |
| T5 | TARGET-VIOLATING | PASS | 1 | 1 | `true` | yes |

**6/6 match expectation. 3/3 tasks READY.** Every target-violating reference is
functionally PASS, which is what makes the two endpoints separable: a model can
be completely right functionally and still wrong architecturally, and the
measurement can tell the difference.

---

## 5. Conditions

Both conditions receive **the same substrate tree** (export tree hash
`4dfadc101db1c9f29b82934db25def67a93a2563`, verified identical across every
prepared workspace and every task), **the same task bytes**, the same tooling,
the same turn ceiling, the same model and the same effort.

### 5.1 C1 — task only

* the frozen model-visible export;
* the exact frozen task statement for the task;
* the repository's own source, documentation and visible build/test tooling, as
  they exist at the substrate;
* **no generated AFCI architecture packet, and no MAD.**

### 5.2 C4 — task plus governed architecture packet

Exactly C1, plus `BACKSTAGE_MAD_V1.md` delivered as a separate labelled section
of the prompt. Nothing else differs — not the task bytes, not the substrate, not
the tooling, not the budget.

### 5.3 BACKSTAGE_MAD_V1

| Field | Value |
| --- | --- |
| File | `tasks/BACKSTAGE_MAD_V1.md` |
| Bytes | 7,874 |
| Characters | 7,848 |
| Words | 1,166 |
| Estimated tokens | ~1,962 |
| SHA-256 | `5bab8d931c24834dc268eb2cdad546abbe13b5e2d9e51e6fbdcfeed09754a7cf` |

**The same bytes are used for all three tasks. There is no task-specific MAD
tailoring.**

Contents — general architecture rules only, each traceable to documentation that
exists in the frozen substrate:

| Section | Rule | Source in the substrate |
| --- | --- | --- |
| 1. Packages, roles and ownership | the eleven package roles; the `plugin-<pluginId>-{backend,node,common,react,backend-module-*}` naming scheme; a construct belongs to its plugin's family and to a role its consumers may depend on | `docs/tooling/cli/02-build-system.md` § Package Roles; `docs/tooling/package-metadata.md` § `name` |
| 2. Extension points | placement is decided by **which feature registers it**: plugin-registered extension points "should always be exported from a plugin node library package"; module-registered ones are "preferred to be exported directly from the module package"; naming patterns; the singleton/setter-throws pattern | `docs/backend-system/architecture/05-extension-points.md`; `docs/backend-system/architecture/08-naming-patterns.md` § Extensions |
| 3. Public and shared contracts | a construct is a contract only if reachable from `main`/`exports`/`typesVersions`; cross-runtime contracts belong in a `common-library`; **all permissions a plugin authorizes should be exported from a common-library package**, because integrators reference them from both frontend components and their policy; `createPermission` and its `action` attribute; a new contract belongs in the package's existing aggregate collection | `docs/permissions/plugin-authors/02-adding-a-basic-permission-check.md`; `docs/tooling/package-metadata.md` §§ `exports`, `typeVersions` |
| 4. Declared surface | changing exports changes the API report, which CI checks | `CONTRIBUTING.md` § API Reports |
| 5. Using this | four ownership questions to answer before placing a construct | derived from the above |

These sections correspond to the private scorer's ownership sub-rules. **The
sub-rule identifiers themselves do not appear in the packet**, because they are
evaluator vocabulary and the packet is model-facing; the identifiers, and which
sub-rule is engaged by which task, are retained in the private evaluator
repository.

### 5.4 MAD safety check — per task

For each of T1, T2 and T5, `BACKSTAGE_MAD_V1`:

| Requirement | T1 | T2 | T5 |
| --- | --- | --- | --- |
| states general architecture principles, not a task answer | yes | yes | yes |
| does not directly identify the expected implementation package | yes — 0 hits | yes — 0 hits | yes — 0 hits |
| does not mention the historical solution (construct ids, PR numbers) | yes — 0 hits | yes — 0 hits | yes — 0 hits |
| contains no task-specific answer string added because of that task | yes | yes | yes |

The packet contains **zero** concrete `@backstage/*` package names — every
example is a generic pattern (`plugin-<pluginId>-node`). It contains none of the
words `kubernetes`, `slack`, `notifications`, `catalog`, `incremental`,
`ingestion`, none of the solution construct ids, none of the three PR numbers,
and none of the words `oracle`, `violation`, `opportunity`, `scorer` or `AFCI`.

A model that applies the packet's general rules correctly can derive a placement
for the construct its task creates — which is the point of the treatment. That
is a **general rule producing an answer**, not an answer stated in advance. The
same rules serve all three tasks, and they point in different directions for
each; **which direction, per task, is frozen in the private evaluator and is not
published here.**

---

## 6. The matrix

| Factor | Levels |
| --- | --- |
| Task | T1, T2, T5 |
| Condition | C1, C4 |
| Reset state | **NON_RESET only** |
| Repetitions | 3 |
| **Total observations** | **3 × 2 × 3 = 18** |
| **Paired blocks** | **9** |

One reset state, deliberately. This pilot isolates **repository architectural
complexity** as the moderator. The Sonnet efficiency pilot crossed NON_RESET and
RESET; a difference found while two factors moved would be attributable to
either. Reset and context-loss are not added here. The reset state is
nonetheless carried on every row and inside every run id, because a row that
merely omitted it would be indistinguishable from a row written before
reset-aware identity existed — the defect that aborted an earlier execution.

### 6.1 Turn budget

**64 turns, NON_RESET, identical for C1 and C4.** Retained unchanged from the
Sonnet efficiency pilot's NON_RESET allowance (`SL-V2-EFF-RESET-01`).

The Backstage tasks are larger than the synthetic ones, but the measured
evaluation loop the budget has to accommodate is not: after preparation warms
the workspace, the frozen visible gate costs roughly a minute end to end
(`yarn tsc` 15 s, targeted tests ~21 s, per-package lint ~4 s, prettier ~2 s,
API report ~9 s). Raising the ceiling without evidence that the tasks need it
would change two things at once between the pilots and make the comparison in
§11 unreadable. **It is not raised.**

---

## 7. Endpoints

### 7.1 Primary — architectural placement / ownership

Each run carries **exactly one frozen applicable architecture opportunity**. An
opportunity is one architectural decision the task forces; it is violated when
any engaged sub-rule check fails.

Recorded per run:

* `architecture_applicable_opportunities`
* `architecture_violated_opportunities`
* `target_violation` (true/false)

**Primary comparison:** the count of C1 target-violation runs versus the count
of C4 target-violation runs. Also reported **by task**.

The scorer's ownership sub-rules are **checked within the single ownership
endpoint**, never endpoints of their own. Several sub-rule failures arising from **one**
placement decision count as **one** violated opportunity, not several. The
scorer reads only files the candidate added or modified, and a construct present
in the frozen substrate baseline can never become an opportunity — run over the
untouched substrate it returns zero opportunities.

The architecture scorer runs **post hoc only**. It never runs inside the model's
workspace and is never visible to the model.

### 7.2 Functional

Measured by the already-validated hidden functional oracle.

**`FUNCTIONAL_VALID` iff every semantic case executes and passes**, with no
missing, failed, errored or indeterminate semantic case. Restraint and other
non-semantic checks are recorded **separately** and do not enter
`FUNCTIONAL_VALID`.

| Task | Semantic cases | Restraint cases |
| --- | --- | --- |
| T1 | 4 | 1 |
| T2 | 4 | 1 |
| T5 | 5 | 1 |

**Architectural placement must NOT determine functional validity**, and the
reference matrix in §4.2 is the evidence that it does not: both the legal and
the target-violating reference are functionally PASS for all three tasks.

### 7.3 Efficiency and cost — secondary

Captured to be comparable with the prior AFCI experiments:

* `TOTAL_INPUT_TOKENS` = `input_tokens` + `cache_creation_input_tokens` +
  `cache_read_input_tokens`. **MAD tokens count.**
* `total_output_tokens`
* provider `costUSD`
* `MODEL_WALL_SECONDS`
* `TOTAL_TOOL_CALLS`, `EXPLORATION_CALLS`, `UNIQUE_FILES_READ`
* `READ`, `GREP`, `GLOB`, `BASH`, `EDIT`, `WRITE` call counts
* `FILES_REEDITED`
* turns used
* CI command runs; test command runs
* failed visible-gate cycles, where deterministically observable
* files changed; lines added; lines removed; net lines

**No metric may silently treat "unavailable" as zero.** A metric that cannot be
derived for a run is recorded as unavailable and is excluded from any median
that depends on it, with the exclusion stated.

Workspace preparation time, pre-warm time and evaluation time are recorded
**separately** and are **not** part of `MODEL_WALL_SECONDS`.

---

## 8. The frozen visible gate

One condition-neutral gate, identical in both arms, stated in the task text in
terms of *what the candidate changed* rather than of any particular package — so
the gate itself leaks no placement information.

| # | Command | Cost on a prepared workspace |
| --- | --- | --- |
| 1 | `yarn tsc` | 13.4 s |
| 2 | `yarn test <package-dir> ... --runInBand` | 10.0 s |
| 3 | `yarn backstage-cli repo lint --since HEAD` | 29–39 s first call, 4 s after |
| 4 | `yarn prettier --check <file> ...` | 2.0 s |
| 5 | `yarn backstage-repo-tools api-reports --allow-all-warnings -o ae-undocumented,ae-wrong-input-file-type --include <package-dir>` | 7.0 s |

`CI=true` is set in the **run process environment** rather than written in front
of each command, so the commands are plain and the Bash allowlist in §8.1 can
match them. Jest would otherwise start in watch mode and never exit. Docker is
not used; SQLite-backed test databases are used where a database is needed.
**Nothing in the repository's lint, type or test configuration is weakened**,
and no rule is disabled to manufacture an architecture violation.

Step 3 is scoped with the repository's own `--since` mechanism against the run
workspace's single commit, so it lints exactly what the candidate changed. That
keeps the gate **placement-neutral**: it names no package, and its text is the
same for all three tasks and both conditions.

Four corrections were made to this gate before it was frozen, each because the
command was executed rather than assumed:

* **`yarn test`, not `backstage-cli repo test`.** The repository's own `test`
  script supplies `NODE_OPTIONS='--no-node-snapshot --experimental-vm-modules'`.
  Invoking the test runner directly without them fails **3 of 3** cases in a
  package that passes 3 of 3 with them. Freezing the direct invocation would
  have handed both arms a validation command that fails for a reason unrelated
  to their work.
* **`api-reports` without `--tsc`.** With `--tsc` the command recompiles from
  scratch every time and costs **456 s even warm**; without it, run after step 1,
  it costs **9 s** and reads the type-check's own output. The task text
  therefore instructs the model to run the type-check first.
* **Tests are scoped by package directory, not by `--since`.** `--since` is
  right for lint, which selects only the changed package, but `repo test
  --since HEAD` additionally selects every **dependent** package. Measured: a
  one-line comment in one package pulled in 5 projects and 847 test cases, of
  which **720 failed** — and the same 720 fail on the **untouched** tree, for
  want of a container runtime. Freezing `--since` for tests would have shown
  every candidate a wall of failures it did not cause.
* **`CI` is set in the environment, not typed in front of each command**, so
  that the frozen commands are exactly what the Bash allowlist admits.

### 8.1 The agent-visible command surface

In headless mode `acceptEdits` auto-approves edits and leaves Bash to rule
evaluation; with no allow rule the call is refused, and a benchmark that tells a
model to validate with a command it is then refused is measuring the refusal.
`SL-V2-EFF-01` established this after 44 refused attempts and 0 executions in an
earlier package. The gate commands are therefore allowlisted, and nothing else
is:

```
Bash(yarn tsc)                      Bash(yarn tsc:*)
Bash(yarn test:*)                   Bash(yarn prettier:*)
Bash(yarn backstage-cli:*)          Bash(yarn backstage-repo-tools:*)
Bash(git status:*)                  Bash(git diff:*)
```

Run process environment: `CI=true`, `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`,
`DISABLE_AUTOUPDATER=1`, with `ANTHROPIC_API_KEY`, `CLAUDE_EFFORT` and
`CLAUDE_CODE_EFFORT_LEVEL` explicitly unset so that nothing about effort or
credentials is inherited from the operator's shell.

Tools granted: `Read`, `Edit`, `Write`, `Glob`, `Grep`, `Bash`. `Task` is
excluded so one observation is one model rather than a fan-out, and
`WebSearch`/`WebFetch` are excluded so no observation can retrieve an answer
from outside the governed substrate.

**`permission_denials` is captured per run.** It is the instrument that makes a
mis-specified allowlist visible instead of silent: a run that spent its turns
being refused is identifiable after the fact rather than mistaken for a model
that chose not to validate.

### 8.2 Pre-existing conditions the gate must absorb

The evaluator additionally applies a **differential** reading of the test and
API-report steps, because the frozen substrate is not itself green on them — at
`f285f6e`, seven Postgres/MySQL test variants in one task-relevant package fail
for want of a container runtime, **720 test cases in another task-relevant
package fail for the same reason** (measured on an untouched tree while freezing
this gate), and one task-relevant API report is already flagged. The affected
package names are recorded in the private evaluator rather than here, because
naming them would narrow the placement decision. A candidate fails only on a
failure that was not present on an
untouched tree and that survives a confirming re-run. This weakens no repository
rule: the same command is run and compared against the same command's output on
an untouched tree.

The hidden functional oracle and the architecture scorer run **post hoc only**.

---

## 9. Dependency and run isolation

A full `yarn install` costs ~10 minutes; eighteen of them is three hours of
install and three hours of variance unrelated to the experiment. Sharing one
`node_modules` is not available, for three reasons that were **measured on this
substrate, not assumed**:

1. **Yarn links every workspace package as an NTFS directory junction with an
   absolute target.** All 204 point at the tree they were installed in. A naive
   copy therefore leaves every `@backstage/*` import resolving to the *template's*
   sources — the model's own edits invisible to the build, and two runs reading
   one source tree. It fails silently.
2. **The dependency layout is 21 directories, not one.** Besides the root
   `node_modules`, yarn creates 20 more inside the workspace sources — including
   one inside a package that a task's own work touches. All 20 are gitignored,
   so `git archive` does not carry them and a root-only
   copy leaves those packages unable to resolve their dependencies. Four further
   `node_modules` directories under `__fixtures__` **are** tracked by git and
   arrive with the export; copying those too would be wrong. The split is derived
   with `git check-ignore`, not by pattern-matching a path.
3. **`node_modules` is written to during a run** (`backstage-cli`, api-extractor
   and prettier all cache under `node_modules/.cache`), so a shared tree is a
   shared mutable surface.

### 9.1 The chosen method

Per run: materialise the model-visible export; copy each of the 21 dependency
roots excluding junctions (`robocopy /XJ`); re-create all 204 junctions pointing
at **that run's own tree**; create a single-commit git repository; then warm the
caches.

The frozen layout manifest (`dependency_layout_f285f6e.json`, SHA-256
`495accaa39fa5016f488f47f2c73c7a1db8f4c61f1356e31f4ac7c27b31dae68`) records:

| Field | Value |
| --- | --- |
| dependency roots | 21 |
| junctions | 204 |
| regular files | 266,599 |
| total bytes | 1,979,103,089 |
| `dependency_digest` | `5442dbd9ddb67822fbda2e632e537839541c3887a93043ddedee2ab1dd7aca09` |

Tool cache directories are excluded from the digest, because the pre-warm writes
into them legitimately; including them would make the digest a measure of how
much warming had happened rather than of which dependencies were installed.

### 9.2 Measured cost

| Step | Seconds |
| --- | --- |
| build model-visible export | 14–15 |
| export contamination proof (6 checks) | 95–108 |
| copy 21 dependency roots | 30–38 |
| create 204 junctions | 6–7 |
| git init + single commit | <1 |
| **pre-warm (3 passes of the frozen gate)** | **~570** |
| integrity verification | 13 |
| **total per run** | **~13 minutes** (measured 749 s, 787 s, 799 s) |

Preparation was validated end to end on five disposable workspaces covering all
three tasks; the last two used the final, corrected command set. In the last
one every one of the 18 pre-warm steps exited 0.

Disk: ~2.3 GB per prepared run (1.84 GB dependencies + sources + build output).
18 runs ≈ 41 GB against 137 GB free; a run's workspace is reclaimable after its
evaluation.

### 9.3 Why the workspace is pre-warmed

TypeScript's incremental state and Jest's transform cache are keyed by
**absolute path**, so a freshly materialised workspace is cold even on a machine
that has built this substrate many times. Measured: `yarn tsc` **244 s cold vs
15 s warm**; one package's tests **234 s cold vs 9 s warm**; warming one package
does **not** warm another (117 s for a second package in an already-warm
workspace); and copying the warm `dist-types` between workspaces recovers only a
third of it (244 s → 164 s), because the build info embeds absolute paths.

Three passes, because two are not reliably enough and the number was measured
rather than chosen. On one prepared workspace `yarn tsc` cost 180 s, then 150 s,
and reached its steady 15 s only on the **third** pass, where it stayed (15 s,
15 s, 15 s); on another it converged by the second (279 s, 17.5 s, 13.4 s). Two
passes would have left the slower case paying ~150 s inside the model's first
gate call. The third pass costs ~39 s when the workspace has already converged,
which is the price of making the starting state the same either way.

Left unwarmed, roughly five minutes of first-touch cost would land inside the
**first gate command the model runs** — charged to `MODEL_WALL_SECONDS` and to
the turn budget, as an artifact of workspace freshness. The warm-up therefore
runs during preparation, before the model is launched, and its cost is recorded
separately.

The warmed package set is the **union of the packages the task's legal and
target-violating references touch**. Warming both homes equally is what keeps it
placement-neutral: it is invisible to the model and cannot make either placement
cheaper to validate. A candidate that writes to some third package pays that
package's cold cost, which is a real cost of its own choice and is symmetric
across conditions.

Real-time antivirus is enabled on this machine and cannot be changed without
administrator rights. It inflates first-touch costs and is the reason the
warm-up needs three passes. It applies identically to both arms, and within-block
condition order is randomised, so it does not bias the comparison; it is recorded
here as a measured environmental condition.

### 9.4 What was proved, not asserted

Verified on prepared workspaces:

| Property | Evidence |
| --- | --- |
| identical dependency state in every run | `dependency_digest`, file count and total bytes match the frozen manifest exactly |
| resolution points at the run's own tree | `require.resolve()` of a workspace `@backstage/*` package from run A returns a path **inside run A**; from run B, inside run B |
| source changes do not leak | a marker written into run A's copy of a workspace package is visible **only** in run A — run B and the template both report it absent |
| one run cannot modify another's dependencies | after run A was edited, run B's digest still matched the frozen manifest |
| the template is never mutated | `git status` on the template remained clean throughout |
| C1/C4 setup identical | the export tree hash is `4dfadc…2563` for every prepared workspace and every task |
| the warm-up touches no tracked file | `git status --porcelain` is empty after the pre-warm |
| the run repository carries no history | exactly 1 commit, 0 remotes |

The run workspace is a git checkout because three condition-neutral things need
one — the repository's own `--since` tooling, the gate's changed-file
derivation, and the scorer's change scoping. It carries exactly one commit with
a neutral message, so there is no future history to leak.

---

## 10. Session and context isolation

Every substantive observation uses a **fresh process**, a **fresh session**, no
`--resume`, no `--continue`, no `--from-pr`, a fresh `--session-id`,
`--no-session-persistence`, a clean model-visible export, no prior run's
conversation, no future git history, no hidden evaluator material and no
historical solution. The launcher refuses any restoration flag.

---

## 11. The frozen continuation rule

**Frozen before data.**

### 11.1 ARCHITECTURE SIGNAL — all three must hold

1. C4 has **fewer** target-violation runs than C1 **overall**;
2. C4 has **fewer** target violations in **at least 2 of the 3 tasks**;
3. C4's `FUNCTIONAL_VALID` count is **no more than 1 below** C1's.

**If all three hold:** authorize a larger Backstage architecture-complexity
study.

**If any fails:** do **not** automatically expand.

### 11.2 Efficiency is secondary and cannot override §11.1

Reported separately, as medians over **functionally valid paired blocks**:

* median `TOKEN_RATIO` (C4/C1 `TOTAL_INPUT_TOKENS`)
* median `WALL_RATIO`
* median `EXPLORATION_RATIO`
* median `TOOL_RATIO`
* median `COST_RATIO`

An unfavourable efficiency result does **not** veto an architecture signal, and
a favourable one does **not** rescue a failed one.

### 11.3 What is never done with this pilot

* **No p-values. No confidence intervals. No confirmatory causal claim.**
* No pooling with AFCI-Bench: `AFCI_BACKSTAGE_PILOT` treatment estimates are
  never mixed with `V2_EFF_ATTEMPT2` or `V2_LOWER_MODEL_PILOT` estimates. A
  descriptive side-by-side is permitted and must be labelled as descriptive.
* It enters no E1, treatment-effect or power analysis.
* It confers no primary-model selection and no confirmatory eligibility.

---

## 12. The schedule

| Field | Value |
| --- | --- |
| Seed | `AFCI_BACKSTAGE_PILOT_V1_20260919` |
| Ordering method | sort by SHA-256 of a seeded string; no language RNG, so the schedule is reproducible on any machine and any Python |
| Runs | 18 |
| Blocks | 9 |
| Plan SHA-256 | `4bc65b6112e603b8fb742b1380de06403d95ae7911ae5aa1102b1df09f30ac98` |
| Scientific projection SHA-256 | `e8e8f2a3e141b1911d183f2e963ff2c7cd0e106cb7c31a8981ed053ff21f126e` |
| Execution attempt | 1 |
| Artifact root | `D:\afci-runs\backstage-pilot` |
| Workspace root | `D:\afci-sterile\backstage-pilot` |

Two orders are randomised deterministically: which condition runs first **within
a block** (so session drift cannot land systematically on one arm), and the
order of the blocks (so the tasks interleave). C1 runs first in 4 blocks and C4
in 5.

The **scientific projection** — the five values that *are* the experiment
(`sequence`, `task_id`, `condition`, `reset_state`, `repetition`) — is hashed
separately, so that a later change to an infrastructure field is visibly not a
change to the experiment, and a change to the experiment cannot hide inside one.

### 12.1 Run identity

Each run id is derived from the run purpose, the task, **the task's frozen
bytes**, the substrate content hash, the mode, the repetition, the reset state
and the execution attempt. Dropping any one of these has previously produced
collisions in this study. The readable prefix carries the same facts in order.

Preflight derives all 18 identities with no model and no cost, and refuses the
whole execution on a single duplicate id, a single duplicate or occupied
destination, or a single overlap with a prior study's artifact root. **All 18
checks pass: 18 unique run ids, 18 unique artifact directories, 18 unique
workspace directories, all unoccupied, none overlapping a prior root.**

---

## 12.2 Frozen artifact manifest

Everything this decision freezes, by content hash. All paths are relative to
`afci-bench-evaluator-private/backstage/`.

| Artifact | SHA-256 |
| --- | --- |
| `tasks/T1_TASK.md` | `c3033787506fa7d30e909638ce64f407fbe9a89a26fb4d84eaf52222a0f8385b` |
| `tasks/T2_TASK.md` | `60dc08a133c47433e01eb62d96b09e52239e632e8f93df9662a09b46f8a1f32f` |
| `tasks/T5_TASK.md` | `8db333264895b3d6df869adf27cc419c9adbd696da065cead8bbae610d62ba3d` |
| `tasks/BACKSTAGE_MAD_V1.md` | `5bab8d931c24834dc268eb2cdad546abbe13b5e2d9e51e6fbdcfeed09754a7cf` |
| `dependency_layout_f285f6e.json` | `495accaa39fa5016f488f47f2c73c7a1db8f4c61f1356e31f4ac7c27b31dae68` |
| `AFCI_BACKSTAGE_PILOT_RUN_PLAN.json` | `4bc65b6112e603b8fb742b1380de06403d95ae7911ae5aa1102b1df09f30ac98` |
| `runtime/effort_provenance_settings.json` | `f84897714ad6f9a9792e06f3701655becee19346d21391bb672c24d14b20e499` |
| `runtime/record_effort.js` | `a447bb7455286180772727029f35371af0554371139a4cfc653c2668484bf111` |
| `prepare_run_workspace.py` | `ba0e8c9b7acdaae42910342e2af365d87b3d3e9db8b24b17dac5d74c9abb5fa9` |
| `backstage_pilot_run_plan.py` | `7d1686dc6cbf6e01251b64f76ab2da002403686bf57d5eb9cabbf88779ddb47e` |

The run plan file's hash **is** the plan hash in §12: the generator writes it
with `newline=""`, so the bytes on disk are exactly the bytes that were hashed.
Python's default newline translation would have written CRLF on this platform
and made the plan's own hash unverifiable from the plan — which was caught and
fixed rather than documented as a quirk.

---

## 13. What this decision does NOT do

* It does not select a primary model. `TD-B03` stays open; `primary_model`
  stays `null`.
* It does not pass `G1` or `G2`, and does not freeze the suite.
* It does not authorize a reset arm.
* It does not re-interpret, re-score or re-read any prior result. Nothing in the
  existing study-results corpus was rewritten to produce it.
* It does not authorize expansion. §11 does, and only on the stated evidence.
* It does not execute anything. **At the moment this decision is written,
  `AFCI_BACKSTAGE_PILOT` has 18 planned observations and 0 completed.**

---

## 14. Infrastructure activity performed for this freeze

Recorded for completeness, because "no model was run" would otherwise be false:

* **one** infrastructure-only model probe (§3.2) — disposable directory, no
  Backstage content, no task, no MAD, no scoring, not study data;
* read-only enumeration of the installed runtime binary;
* the six-reference validation matrix (no model);
* workspace-preparation prototypes on disposable copies (no model).

**No benchmark condition was executed. No task was solved by a model. No C1 or
C4 result exists. No treatment metric was computed.**
