"""Intermediate LLM evaluation schema — judgment-only output (D-14).

Deterministic score mapping, evidence wiring, and narrative construction.
This module owns:
- Strict Pydantic models for structured model output
- Code-fence stripping parser (mirrors analyze.py)
- Competency alignment gate (pre-persistence enforcement)
- Deterministic mapping: model judgment + turn snapshots → narrative, evidence, score rows

No HTTP client, no app.errors — pure validation module.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from app.engine.rationales import (
    EARLY_END_NOTE,
    INSUFFICIENT_SIGNAL_REASON,
    MODEL_FAILURE_NOTE,
    UNPROBED_REASON,
)
from app.jsonb_schemas import CompetencyEvidence, EvaluationNarrative, Flag, TurnReasoning

if TYPE_CHECKING:
    from app.engine.prompts import CompetencyBrief
    from app.repositories import CompetencyScoreRowData


def _uuid_serializer(obj: object) -> str:
    """Strict JSON default: only UUID → str. All else raises TypeError."""
    if isinstance(obj, UUID):
        return str(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


# --- Intermediate LLM-output schemas ---


class ModelCompetencyScore(BaseModel):
    """Per-competency score from the model (Pitfall 1: all fields required)."""

    model_config = ConfigDict(extra="forbid", strict=True)

    competencyId: UUID
    assessed: bool
    score: int | None = Field(ge=1, le=10)
    scoreRationale: str = Field(min_length=1, max_length=600)

    @model_validator(mode="after")
    def score_matches_assessed(self) -> ModelCompetencyScore:
        """assessed=True requires score; assessed=False requires score=None."""
        if self.assessed and self.score is None:
            raise ValueError("assessed=True requires a non-null score (1-10)")
        if not self.assessed and self.score is not None:
            raise ValueError("assessed=False requires score=None")
        return self


class ModelNarrativeItem(BaseModel):
    """Single strength or concern item from the model."""

    model_config = ConfigDict(extra="forbid", strict=True)

    competencyId: UUID
    text: str = Field(min_length=1, max_length=700)


class ModelEvaluationResponse(BaseModel):
    """Full evaluation response from the model (D-14 judgment-only shape).

    Code owns schemaVersion/evaluationVersion — model never emits them.
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    summary: str = Field(min_length=1, max_length=1200)
    overallVerdict: Literal["strong", "mixed", "needs_improvement", "insufficient_signal"]
    competencyScores: list[ModelCompetencyScore] = Field(min_length=1)
    strengths: list[ModelNarrativeItem] = Field(max_length=8)
    concerns: list[ModelNarrativeItem] = Field(max_length=8)


# --- Parser ---


def _strip_code_fences(raw: str) -> str:
    """Remove optional ```json ... ``` fences wrapping the output.

    Models often emit fences even when told not to — strip defensively.
    """
    stripped = raw.strip()
    pattern = r"^```(?:json)?\s*\n?(.*?)\n?\s*```$"
    match = re.match(pattern, stripped, re.DOTALL)
    if match:
        return match.group(1).strip()
    return stripped


def parse_evaluation_response(raw: str) -> ModelEvaluationResponse:
    """Parse raw LLM output into validated ModelEvaluationResponse.

    Uses model_validate_json to accept string UUIDs under strict mode
    (Pitfall 2: Python-mode strict rejects string UUIDs).
    """
    cleaned = _strip_code_fences(raw)
    return ModelEvaluationResponse.model_validate_json(cleaned)


# --- Competency alignment gate ---


class EvaluationAlignmentError(Exception):
    """Model output references unknown/duplicate/missing competencies or scores unprobed ones."""


