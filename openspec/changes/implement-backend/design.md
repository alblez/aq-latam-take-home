## Context

The backend is implemented first. It runs the interview — a deterministic engine that selects role-grounded questions, adapts to answers, persists every turn, and produces a structured evaluation — and it emits the API contract from FastAPI's runtime OpenAPI rather than working against a contract authored up front. Persistence is built first because every capability reads or writes it; the data model below is delivered as runnable artifacts in `tasks.md` §1, not as prose.

## Goals / Non-Goals

**Goals:**
- A minimal persistence model covering jobs, question packs, sessions, turns, evaluations, and decision-panel snapshots.
- A deterministic depth policy that guarantees the brief's question/follow-up minimums independent of the language model.
- A committed `shared/contract.yaml` produced from the running app, with a drift check so code and contract stay in lockstep.
- Replayable interviews: each interviewer turn stores the panel state that produced it.

**Non-Goals:**
- Authentication (owner-scoping only). Background jobs / evaluation retry. Streaming responses.

## Decisions

### Committed contract with drift check
- The API contract (`shared/contract.yaml`, OpenAPI 3.1.0) is committed to the repository and covers all endpoints and schemas. A drift check (`scripts/check_contract.py`) asserts the FastAPI runtime OpenAPI matches the committed contract, so code and contract never diverge. Stabilizing names and optionality for the frontend is handled by the `define-api-contract` change that consumes this file.

### Persistence model (minimal)
- `jobs` — id, title, description.
- `competencies` — id, job_id, name, category (`behavioral` | `technical`). The role's rubric.
- `question_pack_items` — id, competency_id, prompt, ordering. Seeded question packs per competency (stretch 2).
- `sessions` — id, owner_id, job_id, status (`in_progress` | `completed` | `ended_early`), completion_reason, started_at, completed_at.
- `turns` — id, session_id, turn_index, role (`interviewer` | `candidate`), competency_id, content, input_mode, audio_duration_ms, action, source_pack_item_id, client_turn_id, and `reasoning` JSONB holding the **decision-panel snapshot** for interviewer turns.
- `evaluations` — id, session_id, overall_score, narrative JSONB; `session_competency_scores` — competency_id, score, evidence JSONB (quotes, supporting turn ids, signals).

### Engine architecture
- **orchestrator** drives the turn flow; **policy** owns the deterministic counts and `eligibleToEnd`; **generation** produces questions in modes `pack_seed`, `targeted_follow_up`, `generic_probe`; **analyze** derives signal flags from answers; **evaluation** produces the terminal scoring.
- The **deterministic policy is independent of the LLM**: it enforces at least 6 questions and at least 2 answer-dependent follow-ups regardless of model output, satisfying the brief's hard requirement.
- The **panel snapshot is persisted on each interviewer turn** (`turns.reasoning`) so replay reconstructs the interviewer's reasoning exactly.
- **Evaluation degrades gracefully**: insufficient signal or an unavailable model yields an `insufficient_signal` verdict / `model_unavailable` error and unassessed competencies — never a fabricated score.

## Risks / Trade-offs

- **Auto-generated contract naming may need stabilizing** → the `define-api-contract` change reviews and stabilizes the emitted contract before the frontend builds against it.
- **LLM latency / availability** → the deterministic policy and graceful evaluation degradation keep the flow correct when the model is slow or down.
- **DB-gated tests need Docker** → kept under a separate marker so the fast gate does not require a database.
