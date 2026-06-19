-- Backend database schema reference for the AI Interviewer Platform.
--
-- Adjudication summary:
--   * Keep the six-table competency-spine model required by the project spec.
--   * Promote query-critical controller facts out of JSONB: policy_action,
--     source_pack_item_id, input_mode, client_turn_id, completion_reason.
--   * Keep full panel/evaluation snapshots in JSONB because replay reads them
--     whole and interviews are small.
--   * Avoid event-sourcing tables; too much surface area for the home test.
--   * Keep behavioral/technical split on competencies only. Pack items inherit
--     category through their parent competency to avoid duplicate truths.
--
-- This is the backend schema reference to translate into Alembic migrations.
-- It is idempotent-ish for local inspection, but not intended as an app-start
-- migration script or a substitute for explicit migration/deployment steps.

-- ============================================================
-- EXTENSIONS
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto"; -- gen_random_uuid()

-- ============================================================
-- ENUM TYPES
-- ============================================================

DO $$
BEGIN
  CREATE TYPE session_status AS ENUM ('in_progress', 'completed', 'ended_early');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
  CREATE TYPE completion_reason AS ENUM ('all_competencies_covered', 'question_cap', 'ended_early');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
  CREATE TYPE turn_role AS ENUM ('interviewer', 'candidate');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
  CREATE TYPE answer_input_mode AS ENUM ('voice', 'text');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
  CREATE TYPE policy_action AS ENUM ('new_topic', 'follow_up', 'end');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
  CREATE TYPE competency_category AS ENUM ('behavioral', 'technical');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ============================================================
-- jobs
-- ============================================================
-- Seeded job roles shown on the landing page. sort_order makes the list
-- deterministic for UI and tests.

CREATE TABLE IF NOT EXISTS jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title VARCHAR(255) NOT NULL,
  description TEXT NOT NULL,
  sort_order SMALLINT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT uq_jobs_title UNIQUE (title),
  CONSTRAINT ck_jobs_sort_order_nonneg CHECK (sort_order >= 0)
);

CREATE INDEX IF NOT EXISTS ix_jobs_sort_order
  ON jobs(sort_order, title);

-- ============================================================
-- competencies
-- ============================================================
-- The rubric spine. Jobs, controller state, question pack seeds,
-- evaluation rows, decision panel, replay, and analytics all join here.

CREATE TABLE IF NOT EXISTS competencies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  category competency_category NOT NULL,
  description TEXT NOT NULL,
  sort_order SMALLINT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT uq_competencies_job_name UNIQUE (job_id, name),
  CONSTRAINT ck_competencies_sort_order_nonneg CHECK (sort_order >= 0)
);

CREATE INDEX IF NOT EXISTS ix_competencies_job_order
  ON competencies(job_id, sort_order, name);

-- Composite unique key lets downstream tables enforce "same job" in later
-- migrations if desired without changing this table's logical model.
CREATE UNIQUE INDEX IF NOT EXISTS ux_competencies_job_id_id
  ON competencies(job_id, id);

-- ============================================================
-- question_pack_items
-- ============================================================
-- Pack items hang off competencies, not jobs. They are opener seeds for the
-- LLM to rephrase; follow-ups are generated from candidate answers and never
-- use a pack item.
--
-- Behavioral/technical category is inherited from the parent competency. This
-- keeps question packs simple: a job-specific pack is the ordered set of pack
-- items under that job's behavioral and technical competencies.

CREATE TABLE IF NOT EXISTS question_pack_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  competency_id UUID NOT NULL REFERENCES competencies(id) ON DELETE CASCADE,
  prompt_text TEXT NOT NULL,
  sort_order SMALLINT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT uq_question_pack_items_competency_prompt
    UNIQUE (competency_id, prompt_text),
  CONSTRAINT ck_question_pack_items_sort_order_nonneg
    CHECK (sort_order >= 0),
  CONSTRAINT ck_question_pack_items_prompt_not_blank
    CHECK (length(btrim(prompt_text)) > 0)
);

CREATE INDEX IF NOT EXISTS ix_question_pack_items_competency_order
  ON question_pack_items(competency_id, sort_order, created_at);

-- ============================================================
-- sessions
-- ============================================================
-- owner_id is anonymous localStorage UUID. No users table by design.
-- controller_config freezes policy knobs for deterministic replay after code
-- changes. terminal_panel_state captures the final action=end panel if no
-- interviewer turn is created for the ending decision.