def validate_competency_alignment(
    parsed: ModelEvaluationResponse,
    *,
    expected_ids: set[UUID],
    unprobed_ids: set[UUID],
) -> None:
    """Validate model output competency IDs align with job competencies.

    Raises EvaluationAlignmentError on:
    - Unknown competencyId (not in expected_ids)
    - Duplicate competencyId
    - Missing job competency (expected but not in response)
    - assessed=True for an unprobed competency
    """
    seen: set[UUID] = set()

    for entry in parsed.competencyScores:
        cid = entry.competencyId

        # Unknown check
        if cid not in expected_ids:
            raise EvaluationAlignmentError(f"unknown competencyId {cid} — not in job competencies")

        # Duplicate check
        if cid in seen:
            raise EvaluationAlignmentError(
                f"duplicate competencyId {cid} — each competency must appear exactly once"
            )
        seen.add(cid)

        # Unprobed assessed check
        if entry.assessed and cid in unprobed_ids:
            raise EvaluationAlignmentError(
                f"unprobed competencyId {cid} marked assessed=True — "
                "model cannot score a competency that was never probed"
            )

    # Missing check: all expected must appear
    missing = expected_ids - seen
    if missing:
        raise EvaluationAlignmentError(
            f"missing competencyIds {missing} — model must include all job competencies"
        )

    # Narrative item competencyId validation: strengths and concerns
    for label, items in (("strengths", parsed.strengths), ("concerns", parsed.concerns)):
        for item in items:
            if item.competencyId not in expected_ids:
                raise EvaluationAlignmentError(
                    f"unknown competencyId {item.competencyId} in {label} — not in job competencies"
                )


# =============================================================================
# Deterministic mapping — model judgment + turn snapshots → persistence artifacts
# =============================================================================

# --- Quote note constants (D-22: exact deterministic strings) ---

QUOTE_NOTE_FLAG_MATCH: str = "Candidate response directly triggered an interview signal."
QUOTE_NOTE_NARRATIVE_SUPPORT: str = "Candidate response supports the competency narrative."
QUOTE_NOTE_FALLBACK: str = "First candidate response for this competency."

# --- Max quote parameters ---

_MAX_QUOTES: int = 2
_MAX_QUOTE_LEN: int = 240


# --- EvaluationTurn frozen dataclass ---


@dataclass(frozen=True, slots=True)
class EvaluationTurn:
    """Lightweight turn snapshot for deterministic mapping (no DB dependency)."""

    turn_id: UUID
    turn_index: int
    role: str
    competency_id: UUID | None
    content: str
    flags: tuple[Flag, ...]


# --- Public mapping functions ---


def build_evaluation_turns(turns: Sequence[Any]) -> list[EvaluationTurn]:
    """Convert turn rows into EvaluationTurn list for mapping.

    Accepts any duck-typed objects with: id, turn_index, role, competency_id, content, reasoning.
    Parses persisted reasoning JSONB with model_validate_json(json.dumps(...)) — NOT
    model_validate() — because strict Python-mode validation rejects string UUIDs from JSONB
    (review HIGH, decision 06-02).
    """
    result: list[EvaluationTurn] = []
    for turn in turns:
        flags: tuple[Flag, ...] = ()
        reasoning = getattr(turn, "reasoning", None)
        if reasoning is not None and isinstance(reasoning, dict):
            try:
                parsed_reasoning = TurnReasoning.model_validate_json(json.dumps(reasoning))
                flags = tuple(parsed_reasoning.flags)
            except (ValidationError, TypeError):
                # Pitfall 8: sparse/malformed reasoning → empty flags
                flags = ()
        result.append(
            EvaluationTurn(
                turn_id=turn.id,
                turn_index=turn.turn_index,
                role=turn.role,
                competency_id=turn.competency_id,
                content=turn.content,
                flags=flags,
            )
        )
    return result


# --- Private helpers ---


def _normalize_quote(text: str) -> str:
    """Collapse whitespace runs to single space, trim to 240 chars + ellipsis (D-20)."""
    normalized = re.sub(r"\s+", " ", text).strip()
    if len(normalized) > _MAX_QUOTE_LEN:
        return normalized[:_MAX_QUOTE_LEN] + "\u2026"
    return normalized


