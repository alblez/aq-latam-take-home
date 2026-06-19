"""Deterministic interview controller policy (CTRL-04, CTRL-05).

Pure functions only — no I/O, no Settings, no HTTP client, no DEFAULT_CONTROLLER_CONFIG.
Config arrives as the session's persisted, validated ControllerConfig (D-16).
LLM influence is limited to validated enum signals through the flags list.

Per D-09..D-16: identical policy inputs always produce the identical decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from app.engine.rationales import (
    end_rationale,
    follow_up_rationale,
    new_topic_rationale,
    reprobe_rationale,
)
from app.jsonb_schemas import ControllerConfig, Flag

# --- D-13: fixed priority order for follow-up trigger selection ---

SIGNAL_PRIORITY: tuple[str, ...] = (
    "contradiction",
    "vague_claim",
    "no_evidence",
    "interesting_thread",
    "tradeoff_mentioned",
    "metric_mentioned",
    "specific_tool_mentioned",
    "well_covered",
)
"""Clarification signals before depth signals. Per D-13."""


# --- Frozen dataclasses ---


@dataclass(frozen=True)
class CompetencyFacts:
    """Per-competency state visible to policy. Per D-16: derived from persisted turns."""

    id: UUID
    name: str
    category: str
    sort_order: int
    questions_asked: int
    has_candidate_answer: bool


@dataclass(frozen=True)
class PolicyInputs:
    """Complete input to decide(). Per D-16: all counts from persisted state."""

    config: ControllerConfig
    competencies: list[CompetencyFacts]
    current_competency_id: UUID
    question_count: int
    follow_up_count: int
    follow_ups_by_competency: dict[UUID, int]
    flags: list[Flag]


@dataclass(frozen=True, eq=True)
class Decision:
    """Policy output. Per CTRL-04: deterministic, no LLM influence on flow choice."""

    action: Literal["new_topic", "follow_up", "end"]
    target_competency_id: UUID | None
    trigger_flag: Flag | None
    completion_reason: Literal["all_competencies_covered", "question_cap"] | None
    rationale: str
    is_reprobe: bool
    eligible_to_end: bool


# --- Small predicates (each <= ~6 branches for C901/xenon B) ---


def usable_signals(flags: list[Flag], current_competency_id: UUID) -> list[Flag]:
    """D-10/D-11: only flags with competencyId None or matching current are usable."""
    return [f for f in flags if f.competencyId is None or f.competencyId == current_competency_id]


def pick_trigger(usable: list[Flag]) -> Flag | None:
    """D-13: first flag by SIGNAL_PRIORITY order; stable tie-break by list position."""
    if not usable:
        return None
    priority_map = {s: i for i, s in enumerate(SIGNAL_PRIORITY)}
    return min(usable, key=lambda f: priority_map.get(f.flag, len(SIGNAL_PRIORITY)))


def follow_up_allowed(
    config: ControllerConfig,
    question_count: int,
    uncovered_count: int,
    comp_follow_ups: int,
) -> bool:
    """D-15: guard formula — spending one more question on depth must not endanger coverage."""
    if question_count >= config.maxQuestions:
        return False
    if comp_follow_ups >= config.maxFollowUpsPerCompetency:
        return False
    # (maxQuestions - questionCount - 1) >= uncoveredCompetencyCount
    remaining_after = config.maxQuestions - question_count - 1
    return remaining_after >= uncovered_count


def covered_if_end(competencies: list[CompetencyFacts]) -> bool:
    """D-09: every competency has >= 1 question asked and a candidate answer."""
    return all(c.questions_asked >= 1 and c.has_candidate_answer for c in competencies)


def pick_reprobe_competency(
    competencies: list[CompetencyFacts],
    current_competency_id: UUID,
) -> CompetencyFacts:
    """D-14: among answered competencies, fewest questions_asked, tie lowest sort_order."""
    candidates = [
        c for c in competencies if c.has_candidate_answer and c.id != current_competency_id
    ]
    if not candidates:
        # Fallback: reprobe current if it's the only one
        candidates = [c for c in competencies if c.has_candidate_answer]
    return min(candidates, key=lambda c: (c.questions_asked, c.sort_order))


def _current_comp_status(
    c: CompetencyFacts,
    decision_action: str,
    decision_target: UUID | None,
) -> str:
    """Status for the current competency based on decision."""
    if decision_action == "follow_up" and decision_target == c.id:
        return "in-progress"
    return "covered" if c.has_candidate_answer else "in-progress"


def _competency_status(
    c: CompetencyFacts,
    current_competency_id: UUID,
    decision_action: str,
    decision_target: UUID | None,
) -> str:
    """Compute single competency's coverage status after decision."""
    if c.questions_asked == 0 and not c.has_candidate_answer:
        return "not-reached"
    if c.id == current_competency_id:
        return _current_comp_status(c, decision_action, decision_target)
    if c.id == decision_target:
        return "in-progress"
    return "covered" if (c.has_candidate_answer and c.questions_asked >= 1) else "in-progress"


