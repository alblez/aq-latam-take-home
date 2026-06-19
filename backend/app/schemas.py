from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

# --- Enums as Literal types (matching contract.yaml string enums) ---

SessionStatus = Literal["in_progress", "completed", "ended_early"]
CompletionReason = Literal["all_competencies_covered", "question_cap", "ended_early"]
CompetencyCategory = Literal["behavioral", "technical"]
PolicyAction = Literal["new_topic", "follow_up", "end"]
FlagEnum = Literal[
    "vague_claim",
    "no_evidence",
    "interesting_thread",
    "contradiction",
    "well_covered",
    "tradeoff_mentioned",
    "metric_mentioned",
    "specific_tool_mentioned",
]


# --- Sub-models (building blocks) ---


class Job(BaseModel):
    id: UUID
    title: str
    description: str
    competencyCount: int = Field(default=0, ge=0)


class JobDetail(Job):
    pass


class Session(BaseModel):
    id: UUID
    jobId: UUID
    status: SessionStatus
    completionReason: CompletionReason | None = None
    startedAt: str | None = None
    completedAt: str | None = None


class CompetencyStatus(BaseModel):
    id: UUID
    name: str
    category: CompetencyCategory
    status: Literal["not-reached", "in-progress", "covered"]


class CompetencyRef(BaseModel):
    id: UUID
    name: str


class Flag(BaseModel):
    flag: FlagEnum
    detail: str
    competencyId: UUID | None = None
    triggerTurnId: UUID | None = None
    answerExcerpt: str | None = None


class RubricCompetencySnapshot(BaseModel):
    id: UUID
    status: Literal["covered", "in-progress", "not-reached"]
    category: CompetencyCategory | None = None
    evidenceTurnIds: list[UUID] | None = None
    followUpCount: int | None = None
    signalSummary: str | None = None


class RubricSnapshot(BaseModel):
    covered: list[UUID]
    inProgress: list[UUID]
    gaps: list[UUID]
    competencies: list[RubricCompetencySnapshot] | None = None


class PolicyState(BaseModel):
    questionCount: int = Field(ge=0)
    followUpCount: int = Field(ge=0)
    minQuestions: int
    minFollowUps: int
    maxQuestions: int
    maxFollowUpsPerCompetency: int
    followUpCountsByCompetency: dict[str, int] | None = None
    eligibleToEnd: bool


class Trigger(BaseModel):
    turnId: UUID
    answerExcerpt: str
    reason: str


class Generation(BaseModel):
    mode: Literal["pack_seed", "targeted_follow_up", "generic_probe", "terminal"]
    fallbackMode: str | None = None
    answerDependencyRequired: bool


class PanelState(BaseModel):
    rubricSnapshot: RubricSnapshot
    flags: list[Flag]
    policyState: PolicyState
    action: PolicyAction
    targetCompetencyId: UUID | None = None
    sourcePackItemId: UUID | None = None
    trigger: Trigger | None = None
    rationale: str
    generation: Generation
    failureMode: str | None = None


class TerminalPanelState(PanelState):
    completionReason: CompletionReason
    endedBy: Literal["controller", "user"]
    uncoveredCompetencyIds: list[UUID]


class Turn(BaseModel):
    id: UUID
    clientTurnId: UUID | None = None
    role: Literal["interviewer", "candidate"]
    turnIndex: int
    competencyId: UUID
    content: str
    inputMode: Literal["voice", "text"] | None = None
    audioDurationMs: int | None = None
    action: PolicyAction | None = None
    sourcePackItemId: UUID | None = None
    reasoning: PanelState | None = None


# --- Request models (extra="forbid") ---


class CreateSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    jobId: UUID


class SubmitAnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    clientTurnId: UUID
    answerText: str = Field(max_length=10_000)
    inputMode: Literal["voice", "text"]
    audioDurationMs: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _validate_answer_constraints(self) -> SubmitAnswerRequest:
        """Reject blank answers and text-mode audio mismatch per D-03."""
        if not self.answerText.strip():
            msg = "answerText must not be blank or whitespace-only"
            raise ValueError(msg)
        if self.inputMode == "text" and self.audioDurationMs is not None:
            msg = "audioDurationMs must be null when inputMode is text"
            raise ValueError(msg)
        return self


