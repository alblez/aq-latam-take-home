# Backend API Contract Decisions

Status: contract decisions reflected in `shared/contract.yaml`; keep aligned during backend/frontend route work.

Reader: future backend/frontend implementer.

Post-read action: verify `shared/contract.yaml` remains aligned, then implement matching FastAPI routes/frontend client calls without re-deciding API behavior.

## 1. Contract stance

The OpenAPI contract is a first-pass draft aligned to these decisions. It may change when a change improves:

- deterministic decision panel support
- job-specific question pack traceability
- replay and analytics
- delivery speed for the home test

Change `shared/contract.yaml` before changing backend handlers or frontend API client code.

## 2. Owner transport

Use a required header for anonymous owner scoping:

```http
X-Owner-Id: <uuid>
```

Do not send `ownerId` in request body, query string, or URL path.

Routes that require `X-Owner-Id`:

- `POST /api/sessions`
- `POST /api/sessions/{sessionId}/start`
- `POST /api/sessions/{sessionId}/turn`
- `GET /api/sessions/{sessionId}/state`
- `POST /api/sessions/{sessionId}/end-early`
- `GET /api/sessions/{sessionId}/evaluation`
- `GET /api/sessions/{sessionId}/replay`
- `GET /api/history`

Routes that do not require it:

- `GET /health`
- `GET /api/jobs`

Backend rule:

```txt
sessions.owner_id must equal X-Owner-Id for every session-scoped route.
```

If the header does not match the session owner, return `404 session_not_found`, not `403`. This avoids leaking that another owner's session exists.

Never return `owner_id` in API responses.

## 3. SSE decision

SSE is optional polish, not Phase 2 minimum.

First implementation uses synchronous panel updates:

- `/api/sessions/{sessionId}/start` returns the first question and `panelState`.
- `/api/sessions/{sessionId}/turn` returns the next question and `panelState`.
- `/api/sessions/{sessionId}/state` returns latest persisted session state and latest `panelState`.
- `/api/sessions/{sessionId}/replay` returns per-turn reasoning and `terminalPanelState`.

Reason:

- the interview loop already waits for a backend response after each candidate answer
- Stretch 1 grades deterministic controller visibility more than transport mechanism
- skipping streaming avoids Railway/CORS/proxy complexity in the first pass

If time remains, an optional stream may be added later:

```http
GET /api/sessions/{sessionId}/events
Accept: text/event-stream
X-Owner-Id: <uuid>
```

Minimum future event types:

- `panel_state`
- `heartbeat`
- `session_completed`

## 4. Video mode API decision

Video mode has no first-pass backend/API contract impact.

Do not add video-specific request fields, response fields, uploads, or persistence for the home-test implementation. Camera input is frontend-local unless a later explicit decision changes that.

## 5. Idempotency and retries

Use a frontend-generated `clientTurnId` on answer submissions.

`SubmitAnswerRequest` includes:

```json
{
  "clientTurnId": "uuid",
  "answerText": "Candidate answer.",
  "inputMode": "voice | text",
  "audioDurationMs": 42000
}
```

Rules:

- `clientTurnId` is required.
- `inputMode` is required.
- `audioDurationMs` is nullable.
- When `inputMode = text`, `audioDurationMs` should be null.
- When `inputMode = voice`, frontend should send `audioDurationMs` when known.
- Backend stores `inputMode` in `turns.input_mode`.
- Backend stores `clientTurnId` in `turns.client_turn_id` for candidate turns.

Retry behavior for `/turn`:

1. Validate `X-Owner-Id` and session ownership.
2. Check session is `in_progress`.
3. Check whether candidate turn with same `(session_id, client_turn_id)` already exists.
4. If it exists and already has a following interviewer turn, return current session state/latest generated response instead of inserting duplicate turns.
5. If it exists but has no following interviewer turn, continue the missing analyze/policy/generate pipeline from that persisted candidate turn.
6. If it does not exist, insert candidate turn, run analyze/policy/generate, insert interviewer turn, return response.

Retry behavior for `/start`:

- If first interviewer turn already exists, return it.
- Otherwise create the first interviewer turn.

## 6. Request shapes

### Create session

```http
POST /api/sessions
X-Owner-Id: <uuid>
```

```json
{
  "jobId": "uuid"
}
```

No `ownerId` field in the body.

### Start session

```http
POST /api/sessions/{sessionId}/start
X-Owner-Id: <uuid>
```

No request body required.

### Submit answer

```http
POST /api/sessions/{sessionId}/turn
X-Owner-Id: <uuid>
```

```json
{
  "clientTurnId": "uuid",
  "answerText": "Candidate answer.",
  "inputMode": "voice | text",
  "audioDurationMs": 42000
}
```

