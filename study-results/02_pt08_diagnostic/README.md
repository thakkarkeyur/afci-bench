# 02 — PT08 C1 difficulty diagnostic

**3 runs · task PT08 · condition C1 only · `claude-sonnet-5` · CLI 2.1.229 ·
executed 2026-09-13, 06:28–06:35 UTC**

> **Classification: DIAGNOSTIC ONLY.** Must not enter confirmatory analysis,
> treatment-effect estimation or power estimation. Every artifact carries
> `is_result: false`, `scored: false` and all five eligibility flags false.

## Files here

| file | what it is |
| --- | --- |
| `pt08_diagnostic_runs.csv` | **derived** — per-run functional and architecture outcome |

Raw evidence stays at `D:\pt08-diagnostic` (outside both repositories).

## Result

| | R1 | R2 | R3 |
| --- | --- | --- | --- |
| hidden acceptance | 15/15 | 15/15 | 15/15 |
| semantic cases passed | 14 | 14 | 14 |
| functional completion | PASS | PASS | PASS |
| applicable opportunities | 1 | 1 | 1 |
| target violations | **0** | **0** | **0** |
| violation proportion | 0.0 | 0.0 | 0.0 |
| model identity | VALIDATED | VALIDATED | VALIDATED |
| context audit | CLEAN | CLEAN | CLEAN |
| structured events / seconds | 88 / 92.7 | 83 / 88.1 | 63 / 55.3 |

**3/3 functional. 3 applicable opportunities across the set, 0 violated.**

Every repetition enforced the ceiling at the request boundary, so the use-case
scope was never entered and the decision the instrument exists to expose was never
taken.

## Interpretation

**Functional ceiling + architecture floor.** `C1` is a baseline, and a baseline at
the floor has no room beneath it, so PT08 unchanged cannot discriminate. This is a
task-design finding about one instrument — the runner, sterile execution, model
pinning, hidden acceptance, the architecture oracle and the artifact firewall all
worked end to end.

## Decision — `SL-PT08-07`

> **PT08 = REVISE. Benchmark investment = CONTINUE.**

`REVISE` is **not** `INVALID` and **not** `RETIRED`. PT08 is functionally valid;
it is unsuitable *unchanged* as a confirmatory architecture-discrimination
instrument. Its body, package, freeze record and artifacts are preserved and must
not be modified.

Two registers are kept apart: the admitted active E1 register is **unchanged** at
6 opportunities / 3 clusters / depths 3-2-1, while the confirmatory-candidate set
**excludes unchanged PT08**. Neither may be read off the other.

## Two traps for a reader of these records

1. **All three runs share one `run_id`** — `pt08-difficulty-diagnostic-pt08-c1-real-97c5ca96498e`.
   `derive_run_id` hashed only content identity, so the repetitions collided. They
   stayed separable only because each got its own `--artifact-root`. Fixed under
   `SL-RUNID-01`; these artifacts keep the ids they were written with. Distinguish
   the runs by directory (`R1`/`R2`/`R3`) and `session_id` (`85e54e73…`,
   `1f970b85…`, `b3643495…`).
2. **`worktree_content_hash` = `da7a6795…` is identical across all three** because
   it is the **prepared (input)** worktree hash, recorded before model invocation.
   It means the three runs got identical inputs. It says nothing about outputs.

## Not captured

No efficiency metrics exist in these governed records — no token, cost, tool-call
or `MODEL_WALL_SECONDS` figures. `runtime_evidence.jsonl` is preserved, but the
metrics module postdates this purpose and **nothing was derived retroactively**.
The `total_run_seconds` in the derived CSV is parsed from the free-text
`invocation.detail` and is a process wall clock, not the governed endpoint.

## Evaluator manifest provenance

Shipped private manifest `bdb4f0bb68a366ddef93f712c2325092f97387c2765dc94a78037ca6c1768f3b`
(`status=review`, **unmodified**) → derived diagnostic-scoped mount
`9fdbb347aa936ddc98d19737937b954c0a925ab1e13ace6c385dce0b8bb098dc` (`status=frozen`).
Exactly two lifecycle fields differ, **zero semantic fields** differ, and the mount
was never committed.