CREATE TABLE IF NOT EXISTS sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE RESTRICT,
  owner_id UUID NOT NULL,
  status session_status NOT NULL DEFAULT 'in_progress',
  completion_reason completion_reason,
  model_name TEXT,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  controller_config JSONB NOT NULL DEFAULT
    '{"policyVersion":"v1","minQuestions":6,"minFollowUps":2,"maxQuestions":12,"maxFollowUpsPerCompetency":2}'::jsonb,
  terminal_panel_state JSONB,
  evaluation_narrative JSONB,

  CONSTRAINT ck_sessions_time_order
    CHECK (completed_at IS NULL OR completed_at >= started_at),
  CONSTRAINT ck_sessions_lifecycle
    CHECK (
      (
        status = 'in_progress'
        AND completed_at IS NULL
        AND completion_reason IS NULL
      )
      OR (
        status = 'completed'
        AND completed_at IS NOT NULL
        AND completion_reason IN ('all_competencies_covered', 'question_cap')
      )
      OR (
        status = 'ended_early'
        AND completed_at IS NOT NULL
        AND completion_reason = 'ended_early'
      )
    ),
  CONSTRAINT ck_sessions_controller_config_object
    CHECK (jsonb_typeof(controller_config) = 'object'),
  CONSTRAINT ck_sessions_terminal_panel_object
    CHECK (terminal_panel_state IS NULL OR jsonb_typeof(terminal_panel_state) = 'object'),
  CONSTRAINT ck_sessions_evaluation_object
    CHECK (evaluation_narrative IS NULL OR jsonb_typeof(evaluation_narrative) = 'object')
);

CREATE INDEX IF NOT EXISTS ix_sessions_job_id
  ON sessions(job_id);

CREATE INDEX IF NOT EXISTS ix_sessions_owner_status_started
  ON sessions(owner_id, status, started_at DESC);

CREATE INDEX IF NOT EXISTS ix_sessions_owner_job_started
  ON sessions(owner_id, job_id, started_at DESC);

CREATE INDEX IF NOT EXISTS ix_sessions_updated_at
  ON sessions(updated_at DESC);

-- JSONB shapes used by application code:
--
-- sessions.controller_config:
-- {
--   "policyVersion": "v1",
--   "minQuestions": 6,
--   "minFollowUps": 2,
--   "maxQuestions": 12,
--   "maxFollowUpsPerCompetency": 2
-- }
--
-- sessions.terminal_panel_state: final decision-panel snapshot. This is for
-- replay/display only; sessions.status and sessions.completion_reason remain
-- authoritative for lifecycle queries.
-- {
--   "schemaVersion": "terminal_panel_state.v1",
--   "policyVersion": "v1",
--   "action": "end",
--   "completionReason": "all_competencies_covered | question_cap | ended_early",
--   "endedBy": "controller | user",
--   "rubricSnapshot": {
--     "covered": ["competency_uuid"],
--     "inProgress": [],
--     "gaps": ["competency_uuid"],
--     "competencies": [
--       {
--         "id": "competency_uuid",
--         "status": "covered | in-progress | not-reached",
--         "category": "behavioral | technical",
--         "evidenceTurnIds": ["turn_uuid"],
--         "followUpCount": 1,
--         "signalSummary": "Final signal summary."
--       }
--     ]
--   },
--   "policyState": {
--     "questionCount": 8,
--     "followUpCount": 2,
--     "minQuestions": 6,
--     "minFollowUps": 2,
--     "maxQuestions": 12,
--     "maxFollowUpsPerCompetency": 2,
--     "eligibleToEnd": true
--   },
--   "uncoveredCompetencyIds": ["competency_uuid"],
--   "rationale": "Ending because all competencies are covered.",
--   "failureMode": null
-- }
--
-- sessions.evaluation_narrative: free-text evaluation read as a whole. Numeric
-- scores are NOT authoritative here; compute overall score from
-- session_competency_scores.score where assessed=true.
-- {
--   "schemaVersion": "evaluation_narrative.v1",
--   "evaluationVersion": "v1",
--   "scoreScale": {"min": 1, "max": 10},
--   "summary": "Concise overall evaluation grounded in the transcript.",
--   "overallVerdict": "strong | mixed | needs_improvement | insufficient_signal",
--   "strengths": [
--     {
--       "competencyId": "competency_uuid",
--       "text": "Specific strength.",
--       "turnIds": ["candidate_turn_uuid"]
--     }
--   ],
--   "concerns": [
--     {
--       "competencyId": "competency_uuid",
--       "text": "Specific concern.",
--       "turnIds": ["candidate_turn_uuid"]
--     }
--   ],
--   "unassessedCompetencyIds": ["competency_uuid"],
--   "earlyEndNote": "Present only when ended early.",
--   "modelFailureNote": null,
--   "generatedByModel": "model-name-or-null"
-- }

