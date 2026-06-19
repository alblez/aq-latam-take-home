## 1. App scaffold and design system

- [x] 1.1 Next.js config files (`next.config.js`, `postcss.config.mjs`, `components.json`, `knip.json`, `.nvmrc`)
- [x] 1.2 Global styles and fonts (`app/globals.css`, `app/fonts/`)
- [x] 1.3 Root layout (`app/layout.tsx`)
- [x] 1.4 shadcn UI primitives (`components/ui/` — badge, button, card, dialog, scroll-area, select, separator, sheet, skeleton, tabs, textarea, tooltip)
- [x] 1.5 Utility helper (`lib/utils.ts`)

## 2. Types and API layer

- [x] 2.1 Type alias files (`types/competency.ts`, `types/evaluation.ts`, `types/job.ts`, `types/session.ts`, `types/turn.ts`)
- [x] 2.2 API client and endpoints (`lib/api/client.ts`, `lib/api/jobs.ts`, `lib/api/sessions.ts`, `lib/api/evaluation.ts`, `lib/api/history.ts`)
- [x] 2.3 Owner ID and session utilities (`lib/owner-id.ts`, `lib/format-date.ts`, `lib/pending-turn.ts`, `hooks/use-owner-id.ts`)
- [x] 2.4 Results helpers (`lib/results/evidence.ts`, `lib/results/limitations.ts`, `lib/results/verdict.ts`)

## 3. Interview hooks

- [x] 3.1 Interview state machine (`hooks/use-interview-machine.ts`)
- [x] 3.2 Answer input controller (`hooks/use-answer-input-controller.ts`)
- [x] 3.3 Speech recognition STT (`hooks/use-speech-recognition.ts`)
- [x] 3.4 Speech synthesis TTS (`hooks/use-speech-synthesis.ts`)

## 4. Components

- [ ] 4.1 Shared components (`components/shared/empty-state.tsx`, `components/shared/error-state.tsx`, `components/retry-button.tsx`)
- [ ] 4.2 Job selection components (`components/job-card.tsx`, `components/job-list-states.tsx`)
- [ ] 4.3 Interview room components (`components/interview/` — interview-room, decision-panel, answer-area, competency-chips, done-button, early-end-dialog, interview-header, question-display, speaking-orb, thinking-indicator, welcome-screen)
- [ ] 4.4 Results components (`components/results/` — competency-score-card, evaluation-limitations, narrative-section, score-bar, transcript-turn)
- [ ] 4.5 History components (`components/history/` — empty-history, role-filter, score-trend-chart, session-card, turn-navigator)

## 5. App routes

- [ ] 5.1 Root routes (`app/page.tsx`, `app/loading.tsx`, `app/not-found.tsx`, `app/error.tsx`)
- [ ] 5.2 Interview routes (`app/interview/[sessionId]/page.tsx`, `app/interview/[sessionId]/error.tsx`, `app/interview/[sessionId]/result/page.tsx`)
- [ ] 5.3 History routes (`app/history/page.tsx`, `app/history/[sessionId]/page.tsx`, `app/history/[sessionId]/replay-loader.ts`, `app/history/[sessionId]/replay-page-state.ts`, `app/history/[sessionId]/_components/`)

## 6. Tests

- [ ] 6.1 Test fixtures (`test/fixtures.ts`)
- [ ] 6.2 All test files (hooks, lib, components, app — including `lib/contract-smoke.test.ts` already present)
- [ ] 6.3 Verify `pnpm test` (Vitest) passes

## 7. Frontend architecture docs

- [ ] 7.1 Frontend ADRs (`frontend/docs/adr/` — ADR-001 through ADR-008)

## 8. Quality gate

- [ ] 8.1 `pnpm typecheck` (tsc strict) green
- [ ] 8.2 `pnpm lint` (Biome) green
- [ ] 8.3 `pnpm knip` green
- [ ] 8.4 `pnpm test` (Vitest) green
- [ ] 8.5 `just frontend-contract-types-check` green (no drift from the contract)
- [ ] 8.6 Forbidden-words scan clean (only false positives)
- [ ] 8.7 `openspec validate --all` and `just bootstrap-check` pass
