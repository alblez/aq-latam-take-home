# Backend Database Decisions

## 1. Purpose

- Records final confirmed database and backend-internal persistence decisions from the schema refinement session.
- Intended to support a later database/backend work plan.
- Does not redesign the schema.
- Does not create an implementation plan.

## 2. Sources Reviewed

- Current schema refinement chat session.
- `backend/docs/schema.sql`.
- `docs/home_test_requirements.md`, only for baseline home-test requirements.

## 3. Final Schema Direction

- Use a six-table competency-spine model:
  - `jobs`
  - `competencies`
  - `question_pack_items`
  - `sessions`
  - `turns`
  - `session_competency_scores`
- Use a 3NF + JSONB hybrid:
  - Normalize data that must be joined, constrained, filtered, counted, or aggregated.
  - Keep replay, panel, evaluation, evidence, and controller-config snapshots as JSONB because the application reads them as whole objects.
- Do not add event-sourcing/event tables.
- Promote query-critical or idempotency-related turn/session facts to columns:
  - `sessions.completion_reason`
  - `turns.action`
  - `turns.source_pack_item_id`
  - `turns.input_mode`
  - `turns.client_turn_id`
- Keep full panel/replay/evaluation/evidence snapshots as JSONB.
- Prioritize home-test buildability and reviewer-visible behavior over enterprise completeness.

## 4. Confirmed Table Decisions

### `jobs`

- Purpose:
  - Seeded interview roles/jobs shown to the user.
  - Each job has a `title` and `description`.
- Confirmed fields/constraints:
  - `sort_order` provides deterministic display/test ordering.
  - `title` is unique via `uq_jobs_title` for idempotent seed/upsert behavior.
  - `sort_order >= 0` is enforced.
- Relationships:
  - One `job` owns many `competencies`.
  - One `job` has many `sessions`.
- Delete behavior:
  - `competencies.job_id` uses `ON DELETE CASCADE` from `jobs`.
  - `sessions.job_id` uses `ON DELETE RESTRICT` to preserve interview history.

### `competencies`

- Purpose:
  - Central rubric spine for the platform.
  - Shared object for question selection, question packs, turns, panel/replay, evaluation, and analytics.
- Confirmed fields/constraints:
  - `job_id` ties each competency to one job.
  - `category competency_category` is where behavioral/technical split lives.
  - `sort_order` provides stable controller/UI ordering.
  - `UNIQUE(job_id, name)` prevents duplicate competency names within a job.
  - `sort_order >= 0` is enforced.
- Relationships:
  - One `competency` has many `question_pack_items`.
  - One `competency` can be referenced by many `turns`.
  - One `competency` can be referenced by many `session_competency_scores`.
  - Competency ids appear in panel/replay/evaluation JSONB snapshots for traceability.
- Confirmed category decision:
  - Behavioral/technical category lives on `competencies`, not on `question_pack_items`.

### `question_pack_items`

- Purpose:
  - Stores role/job-specific opener seed questions through the relationship `jobs -> competencies -> question_pack_items`.
  - `prompt_text` is a seed for the LLM to rephrase, not necessarily the exact asked question.
- Confirmed relationship decisions:
  - Hangs off `competencies`, not directly off `jobs`.
  - No independent category column.
  - Category is inherited through the parent `competencies.category`.
- Confirmed follow-up decision:
  - Pack items are not follow-up sources.
  - Follow-ups are generated from candidate answer signals.
- Confirmed fields/constraints:
  - `UNIQUE(competency_id, prompt_text)` prevents duplicate seed prompts per competency.
  - `prompt_text` must not be blank.
  - `sort_order >= 0` is enforced.
- Source-pack traceability:
  - Source-pack usage belongs on `turns.source_pack_item_id`, not on `question_pack_items`.

### `sessions`

- Purpose:
  - Represents one interview session for an anonymous owner and a selected job.
- Confirmed fields/constraints:
  - `owner_id UUID NOT NULL` stores anonymous owner identity.
  - No users/auth table is introduced.
  - `status session_status` tracks lifecycle.
  - `completion_reason completion_reason` records why a terminal session ended.
  - `model_name TEXT` records model provenance when available.
  - `started_at`, `completed_at`, and `updated_at` support lifecycle, replay, and analytics.
  - `completed_at >= started_at` is enforced when `completed_at` is present.
