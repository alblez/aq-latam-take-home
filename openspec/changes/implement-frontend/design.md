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
- **Mock mode is a development aid only.** `NEXT_PUBLIC_USE_MOCK=true` swaps in an in-app mock data layer so the UI can be built and demoed while the backend lands. Hosted and production environments MUST set it to `false` and target the deployed backend — mock mode is not a substitute for the hosted end-to-end requirement.
- **Voice via the Web Speech API with a text fallback.** Browser support varies, so a text input path is always available and records `inputMode` accordingly.

## Risks / Trade-offs

- **Web Speech API support varies across browsers** → the text fallback guarantees the flow always works.
- **Mock/real divergence** → the mock layer implements the same contract types, and the typed client keeps both honest.
