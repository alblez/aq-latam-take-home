# ADR-007: Current Session Route Shape

## Decision

For this FE polish pass, keep existing route `/interview/[sessionId]`. Job card creates/reserves a session, then navigates to the session route. Do not rewrite to `/interview/[jobId]`.

## Context

- Current app uses `[sessionId]` in the route. Job card calls `createSession(jobId)` → gets `sessionId` → navigates to `/interview/{sessionId}`.
- Unified parallel plan spec conceptually describes `/interview/[jobId]` with session creation happening on Begin.
- Changing route shape during FE polish creates unnecessary churn with no demo value.
- The session-first approach works for stubs: `createSession` returns a demo session immediately.

## Consequences

- Job card calls `createSession(jobId)` → receives `sessionId` → `router.push(/interview/{sessionId})`.
- Welcome screen and Begin button operate within the existing session context.
- Begin starts the interview (first question generated) for the already-created session.
- The mock engine must handle "session created but not started" state gracefully.
- This decision is scoped to the FE polish phase.
