"""Centralized rationale and failure-string vocabulary for the interview engine.

All template strings the engine persists in reasoning JSONB are defined here.
Tests assert exact strings (D-37). Consumed by policy.decide() and orchestrator.

Per D-36: spec-verbatim strings from docs/decisions-log.md and platform spec.
Per D-38: rationale strings use human competency NAME, never bare IDs.
"""

from __future__ import annotations

# --- Spec-verbatim constants (D-36) ---

ANALYZE_FAILURE_COPY: str = "analysis unavailable this turn"
"""Panel copy when analyze call fails. Spec-verbatim from decisions-log D11."""

GENERIC_PROBE_TEMPLATE: str = "Can you tell me more about your experience with {competency_name}?"
"""Generate fallback when no pack item available. Spec-verbatim from decisions-log D11."""

# --- Failure/fallback vocabulary (D-26) ---

FAILURE_MODES: tuple[str, ...] = (
    "analyze_timeout",
    "analyze_http_error",
    "analyze_invalid_output",
    "generate_timeout",
    "generate_http_error",
    "generate_invalid_output",
    "analyze_and_generate_failed",
)
"""Exhaustive set of failureMode values persisted in reasoning JSONB."""

FALLBACK_MODES: tuple[str, ...] = (
    "pack_item_verbatim",
    "generic_probe",
)
"""Exhaustive set of fallbackMode values persisted in reasoning JSONB."""

# --- Signal-to-human-phrase mapping (D-35, D-38) ---

SIGNAL_PHRASES: dict[str, str] = {
    "contradiction": "a contradiction",
    "vague_claim": "a vague claim",
    "no_evidence": "a claim without evidence",
    "interesting_thread": "an interesting thread",
    "tradeoff_mentioned": "a tradeoff mentioned",
    "metric_mentioned": "a metric mentioned",
    "specific_tool_mentioned": "a specific tool mentioned",
    "well_covered": "a well-covered answer",
}
"""Maps FlagLiteral values to human-readable phrases for rationale strings."""


# --- Template functions (D-35, D-37, D-38) ---


def follow_up_rationale(
    signal: str,
    competency_name: str,
    comp_follow_up_n: int,
    comp_follow_up_max: int,
    question_n: int,
    question_max: int,
) -> str:
    """Rationale for a follow_up decision. Per D-35: shows policy arithmetic."""
    phrase = SIGNAL_PHRASES[signal]
    return (
        f"Following up on {phrase} in {competency_name} "
        f"(follow-up {comp_follow_up_n}/{comp_follow_up_max} for this competency, "
        f"question {question_n}/{question_max})."
    )


def new_topic_rationale(
    competency_name: str,
    gaps_remaining: int,
    question_n: int,
    question_max: int,
) -> str:
    """Rationale for a new_topic decision. Per D-35: shows gaps + question budget."""
    return (
        f"Moving to {competency_name} \u2014 "
        f"{gaps_remaining} competencies remain (question {question_n}/{question_max})."
    )


def reprobe_rationale(
    competency_name: str,
    question_n: int,
    question_max: int,
) -> str:
    """Rationale for re-probing a covered competency to reach minimums (D-14)."""
    return (
        f"Re-probing {competency_name} to reach interview minimums "
        f"(question {question_n}/{question_max})."
    )


def end_rationale(
    reason: str,
    question_count: int,
    follow_up_count: int,
) -> str:
    """Rationale for ending the interview. Two documented reasons."""
    if reason == "all_competencies_covered":
        return (
            f"Ending: all competencies covered "
            f"(questions {question_count}, follow-ups {follow_up_count})."
        )
    # question_cap
    return f"Ending: question cap reached at question {question_count}."


def user_end_rationale(
    question_count: int,
    question_max: int,
    covered_count: int,
    total_count: int,
) -> str:
    """Rationale for user-initiated early end per D-25.

    Policy-math style: one sentence with counts and human-readable totals.
    """
    return (
        f"Ended early by candidate after question {question_count} of {question_max} \u2014 "
        f"{covered_count} of {total_count} competencies covered."
    )


# --- Failure-mode mapping helpers (consumed by plan 06-05 orchestrator) ---


def analyze_failure_mode(exc_type_name: str) -> str:
    """Map gateway exception type to analyze failureMode string."""
    mapping: dict[str, str] = {
        "GatewayTimeout": "analyze_timeout",
        "GatewayHTTPError": "analyze_http_error",
        "GatewayParseError": "analyze_invalid_output",
        "TransportError": "analyze_http_error",
        "ValidationError": "analyze_invalid_output",
        "RepairFailedError": "analyze_invalid_output",
    }
    return mapping.get(exc_type_name, "analyze_http_error")


def generate_failure_mode(exc_type_name: str) -> str:
    """Map gateway exception type to generate failureMode string."""
    mapping: dict[str, str] = {
        "GatewayTimeout": "generate_timeout",
        "GatewayHTTPError": "generate_http_error",
        "GatewayParseError": "generate_invalid_output",
        "TransportError": "generate_http_error",
        "ValidationError": "generate_invalid_output",
        "RepairFailedError": "generate_invalid_output",
    }
    return mapping.get(exc_type_name, "generate_http_error")


# --- Evaluation rationale constants (D-13, D-24, D-26, plan 03) ---

UNPROBED_REASON: str = (
    "Competency not probed during interview \u2014 no questions were asked in this area."
)
"""D-24: locked text for unprobed competency score rows."""

INSUFFICIENT_SIGNAL_REASON: str = (
    "Competency was probed but the interview did not produce enough signal to assess."
)
"""Defensive D-26 path: probed but model-unassessed."""

EVALUATION_UNAVAILABLE_COPY: str = (
    "Evaluation unavailable for this session; transcript/session was saved."
)
"""D-13: deliberately omits 'try again later' — v1 has no retry per D-10."""

EARLY_END_NOTE: str = (
    "Interview was ended early by the candidate; "
    "competencies that were not probed were not assessed."
)
"""Note appended to evaluation narrative when session ended early."""

MODEL_FAILURE_NOTE: str = (
    "A model failure occurred during the interview; "
    "this evaluation was generated from the available signals."
)
"""Note appended to evaluation narrative when a terminal failure mode occurred."""


def evaluation_failure_mode(exc_type_name: str) -> str:
    """Map gateway exception type to evaluation failureMode string.

    Mirrors analyze_failure_mode shape with evaluation_* vocabulary.
    """
    mapping: dict[str, str] = {
        "GatewayTimeout": "evaluation_timeout",
        "GatewayHTTPError": "evaluation_http_error",
        "GatewayParseError": "evaluation_invalid_output",
    }
    return mapping.get(exc_type_name, "evaluation_http_error")
