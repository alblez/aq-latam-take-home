from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

# --- 8-value flag literal (shared by Flag.flag and strict Trigger.reason) ---

FlagLiteral = Literal[
    "vague_claim",
    "no_evidence",
    "interesting_thread",
    "contradiction",
    "well_covered",
    "tradeoff_mentioned",
    "metric_mentioned",
    "specific_tool_mentioned",
]


# --- Controller config (existing) ---


class ControllerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    policyVersion: Literal["v1"]
    minQuestions: int = Field(ge=1)
    minFollowUps: int = Field(ge=0)
    maxQuestions: int = Field(ge=1)
    maxFollowUpsPerCompetency: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_bounds(self) -> ControllerConfig:
        if self.minQuestions > self.maxQuestions:
            raise ValueError("minQuestions must be less than or equal to maxQuestions")
        if self.minFollowUps > self.maxQuestions:
            raise ValueError("minFollowUps must be less than or equal to maxQuestions")
        return self


class Flag(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    flag: FlagLiteral
    detail: str = Field(min_length=1)
    competencyId: UUID | None = None
    triggerTurnId: UUID | None = None
    answerExcerpt: str | None = None


class Generation(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    mode: Literal["pack_seed", "targeted_follow_up", "generic_probe", "terminal"]
    fallbackMode: str | None = None
    answerDependencyRequired: bool


DEFAULT_CONTROLLER_CONFIG = ControllerConfig(
    policyVersion="v1",
    minQuestions=6,
    minFollowUps=2,
    maxQuestions=12,
    maxFollowUpsPerCompetency=2,
)


# --- Strict sub-models for turn reasoning / terminal panel state ---


class RubricCompetencySnapshot(BaseModel):
    """Strict per-competency snapshot in rubric (mirrors schemas.RubricCompetencySnapshot)."""

    model_config = ConfigDict(extra="forbid", strict=True)

    id: UUID
    status: Literal["covered", "in-progress", "not-reached"]
    category: Literal["behavioral", "technical"] | None = None
    evidenceTurnIds: list[UUID] | None = None
    followUpCount: int | None = Field(default=None, ge=0)
    signalSummary: str | None = None


class RubricSnapshot(BaseModel):
    """Strict rubric coverage snapshot (mirrors schemas.RubricSnapshot)."""

    model_config = ConfigDict(extra="forbid", strict=True)

    covered: list[UUID]
    inProgress: list[UUID]
    gaps: list[UUID]
    competencies: list[RubricCompetencySnapshot] | None = None


class PolicyState(BaseModel):
    """Strict policy counters and limits (mirrors schemas.PolicyState)."""

    model_config = ConfigDict(extra="forbid", strict=True)

    questionCount: int = Field(ge=0)
    followUpCount: int = Field(ge=0)
    minQuestions: int
    minFollowUps: int
    maxQuestions: int
    maxFollowUpsPerCompetency: int
    followUpCountsByCompetency: dict[str, int] | None = None
    eligibleToEnd: bool


class Trigger(BaseModel):
    """Strict trigger reference (reason constrained to flag literal)."""

    model_config = ConfigDict(extra="forbid", strict=True)

    turnId: UUID
    answerExcerpt: str = Field(min_length=1)
    reason: FlagLiteral


# --- TurnReasoning (persisted in turns.reasoning JSONB) ---


class TurnReasoning(BaseModel):
    """Strict validation for turns.reasoning JSONB column (CTRL-09).

    SchemaVersion: reasoning.v1
    action is never "end" — terminal state lives on sessions, not turns.
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    schemaVersion: Literal["reasoning.v1"]
    policyVersion: Literal["v1"]
    rubricSnapshot: RubricSnapshot
    flags: list[Flag] = Field(max_length=8)
    policyState: PolicyState
    action: Literal["new_topic", "follow_up"]
    targetCompetencyId: UUID | None = None
    sourcePackItemId: UUID | None = None
    trigger: Trigger | None = None
    rationale: str = Field(min_length=1)
    generation: Generation
    failureMode: str | None = None

    @model_validator(mode="after")
    def follow_up_requires_trigger(self) -> TurnReasoning:
        if self.action == "follow_up":
            if self.trigger is None:
                raise ValueError("follow_up reasoning requires trigger")
            if self.sourcePackItemId is not None:
                raise ValueError("follow_up reasoning cannot carry pack source")
        return self


# --- TerminalPanelState (persisted in sessions.terminal_panel_state JSONB) ---


class TerminalPanelState(BaseModel):
    """Strict validation for sessions.terminal_panel_state JSONB column (CTRL-09).

    SchemaVersion: terminal_panel_state.v1
    Includes flags/generation/trigger for permissive API model compatibility.
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    schemaVersion: Literal["terminal_panel_state.v1"]
    policyVersion: Literal["v1"]
    action: Literal["end"]
    completionReason: Literal["all_competencies_covered", "question_cap", "ended_early"]
    endedBy: Literal["controller", "user"]
    rubricSnapshot: RubricSnapshot
    flags: list[Flag] = Field(max_length=8)
    policyState: PolicyState
    targetCompetencyId: UUID | None = None
    sourcePackItemId: UUID | None = None
    trigger: Trigger | None = None
    uncoveredCompetencyIds: list[UUID]
    rationale: str = Field(min_length=1)
    generation: Generation
    failureMode: str | None = None


# --- EvaluationNarrative (persisted in sessions.evaluation_narrative JSONB) ---
# Validated at write time in Phase 8 evaluation flow (CTRL-09).


class ScoreScale(BaseModel):
    """Score range metadata for evaluation."""

    model_config = ConfigDict(extra="forbid", strict=True)

    min: int
    max: int


class NarrativeItem(BaseModel):
    """Per-competency narrative entry (strength or concern)."""

    model_config = ConfigDict(extra="forbid", strict=True)

    competencyId: UUID
    text: str = Field(min_length=1)
    turnIds: list[UUID]


class EvaluationNarrative(BaseModel):
    """Strict validation for sessions.evaluation_narrative JSONB column (CTRL-09).

    Validated at write time in Phase 8 evaluation flow (CTRL-09).
    SchemaVersion: evaluation_narrative.v1
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    schemaVersion: Literal["evaluation_narrative.v1"]
    evaluationVersion: Literal["v1"]
    scoreScale: ScoreScale
    summary: str = Field(min_length=1)
    overallVerdict: Literal["strong", "mixed", "needs_improvement", "insufficient_signal"]
    strengths: list[NarrativeItem]
    concerns: list[NarrativeItem]
    unassessedCompetencyIds: list[UUID]
    earlyEndNote: str | None = None
    modelFailureNote: str | None = None
    generatedByModel: str | None = None


# --- CompetencyEvidence (persisted in session_competency_scores.evidence JSONB) ---
# Validated at write time in Phase 8 evaluation flow (CTRL-09).


class EvidenceCoverage(BaseModel):
    """Coverage tracking for a competency during the interview."""

    model_config = ConfigDict(extra="forbid", strict=True)

    probed: bool
    assessed: bool
    firstQuestionTurnId: UUID | None = None
    questionTurnIds: list[UUID]
    answerTurnIds: list[UUID]


class EvidenceQuote(BaseModel):
    """Candidate quote as evaluation evidence."""

    model_config = ConfigDict(extra="forbid", strict=True)

    turnId: UUID
    quote: str = Field(min_length=1)
    type: Literal["strength", "concern", "neutral"]
    note: str


class EvidenceSignal(BaseModel):
    """Flag-based signal captured during interview."""

    model_config = ConfigDict(extra="forbid", strict=True)

    turnId: UUID
    flag: FlagLiteral
    detail: str


class CompetencyEvidence(BaseModel):
    """Strict validation for session_competency_scores.evidence JSONB column (CTRL-09).

    Validated at write time in Phase 8 evaluation flow (CTRL-09).
    SchemaVersion: competency_evidence.v1
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    schemaVersion: Literal["competency_evidence.v1"]
    evaluationVersion: Literal["v1"]
    coverage: EvidenceCoverage
    supportingTurnIds: list[UUID]
    quotes: list[EvidenceQuote]
    signals: list[EvidenceSignal]
    scoreRationale: str | None = None
    unassessedReason: str | None = None
