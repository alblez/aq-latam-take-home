# AI Interviewer Platform, Project Specification

## 1. Project Definition

Build a hosted web application where a user selects a job and completes a voice-driven AI interview. The candidate speaks to the screen, the AI asks dynamic questions that adapt to prior answers, and at the end the app shows a full transcript and a structured evaluation.

"Done" means the full feature set below is deployed to a public URL, the code lives in one public GitHub repository, and every phase has passed its acceptance criteria from a fresh browser against the deployed environment, not localhost.

Deployment target: one public URL for the frontend, one reachable backend, one managed database. Share an access password in the README if the host requires one.

---

## 2. Decisions and Constraints

These are settled. An executing agent must not re-decide them.

- **Stack.** Next.js frontend, FastAPI (Python) backend, two separate deployable apps communicating over HTTP/JSON. A separate Python backend is deliberate: the role is Python-infrastructure-heavy and the brief names "desktop (Python)", so a pure Next.js submission would under-demonstrate the half of the job that is Python. The frontend owns presentation and the voice loop in the browser. The backend owns the interview controller, model calls, evaluation, and persistence.
- **Frontend host.** Vercel.
- **Backend host.** Railway (free account). Chosen over a raw EC2 box on purpose: Railway provides automatic HTTPS and Git-push deploys, removing TLS, reverse-proxy, and process-manager work that demonstrates nothing the test grades. It can support optional future streams, but the first implementation does not depend on SSE/WebSocket infrastructure.
- **Cross-origin.** Frontend and backend are on different domains. The backend must be served over HTTPS (a Vercel page calling a plain-HTTP backend is blocked as mixed content) and must set CORS to allow the Vercel origin. All API request/response traffic, including decision-panel payloads, crosses origins.
- **Database.** PostgreSQL on Neon. Schema in Section 3.
- **No authentication.** No user table, no login, no passwords. Sessions are scoped to an anonymous owner ID, a UUID generated on first visit and stored in `localStorage`. Owner-scoped routes receive it through the required `X-Owner-Id` header, persist it in `sessions.owner_id`, and use it to filter history reads.
- **Model gateway.** OpenRouter, reached through a single model gateway adapter: one module exposing one interface (roughly `generate(messages, schema) -> validated object`). Callers never see OpenRouter, the model name, or retry logic. The model name is a configuration value, never hard-coded. The adapter is a thin boundary, not a multi-provider abstraction. The brief requires "model not hard-coded", not "support every provider", so one clean interface is the correct scope. Over-abstraction here reads as poor scope judgment.
- **Voice, STT.** Browser speech-to-text for candidate answers. A visible text-input fallback must exist and be reachable mid-interview without reload, since browser STT support and accent handling are uneven and a reviewer must always be able to complete the interview.
- **Voice, TTS.** Browser-native `SpeechSynthesis` for the interviewer's questions. Free, instant (no API latency), and supported across Chrome, Brave, Firefox, and Safari. Voice quality is OS-dependent but functional. This is a deliberate simplification: fewer moving parts means more engineering attention on Stretch goals 1 and 2, which is what this take-home actually evaluates. No second provider credential needed.
- **Interview controller owns the rubric.** The interview is driven by a deterministic controller in the backend. The controller owns the competency model, tracks coverage, tracks gaps, and decides which competency to probe next and whether to follow up. The LLM only phrases the next question and generates follow-up wording. The model never freely decides interview flow. This is the architecturally central decision and it shapes Phase 2, not only Phase 4.
- **Competency model.** Each role is defined by a set of competencies. This one object is the spine of the app: it grounds question selection (Phase 2), the structured evaluation (Phase 3), the decision panel (Phase 4), the question packs (Phase 5), and the coverage analytics (Phase 7). It is a first-class entity in the schema, designed once, before Phase 4. See Section 4.
- **Evaluation storage.** Per-competency scores are stored in a normalized table (queried by Stretch 4). The free-text evaluation narrative, strengths, concerns, and any early-end note, is stored as JSONB, since it is read and written as a whole and never queried field by field. See Section 3 for the 3NF-plus-JSONB division.
- **Secrets.** No API keys in the repository or git history. Configuration through environment variables, with a committed `.env.example`. Only two credentials: the OpenRouter key and the Neon database URL.
- **Decision-panel delivery.** First implementation returns decision panel state synchronously from normal HTTP routes (`start`, `turn`, `state`, and `replay`). SSE remains optional polish for later; deterministic controller visibility matters more than streaming transport for the home test.
- **Turn boundary.** Explicit "Done" button. The candidate presses a button to signal they are finished answering. No auto-silence-detection. Web Speech API silence detection is unreliable (fires too early on pauses, too late in quiet rooms). The button gives clean turn boundaries, prevents the mic from capturing TTS playback, and works identically in video mode.
- **Turn communication.** Synchronous POST. Candidate presses Done, frontend POSTs `clientTurnId`, `answerText`, `inputMode`, and nullable `audioDurationMs`; backend runs the full pipeline (analyze, policy, generate, ~2-4s) and returns `question`, `panelState`, completion fields, and terminal state when applicable. Frontend shows a "thinking..." indicator during the wait.
- **Follow-up trigger.** Signal-based, not threshold-based. The analyze call returns categorical response signals. If a specific signal can produce an answer-dependent question AND the follow-up budget for that competency is not exhausted, the policy may trigger a follow-up. Negative signals create clarification follow-ups; positive signals create depth follow-ups. No numeric depth thresholds.
- **Flag/signal format.** Fixed enum + free-form detail + trigger metadata. Each flag is `{ "flag": "<enum_value>", "detail": "<free-form explanation>", "competencyId": "<uuid>", "triggerTurnId": "<candidate_turn_uuid>", "answerExcerpt": "<candidate words>" }` when tied to a candidate answer. The enum (e.g. `vague_claim`, `no_evidence`, `interesting_thread`, `contradiction`, `metric_mentioned`) is what the policy reads via exact match. The detail and answer excerpt are what the decision panel displays for humans.
- **Follow-up caps.** Maximum 2 follow-ups per competency. After 2 follow-ups on the same competency, the policy advances regardless of remaining flags. This keeps interviews at 6-12 questions with 5-8 competencies per role.
- **Global question cap.** 12 questions maximum per interview. Minimum 6 questions and minimum 2 answer-dependent follow-ups before automatic completion. The policy prioritizes coverage breadth over depth when approaching the cap: if competencies remain uncovered near question 10, skip optional follow-ups and cover them.
- **LLM failure degradation.** Tiered fallback per call. Analyze fails: skip analysis, no flags, policy advances to next uncovered competency, decision panel shows "analysis unavailable this turn." Generate fails after 1 retry: use pack item text verbatim (if available), otherwise a generic probe ("Can you tell me more about your experience with [competency name]?"). Both fail: serve generic probe immediately. Never stall.
- **Question pack usage.** Pack items are seeds to rephrase, not verbatim questions. The LLM receives the pack item text plus transcript context and produces a natural-sounding question covering the same ground. Follow-ups are NEVER from pack; always LLM-generated from the candidate's specific answer signal. Traceability is preserved via `turns.source_pack_item_id`; fallback/non-pack new-topic turns may leave it null and record fallback context in `turns.reasoning.generation`.

