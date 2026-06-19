## Why

The brief's job description mentions infrastructure, and a CI pipeline demonstrates engineering rigor: it enforces the project's quality gates on every push and pull request, catching regressions before they land. This change adds a GitHub Actions workflow that runs the existing frontend, contract, and backend quality gates in parallel, plus a database migration validation job and an aggregate status check for branch protection.

## What Changes

- A GitHub Actions workflow at `.github/workflows/ci.yml` with five jobs:
  - `frontend-quality` — tsc, Biome, knip, Vitest
  - `contract-check` — redocly lint of `shared/contract.yaml`
  - `backend-quality` — ruff, pyright, pytest, deptry, contract drift, security scan, coverage
  - `backend-db` — PostgreSQL service container, sqlfluff, alembic migration, seed validation
  - `preflight` — aggregate gate (needs all four above) for branch protection
- Triggers on push to `master` and on pull requests.
- No CD — this is pure CI. Deployments are handled by Railway and Vercel via their own integrations.

## Capabilities

### New Capabilities
- `ci-pipeline`: a GitHub Actions CI workflow that runs the project's quality gates in parallel on every push and pull request, with an aggregate status check for branch protection.

## Requirements Coverage

- **Core**: "Must work end-to-end in a hosted environment" — CI ensures the quality gates stay green as the codebase evolves.
- **Infrastructure**: demonstrates CI/CD awareness expected by the job description.

## Impact

- Adds `.github/workflows/ci.yml` (one file, ~120 lines).
- No runtime dependencies. No secrets required — the workflow is self-contained.
- Depends on the existing justfile targets (`just backend-quality`, `just frontend-quality`, `just contract-check`, etc.) which are already implemented and passing.
