## Why

`implement-backend` commits `shared/contract.yaml` with a drift check against the runtime OpenAPI. This change turns that committed document into a stable, agreed interface the frontend can build against: it reviews and stabilizes the contract, documents its invariants, generates the frontend client types, and wires the drift checks that keep both sides in sync.

## What Changes

- Review and stabilize `shared/contract.yaml` produced by `implement-backend` — confirm the schema names and required fields the frontend depends on are stable.
- Document the interface invariants: the `X-Owner-Id` owner-scoping rule, the structured error envelope, the stable `error.code` values, and the rule for how the contract changes over time.
- Generate the frontend client types (`openapi-typescript` → `frontend/types/api/contract.ts`).
- Add `contract-types:check` to the frontend quality gate.
- Confirm the backend's runtime OpenAPI still matches the committed `shared/contract.yaml`.

## Capabilities

### New Capabilities
- `api-contract`: the stabilized request/response interface, the owner-scoping rule, the structured error model, the change/versioning rule, and the codegen + drift checks that keep the frontend and backend aligned.

## Requirements Coverage

Provides the stable, typed interface the frontend consumes, so it enables every frontend-facing requirement: the jobs list, the Interview Room turn flow, the saved session with transcript and structured evaluation, and history/replay. It also pins the schemas for the decision panel (stretch 1) and question-pack provenance (stretch 2).

## Impact

- Stabilizes `shared/contract.yaml`; adds the frontend codegen target `types/api/contract.ts` and the `contract-types:check` gate.
- **Depends on `implement-backend`** (consumes its emitted contract). **Blocks `implement-frontend`**, which builds against the generated types.
