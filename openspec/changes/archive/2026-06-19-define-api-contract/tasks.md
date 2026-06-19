## 1. Frontend project scaffold for contract codegen

- [x] 1.1 `frontend/package.json` with `openapi-typescript` devDependency, `contract-types` and `contract-types:check` scripts, project metadata (`ai-interviewer-frontend`)
- [x] 1.2 `frontend/tsconfig.json` (strict mode, `@/*` path alias, includes `**/*.ts`)
- [x] 1.3 `frontend/biome.json` excluding `types/api/` from linting

## 2. Generate and commit frontend contract types

- [x] 2.1 Generate `frontend/types/api/contract.ts` via `openapi-typescript` from `shared/contract.yaml`
- [x] 2.2 Add `frontend/scripts/check-contract-types.mjs` drift gate (regenerate to temp, diff against committed)
- [x] 2.3 Verify `just frontend-contract-types-check` passes (committed types match contract)

## 3. Document contract invariants

- [x] 3.1 Document the `X-Owner-Id` owner-scoping rule and the structured error envelope with stable `error.code` values
- [x] 3.2 Document the contract change/versioning rule (edits go through a new OpenSpec change; backend drift check keeps runtime aligned)

## 4. Verify drift checks

- [x] 4.1 Confirm `just backend-contract-drift` passes (runtime OpenAPI == committed contract)
- [x] 4.2 Confirm `just frontend-contract-types-check` passes (generated types == committed types)
- [x] 4.3 Confirm `just contract-check` passes (redocly lint)
- [x] 4.4 Confirm `just bootstrap-check` and `openspec validate --all` pass
