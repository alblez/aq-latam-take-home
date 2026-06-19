"""Live pipeline smoke test (D-08, D-46, D-47, D-48).

DB-free, in-memory fixtures only. Exercises gateway → analyze → policy → generate
with real OpenRouter calls. Never runs under pytest or CI; requires OPENROUTER_API_KEY.

Usage: just backend-pipeline-smoke
"""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import UUID

# Ensure backend/ is on sys.path when script is invoked directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.engine.gateway import GatewayError, OpenRouterGateway
from app.engine.generate import run_generate
from app.engine.policy import (
    CompetencyFacts,
    Decision,
    PolicyInputs,
    decide,
)
from app.engine.prompts import CompetencyBrief, TranscriptTurn
from app.jsonb_schemas import ControllerConfig

# --- In-memory fixtures ---

COMPETENCIES = [
    CompetencyBrief(
        id=UUID("11111111-1111-1111-1111-111111111111"),
        name="System Design",
        category="technical",
    ),
    CompetencyBrief(
        id=UUID("22222222-2222-2222-2222-222222222222"),
        name="Problem Solving",
        category="technical",
    ),
    CompetencyBrief(
        id=UUID("33333333-3333-3333-3333-333333333333"),
        name="Communication",
        category="behavioral",
    ),
]

PACK_ITEMS: dict[UUID, list[str]] = {
    UUID("11111111-1111-1111-1111-111111111111"): [
        "Tell me about a system you designed that had to handle high throughput.",
        "How do you approach trade-offs between consistency and availability?",
    ],
    UUID("22222222-2222-2222-2222-222222222222"): [
        "Describe a time you debugged a particularly difficult production issue.",
    ],
    UUID("33333333-3333-3333-3333-333333333333"): [
        "How do you communicate technical decisions to non-technical stakeholders?",
    ],
}

CANNED_ANSWERS: list[str] = [
    # (1) Vague answer — should provoke vague_claim signal
    "We used microservices and it went well overall. The team was happy with it "
    "and we shipped on time. It was a good experience.",
    # (2) Detailed answer with quotable oddity — D-34 follow-up should quote this
    "We cut p99 latency 14x with a homemade bloom-filter cache we nicknamed "
    "the colander. It sits in front of our PostgreSQL read replicas and filters "
    "out 94% of cache-miss lookups before they ever hit the database.",
    # (3) Metric-heavy answer
    "Our service handles 2.3 million requests per second at peak. We achieved "
    "99.99% uptime over the last 18 months by implementing circuit breakers "
    "with a 50ms timeout and automatic failover to three geographic regions.",
]

CONFIG = ControllerConfig(
    policyVersion="v1",
    minQuestions=4,
    minFollowUps=1,
    maxQuestions=8,
    maxFollowUpsPerCompetency=2,
)

FIRST_QUESTION = "Tell me about a system you designed that had to handle high throughput."


# --- Trace printing (D-48) ---


def _print_trace(
    turn_num: int,
    answer: str,
    flags_summary: list[str],
    decision: Decision,
    generated_question: str,
    failure_mode: str | None,
) -> None:
    """Human-readable per-turn trace."""
    print(f"\n{'=' * 60}")
    print(f"  TURN {turn_num}")
    print(f"{'=' * 60}")
    print(f"\n  Candidate: {answer[:100]}{'...' if len(answer) > 100 else ''}")
    print(f"\n  Flags extracted ({len(flags_summary)}):")
    for flag_line in flags_summary:
        print(f"    - {flag_line}")
    if not flags_summary:
        print("    (none)")
    print(f"\n  Decision: action={decision.action}, target={decision.target_competency_id}")
    print(f"  Rationale: {decision.rationale}")
    if failure_mode:
        print(f"  Fallback tier: {failure_mode}")
    print(f"\n  Next question: {generated_question}")


# --- Mutable state container for the loop ---


class _SmokeState:
    """Mutable state passed through the turn loop."""

    def __init__(self) -> None:
        self.transcript: list[TranscriptTurn] = [
            TranscriptTurn(role="interviewer", content=FIRST_QUESTION),
        ]
        self.current_comp_idx: int = 0
        self.question_count: int = 1
        self.follow_up_count: int = 0
        self.follow_ups_by_comp: dict[UUID, int] = {}
        self.questions_asked_by_comp: dict[UUID, int] = {COMPETENCIES[0].id: 1}
        self.answers_by_comp: set[UUID] = set()


def _run_analyze(gateway: OpenRouterGateway, state: _SmokeState) -> tuple[list[str], bool, list]:
    """Analyze step — returns (flags_summary, analyze_failed, flags_for_policy)."""
    flags_summary: list[str] = []
    flags_for_policy = []
    analyze_failed = False

    try:
        analyze_result = gateway.analyze_answer(
            transcript=state.transcript,
            competencies=COMPETENCIES,
        )
        for flag in analyze_result.flags:
            line = f"{flag.flag}: {flag.detail}"
            if flag.answerExcerpt:
                line += f' [excerpt: "{flag.answerExcerpt[:60]}"]'
            flags_summary.append(line)
            flags_for_policy.append(flag)
    except GatewayError as exc:
        flags_summary.append(f"ANALYZE FAILED: {type(exc).__name__}: {exc}")
        analyze_failed = True

    return flags_summary, analyze_failed, flags_for_policy


