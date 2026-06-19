## Purpose

Voice-driven interview room with turn-by-turn flow, live decision panel, and early-end support.

## Requirements

### Requirement: Voice-driven answering with text fallback
The Interview Room SHALL let the candidate answer by microphone (voice), transcribing speech to text in the browser, and MUST provide a text-input fallback when speech recognition is unavailable. Each submitted answer MUST record its input mode (`voice` or `text`).

#### Scenario: Voice answer is captured and submitted
- **WHEN** a candidate speaks an answer and submits it
- **THEN** the transcript is sent as the answer with `inputMode = voice`

#### Scenario: Text fallback when speech is unavailable
- **WHEN** the browser does not support speech recognition
- **THEN** a text input is offered and answers are submitted with `inputMode = text`

### Requirement: Turn-by-turn interview flow
The room SHALL display the current interviewer question, accept one answer, and render the next question until the interview reaches a terminal state. A submitted answer MUST carry a client-generated `clientTurnId` so retries do not create duplicate turns.

#### Scenario: Advancing through questions
- **WHEN** a candidate submits an answer
- **THEN** the next interviewer question is shown, or a completion state if the interview ended

#### Scenario: Duplicate submission is de-duplicated
- **WHEN** the same answer is submitted twice with the same `clientTurnId`
- **THEN** only one candidate turn is recorded

### Requirement: Live decision panel
The room SHALL render the interviewer's live decision panel each turn — competencies covered / in-progress / gaps, detected signals, and the rationale for the next question — reflecting the panel state returned by the backend.

#### Scenario: Panel updates each turn
- **WHEN** a new question is received
- **THEN** the decision panel updates to show current coverage, signals, and the rationale for the chosen question

### Requirement: End interview early
The room SHALL offer an explicit control to end the interview before all competencies are covered, after which the candidate is taken to the review screen.

#### Scenario: Candidate ends early
- **WHEN** a candidate chooses to end early
- **THEN** the interview is finalized and the review screen is shown

### Requirement: Real backend mode
The application SHALL require a live backend (`NEXT_PUBLIC_API_URL`) for all API calls. There is no mock mode — the frontend always talks to the deployed backend. The `NEXT_PUBLIC_API_URL` environment variable MUST be set or the application fails fast at startup.

#### Scenario: App requires a configured backend
- **WHEN** the application starts without `NEXT_PUBLIC_API_URL`
- **THEN** the application fails fast with a clear configuration error

#### Scenario: Hosted environments use the deployed backend
- **WHEN** the app is deployed to a hosted environment
- **THEN** requests go to the deployed backend configured via `NEXT_PUBLIC_API_URL`
