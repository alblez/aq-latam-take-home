"""Evaluation detail assembly — thin read-side module.

Assembles a SessionDetail from persisted evaluation state:
- Competency scores joined with names/categories
- Narrative re-mapped from validated JSONB (drops internal provenance fields)
- overallScore derived at read time via derive_overall_score (never stored, D-27)

Status branching (D-30/D-31/D-32):
- Both absent → evaluation=None (D-31)
- Both present with correct count → full Evaluation
- Any other combination → EvaluationStateError (D-32, loud failure)
"""

from __future__ import annotations

import json
from typing import Any, cast
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.orm import Session as SASession

from app.engine.evaluation import derive_overall_score
from app.jsonb_schemas import CompetencyEvidence as JsonbCompetencyEvidence
from app.jsonb_schemas import EvaluationNarrative as JsonbEvaluationNarrative
from app.models import (
    CompetencyModel,
    JobModel,
    SessionCompetencyScoreModel,
    SessionModel,
    TurnModel,
)
from app.repositories import get_evaluation_detail
from app.schemas import (
    CompetencyEvidence,
    CompetencyScore,
    CompetencyStatus,
    Evaluation,
    EvaluationNarrative,
    EvidenceCoverage,
    EvidenceQuote,
    EvidenceSignal,
    JobDetail,
    NarrativeItem,
    ScoreScale,
    Session,
    SessionDetail,
    TerminalPanelState,
    Turn,
)


class EvaluationStateError(Exception):
    """Raised when persisted evaluation state is inconsistent (D-32).

    Maps to 500 validation_error at the route level — never fabricated partial data.
    """


def assemble_session_detail(
    db: SASession, *, session_id: UUID, include_reasoning: bool = False
) -> SessionDetail | None:
    """Assemble SessionDetail from persisted evaluation state.

    Returns None when session not found (caller maps to 404).
    Raises EvaluationStateError on inconsistent evaluation data (D-32).

    When include_reasoning=True, interviewer turns include validated PanelState
    reasoning (D-18). Default False preserves evaluation endpoint behavior.
    """
    data = get_evaluation_detail(db, session_id)
    if data is None:
        return None

    session = data["session"]
    job = data["job"]
    turns_list = data["turns"]
    competencies_list = data["competencies"]
    scores_list = data["scores"]

    evaluation = _triage_evaluation_state(session, competencies_list, scores_list)

    return _assemble_detail_shell(
        session=session,
        job=job,
        turns_list=turns_list,
        competencies_list=competencies_list,
        scores_list=scores_list,
        evaluation=evaluation,
        include_reasoning=include_reasoning,
    )


def _triage_evaluation_state(
    session: SessionModel,
    competencies_list: list[CompetencyModel],
    scores_list: list[SessionCompetencyScoreModel],
) -> Evaluation | None:
    """D-31/D-32: triage evaluation presence and raise on inconsistency."""
    has_narrative = session.evaluation_narrative is not None
    has_scores = len(scores_list) > 0
    comp_count = len(competencies_list)

    if not has_narrative and not has_scores:
        return None

    # D-32: exactly one artifact present is corrupted
    if not has_narrative or not has_scores:
        _raise_partial_evaluation_error(has_narrative, has_scores)

    # Both present — validate counts match
    if len(scores_list) != comp_count or comp_count <= 0:
        raise EvaluationStateError(
            f"count-mismatch: {len(scores_list)} scores vs {comp_count} competencies"
        )

    return _build_evaluation(
        session=session,
        competencies_list=competencies_list,
        scores_list=scores_list,
    )


def _raise_partial_evaluation_error(has_narrative: bool, has_scores: bool) -> None:
    """Raise the appropriate D-32 error for partial evaluation state."""
    if has_scores:
        raise EvaluationStateError("rows-without-narrative")
    raise EvaluationStateError("narrative-without-rows")


