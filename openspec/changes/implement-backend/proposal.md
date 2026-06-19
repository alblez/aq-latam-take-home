## Why

The backend produces the first working API: it serves roles, drives an adaptive question flow that adapts to the candidate's answers, persists each session, and produces a structured evaluation. It is the first change applied and also **emits** `shared/contract.yaml` from FastAPI's runtime OpenAPI, which later changes stabilize and consume.

## What Changes

- A FastAPI skeleton with settings/env loading, structured logging, a `/health` endpoint, project metadata (`ai-interviewer-backend`), and backend tooling.
- A persistence model with migrations and idempotent seed for jobs, role question packs, sessions, turns, evaluations, and decision-panel snapshots.
- A thin vertical slice — `GET /api/jobs`, `POST /api/sessions`, `POST /api/sessions/{id}/start`, `POST /api/sessions/{id}/turn`, `GET /api/sessions/{id}/evaluation`, with `X-Owner-Id` scoping.
- An initial `shared/contract.yaml` produced from the FastAPI runtime OpenAPI, plus a backend check that the runtime OpenAPI matches the committed contract.
- The full interview engine (deterministic depth policy, role-grounded generation), the decision panel, structured evaluation, and owner-scoped history with analytics.

## Capabilities

### New Capabilities
- `interview-engine`: session lifecycle, the deterministic depth policy (at least 6 questions and at least 2 answer-dependent follow-ups, with caps), role-grounded question generation, end-early, and resume/recovery.
- `decision-panel`: the deterministic interviewer state exposed each turn — rubric snapshot, detected signals, policy state, chosen action, and the rationale for the next question (stretch goal 1).
- `evaluation`: the structured end-of-interview evaluation — overall score, per-competency scores with evidence, and a narrative verdict with strengths and concerns.
- `session-history`: owner-scoped persistence, the history list with per-session analytics metrics, job filtering, and replay detail (stretch goal 4).

## Requirements Coverage

- **Core**: sample jobs; the Interview Room turn flow; at least 6 questions including at least 2 answer-dependent follow-ups; role-grounded questions; saving the session and producing the transcript plus a structured evaluation (strengths, concerns, overall score).
- **Stretch 1**: deterministic decision panel. **Stretch 2**: job-specific question packs (behavioral + technical). **Stretch 4**: replay and analytics (server side).

## Impact

- Adds `backend/` (FastAPI app, SQLAlchemy models, Alembic migrations, seed data, tests) and its quality gates.
- Adds `shared/contract.yaml`, produced from the backend's runtime OpenAPI.
- Runtime dependencies: PostgreSQL (`DATABASE_URL`) and an OpenRouter LLM (`OPENROUTER_API_KEY`, `OPENROUTER_LLM_MODEL`).
- **First change applied — no dependency on other changes.** Its emitted contract is consumed by `define-api-contract` and, in turn, `implement-frontend`.
