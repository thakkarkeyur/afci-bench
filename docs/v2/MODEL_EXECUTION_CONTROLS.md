# docs/v2 — Model Execution Controls (Audit)

Status: **development audit for study v2**. Determines which Claude Code
model-execution controls can be *programmatically pinned* and *recorded* for
non-interactive runs. Per the work package this **does not freeze the final
benchmark configuration** — it only establishes what can be controlled
reliably. No paid model run was performed to produce this document (findings
come from `claude --help`/`claude doctor`, local settings/env, official
Anthropic/Claude Code docs, and a real workflow transcript already on disk),
and every claim is tagged verified vs. doc-only.

Companion table: [`MODEL_CONFIGURATION_MATRIX.csv`](MODEL_CONFIGURATION_MATRIX.csv).

## 0. Evidence legend (how each claim is grounded)

Every behavioural claim below carries an explicit evidence tag. Nothing about
*runtime* behaviour has been confirmed by a controlled `claude -p` execution
(none was run), so any runtime claim is at most a well-supported hypothesis:

- **[CLI-verified]** — confirmed from `claude --version` / `claude --help` on the
  pinned CLI **2.1.209**. Covers *syntax and flag existence only*, never runtime
  behaviour.
- **[transcript]** — observed in a real workflow transcript already on disk. A
  single incidental observation, not a controlled experiment.
- **[doc-derived]** — taken from Anthropic / Claude Code documentation that is
  **not** version-pinned to CLI 2.1.x; the behaviour was **not** executed here.
- **[dry-run-required]** — **UNRESOLVED**: a runtime behaviour that must be
  validated by a controlled real dry run before it can be treated as fact.
  Useful as a hypothesis; do **not** rely on it when freezing the final config.

A claim may carry several tags. All open **[dry-run-required]** items are
collected in §7.

## 1. Installed versions (exact)

| Component | Version | Source |
|-----------|---------|--------|
| Claude Code CLI (`claude` on PATH) | **2.1.209** | `claude --version` |
| Host IDE extension binary (interactive UI) | **2.1.212** | `anthropic.claude-code-2.1.212` (`CLAUDE_CODE_ENTRYPOINT=claude-vscode`) |
| Claude Agent SDK | **0.3.212** | `CLAUDE_AGENT_SDK_VERSION` |

Note the interactive UI (2.1.212) and the scriptable CLI (2.1.209) are different
builds. Non-interactive/benchmark runs must use the pinned **CLI 2.1.209** (or a
single, explicitly recorded version), not the UI build.
`claude config` is **not** a subcommand in 2.1.209 (config is read from settings
files / flags / env), so do not script against `claude config`.

## 2. Model identifiers for non-interactive execution

`claude --help` confirms `--model` accepts an **alias** (`opus`, `sonnet`,
`fable`) or a **full model name** (e.g. `claude-fable-5`). Full identifiers from
the Anthropic model catalog:

| Model | Full id | 1M-context variant |
|-------|---------|--------------------|
| Opus 4.8 | `claude-opus-4-8` | `claude-opus-4-8[1m]` |
| Sonnet 5 | `claude-sonnet-5` | — |
| Fable 5 | `claude-fable-5` | — |
| Haiku 4.5 | `claude-haiku-4-5-20251001` | — |

On this machine `~/.claude/settings.json` pins `model: "opus[1m]"`, which
**[transcript]** resolves to **`claude-opus-4-8[1m]`**: a real run transcript
records `"model":"claude-opus-4-8[1m]"` on every turn. This is a single
transcript observation, not a controlled dry run — the alias→full-id resolution
under `claude -p 2.1.209` is **[dry-run-required]** (§7 Q1). **Pin the full
resolved id**, not the alias, to eliminate alias drift. The expectation that an
unrecognized id is rejected rather than silently degraded is **[doc-derived;
dry-run-required]** — it is not asserted by `--help` and was not executed here
(§7 Q8).

## 3. Control determination (adversarially verified)

