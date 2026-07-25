# AFCI-Bench v2 - Public Task Authoring Report

Status: **candidate** pilot task materials - authored, NOT approved, NOT frozen. The scientific protocol remains **PRE-FREEZE**. No benchmark run, paid model call, or task-count freeze accompanies this report.

## What was authored

- Six primary pilot task candidates (PT01-PT06) and two pre-declared reserve candidates (PR01-PR02).
- Each public task body states functional requirements and observable behaviour only; the single visible validation command is `npm run ci:agent`.
- Every hidden evaluator package for these candidates is stored **only** in a separate local private evaluator repository and is absent from this public repository.

## Coverage

The six primary candidates were selected, before any model outcome existed, to collectively span the pre-declared coverage areas recorded in the private selection policy and coverage matrix. The per-candidate coverage mapping is a hidden design detail and is withheld from this public report.

## Leakage validation

The public-task leakage validator (`experiments/v2/tasks/validate_public_tasks.py`, terms in `docs/v2/TASK_LEAKAGE_TERMS.yml`) was run over every authored public task body. Result: **OK for every task** (no hard leak; no uncovered review-required term; no reviewed exceptions were needed). This advances TD-B17 for the authored draft suite; TD-B17 remains open pending independent review at freeze.

## Public task inventory

| Task | Kind | Category | Scope | Public task SHA-256 |
| --- | --- | --- | --- | --- |
| PT01 | primary | read-endpoint | small | `edadcd79a7ed4779...` |
| PT02 | primary | list-endpoint | medium | `b755f284e6148fe6...` |
| PT03 | primary | write-endpoint | medium | `194308facc16d8ef...` |
| PT04 | primary | logging | medium | `62740ec14d829d99...` |
| PT05 | primary | calculation | medium | `f6efc772e76d6c28...` |
| PT06 | primary | error-handling | medium | `1657163baad1eba6...` |
| PR01 | reserve | calculation | small | `95f885aa81068b64...` |
| PR02 | reserve | write-endpoint | medium | `d6190ac008d81e3c...` |

## What was deliberately NOT done

- No task was selected, rejected, or difficulty-tuned using any observed or expected AFCI advantage (CRITICAL_DESIGN_DECISIONS D3/D10).
- No final task count, repetition count, run count, model, or numerical budget was selected.
- No hidden evaluator package was frozen; the oracle continues to refuse to score a review-status package (`MANIFEST_NOT_FROZEN`).
- Task-specific oracle validity, hidden-acceptance validation, reset checkpoint review, and benchmark discrimination remain open (G1/G2 not passed).

