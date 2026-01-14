# afci-bench

Architecture-First Context Injection Benchmark - A reproducibility artifact for ICSE/FSE research.

## Overview

This repository provides a controlled environment for evaluating LLM code generation under:
1. **Baseline prompting** - minimal constraints
2. **AFCI prompting** - Master Architecture Document (MAD) injected first

## Quick Start

```bash
# Install dependencies
npm install

# Run all CI checks
npm run ci

# Run individual checks
npm run lint      # ESLint with boundary enforcement
npm run typecheck # TypeScript strict mode
npm run test      # Jest unit and integration tests

# Start the API server (development)
npm run serve
```

## Project Structure

```
afci-bench/
├── apps/
│   └── api/                 # Express HTTP API
├── libs/
│   ├── contracts/           # DTOs and API contracts
│   ├── core/                # Pure domain logic
│   ├── features/            # Use cases and orchestration
│   ├── infra/               # Repository adapters
│   └── observability/       # Structured logging
├── docs/
│   ├── MAD_v0.md           # Master Architecture Document
│   ├── ARCH_RULES.yml      # Machine-checkable rules
│   └── PROMPT_PACK_v0.md   # Evaluation prompts
└── .github/workflows/       # CI configuration
```

## Architecture Rules

See [docs/MAD_v0.md](docs/MAD_v0.md) for complete documentation.

### Dependency Direction

```
contracts  ← (nothing)
observability ← (nothing)
core       ← contracts
features   ← core, contracts, observability
infra      ← contracts, observability
apps/api   ← features, infra, contracts, observability
```

### CI Enforcement

| Check | Command | Blocking |
|-------|---------|----------|
| Lint + Boundaries | `npm run lint` | Yes |
| Type Check | `npm run typecheck` | Yes |
| Tests | `npm run test` | Yes |

## API Endpoints

- `GET /health` - Health check
- `POST /orders` - Create a new order

## Development

This is an Nx monorepo. Use Nx commands for development:

```bash
# Run specific project tests
npx nx test core
npx nx test features
npx nx test api

# Lint specific project
npx nx lint api
```

## License

MIT