Each control was assessed against a two-part bar — it is usable as an
experimental control only if it can be **both** explicitly pinned for a `claude
-p` run **and** have its actually-used value recorded from machine-readable
output — then an independent agent tried to refute each verdict.

| Control | Pinnable | Recordable | Suitable as control | Evidence |
|---------|----------|------------|---------------------|----------|
| **model** | ✅ yes | ⚠️ likely | ✅ **yes** (pin), pending record | pin **[CLI-verified]**; resolved-id **[transcript]**; readback via `modelUsage` **[doc-derived; dry-run-required]** (§7 Q1) |
| **effort** | ✅ yes | ❌ no | ❌ no | pin flag **[CLI-verified]**; "not recordable" is a negative-existence claim **[doc-derived; dry-run-required]** (§7 Q4) |
| **thinking** | ❌ no | ❌ no | ❌ no | absence of `--think`/`--reason` flag **[CLI-verified]**; adaptivity/budget behaviour **[doc-derived; dry-run-required]** (§7 Q5) |
| **workflow / agent mode** | ⚠️ OFF-state only | ❌ no | ❌ no | `--agent`/`--agents` exist **[CLI-verified]**; `--effort` enum has no `ultracode` **[CLI-verified]**; ON-mode behaviour under `-p` **[doc-derived; dry-run-required]** (§7 Q3/Q6) |

### 3.1 model — the most controllable knob (pin verified; readback pending a dry run)
- **Pin:** `--model claude-opus-4-8[1m]` **[CLI-verified]** the flag exists and
  accepts alias or full id (also `settings:model`, `env:ANTHROPIC_MODEL`,
  `sdk:model` **[doc-derived]**).
- **Record:** `--output-format json`/`stream-json` **[CLI-verified]** the flags
  exist. That the JSON payload actually carries `modelUsage` / a `system.init`
  `model` field is **[doc-derived; dry-run-required]** (§7 Q1). A transcript
  records the fully-resolved id **[transcript]**, but that is not the same as
  confirming the headless `-p` JSON schema.
- **Caution:** do **not** set `--fallback-model` for a controlled run. The flag
  exists **[CLI-verified]**; that it substitutes another model when the primary
  is overloaded is **[doc-derived; dry-run-required]** (§7 Q9). If used, capture
  `modelUsage` to detect what actually ran.

### 3.2 effort — PINNABLE; recordability & fallback behaviour unresolved → not a clean control
- **Pin:** `--effort <low|medium|high|xhigh|max>` **[CLI-verified]** (the enum is
  exactly those five levels in `--help`). Also `settings:effortLevel` — the claim
  that it **rejects `max`/`ultracode`** is **[doc-derived; dry-run-required]**
  (§7 Q10), not shown by `--help` (which validates the *flag* enum, not the
  settings loader). `env:CLAUDE_CODE_EFFORT_LEVEL` is **[doc-derived]**. Prefer
  the **`--effort` flag**.
- **Not recordable (working hypothesis):** the claim that no
  `--output-format json`/`stream-json`/SDK field echoes the effective effort — so
  it appears only in the interactive session header — is a negative-existence
  claim, **[doc-derived; dry-run-required]** (§7 Q4). The related claim that
  unsupported levels **silently fall back** to the highest supported ≤ requested
  with no readback is likewise **[doc-derived; dry-run-required]** (§7 Q10).
- **Consequence:** regardless of the above, **log the `--effort` value you
  passed** as run metadata and treat it as an *input record*, not a readback —
  this is the safe course whether or not a readback later proves to exist.
  Env-var discrepancy: this machine exposes `CLAUDE_EFFORT=xhigh` **[CLI-verified
  present]** but docs name the input `CLAUDE_CODE_EFFORT_LEVEL` **[doc-derived]**;
  whether `CLAUDE_EFFORT` is a real input is **[dry-run-required]** (§7 Q2) —
  prefer the flag.

