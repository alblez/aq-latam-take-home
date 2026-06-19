## ADDED Requirements

### Requirement: End-of-interview transcript and evaluation
At the end of an interview the application SHALL display the full question/answer transcript and the structured evaluation — overall score, per-competency results, and the narrative strengths and concerns. When the evaluation is not yet available, the UI MUST show a clear unavailable state rather than failing.

#### Scenario: Review shows transcript and evaluation
- **WHEN** an interview completes
- **THEN** the review screen shows the full transcript and the structured evaluation with overall score, strengths, and concerns

#### Scenario: Evaluation unavailable is shown gracefully
- **WHEN** the evaluation could not be generated
- **THEN** the UI shows an unavailable state instead of an error or a fabricated score

### Requirement: History page with role filtering and analytics
The application SHALL provide a history page listing the owner's past sessions with per-session metrics (duration, talk ratio, coverage, score), and MUST allow filtering the list by role.

#### Scenario: History lists past sessions with metrics
- **WHEN** a user opens the history page
- **THEN** their past sessions are listed with duration, talk ratio, coverage, and score

#### Scenario: Filtering history by role
- **WHEN** a user filters history by a role
- **THEN** only sessions for that role are shown

### Requirement: Replay a past interview
From history the user SHALL be able to replay a completed session, stepping through the recorded turns with the decision panel state that produced each interviewer question.

#### Scenario: Replaying a completed session
- **WHEN** a user opens a past session for replay
- **THEN** the recorded turns are shown in order with their decision panel state
