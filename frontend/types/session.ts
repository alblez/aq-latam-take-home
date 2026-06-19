/**
 * Interview state machine phases.
 * "answering" (provider-neutral) replaces "listening" (STT-coupled).
 */
export type InterviewPhase = "welcome" | "thinking" | "speaking" | "answering" | "ended" | "error";

// --- Pure aliases into generated contract (D-14) ---

import type { components } from "@/types/api/contract";

export type Session = components["schemas"]["Session"];
export type SessionStatus = components["schemas"]["SessionStatus"];
export type SessionSummary = components["schemas"]["SessionSummary"];
export type SessionDetail = components["schemas"]["SessionDetail"];

// --- Service response aliases (D-12) ---

export type StartSessionResponse = components["schemas"]["StartSessionResponse"];
export type SubmitAnswerRequest = components["schemas"]["SubmitAnswerRequest"];
export type SubmitAnswerResponse = components["schemas"]["SubmitAnswerResponse"];
export type SessionStateResponse = components["schemas"]["SessionStateResponse"];
export type EndSessionEarlyResponse = components["schemas"]["EndSessionEarlyResponse"];
