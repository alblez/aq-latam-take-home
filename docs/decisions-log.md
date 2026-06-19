# Decisions Log — AI Interviewer Platform

## Architecture Decisions

### D1. Engine Architecture — Split Pipeline

**Decision:** Two LLM calls per turn with a deterministic policy step between.

```
Candidate answer (text)
  → [LLM Call 1: ANALYZE] Extract structured signals from the answer
  → [Pure Code: UPDATE STATE] Merge signals into rubric
  → [Pure Code: DECIDE] Deterministic policy picks next action
  → [LLM Call 2: GENERATE] Phrase the question given the chosen action
  → [Persist turn + full reasoning snapshot]
```

**Why:** The spec mandates "the model never freely decides interview flow." A single structured call conflates analysis with decision-making. The split gives true determinism — same state always produces same decision. Only question wording varies (LLM). Different temperature/prompt configs per call. The decision panel's "why" is provably deterministic (template strings from code, not LLM hallucination).

---

### D2. Live Interview Channel — Synchronous Panel First, SSE Deferred

**Decision:** First implementation returns panel state synchronously from normal HTTP routes (`start`, `turn`, `state`, and `replay`). SSE is optional polish, deferred unless time remains.

**Why:** The interview loop already waits for a backend response after each candidate answer. Stretch 1 grades deterministic controller visibility more than transport mechanism. Skipping streaming avoids Railway/CORS/proxy complexity in the first pass.

**Supersession note:** Earlier drafts named SSE as the default live channel. Backend contract decisions supersede that for first-pass implementation; an optional future `GET /api/sessions/{sessionId}/events` stream may still be added later.

---

### D3. Turn Boundary — Explicit "Done" Button

**Decision:** Candidate presses a button to signal "I'm done answering." No auto-silence-detection.

**Why:** Web Speech API silence detection is unreliable (fires too early on pauses, too late in quiet rooms). An explicit button gives clean turn boundaries, prevents mic from capturing TTS playback, and works identically in video mode. Same pattern as voice messages / walkie-talkie.

---

### D4. Follow-Up Trigger — Signal-Based

**Decision:** The analyze call returns categorical response signals. If a specific response signal can produce an answer-dependent question AND follow-up budget is not exhausted, the policy may trigger a follow-up. No numeric depth thresholds.

**Why:** Signals are categorical (easier for the model to produce reliably) and self-documenting in the decision panel. Negative signals create clarification follow-ups; positive signals create depth follow-ups. A numeric score like 0.7 vs 0.8 is fake precision from an LLM.

**Supersession note:** Follow-ups do not depend only on negative flags. They depend on any specific prior-answer signal, such as `vague_claim`, `no_evidence`, `contradiction`, `interesting_thread`, `tradeoff_mentioned`, `metric_mentioned`, `specific_tool_mentioned`, or `well_covered`.

---

### D5. Flag Format — Fixed Enum + Free-Form Detail

**Decision:** Each signal/flag includes an enum value, human-readable detail, and, when tied to a candidate answer, trigger metadata.

- `flag`: fixed enum (policy reads this via exact match)
- `detail`: free-form string (decision panel displays this for humans)
- `competencyId`: competency the signal applies to
- `triggerTurnId`: candidate turn that produced the signal, when applicable
- `answerExcerpt`: excerpt/detail that makes a follow-up visibly answer-dependent, when applicable

**Example:**

```json
{
  "flag": "vague_claim",
  "detail": "mentioned microservices without discussing tradeoffs",
  "competencyId": "competency_uuid",
  "triggerTurnId": "candidate_turn_uuid",
  "answerExcerpt": "I split the monolith into services."
}
```

**Why:** Pure free-form strings can't be reliably matched in code. Pure enum loses the context that makes the panel useful. Enum + detail gives both: reliable policy decisions AND human-readable explanations.

---

### D6. Question Pack Usage — Seed to Rephrase

**Decision:** When the controller selects a pack item, the LLM receives it as a seed + transcript context and produces a natural-sounding question covering the same ground. Not verbatim.

**Why:** Verbatim pack questions sound canned and ignore conversational context. Rephrasing preserves traceability (`turns.source_pack_item_id` links to the item for pack-seeded new-topic turns) while making the interview feel adaptive.

**Rule:** Follow-ups are NEVER from pack. Always LLM-generated from the candidate's specific answer. Pack provides openers only.

---

### D7. Replay Storage — Full Rubric Snapshot Per Turn

