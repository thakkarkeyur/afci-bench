# docs/v2 — Environment Baseline (Reproducible Dependency Base)

Status: **development baseline for study v2**. This document records the exact
toolchain and the deterministic dependency state used for all v2 development and
future experimental runs. It is a development artifact — it does **not** freeze
the final benchmark configuration and it is **not** an experimental result.

## 1. Pinned toolchain

| Component | Pinned value | Where enforced / recorded |
|-----------|--------------|---------------------------|
| Node.js   | `20.20.2`    | `.nvmrc`, this document, CI (`node-version: [20.x]` currently resolves to 20.20.2) |
| npm       | `10.8.2`     | `package.json` `packageManager` field, this document (npm bundled with Node 20.20.2) |
| lockfile  | `lockfileVersion: 3` | `package-lock.json` |

Rationale: the GitHub Actions workflow ([.github/workflows/ci.yml](../../.github/workflows/ci.yml))
builds on `ubuntu-latest` with `node-version: [20.x]` and installs the npm that
ships with that Node. Node 20 is therefore the canonical major version. To make
the base reproducible we pin the exact patch (`20.20.2`) locally via `.nvmrc`
and record the bundled npm (`10.8.2`) via the `packageManager` field.

`node-version: 20.x` in CI resolves to the newest 20.x available at run time,
so CI and local can drift by patch level. See the recommendations in §7.

## 2. Host environment used to generate this baseline

- OS: Windows 11 Pro (10.0.26200), local developer machine.
- Node version manager: `nvm-windows` (nvm4w). `Node 20.20.2` installed via
  `nvm install 20`; activated via `nvm use 20.20.2`.
- CI environment: `ubuntu-latest` (Linux). Lockfile is OS-independent
  (`lockfileVersion: 3`, no platform-locked optional binaries in the diff).

## 3. Reproducibility controls added on study-v2

- `.nvmrc` → `20.20.2` (consumed by nvm-unix, fnm, Volta, asdf, and
  `actions/setup-node` via `node-version-file`; documentary under nvm-windows,
  which does not auto-read `.nvmrc`).
- `package.json` `"packageManager": "npm@10.8.2"` (records the exact package
  manager; honored by Corepack when enabled).
- This `ENVIRONMENT_BASELINE.md` (exact Node/npm documentation and procedure).

No source, test, paper, or historical v0/v1 artifact was modified for this
baseline. The only functional file changes are `package.json` (added
`packageManager`), `package-lock.json` (regenerated, see §5), and the new
`.nvmrc`.

## 4. Root cause of the pre-existing `npm ci` failure

On the approved foundation (`9791ee18dc7ccfcaa22236762e9b46d17c101570`),
`npm run ci` passed (because a working `node_modules/` was already present) but
`npm ci` failed with `EUSAGE` — the lockfile was out of sync with the resolved
dependency graph:

```
`npm ci` can only install packages when your package.json and package-lock.json
... are in sync.
Invalid: lock file's js-yaml@3.14.2 does not satisfy js-yaml@4.1.0
Missing: js-yaml@3.15.0 from lock file
Invalid: lock file's argparse@1.0.10 does not satisfy argparse@2.0.1
Missing: argparse@1.0.10 from lock file
```

This is a lockfile-integrity issue, **not** a Node-version issue: the recorded
`js-yaml`/`argparse` placements did not match what the dependency tree resolves
to. npm's own guidance is to run `npm install` to update the lock.

## 5. Deterministic lockfile regeneration

Regenerated with the pinned toolchain (Node 20.20.2 / npm 10.8.2) using the
minimal, npm-recommended reconciliation — `npm install` (the existing lockfile
was **not** deleted, and no historical rerun-branch lockfile was copied):

```
nvm use 20.20.2
npm install          # reconciles package-lock.json in place
```

The complete lockfile diff is a **dedup/hoist reconciliation with no
direct-dependency version changes**:

- `js-yaml@4.1.0` + `argparse@2.0.1` hoisted to the top level (the common case),
  replacing the stale top-level `js-yaml@3.14.2` / `argparse@1.0.10`.
- The `js-yaml@3.x` line (which requires `argparse@1.x`) was pushed down into the
  only two packages that need it — `@istanbuljs/load-nyc-config` and
  `@yarnpkg/parsers` — bumping `js-yaml` `3.14.2` → `3.15.0` within its `^3`
  range (the single "added 1 package").
- Redundant nested `argparse@2.0.1` / `js-yaml@4.1.0` copies were removed since
  they are now satisfied by the hoisted top-level versions.

Diff size: 57 insertions / 53 deletions in `package-lock.json`. No `package.json`
dependency range changed; `express`, `uuid`, all `@nx/*@17.2.8`, `typescript`,
`jest`, `eslint`, etc. are unchanged.

## 6. Validation from a clean dependency state

```
rm -rf node_modules
npm ci          # PASS (exit 0), 692 packages
npm run ci      # PASS (exit 0): lint + typecheck + test
```

Test result: `nx run-many --target=test --all` — 6 projects, all green
(20 domain/validation tests + 9 API integration tests). Lint and `tsc --noEmit`
typecheck also pass.

`npm ci` / `npm audit` report 41 known advisories (2 low, 16 moderate, 22 high,
1 critical) in the transitive tree (driven largely by `@nx/*@17.2.8`-era
dependencies). These are **left unchanged**: `npm audit fix` would alter
dependency versions and is out of scope for establishing a reproducible base.
They are recorded here for transparency and should be evaluated separately
before freezing the final benchmark configuration.

## 7. Recommendations (not applied — out of scope for this baseline)

These are suggestions for a later change, deliberately not made here to keep the
dependency-base commit surgical:

1. Pin CI to the exact patch by switching `ci.yml` to
   `node-version-file: .nvmrc` (or `node-version: 20.20.2`) so CI and local can
   no longer drift by patch level.
2. Add an `engines` field (`node: ">=20 <21"`, `npm: ">=10 <11"`) as an advisory
   guard.
3. Triage the 41 advisories in §6 before the final benchmark configuration is
   frozen.

## 8. Exact reproduction procedure

```
git checkout study-v2
nvm install 20.20.2 && nvm use 20.20.2   # or any manager honoring .nvmrc
node --version   # v20.20.2
npm --version    # 10.8.2
rm -rf node_modules
npm ci
npm run ci
```
