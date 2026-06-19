## ADDED Requirements

### Requirement: Structured end-of-interview evaluation
When a session reaches a terminal status, the system SHALL produce a structured evaluation containing an overall score on a fixed scale, per-competency scores with supporting evidence, and a narrative with an overall verdict, strengths, and concerns. Strengths and concerns MUST cite the competency and turn ids they are grounded in.

#### Scenario: Completed session yields an evaluation
- **WHEN** a client requests the evaluation of a completed session
- **THEN** the response includes the transcript plus an evaluation with `overallScore`, `scoreScale`, `competencyScores`, and a `narrative` (`summary`, `overallVerdict`, `strengths`, `concerns`)

#### Scenario: Per-competency scores carry evidence
- **WHEN** a competency was assessed
- **THEN** its score includes evidence with supporting turn ids and quotes

### Requirement: Evaluation availability gating
The evaluation endpoint SHALL only return for terminal sessions. Requesting the evaluation of an in-progress session MUST return `409` with `error.code = session_in_progress`. Turn and end-early responses MUST expose an `evaluationReady` flag.

#### Scenario: In-progress evaluation is rejected
- **WHEN** a client requests the evaluation of an `in_progress` session
- **THEN** the response is `409` with `error.code = session_in_progress`

### Requirement: Degraded-signal and model-failure handling
When there is insufficient signal or the language model is unavailable, the system SHALL still return a well-formed result: an `insufficient_signal` verdict and/or a `modelFailureNote`, with competencies marked unassessed rather than fabricated. Early-ended interviews MUST carry an `earlyEndNote`.

#### Scenario: Insufficient signal is surfaced, not fabricated
- **WHEN** the interview lacks enough signal to score a competency
- **THEN** that competency is marked unassessed and listed in `unassessedCompetencyIds`

#### Scenario: Model unavailable surfaces a stable error
- **WHEN** the evaluation model is unavailable during generation
- **THEN** the failure is surfaced via `error.code = model_unavailable` or a `modelFailureNote`, never as a fabricated score
