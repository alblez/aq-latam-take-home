## ADDED Requirements

### Requirement: CI pipeline runs quality gates on every push and pull request
The system SHALL run a GitHub Actions workflow on push to `master` and on pull requests that executes the project's quality gates: frontend quality (tsc, Biome, knip, Vitest), contract checks (redocly lint, drift detection), backend quality (ruff, pyright, pytest, deptry, security, coverage), and database migration validation (sqlfluff, alembic upgrade, seed).

#### Scenario: Push to master triggers CI
- **WHEN** a commit is pushed to `master`
- **THEN** the CI workflow runs all quality gates

#### Scenario: Pull request triggers CI
- **WHEN** a pull request is opened or updated
- **THEN** the CI workflow runs all quality gates

### Requirement: Parallel jobs with aggregate status check
The CI workflow SHALL run quality gates as parallel jobs (frontend-quality, contract-check, backend-quality, backend-db) and provide a single aggregate `preflight` job that depends on all of them, so branch protection can require one status check instead of four.

#### Scenario: All gates pass
- **WHEN** all four quality jobs pass
- **THEN** the `preflight` aggregate job passes

#### Scenario: Any gate fails
- **WHEN** any quality job fails
- **THEN** the `preflight` aggregate job fails and blocks the pull request

### Requirement: Database migration validation in CI
The CI workflow SHALL validate database migrations and seed data against a real PostgreSQL service container, running sqlfluff lint, `alembic upgrade head`, and the seed script.

#### Scenario: Migrations run clean in CI
- **WHEN** the backend-db job runs
- **THEN** sqlfluff lint passes, alembic upgrade head succeeds, and the seed script completes against the PostgreSQL service container
