# ADR-008: Real-Mode Only

## Decision

The frontend always talks to the live backend. There is no mock mode, no silent fallback, and no fake-data path. A missing `NEXT_PUBLIC_API_URL` fails loud at module init — it throws immediately rather than silently serving fabricated data.

This supersedes ADR-003 (explicit mock mode), ADR-002 (stub-first frontend polish), and ADR-004 (shared stub session store). The mock substrate those ADRs described has been deleted.

**Surviving invariant from ADR-003:** No silent fallback — errors are errors. Catch blocks dispatch error states to the UI; they never fall through to fake data.

## Context

- The mock substrate was a development convenience: a self-contained in-memory session engine that let the frontend run without a backend. It served its purpose during initial UI buildout.
- Once the backend was production-ready and the contract was stable, the mock path became a liability: a missing `NEXT_PUBLIC_API_URL` silently activated the mock directory, meaning a misconfigured production deploy could serve fake interviews to real users with no visible indication.
- The "fail loud" principle (ADR-003's core insight) was correct — the implementation of that principle via a mock-mode flag was the problem. The flag's absence-means-mock behavior was a landmine.
- Phase 14 removes the entire mock substrate and replaces the flag-based guard with a throw-at-init guard in `lib/api/client.ts`. If `NEXT_PUBLIC_API_URL` is not set, the module throws at import time — the loudest possible signal.

## Consequences

- Local development requires the backend running (default: `http://localhost:8000`). There is no frontend-only iteration path.
- `NEXT_PUBLIC_API_URL` is a required configuration value. Builds and dev servers fail immediately if it is absent.
- The throw-at-init guard in `lib/api/client.ts` ensures misconfiguration is caught at boot, not at runtime when a user hits a page.
- All API service modules (`lib/api/sessions.ts`, `lib/api/evaluation.ts`, `lib/api/history.ts`, `lib/api/jobs.ts`) have a single code path: call the live backend via `apiCall()`. No branching, no dynamic imports of fake data.
- Test fixtures are contract-typed builders in `test/fixtures.ts`, not runtime mock data. Tests never depend on the mock substrate.
- Errors surface as errors — in error boundaries, loading states, and user-facing messages. Never as silently fabricated content.