### 3.3 thinking — NOT PINNABLE, NOT RECORDABLE → not a factor
- `claude --help` has **zero** `think`/`reason` flags (the only budget-like flag, `--max-budget-usd`, is a USD cost cap, not a thinking budget). No thinking key in settings/env on this install.
- On **Opus 4.8** thinking is **adaptive and governed by effort** — there is no settable token budget and no output field to read it back. Doc-only knobs (`MAX_THINKING_TOKENS`, `alwaysThinkingEnabled`, `/config thinking`, SDK `thinking`) are model-dependent and were **not verifiable** here. The interactive "Thinking" toggle and the `ultrathink` keyword are interactive/in-context only.
- **Per the work package, Thinking ON/OFF is NOT an experimental factor.** It rides on the chosen effort level.

### 3.4 workflow / agent mode ("Ultracode + workflows") — not a clean control
- Only the **OFF/disabled** direction is reliably reproducible:
  `env:CLAUDE_CODE_DISABLE_WORKFLOWS=1` / `settings:disableWorkflows`
  **[doc-derived]**, plus explicit named agents via `--agent`/`--agents`
  **[CLI-verified]**.
- The **ON** "Ultracode" mode is **not reliably pinnable under `-p`**: `--effort`
  enum has **no `ultracode`** on this install **[CLI-verified]**. The claims that
  the per-prompt `ultracode` keyword does **not** trigger a workflow under `-p`,
  that the mode is session-only / not persistable, and that it is **not
  recordable** (only incidental subagent activity via `parent_tool_use_id` /
  `modelUsage`) are **[doc-derived; dry-run-required]** (§7 Q3/Q6) — none was
  executed under `-p 2.1.209`.
- **For deterministic benchmark runs, disable workflows explicitly**
  (`CLAUDE_CODE_DISABLE_WORKFLOWS=1`) to remove this uncontrolled variable. This
  recommendation stands regardless of the unresolved items, because it removes
  the variable rather than relying on characterising it.

## 4. UI → non-interactive mapping

The interactive UI's three chips decompose for a headless `-p` run as:

1. **Model "Opus"** → `--model claude-opus-4-8[1m]` — fully controlled + recorded.
2. **Effort chip "Ultracode - xhigh + workflows"** → split: `--effort xhigh` is the reproducible part (pinnable, **log it yourself**); the "ultracode + workflows" orchestration layer has **no reliable `-p` equivalent** → **omit**, and for determinism set `CLAUDE_CODE_DISABLE_WORKFLOWS=1`.
3. **"Thinking" toggle** → **no** pinnable+recordable `-p` equivalent on Opus 4.8 → omit; it rides on effort.

## 5. Exact reproduction command (reliably-controllable part only)

```bash
# Reproduces the reliably-pinnable part of the current UI config (Opus 4.8 + xhigh effort),
# with workflows disabled for determinism and json output to record the model actually used.
CLAUDE_CODE_DISABLE_WORKFLOWS=1 \
claude -p "<YOUR_PROMPT>" \
  --model claude-opus-4-8[1m] \
  --effort xhigh \
  --output-format json
```

Deliberately **omitted** because not reliably pinnable/recordable under `-p`: the
"Thinking" toggle and the "Ultracode + workflows" mode. The `--effort` value is
**not** echoed in the JSON output, so record the flag you passed as run metadata.

## 6. Rules for study v2

1. **Same model-execution configuration within each model across C1–C4.** Only
   the *context* (per the isolation policy) may differ between conditions; the
   `--model`, `--effort`, workflow state, and CLI version must be identical for
   all four conditions of a given model. Compare across models only by repeating
   the whole C1–C4 set under each model's own fixed config.
2. **Record per run:** the pinned CLI version, the exact `--model` id (and the
   resolved id from `modelUsage`/`system.init`), and the `--effort` flag value
   (as input metadata, since it is not recordable from output).
3. **Thinking is not an experimental factor** (§3.3).
4. **Workflows disabled** (`CLAUDE_CODE_DISABLE_WORKFLOWS=1`) for benchmark runs
   unless a workflow/agent arm is later added with an explicit, recordable
   mechanism.
