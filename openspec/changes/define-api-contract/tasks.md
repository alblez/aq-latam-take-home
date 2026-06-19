## 1. Stabilize the emitted contract

- [ ] 1.1 Review `shared/contract.yaml` emitted by `implement-backend`; stabilize the schema names and required fields the frontend depends on
- [ ] 1.2 Document the invariants: `X-Owner-Id` scoping, the structured error envelope, and the stable `error.code` values
- [ ] 1.3 Document the contract change/versioning rule (edits go through a new OpenSpec change; backend regenerates the contract)

## 2. Frontend codegen and drift checks

- [ ] 2.1 Generate `frontend/types/api/contract.ts` via `openapi-typescript`
- [ ] 2.2 Add `contract-types:check` to the frontend quality gate
- [ ] 2.3 Confirm the backend's runtime OpenAPI still matches the committed `shared/contract.yaml`
