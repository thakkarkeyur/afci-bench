# docs/v2 — Claude Context Isolation Policy

Status: **development policy for study v2**. Defines how experimental runs are
isolated from development context, previous runs, and machine-level Claude
configuration, and how each run proves that isolation. This is a development
artifact; it does not freeze the final benchmark configuration and never
authorizes a paid model run.

Enforced by: [`experiments/v2/harness/context_audit.py`](../../experiments/v2/harness/context_audit.py),
validated by [`experiments/v2/schemas/context_audit.schema.json`](../../experiments/v2/schemas/context_audit.schema.json),
tested by [`experiments/v2/harness/tests/test_context_isolation.py`](../../experiments/v2/harness/tests/test_context_isolation.py).
Per-source mitigation is tabulated in
[`CONTEXT_SOURCE_MATRIX.csv`](CONTEXT_SOURCE_MATRIX.csv).

## 1. Development vs. experimental sessions

| | Development session | Experimental session |
|---|---|---|
| Purpose | Building the harness, docs, analysis | Producing benchmark evidence |
| Claude settings | **May** use high-capability settings (e.g. Opus, high effort) | Fixed, recorded per §4 / MODEL_EXECUTION_CONTROLS |
| Counts as a run? | **Never** | Yes |
| Usable as evidence? | **Never** | Yes, only if its `context_audit.json` verdict is `CLEAN` |

Development sessions (like the one that authored this policy) are explicitly
**not** experimental evidence and are never counted as runs.

## 2. Experimental session requirements (mandatory)

Every experimental run MUST:

1. Start a **fresh process** (no reattaching to a running session).
2. Use a **unique temporary HOME** (`HOME`/`USERPROFILE`).
3. Use a **unique temporary `CLAUDE_CONFIG_DIR`**.
4. **Disable auto memory**: `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`.
5. **Disable auto-update**: `DISABLE_AUTOUPDATER=1`.
6. **Never restore a previous session**: no `--continue`/`-c`, no `--resume`/`-r`,
   no `--from-pr`, and no reuse of a previous `--session-id`.
7. **Fail closed**: if any unexpected/unapproved context source is detected, or
   any isolation control is missing, the run is aborted and marked
   `CONTAMINATED`.

Required environment (set by `make_sterile_env`):

```
CLAUDE_CODE_DISABLE_AUTO_MEMORY=1
CLAUDE_CONFIG_DIR=<unique temporary directory>
DISABLE_AUTOUPDATER=1
HOME=<unique temporary directory>   (USERPROFILE on Windows)
```

Two runs always receive **different** HOME and `CLAUDE_CONFIG_DIR` directories
(proved by `test_two_runs_use_different_dirs`).

## 3. Condition rules

| Condition | Persistent instructions / memory | Permitted repository context |
|-----------|----------------------------------|------------------------------|
| **C1** | None. No repository architecture context. | None |
| **C2** | Same isolation as C1. | Only the approved **generic, token-matched** guidance file |
| **C3** | Sterile user environment. | Only the approved **condition-specific repository instruction file** |
| **C4** | No persistent repository instruction. | MAD supplied only via **explicit AFCI prompt injection**, re-injected after reset. No persistent MAD file. |

The allowlist is the single source of truth: for each condition the harness is
given the set of *approved* artifacts (path + expected SHA-256). Anything
detected that is not approved — or an approved file whose content hash does not
match — is contamination. C1 and C4 have empty filesystem allowlists (C4 differs
only in runtime prompt injection); C2 and C3 permit exactly one approved file.

Tested: C1 rejects project instructions; C3 permits only its approved
instruction (and rejects extras and tampered content); C4 rejects persistent MAD
files.

## 4. What is scanned

The harness scans the workspace, its ancestor directories, the (temporary) user
HOME, the `CLAUDE_CONFIG_DIR`, and known managed-policy locations for:

`CLAUDE.md` (project / user / ancestor / `.claude/CLAUDE.md`), `CLAUDE.local.md`,
`.claude/rules`, settings files, auto-memory files, skills, agents, commands,
hooks, plugins, MCP configuration, and managed/remote organization policy.