---

## 3. Data Model

The schema is built once in Phase 1 and designed to absorb every later phase. An unused nullable column is acceptable. A mid-project migration is not.

**Design principle: 3NF plus JSONB.** Normalize what the database must reason about, things you query, filter, join, constrain, count, or aggregate. Use JSONB for structured data that the application reads and writes as a whole unit. This yields genuine third normal form where it earns points and avoids over-normalization, such as shredding replay snapshots or free-text strengths into rows.

All six tables below exist from Phase 1. Columns filled by later phases are nullable from the start, so Phases 3 through 7 are additions, never migrations. The schema is a six-table competency-spine model, not an event-sourcing model.

### Normalized tables

**jobs**
- `id` (primary key)
- `title`
- `description`
- `sort_order` (deterministic display order)
- `created_at`

**competencies** (the spine, see Section 4)
- `id` (primary key)
- `job_id` (foreign key to jobs)
- `name` (e.g. "System design", "Conflict handling")
- `category` (behavioral, technical)
- `description`
- `sort_order`
- `created_at`

A job has many competencies. This is the single object that questions, the rubric, the evaluation, the question packs, and coverage analytics all reference.

**question_pack_items** (populated/seeded for Phase 5; the table exists from Phase 1)
- `id` (primary key)
- `competency_id` (foreign key to competencies)
- `prompt_text` (the bankable opener seed)
- `sort_order`
- `created_at`

