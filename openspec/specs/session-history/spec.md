## Purpose

Provide owner-scoped session history, filtering, and replay.

## Requirements

### Requirement: Owner-scoped history with analytics metrics
The system SHALL return a list of the requesting owner's terminal sessions, each summarized with analytics metrics: duration, talk ratio, coverage percent, overall score, and question / follow-up counts. History MUST be scoped to the `X-Owner-Id` owner and MUST NOT expose other owners' sessions.

#### Scenario: History returns owner-scoped summaries with metrics
- **WHEN** an owner requests `/api/history`
- **THEN** the response lists that owner's sessions, each with `durationMs`, `talkRatio`, `coveragePercent`, `overallScore`, `questionCount`, and `followUpCount`

### Requirement: Filter history by job
The history endpoint SHALL accept an optional `jobId` query parameter and, when present, return only sessions for that job. A malformed `jobId` MUST return `422` with `error.code = validation_error`.

#### Scenario: Filtering by job narrows results
- **WHEN** an owner requests `/api/history?jobId=<uuid>`
- **THEN** only that owner's sessions for the given job are returned

### Requirement: Replay detail for completed sessions
For a terminal session, the system SHALL return replay detail containing the job, competencies, the full ordered transcript with per-turn panel state, the terminal panel state, and the evaluation. Replay of an in-progress session MUST return `409`.

#### Scenario: Replay returns the full reconstructable interview
- **WHEN** a client requests replay for a completed session
- **THEN** the response includes the ordered turns with their panel states, the terminal panel state, and the evaluation

#### Scenario: Replay of in-progress session is rejected
- **WHEN** a client requests replay for an `in_progress` session
- **THEN** the response is `409` with `error.code = session_in_progress`
