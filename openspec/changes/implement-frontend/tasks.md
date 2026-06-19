## 1. App shell + typed client

- [ ] 1.1 Next.js app scaffold (App Router), Tailwind, base layout
- [ ] 1.2 Typed API client from the generated contract types; auto-attach `X-Owner-Id`
- [ ] 1.3 Mock data layer toggled by `NEXT_PUBLIC_USE_MOCK` (local development aid)

## 2. Thin vertical slice (one role, end to end)

- [ ] 2.1 Job list page (at least 3 roles)
- [ ] 2.2 Interview Room: show the question, submit a text answer, advance a turn
- [ ] 2.3 Review screen: transcript + structured evaluation

## 3. Voice input

- [ ] 3.1 Microphone capture + Web Speech transcription; record `inputMode = voice`
- [ ] 3.2 Text fallback when speech recognition is unavailable

## 4. Decision panel (stretch 1)

- [ ] 4.1 Render the live rubric, signals, and rationale each turn

## 5. History + replay (stretch 4)

- [ ] 5.1 History page with per-session metrics and a role filter
- [ ] 5.2 Replay a completed session with its decision panel state

## 6. Quality

- [ ] 6.1 Strict `tsc` + Biome + knip + Vitest green
- [ ] 6.2 `contract-types:check` green (no drift from the contract)
