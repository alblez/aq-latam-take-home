# Backend Implementation Decisions

Status: backend implementation decisions; update only through explicit decision changes.

Reader: future backend implementer.

Post-read action: implement the FastAPI backend without re-deciding controller behavior, JSONB validation, seed strategy, ownership checks, resume behavior, transaction boundaries, or the minimum regression test plan.

## 1. Scope and guiding principle

This backend should optimize for the home-test grading signal:

- deterministic interviewer state and decision panel
- job-specific question packs
- replay and analytics
- buildable implementation speed

Do not build enterprise-grade infrastructure unless it directly supports those signals.

Specific simplifications already accepted:

- no SSE in the first pass; panel updates return synchronously from normal HTTP routes
- no cursor pagination in first pass; history uses a fixed cap
- no event-sourcing tables
- no background worker for evaluation or recovery
- no auth system; anonymous owner UUID only
- no backend/API/persistence work for video mode in the first pass; camera input is frontend-local
- analytics are derived live from sessions, turns, and competency score rows; do not add a persisted metrics table

## 2. Controller policy

The interview controller is deterministic code. The LLM analyzes answers and phrases questions; it does not choose interview flow.

### Policy config

Use these policy values for first implementation:

```json
{
  "policyVersion": "v1",
  "minQuestions": 6,
  "minFollowUps": 2,
  "maxQuestions": 12,
  "maxFollowUpsPerCompetency": 2
}
```

Persist the config on session creation so replay can show which policy rules governed that session.

### Turn decision types

The controller chooses one action for each interviewer turn:

- `new_topic`: move to a competency gap and ask a pack-seeded opener
- `follow_up`: ask a targeted question based on a prior candidate answer signal
- `end`: terminate the interview and write terminal panel state

`follow_up` turns never use a pack item. `new_topic` turns should use a pack item unless fallback mode applies.

### Question pack selection

Question packs are job-specific through the relationship `jobs -> competencies -> question_pack_items`.

Behavioral/technical grouping lives on competencies. Pack items inherit category from their parent competency; do not add a separate pack-item category in application logic.

For a `new_topic` action, select a pack item for the target competency when one exists and persist its id on the interviewer turn. For a `follow_up` action, keep `source_pack_item_id = null` because the question is generated from the candidate's answer signal, not from the pack.

### Signal-first follow-up rule

Follow-up should not depend only on negative flags. Follow-up depends on any specific response signal that can produce an answer-dependent question.

Examples of usable signals:

- `vague_claim`
- `no_evidence`
- `contradiction`
- `interesting_thread`
- `tradeoff_mentioned`
- `metric_mentioned`
- `specific_tool_mentioned`
- `well_covered`

Negative signals create clarification follow-ups. Positive signals create depth follow-ups.

A valid follow-up must have all of these:

- persisted interviewer turn has `action = follow_up`
- persisted interviewer turn has `source_pack_item_id = null`
- reasoning includes a trigger candidate turn id
- reasoning includes an answer excerpt or detail
- generated question visibly references that answer excerpt or detail

### Decision order

For every submitted answer:

1. Persist candidate turn.
2. Analyze answer into structured signals.
3. Update competency state.
4. Count existing interviewer questions.
5. Count existing follow-ups overall.
6. Count follow-ups for the current competency.
7. Count uncovered competencies and remaining question budget.
8. Decide next action using deterministic policy.
9. Generate phrasing for the chosen action.
10. Persist interviewer turn or terminal state.

### Follow-up budget

A follow-up consumes:

- one global question slot
- one global follow-up count
- one per-competency follow-up count

Before the session has two follow-ups, prefer a follow-up when:

- a specific response signal exists
- the current competency has follow-up budget remaining
- the global question cap is not reached
- coverage will not be endangered by spending one more question on depth

After the session has two follow-ups, coverage gets priority. Follow-ups become optional depth probes.

Near the question cap, uncovered competencies take priority over more follow-up depth.

### End conditions

The controller may auto-end only when:

```txt
questionCount >= minQuestions
followUpCount >= minFollowUps
and (allCompetenciesCovered or questionCount >= maxQuestions)
```

The user may explicitly end early before those conditions. That produces `status = ended_early` and must write a terminal panel state explaining uncovered competencies.

### Fallback behavior

The interview must not stall on model failure.

Fallback rules:

- Analyze failure: no signals for this answer; show failure mode in reasoning; policy safely advances coverage.
- Generate failure: use selected pack item text when available; otherwise use a generic competency probe.
- Both fail: serve generic probe immediately.

