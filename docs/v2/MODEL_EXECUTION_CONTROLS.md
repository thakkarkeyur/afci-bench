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
resolves to **`claude-opus-4-8[1m]`** — verified: a real run transcript records
`"model":"claude-opus-4-8[1m]"` on every turn. **Pin the full resolved id**, not
the alias, to eliminate alias drift; an unrecognized id is rejected (no silent
degradation).

## 3. Control determination (adversarially verified)

Each control was assessed against a two-part bar — it is usable as an
experimental control only if it can be **both** explicitly pinned for a `claude
-p` run **and** have its actually-used value recorded from machine-readable
output — then an independent agent tried to refute each verdict.

| Control | Pinnable | Recordable | Suitable as control | Verified |
|---------|----------|------------|---------------------|----------|
| **model** | ✅ yes | ✅ yes | ✅ **yes** | local `--help` + real transcript + docs |
| **effort** | ✅ yes | ❌ no | ❌ no | local `--help` (pin); recording absent |
| **thinking** | ❌ no | ❌ no | ❌ no | local `--help` (no flag); rest doc-only/unverified |
| **workflow / agent mode** | ⚠️ OFF-state only | ❌ no | ❌ no | local `--help` (`--agent`/`--agents`); ON mode not pinnable under `-p` |

### 3.1 model — SUITABLE (the only fully controlled knob)
- **Pin:** `--model claude-opus-4-8[1m]` (also `settings:model`, `env:ANTHROPIC_MODEL`, `sdk:model`).
- **Record:** `--output-format json` (`modelUsage` / per-model cost map, keys every model incl. subagents) or `--output-format stream-json` (`system`/`init` `model` field). Directly verified: a transcript records the fully-resolved id.
- **Caution:** do **not** set `--fallback-model` for a controlled run (it can substitute another model when overloaded); if used, capture `modelUsage` to detect what actually ran.

### 3.2 effort — PINNABLE BUT NOT RECORDABLE → not a clean control
- **Pin:** `--effort <low|medium|high|xhigh|max>` (verified in `--help`; levels exactly those five). Also `settings:effortLevel` (**rejects `max`/`ultracode`**), `env:CLAUDE_CODE_EFFORT_LEVEL` (docs). Prefer the **`--effort` flag**.
- **Not recordable:** no `--output-format json`/`stream-json`/SDK field echoes the effective effort; it appears only in the interactive session header (a UI string). Unsupported levels **silently fall back** to the highest supported ≤ requested, and nothing reports the value actually used.
- **Consequence:** you must **log the `--effort` value you passed** as run metadata; treat it as an *input record*, not a readback. Env-var discrepancy: this machine exposes `CLAUDE_EFFORT=xhigh` but docs name the input `CLAUDE_CODE_EFFORT_LEVEL`; `CLAUDE_EFFORT` is unconfirmed as an input — prefer the flag.

### 3.3 thinking — NOT PINNABLE, NOT RECORDABLE → not a factor
- `claude --help` has **zero** `think`/`reason` flags (the only budget-like flag, `--max-budget-usd`, is a USD cost cap, not a thinking budget). No thinking key in settings/env on this install.
- On **Opus 4.8** thinking is **adaptive and governed by effort** — there is no settable token budget and no output field to read it back. Doc-only knobs (`MAX_THINKING_TOKENS`, `alwaysThinkingEnabled`, `/config thinking`, SDK `thinking`) are model-dependent and were **not verifiable** here. The interactive "Thinking" toggle and the `ultrathink` keyword are interactive/in-context only.
- **Per the work package, Thinking ON/OFF is NOT an experimental factor.** It rides on the chosen effort level.

### 3.4 workflow / agent mode ("Ultracode + workflows") — not a clean control
- Only the **OFF/disabled** direction is reliably reproducible: `env:CLAUDE_CODE_DISABLE_WORKFLOWS=1` / `settings:disableWorkflows` (docs), plus explicit named agents via `--agent`/`--agents` (verified in `--help`).
- The **ON** "Ultracode" mode is **not reliably pinnable under `-p`**: `--effort` enum has **no `ultracode`** on this install, the per-prompt `ultracode` keyword does not trigger a workflow under `-p`, and the mode is session-only / not persistable. It is also **not recordable** (no output field reports mode; only incidental subagent activity is visible via `parent_tool_use_id` / `modelUsage`).
- **For deterministic benchmark runs, disable workflows explicitly** (`CLAUDE_CODE_DISABLE_WORKFLOWS=1`) to remove this uncontrolled variable.

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

## 7. Open questions (to resolve before freezing the final config)

1. Does 2.1.209's `--output-format json` result contain `model`/`modelUsage` at
   runtime? Doc-backed and consistent with the local transcript, but not
   confirmed by executing a paid run (deliberately avoided).
2. Reconcile the two effort env vars (`CLAUDE_EFFORT` seen locally vs.
   `CLAUDE_CODE_EFFORT_LEVEL` in docs): real input, legacy alias, or echo?
3. Does `--effort ultracode` work on 2.1.209 despite being absent from the
   `--help` enum?
4. Is there **any** headless mechanism that reports the effort level actually
   used after a fallback? None found.
5. Does `MAX_THINKING_TOKENS` affect Opus 4.8, and can thinking config be
   recorded from headless output at all? Both unconfirmed.
6. Does the local `CLAUDE_CODE_ENABLE_TASKS=0` (and org policy) suppress
   workflow/subagent orchestration in `-p` runs?
7. Do Agent SDK 0.3.212 `thinking`/`effort` options round-trip into any
   recordable init/result field, or are they input-only like the CLI flags?

## 8. Methodology

Determined via local read-only inspection (`claude --version`, `claude --help`,
`claude doctor`; settings/env; a real workflow transcript already on disk) plus
official Anthropic/Claude Code documentation, then **each verdict was
adversarially refuted** by an independent agent under the rule "if either
pinning or recording is unverified/absent, the control is unsuitable." No paid
`claude -p` model run was executed. Docs are not version-pinned to CLI 2.1.x, so
doc-only mechanisms are marked unverified accordingly.
