## Purpose

Publicly hosted deployment of the frontend, backend, and database, with deploy-time migrations, seed, and configuration.

## Requirements

### Requirement: Publicly hosted deployment
The system SHALL be deployed to a public, hosted environment with the frontend and backend reachable over HTTPS, backed by a managed PostgreSQL database, from a single public GitHub repository. The candidate flow MUST work end-to-end against the hosted backend.

#### Scenario: Hosted build serves the full flow
- **WHEN** the app is deployed with the backend, database, and frontend configured
- **THEN** a user at the public URL can browse jobs, complete an interview, and view an evaluation against the hosted backend

### Requirement: Deploy-time configuration and data setup
A production deployment SHALL run database migrations and the idempotent seed before serving traffic, and MUST configure cross-origin access and the environment variables required by both tiers.

#### Scenario: Migrations and seed run before serving
- **WHEN** a new backend deployment is released
- **THEN** Alembic migrations and the idempotent seed run, and `/health` reports ready

#### Scenario: Frontend targets the hosted backend
- **WHEN** the frontend is deployed for production
- **THEN** `NEXT_PUBLIC_API_URL` / `API_URL` target the hosted backend, and backend `CORS_ALLOWED_ORIGINS` permits the frontend origin
