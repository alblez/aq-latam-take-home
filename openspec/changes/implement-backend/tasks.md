## 1. Project scaffold and persistence

- [x] 1.1 Backend project metadata and tooling: `pyproject.toml` (uv-managed, `ai-interviewer-backend`), ruff, pyright, pytest, coverage, deptry config
- [x] 1.2 FastAPI app skeleton: settings/env loading (`app/config.py`), SQLAlchemy engine (`app/db.py`), dependencies (`app/deps.py`), structured logging (`app/logging.py`), error envelope (`app/errors.py`), owner parsing (`app/owners.py`), app factory + middleware + exception handlers (`app/main.py`)
- [x] 1.3 `GET /health` endpoint (`app/routes/health.py`)
- [x] 1.4 Database schema DDL in `backend/docs/schema.sql` (jobs, competencies, question_pack_items, sessions, turns, evaluations, session_competency_scores + enums + indexes)
- [x] 1.5 SQLAlchemy models in `backend/app/models.py` matching the schema
- [x] 1.6 Alembic migration `backend/alembic/versions/0001_initial_schema.py` + companion SQL, `alembic.ini`, `alembic/env.py`
- [x] 1.7 Idempotent seed data (`backend/seed_data.sql`) and runner (`backend/scripts/seed.py`)
- [x] 1.8 Verify `just backend-db-setup` (alembic upgrade head + seed) runs clean

## 2. API schemas and data access

- [x] 2.1 Pydantic API request/response schemas (`app/schemas.py`)
- [x] 2.2 Strict Pydantic models for JSONB columns (`app/jsonb_schemas.py`): TurnReasoning, TerminalPanelState, EvaluationNarrative, CompetencyEvidence, ControllerConfig
- [x] 2.3 Database repositories and query helpers (`app/repositories.py`): CRUD, owner guards, row locks
- [x] 2.4 Session lifecycle helpers: turn flow orchestration (`app/turn_flow.py`), panel state builders (`app/panel_state.py`), evaluation detail assembly (`app/evaluation_detail.py`), history detail assembly (`app/history_detail.py`)

## 3. Deterministic interview engine

- [x] 3.1 Engine package scaffold and OpenRouter gateway (`app/engine/gateway.py`): ModelGateway protocol, OpenRouterGateway, retry logic
- [x] 3.2 Prompt builders (`app/engine/prompts.py`): analyze, generate, evaluation, repair prompts
- [x] 3.3 Answer analysis and signal extraction (`app/engine/analyze.py`)
- [x] 3.4 Deterministic depth policy (`app/engine/policy.py`): pure function, min 6 questions, min 2 follow-ups, caps, eligibleToEnd, follow-up guard
- [x] 3.5 Question generation with tiered fallback (`app/engine/generate.py`): pack_seed, targeted_follow_up, generic_probe
- [x] 3.6 Structured evaluation (`app/engine/evaluation.py`): schema, parsing, competency alignment, deterministic scoring
- [x] 3.7 Pipeline orchestrator (`app/engine/orchestrator.py`): analyze → policy → generate → persist; evaluation runner; end-early terminal builder
- [x] 3.8 Rationale templates and failure-mode vocabulary (`app/engine/rationales.py`)

## 4. API routes

- [ ] 4.1 `GET /api/jobs` (`app/routes/jobs.py`)
- [ ] 4.2 Session routes (`app/routes/sessions.py`): create, get state, start, turn, end-early, evaluation, replay
- [ ] 4.3 `GET /api/history` with optional `jobId` filter (`app/routes/history.py`)
- [ ] 4.4 Wire all routes into `app/main.py` with `X-Owner-Id` scoping on all `/api` endpoints
- [ ] 4.5 Verify `just backend-quality` (ruff, pyright, pytest not db, deptry, app/openapi smoke) is green

## 5. API contract and drift check

- [ ] 5.1 Commit `shared/contract.yaml` (OpenAPI 3.1.0) covering all endpoints and schemas
- [ ] 5.2 Add drift check (`backend/scripts/check_contract.py`) that asserts runtime OpenAPI matches the committed contract
- [ ] 5.3 Verify `just contract-check` (redocly lint) and `just backend-contract-drift` are green

## 6. Test suite

- [ ] 6.1 Unit tests: policy, generate, analyze, evaluation, owners, errors, health
- [ ] 6.2 ASGI integration tests: jobs, session lifecycle, turn flow, end-early, evaluation, replay, history
- [ ] 6.3 DB-gated tests (Testcontainers): seed validation, migration, repositories
- [ ] 6.4 Contract drift test
- [ ] 6.5 Verify `just backend-test` (not db) and `just backend-test-db` are green

## 7. Final quality gate

- [ ] 7.1 `just backend-quality` green (ruff, pyright, pytest not db, deptry, smoke)
- [ ] 7.2 `just contract-check` and `just backend-contract-drift` green
- [ ] 7.3 `just backend-db-lint` and `just backend-db-smoke` green (sqlfluff, alembic)
- [ ] 7.4 `just backend-coverage` meets threshold
- [ ] 7.5 Forbidden-words scan clean (only false positives)
- [ ] 7.6 `openspec validate --all` passes
- [ ] 7.7 `just bootstrap-check` passes