Question pack items hang off competencies, not directly off jobs. They do not have an independent category column; behavioral/technical category is inherited from the parent competency. This keeps Stretch 1 and Stretch 2 sharing one model rather than two overlapping ones.

**sessions**
- `id` (primary key)
- `job_id` (foreign key to jobs)
- `owner_id` (anonymous UUID from `X-Owner-Id`, Phase 7 history scoping; present from Phase 1)
- `status` (in_progress, completed, ended_early)
- `completion_reason` (all_competencies_covered, question_cap, ended_early)
- `model_name` (nullable model provenance)
- `started_at`, `completed_at`, `updated_at`
- `controller_config` (JSONB policy snapshot)
- `terminal_panel_state` (nullable JSONB final decision-panel snapshot)
- `evaluation_narrative` (nullable JSONB, Phase 3: strengths, concerns, overall summary, early-end note)

**turns**
- `id` (primary key)
- `session_id` (foreign key to sessions)
- `client_turn_id` (nullable UUID for candidate-turn retry/idempotency)
- `turn_index` (ordering)
- `role` (interviewer, candidate)
- `competency_id` (foreign key to competencies: which competency this turn was probing)
- `content` (question or answer text)
- `input_mode` (voice, text; candidate turns only)
- `audio_duration_ms` (nullable integer: milliseconds of recording, populated when candidate uses voice. Enables talk-ratio metric in Phase 7.)
- `action` (new_topic, follow_up, end; interviewer turns only)
- `source_pack_item_id` (nullable foreign key to question_pack_items; set for pack-seeded new-topic turns, null for follow-ups and fallback/non-pack cases)
- `reasoning` (nullable JSONB, populated on interviewer turns from Phase 2)
- `created_at`

**session_competency_scores** (populated in Phase 3; table exists from Phase 1)
- `id` (primary key)
- `session_id` (foreign key to sessions)
- `competency_id` (foreign key to competencies)
- `assessed` (boolean: false means the interview ended before this competency was probed/scored)
- `score` (nullable integer 1-10; only meaningful when assessed is true)
- `notes` (nullable short text)
- `evidence` (nullable JSONB score explanation/evidence)
- `created_at`

One row per session per competency. This is the normalized join that makes Stretch 4 analytics, coverage and score trend, straightforward SQL, and it grounds the Phase 3 evaluation in the competency model. `assessed=false` requires `score=null`; `assessed=true` requires an integer score from 1 to 10.

### JSONB columns and why

- `sessions.controller_config`: policy snapshot read as a whole: `policyVersion`, `minQuestions`, `minFollowUps`, `maxQuestions`, and `maxFollowUpsPerCompetency`.
- `sessions.terminal_panel_state`: final decision-panel snapshot for replay/display. Lifecycle truth remains scalar in `status`, `completion_reason`, and timestamps.
- `sessions.evaluation_narrative`: free-text strengths, concerns, summary, verdict, early-end/model-failure notes; read and written whole. Numeric scores live in `session_competency_scores`.
- `turns.reasoning`: full per-interviewer-turn panel/replay snapshot: rubric snapshot, flags/signals, policy state, trigger metadata, deterministic rationale, generation mode, and failure mode. Action, target competency, and source pack item are authoritative columns.
- `session_competency_scores.evidence`: score evidence/quotes/signals read as a whole. Queryable score and coverage facts remain columns.

The numeric, queryable part of the evaluation lives in `session_competency_scores` (normalized). The narrative part lives in `sessions.evaluation_narrative` (JSONB). Per-turn and terminal panel snapshots stay JSONB because replay reads them as whole snapshots.

---

## 4. The Competency Model, the Spine of the App

The competency model is the single most important abstraction in this project. It is not a feature of one phase. It is the object five of the seven phases depend on, and the spec calls it out separately so it is designed once, deliberately, in Phase 1, rather than improvised three times.

A role is defined by a set of competencies. Each competency has a name, a category (behavioral or technical), and a description. Every part of the app reads from this one model:

- **Phase 2, question selection.** The controller walks the role's competencies, tracks which are covered, and picks the next one to probe. Questions are grounded in the role because they are grounded in its competencies.
- **Phase 2, progress display.** The competency chips shown to the candidate are this model, rendered.
- **Phase 3, evaluation.** The structured evaluation is the competency model, scored. `session_competency_scores` has one row per competency. The overall score aggregates them.
- **Phase 4, decision panel.** Covered competencies, in-progress competencies, and gaps are this model, surfaced live.
- **Phase 5, question packs.** Pack items hang off competencies, so the question bank and the rubric are one model, not two.
- **Phase 7, analytics.** Coverage and score trend are aggregations over `session_competency_scores`.