**Decision:** `turns.reasoning` JSONB stores the FULL rubric/panel snapshot at each interviewer turn, not just deltas. Query-critical facts remain relational columns: `turns.action`, `turns.competency_id`, and `turns.source_pack_item_id`.

**Why:** Interviews are short (6-12 interviewer turns, ~12-24KB total per session). Full snapshots make replay trivial: click turn N → render snapshot at turn N. Delta reconstruction adds complexity for negligible storage savings.

**Related terminal state:** `sessions.terminal_panel_state` stores the final `action=end` panel snapshot so replay can show why the interview ended without inserting a fake terminal turn.

---

### D8. Talk Ratio — `audio_duration_ms` Column

**Decision:** Add `audio_duration_ms` (nullable integer) and `input_mode` (`voice | text`) to candidate turns in Phase 1.

- Populated when candidate uses voice (time between mic start and Done button)
- `audio_duration_ms` is null when candidate uses text fallback
- `input_mode` distinguishes text fallback from unknown/missing audio duration
- Talk ratio: sum of candidate audio durations / total interview duration
- Fallback: text character-length ratio when audio duration unavailable

**Why:** Schema is frozen after Phase 1 (no migrations). Adding the column now costs nothing. Gives accurate talk ratio metric for Phase 7.

---

### D9. Max Follow-Ups Per Competency — 2

**Decision:** Maximum 2 follow-up questions per competency. After 2 follow-ups on the same competency, policy advances regardless of remaining flags.

**Why:** With 5-8 competencies per role, cap of 2 keeps interviews at 6-12 questions. It prevents a single competency from trapping the interview in follow-up mode while leaving room for the global minimum of 2 answer-dependent follow-ups.

---

### D10. Global Question Cap — 12

**Decision:** Maximum 12 questions per interview (hard ceiling). Minimum 6 questions and minimum 2 answer-dependent follow-ups before automatic completion. Policy prioritizes coverage breadth over depth when approaching cap.

**Why:** ~15 minutes of interview assuming ~1 min per Q+A cycle. Long enough to cover most competencies with follow-ups, short enough that a reviewer completes it.

---

### D11. LLM Failure Degradation — Tiered Fallback

**Decision:**

- **Analyze fails:** Skip analysis. No flags extracted, no state update. Policy advances to next uncovered competency (safe default). Decision panel shows "analysis unavailable this turn."
- **Generate fails (after 1 retry):** Use selected pack item text when available; otherwise use generic probe: "Can you tell me more about your experience with [competency name]?"
- **Both fail:** Serve generic probe immediately. Never stall.

Fallback mode is recorded in `turns.reasoning.generation.fallbackMode` or `failureMode`.

**Why:** A failed turn in a live voice interview feels broken. The candidate must never sit in silence wondering if the app crashed. Degrade to something reasonable, log the gap, continue.

---

### D12. Video Mode AI Representation — Pulsing CSS Orb + Text

**Decision:** AI panel shows a circle/orb that pulses (CSS animation) when SpeechSynthesis is playing, plus the question text visible simultaneously. 

```
┌─────────────────────┐
│    [Pulsing Orb]    │
│                     │
│  "Question text..." │
└─────────────────────┘
```

**Why:** Minimal implementation (~15 lines CSS + state toggle), no external assets, no audio analysis. Syncs to `speechSynthesis.onstart`/`onend` events. Candidate can listen AND read simultaneously.

---

### D13. Replay UX — Decision Panel + Step-Through

**Decision:** Replay shows the transcript AND the decision panel state at each turn. Navigation is step-through (click turns manually), not auto-play.

**Why:** Step-through is simpler to build, more useful for analysis (study any turn instantly), and the data already exists (full snapshots). Auto-play needs timing calibration and adds playback controls complexity for marginal value.

---

### D14. Main Turn Communication — Synchronous POST

**Decision:** Candidate presses Done → frontend POSTs answer with `clientTurnId`, `inputMode`, answer text, and optional audio duration → backend runs full pipeline (analyze → policy → generate, ~2-4s) → returns `question`, `panelState`, and completion/terminal fields when applicable. Frontend shows "thinking..." indicator during wait.

**Why:** Simplest coordination model. Returning panel state in the same response avoids race condition complexity. 2-4s is acceptable (real interviewers also pause between questions).

---

### D15. TTS — Browser SpeechSynthesis (Drop OpenAI TTS)

**Decision:** Use browser-native `SpeechSynthesis` for the interviewer's voice. Remove OpenAI TTS dependency entirely.

