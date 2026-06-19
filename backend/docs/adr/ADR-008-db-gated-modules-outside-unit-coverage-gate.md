# ADR-008: DB-Gated Modules Outside the Unit Coverage Gate

## Decision

Exclude database-heavy modules — the repository layer, routes, turn orchestration, and the request-scoped database dependency — from the fast unit-test coverage gate, and verify them through real, containerized PostgreSQL tests instead of database mocks. Their behavior lives in SQL constraints, transactions, and migrations that mocks cannot meaningfully exercise.

## Context

- The behavior that matters in these modules is SQL constraints, transactions, and migrations.
- Database mocks assert call shapes, not real behavior.
- Holding every module to the unit coverage threshold via database mocks was rejected: brittle mocks give false confidence.
- Dropping the coverage gate entirely was rejected: it loses the fast regression signal on pure-logic modules.
- `IMPLEMENTATION_DECISIONS.md` §8 "Test plan" records the minimum regression test plan and mocking the model gateway in tests.

## Consequences

- Coverage percentage alone is not full confidence for persistence behavior; reviewers and CI must treat the database-marked tests as part of the safety net.
- New persistence or route behavior should add database-gated tests when SQL constraints, transactions, or migrations matter.
- This leaves branch-coverage blind spots in the fast unit gate — an accepted trade-off.