-- ============================================================
-- turns
-- ============================================================
-- Ordered transcript rows. Candidate and interviewer rows both carry the
-- competency being probed so resume, follow-up counts, analytics, and replay do
-- not infer target competency from JSONB. Full reasoning snapshots remain JSONB
-- because replay reads them as a whole. client_turn_id is supplied by the
-- frontend on answer submission so retries/double-clicks do not create duplicate
-- candidate answers.

CREATE TABLE IF NOT EXISTS turns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  client_turn_id UUID,
  turn_index INTEGER NOT NULL,
  role turn_role NOT NULL,
  competency_id UUID NOT NULL REFERENCES competencies(id) ON DELETE RESTRICT,
  content TEXT NOT NULL,
  input_mode answer_input_mode,
  audio_duration_ms INTEGER,
  action policy_action,
  source_pack_item_id UUID REFERENCES question_pack_items(id) ON DELETE RESTRICT,
  reasoning JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT uq_turns_session_turn_index
    UNIQUE (session_id, turn_index),
  CONSTRAINT ck_turns_turn_index_nonneg
    CHECK (turn_index >= 0),
  CONSTRAINT ck_turns_content_not_blank
    CHECK (length(btrim(content)) > 0),
  CONSTRAINT ck_turns_audio_duration_nonneg
    CHECK (audio_duration_ms IS NULL OR audio_duration_ms >= 0),
  CONSTRAINT ck_turns_role_fields
    CHECK (
      (
        role = 'candidate'
        AND client_turn_id IS NOT NULL
        AND input_mode IS NOT NULL
        AND action IS NULL
        AND source_pack_item_id IS NULL
        AND reasoning IS NULL
      )
      OR (
        role = 'interviewer'
        AND client_turn_id IS NULL
        AND input_mode IS NULL
        AND audio_duration_ms IS NULL
        AND action IS NOT NULL
        AND reasoning IS NOT NULL
      )
    ),
  CONSTRAINT ck_turns_followup_has_no_pack
    CHECK (action IS NULL OR action <> 'follow_up' OR source_pack_item_id IS NULL),
  CONSTRAINT ck_turns_new_topic_can_have_pack
    CHECK (source_pack_item_id IS NULL OR action = 'new_topic'),
  CONSTRAINT ck_turns_reasoning_object
    CHECK (reasoning IS NULL OR jsonb_typeof(reasoning) = 'object')
);

CREATE INDEX IF NOT EXISTS ix_turns_session_order
  ON turns(session_id, turn_index);

CREATE UNIQUE INDEX IF NOT EXISTS ux_turns_session_client_turn
  ON turns(session_id, client_turn_id)
  WHERE client_turn_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_turns_session_role_order
  ON turns(session_id, role, turn_index);

CREATE INDEX IF NOT EXISTS ix_turns_competency_id
  ON turns(competency_id);

CREATE INDEX IF NOT EXISTS ix_turns_source_pack_item_id
  ON turns(source_pack_item_id);

CREATE INDEX IF NOT EXISTS ix_turns_session_action
  ON turns(session_id, action);

CREATE INDEX IF NOT EXISTS ix_turns_followup_budget
  ON turns(session_id, competency_id)
  WHERE role = 'interviewer' AND action = 'follow_up';

-- turns.reasoning stores display/replay data, while action,
-- targetCompetencyId, and sourcePackItemId are authoritative columns and are
-- assembled into the API PanelState by backend code. Candidate turns keep
-- reasoning NULL; interviewer turns require it.
--
-- turns.reasoning:
-- {
--   "schemaVersion": "turn_reasoning.v1",
--   "policyVersion": "v1",
--   "rubricSnapshot": {
--     "covered": ["competency_uuid"],
--     "inProgress": ["competency_uuid"],
--     "gaps": ["competency_uuid"],
--     "competencies": [
--       {
--         "id": "competency_uuid",
--         "status": "covered",
--         "category": "technical",
--         "evidenceTurnIds": ["turn_uuid"],
--         "followUpCount": 1,
--         "signalSummary": "Concrete evidence summary."
--       }
--     ]
--   },
--   "flags": [
--     {
--       "flag": "vague_claim",
--       "detail": "Mentioned microservices without tradeoffs.",
--       "competencyId": "competency_uuid",
--       "triggerTurnId": "candidate_turn_uuid",
--       "answerExcerpt": "I split the monolith into services."
--     }
--   ],
--   "policyState": {
--     "questionCount": 4,
--     "followUpCount": 1,
--     "minQuestions": 6,
--     "minFollowUps": 2,
--     "maxQuestions": 12,
--     "maxFollowUpsPerCompetency": 2,
--     "followUpCountsByCompetency": {"competency_uuid": 1},
--     "eligibleToEnd": false
--   },
--   "trigger": {
--     "turnId": "candidate_turn_uuid",
--     "answerExcerpt": "I split the monolith into services.",
--     "reason": "vague_claim"
--   },
--   "rationale": "Following up on System Design because vague_claim was detected.",
--   "generation": {
--     "mode": "pack_seed | targeted_follow_up | generic_probe | terminal",
--     "fallbackMode": null,
--     "answerDependencyRequired": true
--   },
--   "failureMode": null
-- }

