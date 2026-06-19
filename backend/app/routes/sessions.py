from __future__ import annotations

from typing import cast
from uuid import UUID

from fastapi import APIRouter, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSessionType

from app.deps import DbSession, GatewayDep, OwnerId
from app.errors import ApiError
from app.jsonb_schemas import DEFAULT_CONTROLLER_CONFIG
from app.panel_state import (
    build_baseline_panel_state,
    build_first_turn_panel_state,
    build_first_turn_reasoning,
)
from app.repositories import (
    create_session as repo_create_session,
)
from app.repositories import (
    get_first_interviewer_turn,
    get_job_with_competency_count,
    get_session_for_owner,
    get_session_state_data,
    insert_first_interviewer_turn,
    select_first_question_data,
    update_session_updated_at,
)
from app.schemas import (
    CompetencyStatus,
    CreateSessionRequest,
    EndSessionEarlyResponse,
    PanelState,
    Session,
    SessionDetail,
    SessionStateResponse,
    SessionStatus,
    StartSessionResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    TerminalPanelState,
    Turn,
)

router = APIRouter(tags=["sessions"])


# --- DB-backed endpoints ---


@router.post("/sessions", status_code=201, response_model=Session)
def create_session(
    body: CreateSessionRequest,
    owner_id: OwnerId,
    db: DbSession,
) -> Session:
    """Create a new interview session for a job, scoped to the owner."""
    # Validate job exists and has competencies
    result = get_job_with_competency_count(db, body.jobId)
    if result is None:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="job_not_found",
            message="Job not found.",
        )

    _job, competency_count = result
    if competency_count == 0:
        raise ApiError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="catalog_setup_error",
            message="Job catalog setup is invalid.",
        )

    config_dict = DEFAULT_CONTROLLER_CONFIG.model_dump(mode="json")
    session_model = repo_create_session(db, owner_id, body.jobId, config_dict)

    return Session(
        id=session_model.id,
        jobId=session_model.job_id,
        status="in_progress",
    )


@router.get("/sessions/{sessionId}/state", response_model=SessionStateResponse)
def get_session_state(
    sessionId: UUID,
    owner_id: OwnerId,
    db: DbSession,
) -> SessionStateResponse:
    """Get current session state for the owner."""
    # Validate ownership
    session = get_session_for_owner(db, sessionId, owner_id)
    if session is None:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="session_not_found",
            message="Session not found.",
        )

    # Fetch full state data
    state_data = get_session_state_data(db, sessionId)
    if state_data is None:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="session_not_found",
            message="Session not found.",
        )

    turns_list = state_data["turns"]
    if not turns_list:
        return _build_prestart_state(session, state_data)

    return _build_active_state(session, state_data)


def _build_prestart_state(session: object, state_data: dict) -> SessionStateResponse:
    """Build state response for sessions with no turns yet."""
    from app.models import SessionModel

    s = cast(SessionModel, session)
    competencies_list = state_data["competencies"]
    job = state_data["job"]

    competency_ids = [c.id for c in competencies_list]
    baseline_panel = build_baseline_panel_state(competency_ids)
    comp_statuses = [
        CompetencyStatus(
            id=c.id,
            name=c.name,
            category=c.category,
            status="not-reached",
        )
        for c in competencies_list
    ]

    return SessionStateResponse(
        session=Session(
            id=s.id,
            jobId=s.job_id,
            status=cast(SessionStatus, s.status),
        ),
        turns=[],
        panelState=baseline_panel,
        competencies=comp_statuses,
        jobTitle=job.title,
        currentQuestion=None,
        turnIndex=0,
        status=cast(SessionStatus, s.status),
        needsRecovery=False,
        terminalPanelState=None,
    )


