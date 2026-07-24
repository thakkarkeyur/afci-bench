# experiments/v2/oracle/fixtures — Synthetic oracle validation fixtures

Synthetic, self-contained mini-repositories used to validate the
architecture-conformance oracle. They are **not** benchmark tasks and contain
**no** task-specific answers.

## Why `.ts.fixture`

Code files are stored with the `.ts.fixture` extension so the repository-wide
`tsc -p tsconfig.base.json` (`npm run typecheck`) never compiles them — several
fixtures are deliberately architecture-violating or intentionally malformed, and
must not break the repository's own type check or lint. At test time each case's
`snapshot/` tree is materialized into an OS temp directory, renaming
`*.ts.fixture` → `*.ts`, so the TypeScript compiler API resolves real modules;
the temp directory is removed afterwards.

## Layout

```
cases/<case>/snapshot/            # the repository snapshot to score (model worktree)
  tsconfig.json                   # the snapshot's own alias config
  libs/... apps/...               # *.ts.fixture source
coding_worktree/                  # a clean model-visible snapshot with NO evaluator artifacts
```

The frozen evaluator manifest for each case is built in the test and written to a
separate temp `evaluator/` directory **outside** the materialized snapshot, so the
mount is legal (docs/v2/EVALUATOR_MOUNT_POLICY.md).

## Cases

| Case | Proves |
|------|--------|
| `clean_alias` | allowed alias import is not flagged |
| `violating_alias` | forbidden alias import (core→infra) is detected |
| `clean_relative` | allowed relative import is not flagged |
| `violating_relative` | forbidden relative import is detected (alias bypass caught) |
| `clean_barrel` | sanctioned api→features→core re-export is not flagged (no synthetic deep edge) |
| `violating_barrel` | a forbidden dependency laundered through a barrel `export * from` is detected |
| `deceptive_negative` | import-like text in comments/strings creates no violation |
| `moved_violation` | a violating file at a moved path is still detected (full-repository eval) |
| `deleted_violation` | a frozen opportunity whose file was deleted is recorded absent, not invented |
| `malformed_alias` | a malformed snapshot tsconfig fails closed |
| `legitimate_alternative` | a diverse but allowed solution is not flagged (specificity) |

Unknown-rule, unimplemented-stub, determinism, blindness, and mount-rejection are
exercised in the tests using these snapshots with varied manifests/inputs.