def _coverage_for(
    competency_id: UUID,
    eval_turns: list[EvaluationTurn],
    model_assessed: bool,
) -> dict:
    """Build EvidenceCoverage dict for a competency (D-17)."""
    question_turn_ids: list[UUID] = []
    answer_turn_ids: list[UUID] = []

    for i, et in enumerate(eval_turns):
        if et.role == "interviewer" and et.competency_id == competency_id:
            question_turn_ids.append(et.turn_id)
        elif et.role == "candidate" and i > 0:
            prev = eval_turns[i - 1]
            if prev.role == "interviewer" and prev.competency_id == competency_id:
                answer_turn_ids.append(et.turn_id)

    probed = len(question_turn_ids) > 0
    return {
        "probed": probed,
        "assessed": model_assessed,
        "firstQuestionTurnId": question_turn_ids[0] if question_turn_ids else None,
        "questionTurnIds": question_turn_ids,
        "answerTurnIds": answer_turn_ids,
    }


def _signals_for(
    competency_id: UUID,
    eval_turns: list[EvaluationTurn],
) -> list[dict]:
    """Build EvidenceSignal list for a competency (D-16, Pitfall 8).

    Only flags with competencyId==C AND triggerTurnId present produce signals.
    Flags with competencyId=None are excluded from every competency.
    """
    signals: list[dict] = []
    for et in eval_turns:
        for flag in et.flags:
            if flag.competencyId == competency_id and flag.triggerTurnId is not None:
                signals.append(
                    {
                        "turnId": flag.triggerTurnId,
                        "flag": flag.flag,
                        "detail": flag.detail,
                    }
                )
    return signals


def _quote_type_for(competency_id: UUID, strength_ids: set[UUID], concern_ids: set[UUID]) -> str:
    """Determine quote type: strength wins over concern (D-21)."""
    if competency_id in strength_ids:
        return "strength"
    if competency_id in concern_ids:
        return "concern"
    return "neutral"


def _flag_referenced_turn_ids(
    competency_id: UUID,
    eval_turns: list[EvaluationTurn],
    candidate_content: dict[UUID, str],
) -> tuple[list[UUID], set[UUID]]:
    """Collect deduplicated candidate turn IDs referenced by flags for competency."""
    flag_turn_ids: list[UUID] = []
    seen: set[UUID] = set()
    for et in eval_turns:
        for flag in et.flags:
            if (
                flag.competencyId == competency_id
                and flag.triggerTurnId is not None
                and flag.triggerTurnId not in seen
                and flag.triggerTurnId in candidate_content
            ):
                flag_turn_ids.append(flag.triggerTurnId)
                seen.add(flag.triggerTurnId)
    return flag_turn_ids, seen


def _first_answer_turn_for(competency_id: UUID, eval_turns: list[EvaluationTurn]) -> UUID | None:
    """Find first candidate answer turn following an interviewer turn for C."""
    for i, et in enumerate(eval_turns):
        if et.role == "candidate" and i > 0:
            prev = eval_turns[i - 1]
            if prev.role == "interviewer" and prev.competency_id == competency_id:
                return et.turn_id
    return None


def _make_quote(turn_id: UUID, text: str, quote_type: str, note: str) -> dict:
    """Build a single EvidenceQuote dict."""
    return {
        "turnId": turn_id,
        "quote": _normalize_quote(text),
        "type": quote_type,
        "note": note,
    }


def _fallback_note(competency_id: UUID, strength_ids: set[UUID], concern_ids: set[UUID]) -> str:
    """Determine note for a fallback quote (D-21)."""
    if competency_id in strength_ids or competency_id in concern_ids:
        return QUOTE_NOTE_NARRATIVE_SUPPORT
    return QUOTE_NOTE_FALLBACK


