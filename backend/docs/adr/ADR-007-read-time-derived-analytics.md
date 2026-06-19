# ADR-007: Read-Time Derived Analytics

## Decision

Derive history, replay, and evaluation analytics — duration, coverage percent, overall score, talk ratio, question count, follow-up count — at read time from sessions, turns, and competency score rows, rather than storing aggregate metric rows. Stored data stays the single source of truth and can be recomputed after logic changes.

## Context

- Metrics depend on logic that changes; recomputing from source avoids stale aggregates.
- Current scale makes read-time computation affordable.
- A persisted or denormalized aggregate metrics table was rejected (deferred): it adds invalidation and drift risk and complicates writes; recorded as a possible future decision if read cost demands it.
- `IMPLEMENTATION_DECISIONS.md` records "analytics are derived live … do not add a persisted metrics table" (§9 Deferred work lists a materialized analytics table); `schema.sql` notes common analytics are derived and defines no aggregate metrics table.

## Consequences

- Writes stay simple — there are no aggregate rows to update or invalidate.
- History reads do batch queries and computation proportional to the sessions returned.
- Metrics can be recomputed from source after logic changes.
- Adding persisted analytics later requires a new ADR because it introduces invalidation and drift.
