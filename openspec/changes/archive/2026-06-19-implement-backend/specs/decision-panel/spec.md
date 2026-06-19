## ADDED Requirements

### Requirement: Per-turn decision panel state
Every interviewer turn SHALL be accompanied by a panel state that exposes the interviewer's deterministic reasoning: a rubric snapshot (competencies covered / in-progress / gaps), detected signals, the policy state, the chosen action (`new_topic`, `follow_up`, or `end`), the target competency, and the generation provenance. The panel state MUST be persisted with the turn so it can be replayed.

#### Scenario: Panel accompanies each question
- **WHEN** the engine produces an interviewer question
- **THEN** the response includes a panel state with the rubric snapshot, policy state, chosen action, and generation mode

#### Scenario: Panel is persisted for replay
- **WHEN** a completed session is replayed
- **THEN** each interviewer turn carries the panel state that produced it

### Requirement: Rationale for the next question
The panel SHALL include a human-readable `rationale` explaining why the engine chose the next action, referencing the rubric gaps or the triggering answer. When a follow-up is chosen, the panel MUST identify the trigger turn and the answer excerpt that prompted it.

#### Scenario: Follow-up rationale names its trigger
- **WHEN** the engine chooses a follow-up
- **THEN** the panel `trigger` identifies the triggering turn and answer excerpt, and `rationale` explains the choice

### Requirement: Signal detection from answers
The system SHALL analyze each candidate answer and attach typed signal flags to the panel (for example `vague_claim`, `no_evidence`, `well_covered`, `tradeoff_mentioned`, `metric_mentioned`, `contradiction`). Each flag MUST carry a human-readable detail and, where applicable, the competency and turn it relates to.

#### Scenario: Answer produces signal flags
- **WHEN** a candidate submits an answer
- **THEN** the resulting panel includes zero or more typed flags, each with a `detail`