Each present source is recorded with its **path, scope, SHA-256 hash, and a
non-secret detail string only**. File contents, tokens, API keys, and MCP server
configurations are **never** parsed into the audit
(proved by `test_no_secret_values_recorded`).

## 5. The audit artifact

Each run emits `context_audit.json` conforming to
`experiments/v2/schemas/context_audit.schema.json`, containing: run ID,
condition, temporary HOME, `CLAUDE_CONFIG_DIR`, detected context sources,
permitted context sources, SHA-256 hashes of approved context, auto-memory
status, session-restoration status, per-component (MCP / plugins / hooks /
skills / agents / commands) status, and the contamination verdict with reasons.
A non-`CLEAN` verdict aborts the run (CLI exit code 1).

## 6. Findings on the reference development machine (2026-07-19)

An inventory scan of this machine (CLI `claude` 2.1.209; host extension 2.1.212)
found **50 context sources**, all account/user level:

- **40+ auto-memory files** under `CLAUDE_CONFIG_DIR/projects/*/memory/` (across
  several unrelated projects, including this repository's own memory).
- User `~/.claude/settings.json` (`model: opus[1m]`, `effortLevel: xhigh`).
- Populated `~/.claude/skills/` and `~/.claude/plugins/`.
- `~/.claude.json` (MCP configuration container).
- Account-tied **managed/remote organization policy** cached at
  `~/.claude/policy-limits.json` (keys: `compliance_taints`, `defaults`,
  `monitoring_notice`, `restrictions`) and `~/.claude/remote-settings.json`.

Not present: any `CLAUDE.md` / `CLAUDE.local.md` (user, project, or ancestor),
project `.claude/`, `.mcp.json`, hooks, agents, commands, `.claude/rules`, or a
local `managed-settings.json` at the documented OS path.

## 7. Sources that cannot be disabled reliably; is a container/VM mandatory?

Almost every source above is reliably neutralized by the sterile environment
(temporary HOME + temporary `CLAUDE_CONFIG_DIR` + the mandatory env vars +
workspace-level condition control), optionally reinforced by `claude --bare`
(which skips hooks, LSP, plugin sync, attribution, auto-memory, keychain reads,
and `CLAUDE.md` auto-discovery). See the matrix for the per-source mechanism.

The **one source that does not follow the filesystem** is the **managed/remote
organization policy**. On this machine it is delivered to the authenticated
Claude account (cached in `policy-limits.json`/`remote-settings.json`), not via a
local `managed-settings.json`. A fresh HOME/`CLAUDE_CONFIG_DIR` does not remove
it — it is re-applied for the same account.

**Therefore, an isolated container (or equivalent dedicated environment) with a
dedicated identity is MANDATORY for every counted run** — binding decision D11
([`CRITICAL_DESIGN_DECISIONS.md`](CRITICAL_DESIGN_DECISIONS.md)), blocker
**`TD-B19`**. It is the only way to guarantee the absence of (a) account-tied
managed/remote policy and (b) any host-level `managed-settings.json`. The
isolated environment authenticates with a **dedicated identity** (or `--bare` +
`ANTHROPIC_API_KEY`, once it is verified that organization policy does not also
bind the API-key path) and runs the audit. **Every counted run requires a
`context_audit` verdict of `CLEAN` with managed policy recorded as absent**;
contaminated executions are excluded as **environment failures**
(`EXCL_CONTAMINATED` / `SETUP_CONTAMINATED`), never treated as valid model
outcomes. The container image digest is captured in `environment_fingerprint`
(non-blocking companion `TD-N04`).

Minimum acceptable configuration if a container is not used: temporary HOME +
temporary `CLAUDE_CONFIG_DIR` + the three mandatory env vars + no session
restoration + `--bare` + a dedicated API key, with a `CLEAN` audit that confirms
no managed policy is present. This is weaker than a container and must be
justified explicitly.
