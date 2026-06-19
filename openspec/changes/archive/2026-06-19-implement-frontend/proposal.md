## Why

Candidates need a clean, voice-first interface: browse roles, run an adaptive interview by microphone, watch the interviewer's reasoning, and review a transcript plus evaluation. This change implements the Next.js frontend against the `api-contract`, starting from a thin end-to-end slice.

## What Changes

- Job selection (at least 3 roles, each with a title and description) leading into the Interview Room.
- Voice-driven answering using the Web Speech API, with a text fallback; turn-by-turn question/answer flow.
- A live decision panel that shows the interviewer's rubric, signals, and rationale (stretch goal 1).
- An end-of-interview review with the full transcript and structured evaluation; a history page with role filtering, per-session analytics, and replay (stretch goal 4).
- A typed API client driven by the generated contract types, with an auto-generated `X-Owner-Id`.
- The frontend requires a live backend (`NEXT_PUBLIC_API_URL`); hosted environments run against the deployed backend.

## Capabilities

### New Capabilities
- `job-selection`: browse at least three sample roles and enter an interview room for a chosen role.
- `interview-room`: voice-driven answering with a text fallback, turn-by-turn question/answer flow, the live decision panel, and end-early.
- `session-review`: the end-of-interview transcript and structured evaluation, plus the history page with role filtering, per-session analytics, and replay.

## Requirements Coverage

- **Core**: the jobs list; entering the Interview Room; answering by microphone and seeing the AI's questions; the saved session's transcript and structured evaluation; a clean, low-friction UI.
- **Stretch 1**: the decision panel UI. **Stretch 4**: replay and analytics UI.
- **Deferred**: stretch goal 3 (video mode) is out of scope for this implementation.

## Impact

- Adds `frontend/` (Next.js 16 / React 19 / TypeScript). Consumes the generated contract types; `contract-types:check` guards drift.
- Depends on `define-api-contract` (consumes the generated contract types). The frontend requires a live backend (`NEXT_PUBLIC_API_URL`); hosted environments use the deployed backend.