The design consequence: build the competency model first, in Phase 1, even though the decision panel (Phase 4) and question packs (Phase 5) ship later. The Phase 1 schema includes `competencies`, `question_pack_items`, and `session_competency_scores` so that later phases add data and behavior, never tables. Treating Stretch 1's rubric and Stretch 2's question bank as two separate things would produce two overlapping representations of "what this role should be probed on." One competency model prevents that.

This is also the through-line for grading. The take-home test rewards engineering the controller around the LLM rather than treating the model as a black box. A competency model the controller owns, that grounds questions, evaluation, and analytics in one inspectable object, is exactly that signal.

---

## 5. Phase Breakdown

Phases 1 to 3 deliver the core requirements. Phases 4 to 7 deliver the stretch goals in the brief's stated order. Each phase ends with an atomic, labeled commit.

### Phase 1, Foundation

**Goal.** A skeleton that boots and deploys.

**Scope.**
- Repository structure with the Next.js app (Vercel) and the FastAPI backend (Railway).
- Neon PostgreSQL database provisioned, full schema from Section 3 applied via migration. All six tables exist now, including the ones later phases populate.
- Seed data: at least 3 jobs, each with a title and short description, and for each job a set of competencies in the `competencies` table. The competency model exists from day one because five later phases depend on it.
- Backend health endpoint.
- CORS configured on the backend to allow the Vercel frontend origin.
- Frontend deployed to its Vercel URL, backend deployed to Railway over HTTPS and reachable from the frontend.

**Acceptance criteria.**
- The Vercel URL loads without error in a fresh browser with no cache.
- The landing view renders the seeded job list, read from the database, not hard-coded.
- The backend health endpoint returns a success response over HTTPS from the deployed Railway environment.
- A request from the Vercel origin to the Railway backend succeeds, no CORS or mixed-content error.
- All six schema tables and their columns from Section 3 exist, confirmed by inspection.
- Each seeded job has competency rows attached.
- No secrets in the repository. `.env.example` is present and complete, listing the OpenRouter key and the database URL.

### Phase 2, Core Interview Loop

**Goal.** A working voice interview, driven by a deterministic controller, that adapts and persists.

