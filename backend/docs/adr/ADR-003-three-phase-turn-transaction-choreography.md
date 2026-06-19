# ADR-003: Three-Phase Turn Transaction Choreography

## Decision

Process each interview turn in three phases: a first short transaction reads state and derives a snapshot, then commits; model-provider calls and pure policy run with no transaction open; then a second guarded transaction re-validates state and writes or finalizes. This keeps provider latency out of any database transaction or row lock.

## Context

- Model-provider calls take seconds; holding a transaction across them would hold row locks for that whole time.
- The snapshot derived in the first phase can drift while the model calls run — a concurrent submit or end-early.
- A single transaction spanning the model calls was rejected: it throttles concurrency and risks timeouts.
- An optimistic write without re-validation was rejected: the second phase must re-check because the snapshot can drift.
- `IMPLEMENTATION_DECISIONS.md` §7 "Transaction boundaries" states: do not hold a database transaction during a model call.

## Consequences

- The second phase must re-check session state; concurrent submit and end-early races are expected behavior, not incidental errors, and must converge explicitly.
- Recovery and idempotency paths stay first-class and must remain tested whenever the choreography changes.
- Builds on the synchronous request model (ADR-002).