def _quotes_for(
    competency_id: UUID,
    eval_turns: list[EvaluationTurn],
    model_assessed: bool,
    strength_ids: set[UUID],
    concern_ids: set[UUID],
) -> list[dict]:
    """Build EvidenceQuote list for a competency (D-18..D-22).

    Selection: flag-first (candidate turns referenced by triggerTurnId of C's flags),
    then fallback to first candidate answer turn for C. Max 2 quotes.
    Unassessed competencies get quotes=[].
    """
    if not model_assessed:
        return []

    quote_type = _quote_type_for(competency_id, strength_ids, concern_ids)

    # Gather candidate turn content by turn_id
    candidate_content: dict[UUID, str] = {
        et.turn_id: et.content for et in eval_turns if et.role == "candidate"
    }

    flag_turn_ids, seen_flag_turns = _flag_referenced_turn_ids(
        competency_id, eval_turns, candidate_content
    )
    fallback_tid = _first_answer_turn_for(competency_id, eval_turns)

    # Build quotes: flag-first, then fallback, max 2
    quotes: list[dict] = []
    for tid in flag_turn_ids[:_MAX_QUOTES]:
        text = candidate_content.get(tid, "")
        if text:
            quotes.append(_make_quote(tid, text, quote_type, QUOTE_NOTE_FLAG_MATCH))

    # Fill with fallback if not at max
    if len(quotes) < _MAX_QUOTES and fallback_tid and fallback_tid not in seen_flag_turns:
        text = candidate_content.get(fallback_tid, "")
        if text:
            note = _fallback_note(competency_id, strength_ids, concern_ids)
            quotes.append(_make_quote(fallback_tid, text, quote_type, note))

    return quotes


# --- Public: build_competency_evidence ---


def build_competency_evidence(
    *,
    competency_id: UUID,
    model_entry: ModelCompetencyScore | None,
    eval_turns: list[EvaluationTurn],
    strength_ids: set[UUID],
    concern_ids: set[UUID],
) -> CompetencyEvidence:
    """Build validated CompetencyEvidence for a single competency.

    Strict validation ensures what leaves this module matches CTRL-09 schema.
    """
    model_assessed = model_entry.assessed if model_entry else False

    coverage = _coverage_for(competency_id, eval_turns, model_assessed)
    signals = _signals_for(competency_id, eval_turns)
    quotes = _quotes_for(competency_id, eval_turns, model_assessed, strength_ids, concern_ids)

    # Supporting turn IDs = union of question + answer turn ids
    supporting = coverage["questionTurnIds"] + coverage["answerTurnIds"]

    # Determine unassessedReason
    unassessed_reason: str | None = None
    if not model_assessed:
        if not coverage["probed"]:
            unassessed_reason = UNPROBED_REASON
        else:
            unassessed_reason = INSUFFICIENT_SIGNAL_REASON

    # Determine scoreRationale
    score_rationale: str | None = None
    if model_entry and model_assessed:
        score_rationale = model_entry.scoreRationale

    evidence_dict = {
        "schemaVersion": "competency_evidence.v1",
        "evaluationVersion": "v1",
        "coverage": coverage,
        "supportingTurnIds": supporting,
        "quotes": quotes,
        "signals": signals,
        "scoreRationale": score_rationale,
        "unassessedReason": unassessed_reason,
    }

    # Validate strictly before returning
    return CompetencyEvidence.model_validate_json(
        json.dumps(evidence_dict, default=_uuid_serializer)
    )


# --- Public: build_evaluation_narrative ---


def _build_comp_answer_index(
    competencies: list[CompetencyBrief],
    eval_turns: list[EvaluationTurn],
) -> dict[UUID, list[UUID]]:
    """Map competency_id → list of answer turn IDs for narrative turn references."""
    result: dict[UUID, list[UUID]] = {}
    for comp in competencies:
        cov = _coverage_for(comp.id, eval_turns, False)
        result[comp.id] = cov["answerTurnIds"]
    return result


def _build_narrative_items(
    items: list[ModelNarrativeItem],
    answer_index: dict[UUID, list[UUID]],
) -> list[dict]:
    """Convert model narrative items to serializable dicts with turn references."""
    return [
        {
            "competencyId": item.competencyId,
            "text": item.text,
            "turnIds": answer_index.get(item.competencyId, []),
        }
        for item in items
    ]