def _build_active_state(session: object, state_data: dict) -> SessionStateResponse:
    """Build state response for sessions with existing turns."""
    from app.models import SessionModel
    from app.turn_flow import detect_needs_recovery

    s = cast(SessionModel, session)
    turns_list = state_data["turns"]
    competencies_list = state_data["competencies"]
    job = state_data["job"]

    latest_interviewer = None
    for t in reversed(turns_list):
        if t.role == "interviewer":
            latest_interviewer = t
            break

    current_question = latest_interviewer.content if latest_interviewer else None
    turn_index = turns_list[-1].turn_index if turns_list else 0
    needs_recovery = detect_needs_recovery(turns_list, s.status)

    # Build panel state from latest interviewer turn reasoning (per D-31)
    panel = _derive_panel_state(latest_interviewer, competencies_list)

    # Terminal panel from session if terminal (per D-17)
    terminal_panel: TerminalPanelState | None = None
    if s.status != "in_progress" and s.terminal_panel_state:
        terminal_panel = TerminalPanelState.model_validate(s.terminal_panel_state)

    # Build competency statuses from panel rubric
    comp_statuses = _derive_competency_statuses(competencies_list, panel)

    # Build Turn schema objects from DB models
    turn_schemas = [
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

    return SessionStateResponse(
        session=Session(
            id=s.id,
            jobId=s.job_id,
            status=cast(SessionStatus, s.status),
        ),
        turns=turn_schemas,
        panelState=panel,
        competencies=comp_statuses,
        jobTitle=job.title,
        currentQuestion=current_question,
        turnIndex=turn_index,
        status=cast(SessionStatus, s.status),
        needsRecovery=needs_recovery,
        terminalPanelState=terminal_panel,
    )


def _derive_panel_state(latest_interviewer: object | None, competencies_list: list) -> PanelState:
    """Extract panel state from latest interviewer turn reasoning or build baseline."""
    if latest_interviewer is not None:
        reasoning = getattr(latest_interviewer, "reasoning", None)
        if reasoning:
            return PanelState.model_validate(reasoning)
    competency_ids = [c.id for c in competencies_list]
    return build_baseline_panel_state(competency_ids)


def _derive_competency_statuses(
    competencies_list: list,
    panel: PanelState,
) -> list[CompetencyStatus]:
    """Build competency status list from panel rubric snapshot."""
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


@router.post("/sessions/{sessionId}/start", response_model=StartSessionResponse)
def start_session(
    sessionId: UUID,
    owner_id: OwnerId,
    db: DbSession,
) -> StartSessionResponse:
    """Start a session — persists first interviewer turn idempotently."""
    session = get_session_for_owner(db, sessionId, owner_id)
    if session is None:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="session_not_found",
            message="Session not found.",
        )

    # Guard: terminal sessions cannot be started per D-19
    if session.status != "in_progress":
        raise ApiError(
            status_code=status.HTTP_409_CONFLICT,
            code="session_not_in_progress",
            message="Session is not in progress.",
        )

    # Idempotent path: check if first turn already exists (per D-25)
    existing_turn = get_first_interviewer_turn(db, sessionId)
    if existing_turn is not None:
        return _build_start_response(db, session, existing_turn)

    # Select first question deterministically (per D-14)
    question_data = select_first_question_data(db, session.job_id)
    if question_data is None:
        raise ApiError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="catalog_setup_error",
            message="Job catalog setup is invalid: no question pack for first competency.",
        )

    competency, pack_item = question_data

    # Get all competency IDs for panel state
    competencies_list = get_session_state_data(db, sessionId)
    all_competency_ids = (
        [c.id for c in competencies_list["competencies"]] if competencies_list else []
    )

    # Build panel state and reasoning
    panel_state = build_first_turn_panel_state(
        all_competency_ids=all_competency_ids,
        target_competency_id=competency.id,
        source_pack_item_id=pack_item.id,
    )
    reasoning = build_first_turn_reasoning(panel_state)

    # Insert first turn with race protection (per D-26)
    try:
        turn = insert_first_interviewer_turn(
            db=db,
            session_id=sessionId,
            competency_id=competency.id,
            content=pack_item.prompt_text,
            action="new_topic",
            source_pack_item_id=pack_item.id,
            reasoning=reasoning,
        )
        update_session_updated_at(db, sessionId)
        db.commit()
    except IntegrityError:
        db.rollback()
        # Retry-read: concurrent caller already inserted (per D-26)
        turn = get_first_interviewer_turn(db, sessionId)
        if turn is None:
            raise

    return _build_start_response(db, session, turn)


