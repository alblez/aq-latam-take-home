"""Turn submission flow: submit_turn entry point (D-22).

Separates validation → guards → candidate insert → orchestrator call → response
assembly from the thin route handler. Unit-testable without ASGI.

Per D-10/D-11: no DB transaction spans gateway calls.
Per D-18: requires an existing latest interviewer turn for new submissions.
Per D-01/D-02/D-05: idempotency branches for duplicate/recovery/stale submissions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast
from uuid import UUID

import structlog
from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.engine.gateway import ModelGateway
from app.engine.orchestrator import (
    EndEarlyData,
    PipelineResult,
    build_end_early_terminal,
    process_candidate_answer,
    run_evaluation,
)
from app.errors import ApiError
from app.models import CompetencyModel, JobModel, SessionModel, TurnModel
from app.repositories import (
    SessionNotInProgressError,
    finalize_session_terminal,
    get_candidate_turn_by_client_turn_id,
    get_following_interviewer_turn,
    get_latest_turn,
    get_session_for_owner,
    get_session_state_data,
    guard_session_in_progress,
    has_complete_evaluation,
    insert_candidate_turn,
    insert_competency_scores,
    update_session_updated_at,
)
from app.schemas import (
    CompetencyRef,
    CompetencyStatus,
    EndSessionEarlyResponse,
    PanelState,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    TerminalPanelState,
    Turn,
)

logger = structlog.get_logger()

# --- Module-level constants ---
SESSION_NOT_FOUND_MSG = "Session not found."
SESSION_NOT_IN_PROGRESS_MSG = "Session is not in progress."


class SnapshotDriftError(Exception):
    """Raised when turn count changed between TX-A snapshot and TX-B finalization."""


@dataclass(frozen=True)
class LoadedSessionState:
    """Pre-fetched session state for response assembly. Decouples DB from builders."""

    session: SessionModel
    job: JobModel
    turns: list[TurnModel]
    competencies: list[CompetencyModel]
    latest_interviewer: TurnModel | None


def load_session_state(db: Session, session_id: UUID) -> LoadedSessionState:
    """Single DB fetch for response construction. Raises RuntimeError if missing."""
    state_data = get_session_state_data(db, session_id)
    if state_data is None:
        msg = f"Session {session_id} state unreadable"
        raise RuntimeError(msg)

    turns_list: list[TurnModel] = state_data["turns"]
    return LoadedSessionState(
        session=state_data["session"],
        job=state_data["job"],
        turns=turns_list,
        competencies=state_data["competencies"],
        latest_interviewer=_find_latest_interviewer(turns_list),
    )


# --- Public helpers (exported for unit testing) ---


def assert_same_candidate_payload(existing_turn: TurnModel, body: SubmitAnswerRequest) -> None:
    """Raise 409 if payload differs from existing candidate turn per D-01.

    Same clientTurnId + same payload = idempotent (no error).
    Same clientTurnId + different payload = loud conflict.
    Compares answerText, inputMode, and audioDurationMs.
    """
    if existing_turn.content != body.answerText:
        raise ApiError(
            status_code=status.HTTP_409_CONFLICT,
            code="turn_already_submitted",
            message="Turn already submitted with different content.",
        )
    if existing_turn.input_mode != body.inputMode:
        raise ApiError(
            status_code=status.HTTP_409_CONFLICT,
            code="turn_already_submitted",
            message="Turn already submitted with different inputMode.",
        )
    if existing_turn.audio_duration_ms != body.audioDurationMs:
        raise ApiError(
            status_code=status.HTTP_409_CONFLICT,
            code="turn_already_submitted",
            message="Turn already submitted with different audioDurationMs.",
        )


def detect_needs_recovery(turns: list, session_status: str) -> bool:
    """Determine if session needs recovery per D-16.

    True only when: status=in_progress AND latest turn is candidate (dangling).
    Terminal sessions always return False.
    """
    if session_status != "in_progress":
        return False
    if not turns:
        return False
    latest = turns[-1]
    return latest.role == "candidate"


def submit_turn(
    db: Session,
    gateway: ModelGateway,
    session_id: UUID,
    owner_id: UUID,
    body: SubmitAnswerRequest,
) -> SubmitAnswerResponse:
    """Submit candidate answer flow per D-22 with idempotency branches.

    Branch order per D-01/D-02/D-05:
    1. Owner-check session
    2. Check existing candidate by clientTurnId (idempotency — works even if terminal)
    3. Guard: session must be in_progress (new submissions only)
    4. Check for dangling candidate (new clientTurnId while recovery pending → 409)
    5. Require latest interviewer turn exists (D-18)
    6. Insert candidate turn in short TX, commit
    7. Call process_candidate_answer (no open TX per D-10)
    8. Build and return SubmitAnswerResponse
    """
    # 1. Owner-scoped session lookup
    session = get_session_for_owner(db, session_id, owner_id)
    if session is None:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="session_not_found",
            message=SESSION_NOT_FOUND_MSG,
        )

    # 2. Idempotency check BEFORE status guard — allows terminal duplicate retries
    existing_candidate = get_candidate_turn_by_client_turn_id(db, session_id, body.clientTurnId)
    if existing_candidate is not None:
        return _handle_existing_candidate(
            db, gateway, session, existing_candidate, body, session_id
        )

    # 3. Guard: session must be in_progress (only for new/non-matching clientTurnIds)
    if session.status != "in_progress":
        raise ApiError(
            status_code=status.HTTP_409_CONFLICT,
            code="session_not_in_progress",
            message=SESSION_NOT_IN_PROGRESS_MSG,
        )

    # 4. Check for dangling candidate (D-02)
    latest_turn = get_latest_turn(db, session_id)
    if latest_turn is not None and latest_turn.role == "candidate":
        # Race: a concurrent request with the SAME clientTurnId may have committed
        # its candidate between the idempotency check above and this read. Converge
        # to that winner via the idempotency branch instead of 409 (D-10).
        if latest_turn.client_turn_id == body.clientTurnId:
            return _handle_existing_candidate(db, gateway, session, latest_turn, body, session_id)
        raise ApiError(
            status_code=status.HTTP_409_CONFLICT,
            code="turn_already_submitted",
            message="A previous answer is pending recovery. Retry with the original clientTurnId.",
        )

    # 5-8. New submission path
    return _handle_new_submission(db, gateway, session, session_id, body)


def _handle_existing_candidate(
    db: Session,
    gateway: ModelGateway,
    session: SessionModel,
    existing_candidate: TurnModel,
    body: SubmitAnswerRequest,
    session_id: UUID,
) -> SubmitAnswerResponse:
    """Handle idempotency branch for existing clientTurnId per D-01/D-05."""
    # Check payload match per D-01
    assert_same_candidate_payload(existing_candidate, body)

    # Same payload — check if pipeline already completed
    following_interviewer = get_following_interviewer_turn(
        db, session_id, existing_candidate.turn_index
    )
    if following_interviewer is not None:
        # D-05: stale duplicate — pipeline completed, return current state
        logger.info(
            "idempotent_duplicate_hit",
            session_id=str(session_id),
            client_turn_id=str(body.clientTurnId),
        )
        ctx = load_session_state(db, session_id)
        return _build_current_state_response(db, ctx)

    # Dangling candidate — recovery: call pipeline per SESS-05
    logger.info(
        "recovery_continuation_started",
        session_id=str(session_id),
        client_turn_id=str(body.clientTurnId),
    )
    try:
        result: PipelineResult = process_candidate_answer(
            db=db,
            gateway=gateway,
            session=session,
            candidate_turn=existing_candidate,
        )
    except SessionNotInProgressError:
        # D-12: guard trip during recovery continuation
        logger.info(
            "guard_trip_terminal_response",
            session_id=str(session_id),
            client_turn_id=str(body.clientTurnId),
        )
        ctx = load_session_state(db, session_id)
        return _build_guard_trip_response(db, ctx)
    except IntegrityError:
        # Concurrent pipeline converged: another runner persisted the interviewer
        # turn for this same candidate first (uq_turns_session_turn_index). The
        # loser converges to the winner's committed state per D-10.
        db.rollback()
        logger.info(
            "pipeline_race_converged",
            session_id=str(session_id),
            client_turn_id=str(body.clientTurnId),
        )
        ctx = load_session_state(db, session_id)
        return _build_current_state_response(db, ctx)
    ctx = load_session_state(db, session_id)
    return _build_submit_response(db=db, ctx=ctx, result=result)


def _validate_new_submission_state(
    db: Session, session_id: UUID, client_turn_id: UUID | None = None
) -> tuple[int, UUID]:
    """Validate state for new submission. Returns (next_turn_index, competency_id).

    Raises ApiError if session not found or not started (D-18).

    When client_turn_id is supplied and the latest turn is a candidate carrying
    that same id, this is a concurrent same-clientTurnId race: return normally and
    let the lock-protected caller converge via idempotency (D-10) rather than 409.
    """
    state_data = get_session_state_data(db, session_id)
    if state_data is None:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="session_not_found",
            message=SESSION_NOT_FOUND_MSG,
        )

    turns_list: list[TurnModel] = state_data["turns"]
    if not turns_list or turns_list[-1].role != "interviewer":
        has_any_interviewer = any(t.role == "interviewer" for t in turns_list)
        if not has_any_interviewer:
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code="session_not_in_progress",
                message="Session has not been started.",
            )
        # Latest is candidate — defense-in-depth for CR-01 race (WR-01).
        # Our own clientTurnId landing concurrently is not a conflict: defer to the
        # locked path, which converges via _handle_existing_candidate.
        own_race = client_turn_id is not None and turns_list[-1].client_turn_id == client_turn_id
        if not own_race:
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code="turn_already_submitted",
                message="A previous answer is pending recovery.",
            )

    latest_interviewer = _find_latest_interviewer(turns_list)
    assert latest_interviewer is not None  # noqa: S101 -- guarded above
    return len(turns_list), latest_interviewer.competency_id


def _handle_new_submission(
    db: Session,
    gateway: ModelGateway,
    session: SessionModel,
    session_id: UUID,
    body: SubmitAnswerRequest,
) -> SubmitAnswerResponse:
    """Handle fresh candidate submission: validate, insert, pipeline, respond."""
    # Race re-check: a concurrent request with the same clientTurnId may have
    # committed its candidate after submit_turn's idempotency check. Converge to
    # that winner before validating new-submission preconditions (D-10).
    existing_candidate = get_candidate_turn_by_client_turn_id(db, session_id, body.clientTurnId)
    if existing_candidate is not None:
        return _handle_existing_candidate(
            db, gateway, session, existing_candidate, body, session_id
        )

    # 5. Require latest interviewer turn (D-18)
    next_turn_index, competency_id = _validate_new_submission_state(
        db, session_id, body.clientTurnId
    )

    # 6. Insert candidate turn in short TX with D-11 guard to prevent TOCTOU race.
    # Guard acquires FOR NO KEY UPDATE lock, then we re-validate latest turn is
    # still interviewer before inserting. IntegrityError retry-read for concurrent
    # duplicate per D-10/D-28.
    try:
        guard_session_in_progress(db, session_id=session_id)
        # Re-read latest turn under lock to close TOCTOU window (CR-01)
        latest_turn_locked = get_latest_turn(db, session_id)
        if latest_turn_locked and latest_turn_locked.role == "candidate":
            db.rollback()
            # Same clientTurnId committed by a concurrent winner under the lock →
            # converge via idempotency rather than 409 (D-10).
            if latest_turn_locked.client_turn_id == body.clientTurnId:
                return _handle_existing_candidate(
                    db, gateway, session, latest_turn_locked, body, session_id
                )
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code="turn_already_submitted",
                message="A previous answer is pending recovery.",
            )
        candidate_turn = insert_candidate_turn(
            db,
            session_id=session_id,
            turn_index=next_turn_index,
            competency_id=competency_id,
            content=body.answerText,
            client_turn_id=body.clientTurnId,
            input_mode=body.inputMode,
            audio_duration_ms=body.audioDurationMs,
        )
        update_session_updated_at(db, session_id)
        db.commit()
    except SessionNotInProgressError:
        # D-11 guard trip during insert TX — session finalized concurrently.
        logger.info("guard_trip_during_insert", session_id=str(session_id))
        ctx = load_session_state(db, session_id)
        return _build_guard_trip_response(db, ctx)
    except IntegrityError:
        # Concurrent duplicate: ux_turns_session_client_turn unique index violated.
        # Retry-read the winner row and delegate to idempotency branch per D-10.
        db.rollback()
        existing_candidate = get_candidate_turn_by_client_turn_id(db, session_id, body.clientTurnId)
        if existing_candidate is None:
            raise  # pragma: no cover -- should not happen; re-raise for visibility
        return _handle_existing_candidate(
            db, gateway, session, existing_candidate, body, session_id
        )

    # 7. Call orchestrator pipeline (no DB transaction open per D-10/SESS-08)
    try:
        result: PipelineResult = process_candidate_answer(
            db=db,
            gateway=gateway,
            session=session,
            candidate_turn=candidate_turn,
        )
    except SessionNotInProgressError:
        # D-12: session ended during gateway call (guard trip in TX-B).
        # Candidate turn is already persisted (TX-A committed).
        # Return terminal-shaped 200 from current DB state.
        logger.info(
            "guard_trip_terminal_response",
            session_id=str(session_id),
            client_turn_id=str(body.clientTurnId),
        )
        ctx = load_session_state(db, session_id)
        return _build_guard_trip_response(db, ctx)
    except IntegrityError:
        # Concurrent pipeline converged: another runner persisted the interviewer
        # turn for this same candidate first (uq_turns_session_turn_index). The
        # loser converges to the winner's committed state per D-10.
        db.rollback()
        logger.info(
            "pipeline_race_converged",
            session_id=str(session_id),
            client_turn_id=str(body.clientTurnId),
        )
        ctx = load_session_state(db, session_id)
        return _build_current_state_response(db, ctx)

    # 8. Build response from current state
    ctx = load_session_state(db, session_id)
    return _build_submit_response(db=db, ctx=ctx, result=result)


# --- Shared response-building helpers (reduce complexity per xenon) ---


def _evaluation_ready(db: Session, *, session_id: UUID, job_id: UUID) -> bool:
    """D-33: dynamically query evaluation readiness from DB state.

    Delegates to has_complete_evaluation — True only when narrative exists
    AND score count equals competency count.
    Called ONLY for terminal responses; non-terminal paths return literal False.
    """
    return has_complete_evaluation(db, session_id=session_id, job_id=job_id)


def _find_latest_interviewer(turns_list: list[TurnModel]) -> TurnModel | None:
    """Find the most recent interviewer turn in an ordered list."""
    for t in reversed(turns_list):
        if t.role == "interviewer":
            return t
    return None


def _resolve_panel(
    latest_interviewer: TurnModel | None,
    competencies_list: list,
) -> PanelState:
    """Resolve PanelState from latest interviewer reasoning or baseline."""
    if latest_interviewer and latest_interviewer.reasoning:
        return PanelState.model_validate(latest_interviewer.reasoning)
    from app.panel_state import build_baseline_panel_state

    return build_baseline_panel_state([c.id for c in competencies_list])


def _build_competency_statuses(
    panel: PanelState, competencies_list: list
) -> list[CompetencyStatus]:
    """Derive CompetencyStatus list from panel rubric snapshot."""
    in_progress_ids = set(panel.rubricSnapshot.inProgress)
    covered_ids = set(panel.rubricSnapshot.covered)
    return [
        CompetencyStatus(
            id=c.id,
            name=c.name,
            category=c.category,
            status=(
                "in-progress"
                if c.id in in_progress_ids
                else ("covered" if c.id in covered_ids else "not-reached")
            ),
        )
        for c in competencies_list
    ]


def _build_turn_schemas(turns_list: list[TurnModel]) -> list[Turn]:
    """Convert TurnModel list to Turn schema list."""
    return [
        Turn(
            id=t.id,
            clientTurnId=t.client_turn_id,
            role=cast("Turn.role", t.role),  # type: ignore[arg-type]
            turnIndex=t.turn_index,
            competencyId=t.competency_id,
            content=t.content,
            action=cast("Turn.action", t.action),  # type: ignore[arg-type]
            sourcePackItemId=t.source_pack_item_id,
            inputMode=cast("Turn.inputMode", t.input_mode),  # type: ignore[arg-type]
            audioDurationMs=t.audio_duration_ms,
        )
        for t in turns_list
    ]


def _build_guard_trip_response(
    db: Session,
    ctx: LoadedSessionState,
) -> SubmitAnswerResponse:
    """Build terminal-shaped SubmitAnswerResponse after guard trip per D-12.

    When SessionNotInProgressError fires during TX-B, the session has already
    been finalized by a concurrent /end-early or controller action. Return
    isComplete=true, question=null, and the persisted terminalPanelState.
    """
    panel = _resolve_panel(ctx.latest_interviewer, ctx.competencies)
    turn_index = ctx.turns[-1].turn_index if ctx.turns else 0

    terminal: TerminalPanelState | None = None
    if ctx.session.terminal_panel_state:
        terminal = TerminalPanelState.model_validate(ctx.session.terminal_panel_state)

    return SubmitAnswerResponse(
        question=None,
        turnIndex=turn_index,
        panelState=panel,
        competencies=_build_competency_statuses(panel, ctx.competencies),
        turns=_build_turn_schemas(ctx.turns),
        jobTitle=ctx.job.title,
        isComplete=True,
        terminalPanelState=terminal,
        evaluationReady=_evaluation_ready(db, session_id=ctx.session.id, job_id=ctx.session.job_id),
    )


def _build_current_state_response(
    db: Session,
    ctx: LoadedSessionState,
) -> SubmitAnswerResponse:
    """Build SubmitAnswerResponse from current DB state (stale duplicate path per D-05)."""
    panel = _resolve_panel(ctx.latest_interviewer, ctx.competencies)

    current_question = ctx.latest_interviewer.content if ctx.latest_interviewer else None
    turn_index = ctx.turns[-1].turn_index if ctx.turns else 0
    is_complete = ctx.session.status != "in_progress"

    terminal: TerminalPanelState | None = None
    if ctx.session.terminal_panel_state:
        terminal = TerminalPanelState.model_validate(ctx.session.terminal_panel_state)

    return SubmitAnswerResponse(
        question=current_question,
        turnIndex=turn_index,
        panelState=panel,
        competencies=_build_competency_statuses(panel, ctx.competencies),
        turns=_build_turn_schemas(ctx.turns),
        jobTitle=ctx.job.title,
        isComplete=is_complete,
        terminalPanelState=terminal,
        evaluationReady=(
            _evaluation_ready(db, session_id=ctx.session.id, job_id=ctx.session.job_id)
            if is_complete
            else False
        ),
    )


def _build_submit_response(
    db: Session,
    ctx: LoadedSessionState,
    result: PipelineResult,
) -> SubmitAnswerResponse:
    """Build SubmitAnswerResponse from pipeline result and loaded state."""
    # Panel state from pipeline result, latest interviewer reasoning, or baseline
    panel: PanelState
    if result.reasoning:
        panel = PanelState.model_validate(result.reasoning)
    elif ctx.latest_interviewer and ctx.latest_interviewer.reasoning:
        panel = PanelState.model_validate(ctx.latest_interviewer.reasoning)
    else:
        from app.panel_state import build_baseline_panel_state

        panel = build_baseline_panel_state([c.id for c in ctx.competencies])

    # Determine question and completion
    is_complete = result.action == "end"
    current_question = result.interviewer_turn.content if result.interviewer_turn else None
    turn_index = ctx.turns[-1].turn_index if ctx.turns else 0

    terminal: TerminalPanelState | None = None
    if result.terminal_panel_state:
        terminal = TerminalPanelState.model_validate(result.terminal_panel_state)

    return SubmitAnswerResponse(
        question=current_question,
        turnIndex=turn_index,
        panelState=panel,
        competencies=_build_competency_statuses(panel, ctx.competencies),
        turns=_build_turn_schemas(ctx.turns),
        jobTitle=ctx.job.title,
        isComplete=is_complete,
        terminalPanelState=terminal,
        evaluationReady=(
            _evaluation_ready(db, session_id=ctx.session.id, job_id=ctx.session.job_id)
            if is_complete
            else False
        ),
    )


# --- End-Early Flow (D-23, D-06, D-07, D-08) ---


def _end_early_tx_b(
    db: Session,
    session_id: UUID,
    data: EndEarlyData,
    narrative_dict: dict | None,
    score_rows: list | None,
) -> None:
    """TX-B for end-early: guard + drift check + finalize + persist (Pattern 4 step 3).

    Raises SessionNotInProgressError if guard trips (concurrent finalizer won).
    """
    from sqlalchemy import func as sa_func
    from sqlalchemy import select as sa_select

    from app.models import TurnModel as TM

    guard_session_in_progress(db, session_id=session_id)

    # A4 mitigation: re-check turn count for snapshot drift — abort if changed
    current_count: int = (
        db.scalar(sa_select(sa_func.count(TM.id)).where(TM.session_id == session_id)) or 0
    )
    if current_count != data.turn_count:
        db.rollback()
        raise SnapshotDriftError(
            f"Turn count drifted: snapshot={data.turn_count}, current={current_count}"
        )

    now = datetime.now(UTC)
    finalize_session_terminal(
        db,
        session_id=session_id,
        completion_reason="ended_early",
        terminal_panel_state=data.terminal_dict,
        completed_at=now,
        status="ended_early",
        evaluation_narrative=narrative_dict,
    )

    # Persist score rows in same TX-B when evaluation succeeded (D-26)
    if score_rows is not None:
        insert_competency_scores(db, rows=score_rows)

    db.commit()


def end_session_early_flow(
    db: Session,
    gateway: ModelGateway,
    session_id: UUID,
    owner_id: UUID,
) -> EndSessionEarlyResponse:
    """End session early flow per D-22/D-23 with Pattern 4 TX choreography.

    Branches:
    - Owner-check → 404
    - status=ended_early → idempotent: return existing terminal (D-06)
    - status=completed → 409 session_not_in_progress (D-06)
    - status=in_progress → Pattern 4: read+commit → eval (no TX) → guard+finalize+persist
    """
    # 1. Owner-scoped lookup
    session = get_session_for_owner(db, session_id, owner_id)
    if session is None:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="session_not_found",
            message=SESSION_NOT_FOUND_MSG,
        )

    # 2. Idempotent return for already ended_early (D-06)
    if session.status == "ended_early":
        return _build_end_early_response_from_terminal(db, session)

    # 3. Completed by controller → 409 (D-06)
    if session.status == "completed":
        raise ApiError(
            status_code=status.HTTP_409_CONFLICT,
            code="session_not_in_progress",
            message=SESSION_NOT_IN_PROGRESS_MSG,
        )

    # 4. In-progress → Pattern 4 restructure

    # --- Step 1: Short read TX — snapshot + commit (releases all locks) ---
    data: EndEarlyData = build_end_early_terminal(db, session)
    db.commit()

    # --- Step 2: No transaction — gateway evaluation (may take 60s) ---
    narrative_dict, score_rows, _eval_failure_mode = run_evaluation(
        gateway,
        eval_turns=data.eval_turns,
        comp_briefs=data.comp_briefs,
        transcript=data.transcript,
        flags=[],
        coverage=data.coverage,
        terminal_reason="ended_early",
        session_id=data.session_id,
        job_id=data.job_id,
        terminal_failure_mode=None,
    )

    # --- Step 3: TX-B — guard + re-check + finalize + persist ---
    try:
        _end_early_tx_b(db, session_id, data, narrative_dict, score_rows)
    except SnapshotDriftError:
        # Rebuild from current DB state and retry once (bounded)
        logger.warning(
            "end_early_snapshot_drift_retry",
            session_id=str(session_id),
        )
        session = get_session_for_owner(db, session_id, owner_id)
        if session is None or session.status != "in_progress":
            return _handle_end_early_race(db, session_id, owner_id)
        data = build_end_early_terminal(db, session)
        db.commit()
        narrative_dict, score_rows, _eval_failure_mode = run_evaluation(
            gateway,
            eval_turns=data.eval_turns,
            comp_briefs=data.comp_briefs,
            transcript=data.transcript,
            flags=[],
            coverage=data.coverage,
            terminal_reason="ended_early",
            session_id=data.session_id,
            job_id=data.job_id,
            terminal_failure_mode=None,
        )
        try:
            _end_early_tx_b(db, session_id, data, narrative_dict, score_rows)
        except (SnapshotDriftError, SessionNotInProgressError):
            # Second drift or concurrent finalizer won during retry window
            return _handle_end_early_race(db, session_id, owner_id)
    except SessionNotInProgressError:
        # Concurrent finalizer won the race — re-read and return appropriate response
        return _handle_end_early_race(db, session_id, owner_id)

    logger.info("end_early_finalized", session_id=str(session_id))
    ctx = load_session_state(db, session_id)
    return _build_end_early_response(db, ctx, data.terminal_dict)


def _build_end_early_response(
    db: Session,
    ctx: LoadedSessionState,
    terminal_dict: dict,
) -> EndSessionEarlyResponse:
    """Build EndSessionEarlyResponse from terminal panel state dict."""
    terminal = TerminalPanelState.model_validate(terminal_dict)
    uncovered_ids = terminal_dict.get("uncoveredCompetencyIds", [])

    comp_map = {str(c.id): c for c in ctx.competencies}

    uncovered_refs = []
    for uid in uncovered_ids:
        uid_str = str(uid) if not isinstance(uid, str) else uid
        comp = comp_map.get(uid_str)
        if comp:
            uncovered_refs.append(CompetencyRef(id=comp.id, name=comp.name))

    return EndSessionEarlyResponse(
        uncoveredCompetencies=uncovered_refs,
        terminalPanelState=terminal,
        evaluationReady=_evaluation_ready(db, session_id=ctx.session.id, job_id=ctx.session.job_id),
    )


def _build_end_early_response_from_terminal(
    db: Session,
    session: SessionModel,
) -> EndSessionEarlyResponse:
    """Build idempotent EndSessionEarlyResponse from persisted terminal state (D-06)."""
    if not session.terminal_panel_state:
        msg = f"Terminal panel state missing for ended_early session {session.id}"
        raise RuntimeError(msg)

    ctx = load_session_state(db, session.id)
    return _build_end_early_response(db, ctx, session.terminal_panel_state)


def _handle_end_early_race(
    db: Session,
    session_id: UUID,
    owner_id: UUID,
) -> EndSessionEarlyResponse:
    """Handle race condition where concurrent finalizer won (D-06)."""
    db.rollback()
    session = get_session_for_owner(db, session_id, owner_id)
    if session is None:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="session_not_found",
            message=SESSION_NOT_FOUND_MSG,
        ) from None
    if session.status == "ended_early":
        return _build_end_early_response_from_terminal(db, session)
    raise ApiError(
        status_code=status.HTTP_409_CONFLICT,
        code="session_not_in_progress",
        message=SESSION_NOT_IN_PROGRESS_MSG,
    ) from None
