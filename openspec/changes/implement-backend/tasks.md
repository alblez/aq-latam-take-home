## 1. Skeleton + persistence (data layer first)

- [ ] 1.1 FastAPI app skeleton with settings/env loading and structured logging; project metadata `ai-interviewer-backend`; backend tooling (ruff, pyright, pytest)
- [ ] 1.2 `GET /health` endpoint
- [ ] 1.3 Define the minimal schema — jobs, competencies, question-pack items, sessions, turns, evaluations + competency scores, and decision-panel snapshots — in `backend/docs/schema.sql`
- [ ] 1.4 Implement the SQLAlchemy models in `backend/app/models.py`
- [ ] 1.5 Create the Alembic migration `backend/alembic/versions/0001_initial_schema.py` matching the schema
- [ ] 1.6 Author idempotent seed data (at least 3 roles, each with behavioral + technical question packs) in `backend/seed_data.sql` and a `backend/scripts/seed.py` runner
- [ ] 1.7 Verify `alembic upgrade head` then seed run clean against local PostgreSQL (`just backend-db-setup`)

## 2. Thin vertical slice (one role, end to end)

- [ ] 2.1 `GET /api/jobs` returns the seeded roles
- [ ] 2.2 `POST /api/sessions` + `POST /api/sessions/{id}/start`: create a session and return the first pack-seeded question with panel state
- [ ] 2.3 `POST /api/sessions/{id}/turn`: persist the answer and return the next question
- [ ] 2.4 `GET /api/sessions/{id}/evaluation`: a minimal structured evaluation for a completed session
- [ ] 2.5 Enforce `X-Owner-Id` scoping on all `/api` routes

## 3. Emit the API contract

- [ ] 3.1 Export `shared/contract.yaml` from the FastAPI runtime OpenAPI
- [ ] 3.2 Add a backend check that the runtime OpenAPI matches the committed `shared/contract.yaml`
- [ ] 3.3 Backend quality gate green: ruff, pyright, unit tests, and ASGI integration tests

## 4. Deterministic interview engine

- [ ] 4.1 Policy: enforce min 6 questions, min 2 answer-dependent follow-ups, the caps, and `eligibleToEnd`
- [ ] 4.2 Generation modes: `pack_seed`, `targeted_follow_up` (depends on prior answer), `generic_probe` fallback
- [ ] 4.3 `end-early` and resume/recovery (`needsRecovery`)

## 5. Decision panel (stretch 1)

- [ ] 5.1 Per-turn rubric snapshot (covered / in-progress / gaps)
- [ ] 5.2 Signal flags derived from answers
- [ ] 5.3 Rationale + trigger for the chosen next question; persist the snapshot on the turn

## 6. Structured evaluation

- [ ] 6.1 Overall score + per-competency scores with evidence (quotes, supporting turns)
- [ ] 6.2 Narrative verdict + strengths + concerns grounded in turn ids
- [ ] 6.3 Graceful degradation: `insufficient_signal` / `model_unavailable`, never fabricate

## 7. History + analytics (stretch 4)

- [ ] 7.1 `GET /api/history` (owner-scoped) with duration, talk ratio, coverage, score, and counts
- [ ] 7.2 Optional `jobId` filter
- [ ] 7.3 `GET /api/sessions/{id}/replay` detail

## 8. Quality

- [ ] 8.1 Unit + ASGI integration tests; `ruff` and `pyright` clean
- [ ] 8.2 Runtime OpenAPI drift check against `shared/contract.yaml` green
