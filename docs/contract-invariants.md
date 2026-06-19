# API Contract Invariants

## Owner scoping

Every `/api` endpoint requires an `X-Owner-Id` header containing a UUID. All session
data is scoped to that owner. Missing or malformed → `400` with
`error.code = invalid_owner_id`.

## Error envelope

All error responses use `{ error: { code, message, details?, requestId? } }` where
`code` is one of:

| Code | HTTP | Meaning |
|---|---|---|
| `invalid_owner_id` | 400 | Missing or malformed X-Owner-Id |
| `job_not_found` | 404 | Job does not exist |
| `session_not_found` | 404 | Session does not exist for this owner |
| `session_not_in_progress` | 409 | Session is not in_progress |
| `session_in_progress` | 409 | Session is still in_progress |
| `turn_already_submitted` | 409 | Duplicate clientTurnId with different payload |
| `validation_error` | 422 | Request body failed validation |
| `model_unavailable` | 500 | LLM gateway unavailable |
| `catalog_setup_error` | 500 | Seed/catalog misconfiguration |

Clients branch on `error.code` independent of HTTP status.

## Contract change rule

`shared/contract.yaml` is the authoritative interface. The backend drift check
(`just backend-contract-drift`) asserts the runtime OpenAPI matches the committed
contract. The frontend drift check (`just frontend-contract-types-check`) asserts the
generated types match the contract. Once stabilized, the contract changes only through
a new OpenSpec change that modifies the `api-contract` capability.

## Codegen

`openapi-typescript ../shared/contract.yaml -o types/api/contract.ts` generates the
frontend types. The generated file is committed (not gitignored) so the drift gate can
compare against it.