def compute_coverage(
    competencies: list[CompetencyFacts],
    current_competency_id: UUID,
    decision_action: str,
    decision_target: UUID | None,
) -> dict[UUID, str]:
    """D-09: per-competency coverage status after applying the decision.

    - follow_up on current: current stays in-progress
    - new_topic targeting another: current becomes covered (if answered)
    - end: current becomes covered (if answered)
    - unasked competencies: not-reached
    - decision target becomes in-progress (new question about to be asked)
    """
    return {
        c.id: _competency_status(c, current_competency_id, decision_action, decision_target)
        for c in competencies
    }


# --- Main decision function ---


def is_eligible_to_end(
    config: ControllerConfig,
    question_count: int,
    follow_up_count: int,
    all_covered: bool,
) -> bool:
    """D-09: session may end only when minimum depth thresholds are met.

    At question cap, eligibility is always True (never-stall).
    Otherwise requires minQuestions AND minFollowUps AND all_covered.
    """
    return (
        question_count >= config.minQuestions
        and follow_up_count >= config.minFollowUps
        and (all_covered or question_count >= config.maxQuestions)
    )


def gap_competencies(competencies: list[CompetencyFacts]) -> list[CompetencyFacts]:
    """Competencies with zero questions asked — the unvisited gaps."""
    return [c for c in competencies if c.questions_asked == 0]


def decide(inputs: PolicyInputs) -> Decision:
    """Deterministic policy decision. Per §2 decision order.

    Never stalls: at question cap the decision is always end.
    """
    cfg = inputs.config
    q = inputs.question_count
    f = inputs.follow_up_count

    all_covered = covered_if_end(inputs.competencies)

    # Step 1: compute eligibility (exposed on every Decision)
    eligible = is_eligible_to_end(cfg, q, f, all_covered)

    # Step 2: hard cap → end (never-stall)
    if q >= cfg.maxQuestions:
        reason = _cap_reason(all_covered, eligible)
        return Decision(
            action="end",
            target_competency_id=None,
            trigger_flag=None,
            completion_reason=reason,
            rationale=end_rationale(reason, q, f),
            is_reprobe=False,
            eligible_to_end=True,
        )

    # Step 3: all covered + eligible → end
    if all_covered and eligible:
        return Decision(
            action="end",
            target_competency_id=None,
            trigger_flag=None,
            completion_reason="all_competencies_covered",
            rationale=end_rationale("all_competencies_covered", q, f),
            is_reprobe=False,
            eligible_to_end=True,
        )

    # Step 4: all covered but NOT eligible (minimums unmet) — D-14
    if all_covered:
        return _decide_covered_not_eligible(inputs, eligible)

    # Step 5: gaps exist
    return _decide_gaps_exist(inputs, eligible)


def _cap_reason(
    all_covered: bool, eligible: bool
) -> Literal["all_competencies_covered", "question_cap"]:
    """At cap: all_competencies_covered only if actually covered AND eligible."""
    if all_covered and eligible:
        return "all_competencies_covered"
    return "question_cap"