- Lifecycle rules:
  - `status = 'in_progress'` requires `completed_at IS NULL` and `completion_reason IS NULL`.
  - `status = 'completed'` requires `completed_at IS NOT NULL` and `completion_reason IN ('all_competencies_covered', 'question_cap')`.
  - `status = 'ended_early'` requires `completed_at IS NOT NULL` and `completion_reason = 'ended_early'`.
- Confirmed JSONB fields:
  - `controller_config` snapshots controller guard/config values.
  - `terminal_panel_state` stores final decision-panel state for replay/display.
  - `evaluation_narrative` stores free-text evaluation narrative read as a whole.
- Indexing:
  - `job_id` indexed.
  - `(owner_id, status, started_at DESC)` supports owner-scoped history.
  - `(owner_id, job_id, started_at DESC)` supports owner-scoped job filtering.
  - `updated_at DESC` supports recent activity ordering.

### `turns`

- Purpose:
  - Ordered transcript rows for candidate and interviewer turns.
  - Stores the per-interviewer-turn deterministic controller snapshot.
- Confirmed fields/constraints:
  - `session_id` links turn to session.
  - `client_turn_id` is supplied for candidate answers so retries/double-clicks do not create duplicate candidate turns.
  - `turn_index` orders transcript rows and is unique per session.
  - `role turn_role` distinguishes `interviewer` from `candidate`.
  - `competency_id NOT NULL` records which competency the turn probes.
  - `content` stores question or answer text and must not be blank.
  - `input_mode answer_input_mode` records `voice` or `text` for candidate turns.
  - `audio_duration_ms` supports talk-ratio analytics and must be non-negative when present.
  - `action policy_action` records deterministic controller action for interviewer turns.
  - `source_pack_item_id` traces pack-seeded new-topic turns to `question_pack_items`.
  - `reasoning JSONB` stores full per-interviewer-turn panel/replay snapshot.
- Role-scoped rules:
  - Candidate turns require `client_turn_id` and `input_mode`.
  - Candidate turns must not have `action`, `source_pack_item_id`, or `reasoning`.
  - Interviewer turns require `action` and `reasoning`.
  - Interviewer turns require `client_turn_id IS NULL`, `input_mode IS NULL`, and `audio_duration_ms IS NULL`.
- Follow-up/pack rules:
  - Follow-up turns cannot have `source_pack_item_id`.
  - If `source_pack_item_id` is present, `action` must be `new_topic`.
  - `source_pack_item_id` may be null for fallback or non-pack cases.
- Ordering/indexing:
  - `UNIQUE(session_id, turn_index)`.
  - Partial unique index on `(session_id, client_turn_id)` where `client_turn_id IS NOT NULL`.
  - `(session_id, turn_index)` for replay ordering.
  - `(session_id, role, turn_index)` for role-filtered transcript queries.
  - `competency_id`, `source_pack_item_id`, and `(session_id, action)` are indexed.
  - Partial index `(session_id, competency_id)` where `role = 'interviewer' AND action = 'follow_up'` supports follow-up budget counting.

### `session_competency_scores`

- Purpose:
  - Stores one evaluation row per session per competency.
  - Supports coverage analytics and score trend.
- Confirmed fields/constraints:
  - `UNIQUE(session_id, competency_id)` enforces one score row per session/competency pair.
  - `assessed BOOLEAN NOT NULL DEFAULT false` distinguishes probed/scored from unassessed.
  - `score SMALLINT` uses whole-number score scale 1-10.
  - `score` must be null when `assessed = false`.
  - `score` is required when `assessed = true`.
  - `evidence JSONB` stores score explanation/evidence read as a whole.
- Relationship to evaluation:
  - Numeric/queryable evaluation lives here.
  - Free-text narrative lives in `sessions.evaluation_narrative`.
- Relationship to analytics:
  - Coverage derives from `assessed`.
  - Score trend derives from assessed `score` values.

## 5. Confirmed Relationship Decisions

```txt
jobs 1 ── many competencies
competencies 1 ── many question_pack_items
jobs 1 ── many sessions
sessions 1 ── many turns
competencies 1 ── many turns
sessions 1 ── many session_competency_scores
competencies 1 ── many session_competency_scores
question_pack_items 1 ── many turns via source_pack_item_id
```

