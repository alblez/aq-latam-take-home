# ADR-005: Interview State Machine and Reasoning Contract

## Decision

Interview room uses `useReducer` with finite phases. Every interviewer turn carries a `ReasoningSnapshot` with full rubric state. Decision panel and replay render from these snapshots directly.

## Context

- Current `useState` patch pattern (`setData(prev => ({...prev, ...patch}))`) allows invalid state transitions: submit while speaking, double-submit from listening, speaking while already speaking.
- Spec D7: `turns.reasoning` stores full rubric snapshot per turn (not deltas).
- Spec D17: Reasoning populated from Phase 2, making Phase 4 (decision panel) purely a rendering task.
- Spec D13: Replay shows panel state at each turn from stored snapshots.

## Consequences

- Reducer is a pure function — testable without React, auditable transitions.
- Valid phases: `welcome`, `thinking`, `speaking`, `answering`, `ended`, `error`.
- Invalid transitions are no-ops (e.g., SUBMIT_ANSWER from `speaking` returns unchanged state).
- `sessionId` lives in reducer state after BEGIN — all subsequent API calls use it.
- No external state library (Zustand, Jotai, Redux). `useReducer` is built-in React, zero bundle cost.
- Decision panel reads `panelState` from state (fed by SSE or POST response).
- Replay reads `turn.reasoning` directly — never recomputes panel state from turn index.
- Mock interview engine produces valid `ReasoningSnapshot` per interviewer turn.