Fallback must be recorded in `generation.fallbackMode` or `failureMode` inside the reasoning/terminal panel payload.

## 3. JSONB validation schemas

JSONB is flexible in Postgres but strict in backend code.

Use backend validation models before writing any JSONB field.

Validate these payloads:

- controller config
- turn reasoning
- terminal panel state
- evaluation narrative
- competency score evidence

### Controller config

Stored on sessions. Read as a whole.

Required fields:

- `policyVersion`
- `minQuestions`
- `minFollowUps`
- `maxQuestions`
- `maxFollowUpsPerCompetency`

### Turn reasoning

Stored on interviewer turns only. Candidate turns have no reasoning payload.

Must include:

- `schemaVersion`
- `policyVersion`
- `rubricSnapshot`
- `flags`
- `policyState`
- `trigger` when the action is a targeted follow-up
- `rationale`
- `generation`
- `failureMode`

The relational columns remain authoritative for:

- action
- target competency
- source pack item

The API assembles the full panel state from relational columns plus reasoning JSON.

### Terminal panel state

Stored on sessions when the interview ends.

Purpose:

- show why the interview ended
- preserve final coverage/gap state
- avoid inserting a fake terminal turn with null content

Must include:

- `schemaVersion`
- `policyVersion`
- `action = end`
- `completionReason`
- `endedBy`
- `rubricSnapshot`
- `policyState`
- `uncoveredCompetencyIds`
- `rationale`
- `failureMode`

Lifecycle query truth still lives in scalar columns: status, completion reason, timestamps.

### Evaluation narrative

Stored on sessions. Read as a whole.

Must include:

- `schemaVersion`
- `evaluationVersion`
- `scoreScale`
- `summary`
- `overallVerdict`
- `strengths`
- `concerns`
- `unassessedCompetencyIds`
- `earlyEndNote`
- `modelFailureNote`

Do not store authoritative overall score in this JSON. Compute overall score from assessed competency score rows.

### Competency score evidence

Stored on session competency score rows. Nullable but recommended.

Must include when present:

- `schemaVersion`
- `evaluationVersion`
- `coverage`
- `supportingTurnIds`
- `quotes`
- `signals`
- `scoreRationale`
- `unassessedReason`

### Strict-Mode JSONB UUID Coercion Pattern

When reading JSONB columns that contain UUID values (stored as strings by PostgreSQL),
use `Model.model_validate_json(json.dumps(data))` — NOT `Model.model_validate(data)`.

**Why:** Strict-mode Pydantic models (`strict=True`) reject Python `str` values for UUID
fields. PostgreSQL JSONB stores UUIDs as strings; SQLAlchemy deserializes JSONB into plain
Python dicts with string values. Calling `model_validate(data)` in strict mode raises
`ValidationError` because the validator sees `str` where it expects `UUID`.

The `model_validate_json()` path uses Pydantic's JSON-mode parsing which applies str→UUID
coercion even under strict mode, making it safe for JSONB payloads with UUID fields.

**Where applied:**
- `app/evaluation_detail.py` — narrative and evidence JSONB validation
- `app/engine/evaluation.py` — turn reasoning JSONB parsing

**Origin:** Phase 9 WR-03 review fix (decision 06-02).

## 4. Seed data design

Do not rely on hidden data manually created in a Neon project.

Use Neon tooling or local SQL work to draft seed data, but commit the final seed SQL so the project is reproducible.

Minimum committed seed artifact:

```txt
backend/seed_data.sql
```

Seed data must include:

- at least 3 jobs
- behavioral and technical competencies per job
- ordered question pack items per competency, targeting 3-5 items per competency where practical
- stable sort orders

Seed data should be idempotent.

The seed should support the demo without hand-editing production data:

- job list loads from database
- every job has competencies
- every job has both behavioral and technical coverage through competencies
- every competency has at least one pack item
- enough pack items exist to avoid repetitive first-pass interviews

Do not run seeding as a hidden app-start side effect. Run schema and seed as explicit setup/deployment steps.

## 5. Session ownership rule

Owner scope is anonymous and header-based.

Every owner-scoped request must include:

```http
X-Owner-Id: <uuid>
```

Backend rules:

- validate header is a UUID
- create sessions with `owner_id = X-Owner-Id`
- every session-scoped route checks stored session owner against header
- wrong owner returns `404 session_not_found`
- never return owner id in response payloads

This is not security-grade authentication. It is browser-local anonymous scoping suitable for the home test.

## 6. Resume and crash behavior