**Scope.**
- Clicking a job opens an Interview Room for that role.
- A "Ready to start?" welcome screen before the interview begins. Shows the role name, a brief description of what will happen, a one-line instruction ("Listen to each question, then press Done when you've finished answering"), and a "Begin Interview" button. On non-Chrome/Chromium browsers, show a notice: "Voice input works best in Chrome. A text fallback is always available." On Chrome, show nothing. The Begin button provides the user gesture required by browsers for audio APIs and eliminates dead-air confusion.
- Clicking "Begin Interview" triggers: mic permission request (if voice mode), then the first question is generated via POST to the backend, "thinking..." indicator shown, question arrives, TTS speaks it, UI transitions to "your turn" state. No dead air between room entry and first question.
- A deterministic interview controller in the backend. The controller owns the competency model for the selected role, tracks which competencies are covered, and decides which competency to probe next. The split pipeline runs two LLM calls per turn with a deterministic policy step between: (1) Analyze — extract structured signals from the candidate's answer as validated JSON, (2) Policy — pure code updates state and decides the next action, (3) Generate — LLM phrases the question given the chosen action and target competency. The model never decides flow.
- Microphone capture and browser speech-to-text for candidate answers.
- Browser `SpeechSynthesis` for the interviewer's spoken questions. Triggered immediately on receiving question text from the backend. The orb/UI indicator syncs to `speechSynthesis.onstart` and `onend` events.
- A visible text-input fallback, reachable mid-interview without reload.
- An explicit "Done" button for the candidate to signal they have finished answering. No auto-silence-detection. The button gives clean turn boundaries and prevents the mic from capturing TTS playback.
- Synchronous decision-panel state updates from backend responses. `start`, `turn`, `state`, and `replay` return the relevant panel state; SSE is deferred optional polish.
- An interview flow of at least 6 questions, every question grounded in the selected role through its competencies. Global cap of 12 questions. Minimum 2 answer-dependent follow-ups before automatic completion. Maximum 2 follow-ups per competency.
- At least 2 follow-up questions whose content depends on the candidate's prior answer. Follow-ups are triggered by specific response signals from the analyze call (signal-based, not threshold-based, and not only negative flags). The controller decides when to follow up on an answer versus advance to the next planned competency. The generate call for follow-ups must be explicitly instructed to reference the candidate's specific words — quoting, paraphrasing, or naming the detail that triggered the follow-up. A generic "tell me more" does not satisfy the follow-up requirement. The dependency must be unmistakable to a reviewer and persisted via `turns.reasoning.trigger`/`flags`.
- Conversation state held server-side. Each turn is written to the database as it happens, with `competency_id` set to the competency being probed, `input_mode` and `audio_duration_ms` recorded for candidate answers, `client_turn_id` recorded for candidate-turn retry/idempotency, `action` and `source_pack_item_id` recorded for interviewer turns, and `reasoning` populated with the full rubric snapshot, signals, policy state, trigger metadata, generation mode, and rationale. Logging reasoning from Phase 2 (not Phase 4) means the decision panel is purely a rendering task and all sessions have reasoning data for replay.
- Turn-taking state in the UI: a clear indication of whether the interviewer is speaking or it is the candidate's turn. States: "thinking" (waiting for backend), "speaking" (TTS active), "your turn" (mic active or text input ready).
- A progress display built from competencies, not a question count. The Interview Room shows the role's competencies as chips that fill in as each is covered (covered, in progress, not yet reached). The question cap stays invisible.
- An early-end control. The user can choose to end the interview before all competencies are covered. Before the interview ends, a confirmation step names the competencies not yet covered so the user understands what they are leaving unassessed. On confirm, the session is marked `ended_early`.
- Interview end condition: all competencies covered, OR the 12-question cap reached, OR the user confirms an early end. Automatic completion additionally requires at least 6 questions and at least 2 answer-dependent follow-ups. User-confirmed early end writes `status = ended_early`, `completion_reason = ended_early`, and `terminal_panel_state`.
- LLM failure handling: tiered fallback. Analyze fails — skip analysis, advance to next competency. Generate fails after 1 retry — use pack item verbatim or generic probe. Never stall.
- Voice-loop edge handling: a candidate who is silent, who gives a one-word answer, or who starts speaking while the interviewer is still talking, does not break the loop.
- Session resumption: if the candidate reloads mid-interview, the session resumes from its persisted turns rather than starting over or breaking.

**Acceptance criteria.**
- From the deployed URL, a fresh browser can select a job and reach the Interview Room.
- The candidate can answer by voice, and can switch to text input mid-interview without reloading.
- The interview asks at least 6 role-grounded questions and stops at or before 12.
- At least 2 questions visibly reference a specific detail from a prior answer. Test: give a distinctive answer early, confirm a later question paraphrases or names that detail.
- The competency chips update as the interview progresses and never show a frozen or misleading state.
- The early-end control works, and the confirmation step lists the uncovered competencies by name before the interview ends.
- An interview that runs to completion ends when competencies are covered or the 12-question cap is hit, subject to the minimum 6 questions and minimum 2 answer-dependent follow-ups guards, not on a fixed hard-coded count.
- Reloading the page mid-interview resumes the same session from its stored turns.
- After the interview ends, the session row (with the correct status) and the matching ordered turn rows exist in the database. `audio_duration_ms` is populated for voice-answered turns.
- The interview does not stall on a slow or failed model call, nor on silence or an interruption. Failures degrade gracefully via the tiered fallback.
- The Done button cleanly terminates recording and triggers the turn submission.
- SpeechSynthesis speaks the interviewer's questions audibly, and the UI reflects speaking state.

### Phase 3, Evaluation and Transcript

**Goal.** Close the loop with a structured result grounded in the competency model.

**Scope.**
- On interview end (complete or early), generate a structured evaluation.
- The evaluation is grounded in the competencies, not free-floating. For each competency, write a row to `session_competency_scores`: `assessed` true with an integer 1-10 score for competencies that were probed/scored, `assessed` false with `score = null` for competencies the interview never reached (the early-end case), plus nullable evidence JSONB when available.
- The overall score is computed over assessed competencies only. A candidate is never scored down for competencies left unassessed by an early end.
- The free-text narrative, strengths, concerns, and an early-end note when applicable, is generated and stored in `sessions.evaluation_narrative` as JSONB.
- Validate the model's evaluation output against a schema. Handle malformed output without crashing.
- Display the full transcript as ordered question and answer turns.
- Display the evaluation: per-competency scores, overall score, strengths, concerns, and, for an early-ended session, which competencies were not assessed.