def _assemble_detail_shell(
    *,
    session: SessionModel,
    job: JobModel,
    turns_list: list[TurnModel],
    competencies_list: list[CompetencyModel],
    scores_list: list[SessionCompetencyScoreModel],
    evaluation: Evaluation | None,
    include_reasoning: bool,
) -> SessionDetail:
    """Build the SessionDetail response shell from validated components."""
    comp_count = len(competencies_list)

    session_schema = Session(
        id=session.id,
        jobId=session.job_id,
        status=cast(Any, session.status),
        completionReason=cast(Any, session.completion_reason),
        startedAt=session.started_at.isoformat() if session.started_at else None,
        completedAt=session.completed_at.isoformat() if session.completed_at else None,
    )

    job_schema = JobDetail(
        id=job.id,
        title=job.title,
        description=job.description,
        competencyCount=comp_count,
    )

    comp_statuses = _build_competency_statuses(competencies_list, scores_list)
    turn_schemas = _build_turn_schemas(turns_list, include_reasoning=include_reasoning)

    terminal_panel: TerminalPanelState | None = None
    if session.terminal_panel_state:
        try:
            terminal_panel = TerminalPanelState.model_validate(session.terminal_panel_state)
        except ValidationError as exc:
            raise EvaluationStateError(f"invalid terminal_panel_state JSONB: {exc}") from exc

    return SessionDetail(
        session=session_schema,
        job=job_schema,
        competencies=comp_statuses,
        turns=turn_schemas,
        evaluation=evaluation,
        terminalPanelState=terminal_panel,
    )


def _build_evaluation(
    *,
    session: SessionModel,
    competencies_list: list[CompetencyModel],
    scores_list: list[SessionCompetencyScoreModel],
) -> Evaluation:
    """Build full Evaluation from validated persisted state."""
    # Intentional JSON roundtrip: strict-mode Pydantic rejects string UUIDs from JSONB dicts.
    # model_validate_json(json.dumps(data)) enables JSON-mode coercion (decision 06-02).
    narrative_raw = session.evaluation_narrative
    validated_narrative = JsonbEvaluationNarrative.model_validate_json(json.dumps(narrative_raw))

    # Map narrative to API schema — explicit field-by-field (Pitfall 6)
    narrative_schema = EvaluationNarrative(
        summary=validated_narrative.summary,
        overallVerdict=validated_narrative.overallVerdict,
        strengths=[
            NarrativeItem(
                competencyId=item.competencyId,
                text=item.text,
                turnIds=item.turnIds,
            )
            for item in validated_narrative.strengths
        ],
        concerns=[
            NarrativeItem(
                competencyId=item.competencyId,
                text=item.text,
                turnIds=item.turnIds,
            )
            for item in validated_narrative.concerns
        ],
        unassessedCompetencyIds=validated_narrative.unassessedCompetencyIds,
        earlyEndNote=validated_narrative.earlyEndNote,
        modelFailureNote=validated_narrative.modelFailureNote,
    )

    # Map scores — join with competency name/category
    comp_map: dict[UUID, CompetencyModel] = {c.id: c for c in competencies_list}
    competency_scores: list[CompetencyScore] = []

    for row in scores_list:
        comp = comp_map.get(row.competency_id)
        if comp is None:
            raise EvaluationStateError(
                f"score row references unknown competency {row.competency_id}"
            )

        # Intentional JSON roundtrip: strict-mode Pydantic rejects string UUIDs from JSONB dicts.
        # model_validate_json(json.dumps(data)) enables JSON-mode coercion (decision 06-02).
        evidence_schema: CompetencyEvidence | None = None
        if row.evidence is not None:
            try:
                validated_ev = JsonbCompetencyEvidence.model_validate_json(json.dumps(row.evidence))
                evidence_schema = CompetencyEvidence(
                    schemaVersion=validated_ev.schemaVersion,
                    evaluationVersion=validated_ev.evaluationVersion,
                    coverage=EvidenceCoverage(
                        probed=validated_ev.coverage.probed,
                        assessed=validated_ev.coverage.assessed,
                        firstQuestionTurnId=validated_ev.coverage.firstQuestionTurnId,
                        questionTurnIds=validated_ev.coverage.questionTurnIds,
                        answerTurnIds=validated_ev.coverage.answerTurnIds,
                    ),
                    supportingTurnIds=validated_ev.supportingTurnIds,
                    quotes=[
                        EvidenceQuote(
                            turnId=q.turnId,
                            quote=q.quote,
                            type=q.type,
                            note=q.note,
                        )
                        for q in validated_ev.quotes
                    ],
                    signals=[
                        EvidenceSignal(
                            turnId=s.turnId,
                            flag=s.flag,
                            detail=s.detail,
                        )
                        for s in validated_ev.signals
                    ],
                    scoreRationale=validated_ev.scoreRationale,
                    unassessedReason=validated_ev.unassessedReason,
                )
            except (ValidationError, KeyError, TypeError) as exc:
                raise EvaluationStateError(
                    f"invalid evidence JSONB for competency {row.competency_id}: {exc}"
                ) from exc
        else:
            # NULL evidence on a score row is corrupted state
            raise EvaluationStateError(
                f"NULL evidence for competency {row.competency_id} — corrupted state"
            )

        competency_scores.append(
            CompetencyScore(
                competencyId=row.competency_id,
                name=comp.name,
                category=cast(Any, comp.category),
                assessed=row.assessed,
                score=row.score,
                notes=row.notes,
                evidence=evidence_schema,
            )
        )

    # Derive overall score at read time (D-27, never stored)
    overall_score = derive_overall_score(scores_list)

    return Evaluation(
        overallScore=overall_score,
        scoreScale=ScoreScale(min=1, max=10),
        competencyScores=competency_scores,
        narrative=narrative_schema,
    )


