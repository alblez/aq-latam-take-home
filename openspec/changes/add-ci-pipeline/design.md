## Context

The project has comprehensive quality gates defined in the justfile (frontend, backend, contract) and enforced locally via lefthook. This change adds a GitHub Actions workflow that runs those same gates in CI on every push and pull request, so regressions are caught before they land on `master`.

## Goals / Non-Goals

**Goals:**
- Run all quality gates in CI: frontend (tsc, Biome, knip, Vitest), contract (redocly, drift checks), backend (ruff, pyright, pytest, deptry, security, coverage), and DB (sqlfluff, alembic migration, seed).
- Provide a single aggregate status check (`preflight`) for branch protection.
- Keep the workflow self-contained — no secrets, no external services beyond a PostgreSQL service container.

**Non-Goals:**
- Continuous deployment (Railway and Vercel handle deployment via their own integrations).
- Branch protection configuration (that's a GitHub repo setting, not a workflow file).
- Scheduled runs or nightly jobs.

## Decisions

- **Four parallel jobs + one aggregate gate.** Each quality domain runs independently so failures are isolated and fast. The `preflight` job depends on all four and serves as the single required status check.
- **PostgreSQL service container for the DB job.** GitHub Actions supports service containers natively — no Docker Compose needed. The job runs sqlfluff, `alembic upgrade head`, and seed validation against the container.
- **No `pytest -m db` step.** The project has 0 DB-marked tests today. The DB job validates migrations and seed instead, which is the valuable part. If DB-marked tests are added later, the step can be added back.
- **Triggers on push to `master` and pull requests.** The branch is `master` (not `main`).
- **Concurrency cancellation.** In-progress runs for the same ref are cancelled when a new push lands, saving CI minutes.

## Risks / Trade-offs

- **CI runtime** → four parallel jobs keep the wall-clock time low; total CI minutes are modest for a public repo (free tier).
- **No DB-marked tests** → the DB job validates migrations + seed instead of running Testcontainers tests. Acceptable for now; the step can be added when tests exist.