**Acceptance criteria.**
- Ending an interview produces `session_competency_scores` rows covering every competency of the role.
- For a fully completed interview, all competencies are marked assessed.
- For an early-ended interview, the competencies not reached are marked `assessed = false` and excluded from the overall score, and the evaluation states the interview ended early.
- The free-text narrative is valid JSONB and contains strengths and concerns.
- A malformed model response is caught and handled. The app shows no raw error or crash.
- The transcript view renders every turn in the correct order.

### Phase 4, Stretch 1, Decision Panel

**Goal.** Make the interviewer's control flow inspectable.

**Scope.**
- A decision panel showing the interview controller's current state: competencies detected as covered, competencies in progress, competencies still as gaps. This is the same competency model the controller already tracks from Phase 2, now surfaced.
- For each question, surface why it was chosen: which competency gap it targets, or which prior answer triggered a follow-up. The "why" comes from the deterministic policy function (template strings from code), not from LLM-generated rationale. This makes the panel provably deterministic.
- The `turns.reasoning` JSONB field is already populated per interviewer turn since Phase 2. Phase 4 does not add the logging — it adds the UI that reads it. This phase is purely a rendering task over existing data.
- The panel consumes panel state returned by `start`, `turn`, and `state` responses. SSE may be added later but is not required for the first implementation.
- Display: competency coverage grid (chips colored by status), signals/flags detected this turn with their detail text and trigger excerpt when present, follow-up budget state, generation/fallback mode, and the policy rationale string.

**Acceptance criteria.**
- The panel updates as the interview progresses from backend-returned panel state, reflecting competency coverage in real time from the user's perspective.
- Each question is traceable to a stated competency gap, flag, or prior answer. The rationale is a deterministic template string, not LLM prose.
- The `reasoning` field is populated for every interviewer turn with a full rubric snapshot and is inspectable in the database.
- Question selection is visibly deterministic and controller-driven, not an unexplained model choice.
- Flags display both the enum label and the free-form detail.

### Phase 5, Stretch 2, Job-Specific Question Packs

**Goal.** Constrain generation with structured question banks tied to competencies.

**Scope.**
- Populate `question_pack_items` with a bank of opener seed questions per competency. Behavioral/technical category lives on `competencies`, so pack items inherit category from their parent competency. Because pack items hang off competencies, the question pack and the rubric are one shared model, not two overlapping ones.
- The controller selects a pack item for the competency it is probing. The pack item is a seed to rephrase: the LLM receives the pack item text plus transcript context and produces a natural-sounding question covering the same ground. Pack items are never used verbatim.
- Follow-up questions are NEVER drawn from the pack. Follow-ups are always LLM-generated from the candidate's specific answer. The pack provides openers only.
- Record the originating pack item id in `turns.source_pack_item_id` so each pack-seeded new-topic question is traceable to its source. Null for follow-ups and fallback/non-pack cases.

**Acceptance criteria.**
- Each role's competencies have question pack items, with behavioral and technical coverage coming from `competencies.category`.
- An interview question drawn from a pack item is traceable to that item via `turns.source_pack_item_id`.
- Questions adapted from pack items sound natural and conversational, not canned or verbatim.
- Follow-up questions are still generated fresh and still depend on prior answers. They never come from the pack.

### Phase 6, Stretch 3, Video Mode

**Goal.** A video-call interface layer over the existing voice interview.

**Scope.**
- Optional camera input via `getUserMedia`. Camera feed is local only, never sent to the server. Zero backend changes.
- A two-panel video-call layout for the Interview Room: AI panel on the left (pulsing CSS orb + question text), candidate camera feed on the right.
- The AI panel shows a circle/orb that pulses (CSS animation) when `SpeechSynthesis` is playing, plus the current question text visible simultaneously. The candidate can listen AND read.
- Pre-interview toggle: "Enable camera?" prompt. Mid-interview on/off button for the camera. Camera denial or toggle-off falls back gracefully to voice-only layout.
- The interview stays voice-driven. Video is interface only and changes no interview logic or backend behavior.