# --- Response models (NO extra="forbid") ---


class StartSessionResponse(BaseModel):
    question: str
    turnIndex: int
    panelState: PanelState
    competencies: list[CompetencyStatus]
    turns: list[Turn]
    jobTitle: str


class SubmitAnswerResponse(BaseModel):
    question: str | None
    turnIndex: int
    panelState: PanelState
    competencies: list[CompetencyStatus]
    turns: list[Turn]
    jobTitle: str
    isComplete: bool
    terminalPanelState: TerminalPanelState | None = None
    evaluationReady: bool


class SessionStateResponse(BaseModel):
    session: Session
    turns: list[Turn]
    panelState: PanelState
    competencies: list[CompetencyStatus]
    jobTitle: str
    currentQuestion: str | None
    turnIndex: int
    status: SessionStatus
    needsRecovery: bool
    terminalPanelState: TerminalPanelState | None = None


class EndSessionEarlyResponse(BaseModel):
    uncoveredCompetencies: list[CompetencyRef]
    terminalPanelState: TerminalPanelState
    evaluationReady: bool


# --- Evaluation models ---


class ScoreScale(BaseModel):
    min: int
    max: int


class EvidenceQuote(BaseModel):
    turnId: UUID
    quote: str
    type: Literal["strength", "concern", "neutral"]
    note: str


class EvidenceSignal(BaseModel):
    turnId: UUID
    flag: str
    detail: str


class EvidenceCoverage(BaseModel):
    probed: bool
    assessed: bool
    firstQuestionTurnId: UUID | None = None
    questionTurnIds: list[UUID]
    answerTurnIds: list[UUID]


class CompetencyEvidence(BaseModel):
    schemaVersion: str
    evaluationVersion: str
    coverage: EvidenceCoverage
    supportingTurnIds: list[UUID]
    quotes: list[EvidenceQuote]
    signals: list[EvidenceSignal]
    scoreRationale: str | None = None
    unassessedReason: str | None = None


class CompetencyScore(BaseModel):
    competencyId: UUID
    name: str
    category: CompetencyCategory
    assessed: bool
    score: int | None = None
    notes: str | None = None
    evidence: CompetencyEvidence | None = None


class NarrativeItem(BaseModel):
    competencyId: UUID
    text: str
    turnIds: list[UUID]


class EvaluationNarrative(BaseModel):
    summary: str
    overallVerdict: Literal["strong", "mixed", "needs_improvement", "insufficient_signal"]
    strengths: list[NarrativeItem]
    concerns: list[NarrativeItem]
    unassessedCompetencyIds: list[UUID]
    earlyEndNote: str | None = None
    modelFailureNote: str | None = None


class Evaluation(BaseModel):
    overallScore: float | None = None
    scoreScale: ScoreScale
    competencyScores: list[CompetencyScore]
    narrative: EvaluationNarrative


class SessionDetail(BaseModel):
    session: Session
    job: JobDetail
    competencies: list[CompetencyStatus]
    turns: list[Turn]
    evaluation: Evaluation | None = None
    terminalPanelState: TerminalPanelState | None = None


# --- History models ---


class SessionSummary(BaseModel):
    id: UUID
    jobId: UUID
    jobTitle: str
    status: SessionStatus
    startedAt: str
    completedAt: str | None = None
    durationMs: int | None = None
    overallScore: float | None = None
    coveragePercent: float | None = None
    talkRatio: float | None = None
    questionCount: int = Field(ge=0)
    followUpCount: int = Field(ge=0)


class HistoryResponse(BaseModel):
    sessions: list[SessionSummary]


# --- Job list response ---


class JobListResponse(BaseModel):
    jobs: list[Job]
