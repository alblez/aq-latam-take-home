# ADR-001: Schema-First SQL Through Alembic

## Decision

Define the database schema as hand-written SQL — the six-table competency spine with PostgreSQL enums, constraints, partial indexes, and JSONB checks — and have Alembic apply that DDL verbatim, rather than autogenerating migrations from ORM metadata. The explicit, reviewable DDL is the single source of truth the rest of the backend assumes.

## Context

- The schema is the foundation: runtime, transactions, JSONB models, and analytics all assume it exists first.
- The design leans on PostgreSQL-specific features — enums, partial indexes, JSONB checks — that ORM autogeneration represents poorly.
- ORM-metadata autogeneration was an option; rejected because it hides those constraints behind ORM models and produces migrations no one reviews carefully.
- Using the ORM as the schema source of truth was rejected: it couples the schema to ORM mapping and weakens database-level guarantees.
- `backend-database-decisions.md` records that Alembic should translate `schema.sql` into migrations; `schema.sql` is the canonical schema reference.

## Consequences

- PostgreSQL constraints, enums, partial indexes, and JSONB checks stay explicit and reviewable.
- With no ORM metadata source, autogenerate cannot detect drift; the canonical schema reference and the migration DDL must be kept in sync by hand.
- Database lint and smoke checks are the authority for catching schema drift.
- Future migrations must preserve schema-first discipline — write the DDL, do not generate it.