5. Controls that cannot be both pinned and recorded (**effort readback**,
   **thinking**, **workflow ON mode**) are **not** treated as verified controls
   and are **not** silently approximated.
6. **`npm run ci:agent` is the ONLY CI command visible to the coding model**
   (type-check + visible unit tests + ordinary non-architecture lint; no
   `@nx/enforce-module-boundaries`, no hidden checks). **`npm run ci`
   (architecture-enforcing) is repository validation, not agent feedback**, and
   is never part of a run's edit-verify loop. Hidden acceptance and
   architecture-oracle checks never run inside the model's workspace. See
   [`EXPERIMENTAL_CI_POLICY.md`](EXPERIMENTAL_CI_POLICY.md). Each run records this
   in the manifest's `agent_visible_ci` block (`TD-B16`).

## 7. Open questions (to resolve before freezing the final config)

> **Q1 and Q8 are explicit dry-run BLOCKERS before the paid pilot** — the
> **resolved-model-id readback** (Q1) and the **invalid-model-id rejection** (Q8)
> **must** be verified through controlled dry runs **after the runner exists**.
> They are **not** performed in this work package (no runner; no paid/dry run).
> Tracked as **`TD-B21`** (cross-references `TD-B02`); see
> [`CRITICAL_DESIGN_DECISIONS.md`](CRITICAL_DESIGN_DECISIONS.md) D12 and
> [`PILOT_AND_POWER_POLICY.md`](PILOT_AND_POWER_POLICY.md) Stage 0.

1. Does 2.1.209's `--output-format json` result contain `model`/`modelUsage` at
   runtime? Doc-backed and consistent with the local transcript, but not
   confirmed by executing a paid run (deliberately avoided). **Dry-run BLOCKER
   before the paid pilot (`TD-B21`).**
2. Reconcile the two effort env vars (`CLAUDE_EFFORT` seen locally vs.
   `CLAUDE_CODE_EFFORT_LEVEL` in docs): real input, legacy alias, or echo?
3. Does `--effort ultracode` work on 2.1.209 despite being absent from the
   `--help` enum, and does the per-prompt `ultracode` keyword trigger a workflow
   under `-p`? (Both asserted negative in §3.4 on doc grounds only.)
4. Is there **any** headless mechanism that reports the effort level actually
   used after a fallback? Assumed none; the negative is **[dry-run-required]**.
5. Does `MAX_THINKING_TOKENS` affect Opus 4.8, and can thinking config be
   recorded from headless output at all? Both unconfirmed.
6. Does the local `CLAUDE_CODE_ENABLE_TASKS=0` (and org policy) suppress
   workflow/subagent orchestration in `-p` runs?
7. Do Agent SDK 0.3.212 `thinking`/`effort` options round-trip into any
   recordable init/result field, or are they input-only like the CLI flags?
8. Is an **unrecognized `--model` id rejected** (hard error) rather than silently
   degraded on 2.1.209? Asserted in §2 on doc grounds; not executed. **Dry-run
   BLOCKER before the paid pilot (`TD-B21`).**
9. Does **`--fallback-model` actually substitute** another model when the primary
   is overloaded (the §3.1 rationale for avoiding it), and is the substitution
   visible in `modelUsage`? Doc-derived; not executed.
10. Does `settings:effortLevel` **reject `max`/`ultracode`** (§3.2), and do
    unsupported `--effort` levels **silently downshift** to the highest supported
    level with no readback? Both doc-derived; a real dry run is required to
    confirm the settings-loader and fallback behaviour.

## 8. Methodology

Determined via local read-only inspection (`claude --version`, `claude --help`,
`claude doctor`; settings/env; a real workflow transcript already on disk) plus
official Anthropic/Claude Code documentation, then **each verdict was
adversarially refuted** by an independent agent under the rule "if either
pinning or recording is unverified/absent, the control is unsuitable." No paid
`claude -p` model run was executed. Docs are not version-pinned to CLI 2.1.x, so
doc-only mechanisms are marked unverified accordingly.
