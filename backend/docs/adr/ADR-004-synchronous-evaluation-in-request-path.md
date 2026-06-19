# ADR-004: Synchronous Evaluation in the Request Path

## Decision

Run the final interview evaluation synchronously inside the same request that makes the session terminal — a turn that ends the interview, or an explicit end-early — rather than dispatching it to a background worker or queue. A successful terminal response then exposes ready evaluation state immediately.

## Context

- The deployment target favors simplicity: no worker, queue, scheduler, or recovery daemon to operate.
- Clients should see evaluation state on the terminal response without polling.
- A background worker or job queue was rejected (deferred): it adds infrastructure and forces the client to poll for readiness.
- Fire-and-forget with later polling was rejected: same operational cost, weaker user experience.
- `IMPLEMENTATION_DECISIONS.md` ("no background worker for evaluation or recovery"; §9 Deferred work) and `CONTRACT_DECISIONS.md` (evaluation generated and persisted synchronously; "no background worker needed") record this.

## Consequences

- A terminal request can be slow when the provider or a repair retry is slow; evaluation is given a generous dedicated timeout budget.
- Terminal responses expose evaluation state without polling a queue.
- Moving evaluation out of band later would change request semantics, persistence timing, and frontend readiness handling — a future ADR.