**Consequences:**
- Remove OpenAI key from credentials / `.env.example`
- Only external APIs: OpenRouter (LLM) + Neon (DB)
- Zero TTS latency (instant after POST returns)
- Lower voice quality than OpenAI TTS (OS-dependent voices), but functional across Chrome, Brave, Firefox, Safari

**Why:** Fewer moving parts → more attention on Stretch goals 1 and 2 (decision panel + question packs), which is what this take-home actually evaluates. Removes a credential, a failure point, and a latency source.

---

### D16. Simplification Accepted

**Decision:** Fewer dependencies, simpler architecture, focus engineering effort on the deterministic controller and question packs.

**Strategic reason:** The take-home test rewards observable, inspectable AI orchestration. Time saved on TTS infrastructure goes directly into making Stretch 1 and 2 excellent.

---

## Spec Changes Required

The following updates to `ai-interviewer-platform-spec.md` are needed based on these decisions:

1. **Line 29:** Replace OpenAI TTS with browser SpeechSynthesis. Remove "second provider credential" framing.
2. **Line 33 / .env.example:** Remove OpenAI key. Only OpenRouter + Neon DB URL needed.
3. **Section 3 (turns table):** Add `audio_duration_ms`, `input_mode`, `client_turn_id`, `action`, and `source_pack_item_id` columns.
4. **Phase 2:** Add synchronous decision-panel payloads, Done button for turn boundary, 12-question global cap, 2 required answer-dependent follow-ups, and 2-follow-up-per-competency cap.
5. **Phase 4:** Specify signal enum + detail + trigger metadata, full snapshot per interviewer turn in reasoning JSONB, template-string rationale from policy (not LLM), and terminal panel state on session end.
6. **Phase 5:** Clarify pack items are seeds to rephrase, follow-ups never from pack, and pack source traceability lives in `turns.source_pack_item_id`.
7. **Phase 6:** Specify pulsing CSS orb + question text, two-panel layout.
8. **Phase 7:** Specify step-through replay with decision panel, final terminal panel state, talk ratio from `audio_duration_ms`, and text-length fallback using `input_mode`.
9. **Cross-cutting:** Add tiered LLM fallback strategy.

---

## Decisions from Expand Requirements Review

### D17. `turns.reasoning` Populated from Phase 2 (Not Phase 4)

**Decision:** The controller writes reasoning (full rubric snapshot, signals/flags, policy state, trigger metadata, generation mode, and rationale) into `turns.reasoning` from Phase 2 onward, while query-critical action/target/source facts are persisted in relational turn columns. Phase 4 becomes purely a rendering task.

**Why:** The controller already produces this data in Phase 2. Writing it costs one JSON serialization per turn. Waiting until Phase 4 means retrofitting the controller AND creates a data gap (early sessions have no reasoning, breaking Phase 7 replay). This aligns with `expand_requirements.md` line 122: "Make the question-selection reasoning loggable from the start."

**Impact:** Phase 2 +30 min. Phase 4 becomes frontend-only. Phase 7 replay has full coverage from day one.

---

### D18. Follow-Ups Must Explicitly Reference Candidate's Words

**Decision:** The generate prompt for follow-up questions is explicitly instructed to quote, paraphrase, or name the specific detail from the candidate's prior answer that triggered the follow-up. A generic "tell me more" does not satisfy the follow-up requirement.

**Why:** `expand_requirements.md` line 100: "A reviewer testing your app will deliberately give a weird or specific answer to see if question seven actually references it. If your follow-up quotes or paraphrases their prior answer, the dependency is unmistakable." The follow-up must be visibly, provably dependent — not just structurally tagged as one.

---

### D19. "Ready to Start?" Welcome Screen with Begin Button

**Decision:** Between entering the Interview Room and the first question, show a welcome screen with:
- Role name
- One-line instruction: "Listen to each question, then press Done when you've finished answering."
- "Begin Interview" button (provides user gesture required for audio APIs)
- Browser detection notice (non-Chrome only): "Voice input works best in Chrome. A text fallback is always available."

Clicking Begin triggers: mic permission → first question generated → "thinking..." → TTS speaks → "your turn."

**Why:** `expand_requirements.md` line 106: "The first ten seconds decide their impression. If the mic permission prompt is confusing, if there is dead air before the first question, if they do not know when to speak, the 'minimal friction' criterion is already lost." The Begin button eliminates dead-air confusion and satisfies browser audio API requirements.

---

### D20. Browser Detection Notice (Chrome Recommendation)