### Get session state

```http
GET /api/sessions/{sessionId}/state
X-Owner-Id: <uuid>
```

No request body required. Used for reload resume, early-end confirmation, and minimal crash recovery UI.

### End session early

```http
POST /api/sessions/{sessionId}/end-early
X-Owner-Id: <uuid>
```

No request body required. The frontend should use `/state` before this call to show uncovered competencies and ask for confirmation.

### Get evaluation

```http
GET /api/sessions/{sessionId}/evaluation
X-Owner-Id: <uuid>
```

No request body required.

### Get replay

```http
GET /api/sessions/{sessionId}/replay
X-Owner-Id: <uuid>
```

No request body required.

### History

```http
GET /api/history?jobId=<uuid>
X-Owner-Id: <uuid>
```

`jobId` is optional. Use `jobId`, not role/title string.

For speed, history uses a fixed server-side cap of 50 sessions. No cursor pagination in the first pass.

## 7. Response shapes

### Competency payload

Competency arrays returned from start, turn, state, evaluation/replay details use the database competency model. The category is required so frontend can render behavioral/technical grouping without inferring it from question text.

```json
{
  "id": "uuid",
  "name": "PostgreSQL schema design",
  "category": "behavioral | technical",
  "status": "not-reached | in-progress | covered"
}
```

### PanelState

`PanelState` is assembled from relational columns plus `turns.reasoning` JSONB.

Authoritative relational sources:

- `turns.action` -> `action`
- `turns.competency_id` -> `targetCompetencyId`
- `turns.source_pack_item_id` -> `sourcePackItemId`

Shape:

```json
{
  "rubricSnapshot": {
    "covered": ["competency_uuid"],
    "inProgress": ["competency_uuid"],
    "gaps": ["competency_uuid"],
    "competencies": []
  },
  "flags": [],
  "policyState": {
    "questionCount": 4,
    "followUpCount": 1,
    "minQuestions": 6,
    "minFollowUps": 2,
    "maxQuestions": 12,
    "maxFollowUpsPerCompetency": 2,
    "followUpCountsByCompetency": {},
    "eligibleToEnd": false
  },
  "action": "new_topic | follow_up | end",
  "targetCompetencyId": "uuid | null",
  "sourcePackItemId": "uuid | null",
  "trigger": {
    "turnId": "candidate_turn_uuid",
    "answerExcerpt": "Candidate answer excerpt.",
    "reason": "interesting_thread"
  },
  "rationale": "Deterministic policy rationale string.",
  "generation": {
    "mode": "pack_seed | targeted_follow_up | generic_probe | terminal",
    "fallbackMode": null,
    "answerDependencyRequired": true
  },
  "failureMode": null
}
```

`trigger` is nullable for the first question and for ordinary new-topic questions.

### StartSessionResponse

Returns first question and current panel state.

```json
{
  "question": "Question text.",
  "turnIndex": 0,
  "panelState": {},
  "competencies": [],
  "turns": [],
  "jobTitle": "Backend Engineer"
}
```

### SubmitAnswerResponse

`question` must be nullable because a final response has no next question.

```json
{
  "question": "Next question text or null.",
  "turnIndex": 5,
  "panelState": {},
  "competencies": [],
  "turns": [],
  "jobTitle": "Backend Engineer",
  "isComplete": false,
  "terminalPanelState": null,
  "evaluationReady": false
}
```

When the interview ends:

```json
{
  "question": null,
  "turnIndex": 11,
  "panelState": {},
  "competencies": [],
  "turns": [],
  "jobTitle": "Backend Engineer",
  "isComplete": true,
  "terminalPanelState": {},
  "evaluationReady": true
}
```

Schema impact of `question: null`: none. The database does not store a terminal turn with null content; `turns.content` remains `NOT NULL`.

### SessionStateResponse

Returned by `/state` for reload resume, early-end confirmation, and crash recovery.

```json
{
  "turns": [],
  "panelState": {},
  "competencies": [],
  "jobTitle": "Backend Engineer",
  "currentQuestion": "Question text or null.",
  "turnIndex": 5,
  "status": "in_progress | completed | ended_early",
  "needsRecovery": false,
  "terminalPanelState": null
}
```

`needsRecovery` is true when the latest persisted turn is a candidate answer with no following interviewer turn. In that case the frontend should offer a simple retry/continue action that resubmits `/turn` with the same `clientTurnId`.

### EndSessionEarlyResponse

End early uses current state for confirmation before the POST. On confirm, backend finalizes session, writes `terminalPanelState`, and generates/persists evaluation synchronously.

```json
{
  "uncoveredCompetencies": [
    { "id": "uuid", "name": "PostgreSQL schema design" }
  ],
  "terminalPanelState": {},
  "evaluationReady": true
}
```

