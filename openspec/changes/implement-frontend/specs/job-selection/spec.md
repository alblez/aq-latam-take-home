## ADDED Requirements

### Requirement: Browse sample jobs
The application SHALL present a list of at least three sample jobs, each showing a title and a short description. The list MUST be fetched from `/api/jobs`.

#### Scenario: Job list is shown on the landing page
- **WHEN** a user opens the app
- **THEN** at least three jobs are listed, each with a title and description

### Requirement: Enter an interview room for a role
Selecting a job SHALL create and start a session for that role and navigate the user into the Interview Room, where the first interviewer question is shown.

#### Scenario: Selecting a job starts the interview
- **WHEN** a user clicks a job
- **THEN** a session is created and started for that role
- **AND** the user lands in the Interview Room showing the first question

#### Scenario: Job that no longer exists is handled
- **WHEN** session creation fails because the job is not found
- **THEN** the user is shown a clear error rather than a broken room