- Delete behavior:
  - `jobs -> competencies`: cascade.
  - `competencies -> question_pack_items`: cascade.
  - `jobs -> sessions`: restrict.
  - `sessions -> turns`: cascade.
  - `sessions -> session_competency_scores`: cascade.
  - `competencies -> turns`: restrict.
  - `competencies -> session_competency_scores`: restrict.
  - `question_pack_items -> turns`: restrict.
- Confirmed practical rule:
  - Delete sessions to remove interview transcript/evaluation.
  - Do not delete seed jobs/competencies/pack items once referenced by sessions/turns; historical replay traceability is preserved.

## 6. Confirmed JSONB Decisions

### `sessions.controller_config`

- Purpose:
  - Stores controller guard/config snapshot for deterministic replay context.
- Why JSONB:
  - Read as a whole.
  - Policy knobs may evolve together.
  - Not used as primary relational facts.
- Query/read pattern:
  - Read whole by backend controller/replay logic.
- Confirmed shape:

```json
{
  "policyVersion": "v1",
  "minQuestions": 6,
  "minFollowUps": 2,
  "maxQuestions": 12,
  "maxFollowUpsPerCompetency": 2
}
```

### `sessions.terminal_panel_state`

- Purpose:
  - Stores final decision-panel snapshot for replay/display.
  - Explains why the interview ended without requiring a fake terminal turn.
- Why JSONB:
  - Snapshot read as a whole for replay.
  - Lifecycle source of truth remains normalized in `sessions.status` and `sessions.completion_reason`.
- Query/read pattern:
  - Read whole for replay/final panel.
- Confirmed shape:

```json
{
  "schemaVersion": "terminal_panel_state.v1",
  "policyVersion": "v1",
  "action": "end",
  "completionReason": "all_competencies_covered | question_cap | ended_early",
  "endedBy": "controller | user",
  "rubricSnapshot": {
    "covered": ["competency_uuid"],
    "inProgress": [],
    "gaps": ["competency_uuid"],
    "competencies": [
      {
        "id": "competency_uuid",
        "status": "covered | in-progress | not-reached",
        "category": "behavioral | technical",
        "evidenceTurnIds": ["turn_uuid"],
        "followUpCount": 1,
        "signalSummary": "Final signal summary."
      }
    ]
  },
  "policyState": {
    "questionCount": 8,
    "followUpCount": 2,
    "minQuestions": 6,
    "minFollowUps": 2,
    "maxQuestions": 12,
    "maxFollowUpsPerCompetency": 2,
    "eligibleToEnd": true
  },
  "uncoveredCompetencyIds": ["competency_uuid"],
  "rationale": "Ending because all competencies are covered.",
  "failureMode": null
}
```

### `sessions.evaluation_narrative`

- Purpose:
  - Stores free-text structured evaluation narrative.
  - Holds summary, strengths, concerns, early-end/model-failure notes, and verdict text.
- Why JSONB:
  - Narrative is read/written as a whole.
  - Numeric/queryable scores are normalized in `session_competency_scores`.
- Query/read pattern:
  - Read whole for evaluation display.
- Confirmed shape:

```json
{
  "schemaVersion": "evaluation_narrative.v1",
  "evaluationVersion": "v1",
  "scoreScale": {"min": 1, "max": 10},
  "summary": "Concise overall evaluation grounded in the transcript.",
  "overallVerdict": "strong | mixed | needs_improvement | insufficient_signal",
  "strengths": [
    {
      "competencyId": "competency_uuid",
      "text": "Specific strength.",
      "turnIds": ["candidate_turn_uuid"]
    }
  ],
  "concerns": [
    {
      "competencyId": "competency_uuid",
      "text": "Specific concern.",
      "turnIds": ["candidate_turn_uuid"]
    }
  ],
  "unassessedCompetencyIds": ["competency_uuid"],
  "earlyEndNote": "Present only when ended early.",
  "modelFailureNote": null,
  "generatedByModel": "model-name-or-null"
}
```

### `turns.reasoning`

- Purpose:
  - Stores per-interviewer-turn decision panel/replay snapshot.
  - Records deterministic rationale, signals, follow-up state, and generation mode.
- Why JSONB:
  - Snapshot read as a whole by panel/replay.
  - Query-critical facts are promoted to columns: `action`, `competency_id`, `source_pack_item_id`.
