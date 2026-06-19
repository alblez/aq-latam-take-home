"""Strict JSONB schema models: ControllerConfig, Flag, TurnReasoning validators."""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.jsonb_schemas import (
    DEFAULT_CONTROLLER_CONFIG,
    ControllerConfig,
    Flag,
)


def test_default_controller_config_values() -> None:
    cfg = DEFAULT_CONTROLLER_CONFIG
    assert cfg.minQuestions == 6
    assert cfg.minFollowUps == 2
    assert cfg.maxQuestions == 12
    assert cfg.maxFollowUpsPerCompetency == 2


def test_controller_config_rejects_min_above_max_questions() -> None:
    with pytest.raises(ValidationError):
        ControllerConfig(
            policyVersion="v1",
            minQuestions=10,
            minFollowUps=2,
            maxQuestions=6,
            maxFollowUpsPerCompetency=2,
        )


def test_controller_config_rejects_min_follow_ups_above_max_questions() -> None:
    with pytest.raises(ValidationError):
        ControllerConfig(
            policyVersion="v1",
            minQuestions=1,
            minFollowUps=20,
            maxQuestions=6,
            maxFollowUpsPerCompetency=2,
        )


def test_flag_requires_known_literal_and_detail() -> None:
    flag = Flag(flag="contradiction", detail="said X then not-X", competencyId=uuid4())
    assert flag.flag == "contradiction"
    with pytest.raises(ValidationError):
        Flag(flag="not_a_signal", detail="x")  # type: ignore[arg-type]


def test_flag_forbids_extra_fields() -> None:
    with pytest.raises(ValidationError):
        Flag(flag="vague_claim", detail="x", unexpected="nope")  # type: ignore[call-arg]
