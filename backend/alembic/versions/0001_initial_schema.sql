CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TYPE session_status AS ENUM ('in_progress', 'completed', 'ended_early');

CREATE TYPE completion_reason AS ENUM ('all_competencies_covered', 'question_cap', 'ended_early');

CREATE TYPE turn_role AS ENUM ('interviewer', 'candidate');

CREATE TYPE answer_input_mode AS ENUM ('voice', 'text');

CREATE TYPE policy_action AS ENUM ('new_topic', 'follow_up', 'end');

CREATE TYPE competency_category AS ENUM ('behavioral', 'technical');

CREATE TABLE jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title VARCHAR(255) NOT NULL,
  description TEXT NOT NULL,
  sort_order SMALLINT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT uq_jobs_title UNIQUE (title),
  CONSTRAINT ck_jobs_sort_order_nonneg CHECK (sort_order >= 0)
);

CREATE INDEX ix_jobs_sort_order
  ON jobs(sort_order, title);

CREATE TABLE competencies (
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

CREATE INDEX ix_competencies_job_order
  ON competencies(job_id, sort_order, name);

CREATE UNIQUE INDEX ux_competencies_job_id_id
  ON competencies(job_id, id);

CREATE TABLE question_pack_items (
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

CREATE INDEX ix_question_pack_items_competency_order
  ON question_pack_items(competency_id, sort_order, created_at);

CREATE TABLE sessions (
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

CREATE INDEX ix_sessions_job_id
  ON sessions(job_id);

CREATE INDEX ix_sessions_owner_status_started
  ON sessions(owner_id, status, started_at DESC);

CREATE INDEX ix_sessions_owner_job_started
  ON sessions(owner_id, job_id, started_at DESC);

CREATE INDEX ix_sessions_updated_at
  ON sessions(updated_at DESC);

CREATE TABLE turns (
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

CREATE INDEX ix_turns_session_order
  ON turns(session_id, turn_index);

CREATE UNIQUE INDEX ux_turns_session_client_turn
  ON turns(session_id, client_turn_id)
  WHERE client_turn_id IS NOT NULL;

CREATE INDEX ix_turns_session_role_order
  ON turns(session_id, role, turn_index);

CREATE INDEX ix_turns_competency_id
  ON turns(competency_id);

CREATE INDEX ix_turns_source_pack_item_id
  ON turns(source_pack_item_id);

CREATE INDEX ix_turns_session_action
  ON turns(session_id, action);

CREATE INDEX ix_turns_followup_budget
  ON turns(session_id, competency_id)
  WHERE role = 'interviewer' AND action = 'follow_up';

CREATE TABLE session_competency_scores (
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

CREATE INDEX ix_session_competency_scores_session
  ON session_competency_scores(session_id);

CREATE INDEX ix_session_competency_scores_competency
  ON session_competency_scores(competency_id);

CREATE INDEX ix_session_competency_scores_session_assessed
  ON session_competency_scores(session_id, assessed);
