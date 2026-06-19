## Context

The frontend is a Next.js app built against the `api-contract`. It must run a voice-first interview, render the interviewer's live reasoning, and present a transcript plus structured evaluation, with minimal friction.

## Goals / Non-Goals

**Goals:**
- A typed client generated from the contract so the UI never drifts from the API.
- A voice-first flow that still works where speech recognition is unavailable.
- Local development without a running backend via a mock data layer.

**Non-Goals:**
- Video mode (stretch 3), deferred. Authentication. A design system beyond the component primitives needed for a clean UI.

## Decisions

- **App Router with server and client components.** Data fetching through a typed client built on the generated contract types; `X-Owner-Id` is generated client-side and attached to every request.
- **Real backend mode.** The frontend always talks to the live backend via `NEXT_PUBLIC_API_URL`. There is no mock mode — the app fails fast if the backend URL is not configured. Hosted and production environments use the deployed backend.
- **Voice via the Web Speech API with a text fallback.** Browser support varies, so a text input path is always available and records `inputMode` accordingly.

## Risks / Trade-offs

- **Web Speech API support varies across browsers** → the text fallback guarantees the flow always works.
- **Mock/real divergence** → eliminated by design: the frontend always uses the real backend, and the typed client keeps the contract honest.