- Query/read pattern:
  - Read whole for panel/replay.
  - Relational queries use promoted columns.
- Confirmed shape:

```json
{
  "schemaVersion": "turn_reasoning.v1",
  "policyVersion": "v1",
  "rubricSnapshot": {
    "covered": ["competency_uuid"],
    "inProgress": ["competency_uuid"],
    "gaps": ["competency_uuid"],
    "competencies": [
      {
        "id": "competency_uuid",
        "status": "covered",
        "category": "technical",
        "evidenceTurnIds": ["turn_uuid"],
        "followUpCount": 1,
        "signalSummary": "Concrete evidence summary."
      }
    ]
  },
  "flags": [
    {
      "flag": "vague_claim",
      "detail": "Mentioned microservices without tradeoffs.",
      "competencyId": "competency_uuid",
      "triggerTurnId": "candidate_turn_uuid",
      "answerExcerpt": "I split the monolith into services."
    }
  ],
  "policyState": {
    "questionCount": 4,
    "followUpCount": 1,
    "minQuestions": 6,
    "minFollowUps": 2,
    "maxQuestions": 12,
    "maxFollowUpsPerCompetency": 2,
    "followUpCountsByCompetency": {"competency_uuid": 1},
    "eligibleToEnd": false
  },
  "trigger": {
    "turnId": "candidate_turn_uuid",
    "answerExcerpt": "I split the monolith into services.",
    "reason": "vague_claim"
  },
  "rationale": "Following up on System Design because vague_claim was detected.",
  "generation": {
    "mode": "pack_seed | targeted_follow_up | generic_probe | terminal",
    "fallbackMode": null,
    "answerDependencyRequired": true
  },
  "failureMode": null
}
```

### `session_competency_scores.evidence`

- Purpose:
  - Stores supporting evidence for a competency score.
  - Links score rationale to transcript turns, quotes, and signals.
- Why JSONB:
  - Evidence details are read/written as a whole.
  - Queryable score/coverage facts remain columns: `assessed`, `score`.
- Query/read pattern:
  - Read whole for score explanation/evaluation display.
- Confirmed shape:

```json
{
  "schemaVersion": "competency_evidence.v1",
  "evaluationVersion": "v1",
  "coverage": {
    "probed": true,
    "assessed": true,
    "firstQuestionTurnId": "interviewer_turn_uuid",
    "questionTurnIds": ["interviewer_turn_uuid"],
    "answerTurnIds": ["candidate_turn_uuid"]
  },
  "supportingTurnIds": ["candidate_turn_uuid"],
  "quotes": [
    {
      "turnId": "candidate_turn_uuid",
      "quote": "Candidate quote used for score.",
      "type": "strength | concern | neutral",
      "note": "Why this quote matters."
    }
  ],
  "signals": [
    {
      "turnId": "candidate_turn_uuid",
      "flag": "well_covered",
      "detail": "Concrete tradeoff was explained."
    }
  ],
  "scoreRationale": "Why the 1-10 score was assigned.",
  "unassessedReason": null
}
```

## 7. Confirmed Enum / Constraint Decisions

- Enum types:
  - `session_status`: `in_progress`, `completed`, `ended_early`.
  - `completion_reason`: `all_competencies_covered`, `question_cap`, `ended_early`.
  - `turn_role`: `interviewer`, `candidate`.
  - `answer_input_mode`: `voice`, `text`.
  - `policy_action`: `new_topic`, `follow_up`, `end`.
  - `competency_category`: `behavioral`, `technical`.
- Session lifecycle constraints:
  - In-progress sessions cannot have `completed_at` or `completion_reason`.
  - Completed sessions require valid terminal `completion_reason` and `completed_at`.
  - Ended-early sessions require `completion_reason = 'ended_early'` and `completed_at`.
  - `completed_at` cannot be before `started_at`.
- Turn constraints:
  - `turn_index >= 0`.
  - `content` cannot be blank.
  - `audio_duration_ms >= 0` when present.
  - Candidate/interviewer role fields are mutually constrained.
  - Follow-up turns cannot reference a pack item.
  - Pack-source references are only allowed for `new_topic` turns.
