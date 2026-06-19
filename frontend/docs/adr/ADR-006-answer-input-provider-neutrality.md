# ADR-006: Answer Input Provider Neutrality

## Decision

Frontend interview flow treats **answer text** as canonical input. The STT method (Web Speech preview or text fallback) is an answer producer — not the answer itself. The state machine uses a generic `answering` phase, not an STT-coupled `listening` phase.

## Context

- Current Web Speech API (`webkitSpeechRecognition`) fails permanently in Brave with `network` error (brave/brave-browser#3725).
- The interview turn submission API is `submitAnswer(answerText, audioDurationMs?)` — it accepts text regardless of how that text was produced.
- Phase 15 removed the cross-browser upload-based STT path (superseded); voice input now uses browser Web Speech only.

## Consequences

- State machine phase is `answering` (replaces hard-coded `listening`).
- Answer mode is a substate: `text | speech-preview`.
- `text` is first-class, always available. `speech-preview` is an optional Chrome enhancement via Web Speech.
- `submitAnswer(answerText, audioDurationMs?)` remains stable.
- Text fallback is first-class, not a backup. It must be polished, accessible, keyboard-navigable.
- Web Speech API provides live interim preview while speaking. The browser may use a vendor server engine for recognition — "browser-local" means no app/backend upload, not guaranteed local processing.
- Browser detection notice (D20) uses soft language: voice is optional, text always works.
