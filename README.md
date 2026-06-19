# AI Interviewer Platform

An implementation of the **AI Interviewer Platform** take-home brief — see
[`docs/home_test_requirements.md`](docs/home_test_requirements.md) for the full prompt.

A candidate picks a role and completes a voice-driven interview that asks role-grounded
questions and follow-ups based on what they say, then receives a full transcript and a
structured evaluation (strengths, concerns, overall score).

The work is planned with **[OpenSpec](https://github.com/Fission-AI/OpenSpec)**: a small
set of change proposals in [`openspec/`](openspec/), each mapped to the brief's
requirements. See [AGENTS.md](AGENTS.md) for how the project is built.

## Requirement coverage

| Brief requirement | Covered by OpenSpec change |
| --- | --- |
| At least 3 sample jobs (title + description) | `implement-backend`, `implement-frontend` › job-selection |
| Click a job → Interview Room | `implement-frontend` › interview-room |
| Voice input + see the AI's questions | `implement-frontend` › interview-room |
| At least 6 questions, including 2 answer-dependent follow-ups | `implement-backend` › interview-engine |
| Role-grounded questions | `implement-backend` › interview-engine |
| Save the session + show transcript + structured evaluation | `implement-backend` › evaluation, session-history · `implement-frontend` › session-review |
| Clean, low-friction UI | `implement-frontend` |
| Works end-to-end in a hosted environment + public website | `prepare-deployment` |
| Stretch 1 — deterministic decision panel | `implement-backend` + `implement-frontend` › decision-panel |
| Stretch 2 — job-specific question packs | `implement-backend` › interview-engine (+ persistence) |
| Stretch 3 — video mode | Deferred (out of scope) |
| Stretch 4 — replay + analytics | `implement-backend` › session-history · `implement-frontend` › session-review |
| _Shared API contract_ | `implement-backend` emits it · `define-api-contract` stabilizes it + frontend codegen |

## Methodology: backend-first sequencing

The work runs as an ordered sequence of OpenSpec changes:

```
implement-backend     builds the API and commits shared/contract.yaml with a drift check
        │
        ▼
define-api-contract   stabilizes that contract, generates frontend types, wires drift checks
        │
        ▼
implement-frontend    built against the generated contract types
        │
        ▼
prepare-deployment    public, hosted, end-to-end against the real backend
```

The backend produces the first working API and emits the OpenAPI contract; `define-api-contract`
then stabilizes it (naming, invariants, versioning), adds `openapi-typescript` codegen, and wires
the drift checks that keep the frontend and backend in sync. A thin vertical slice is built first
and deployed early, then extended with depth and the stretch goals.

## Repository structure

```txt
docs/home_test_requirements.md   the supplied brief (source of truth)
openspec/                        change proposals + specs, one folder per unit of work
shared/contract.yaml             produced by `implement-backend`, stabilized by `define-api-contract`
backend/                         FastAPI app (Python 3.12, SQLAlchemy, Alembic)  (implement-backend)
frontend/                        Next.js 16 / React 19 / TypeScript app          (implement-frontend)
justfile                         root task runner
```

## Local development

```sh
just bootstrap-check    # day-zero gate: passes on the scaffold today
```

As each track lands, the full gates and app commands become runnable:

```sh
pnpm install            # frontend deps
just frontend-dev       # Next.js dev server (needs a running backend)
just backend-dev        # FastAPI (needs PostgreSQL + OPENROUTER_* in backend/.env)
just backend-db-setup   # migrate + idempotent seed
```

Each app owns its own env example: copy [`frontend/.env.example`](frontend/.env.example)
to `frontend/.env.local` and [`backend/.env.example`](backend/.env.example) to
`backend/.env`. The frontend requires a live backend (`NEXT_PUBLIC_API_URL`).

## Commands

| Command | What it does |
| --- | --- |
| `just bootstrap-check` | Day-zero gate — OpenSpec validation, secret scan, docs sanity. Passes today. |
| `just quality` | Full project gate (frontend + contract + backend). Green once the tracks land. |
| `just preflight` | Full ship gate — quality + build + coverage + contract + db. |
| `just frontend-dev` / `just backend-dev` | Run the apps locally. |

`just quality` and `just preflight` are the real, full-project gates; they intentionally
exercise everything and turn green as the corresponding tracks are implemented.

## Scope

All six core requirements plus stretch goals 1 (deterministic decision panel),
2 (job-specific question packs), and 4 (replay + analytics). A public hosted deployment
is required (`prepare-deployment`). Stretch goal 3 (video mode) is deferred.
