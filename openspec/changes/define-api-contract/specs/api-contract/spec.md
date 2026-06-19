## ADDED Requirements

### Requirement: Stabilized OpenAPI contract sourced from the backend
The frontend↔backend interface SHALL be a single OpenAPI 3.1 document at `shared/contract.yaml`, committed as the authoritative interface with a drift check asserting the backend's runtime OpenAPI matches it at all times. Once stabilized, the contract MUST only change through an OpenSpec change that modifies the `api-contract` capability.

#### Scenario: Contract matches the running backend
- **WHEN** the contract is stabilized from the backend's runtime OpenAPI
- **THEN** the committed `shared/contract.yaml` matches the backend's runtime schema
- **AND** the frontend generates its types from that document

#### Scenario: Interface changes are reviewed
- **WHEN** a developer needs to change the API shape
- **THEN** the backend change regenerates the contract and they open an OpenSpec change that modifies `api-contract`

### Requirement: Owner-scoped access via X-Owner-Id
Every application endpoint under `/api` SHALL require an `X-Owner-Id` request header containing a UUID, and MUST scope all session data to that owner. Requests with a missing or malformed owner id MUST return `400` with `error.code = invalid_owner_id`.

#### Scenario: Valid owner id scopes data
- **WHEN** a client calls `/api/history` with a valid `X-Owner-Id`
- **THEN** the response contains only sessions belonging to that owner

#### Scenario: Missing or malformed owner id is rejected
- **WHEN** a client calls an `/api` endpoint without a valid UUID `X-Owner-Id`
- **THEN** the response is `400` with `error.code = invalid_owner_id`

### Requirement: Standard structured error model
All error responses SHALL use the envelope `{ error: { code, message, details?, requestId? } }` where `code` is one of the contract's closed enum values. Clients MUST be able to branch on `error.code` independent of HTTP status.

#### Scenario: Known domain error returns a stable code
- **WHEN** a client requests a session that does not exist for the owner
- **THEN** the response is `404` with `error.code = session_not_found`

#### Scenario: Validation failure returns validation_error
- **WHEN** a request body fails contract validation
- **THEN** the response is `422` with `error.code = validation_error`

### Requirement: Generated client types stay in sync with the contract
The frontend SHALL generate its API types from `shared/contract.yaml` via `openapi-typescript`, and a drift gate (`contract-types:check`) MUST fail when the committed types diverge from the contract. The backend MUST assert that its runtime-generated OpenAPI matches the committed contract.

#### Scenario: Frontend type drift fails the gate
- **WHEN** the contract changes but `frontend/types/api/contract.ts` is not regenerated
- **THEN** `contract-types:check` fails and blocks the quality gate

#### Scenario: Backend schema drift fails the gate
- **WHEN** the backend's runtime OpenAPI no longer matches `shared/contract.yaml`
- **THEN** the backend conformance check fails
