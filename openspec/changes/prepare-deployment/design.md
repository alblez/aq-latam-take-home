## Context

The brief mandates a hosted, publicly reachable deployment. This document records the deployment topology and the configuration needed to run the app end-to-end against a real backend. Deployment is delivered early on the thin vertical slice and re-run as features land, so the public URL is live throughout.

## Goals / Non-Goals

**Goals:**
- A public HTTPS URL serving the full candidate flow against a real backend and database.
- Repeatable releases: migrations and idempotent seed run on every backend deploy.
- Production configuration that disables mock mode and restricts CORS to the frontend origin.

**Non-Goals:**
- Multi-region or autoscaling infrastructure. Zero-downtime migration orchestration. Custom domains beyond what the host provides.

## Decisions

- **Topology**: frontend on a Next.js-friendly host (e.g. Vercel), backend as a container service (e.g. Railway or Fly), and a managed PostgreSQL database. Hosts are interchangeable; the contract and env wiring are what matter.
- **Release runs migrations + seed.** The backend release step runs `alembic upgrade head` then the idempotent seed, so a fresh environment is ready after deploy and re-deploys are safe.
- **Production disables mock mode.** The frontend is deployed with `NEXT_PUBLIC_USE_MOCK=false` and its API URLs pointing at the deployed backend; the backend restricts `CORS_ALLOWED_ORIGINS` to the frontend origin.
- **Secrets via host environment**, never committed. `OPENROUTER_API_KEY`, `DATABASE_URL`, and origins are set in the host's env settings.

## Risks / Trade-offs

- **Free-tier cold starts** → first request after idle is slow; acceptable for a demo and noted in the README.
- **Managed DB connection limits** → keep pool sizing modest.

## Migration Plan

1. Provision the managed PostgreSQL database.
2. Deploy the backend with env set; release runs migrations + seed; verify `/health`.
3. Deploy the frontend pointing at the backend with mock mode off.
4. Verify a full interview end-to-end against the hosted backend; confirm the public URL.