-- ============================================================
-- session_competency_scores
-- ============================================================
-- One row per session per competency. Queryable whole-number scores and
-- assessed flags live here; free-text narrative stays whole in
-- sessions.evaluation_narrative. The model should be asked for an integer 1-10
-- directly; do not ask for decimals and round after the fact.

CREATE TABLE IF NOT EXISTS session_competency_scores (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  competency_id UUID NOT NULL REFERENCES competencies(id) ON DELETE RESTRICT,
  assessed BOOLEAN NOT NULL DEFAULT false,
  score SMALLINT,
  notes TEXT,
  evidence JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT uq_session_competency_scores
    UNIQUE (session_id, competency_id),
  CONSTRAINT ck_session_competency_scores_score_range
    CHECK (score IS NULL OR (score BETWEEN 1 AND 10)),
  CONSTRAINT ck_session_competency_scores_score_assessed
    CHECK (
      (assessed = true AND score IS NOT NULL)
      OR
      (assessed = false AND score IS NULL)
    ),
  CONSTRAINT ck_session_competency_scores_evidence_object
    CHECK (evidence IS NULL OR jsonb_typeof(evidence) = 'object')
);

CREATE INDEX IF NOT EXISTS ix_session_competency_scores_session
  ON session_competency_scores(session_id);

CREATE INDEX IF NOT EXISTS ix_session_competency_scores_competency
  ON session_competency_scores(competency_id);

CREATE INDEX IF NOT EXISTS ix_session_competency_scores_session_assessed
  ON session_competency_scores(session_id, assessed);

-- session_competency_scores.evidence:
-- {
--   "schemaVersion": "competency_evidence.v1",
--   "evaluationVersion": "v1",
--   "coverage": {
--     "probed": true,
--     "assessed": true,
--     "firstQuestionTurnId": "interviewer_turn_uuid",
--     "questionTurnIds": ["interviewer_turn_uuid"],
--     "answerTurnIds": ["candidate_turn_uuid"]
--   },
--   "supportingTurnIds": ["candidate_turn_uuid"],
--   "quotes": [
--     {
--       "turnId": "candidate_turn_uuid",
--       "quote": "Candidate quote used for score.",
--       "type": "strength | concern | neutral",
--       "note": "Why this quote matters."
--     }
--   ],
--   "signals": [
--     {
--       "turnId": "candidate_turn_uuid",
--       "flag": "well_covered",
--       "detail": "Concrete tradeoff was explained."
--     }
--   ],
--   "scoreRationale": "Why the 1-10 score was assigned.",
--   "unassessedReason": null
-- }

-- ============================================================
-- RELATIONSHIP / QUERY NOTES
-- ============================================================
-- jobs 1 -> many competencies
-- competencies 1 -> many question_pack_items
-- jobs 1 -> many sessions
-- sessions 1 -> many turns
-- sessions 1 -> many session_competency_scores
-- competencies 1 -> many turns and session_competency_scores
-- question_pack_items 1 -> many turns through source_pack_item_id
--
-- Delete behavior:
--   * Delete sessions to remove interview transcript/evaluation.
--   * Do not delete seed jobs/competencies once sessions exist; RESTRICT on
--     historical references preserves replay integrity.
--   * question_pack_items are RESTRICTed when used by turns so traceability is
--     not silently erased. Disable old seeds in application seed data rather
--     than deleting them after interviews exist.
--
-- Common analytics are derived, not persisted:
--   * duration: sessions.completed_at - sessions.started_at
--   * talk ratio: SUM(candidate audio_duration_ms) / duration, with text-length
--     fallback in application SQL when input_mode = 'text'
--   * coverage: COUNT(assessed) / COUNT(*) from session_competency_scores
--   * score trend: AVG(score) where assessed = true, ordered by started_at