- Score constraints:
  - `session_competency_scores.score` is `SMALLINT`.
  - Score range is 1-10.
  - `assessed = false` requires `score IS NULL`.
  - `assessed = true` requires `score IS NOT NULL`.
- JSONB object constraints:
  - `sessions.controller_config` must be a JSON object.
  - `sessions.terminal_panel_state`, `sessions.evaluation_narrative`, `turns.reasoning`, and `session_competency_scores.evidence` must be JSON objects when present.
- Order/index constraints:
  - `jobs.sort_order >= 0`.
  - `competencies.sort_order >= 0`.
  - `question_pack_items.sort_order >= 0`.
  - Deterministic ordering indexes exist for jobs, competencies, question pack items, turns, and owner history.

## 8. Confirmed Controller Persistence Decisions

- Controller guard values are stored in `sessions.controller_config`:
  - `minQuestions = 6`
  - `minFollowUps = 2`
  - `maxQuestions = 12`
  - `maxFollowUpsPerCompetency = 2`
- Deterministic per-turn decisions are evidenced by:
  - `turns.action`
  - `turns.competency_id`
  - `turns.reasoning`
- Terminal end-state is captured in `sessions.terminal_panel_state`.
- Follow-up versus new-topic action is stored in `turns.action`.
- Question-pack source traceability is stored in `turns.source_pack_item_id`.
- Follow-ups never use pack source:
  - `turns.action = 'follow_up'` requires `turns.source_pack_item_id IS NULL`.
- Pack-seeded new-topic turns can reference `turns.source_pack_item_id`.
- Fallback/non-pack cases can leave `source_pack_item_id` null, with fallback context represented in `turns.reasoning.generation`.
- Follow-up trigger persistence:
  - Follow-ups depend on candidate response signals, not only negative flags.
  - Dependency proof is stored in `turns.reasoning.flags`, `turns.reasoning.trigger`, and `turns.reasoning.generation.answerDependencyRequired`.
- Backend controller, not the LLM, owns guard decisions.
- LLM/model output must be validated before JSONB snapshots are persisted.

## 9. Confirmed Analytics / Replay Decisions

- Replay:
  - Reconstruct from ordered `turns` using `turn_index`.
  - Per-turn panel state comes from `turns.reasoning`.
  - Final panel state comes from `sessions.terminal_panel_state`.
- Duration:
  - Derived from `sessions.completed_at - sessions.started_at`.
- Talk ratio:
  - Uses candidate `turns.audio_duration_ms`.
  - Text fallback can use `turns.input_mode` and answer content length in backend/application logic.
- Topic/competency coverage:
  - Derived from `session_competency_scores.assessed`.
- Score trend:
  - Derived from assessed `session_competency_scores.score` values.
  - Scores use integer 1-10 scale.
- Owner-scoped history:
  - Uses `sessions.owner_id`.
  - Indexed by owner/status/time and owner/job/time.
- Follow-up budget counting:
  - Derived from `turns` where `role = 'interviewer' AND action = 'follow_up'`.

## 10. Rejected Design Decisions

- No event-sourcing/event table.
- No separate `question_packs` table.
- No category column on `question_pack_items`.
- No user/auth table.
- No over-normalizing panel/replay/evaluation/evidence snapshots into many child tables.
- No separate persisted aggregate analytics tables.
- No pack source on follow-up turns.

## 11. Backend Implementation Implications

- Alembic should translate `backend/docs/schema.sql` into migrations.
- Seed data must satisfy:
  - at least one `jobs` row set suitable for the home-test job list;
  - `competencies` per job;
  - behavioral and technical coverage through `competencies.category`;
  - `question_pack_items` under competencies.
- Backend controller must populate:
  - promoted columns on `turns`;
  - `turns.reasoning` for interviewer turns;
  - `sessions.terminal_panel_state` for terminal state;
  - `sessions.evaluation_narrative` and `session_competency_scores` on evaluation.
- Tests should verify deterministic policy persistence:
  - minimum questions guard;
  - minimum follow-ups guard;
  - per-competency follow-up cap;
  - follow-up source-pack exclusion;
  - terminal panel persistence.
- Model gateway output must be validated before persisted JSONB snapshots or scores are written.
- Candidate turn retry/idempotency should use `turns.client_turn_id`.

## 12. Explicit Non-Decisions

- No additional non-decisions recorded from confirmed sources.