def build_evaluation_narrative(
    *,
    parsed: ModelEvaluationResponse,
    eval_turns: list[EvaluationTurn],
    competencies: list[CompetencyBrief],
    terminal_reason: str,
    model_name: str,
    terminal_failure_mode: str | None,
) -> dict:
    """Build validated EvaluationNarrative dict from model judgment + turn data (D-15).

    Returns a JSON-serializable dict (model_dump(mode="json")) after strict validation.
    """
    # Determine if ANY competency is assessed
    any_assessed = any(entry.assessed for entry in parsed.competencyScores)

    # D-28: force verdict when zero assessed
    verdict = parsed.overallVerdict if any_assessed else "insufficient_signal"

    # Build narrative items with answer turn references
    answer_index = _build_comp_answer_index(competencies, eval_turns)
    strengths = _build_narrative_items(parsed.strengths, answer_index)
    concerns = _build_narrative_items(parsed.concerns, answer_index)

    # Unassessed competency IDs
    assessed_ids = {entry.competencyId for entry in parsed.competencyScores if entry.assessed}
    unassessed_ids = [comp.id for comp in competencies if comp.id not in assessed_ids]

    narrative_dict = {
        "schemaVersion": "evaluation_narrative.v1",
        "evaluationVersion": "v1",
        "scoreScale": {"min": 1, "max": 10},
        "summary": parsed.summary,
        "overallVerdict": verdict,
        "strengths": strengths,
        "concerns": concerns,
        "unassessedCompetencyIds": unassessed_ids,
        "earlyEndNote": EARLY_END_NOTE if terminal_reason == "ended_early" else None,
        "modelFailureNote": MODEL_FAILURE_NOTE if terminal_failure_mode else None,
        "generatedByModel": model_name,
    }

    # Validate strictly (CTRL-09)
    validated = EvaluationNarrative.model_validate_json(
        json.dumps(narrative_dict, default=_uuid_serializer)
    )
    return validated.model_dump(mode="json")


# --- Public: build_score_rows ---


def build_score_rows(
    *,
    session_id: UUID,
    parsed: ModelEvaluationResponse,
    eval_turns: list[EvaluationTurn],
    competencies: list[CompetencyBrief],
) -> list[CompetencyScoreRowData]:
    """Build one CompetencyScoreRowData per job competency (D-23).

    Imports CompetencyScoreRowData from app.repositories (plan-01 dataclass).
    """
    from app.repositories import CompetencyScoreRowData as RowData

    # Index model entries by competencyId
    model_entries: dict[UUID, ModelCompetencyScore] = {
        entry.competencyId: entry for entry in parsed.competencyScores
    }

    # Strength/concern ID sets for quote typing
    strength_ids = {item.competencyId for item in parsed.strengths}
    concern_ids = {item.competencyId for item in parsed.concerns}

    rows: list[RowData] = []
    for comp in competencies:
        model_entry = model_entries.get(comp.id)
        evidence = build_competency_evidence(
            competency_id=comp.id,
            model_entry=model_entry,
            eval_turns=eval_turns,
            strength_ids=strength_ids,
            concern_ids=concern_ids,
        )
        evidence_dict = evidence.model_dump(mode="json")

        if model_entry and model_entry.assessed:
            rows.append(
                RowData(
                    session_id=session_id,
                    competency_id=comp.id,
                    assessed=True,
                    score=model_entry.score,
                    notes=model_entry.scoreRationale,
                    evidence_dict=evidence_dict,
                )
            )
        else:
            rows.append(
                RowData(
                    session_id=session_id,
                    competency_id=comp.id,
                    assessed=False,
                    score=None,
                    notes=None,
                    evidence_dict=evidence_dict,
                )
            )

    return rows


# --- Public: derive_overall_score ---


def derive_overall_score(rows: Sequence[Any]) -> float | None:
    """Derive overall score from assessed rows (D-27, D-28).

    Accepts any objects with `assessed` and `score` attributes.
    Returns arithmetic mean rounded to 1 decimal, or None when zero assessed.
    """
    scores: list[int] = []
    for row in rows:
        if getattr(row, "assessed", False) and getattr(row, "score", None) is not None:
            scores.append(row.score)
    if not scores:
        return None
    return round(sum(scores) / len(scores), 1)
