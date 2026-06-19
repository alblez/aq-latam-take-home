## Why

The brief requires the app to work end-to-end in a hosted environment, deployed to a publicly viewable website from a public GitHub repository. This change delivers that hosted deployment. It is a required part of the deliverable, not optional.

## What Changes

- Deploy the frontend and backend to managed hosting with a managed PostgreSQL database, reachable over HTTPS.
- Run database migrations and the idempotent seed on backend release.
- Configure production environment: `NEXT_PUBLIC_USE_MOCK=false`, `NEXT_PUBLIC_API_URL` / `API_URL` pointing at the deployed backend, backend `CORS_ALLOWED_ORIGINS` allowing the frontend origin, plus `DATABASE_URL` and `OPENROUTER_*`.
- Publish the repository publicly with a working public URL.

## Capabilities

### New Capabilities
- `production-deployment`: a publicly hosted, end-to-end deployment of the frontend, backend, and database, with deploy-time migrations, seed, and configuration.

## Requirements Coverage

- **Core**: "Must work end-to-end in a hosted environment" and "deployed on a publicly viewable website" from a single public GitHub repository.

## Impact

- Hosting for the frontend (e.g. Vercel), the backend (e.g. Railway or Fly), and a managed PostgreSQL instance.
- Depends on a deployable slice of `implement-backend` and `implement-frontend`. The thin vertical slice is deployed early and then re-deployed as features land.
