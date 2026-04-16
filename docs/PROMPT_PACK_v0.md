## Baseline Prompt (B0)
You are working in a codebase. Implement the task below.
Constraints:
- Keep changes minimal
- Ensure tests pass

TASK:
{{task}}

## AFCI Prompt (B1: Architecture-First Context Injection)
You must follow the Master Architecture Document (MAD) as the source of truth.
MAD (PRIMARY CONTEXT):
{{MAD}}

TASK (SECONDARY CONTEXT):
{{task}}

Hard rules:
- Do not violate MAD dependency rules or folder structure.
- Do not invent new contracts outside libs/contracts.
- If information is missing, propose the smallest MAD-consistent change.
Deliver:
- Patch-level changes
- Tests updated
- Short explanation of how constraints were satisfied