### Evaluation

Evaluation is typed, not a generic object. Scores use integer 1-10 per competency. Overall score is derived from assessed competency scores.

```json
{
  "overallScore": 8.2,
  "scoreScale": { "min": 1, "max": 10 },
  "competencyScores": [
    {
      "competencyId": "uuid",
      "name": "PostgreSQL schema design",
      "category": "technical",
      "assessed": true,
      "score": 8,
      "notes": "Good schema tradeoff discussion.",
      "evidence": {}
    }
  ],
  "narrative": {
    "summary": "Concise overall evaluation.",
    "overallVerdict": "strong | mixed | needs_improvement | insufficient_signal",
    "strengths": [],
    "concerns": [],
    "unassessedCompetencyIds": [],
    "earlyEndNote": null,
    "modelFailureNote": null
  }
}
```

### SessionDetail

Used by evaluation and replay endpoints.

```json
{
  "session": {
    "id": "uuid",
    "jobId": "uuid",
    "status": "completed | ended_early | in_progress"
  },
  "job": {
    "id": "uuid",
    "title": "Backend Engineer",
    "description": "Role description."
  },
  "competencies": [],
  "turns": [],
  "evaluation": {},
  "terminalPanelState": {}
}
```

This is an additive contract change. It is needed because replay snapshots contain competency IDs and the UI needs names/categories.

### SessionSummary

History returns an envelope, not a raw array:

```json
{
  "sessions": [
    {
      "id": "uuid",
      "jobId": "uuid",
      "jobTitle": "Backend Engineer",
      "status": "completed",
      "startedAt": "2026-06-03T12:00:00Z",
      "completedAt": "2026-06-03T12:12:00Z",
      "durationMs": 720000,
      "overallScore": 8.2,
      "coveragePercent": 0.83,
      "talkRatio": 0.42,
      "questionCount": 8,
      "followUpCount": 2
    }
  ]
}
```

## 8. Completion behavior

The backend generates and persists evaluation synchronously when a session completes or ends early.

Reason:

- no background worker needed
- frontend can immediately navigate to results
- simpler home-test deployment

After `/turn` returns `isComplete: true` or `/end-early` returns `evaluationReady: true`, the frontend calls:

```http
GET /api/sessions/{sessionId}/evaluation
X-Owner-Id: <uuid>
```

## 9. Error shape

Use one error response shape everywhere.

```json
{
  "error": {
    "code": "session_not_found",
    "message": "Session not found.",
    "details": {},
    "requestId": "req_123"
  }
}
```

Minimum error codes:

- `invalid_owner_id`
- `job_not_found`
- `session_not_found`
- `session_not_in_progress`
- `turn_already_submitted`
- `validation_error`
- `model_unavailable`

Status code guidance:

- `400` malformed UUID/header
- `404` job/session missing or wrong owner
- `409` invalid session state or already completed session
- `422` request validation failure
- `503` model unavailable only if fallback cannot recover

Never return `200` with an error body.

## 10. Internal fields not exposed directly

Do not expose:

- `owner_id`
- `controller_config`
- raw `model_name` unless adding explicit debug/provenance UI
- raw database IDs for score rows
- model exception details, stack traces, provider payloads, prompts, or secrets

Expose intentionally:

- `panelState`
- per-turn `reasoning` through `turns.reasoning` in replay/detail responses
- `terminalPanelState`
- `sourcePackItemId` for question pack traceability

## 11. Contract update checklist

Apply these changes to `shared/contract.yaml` before implementation:

- Add required `X-Owner-Id` header parameter to owner-scoped endpoints.
- Remove `ownerId` from request body/query parameters.
- Add `clientTurnId` and required `inputMode` to `SubmitAnswerRequest`.
- Make `question` nullable in submit response.
- Add `category` to competency payloads returned by start, turn, state, and detail responses.
- Add `status`, `needsRecovery`, and `terminalPanelState` to `SessionStateResponse`.
- Add `terminalPanelState` and `evaluationReady` to terminal responses.
- Add `policyState`, `trigger`, `generation`, and `failureMode` to `PanelState`.
- Type `Evaluation` instead of generic object.
- Add `job`, `competencies`, and `terminalPanelState` to `SessionDetail`.
- Add `jobId`, `completedAt`, `durationMs`, `talkRatio`, `questionCount`, and `followUpCount` to `SessionSummary`.
- Change history response from raw array to `{ "sessions": [] }`.
- Use optional `jobId` history filter, not role/title.
- Add standard `ErrorResponse` to every endpoint.
- Do not add video-specific API fields in the first pass.
- Mark SSE endpoint as optional/not in first-pass contract, unless explicitly implemented later.
