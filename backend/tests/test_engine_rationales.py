"""Rationale templates and failure-mode vocabulary."""

from __future__ import annotations

import pytest

from app.engine.rationales import (
    SIGNAL_PHRASES,
    analyze_failure_mode,
    end_rationale,
    evaluation_failure_mode,
    follow_up_rationale,
    generate_failure_mode,
    new_topic_rationale,
    reprobe_rationale,
    user_end_rationale,
)


def test_follow_up_rationale_includes_signal_and_counts() -> None:
    text = follow_up_rationale("contradiction", "Communication", 1, 2, 4, 12)
    assert "a contradiction" in text
    assert "Communication" in text
    assert "follow-up 1/2" in text
    assert "question 4/12" in text


def test_new_topic_rationale_reports_gaps() -> None:
    text = new_topic_rationale("System Design", 3, 5, 12)
    assert "System Design" in text
    assert "3 competencies remain" in text
    assert "question 5/12" in text


def test_reprobe_rationale_mentions_minimums() -> None:
    text = reprobe_rationale("Testing", 7, 12)
    assert "Re-probing Testing" in text
    assert "question 7/12" in text


def test_end_rationale_branches() -> None:
    covered = end_rationale("all_competencies_covered", 8, 3)
    assert "all competencies covered" in covered
    cap = end_rationale("question_cap", 12, 4)
    assert "question cap reached at question 12" in cap


def test_user_end_rationale_reports_coverage() -> None:
    text = user_end_rationale(5, 12, 2, 4)
    assert "Ended early by candidate after question 5 of 12" in text
    assert "2 of 4 competencies covered" in text


@pytest.mark.parametrize(
    ("exc_name", "expected"),
    [
        ("GatewayTimeout", "analyze_timeout"),
        ("GatewayParseError", "analyze_invalid_output"),
        ("SomethingElse", "analyze_http_error"),
    ],
)
def test_analyze_failure_mode_mapping(exc_name: str, expected: str) -> None:
    assert analyze_failure_mode(exc_name) == expected


def test_generate_and_evaluation_failure_modes() -> None:
    assert generate_failure_mode("GatewayTimeout") == "generate_timeout"
    assert generate_failure_mode("Other") == "generate_http_error"
    assert evaluation_failure_mode("GatewayParseError") == "evaluation_invalid_output"
    assert evaluation_failure_mode("Other") == "evaluation_http_error"


def test_signal_phrases_cover_all_signals() -> None:
    assert SIGNAL_PHRASES["vague_claim"] == "a vague claim"
    assert len(SIGNAL_PHRASES) == 8
