"""Deterministic depth policy: decision branches and pure predicates."""

from __future__ import annotations

from uuid import UUID, uuid4

from app.engine.policy import (
    CompetencyFacts,
    PolicyInputs,
    compute_coverage,
    covered_if_end,
    decide,
    follow_up_allowed,
    gap_competencies,
    is_eligible_to_end,
    pick_reprobe_competency,
    pick_trigger,
    usable_signals,
)
from app.jsonb_schemas import DEFAULT_CONTROLLER_CONFIG, Flag

CFG = DEFAULT_CONTROLLER_CONFIG


def _comp(
    *,
    name: str = "Competency",
    sort_order: int = 0,
    questions_asked: int = 0,
    answered: bool = False,
    cid: UUID | None = None,
) -> CompetencyFacts:
    return CompetencyFacts(
        id=cid or uuid4(),
        name=name,
        category="behavioral",
        sort_order=sort_order,
        questions_asked=questions_asked,
        has_candidate_answer=answered,
    )


def _inputs(
    *,
    competencies: list[CompetencyFacts],
    current_competency_id: UUID,
    question_count: int,
    follow_up_count: int,
    flags: list[Flag] | None = None,
    follow_ups_by_competency: dict[UUID, int] | None = None,
) -> PolicyInputs:
    return PolicyInputs(
        config=CFG,
        competencies=competencies,
        current_competency_id=current_competency_id,
        question_count=question_count,
        follow_up_count=follow_up_count,
        follow_ups_by_competency=follow_ups_by_competency or {},
        flags=flags or [],
    )


# --- decide() branches ---


def test_decide_new_topic_when_gaps_exist() -> None:
    comp = _comp(name="System Design", sort_order=0)
    decision = decide(
        _inputs(
            competencies=[comp],
            current_competency_id=comp.id,
            question_count=0,
            follow_up_count=0,
        )
    )
    assert decision.action == "new_topic"
    assert decision.target_competency_id == comp.id
    assert decision.is_reprobe is False
    assert decision.eligible_to_end is False


def test_decide_ends_at_question_cap() -> None:
    answered = _comp(questions_asked=1, answered=True, sort_order=0)
    gap = _comp(questions_asked=0, sort_order=1)
    decision = decide(
        _inputs(
            competencies=[answered, gap],
            current_competency_id=answered.id,
            question_count=CFG.maxQuestions,
            follow_up_count=2,
        )
    )
    assert decision.action == "end"
    assert decision.completion_reason == "question_cap"
    assert decision.eligible_to_end is True


def test_decide_ends_when_all_covered_and_eligible() -> None:
    c1 = _comp(questions_asked=1, answered=True, sort_order=0)
    c2 = _comp(questions_asked=1, answered=True, sort_order=1)
    decision = decide(
        _inputs(
            competencies=[c1, c2],
            current_competency_id=c1.id,
            question_count=6,
            follow_up_count=2,
        )
    )
    assert decision.action == "end"
    assert decision.completion_reason == "all_competencies_covered"
    assert decision.eligible_to_end is True


def test_decide_follow_up_on_signal_before_min_follow_ups() -> None:
    current = _comp(questions_asked=1, answered=True, sort_order=0)
    gap = _comp(questions_asked=0, sort_order=1)
    flag = Flag(flag="contradiction", detail="said X then not-X")
    decision = decide(
        _inputs(
            competencies=[current, gap],
            current_competency_id=current.id,
            question_count=2,
            follow_up_count=0,
            flags=[flag],
        )
    )
    assert decision.action == "follow_up"
    assert decision.target_competency_id == current.id
    assert decision.trigger_flag is not None
    assert decision.trigger_flag.flag == "contradiction"


def test_decide_reprobes_when_covered_but_minimums_unmet() -> None:
    c1 = _comp(questions_asked=1, answered=True, sort_order=0)
    c2 = _comp(questions_asked=1, answered=True, sort_order=1)
    decision = decide(
        _inputs(
            competencies=[c1, c2],
            current_competency_id=c1.id,
            question_count=3,
            follow_up_count=0,
        )
    )
    assert decision.action == "new_topic"
    assert decision.is_reprobe is True
    assert decision.target_competency_id == c2.id


# --- pure predicates ---


def test_is_eligible_to_end() -> None:
    assert is_eligible_to_end(CFG, 6, 2, True) is True
    assert is_eligible_to_end(CFG, 5, 2, True) is False
    assert is_eligible_to_end(CFG, 6, 1, True) is False
    assert is_eligible_to_end(CFG, 6, 2, False) is False


def test_usable_signals_filters_by_competency() -> None:
    current = uuid4()
    other = uuid4()
    shared = Flag(flag="vague_claim", detail="d", competencyId=None)
    mine = Flag(flag="no_evidence", detail="d", competencyId=current)
    theirs = Flag(flag="metric_mentioned", detail="d", competencyId=other)
    usable = usable_signals([shared, mine, theirs], current)
    assert shared in usable
    assert mine in usable
    assert theirs not in usable


def test_pick_trigger_respects_priority() -> None:
    assert pick_trigger([]) is None
    low = Flag(flag="metric_mentioned", detail="d")
    high = Flag(flag="contradiction", detail="d")
    assert pick_trigger([low, high]) is high


def test_follow_up_allowed_guard() -> None:
    assert follow_up_allowed(CFG, CFG.maxQuestions, 0, 0) is False
    assert follow_up_allowed(CFG, 2, 0, CFG.maxFollowUpsPerCompetency) is False
    assert follow_up_allowed(CFG, 2, 1, 0) is True


def test_covered_if_end_and_gaps() -> None:
    answered = _comp(questions_asked=1, answered=True)
    gap = _comp(questions_asked=0)
    assert covered_if_end([answered]) is True
    assert covered_if_end([answered, gap]) is False
    assert gap_competencies([answered, gap]) == [gap]


def test_pick_reprobe_prefers_fewest_questions() -> None:
    current = _comp(questions_asked=2, answered=True, sort_order=0)
    light = _comp(questions_asked=1, answered=True, sort_order=1)
    heavy = _comp(questions_asked=3, answered=True, sort_order=2)
    chosen = pick_reprobe_competency([current, light, heavy], current.id)
    assert chosen is light


def test_compute_coverage_marks_statuses() -> None:
    answered = _comp(questions_asked=1, answered=True, sort_order=0)
    gap = _comp(questions_asked=0, sort_order=1)
    coverage = compute_coverage([answered, gap], answered.id, "end", None)
    assert coverage[answered.id] == "covered"
    assert coverage[gap.id] == "not-reached"