**Acceptance criteria.**
- The user can enable or skip camera input before the interview starts.
- With camera enabled, the Interview Room renders in the two-panel video-call layout with the pulsing orb and question text on the AI side.
- The orb animates in sync with SpeechSynthesis playback (pulses when speaking, static when silent).
- Camera can be toggled off mid-interview without disrupting the interview flow.
- Camera permission denial is handled gracefully (falls back to voice-only layout, no crash).
- The interview flow, question logic, and persistence are unchanged from Phase 2.

### Phase 7, Stretch 4, Replay and Analytics

**Goal.** A session history experience scoped to the visitor.

**Scope.**
- An anonymous owner UUID generated on first visit, stored in `localStorage`, sent through the required `X-Owner-Id` header on owner-scoped routes, saved as `sessions.owner_id`, and never returned in API responses.
- A session history page listing the current browser's past interviews. Session cards show: role, date, duration, overall score, competency coverage percentage.
- Filter by role/job using the stable job id.
- Replay of a past interview: step-through navigation (click through turns manually, not auto-play). Each turn renders the transcript AND the decision panel state at that turn (from the full rubric snapshot stored in `turns.reasoning`), and the final state from `sessions.terminal_panel_state`. The candidate can study the AI's reasoning at each step.
- Per-session metrics:
  - **Duration:** `completed_at - started_at`.
  - **Talk ratio:** Sum of candidate `audio_duration_ms` / total interview duration. Falls back to text character-length ratio for turns where `audio_duration_ms` is null (text fallback was used).
  - **Competency coverage:** `COUNT(assessed=true) / COUNT(*)` from `session_competency_scores`.
  - **Score trend:** Overall score (average of assessed competency scores) plotted across sessions. Respects the role/job filter: when filtered to one job, the trend is a meaningful comparison.

**Acceptance criteria.**
- A first-time visitor receives an owner id, and that id persists across reloads.
- The history page lists only sessions created by the current browser.
- Filtering by job id narrows the list correctly.
- Replay reconstructs a past interview from its stored turns with step-through navigation.
- Replay shows the decision panel state (rubric snapshot, flags, rationale) at each turn alongside the transcript.
- Metrics compute and display per session, with coverage and score derived from `session_competency_scores`.
- Talk ratio uses `audio_duration_ms` when available and text-length fallback when not.
- Score trend chart respects the active role/job filter.
- An empty history shows a deliberate empty state, not a blank screen or an error.

---

## 6. Cross-Cutting Requirements

These apply to every phase and are checked at every verify step.

- All project code in one public GitHub repository.
- The app deployed and reachable on public URLs: the Next.js frontend on Vercel, the FastAPI backend on Railway. Access password shared in the README if used.
- The backend is served over HTTPS, and CORS allows the Vercel origin. A mixed-content or CORS failure fails the phase.
- Railway free tier may cold-start an idle service. Account for a possible first-request delay, and note it in the README so a reviewer's first hit is not mistaken for a broken app.
- No API keys or secrets in the repository or git history. `.env.example` committed and current, covering the OpenRouter key and the Neon database URL.
- Atomic, labeled commits. Each phase, and each task within a phase, gets its own commit so the build sequence is legible in the log.
- The model name is read from configuration through the model gateway adapter, never hard-coded.
- README includes: what the app does, how to run it locally, what was built, what was cut and why, and known limitations.
- Every phase verified from a fresh browser against the deployed environment, not localhost.
- **Empty and transitional states.** Every component that depends on data which may be absent, empty, or loading renders one of three explicit states: loading, empty, or populated. No implicit blank state. Empty states contain text explaining why and what will fill them (e.g., "Evaluation will appear when the interview ends"). Loading states are visually distinct from empty states. No component throws or renders undefined when its data source is null, empty array, or pending. This applies to: the interview room before the first question, competency chips before coverage, the decision panel at turn 1, the transcript before any turns, the evaluation before interview ends, and the history page with zero sessions.

---

## 8. Build Order Summary

| Phase | Deliverable | Category |
|-------|-------------|----------|
| 1 | Foundation, schema, deploy skeleton | Core |
| 2 | Voice interview loop, dynamic follow-ups, persistence | Core |
| 3 | Structured evaluation, transcript | Core |
| 4 | Decision panel | Stretch 1 |
| 5 | Question packs | Stretch 2 |
| 6 | Video mode | Stretch 3 |
| 7 | Replay and analytics | Stretch 4 |

The phase number is the priority. Build in this order, commit in this order, and the git log will show the reviewer that the brief's "implement in order" instruction was followed.
