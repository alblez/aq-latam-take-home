# ADR-005: Separate Strict JSONB and API Models

## Decision

Validate persisted JSONB payloads — controller config, reasoning, terminal panel state, evaluation narrative, evidence — with their own strict models that forbid unknown fields, kept separate from the public HTTP request/response models that mirror the API contract. Two model sets let persistence reject drifted JSONB while the API shape evolves independently.

## Context

- Stored JSONB and the public wire format change for different reasons and at different rates.
- Persistence needs a strict guard; the public API needs freedom to evolve.
- One shared model set was rejected: it couples the wire format to the stored format, so either the API cannot evolve without a migration or persistence loses its strict guard.
- Loose, non-strict persistence validation was rejected: drifted JSONB would be written silently.
- `IMPLEMENTATION_DECISIONS.md` §3 "JSONB validation schemas" records "JSONB is flexible in Postgres but strict in backend code"; `CONTRACT_DECISIONS.md` defines the public API contract the HTTP models mirror.

## Consequences

- Some fields and nested shapes are intentionally duplicated across database and API models — the price of independent evolution.
- Persistence can reject malformed or drifted JSONB even when the API shape is stable.
- Changes crossing the database and API seam need coordinated edits in both model sets and their tests.
