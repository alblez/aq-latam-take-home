## Context

The backend produces `shared/contract.yaml` from its runtime OpenAPI. That document is accurate by construction but auto-generated; before the frontend builds against it, the interface needs to be reviewed for stability and pinned as the agreed contract. This change records those interface decisions and wires the tooling that keeps the two sides in sync.

## Goals / Non-Goals

**Goals:**
- A stable interface the frontend can generate types from without churn.
- Clear, documented invariants and a rule for how the contract changes over time.
- Bidirectional drift detection: frontend generated types ↔ contract, and backend runtime schema ↔ contract.

**Non-Goals:**
- Redesigning the API. The shape comes from the backend; this change stabilizes it, it does not re-author it.
- Authentication / authorization (see owner-scoping invariant).

## Decisions

- **The contract is committed to the repository.** A drift check asserts the backend's runtime OpenAPI matches the committed contract, so code and contract cannot silently diverge. This change reviews the committed file and stabilizes schema names and field optionality the frontend relies on. *Alternative considered:* auto-emitting the contract from the runtime on every build — not chosen, because a committed document is reviewable and stable across builds.
- **Owner-scoping invariant.** Every `/api` endpoint requires an `X-Owner-Id` UUID header and scopes data to that owner. Anonymous and browser-local; satisfies "save my sessions" without an account system. Spoofable, not security-grade — acceptable for this scope and noted as a limitation.
- **Structured error envelope.** All errors use `{ error: { code, message, details?, requestId? } }` with a closed `code` enum, so clients branch on `code` rather than HTTP status alone.
- **Change / versioning rule.** Once stabilized, the contract changes only through a new OpenSpec change; the drift check keeps the backend runtime OpenAPI and the committed contract identical at all times.
- **Frontend codegen.** `openapi-typescript` generates `frontend/types/api/contract.ts`; `contract-types:check` fails when the committed types diverge from the contract.

## Risks / Trade-offs

- **Auto-generated naming/optionality may be awkward** → reviewed and stabilized here before the frontend depends on it.
- **Drift between backend runtime and committed contract** → the bidirectional checks fail the quality gate on either side.
