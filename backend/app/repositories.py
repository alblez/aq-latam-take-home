"""Database query helpers for jobs, sessions, and state assembly."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    CompetencyModel,
    JobModel,
    QuestionPackItemModel,
    SessionCompetencyScoreModel,
    SessionModel,
    TurnModel,
)

# --- D-11 session guard primitives ---


class SessionNotInProgressError(Exception):
    """Raised when a turn-writing TX finds the session no longer in_progress (D-11 guard trip).

    The flow layer maps this to the D-12 terminal-shaped 200 (plan 07-08).
    """

    def __init__(self, *, session_id: UUID, status: str | None) -> None:
        self.session_id = session_id
        self.status = status
        super().__init__(
            f"Session {session_id} guard trip: status={status!r} (expected 'in_progress')"
        )


def lock_session_for_write(db: Session, *, session_id: UUID) -> SessionModel | None:
    """Acquire FOR NO KEY UPDATE row lock on a session.

    Uses `with_for_update(key_share=True)` which emits `FOR NO KEY UPDATE` on
    PostgreSQL. This flavor:
    - Does NOT conflict with FK-checking `FOR KEY SHARE` locks taken by `turns`
      inserts (so concurrent candidate writes to the SAME session are not blocked
      on the parent row FK check).
    - DOES mutually exclude other `FOR NO KEY UPDATE` / `FOR UPDATE` holders,
      serializing guard-holding writers.

    Must be called inside a short transaction. Caller commits or rolls back promptly.
    NEVER hold across a gateway call (D-10/D25).
    """
    stmt = (
        select(SessionModel)
        .where(SessionModel.id == session_id)
        .with_for_update(key_share=True)
        .execution_options(populate_existing=True)
    )
    return db.scalars(stmt).first()


def guard_session_in_progress(db: Session, *, session_id: UUID) -> SessionModel:
    """Lock session row and verify status='in_progress'. D-11 guard.

    MUST be the FIRST statement of every turn-writing transaction.
    On trip (row missing or status != 'in_progress'): rolls back to release the
    lock immediately, then raises SessionNotInProgressError.

    Contract:
    - Caller commits promptly after writes.
    - Guard MUST NEVER be held across a gateway call (D-10/D25).
    """
    row = lock_session_for_write(db, session_id=session_id)
    if row is None or row.status != "in_progress":
        # Capture status BEFORE rollback — rollback expires ORM attributes,
        # and a post-rollback attribute access would trigger autobegin.
        observed_status = row.status if row else None
        db.rollback()
        raise SessionNotInProgressError(
            session_id=session_id,
            status=observed_status,
        )
    return row


def list_jobs_with_counts(db: Session) -> list[tuple[JobModel, int]]:
    """List jobs with live competency counts, excluding zero-competency jobs.

    Returns jobs ordered by sort_order ASC, title ASC.
    Only jobs with at least one competency are returned (per D-04).
    """
    stmt = (
        select(JobModel, func.count(CompetencyModel.id).label("comp_count"))
        .outerjoin(CompetencyModel, CompetencyModel.job_id == JobModel.id)
        .group_by(JobModel.id)
        .having(func.count(CompetencyModel.id) > 0)
        .order_by(JobModel.sort_order.asc(), JobModel.title.asc())
    )
    rows = db.execute(stmt).all()
    return [(row[0], row[1]) for row in rows]


def get_job_with_competency_count(db: Session, job_id: UUID) -> tuple[JobModel, int] | None:
    """Fetch a single job with its competency count. Returns None if not found."""
    stmt = (
        select(JobModel, func.count(CompetencyModel.id).label("comp_count"))
        .outerjoin(CompetencyModel, CompetencyModel.job_id == JobModel.id)
        .where(JobModel.id == job_id)
        .group_by(JobModel.id)
    )
    row = db.execute(stmt).first()
    if row is None:
        return None
    return (row[0], row[1])


def create_session(
    db: Session,
    owner_id: UUID,
    job_id: UUID,
    controller_config: dict,
) -> SessionModel:
    """Insert a new session row with in_progress status."""
    now = datetime.now(UTC)
    session_model = SessionModel(
        id=uuid.uuid4(),
        job_id=job_id,
        owner_id=owner_id,
        status="in_progress",
        started_at=now,
        updated_at=now,
        controller_config=controller_config,
    )
    db.add(session_model)
    db.commit()
    db.refresh(session_model)
    return session_model


def get_session_for_owner(db: Session, session_id: UUID, owner_id: UUID) -> SessionModel | None:
    """Fetch session by ID filtered by owner. Returns None for wrong owner or missing."""
    stmt = select(SessionModel).where(
        SessionModel.id == session_id,
        SessionModel.owner_id == owner_id,
    )
    return db.scalars(stmt).first()


def get_session_state_data(db: Session, session_id: UUID) -> dict | None:
    """Fetch session + job title + turns + competencies for state assembly."""
    session = db.scalars(select(SessionModel).where(SessionModel.id == session_id)).first()
    if session is None:
        return None

    job = db.scalars(select(JobModel).where(JobModel.id == session.job_id)).first()
    if job is None:
        return None

    turns = db.scalars(
        select(TurnModel)
        .where(TurnModel.session_id == session_id)
        .order_by(TurnModel.turn_index.asc())
    ).all()

    competencies = db.scalars(
        select(CompetencyModel)
        .where(CompetencyModel.job_id == session.job_id)
        .order_by(CompetencyModel.sort_order.asc(), CompetencyModel.name.asc())
    ).all()

    return {
        "session": session,
        "job": job,
        "turns": list(turns),
        "competencies": list(competencies),
    }


# --- Start-specific queries ---


def select_first_question_data(
    db: Session, job_id: UUID
) -> tuple[CompetencyModel, QuestionPackItemModel] | None:
    """Select first competency (lowest sort_order) and its first pack item.

    Per D-14: deterministic selection by competencies.sort_order ASC,
    then question_pack_items.sort_order ASC.
    Returns None if job has no competencies or first competency has no pack items.
    """
    first_comp = db.scalars(
        select(CompetencyModel)
        .where(CompetencyModel.job_id == job_id)
        .order_by(CompetencyModel.sort_order.asc(), CompetencyModel.name.asc())
        .limit(1)
    ).first()
    if first_comp is None:
        return None

    first_item = db.scalars(
        select(QuestionPackItemModel)
        .where(QuestionPackItemModel.competency_id == first_comp.id)
        .order_by(QuestionPackItemModel.sort_order.asc())
        .limit(1)
    ).first()
    if first_item is None:
        return None

    return (first_comp, first_item)


def get_first_interviewer_turn(db: Session, session_id: UUID) -> TurnModel | None:
    """Get the first interviewer turn (turn_index=0) for a session."""
    stmt = select(TurnModel).where(
        TurnModel.session_id == session_id,
        TurnModel.turn_index == 0,
        TurnModel.role == "interviewer",
    )
    return db.scalars(stmt).first()


def insert_first_interviewer_turn(
    db: Session,
    session_id: UUID,
    competency_id: UUID,
    content: str,
    action: str,
    source_pack_item_id: UUID,
    reasoning: dict,
) -> TurnModel:
    """Insert first interviewer turn with turn_index=0.

    Per D-15, D-16: persists immediately with action and source_pack_item_id.
    """
    now = datetime.now(UTC)
    turn = TurnModel(
        id=uuid.uuid4(),
        session_id=session_id,
        turn_index=0,
        role="interviewer",
        competency_id=competency_id,
        content=content,
        action=action,
        source_pack_item_id=source_pack_item_id,
        reasoning=reasoning,
        created_at=now,
    )
    db.add(turn)
    db.flush()
    return turn


def update_session_updated_at(db: Session, session_id: UUID) -> None:
    """Update sessions.updated_at to now. Per D-08."""
    now = datetime.now(UTC)
    session = db.scalars(select(SessionModel).where(SessionModel.id == session_id)).first()
    if session:
        session.updated_at = now


# --- Engine pipeline helpers (Plan 06-05) ---


def insert_interviewer_turn(
    db: Session,
    *,
    session_id: UUID,
    turn_index: int,
    competency_id: UUID,
    content: str,
    action: str,
    source_pack_item_id: UUID | None,
    reasoning: dict,
) -> TurnModel:
    """Insert an interviewer turn at any index. Per D-02: generalizes first-turn helper.

    Caller commits. Uses uuid4() per PATTERNS.md.
    """
    now = datetime.now(UTC)
    turn = TurnModel(
        id=uuid.uuid4(),
        session_id=session_id,
        turn_index=turn_index,
        role="interviewer",
        competency_id=competency_id,
        content=content,
        action=action,
        source_pack_item_id=source_pack_item_id,
        reasoning=reasoning,
        created_at=now,
    )
    db.add(turn)
    db.flush()
    return turn


def insert_candidate_turn(
    db: Session,
    *,
    session_id: UUID,
    turn_index: int,
    competency_id: UUID,
    content: str,
    client_turn_id: UUID | None = None,
    input_mode: str = "text",
    audio_duration_ms: int | None = None,
) -> TurnModel:
    """Insert a candidate turn. Per schema: role=candidate, action/reasoning/source NULL.

    Caller commits. Uses uuid4() per PATTERNS.md.
    """
    now = datetime.now(UTC)
    turn = TurnModel(
        id=uuid.uuid4(),
        session_id=session_id,
        turn_index=turn_index,
        role="candidate",
        competency_id=competency_id,
        content=content,
        client_turn_id=client_turn_id,
        input_mode=input_mode,
        audio_duration_ms=audio_duration_ms,
        action=None,
        source_pack_item_id=None,
        reasoning=None,
        created_at=now,
    )
    db.add(turn)
    db.flush()
    return turn


def select_pack_item_for_competency(
    db: Session,
    *,
    session_id: UUID,
    competency_id: UUID,
) -> QuestionPackItemModel | None:
    """Select first unused pack item for a competency in this session.

    Per D-14: lowest sort_order among items NOT already referenced by this
    session's turns.source_pack_item_id. Returns None when exhausted.
    """
    used_ids_subq = (
        select(TurnModel.source_pack_item_id)
        .where(
            TurnModel.session_id == session_id,
            TurnModel.source_pack_item_id.isnot(None),
        )
        .scalar_subquery()
    )
    stmt = (
        select(QuestionPackItemModel)
        .where(
            QuestionPackItemModel.competency_id == competency_id,
            QuestionPackItemModel.id.notin_(used_ids_subq),
        )
        .order_by(QuestionPackItemModel.sort_order.asc())
        .limit(1)
    )
    return db.scalars(stmt).first()


def set_model_name_once(db: Session, *, session_id: UUID, model_name: str) -> None:
    """Write-once model_name on session. Per D-05: no-op when already set.

    Caller commits.
    """
    session = db.scalars(select(SessionModel).where(SessionModel.id == session_id)).first()
    if session and session.model_name is None:
        session.model_name = model_name


def finalize_session_terminal(
    db: Session,
    *,
    session_id: UUID,
    completion_reason: str,
    terminal_panel_state: dict,
    completed_at: datetime,
    status: Literal["completed", "ended_early"] = "completed",
    evaluation_narrative: dict | None = None,
) -> None:
    """Single-update terminal finalization. Per D-04, Pitfall 11.

    Sets status, completion_reason, completed_at, terminal_panel_state,
    updated_at together in one flush. Optionally persists evaluation_narrative
    in the same transaction when provided. Caller commits.

    ck_sessions_lifecycle pairing rules:
    - status='completed' requires completion_reason in ('all_competencies_covered', 'question_cap')
    - status='ended_early' requires completion_reason='ended_early' and completed_at IS NOT NULL
    """
    session = db.scalars(select(SessionModel).where(SessionModel.id == session_id)).first()
    if session is None:
        msg = f"Session {session_id} not found for terminal finalization"
        raise ValueError(msg)
    session.status = status
    session.completion_reason = completion_reason
    session.completed_at = completed_at
    session.terminal_panel_state = terminal_panel_state
    session.updated_at = completed_at
    if evaluation_narrative is not None:
        session.evaluation_narrative = evaluation_narrative
    db.flush()


# --- Idempotency & Recovery helpers (Plan 07-02) ---


def get_candidate_turn_by_client_turn_id(
    db: Session, session_id: UUID, client_turn_id: UUID
) -> TurnModel | None:
    """Lookup existing candidate turn by clientTurnId within a session.

    Per D-01: enables same-clientTurnId idempotency check.
    """
    stmt = select(TurnModel).where(
        TurnModel.session_id == session_id,
        TurnModel.client_turn_id == client_turn_id,
        TurnModel.role == "candidate",
    )
    return db.scalars(stmt).first()


def get_following_interviewer_turn(
    db: Session, session_id: UUID, after_turn_index: int
) -> TurnModel | None:
    """Get the interviewer turn immediately following a given turn_index.

    Per D-05: used to determine if a candidate turn's pipeline completed.
    """
    stmt = (
        select(TurnModel)
        .where(
            TurnModel.session_id == session_id,
            TurnModel.turn_index > after_turn_index,
            TurnModel.role == "interviewer",
        )
        .order_by(TurnModel.turn_index.asc())
        .limit(1)
    )
    return db.scalars(stmt).first()


def get_latest_turn(db: Session, session_id: UUID) -> TurnModel | None:
    """Get the turn with highest turn_index for a session."""
    stmt = (
        select(TurnModel)
        .where(TurnModel.session_id == session_id)
        .order_by(TurnModel.turn_index.desc())
        .limit(1)
    )
    return db.scalars(stmt).first()


# --- Evaluation persistence helpers (Plan 08-01) ---


@dataclass(frozen=True, slots=True)
class CompetencyScoreRowData:
    """Immutable input for batch score-row persistence."""

    session_id: UUID
    competency_id: UUID
    assessed: bool
    score: int | None
    notes: str | None
    evidence_dict: dict | None


def insert_competency_scores(db: Session, *, rows: list[CompetencyScoreRowData]) -> None:
    """Batch insert score rows for a session. One flush for all rows.

    Caller commits. DB constraints enforce score_range, score_assessed, and uniqueness.
    """
    for row in rows:
        model = SessionCompetencyScoreModel(
            id=uuid.uuid4(),
            session_id=row.session_id,
            competency_id=row.competency_id,
            assessed=row.assessed,
            score=row.score,
            notes=row.notes,
            evidence=row.evidence_dict,
            created_at=datetime.now(UTC),
        )
        db.add(model)
    db.flush()


def get_competency_scores(db: Session, *, session_id: UUID) -> list[SessionCompetencyScoreModel]:
    """Read score rows for a session, ordered by competency sort_order for stable output.

    Joins competencies to get deterministic ordering.
    """
    stmt = (
        select(SessionCompetencyScoreModel)
        .join(
            CompetencyModel,
            CompetencyModel.id == SessionCompetencyScoreModel.competency_id,
        )
        .where(SessionCompetencyScoreModel.session_id == session_id)
        .order_by(CompetencyModel.sort_order.asc(), CompetencyModel.name.asc())
    )
    return list(db.scalars(stmt).all())


def has_complete_evaluation(db: Session, *, session_id: UUID, job_id: UUID) -> bool:
    """D-33: evaluation is complete when narrative exists AND score count == competency count > 0.

    Returns False for any partial state (no narrative, fewer rows, or zero competencies).
    """
    # Check narrative existence
    session = db.scalars(select(SessionModel).where(SessionModel.id == session_id)).first()
    if session is None or session.evaluation_narrative is None:
        return False

    # Count competencies for this job
    comp_count: int = (
        db.scalar(select(func.count(CompetencyModel.id)).where(CompetencyModel.job_id == job_id))
        or 0
    )
    if comp_count == 0:
        return False

    # Count score rows for this session
    score_count: int = (
        db.scalar(
            select(func.count(SessionCompetencyScoreModel.id)).where(
                SessionCompetencyScoreModel.session_id == session_id
            )
        )
        or 0
    )

    return score_count == comp_count


def get_evaluation_detail(db: Session, session_id: UUID) -> dict | None:
    """Fetch session + job + turns + competencies + scores for evaluation assembly.

    Returns None when session not found. Extends get_session_state_data pattern.
    """
    session = db.scalars(select(SessionModel).where(SessionModel.id == session_id)).first()
    if session is None:
        return None

    job = db.scalars(select(JobModel).where(JobModel.id == session.job_id)).first()
    if job is None:
        return None

    turns = list(
        db.scalars(
            select(TurnModel)
            .where(TurnModel.session_id == session_id)
            .order_by(TurnModel.turn_index.asc())
        ).all()
    )

    competencies = list(
        db.scalars(
            select(CompetencyModel)
            .where(CompetencyModel.job_id == session.job_id)
            .order_by(CompetencyModel.sort_order.asc(), CompetencyModel.name.asc())
        ).all()
    )

    scores = get_competency_scores(db, session_id=session_id)

    return {
        "session": session,
        "job": job,
        "turns": turns,
        "competencies": competencies,
        "scores": scores,
    }
