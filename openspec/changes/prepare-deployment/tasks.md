## 1. Hosting setup

- [x] 1.1 Provision a managed PostgreSQL database
- [x] 1.2 Configure the backend host: env vars, a release step that runs `alembic upgrade head` + seed, and a `/health` check
- [x] 1.3 Configure the frontend host: `NEXT_PUBLIC_API_URL` and `API_URL` pointing at the deployed backend

## 2. Deploy the thin slice first

- [x] 2.1 Deploy the minimal end-to-end slice (one role → interview → evaluation) to public URLs
- [x] 2.2 Set backend `CORS_ALLOWED_ORIGINS` to the frontend origin
- [x] 2.3 Verify a full interview against the hosted backend

## 3. Publish

- [x] 3.1 Publish the single public GitHub repository
- [x] 3.2 Confirm the publicly viewable website and link it from the README
- [x] 3.3 Re-deploy as backend and frontend features land
