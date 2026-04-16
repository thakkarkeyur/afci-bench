# TASK_TEMPLATE (v0)

## Task ID
TXX_<short_name>

## Title
One-line title.

## Motivation (Why this task exists)
- What architectural drift / failure mode does this task stress?
- Why is it representative of industrial work?

## Scope
- In scope:
- Out of scope:

## Acceptance Criteria (must be objectively checkable)
- [ ] CI passes (`npm run ci`)
- [ ] Tests added/updated (state what kind and where)
- [ ] Public API/DTO changes (if any) are in `libs/contracts`
- [ ] Ports/interfaces rules followed (if applicable)
- [ ] Observability fields present (if applicable)

## Architectural Constraints (MAD hooks)
List the *specific* MAD rules that matter for this task (copy the exact bullets).
- Rule 1:
- Rule 2:
- Rule 3:

## Baseline Prompt (task-only)
Paste the baseline prompt text or reference it:
- Use `docs/PROMPT_PACK_v0.md` → Baseline template

## AFCI Prompt (MAD-first)
Paste the AFCI prompt text or reference it:
- Use `docs/PROMPT_PACK_v0.md` → AFCI template
- Must include `{{MAD}}` or the full MAD as primary context

## Reset Protocol
- baseline_reset: fresh session + baseline prompt
- afci_reset: fresh session + AFCI prompt

## Artifacts to Save (per run)
For each run folder `experiments/runs/<TASK>/<condition>/`:
- prompt.md
- patch.diff
- ci_output.txt
- metrics.json
- (optional) conformance.json

## Notes / Edge Cases
Anything that could trip determinism or interpretation.