def _resolve_generate_args(
    decision: Decision,
    state: _SmokeState,
    answer: str,
) -> tuple[CompetencyBrief, str | None, str | None, str | None]:
    """Resolve target competency, pack text, trigger excerpt/reason for generation."""
    target_comp = COMPETENCIES[state.current_comp_idx]
    if decision.target_competency_id:
        target_comp = next(c for c in COMPETENCIES if c.id == decision.target_competency_id)

    pack_text: str | None = None
    if decision.action == "new_topic":
        items = PACK_ITEMS.get(target_comp.id, [])
        asked_count = state.questions_asked_by_comp.get(target_comp.id, 0)
        if asked_count < len(items):
            pack_text = items[asked_count]

    trigger_excerpt: str | None = None
    trigger_reason: str | None = None
    if decision.trigger_flag:
        trigger_excerpt = decision.trigger_flag.answerExcerpt or answer[:80]
        trigger_reason = decision.trigger_flag.detail

    return target_comp, pack_text, trigger_excerpt, trigger_reason


def _update_state(decision: Decision, state: _SmokeState, target_comp: CompetencyBrief) -> None:
    """Advance mutable state after a turn."""
    state.question_count += 1

    if decision.action == "follow_up":
        state.follow_up_count += 1
        comp_id = decision.target_competency_id or COMPETENCIES[state.current_comp_idx].id
        state.follow_ups_by_comp[comp_id] = state.follow_ups_by_comp.get(comp_id, 0) + 1
        state.questions_asked_by_comp[comp_id] = state.questions_asked_by_comp.get(comp_id, 0) + 1
    elif decision.action == "new_topic" and decision.target_competency_id:
        new_idx = next(
            i for i, c in enumerate(COMPETENCIES) if c.id == decision.target_competency_id
        )
        state.current_comp_idx = new_idx
        state.questions_asked_by_comp[target_comp.id] = (
            state.questions_asked_by_comp.get(target_comp.id, 0) + 1
        )


# --- Main ---


def main() -> int:
    """Run live smoke trace. Returns 0 on success, 1 on missing config."""
    from pydantic import ValidationError

    from app.config import Settings

    # Settings instantiated INSIDE main() — never at module level
    try:
        settings = Settings()  # pyright: ignore[reportCallIssue] -- reads .env at runtime
    except (ValidationError, Exception) as exc:
        print(
            f"ERROR: Cannot load settings — check OPENROUTER_API_KEY and "
            f"OPENROUTER_LLM_MODEL in backend/.env: {exc}",
            file=sys.stderr,
        )
        return 1

    gateway = OpenRouterGateway(
        api_key=settings.openrouter_api_key,
        model=settings.openrouter_llm_model,
    )

    print(f"Pipeline smoke — model: {gateway.model_name}")
    print(
        f"Config: {CONFIG.maxQuestions} max questions, {CONFIG.maxFollowUpsPerCompetency} max FU/comp"
    )

    state = _SmokeState()

    for turn_num, answer in enumerate(CANNED_ANSWERS, start=1):
        state.transcript.append(TranscriptTurn(role="candidate", content=answer))
        state.answers_by_comp.add(COMPETENCIES[state.current_comp_idx].id)

        flags_summary, analyze_failed, flags_for_policy = _run_analyze(gateway, state)

        # --- Policy ---
        comp_facts = [
            CompetencyFacts(
                id=c.id,
                name=c.name,
                category=c.category,
                sort_order=i,
                questions_asked=state.questions_asked_by_comp.get(c.id, 0),
                has_candidate_answer=(c.id in state.answers_by_comp),
            )
            for i, c in enumerate(COMPETENCIES)
        ]

        decision = decide(
            PolicyInputs(
                config=CONFIG,
                competencies=comp_facts,
                current_competency_id=COMPETENCIES[state.current_comp_idx].id,
                question_count=state.question_count,
                follow_up_count=state.follow_up_count,
                follow_ups_by_competency=dict(state.follow_ups_by_comp),
                flags=flags_for_policy,
            )
        )

        # --- Generate ---
        target_comp, pack_text, trigger_excerpt, trigger_reason = _resolve_generate_args(
            decision, state, answer
        )

        outcome = run_generate(
            gateway,
            action="follow_up" if decision.action == "follow_up" else "new_topic",
            transcript=state.transcript,
            competency=target_comp,
            pack_item_text=pack_text,
            trigger_excerpt=trigger_excerpt,
            trigger_reason=trigger_reason,
            analyze_failed=analyze_failed,
        )

        _print_trace(
            turn_num=turn_num,
            answer=answer,
            flags_summary=flags_summary,
            decision=decision,
            generated_question=outcome.question_text,
            failure_mode=outcome.failure_mode,
        )

        # --- Update state ---
        state.transcript.append(TranscriptTurn(role="interviewer", content=outcome.question_text))
        _update_state(decision, state, target_comp)

        if decision.action == "end":
            print(f"\n{'=' * 60}")
            print("  INTERVIEW ENDED by policy")
            print(f"  Reason: {decision.completion_reason}")
            print(f"{'=' * 60}")
            break

    print(
        f"\n\nSmoke complete: {state.question_count} questions, {state.follow_up_count} follow-ups"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
