"""History detail assembly — derived metrics at read time.

Assembles HistoryResponse from DB state, deriving all 6 analytics metrics
per session at query time (no persisted aggregates):
- durationMs (D-02): completed_at - started_at in milliseconds
- overallScore (D-03/D-06): average assessed scores, null if incomplete
- coveragePercent (D-01/D-06): assessed/total ratio 0-1, null if incomplete
- talkRatio (D-07 through D-11): three-branch formula (audio/text/mixed)
- questionCount (D-04): interviewer turn count
- followUpCount (D-05): interviewer turns with action='follow_up'
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.engine.evaluation import derive_overall_score
from app.models import (
    CompetencyModel,
    JobModel,
    SessionCompetencyScoreModel,
    SessionModel,
    TurnModel,
)
from app.schemas import HistoryResponse, SessionSummary


def assemble_history_response(
    db: Session, owner_id: UUID, job_id: UUID | None = None
) -> HistoryResponse:
    """Build HistoryResponse from DB for an owner's terminal sessions.

    Derives all 6 metrics per session at query time. Fixed 50-session cap (T-09-07).
    """
    sessions = get_owner_terminal_sessions(db, owner_id, job_id=job_id)
    if not sessions:
        return HistoryResponse(sessions=[])

    session_ids = [s.id for s in sessions]

    # Batch-load turns for all sessions (avoid N+1)
    all_turns = list(
        db.scalars(
            select(TurnModel)
            .where(TurnModel.session_id.in_(session_ids))
            .order_by(TurnModel.turn_index.asc())
        ).all()
    )
    turns_by_session: dict[UUID, list[Any]] = {}
    for t in all_turns:
        turns_by_session.setdefault(t.session_id, []).append(t)

    # Batch-load scores for all sessions
    all_scores = list(
        db.scalars(
            select(SessionCompetencyScoreModel).where(
                SessionCompetencyScoreModel.session_id.in_(session_ids)
            )
        ).all()
    )
    scores_by_session: dict[UUID, list[Any]] = {}
    for s in all_scores:
        scores_by_session.setdefault(s.session_id, []).append(s)

    # Batch competency counts per job (review concern 8)
    job_ids = list({s.job_id for s in sessions})
    comp_counts_raw = db.execute(
        select(CompetencyModel.job_id, func.count(CompetencyModel.id))
        .where(CompetencyModel.job_id.in_(job_ids))
        .group_by(CompetencyModel.job_id)
    ).all()
    comp_counts: dict[UUID, int] = {row[0]: row[1] for row in comp_counts_raw}

    # Batch job titles per job (eliminates object_session introspection per WR-02)
    job_titles_raw = db.execute(
        select(JobModel.id, JobModel.title).where(JobModel.id.in_(job_ids))
    ).all()
    job_titles: dict[UUID, str] = {row[0]: row[1] for row in job_titles_raw}

    summaries: list[SessionSummary] = []
    for sess in sessions:
        turns = turns_by_session.get(sess.id, [])
        scores = scores_by_session.get(sess.id, [])
        total_comps = comp_counts.get(sess.job_id, 0)
        job_title = job_titles.get(sess.job_id, "")
        summaries.append(_session_to_summary(sess, turns, scores, total_comps, job_title))

    return HistoryResponse(sessions=summaries)


def get_owner_terminal_sessions(
    db: Session, owner_id: UUID, *, job_id: UUID | None = None, limit: int = 50
) -> list[SessionModel]:
    """Query terminal sessions for an owner, ordered newest first.

    Filters: status IN ('completed', 'ended_early'), owner_id match.
    Optional jobId filter. Fixed 50-session server-side cap (T-09-07).
    Ordering: completed_at DESC, started_at DESC, id (stable tie-break per D-13).
    """
    stmt = (
        select(SessionModel)
        .where(
            SessionModel.owner_id == owner_id,
            SessionModel.status.in_(["completed", "ended_early"]),
        )
        .order_by(
            SessionModel.completed_at.desc(),
            SessionModel.started_at.desc(),
            SessionModel.id,
        )
        .limit(limit)
    )
    if job_id is not None:
        stmt = stmt.where(SessionModel.job_id == job_id)
    return list(db.scalars(stmt).all())


def _session_to_summary(
    session: Any, turns: list[Any], scores: list[Any], total_competencies: int, job_title: str
) -> SessionSummary:
    """Map a session + loaded relations to SessionSummary with derived metrics."""
    duration_ms = _compute_duration_ms(session)
    overall_score = _compute_overall_score(scores, total_competencies)
    coverage = _compute_coverage_percent(scores, total_competencies)
    talk_ratio = _compute_talk_ratio(session, turns)

    # D-04: questionCount = interviewer turns
    question_count = sum(1 for t in turns if t.role == "interviewer")
    # D-05: followUpCount = interviewer turns with action='follow_up'
    follow_up_count = sum(1 for t in turns if t.role == "interviewer" and t.action == "follow_up")

    started_at_str = session.started_at.isoformat() if session.started_at else ""
    completed_at_str = session.completed_at.isoformat() if session.completed_at else None

    return SessionSummary(
        id=session.id,
        jobId=session.job_id,
        jobTitle=job_title,
        status=session.status,
        startedAt=started_at_str,
        completedAt=completed_at_str,
        durationMs=duration_ms,
        overallScore=overall_score,
        coveragePercent=coverage,
        talkRatio=talk_ratio,
        questionCount=question_count,
        followUpCount=follow_up_count,
    )


# --- Private metric helpers ---


def _compute_duration_ms(session: Any) -> int | None:
    """D-02: duration = completed_at - started_at in milliseconds. None if either missing."""
    if session.started_at is None or session.completed_at is None:
        return None
    delta = session.completed_at - session.started_at
    return int(delta.total_seconds() * 1000)


def _compute_coverage_percent(scores: Sequence[Any], total_competencies: int) -> float | None:
    """D-01/D-06: assessed/total as 0-1 ratio. Null if scores incomplete or zero total."""
    if total_competencies <= 0:
        return None
    # D-06: null unless score rows cover all competencies
    if len(scores) != total_competencies:
        return None
    assessed_count = sum(1 for s in scores if getattr(s, "assessed", False))
    return round(assessed_count / total_competencies, 2)


def _compute_overall_score(scores: Sequence[Any], total_competencies: int) -> float | None:
    """D-03/D-06: average assessed scores rounded 1 decimal. Null if incomplete."""
    if total_competencies <= 0:
        return None
    # D-06: null unless score rows cover all competencies
    if len(scores) != total_competencies:
        return None
    return derive_overall_score(scores)


def _compute_talk_ratio(session: Any, turns: list[Any]) -> float | None:
    """D-07 through D-11: three-branch talkRatio formula.

    - D-08: all audio → SUM(candidate audio_duration_ms) / durationMs
    - D-09: all text → candidate_chars / total_chars
    - D-10: mixed → combine audio + allocated text time
    - D-11: null if durationMs <= 0, no candidate turns, or zero text denominator
    """
    duration_ms = _compute_duration_ms(session)
    if duration_ms is None or duration_ms <= 0:
        return None

    audio_turns, text_turns = _classify_candidate_turns(turns)
    if not audio_turns and not text_turns:
        return None

    return _dispatch_talk_ratio(turns, audio_turns, text_turns, duration_ms)


def _classify_candidate_turns(turns: list[Any]) -> tuple[list[Any], list[Any]]:
    """Split candidate turns into audio (has audio_duration_ms) and text (no audio)."""
    audio: list[Any] = []
    text: list[Any] = []
    for t in turns:
        if t.role != "candidate":
            continue
        if getattr(t, "audio_duration_ms", None) is not None:
            audio.append(t)
        else:
            text.append(t)
    return audio, text


def _dispatch_talk_ratio(
    all_turns: list[Any],
    audio_turns: list[Any],
    text_turns: list[Any],
    duration_ms: int,
) -> float | None:
    """Dispatch to the correct talk ratio formula based on turn classification."""
    if audio_turns and not text_turns:
        return _compute_audio_talk_ratio(audio_turns, duration_ms)
    if text_turns and not audio_turns:
        return _compute_text_talk_ratio(all_turns, text_turns)
    return _compute_mixed_talk_ratio(all_turns, audio_turns, text_turns, duration_ms)


def _compute_audio_talk_ratio(candidate_audio_turns: list[Any], duration_ms: int) -> float | None:
    """D-08: SUM(candidate audio_duration_ms) / durationMs."""
    total_audio = sum(t.audio_duration_ms for t in candidate_audio_turns)
    if duration_ms <= 0:
        return None
    return min(round(total_audio / duration_ms, 2), 1.0)


def _compute_text_talk_ratio(all_turns: list[Any], candidate_text_turns: list[Any]) -> float | None:
    """D-09: candidate_text_chars / total_transcript_chars."""
    candidate_chars = sum(len(t.content) for t in candidate_text_turns)
    total_chars = sum(len(t.content) for t in all_turns)
    if total_chars <= 0:
        return None
    return round(candidate_chars / total_chars, 2)


def _compute_mixed_talk_ratio(
    all_turns: list[Any],
    candidate_audio_turns: list[Any],
    candidate_text_turns: list[Any],
    duration_ms: int,
) -> float | None:
    """D-10: mixed voice/text talkRatio.

    recorded_candidate_audio_ms = SUM(candidate audio_duration_ms)
    remaining_duration_ms = durationMs - recorded_candidate_audio_ms
    non_audio_text_chars = chars from interviewer + candidate turns without audio
    text_candidate_chars = chars from candidate turns without audio
    allocated_text_ms = remaining_duration_ms * text_candidate_chars / non_audio_text_chars
    talkRatio = (recorded_audio_ms + allocated_text_ms) / durationMs
    """
    recorded_audio_ms = sum(t.audio_duration_ms for t in candidate_audio_turns)
    remaining_ms = duration_ms - recorded_audio_ms

    if remaining_ms <= 0:
        # All time accounted by audio — pure audio ratio
        return min(round(recorded_audio_ms / duration_ms, 2), 1.0)

    # Non-audio text chars: interviewer turns + candidate turns without audio
    interviewer_turns = [t for t in all_turns if t.role == "interviewer"]
    non_audio_text_chars = sum(len(t.content) for t in interviewer_turns) + sum(
        len(t.content) for t in candidate_text_turns
    )
    text_candidate_chars = sum(len(t.content) for t in candidate_text_turns)

    if non_audio_text_chars <= 0:
        return min(round(recorded_audio_ms / duration_ms, 2), 1.0)

    allocated_text_ms = remaining_ms * text_candidate_chars / non_audio_text_chars
    return min(round((recorded_audio_ms + allocated_text_ms) / duration_ms, 2), 1.0)
