# ADR-002: Synchronous SQLAlchemy Engine and Request Model

## Decision

Run a synchronous request model — synchronous route handlers, a synchronous SQLAlchemy engine, a session per request, and a synchronous repository layer — instead of async SQLAlchemy. A single synchronous runtime keeps persistence and migration uniform and simple.

## Context

- The external model-provider boundary is already synchronous, so async would add no concurrency benefit there.
- The migration path (ADR-001) is synchronous; one runtime keeps the persistence and migration story uniform.
- Transactions are short (ADR-003), so blocking I/O does not bottleneck request throughput at current scale.
- Async SQLAlchemy with async handlers was an option; rejected as a cross-cutting change across dependencies, routes, repositories, tests, and orchestration for no real gain.
- Mixed sync and async sessions were rejected: two session models in one app invite footguns.
- `IMPLEMENTATION_DECISIONS.md` records the synchronous request model (no SSE; panel updates return synchronously) and the transaction-boundary rules.

## Consequences

- Database and model calls are synchronous boundaries; handlers must keep transactions short and never hold a session across a slow external call (ADR-003).
- Repository code stays simple and aligned with the synchronous migration path (ADR-001).
- Introducing async sessions later requires a deliberate, broader migration plan, not a piecemeal mix.
