"""Generate question orchestration with D11 tiered fallback (CTRL-08).

Implements the three-tier fallback documented in decisions-log D11:
1. Analyze fail → degrade to no-signals policy (covered in orchestrator)
2. Generate fail → pack text verbatim when available, else generic probe
3. Both fail → generic probe immediately (pack text bypassed)

NEVER raises GatewayError — every tier returns a usable GenerateOutcome.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import structlog

from app.engine.gateway import GatewayError
from app.engine.prompts import build_follow_up_messages, build_new_topic_messages
from app.engine.rationales import GENERIC_PROBE_TEMPLATE, generate_failure_mode
from app.jsonb_schemas import Generation

if TYPE_CHECKING:
    from app.engine.gateway import ModelGateway
    from app.engine.prompts import CompetencyBrief, TranscriptTurn

logger = structlog.get_logger()


@dataclass(frozen=True, slots=True)
class GenerateOutcome:
    """Result of run_generate — always a usable question + metadata."""

    question_text: str
    generation: Generation
    failure_mode: str | None
    gateway_succeeded: bool


def _generic_probe_outcome(
    generic_probe: str,
    *,
    fallback_mode: str | None,
    failure_mode: str | None,
    answer_dependency_required: bool,
    gateway_succeeded: bool,
) -> GenerateOutcome:
    """Build a GenerateOutcome for generic probe paths."""
    return GenerateOutcome(
        question_text=generic_probe,
        generation=Generation(
            mode="generic_probe",
            fallbackMode=fallback_mode,
            answerDependencyRequired=answer_dependency_required,
        ),
        failure_mode=failure_mode,
        gateway_succeeded=gateway_succeeded,
    )


def _success_outcome(
    question_text: str,
    *,
    action: Literal["new_topic", "follow_up"],
) -> GenerateOutcome:
    """Build a GenerateOutcome for successful generation."""
    mode: Literal["targeted_follow_up", "pack_seed"] = (
        "targeted_follow_up" if action == "follow_up" else "pack_seed"
    )
    return GenerateOutcome(
        question_text=question_text,
        generation=Generation(
            mode=mode,
            fallbackMode=None,
            answerDependencyRequired=(action == "follow_up"),
        ),
        failure_mode=None,
        gateway_succeeded=True,
    )


def run_generate(
    gateway: ModelGateway,
    *,
    action: Literal["new_topic", "follow_up"],
    transcript: list[TranscriptTurn],
    competency: CompetencyBrief,
    pack_item_text: str | None,
    trigger_excerpt: str | None,
    trigger_reason: str | None,
    analyze_failed: bool,
) -> GenerateOutcome:
    """Run question generation with D11 tiered fallback.

    Per D11:
    - new_topic with no pack_item_text → generic probe immediately (no gateway call)
    - Both failed (analyze_failed + generate raises) → generic probe immediately
      (pack text BYPASSED per D11 both-fail wording)
    - Generate fail, new_topic with pack → pack text verbatim
    - Generate fail, follow_up or new_topic without pack → generic probe
    """
    generic_probe = GENERIC_PROBE_TEMPLATE.format(competency_name=competency.name)

    # --- Fast path: new_topic with no pack item → generic probe, no gateway call (D11) ---
    if action == "new_topic" and pack_item_text is None:
        if analyze_failed:
            # Both-fail: generic probe immediately, pack bypassed (D11 both-fail wording)
            return _generic_probe_outcome(
                generic_probe,
                fallback_mode="generic_probe",
                failure_mode="analyze_and_generate_failed",
                answer_dependency_required=False,
                gateway_succeeded=False,
            )
        return _generic_probe_outcome(
            generic_probe,
            fallback_mode=None,
            failure_mode=None,
            answer_dependency_required=False,
            gateway_succeeded=False,
        )

    # --- Build messages for gateway call ---
    if action == "follow_up":
        if trigger_excerpt is None or trigger_reason is None:
            msg = "follow_up requires trigger_excerpt and trigger_reason"
            raise ValueError(msg)
        messages = build_follow_up_messages(transcript, competency, trigger_excerpt, trigger_reason)
    else:
        messages = build_new_topic_messages(transcript, competency, pack_item_text)

    # --- Attempt gateway call ---
    try:
        question_text = gateway.generate_question(messages=messages)
    except GatewayError as exc:
        return _handle_generate_failure(
            exc=exc,
            action=action,
            pack_item_text=pack_item_text,
            generic_probe=generic_probe,
            analyze_failed=analyze_failed,
        )

    # --- Success ---
    return _success_outcome(question_text, action=action)


def _handle_generate_failure(
    *,
    exc: GatewayError,
    action: Literal["new_topic", "follow_up"],
    pack_item_text: str | None,
    generic_probe: str,
    analyze_failed: bool,
) -> GenerateOutcome:
    """Map generate failure to appropriate fallback tier (D11)."""
    exc_type = type(exc).__name__

    # Log fallback activation — no prompt/answer content (D-24)
    logger.error(
        "generate_fallback_activated",
        exc_type=exc_type,
        action=action,
        analyze_failed=analyze_failed,
        has_pack=pack_item_text is not None,
    )

    # Both-fail tier: generic probe immediately, pack BYPASSED (D11 both-fail wording)
    if analyze_failed:
        return _generic_probe_outcome(
            generic_probe,
            fallback_mode="generic_probe",
            failure_mode="analyze_and_generate_failed",
            answer_dependency_required=(action == "follow_up"),
            gateway_succeeded=False,
        )

    # Generate fail, new_topic with pack → pack text verbatim
    if action == "new_topic" and pack_item_text is not None:
        return GenerateOutcome(
            question_text=pack_item_text,
            generation=Generation(
                mode="pack_seed",
                fallbackMode="pack_item_verbatim",
                answerDependencyRequired=False,
            ),
            failure_mode=generate_failure_mode(exc_type),
            gateway_succeeded=False,
        )

    # Generate fail, follow_up or new_topic without pack → generic probe
    return _generic_probe_outcome(
        generic_probe,
        fallback_mode="generic_probe",
        failure_mode=generate_failure_mode(exc_type),
        answer_dependency_required=(action == "follow_up"),
        gateway_succeeded=False,
    )
