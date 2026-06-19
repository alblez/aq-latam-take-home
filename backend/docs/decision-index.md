# Implementation Decision Index

This index maps the decision identifiers referenced in code comments and docstrings
to their one-line summaries. Decisions are grouped by prefix. For the higher-level
architecture decisions (D1–D27), see [`docs/decisions-log.md`](../../docs/decisions-log.md).

## D-XX — Implementation Decisions

| ID | Summary |
|---|---|
| D-01 | Idempotency: duplicate clientTurnId with same payload returns cached result |
| D-02 | Recovery: dangling candidate turn; single orchestrator entry point |
| D-03 | No DB transaction spans gateway calls; repair retry on validation failure |
| D-04 | questionCount = interviewer turn count; single-update terminal finalization |
| D-05 | Stale duplicate: pipeline completed → return current state; write-once model_name |
| D-06 | End-session idempotency + race handling for concurrent finalizers |
| D-07 | Protocol for test fakes; typed gateway methods (analyze/generate/evaluate) |
| D-08 | All-audio talkRatio = SUM(candidate audio_duration_ms) / durationMs |
| D-09 | All-text talkRatio = candidate_chars / total_chars; coverage requirements |
| D-10 | Mixed voice/text talkRatio; no TX spans gateway calls; loser converges via idempotency |
| D-11 | Null talkRatio edge cases; session guard primitives to prevent TOCTOU races |
| D-12 | Guard trip returns terminal-shaped 200; new_topic picks lowest sort_order gap |
| D-13 | Fixed priority order for follow-up trigger selection; evaluation-unavailable copy |
| D-14 | Deterministic question selection: fewest questions, lowest sort_order; reprobe when covered but minimums unmet |
| D-15 | Follow-up guard formula: depth must not endanger coverage; persist turn with action |
| D-16 | Policy inputs derived from persisted turns; all signals use persisted state |
| D-17 | Enough schema-valid state for panel/replay; evidence coverage built from turns |
| D-18 | Requires existing latest interviewer turn; candidate turns get reasoning=None |
| D-19 | One repair retry on analyze validation failure |
| D-20 | Quote normalization: collapse whitespace, trim to 240 chars; two-attempt retry loop |
| D-21 | Quote type: strength wins over concern; ModelGateway wired from app.state |
| D-22 | Turn submission flow entry point; deterministic quote note strings; 30s timeout |
| D-23 | End-early flow; analyze temp=0.0, generate temp=0.2; user-initiated early end |
| D-24 | Locked text for unprobed competency scores; final failure logging only |
| D-25 | User-end rationale with policy-math style; no TX spans gateway calls |
| D-26 | Failure/fallback vocabulary; score rows persisted in same TX-B |
| D-27 | Overall score derived at read time, never stored; prompt builders |
| D-28 | Module constants; force verdict=insufficient_signal when zero assessed |
| D-30 | In-progress sessions cannot have evaluations; full transcript in prompts |
| D-31 | Both evaluation artifacts absent → evaluation=None |
| D-32 | Loud failure on inconsistent evaluation state; new-topic prompt with pack seed |
| D-33 | Evaluation complete when narrative exists AND score count == competency count |
| D-34 | Quote verbatim below 120 chars, paraphrase above; follow-up embeds trigger excerpt |
| D-35 | Signal-to-human-phrase mapping; rationale template functions |
| D-36 | Spec-verbatim strings from docs/decisions-log.md |
| D-37 | Tests assert exact rationale strings |
| D-38 | Rationale strings use human competency NAME, never bare IDs |
| D-39 | Strict analyze response parsing (part of CTRL-03 group) |
| D-40 | Build analyze prompt demanding flags-only JSON output |
| D-41 | Strict analyze response parsing (part of CTRL-03 group) |
| D-42 | Strict flags-only schema: only a "flags" key, max 8 entries |
| D-46 | Live pipeline smoke test (DB-free, real OpenRouter calls) |
| D-47 | Live pipeline smoke test (DB-free, real OpenRouter calls) |
| D-48 | Human-readable per-turn trace printing in smoke test |

## CTRL-XX — Controller Policy Decisions

| ID | Summary |
|---|---|
| CTRL-01 | Single model-gateway boundary: all OpenRouter HTTP calls through one module |
| CTRL-03 | Strict analyze response parsing: model_validate_json on raw string |
| CTRL-04 | Deterministic policy: no LLM influence on flow choice |
| CTRL-05 | Deterministic policy: pure functions, no I/O, no Settings |
| CTRL-08 | Generate question orchestration with tiered fallback |
| CTRL-09 | Strict JSONB validation on all persisted structured columns |

## SESS-XX — Session Flow Decisions

| ID | Summary |
|---|---|
| SESS-05 | Dangling candidate recovery: call pipeline for existing unfinished turn |
| SESS-08 | Orchestrator pipeline MUST be called with NO open DB transaction |

## Pitfall N — Implementation Pitfalls

| ID | Summary |
|---|---|
| Pitfall 1 | All fields required in ModelCompetencyScore (strict Pydantic) |
| Pitfall 2 | Python-mode strict rejects string UUIDs; capture turn snapshots while ORM live |
| Pitfall 3 | Constructor takes explicit args — never read env/Settings at import time |
| Pitfall 6 | Never hold DB transaction open during gateway (HTTP) call |
| Pitfall 8 | Sparse/malformed reasoning JSONB → gracefully return empty flags |
| Pitfall 11 | Single-update terminal finalization: all fields set in one flush |

## CR-XX — Code Review Decisions

| ID | Summary |
|---|---|
| CR-01 | Close TX before gateway call; lazy load would hold TX during HTTP call |

## WR-XX — Concurrency/Write Decisions

| ID | Summary |
|---|---|
| WR-01 | Defense-in-depth for race: latest-is-candidate check under lock |
| WR-02 | Batch job titles per job to eliminate object_session introspection |
| WR-03 | Avoid lazy load after TX-A commit: use pre-commit captured values |

## T-XX-XX — Task References

| ID | Summary |
|---|---|
| T-09-07 | Fixed 50-session server-side cap on history detail queries |
