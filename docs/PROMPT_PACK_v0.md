# Prompt Pack v0

This document contains the two prompt templates used for AFCI benchmark experiments.

**Authoritative Architecture Source:** `docs/MAD_v0.md`

> **Important:** The AFCI prompt uses a `{{MAD}}` placeholder. When running experiments, replace this placeholder with the full contents of `docs/MAD_v0.md`. This ensures the MAD remains the single source of truth and avoids drift between documents.

---

## Baseline Prompt

Use this prompt for the control condition (no architecture context injection).

```markdown
# Task

You are working on a TypeScript monorepo using Nx, Express, and Jest. The codebase has multiple libraries and an API application.

## Your Task

{{TASK}}

## Constraints

- Write clean, well-typed TypeScript code
- Ensure your changes pass linting and type checking
- Write tests for new functionality
- Follow existing code patterns

## Output

Provide the complete code changes needed to implement this task.
```

---

## AFCI Prompt (Architecture-First Context Injection)

Use this prompt for the experimental condition. The Master Architecture Document (MAD) is injected as **primary context** before the task.

```markdown
# Architecture-First Context

You are working on the `afci-bench` repository.

**CRITICAL:** The following Master Architecture Document (MAD) is your PRIMARY context. You MUST read, understand, and comply with it before proceeding. The MAD takes precedence over any assumptions.

---

{{MAD}}

---

# Task (Secondary Context)

The above MAD defines the architecture you must follow. Now complete the following task while maintaining strict compliance:

{{TASK}}

## Compliance Checklist

Before writing any code, verify your implementation plan against the MAD:

- [ ] DTOs placed in the correct library per MAD
- [ ] Dependency direction respected (see MAD dependency table)
- [ ] Observability library used for logging
- [ ] correlationId included in responses
- [ ] Tests provided for new functionality
- [ ] No `any` type usage

## Output

Provide the complete code changes needed to implement this task. For each file, indicate:
- File path
- Whether it's a new file or modification
- The complete content or diff

Explain how your implementation complies with the MAD.
```

---

## Placeholder Reference

| Placeholder | Description | Source |
|-------------|-------------|--------|
| `{{MAD}}` | Full Master Architecture Document | `docs/MAD_v0.md` |
| `{{TASK}}` | Specific task description | Experiment-defined |

---

## Example Task Insertions

### Task 1: Add a new endpoint

```
Add a GET /orders/:id endpoint that retrieves an order by its ID.

Requirements:
- Return 404 if order not found
- Include correlationId in response header
- Log the request with required fields
- Add integration tests
```

### Task 2: Add a new domain feature

```
Add discount calculation to orders.

Requirements:
- Support percentage-based discounts (0-100%)
- Apply discount to order total
- Validate discount is within valid range
- Add unit tests for pure calculation functions
- Update OrderResponse to include discountAmount field
```

### Task 3: Refactor existing code

```
Refactor the order creation flow to support multiple payment methods.

Requirements:
- Payment method should be in the request DTO
- Supported methods: 'credit_card', 'paypal', 'bank_transfer'
- Validation in core layer
- No changes to infra layer in this phase
```

---

## Evaluation Criteria

When evaluating LLM outputs, check:

| Criterion | P0 (Blocking) | P1 (Feedback) |
|-----------|---------------|---------------|
| Boundary violations | ✓ | |
| Type errors | ✓ | |
| Test failures | ✓ | |
| Missing correlationId | | ✓ |
| Missing log fields | | ✓ |
| Code style issues | | ✓ |

Count violations in each category. P0 violations indicate failure to comply with architecture.

---

## Usage Instructions

1. **Baseline experiments:** Use the Baseline Prompt with `{{TASK}}` replaced.
2. **AFCI experiments:**
   - Read `docs/MAD_v0.md`
   - Replace `{{MAD}}` with the full MAD content
   - Replace `{{TASK}}` with the task description
3. **Evaluation:** Run `npm run ci` on generated code; count P0/P1 violations per `docs/ARCH_RULES.yml`.
