## Purpose

Manage interview session lifecycle, question generation, and depth policy.

## Requirements

### Requirement: Deterministic session lifecycle
The system SHALL model an interview as a session with status `in_progress`, `completed`, or `ended_early`. A session MUST be created for a job, started to yield the first interviewer question, advanced one turn at a time, and moved to a terminal status exactly once. Each terminal session MUST record a `completionReason` of `all_competencies_covered`, `question_cap`, or `ended_early`.

#### Scenario: Create then start a session
- **WHEN** a client creates a session for a valid job and then starts it
- **THEN** the session status is `in_progress` and the response contains the first interviewer question, the job title, and the initial panel state

#### Scenario: Starting an already-started session is rejected
- **WHEN** a client starts a session that is not in a startable state
- **THEN** the response is `409` and the session status is unchanged

#### Scenario: Terminal status is assigned once
- **WHEN** an interview reaches a terminal condition
- **THEN** the session status becomes `completed` or `ended_early` with a `completionReason`
- **AND** subsequent answer submissions are rejected with `409`

### Requirement: Minimum interview depth policy
The engine SHALL enforce a deterministic policy independent of the language model: at least `minQuestions` (6) questions and at least `minFollowUps` (2) answer-dependent follow-ups before the interview is eligible to end, capped at `maxQuestions` (12) overall and `maxFollowUpsPerCompetency` (2). The policy MUST expose `eligibleToEnd` and the live counts each turn.

#### Scenario: Cannot end before minimums are met
- **WHEN** fewer than 6 questions or fewer than 2 follow-ups have occurred
- **THEN** `policyState.eligibleToEnd` is `false` and the engine selects another question

#### Scenario: Question cap forces termination
- **WHEN** the interview reaches `maxQuestions`
- **THEN** the next turn is terminal with `completionReason = question_cap`

### Requirement: Role-grounded, answer-dependent question generation
Questions SHALL be grounded in the selected job's competencies and seeded question packs. The engine MUST support generation modes `pack_seed` (a question drawn from the role's pack), `targeted_follow_up` (a probe that depends on the candidate's prior answer), and `generic_probe` (a deterministic fallback). Follow-up questions MUST reference the prior answer that triggered them.

#### Scenario: New topic is grounded in a role competency
- **WHEN** the engine opens a new topic
- **THEN** the question targets a competency belonging to the session's job, with generation mode `pack_seed`

#### Scenario: Follow-up depends on the prior answer
- **WHEN** the engine chooses to follow up
- **THEN** the question is generated with mode `targeted_follow_up` and is tied to the triggering answer turn

### Requirement: End-early and resume
A client SHALL be able to end an in-progress interview early, receiving a terminal panel state and the list of uncovered competencies. The system MUST also expose the persisted session state so an interrupted interview can be resumed, signalling when the last turn was a candidate answer awaiting an interviewer response.

#### Scenario: End early before full coverage
- **WHEN** a client ends an in-progress session early
- **THEN** the response includes the terminal panel state and `uncoveredCompetencies`, and the status becomes `ended_early`

#### Scenario: Resume flags pending recovery
- **WHEN** a client fetches session state whose latest turn is an unanswered candidate answer
- **THEN** the response sets `needsRecovery = true`
