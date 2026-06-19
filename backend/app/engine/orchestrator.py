"""Engine orchestrator: process_candidate_answer pipeline (D-02, D-03/D25).

Encodes IMPLEMENTATION_DECISIONS §2 decision order:
TX-A (short read) → commit → gateway calls + pure policy (no TX) → TX-B (short write).

Does NOT import app.errors.ApiError — engine raises typed exceptions only.
Does NOT modify routes/sessions.py — /start remains untouched (D-01).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal
from uuid import UUID

import structlog
from asgi_correlation_id import correlation_id

from app.engine.evaluation import (
    EvaluationTurn,
    build_evaluation_narrative,
    build_evaluation_turns,
    build_score_rows,
)
from app.engine.gateway import GatewayError
from app.engine.generate import GenerateOutcome, run_generate
from app.engine.policy import (
    CompetencyFacts,
    Decision,
    PolicyInputs,
    compute_coverage,
    decide,
)
from app.engine.prompts import CompetencyBrief, TranscriptTurn
from app.engine.rationales import (
    ANALYZE_FAILURE_COPY,
    analyze_failure_mode,
    evaluation_failure_mode,
    user_end_rationale,
)
from app.jsonb_schemas import (
    ControllerConfig,
    Flag,
    Generation,
    PolicyState,
    RubricCompetencySnapshot,
    RubricSnapshot,
    TerminalPanelState,
    Trigger,
    TurnReasoning,
)
from app.repositories import (
    CompetencyScoreRowData,
    finalize_session_terminal,
    guard_session_in_progress,
    insert_competency_scores,
    insert_interviewer_turn,
    select_pack_item_for_competency,
    set_model_name_once,
    update_session_updated_at,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.engine.analyze import AnalyzeResponse
    from app.engine.gateway import ModelGateway
    from app.models import CompetencyModel, SessionModel, TurnModel

logger = structlog.get_logger()


# --- Pipeline result ---


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """Outcome of process_candidate_answer."""

    action: Literal["new_topic", "follow_up", "end"]
    interviewer_turn: TurnModel | None
    reasoning: dict | None
    terminal_panel_state: dict | None
    failure_mode: str | None


# --- Public entry point ---


def run_evaluation(
    gateway: ModelGateway,
    *,
    eval_turns: list[EvaluationTurn],
    comp_briefs: list[CompetencyBrief],
    transcript: list[TranscriptTurn],
    flags: list[Flag],
    coverage: dict[UUID, str],
    terminal_reason: str,
    session_id: UUID,
    job_id: UUID,
    terminal_failure_mode: str | None,
) -> tuple[dict | None, list[CompetencyScoreRowData] | None, str | None]:
    """Run evaluation gateway call and map result to persistence artifacts.

    Returns (narrative_dict, score_rows, failure_mode):
    - On success: (dict, list[CompetencyScoreRowData], None)
    - On failure: (None, None, failure_mode_str)

    MUST be called with NO open DB transaction (SESS-08/D25).
    The gateway owns the retry budget (D-03); this helper does NOT retry (D-10).

    Note: final-answer in-flight flags are included for model scoring but deterministic
    evidence signals/quotes still come from persisted eval_turns only; final-answer-only
    flags may therefore affect scores/narrative text but not persisted EvidenceSignal rows
    until a future schema/change captures them (review LOW documented, D-16 literal preserved).
    """
    # Combine persisted turn flags with in-flight final-turn flags for full signal context (D-05)
    all_flags: list[Flag] = []
    for et in eval_turns:
        all_flags.extend(et.flags)
    all_flags.extend(flags)

    try:
        parsed = gateway.evaluate_session(
            transcript=transcript,
            competencies=comp_briefs,
            flags=all_flags,
            coverage=coverage,
            terminal_reason=terminal_reason,
        )
    except GatewayError as exc:
        mode = evaluation_failure_mode(type(exc).__name__)
        logger.warning(
            "evaluation_failed",
            session_id=str(session_id),
            job_id=str(job_id),
            request_id=correlation_id.get(),
            terminal_reason=terminal_reason,
            failure_mode=mode,
        )
        return (None, None, mode)

    # Map model response to persistence artifacts
    narrative_dict = build_evaluation_narrative(
        parsed=parsed,
        eval_turns=eval_turns,
        competencies=comp_briefs,
        terminal_reason=terminal_reason,
        model_name=gateway.model_name,
        terminal_failure_mode=terminal_failure_mode,
    )
    score_rows = build_score_rows(
        session_id=session_id,
        parsed=parsed,
        eval_turns=eval_turns,
        competencies=comp_briefs,
    )
    return (narrative_dict, score_rows, None)


def process_candidate_answer(
    db: Session,
    gateway: ModelGateway,
    session: SessionModel,
    candidate_turn: TurnModel,
) -> PipelineResult:
    """Full pipeline: analyze → policy → generate → persist.

    Per D-03/D25: no DB transaction spans gateway calls.
    Per D-02: single orchestrator entry point.
    """
    # === TX-A: short read ===
    config = ControllerConfig.model_validate(session.controller_config)

    from sqlalchemy import select as sa_select

    from app.models import CompetencyModel as CM
    from app.models import TurnModel as TM

    turns = list(
        db.scalars(
            sa_select(TM).where(TM.session_id == session.id).order_by(TM.turn_index.asc())
        ).all()
    )
    competencies = list(
        db.scalars(
            sa_select(CM)
            .where(CM.job_id == session.job_id)
            .order_by(CM.sort_order.asc(), CM.name.asc())
        ).all()
    )

    # Derive pure data structures while ORM instances are still valid (SESS-08/D25).
    # These must precede db.commit() because expire_on_commit=True would autobegin a
    # new transaction on first attribute access after commit.
    comp_facts = _derive_competency_facts(turns, competencies)
    policy_inputs = _build_policy_inputs(config, turns, comp_facts)
    transcript = _build_transcript(turns)
    # Pitfall 2: capture richer turn snapshot for evaluation while ORM instances are live;
    # _handle_end cannot reconstruct after TX-A commit (expire_on_commit=True).
    eval_turns = build_evaluation_turns(turns)

    comp_briefs = [CompetencyBrief(id=c.id, name=c.name, category=c.category) for c in competencies]

    # Capture scalar IDs before commit — expire_on_commit=True makes lazy access
    # implicitly reopen a transaction (CR-01: would hold TX during gateway call).
    session_id_val = session.id
    session_job_id = session.job_id
    candidate_turn_index = candidate_turn.turn_index

    # MANDATORY: close TX-A before any gateway call (D-03/D25/Pitfall 6)
    db.commit()

    # === No transaction: gateway calls + pure policy ===

    # Analyze
    analyze_failed_mode: str | None = None
    flags: list[Flag] = []

    try:
        analyze_result: AnalyzeResponse = gateway.analyze_answer(
            transcript=transcript, competencies=comp_briefs
        )
        flags = analyze_result.flags
    except GatewayError as exc:
        analyze_failed_mode = analyze_failure_mode(type(exc).__name__)
        logger.error("analyze_failed", failure_mode=analyze_failed_mode)

    # Policy decision
    policy_inputs_with_flags = PolicyInputs(
        config=policy_inputs.config,
        competencies=policy_inputs.competencies,
        current_competency_id=policy_inputs.current_competency_id,
        question_count=policy_inputs.question_count,
        follow_up_count=policy_inputs.follow_up_count,
        follow_ups_by_competency=policy_inputs.follow_ups_by_competency,
        flags=flags,
    )
    decision = decide(policy_inputs_with_flags)

    # End action — no generate needed
    if decision.action == "end":
        return _handle_end(
            db=db,
            gateway=gateway,
            session_id=session_id_val,
            config=config,
            decision=decision,
            comp_facts=comp_facts,
            policy_inputs=policy_inputs_with_flags,
            flags=flags,
            analyze_failed_mode=analyze_failed_mode,
            eval_turns=eval_turns,
            transcript=transcript,
            comp_briefs=comp_briefs,
            session_job_id=session_job_id,
        )

    # Generate for non-end actions
    return _handle_continue(
        db=db,
        gateway=gateway,
        session=session,
        candidate_turn=candidate_turn,
        candidate_turn_index=candidate_turn_index,
        config=config,
        decision=decision,
        comp_facts=comp_facts,
        policy_inputs=policy_inputs_with_flags,
        transcript=transcript,
        competencies=competencies,
        flags=flags,
        analyze_failed_mode=analyze_failed_mode,
    )


# --- Exported derivation helpers (tested in fast suite) ---


def _build_transcript(turns: list[TurnModel]) -> list[TranscriptTurn]:
    """Build transcript preserving turn order and mapping roles."""
    return [
        TranscriptTurn(role=t.role, content=t.content)  # type: ignore[arg-type]
        for t in turns
    ]


def _interviewer_turns(turns: list[TurnModel]) -> list[TurnModel]:
    """Filter to interviewer-role turns only."""
    return [t for t in turns if t.role == "interviewer"]


def _follow_ups_by_competency(interviewer_turns: list[TurnModel]) -> dict[UUID, int]:
    """Count follow-up actions grouped by competency ID."""
    result: dict[UUID, int] = {}
    for t in interviewer_turns:
        if t.action == "follow_up":
            cid = t.competency_id
            result[cid] = result.get(cid, 0) + 1
    return result


def _current_competency_id(
    interviewer_turns: list[TurnModel],
    competencies: list,
    fallback_error: str,
) -> UUID:
    """Resolve active competency: latest interviewer turn or first competency as fallback."""
    if not interviewer_turns:
        if not competencies:
            raise ValueError(fallback_error)
        return competencies[0].id
    return interviewer_turns[-1].competency_id


def _build_policy_inputs(
    config: ControllerConfig,
    turns: list[TurnModel],
    competencies: list[CompetencyFacts],
) -> PolicyInputs:
    """Derive PolicyInputs from persisted turns (D-16)."""
    i_turns = _interviewer_turns(turns)
    question_count = len(i_turns)
    follow_up_count = sum(1 for t in i_turns if t.action == "follow_up")
    fu_by_comp = _follow_ups_by_competency(i_turns)
    current_comp_id = _current_competency_id(
        i_turns, competencies, "No competencies found for policy inputs"
    )

    return PolicyInputs(
        config=config,
        competencies=competencies,
        current_competency_id=current_comp_id,
        question_count=question_count,
        follow_up_count=follow_up_count,
        follow_ups_by_competency=fu_by_comp,
        flags=[],  # flags added after analyze
    )


def _derive_competency_facts(
    turns: list[TurnModel],
    competencies: list[CompetencyModel],
) -> list[CompetencyFacts]:
    """Derive CompetencyFacts from persisted turns and competency models."""
    # Count interviewer questions per competency
    questions_per_comp: dict[UUID, int] = {}
    for t in turns:
        if t.role == "interviewer":
            questions_per_comp[t.competency_id] = questions_per_comp.get(t.competency_id, 0) + 1

    # Determine has_candidate_answer: candidate turn at index i follows interviewer at i-1
    answered_competencies: set[UUID] = set()
    for i, t in enumerate(turns):
        if t.role == "candidate" and i > 0:
            prev = turns[i - 1]
            if prev.role == "interviewer":
                answered_competencies.add(prev.competency_id)

    return [
        CompetencyFacts(
            id=c.id,
            name=c.name,
            category=c.category,
            sort_order=c.sort_order,
            questions_asked=questions_per_comp.get(c.id, 0),
            has_candidate_answer=c.id in answered_competencies,
        )
        for c in competencies
    ]


def _trigger_excerpt(flag: Flag) -> str:
    """Extract trigger excerpt: prefer answerExcerpt, fall back to detail, cap at 240."""
    text = flag.answerExcerpt or flag.detail
    return text[:240]


def _resolve_source_pack_item_id(
    outcome: GenerateOutcome, pack_item_id: UUID | None
) -> UUID | None:
    """Only set source_pack_item_id when generation.mode == 'pack_seed' and we had a pack item."""
    if outcome.generation.mode == "pack_seed" and pack_item_id is not None:
        return pack_item_id
    return None


def _combined_failure_mode(
    analyze_failed_mode: str | None, outcome_failure_mode: str | None
) -> str | None:
    """Merge analyze + generate failure modes per D-11 precedence."""
    if analyze_failed_mode and outcome_failure_mode == "analyze_and_generate_failed":
        return "analyze_and_generate_failed"
    return analyze_failed_mode or outcome_failure_mode


def _continue_rationale(decision: Decision, analyze_failed_mode: str | None) -> str:
    """Append analyze failure suffix when applicable (D-36)."""
    rationale = decision.rationale
    if analyze_failed_mode is not None:
        rationale = f"{rationale} — {ANALYZE_FAILURE_COPY}"
    return rationale


def _continue_trigger(decision: Decision, candidate_turn_id: UUID) -> Trigger | None:
    """Build trigger metadata for follow_up actions."""
    if decision.action == "follow_up" and decision.trigger_flag is not None:
        return Trigger(
            turnId=candidate_turn_id,
            answerExcerpt=_trigger_excerpt(decision.trigger_flag),
            reason=decision.trigger_flag.flag,
        )
    return None


# --- Internal pipeline helpers ---


def _handle_end(
    *,
    db: Session,
    gateway: ModelGateway,
    session_id: UUID,
    config: ControllerConfig,
    decision: Decision,
    comp_facts: list[CompetencyFacts],
    policy_inputs: PolicyInputs,
    flags: list[Flag],
    analyze_failed_mode: str | None,
    eval_turns: list[EvaluationTurn],
    transcript: list[TranscriptTurn],
    comp_briefs: list[CompetencyBrief],
    session_job_id: UUID,
) -> PipelineResult:
    """Handle end action: build + validate TerminalPanelState, evaluate, finalize session."""
    coverage = compute_coverage(
        comp_facts,
        policy_inputs.current_competency_id,
        "end",
        None,
    )
    uncovered_ids = [cid for cid, status in coverage.items() if status != "covered"]

    rubric = _build_rubric_snapshot(comp_facts, coverage, policy_inputs)
    policy_state = _build_policy_state(config, policy_inputs, decision)

    assert decision.completion_reason is not None  # noqa: S101

    terminal = TerminalPanelState(
        schemaVersion="terminal_panel_state.v1",
        policyVersion="v1",
        action="end",
        completionReason=decision.completion_reason,
        endedBy="controller",
        rubricSnapshot=rubric,
        flags=flags,
        policyState=policy_state,
        targetCompetencyId=None,
        sourcePackItemId=None,
        trigger=None,
        uncoveredCompetencyIds=uncovered_ids,
        rationale=decision.rationale,
        generation=Generation(mode="terminal", fallbackMode=None, answerDependencyRequired=False),
        failureMode=analyze_failed_mode,
    )
    terminal_dict = terminal.model_dump(mode="json")

    # === Evaluation call — NO open transaction (D-03/D25/SESS-08) ===
    # Worst-case synchronous evaluation may outlive a browser/proxy request timeout;
    # server-side finalization remains idempotent and retry/GET state returns terminal
    # DB truth (D-04/D-26 latency story).
    narrative_dict, score_rows, eval_failure_mode = run_evaluation(
        gateway,
        eval_turns=eval_turns,
        comp_briefs=comp_briefs,
        transcript=transcript,
        flags=flags,
        coverage=coverage,
        terminal_reason=decision.completion_reason,
        session_id=session_id,
        job_id=session_job_id,
        terminal_failure_mode=analyze_failed_mode,
    )

    # === TX-B: short write ===
    guard_session_in_progress(db, session_id=session_id)

    now = datetime.now(UTC)
    # D-05: set model_name if analyze OR evaluation succeeded
    any_gateway_succeeded = (analyze_failed_mode is None) or (eval_failure_mode is None)
    if any_gateway_succeeded:
        set_model_name_once(db, session_id=session_id, model_name=gateway.model_name)

    finalize_session_terminal(
        db,
        session_id=session_id,
        completion_reason=decision.completion_reason,
        terminal_panel_state=terminal_dict,
        completed_at=now,
        status="completed",
        evaluation_narrative=narrative_dict,
    )

    # Persist score rows in same TX-B when evaluation succeeded (D-26)
    if score_rows is not None:
        insert_competency_scores(db, rows=score_rows)

    db.commit()

    return PipelineResult(
        action="end",
        interviewer_turn=None,
        reasoning=None,
        terminal_panel_state=terminal_dict,
        failure_mode=analyze_failed_mode,
    )


def _handle_continue(
    *,
    db: Session,
    gateway: ModelGateway,
    session: SessionModel,
    candidate_turn: TurnModel,
    candidate_turn_index: int,
    config: ControllerConfig,
    decision: Decision,
    comp_facts: list[CompetencyFacts],
    policy_inputs: PolicyInputs,
    transcript: list[TranscriptTurn],
    competencies: list[CompetencyModel],
    flags: list[Flag],
    analyze_failed_mode: str | None,
) -> PipelineResult:
    """Handle new_topic/follow_up: generate question, build reasoning, persist turn."""
    assert decision.target_competency_id is not None  # noqa: S101

    # Resolve target competency brief
    target_comp = next(c for c in competencies if c.id == decision.target_competency_id)
    target_brief = CompetencyBrief(
        id=target_comp.id, name=target_comp.name, category=target_comp.category
    )

    # Pack item selection (new_topic only)
    pack_item_text: str | None = None
    pack_item_id: UUID | None = None
    if decision.action == "new_topic":
        pack_item = select_pack_item_for_competency(
            db, session_id=session.id, competency_id=decision.target_competency_id
        )
        if pack_item is not None:
            pack_item_text = pack_item.prompt_text
            pack_item_id = pack_item.id

    # Use pre-commit captured values (CR-01/WR-03: avoid lazy load after TX-A commit)
    candidate_turn_id = candidate_turn.id
    next_turn_index = candidate_turn_index + 1

    # D-03/D25: commit after pack selection to release connection before gateway call
    db.commit()

    # Trigger excerpt for follow-up
    trigger_excerpt: str | None = None
    trigger_reason: str | None = None
    if decision.trigger_flag is not None:
        trigger_excerpt = _trigger_excerpt(decision.trigger_flag)
        trigger_reason = decision.trigger_flag.flag

    # Generate question
    outcome: GenerateOutcome = run_generate(
        gateway,
        action=decision.action,  # type: ignore[arg-type]
        transcript=transcript,
        competency=target_brief,
        pack_item_text=pack_item_text,
        trigger_excerpt=trigger_excerpt,
        trigger_reason=trigger_reason,
        analyze_failed=analyze_failed_mode is not None,
    )

    # Derive reasoning fields
    source_pack_item_id = _resolve_source_pack_item_id(outcome, pack_item_id)
    combined_failure = _combined_failure_mode(analyze_failed_mode, outcome.failure_mode)
    rationale = _continue_rationale(decision, analyze_failed_mode)
    trigger = _continue_trigger(decision, candidate_turn_id)

    coverage = compute_coverage(
        comp_facts,
        policy_inputs.current_competency_id,
        decision.action,
        decision.target_competency_id,
    )
    rubric = _build_rubric_snapshot(comp_facts, coverage, policy_inputs)
    policy_state = _build_policy_state(config, policy_inputs, decision)

    reasoning = TurnReasoning(
        schemaVersion="reasoning.v1",
        policyVersion="v1",
        rubricSnapshot=rubric,
        flags=flags,
        policyState=policy_state,
        action=decision.action,  # type: ignore[arg-type]
        targetCompetencyId=decision.target_competency_id,
        sourcePackItemId=source_pack_item_id,
        trigger=trigger,
        rationale=rationale,
        generation=outcome.generation,
        failureMode=combined_failure,
    )
    reasoning_dict = reasoning.model_dump(mode="json")

    # === TX-B: short write ===
    guard_session_in_progress(db, session_id=session.id)

    new_turn = insert_interviewer_turn(
        db,
        session_id=session.id,
        turn_index=next_turn_index,
        competency_id=decision.target_competency_id,
        content=outcome.question_text,
        action=decision.action,
        source_pack_item_id=source_pack_item_id,
        reasoning=reasoning_dict,
    )

    # D-05: set model_name if any gateway call succeeded this turn
    any_gateway_succeeded = (analyze_failed_mode is None) or outcome.gateway_succeeded
    if any_gateway_succeeded:
        set_model_name_once(db, session_id=session.id, model_name=gateway.model_name)

    update_session_updated_at(db, session_id=session.id)
    db.commit()

    return PipelineResult(
        action=decision.action,
        interviewer_turn=new_turn,
        reasoning=reasoning_dict,
        terminal_panel_state=None,
        failure_mode=combined_failure,
    )


# --- Shared builders ---


def _build_rubric_snapshot(
    comp_facts: list[CompetencyFacts],
    coverage: dict[UUID, str],
    policy_inputs: PolicyInputs,
) -> RubricSnapshot:
    """Build RubricSnapshot from coverage map and facts."""
    covered_ids = [cid for cid, s in coverage.items() if s == "covered"]
    in_progress_ids = [cid for cid, s in coverage.items() if s == "in-progress"]
    gap_ids = [cid for cid, s in coverage.items() if s == "not-reached"]

    # Per-competency detail with follow-up counts and evidence turn IDs
    comp_snapshots = []
    for cf in comp_facts:
        fu_count = policy_inputs.follow_ups_by_competency.get(cf.id, 0)
        comp_snapshots.append(
            RubricCompetencySnapshot(
                id=cf.id,
                status=coverage[cf.id],  # type: ignore[arg-type]
                category=cf.category,  # type: ignore[arg-type]
                followUpCount=fu_count,
            )
        )

    return RubricSnapshot(
        covered=covered_ids,
        inProgress=in_progress_ids,
        gaps=gap_ids,
        competencies=comp_snapshots,
    )


def _build_policy_state(
    config: ControllerConfig,
    policy_inputs: PolicyInputs,
    decision: Decision,
) -> PolicyState:
    """Build PolicyState for reasoning JSONB."""
    fu_by_comp = {str(k): v for k, v in policy_inputs.follow_ups_by_competency.items()}
    return PolicyState(
        questionCount=policy_inputs.question_count,
        followUpCount=policy_inputs.follow_up_count,
        minQuestions=config.minQuestions,
        minFollowUps=config.minFollowUps,
        maxQuestions=config.maxQuestions,
        maxFollowUpsPerCompetency=config.maxFollowUpsPerCompetency,
        followUpCountsByCompetency=fu_by_comp if fu_by_comp else None,
        eligibleToEnd=decision.eligible_to_end,
    )


# --- User-initiated end-early (D-23) ---


@dataclass(frozen=True, slots=True)
class EndEarlyData:
    """Pre-commit snapshot for end-early flow (Pattern 4 step 1).

    Captures everything the flow needs before releasing the DB session,
    so the caller can commit immediately and proceed lock-free to evaluation.
    """

    terminal_dict: dict
    eval_turns: list[EvaluationTurn]
    comp_briefs: list[CompetencyBrief]
    transcript: list[TranscriptTurn]
    coverage: dict[UUID, str]
    turn_count: int
    session_id: UUID
    job_id: UUID


def build_end_early_terminal(
    db: Session,
    session: SessionModel,
) -> EndEarlyData:
    """Build terminal panel state + evaluation snapshot for user-initiated early end per D-23.

    Reuses _build_rubric_snapshot and _build_policy_state.
    No gateway call — short DB read only.
    Returns EndEarlyData with terminal dict + all fields needed for post-commit evaluation.
    """
    from sqlalchemy import select as sa_select

    from app.models import CompetencyModel as CM
    from app.models import TurnModel as TM

    config = ControllerConfig.model_validate(session.controller_config)

    turns = list(
        db.scalars(
            sa_select(TM).where(TM.session_id == session.id).order_by(TM.turn_index.asc())
        ).all()
    )
    competencies = list(
        db.scalars(
            sa_select(CM)
            .where(CM.job_id == session.job_id)
            .order_by(CM.sort_order.asc(), CM.name.asc())
        ).all()
    )

    comp_facts = _derive_competency_facts(turns, competencies)
    policy_inputs = _build_policy_inputs(config, turns, comp_facts)

    # Compute coverage with end action
    coverage = compute_coverage(
        comp_facts,
        policy_inputs.current_competency_id,
        "end",
        None,
    )
    uncovered_ids = [cid for cid, s in coverage.items() if s != "covered"]

    rubric = _build_rubric_snapshot(comp_facts, coverage, policy_inputs)

    # Build policy state manually (no Decision object for user-end)
    fu_by_comp = {str(k): v for k, v in policy_inputs.follow_ups_by_competency.items()}
    policy_state = PolicyState(
        questionCount=policy_inputs.question_count,
        followUpCount=policy_inputs.follow_up_count,
        minQuestions=config.minQuestions,
        minFollowUps=config.minFollowUps,
        maxQuestions=config.maxQuestions,
        maxFollowUpsPerCompetency=config.maxFollowUpsPerCompetency,
        followUpCountsByCompetency=fu_by_comp if fu_by_comp else None,
        eligibleToEnd=False,  # User-end bypasses eligibility check
    )

    # Rationale per D-25
    covered_count = sum(1 for s in coverage.values() if s == "covered")
    total_count = len(competencies)
    rationale = user_end_rationale(
        question_count=policy_inputs.question_count,
        question_max=config.maxQuestions,
        covered_count=covered_count,
        total_count=total_count,
    )

    terminal = TerminalPanelState(
        schemaVersion="terminal_panel_state.v1",
        policyVersion="v1",
        action="end",
        completionReason="ended_early",
        endedBy="user",
        rubricSnapshot=rubric,
        flags=[],  # D-24: no analysis ran for user-end
        policyState=policy_state,
        targetCompetencyId=None,
        sourcePackItemId=None,
        trigger=None,
        uncoveredCompetencyIds=uncovered_ids,
        rationale=rationale,
        generation=Generation(mode="terminal", fallbackMode=None, answerDependencyRequired=False),
        failureMode=None,
    )
    terminal_dict = terminal.model_dump(mode="json")

    # Capture evaluation inputs while ORM instances are live (Pitfall 2)
    eval_turns = build_evaluation_turns(turns)
    transcript = _build_transcript(turns)
    comp_briefs = [CompetencyBrief(id=c.id, name=c.name, category=c.category) for c in competencies]

    return EndEarlyData(
        terminal_dict=terminal_dict,
        eval_turns=eval_turns,
        comp_briefs=comp_briefs,
        transcript=transcript,
        coverage=coverage,
        turn_count=len(turns),
        session_id=session.id,
        job_id=session.job_id,
    )


def end_session_early(
    db: Session,
    session: SessionModel,
) -> dict:
    """Build terminal panel state for user-initiated early end per D-23.

    Thin wrapper for backward compatibility — delegates to build_end_early_terminal.
    Returns terminal panel state dict only.
    """
    data = build_end_early_terminal(db, session)
    return data.terminal_dict
