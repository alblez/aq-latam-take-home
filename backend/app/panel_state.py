"""Panel state builders for session lifecycle."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.jsonb_schemas import DEFAULT_CONTROLLER_CONFIG, ControllerConfig
from app.schemas import Generation, PanelState, PolicyState, RubricSnapshot


def build_baseline_panel_state(
    competency_ids: list[UUID],
    controller_config: ControllerConfig | None = None,
) -> PanelState:
    """Build empty baseline panel state for pre-start sessions.

    Per D-32: no current action/target, all competencies gaps/not-reached,
    policy counts zero, no flags, no trigger.
    """
    config = controller_config or DEFAULT_CONTROLLER_CONFIG

    return PanelState(
        rubricSnapshot=RubricSnapshot(
            covered=[],
            inProgress=[],
            gaps=competency_ids,
        ),
        flags=[],
        policyState=PolicyState(
            questionCount=0,
            followUpCount=0,
            minQuestions=config.minQuestions,
            minFollowUps=config.minFollowUps,
            maxQuestions=config.maxQuestions,
            maxFollowUpsPerCompetency=config.maxFollowUpsPerCompetency,
            eligibleToEnd=False,
        ),
        action="new_topic",
        targetCompetencyId=None,
        sourcePackItemId=None,
        trigger=None,
        rationale="Session created, awaiting start.",
        generation=Generation(
            mode="pack_seed",
            answerDependencyRequired=False,
        ),
        failureMode=None,
    )


def build_first_turn_panel_state(
    all_competency_ids: list[UUID],
    target_competency_id: UUID,
    source_pack_item_id: UUID,
    controller_config: ControllerConfig | None = None,
) -> PanelState:
    """Build panel state for the first interviewer turn.

    Per D-20 through D-24:
    - Target competency in inProgress, all others in gaps, covered=[]
    - policyState questionCount=1, followUpCount=0
    - action=new_topic, trigger=None (per D-23)
    """
    config = controller_config or DEFAULT_CONTROLLER_CONFIG
    gaps = [cid for cid in all_competency_ids if cid != target_competency_id]

    return PanelState(
        rubricSnapshot=RubricSnapshot(
            covered=[],
            inProgress=[target_competency_id],
            gaps=gaps,
        ),
        flags=[],
        policyState=PolicyState(
            questionCount=1,
            followUpCount=0,
            minQuestions=config.minQuestions,
            minFollowUps=config.minFollowUps,
            maxQuestions=config.maxQuestions,
            maxFollowUpsPerCompetency=config.maxFollowUpsPerCompetency,
            eligibleToEnd=False,
        ),
        action="new_topic",
        targetCompetencyId=target_competency_id,
        sourcePackItemId=source_pack_item_id,
        trigger=None,
        rationale="Opening first competency probe.",
        generation=Generation(
            mode="pack_seed",
            answerDependencyRequired=False,
        ),
        failureMode=None,
    )


def build_first_turn_reasoning(panel_state: PanelState) -> dict[str, Any]:
    """Build minimal reasoning JSONB for the first interviewer turn.

    Per D-17: enough schema-valid state for panel/replay foundations.
    Adds schemaVersion and policyVersion metadata.
    """
    data = panel_state.model_dump(mode="json")
    data["schemaVersion"] = "reasoning.v1"
    data["policyVersion"] = "v1"
    return data
