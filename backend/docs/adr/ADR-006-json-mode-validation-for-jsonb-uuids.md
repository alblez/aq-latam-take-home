# ADR-006: JSON-Mode Validation for JSONB UUIDs

## Decision

Validate strict JSONB payloads with UUID fields in JSON mode — serialize the loaded value back to a JSON string and validate that — rather than validating the in-memory dictionary directly. This is the only path that keeps strict mode on and still accepts the stored shape.

## Context

- Strict-mode validation rejects plain string values for UUID fields.
- PostgreSQL stores JSONB UUIDs as strings and returns plain dictionaries on read.
- Direct object validation of the dictionary was rejected: strict mode rejects string UUIDs and fails on valid stored payloads.
- Relaxing strict mode or dropping UUID typing was rejected: it gives up the strict guard from ADR-005.
- Pre-coercing UUID strings field by field was rejected: brittle and easy to miss on nested shapes.
- `IMPLEMENTATION_DECISIONS.md` §3 records this as the Strict-Mode JSONB UUID Coercion Pattern.

## Consequences

- Every strict JSONB read with UUID fields must use this pattern, or a shared helper; direct object validation will fail against valid persisted JSON.
- Strict-mode validation stays intact for persisted snapshots (ADR-005).
- The extra serialization round-trip is surprising, so it warrants an explaining comment wherever it is used.