**Decision:** Two places:
1. **Runtime (in-app):** On the welcome screen, detect non-Chrome/Chromium. Show notice only to non-Chrome users. Chrome users see nothing (zero friction on happy path).
2. **README:** State supported browsers and Chrome recommendation for voice input.

**Why:** The reviewer's browser is unknown. Non-Chrome STT failure without warning feels like a bug. Warning + text fallback feels like defensive engineering. README covers the reviewer who reads docs before opening the app.

---

### D21. Backend Database Shape — Six-Table Competency Spine

**Decision:** Use a six-table competency-spine schema: `jobs`, `competencies`, `question_pack_items`, `sessions`, `turns`, and `session_competency_scores`.

**Details:**
- Use 3NF + JSONB hybrid design.
- Do not add event-sourcing/event tables.
- Do not add a separate `question_packs` table.
- `question_pack_items` hang off competencies, not jobs.
- Behavioral/technical category lives on `competencies`; pack items inherit category from their parent competency.
- Query-critical controller facts are columns: `sessions.completion_reason`, `turns.action`, `turns.source_pack_item_id`, `turns.input_mode`, and `turns.client_turn_id`.
- Full snapshots/narratives stay JSONB: `sessions.controller_config`, `sessions.terminal_panel_state`, `sessions.evaluation_narrative`, `turns.reasoning`, and `session_competency_scores.evidence`.

**Why:** This supports deterministic controller traceability, question-pack source traceability, replay, and analytics without event-sourcing overbuild.

---

### D22. Evaluation Scores — Integer 1-10

**Decision:** Per-competency scores are integer `SMALLINT` values from 1 to 10. `assessed=false` means `score IS NULL`; `assessed=true` requires a score.

**Why:** Whole-number scoring is easier to validate, explain, and display. Overall score is derived from assessed competency score rows, not stored as an authoritative JSON field.

---

### D23. Anonymous Owner Transport — `X-Owner-Id`

**Decision:** Owner-scoped API routes use required `X-Owner-Id: <uuid>` header. Do not send `ownerId` in request body, query string, or URL path.

**Why:** Header scoping avoids mixing owner identity with filters or request payloads. Backend stores the value in `sessions.owner_id`, checks it on every session-scoped route, and returns `404 session_not_found` for wrong-owner access to avoid leaking another owner's session existence.

---

### D24. Turn Idempotency and Minimal Recovery — `clientTurnId`

**Decision:** Candidate answer submissions include frontend-generated `clientTurnId`. Candidate turns persist it in `turns.client_turn_id`, with uniqueness per session. Repeated `/turn` requests with the same client turn id must not insert duplicate candidate turns.

**Recovery rule:** If a duplicate client turn id already has a following interviewer turn, return the current/latest session state. If it exists without a following interviewer turn, continue the missing analyze → policy → generate pipeline from the persisted candidate turn. `/state` reports `needsRecovery = true` when the latest persisted turn is a candidate answer with no following interviewer turn.

**Why:** Browser retries and double-clicks must not duplicate transcript turns or corrupt follow-up counts. Minimal recovery satisfies reload/crash behavior without background workers or event sourcing.

---

### D25. Transaction Boundaries — No DB Transaction During Model Calls

**Decision:** Do not hold a database transaction open while calling the model gateway. Persist candidate turns in a short transaction, commit, run analyze/policy/generate outside the transaction, then persist the interviewer turn in another short transaction.

**Why:** OpenRouter latency should not extend Postgres transaction lifetime or locks. Short transactions make retry/recovery states explicit and keep the home-test backend simple.

---

### D26. Evaluation Completion — Synchronous Persistence

**Decision:** When a session completes or ends early, generate and validate evaluation synchronously, then persist one `session_competency_scores` row per job competency plus `sessions.evaluation_narrative`, `sessions.terminal_panel_state`, terminal status, completion reason, and completed timestamp in a short transaction.

**Why:** No background worker is needed for the home test. The frontend can immediately navigate to results after receiving `evaluationReady = true`.

---

### D27. JSONB Validation Before Persistence

**Decision:** JSONB payloads are flexible in Postgres but strict in backend code. Validate `sessions.controller_config`, `turns.reasoning`, `sessions.terminal_panel_state`, `sessions.evaluation_narrative`, and `session_competency_scores.evidence` before writing them.

**Why:** The schema intentionally stores replay, panel, narrative, evidence, and controller snapshots as JSONB read-whole payloads. Backend validation preserves shape guarantees without over-normalizing those payloads into many tables.