def _build_start_response(
    db: DbSessionType,
    session: object,
    turn: object,
) -> StartSessionResponse:
    """Build StartSessionResponse from persisted session and turn."""
    from app.models import SessionModel, TurnModel

    # Narrow types (models come from DB layer typed as object to avoid circular imports)
    s = cast(SessionModel, session)
    t = cast(TurnModel, turn)

    # Get job and competencies
    state_data = get_session_state_data(db, s.id)
    job = state_data["job"]  # type: ignore[index]
    competencies_list = state_data["competencies"]  # type: ignore[index]

    # Rebuild panel from turn reasoning
    panel: PanelState
    if t.reasoning:
        panel = PanelState.model_validate(t.reasoning)
    else:
        all_ids = [c.id for c in competencies_list]
        panel = build_baseline_panel_state(all_ids)

    # Derive competency statuses from panel rubric
    in_progress_ids = set(panel.rubricSnapshot.inProgress)
    covered_ids = set(panel.rubricSnapshot.covered)
    comp_statuses = [
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

    turn_schema = Turn(
        id=t.id,
        role=cast("Turn.role", t.role),  # type: ignore[arg-type]
        turnIndex=t.turn_index,
        competencyId=t.competency_id,
        content=t.content,
        action=cast("Turn.action", t.action),  # type: ignore[arg-type]
        sourcePackItemId=t.source_pack_item_id,
    )

    return StartSessionResponse(
        question=t.content,
        turnIndex=t.turn_index,
        panelState=panel,
        competencies=comp_statuses,
        turns=[turn_schema],
        jobTitle=job.title,
    )


# --- Stub endpoints (to be replaced in Plan 03+) ---


@router.post("/sessions/{sessionId}/turn", response_model=SubmitAnswerResponse)
def submit_turn(
    sessionId: UUID,
    body: SubmitAnswerRequest,
    owner_id: OwnerId,
    db: DbSession,
    gateway: GatewayDep,
) -> SubmitAnswerResponse:
    """Submit an answer — delegates to turn_flow per D-22."""
    from app.turn_flow import submit_turn as do_submit_turn

    return do_submit_turn(
        db=db,
        gateway=gateway,
        session_id=sessionId,
        owner_id=owner_id,
        body=body,
    )


@router.post("/sessions/{sessionId}/end-early", response_model=EndSessionEarlyResponse)
def end_session_early(
    sessionId: UUID,
    owner_id: OwnerId,
    db: DbSession,
    gateway: GatewayDep,
) -> EndSessionEarlyResponse:
    """End session early — delegates to turn_flow per D-22/D-23."""
    from app.turn_flow import end_session_early_flow

    return end_session_early_flow(
        db=db,
        gateway=gateway,
        session_id=sessionId,
        owner_id=owner_id,
    )


@router.get("/sessions/{sessionId}/evaluation", response_model=SessionDetail)
def get_evaluation(
    sessionId: UUID,
    owner_id: OwnerId,
    db: DbSession,
) -> SessionDetail:
    """Get evaluation — DB-backed response with D-30/D-31/D-32 branching."""
    session = get_session_for_owner(db, sessionId, owner_id)
    if session is None:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="session_not_found",
            message="Session not found.",
        )

    # D-30: in_progress sessions cannot have evaluations
    if session.status == "in_progress":
        raise ApiError(
            status_code=status.HTTP_409_CONFLICT,
            code="session_in_progress",
            message="Session has not completed yet. Evaluation is unavailable.",
        )

    from app.evaluation_detail import EvaluationStateError, assemble_session_detail

    try:
        detail = assemble_session_detail(db, session_id=sessionId)
    except EvaluationStateError as exc:
        raise ApiError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="validation_error",
            message="Evaluation data is corrupted for this session.",
        ) from exc

    if detail is None:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="session_not_found",
            message="Session not found.",
        )

    return detail


@router.get("/sessions/{sessionId}/replay", response_model=SessionDetail)
def get_replay(
    sessionId: UUID,
    owner_id: OwnerId,
    db: DbSession,
) -> SessionDetail:
    """Get replay — DB-backed response with terminal gate and per-turn reasoning (D-16/D-18/D-19)."""
    session = get_session_for_owner(db, sessionId, owner_id)
    if session is None:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="session_not_found",
            message="Session not found.",
        )

    # D-19: replay is terminal-only
    if session.status == "in_progress":
        raise ApiError(
            status_code=status.HTTP_409_CONFLICT,
            code="session_in_progress",
            message="Replay unavailable for in-progress sessions.",
        )

    from app.evaluation_detail import EvaluationStateError, assemble_session_detail

    try:
        detail = assemble_session_detail(db, session_id=sessionId, include_reasoning=True)
    except EvaluationStateError as exc:
        raise ApiError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="validation_error",
            message="Session data is corrupted for replay.",
        ) from exc

    if detail is None:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="session_not_found",
            message="Session not found.",
        )

    return detail
