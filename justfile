# AI Interviewer Platform — root command runner.
# `just bootstrap-check` is the day-zero gate (passes on the scaffold today).
# `just quality` / `just preflight` are the full project gates; they turn green
# as the backend/ and frontend/ tracks are implemented.

# Day-zero gate: validates only what exists on the scaffold today.
bootstrap-check:
    @echo "→ OpenSpec validation"
    openspec validate --all
    @echo "→ Secret scan"
    gitleaks detect --source . --no-banner
    @echo "→ Docs sanity"
    test -f docs/home_test_requirements.md
    test -f frontend/.env.example
    test -f backend/.env.example
    @echo "✓ bootstrap-check passed"

frontend-dev:
    pnpm --dir frontend dev

frontend-quality:
    pnpm --dir frontend quality

frontend-preflight:
    pnpm --dir frontend preflight

frontend-lint-fix:
    pnpm --dir frontend lint:fix

frontend-format:
    pnpm --dir frontend format

frontend-contract-types:
    pnpm --dir frontend contract-types

frontend-contract-types-check:
    pnpm --dir frontend contract-types:check

backend-dev:
    cd backend && uv run uvicorn app.main:app --reload

backend-format:
    cd backend && uv run ruff format . && uv run ruff check --fix .

backend-lint:
    cd backend && uv run ruff format --check . && uv run ruff check .

backend-typecheck:
    cd backend && uv run pyright

backend-test:
    cd backend && uv run pytest -m "not db" --tb=short -q

backend-coverage:
    cd backend && uv run pytest -m "not db" --cov=app --cov-branch --cov-report=term-missing

backend-deps:
    cd backend && uv run deptry .

backend-security:
    cd backend && uv run pip-audit
    gitleaks detect --source . --verbose

backend-app-smoke:
    cd backend && uv run python -c "from app.main import app; assert app.title == 'AI Interviewer Platform API'"

backend-openapi-smoke:
    cd backend && uv run python -c "from app.main import app; schema = app.openapi(); assert schema['openapi'] == '3.1.0'; assert '/health' in schema['paths']"

backend-contract-drift:
    cd backend && uv run python scripts/check_contract.py

backend-db-lint:
    cd backend && uv run sqlfluff lint docs/schema.sql alembic/versions/0001_initial_schema.sql seed_data.sql --dialect postgres --nofail --format none
    cd backend && uv run sqlfluff parse docs/schema.sql --dialect postgres --format none
    cd backend && uv run sqlfluff parse alembic/versions/0001_initial_schema.sql --dialect postgres --format none
    cd backend && uv run sqlfluff parse seed_data.sql --dialect postgres --format none

backend-db-smoke:
    cd backend && uv run alembic heads
    cd backend && uv run alembic upgrade head --sql > /tmp/ai-interviewer-migration.sql

backend-seed:
    cd backend && uv run python scripts/seed.py

backend-pipeline-smoke:
    cd backend && uv run python scripts/pipeline_smoke.py

backend-db-setup:
    cd backend && uv run alembic upgrade head
    cd backend && uv run python scripts/seed.py

backend-db-seed-check:
    cd backend && uv run pytest tests/test_db_seed.py -m db

# Full DB-gated suite via Testcontainers (requires a running Docker daemon).
backend-test-db:
    cd backend && DOCKER_HOST="$(test -S "$HOME/.docker/run/docker.sock" && echo "unix://$HOME/.docker/run/docker.sock" || echo "$DOCKER_HOST")" uv run pytest -m db --tb=short -q

backend-quality: backend-lint backend-typecheck backend-test backend-deps backend-app-smoke backend-openapi-smoke

backend-preflight: backend-quality backend-coverage contract-check backend-contract-drift backend-security backend-db-lint backend-db-smoke

backend-dead-code:
    cd backend && uv run vulture app tests scripts --min-confidence 100

backend-complexity:
    cd backend && uv run radon cc app -a -s --min C
    cd backend && uv run xenon --max-absolute B --max-modules B --max-average A app

backend-mutation:
    cd backend && uv run mutmut run

backend-contract-fuzz:
    @echo "Manual gate: start backend first, then run schemathesis against http://127.0.0.1:8000/openapi.json"
    cd backend && uv run schemathesis run http://127.0.0.1:8000/openapi.json --checks all

backend-risk: backend-coverage backend-complexity

contract-check:
    pnpm --package=@redocly/cli dlx redocly lint --config .redocly.yaml shared/contract.yaml

# OpenSpec: validate all active change proposals/specs.
spec-validate:
    openspec list

quality: frontend-quality contract-check backend-quality

preflight: frontend-preflight contract-check backend-preflight

secrets:
    gitleaks detect --source . --verbose