def _build_competency_statuses(
    competencies_list: list[CompetencyModel],
    scores_list: list[SessionCompetencyScoreModel],
) -> list[CompetencyStatus]:
    """Build competency status list from scores (covered if assessed)."""
    assessed_ids: set[UUID] = set()
    scored_ids: set[UUID] = set()
    for row in scores_list:
        scored_ids.add(row.competency_id)
        if row.assessed:
            assessed_ids.add(row.competency_id)

    return [
        CompetencyStatus(
            id=c.id,
            name=c.name,
            category=cast(Any, c.category),
            status=(
                "covered"
                if c.id in assessed_ids
                else ("in-progress" if c.id in scored_ids else "not-reached")
            ),
        )
        for c in competencies_list
    ]


def _build_turn_schemas(
    turns_list: list[TurnModel], *, include_reasoning: bool = False
) -> list[Turn]:
    """Build Turn schema objects from DB models.

    When include_reasoning=True, interviewer turns get validated PanelState reasoning.
    Candidate turns always get reasoning=None (D-18).
    """
    from app.schemas import PanelState as PanelStateSchema

    result: list[Turn] = []
    for t in turns_list:
        reasoning = None
        if include_reasoning and t.role == "interviewer" and t.reasoning is not None:
            try:
                reasoning = PanelStateSchema.model_validate(t.reasoning)
            except ValidationError as exc:
                raise EvaluationStateError(
                    f"invalid turn reasoning JSONB for turn {t.id}: {exc}"
                ) from exc

        result.append(
            Turn(
                id=t.id,
                clientTurnId=t.client_turn_id,
                role=cast(Any, t.role),
                turnIndex=t.turn_index,
                competencyId=t.competency_id,
                content=t.content,
                action=cast(Any, t.action),
                sourcePackItemId=getattr(t, "source_pack_item_id", None),
                inputMode=cast(Any, getattr(t, "input_mode", None)),
                audioDurationMs=getattr(t, "audio_duration_ms", None),
                reasoning=reasoning,
            ),
        )
    return result