Zero resume is not acceptable because the product spec requires reload recovery. Keep recovery minimal.

### Normal resume

`GET /state` returns enough data for the frontend to resume:

- session status
- job title
- competencies with status
- ordered turns
- latest current question when one exists
- latest panel state
- terminal panel state when complete

### Start idempotency

If the first interviewer turn already exists, `POST /start` returns it instead of creating another first question.

### Turn retry idempotency

`clientTurnId` protects answer submission.

If the same client turn id is submitted again for the same session, do not insert a duplicate candidate answer.

If a following interviewer turn already exists, return the current/latest session state. If no following interviewer turn exists, continue the missing analyze/policy/generate pipeline from the existing candidate turn.

### Crash after candidate answer commit

This can happen because model calls occur outside DB transactions.

Minimal behavior:

- if latest turn is a candidate turn with no following interviewer turn, session state reports `needsRecovery = true`
- retrying `/turn` with the same client turn id continues the pipeline from the existing candidate turn
- no background repair daemon is required

The frontend may show a simple “Continue interview” or “Retry last answer” state.

### What not to build

Do not build:

- background job queue
- worker-based recovery
- event sourcing
- durable orchestration engine
- multi-step crash journal

## 7. Transaction boundaries

Do not hold a database transaction during a model call.

Recommended turn flow:

1. Validate owner/session/request.
2. Insert candidate turn in a short transaction.
3. Commit.
4. Run analyze, deterministic policy, and generate outside transaction.
5. Insert interviewer turn in a short transaction.
6. Commit.
7. Return next question and panel state.

If generation fails but process is alive, persist a fallback interviewer turn and return it. Do not leave the user stuck waiting silently.

Evaluation flow at session end:

1. Decide terminal state.
2. Generate/validate evaluation synchronously.
3. Insert one competency score row per job competency.
4. Update session status, completion reason, completed timestamp, terminal panel state, and evaluation narrative in one short transaction.
5. Return completion response.

Evaluation scoring rule:

- ask the model for integer per-competency scores on a 1-10 scale directly
- do not ask for decimal scores and round after the fact
- reject or repair invalid score payloads before persistence

Rationale:

- avoids long DB locks
- avoids tying Postgres transaction lifetime to OpenRouter latency
- makes retry/recovery states explicit
- keeps implementation simple enough for the home test

## 8. Test plan

Write the minimum tests that protect the behavior most likely to regress.

Do not use live OpenRouter in normal tests. Mock the model gateway.

### Controller policy tests

Cover:

- cannot auto-end before 6 interviewer questions
- cannot auto-end before 2 follow-ups
- maximum 2 follow-ups per competency
- follow-up can be triggered by positive or negative specific answer signals
- follow-up requires trigger turn and answer excerpt
- coverage is prioritized near max question cap
- final state records why the interview ended

### Ownership tests

Cover:

- owner header required on owner-scoped routes
- matching owner can access session
- wrong owner gets 404
- owner id is not returned in responses

### Idempotency tests

Cover:

- duplicate `/start` does not create duplicate first question
- duplicate `/turn` with same client turn id does not create duplicate candidate turn
- duplicate `/turn` returns current/latest state

### Question pack traceability tests

Cover:

- new-topic interviewer turns have source pack item when pack exists
- follow-up turns have no source pack item
- pack item belongs to selected job through competency

### Evaluation tests

Cover:

- one score row per job competency
- assessed rows require integer score 1-10
- unassessed rows have null score
- overall score averages assessed rows only
- evaluation narrative validates before persistence

### History/replay tests

Cover:

- history filters by owner
- optional job filter works
- history response envelope is returned
- replay includes ordered turns
- replay includes terminal panel state
- replay can map competency ids to names/categories

### JSONB validation tests

Cover:

- invalid reasoning payload rejected before DB write
- invalid terminal panel payload rejected before DB write
- invalid evaluation narrative rejected before DB write
- invalid evidence payload rejected before DB write

## 9. Deferred work

Defer unless time remains:

- SSE panel stream
- cursor pagination for history
- materialized analytics table
- background evaluation job
- richer cross-session signal analytics
- persisted live-state cursor separate from turns/reasoning

## 10. Implementation readiness checklist

Before coding handlers:

- update OpenAPI contract with the contract decisions
- translate unified schema into migration or setup SQL
- add idempotent seed SQL
- define backend validation models for JSONB payloads
- define controller policy module boundaries
- mock model gateway in tests
- add ownership dependency/helper for `X-Owner-Id`