def _build_follow_up_decision(
    inputs: PolicyInputs,
    trigger: Flag,
    comp_follow_ups: int,
    eligible: bool,
) -> Decision:
    """Construct a follow_up Decision targeting the current competency."""
    cfg = inputs.config
    current_id = inputs.current_competency_id
    current = _find_competency(inputs.competencies, current_id)
    return Decision(
        action="follow_up",
        target_competency_id=current_id,
        trigger_flag=trigger,
        completion_reason=None,
        rationale=follow_up_rationale(
            trigger.flag,
            current.name,
            comp_follow_ups + 1,
            cfg.maxFollowUpsPerCompetency,
            inputs.question_count + 1,
            cfg.maxQuestions,
        ),
        is_reprobe=False,
        eligible_to_end=eligible,
    )


def _decide_covered_not_eligible(inputs: PolicyInputs, eligible: bool) -> Decision:
    """D-14: all covered but minimums unmet — follow_up or reprobe."""
    cfg = inputs.config
    current_id = inputs.current_competency_id
    comp_fu = inputs.follow_ups_by_competency.get(current_id, 0)

    usable = usable_signals(inputs.flags, current_id)
    trigger = pick_trigger(usable)

    # Try follow_up on current if budget allows
    if trigger and comp_fu < cfg.maxFollowUpsPerCompetency:
        return _build_follow_up_decision(inputs, trigger, comp_fu, eligible)

    # No usable signal or budget exhausted → reprobe (D-14)
    reprobe_target = pick_reprobe_competency(inputs.competencies, current_id)
    return Decision(
        action="new_topic",
        target_competency_id=reprobe_target.id,
        trigger_flag=None,
        completion_reason=None,
        rationale=reprobe_rationale(
            reprobe_target.name,
            inputs.question_count + 1,
            cfg.maxQuestions,
        ),
        is_reprobe=True,
        eligible_to_end=eligible,
    )


def _decide_gaps_exist(inputs: PolicyInputs, eligible: bool) -> Decision:
    """§2: gaps exist — coverage priority after minFollowUps, else signal-first."""
    cfg = inputs.config
    current_id = inputs.current_competency_id
    f = inputs.follow_up_count
    comp_fu = inputs.follow_ups_by_competency.get(current_id, 0)

    gaps = gap_competencies(inputs.competencies)
    uncovered_count = len(gaps)

    # §2: after minFollowUps met, coverage gets priority
    if f >= cfg.minFollowUps:
        return _new_topic_decision(inputs, eligible, gaps, uncovered_count)

    # Before minFollowUps: try follow_up if usable signal + guard passes
    usable = usable_signals(inputs.flags, current_id)
    trigger = pick_trigger(usable)

    if trigger and follow_up_allowed(cfg, inputs.question_count, uncovered_count, comp_fu):
        return _build_follow_up_decision(inputs, trigger, comp_fu, eligible)

    # No signal or guard blocked → new_topic
    return _new_topic_decision(inputs, eligible, gaps, uncovered_count)


def _new_topic_decision(
    inputs: PolicyInputs,
    eligible: bool,
    gaps: list[CompetencyFacts],
    uncovered_count: int,
) -> Decision:
    """Pick gap competency with lowest sort_order (D-12)."""
    target = min(gaps, key=lambda c: c.sort_order)
    return Decision(
        action="new_topic",
        target_competency_id=target.id,
        trigger_flag=None,
        completion_reason=None,
        rationale=new_topic_rationale(
            target.name,
            uncovered_count,
            inputs.question_count + 1,
            inputs.config.maxQuestions,
        ),
        is_reprobe=False,
        eligible_to_end=eligible,
    )


def _find_competency(competencies: list[CompetencyFacts], uid: UUID) -> CompetencyFacts:
    """Lookup helper — raises if not found (programming error)."""
    for c in competencies:
        if c.id == uid:
            return c
    msg = f"Competency {uid} not in inputs"
    raise ValueError(msg)
