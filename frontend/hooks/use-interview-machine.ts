"use client";

import { useCallback, useReducer, useState } from "react";
import type { ApiResult } from "@/lib/api/client";
import type { InputMode } from "@/lib/pending-turn";
import type { CompetencyStatus } from "@/types/competency";
import type { InterviewPhase, SessionStatus, SubmitAnswerResponse } from "@/types/session";
import type { PanelState, TerminalPanelState, Turn } from "@/types/turn";

// Re-export for consumers
export type { InterviewPhase };

// --- State ---
export interface InterviewMachineState {
  phase: InterviewPhase;
  sessionId: string | null;
  jobTitle: string | null;
  currentQuestion: string | null;
  turnIndex: number;
  turns: Turn[];
  competencies: CompetencyStatus[];
  panelState: PanelState | null;
  evaluationReady: boolean;
  terminalPanelState: TerminalPanelState | null;
  error: string | null;
}

// --- Actions ---
export type InterviewAction =
  | { type: "BEGIN"; sessionId: string }
  | {
      type: "QUESTION_RECEIVED";
      question: string;
      turnIndex: number;
      panelState: PanelState;
      competencies: CompetencyStatus[];
      turns: Turn[];
      jobTitle?: string;
    }
  | { type: "TTS_FINISHED" }
  | { type: "SUBMIT_ANSWER" }
  | {
      type: "INTERVIEW_ENDED";
      evaluationReady: boolean;
      terminalPanelState: TerminalPanelState | null;
      panelState?: PanelState | null;
      competencies?: CompetencyStatus[];
    }
  | { type: "ERROR"; message: string }
  | { type: "RESET" }
  | { type: "SET_JOB_TITLE"; jobTitle: string }
  | {
      type: "RESUME";
      sessionId: string;
      question: string | null;
      turnIndex: number;
      panelState: PanelState;
      competencies: CompetencyStatus[];
      turns: Turn[];
      jobTitle: string;
    };

// --- Initial state ---
const initialState: InterviewMachineState = {
  phase: "welcome",
  sessionId: null,
  jobTitle: null,
  currentQuestion: null,
  turnIndex: -1,
  turns: [],
  competencies: [],
  panelState: null,
  evaluationReady: false,
  terminalPanelState: null,
  error: null,
};

// --- Reducer (pure, testable) ---
export function interviewReducer(
  state: InterviewMachineState,
  action: InterviewAction,
): InterviewMachineState {
  switch (action.type) {
    case "BEGIN":
      if (state.phase !== "welcome") return state;
      return { ...state, phase: "thinking", sessionId: action.sessionId, error: null };

    case "QUESTION_RECEIVED":
      if (state.phase !== "thinking") return state;
      return {
        ...state,
        phase: "speaking",
        currentQuestion: action.question,
        turnIndex: action.turnIndex,
        panelState: action.panelState,
        competencies: action.competencies,
        turns: action.turns,
        jobTitle: action.jobTitle ?? state.jobTitle,
      };

    case "TTS_FINISHED":
      if (state.phase !== "speaking") return state;
      return { ...state, phase: "answering" };

    case "SUBMIT_ANSWER":
      if (state.phase !== "answering" && state.phase !== "error") return state;
      return { ...state, phase: "thinking", error: null };

    case "INTERVIEW_ENDED":
      return {
        ...state,
        phase: "ended",
        panelState: action.panelState ?? state.panelState,
        competencies: action.competencies ?? state.competencies,
        evaluationReady: action.evaluationReady,
        terminalPanelState: action.terminalPanelState,
      };

    case "ERROR":
      return { ...state, phase: "error", error: action.message };

    case "RESET":
      return initialState;

    case "SET_JOB_TITLE":
      return { ...state, jobTitle: action.jobTitle };

    case "RESUME":
      if (state.phase !== "welcome") return state;
      return {
        ...state,
        phase: "speaking",
        sessionId: action.sessionId,
        jobTitle: action.jobTitle,
        currentQuestion: action.question,
        turnIndex: action.turnIndex,
        panelState: action.panelState,
        competencies: action.competencies,
        turns: action.turns,
        error: null,
      };

    default:
      return state;
  }
}

// --- API helpers (extracted to keep hook under complexity budget) ---

// --- Pure recovery helpers (exported for testability) ---

import type { PendingTurn } from "@/lib/pending-turn";

export type RecoveryDecision =
  | { action: "resubmit"; payload: PendingTurn }
  | { action: "resume" }
  | { action: "idle" };

/** Decide recovery path from session state + localStorage pending-turn. */
export function decideRecovery(
  state: { needsRecovery: boolean; hasTurns: boolean },
  pending: PendingTurn | null,
): RecoveryDecision {
  if (state.needsRecovery && pending) {
    return { action: "resubmit", payload: pending };
  }
  if (state.needsRecovery || state.hasTurns) {
    return { action: "resume" };
  }
  return { action: "idle" };
}

/** True when the resubmit landed (ok OR 409 turn_already_submitted). */
export function isLandedResubmit(result: {
  status: "ok" | "error";
  code?: string | null;
}): boolean {
  if (result.status === "ok") return true;
  return result.status === "error" && result.code === "turn_already_submitted";
}

export type SubmitOutcome = "landed" | "retry" | "error";

/**
 * Decide the safe-retry path for a direct submit result (RETRY-01).
 *
 * - ok → landed
 * - turn_already_submitted → landed (409 duplicate; replay collapses to no-op)
 * - model_unavailable on first attempt → retry exactly once
 * - model_unavailable after retry, or any other error → error
 */
export function decideSubmitOutcome(
  result: { status: "ok" | "error"; code?: string | null },
  alreadyRetried: boolean,
): SubmitOutcome {
  if (result.status === "ok") return "landed";
  if (result.code === "turn_already_submitted") return "landed";
  if (result.code === "model_unavailable" && !alreadyRetried) return "retry";
  return "error";
}

async function performBegin(
  sessionId: string,
  dispatch: React.ActionDispatch<[action: InterviewAction]>,
): Promise<void> {
  const { startSession } = await import("@/lib/api/sessions");
  const result = await startSession(sessionId);
  if (result.status === "error") throw new Error(result.message);
  dispatch({
    type: "QUESTION_RECEIVED",
    question: result.data.question,
    turnIndex: result.data.turnIndex,
    turns: result.data.turns,
    competencies: result.data.competencies,
    panelState: result.data.panelState,
    jobTitle: "jobTitle" in result.data ? result.data.jobTitle : undefined,
  });
}

async function dispatchFromSubmitResult(
  result: ApiResult<SubmitAnswerResponse>,
  sessionId: string,
  dispatch: React.ActionDispatch<[action: InterviewAction]>,
): Promise<void> {
  if (result.status === "ok") {
    if (result.data.isComplete) {
      dispatch({
        type: "INTERVIEW_ENDED",
        evaluationReady: result.data.evaluationReady,
        terminalPanelState: result.data.terminalPanelState,
        competencies: result.data.competencies,
      });
      return;
    }

    if (result.data.question) {
      dispatch({
        type: "QUESTION_RECEIVED",
        question: result.data.question,
        turnIndex: result.data.turnIndex,
        turns: result.data.turns,
        competencies: result.data.competencies,
        panelState: result.data.panelState,
      });
    }
    return;
  }

  // 409 turn_already_submitted: the turn landed but the response was lost.
  // Re-fetch session state and dispatch from it so the interview continues.
  const { getSessionState } = await import("@/lib/api/sessions");
  const fresh = await getSessionState(sessionId);
  if (fresh.status === "ok") dispatchFromState(fresh.data, sessionId, dispatch);
}

async function performSubmitAnswer(
  sessionId: string,
  body: {
    clientTurnId: string;
    answerText: string;
    inputMode: InputMode;
    audioDurationMs?: number | null;
  },
  dispatch: React.ActionDispatch<[action: InterviewAction]>,
  setRetrying: (value: boolean) => void,
): Promise<void> {
  const { submitAnswer } = await import("@/lib/api/sessions");

  async function trySubmit(alreadyRetried: boolean): Promise<void> {
    const result = await submitAnswer(sessionId, body);
    const outcome = decideSubmitOutcome(result, alreadyRetried);

    if (outcome === "landed") {
      await dispatchFromSubmitResult(result, sessionId, dispatch);
      return;
    }

    if (outcome === "retry") {
      setRetrying(true);
      try {
        return await trySubmit(true);
      } finally {
        setRetrying(false);
      }
    }

    if (result.status === "error") throw new Error(result.message);
    throw new Error("Failed to submit answer");
  }

  return trySubmit(false);
}

async function performEndInterview(
  sessionId: string,
  dispatch: React.ActionDispatch<[action: InterviewAction]>,
): Promise<void> {
  const { endSessionEarly } = await import("@/lib/api/sessions");
  const result = await endSessionEarly(sessionId);
  if (result.status === "error") throw new Error(result.message);
  dispatch({
    type: "INTERVIEW_ENDED",
    evaluationReady: result.data.evaluationReady,
    terminalPanelState: result.data.terminalPanelState,
  });
}

async function performResumeSession(
  sessionId: string,
  dispatch: React.ActionDispatch<[action: InterviewAction]>,
  cancellation: { cancelled: boolean },
): Promise<void> {
  const { getSessionState, submitAnswer } = await import("@/lib/api/sessions");
  const { readPendingTurn, clearPendingTurn } = await import("@/lib/pending-turn");

  const result = await getSessionState(sessionId);
  if (cancellation.cancelled) return;
  if (result.status !== "ok") return;

  const decision = decideRecovery(
    { needsRecovery: result.data.needsRecovery, hasTurns: result.data.turns.length > 0 },
    readPendingTurn(sessionId),
  );

  if (decision.action === "resubmit") {
    const resubmitResult = await submitAnswer(sessionId, decision.payload);
    if (cancellation.cancelled) return;

    if (isLandedResubmit(resubmitResult)) {
      clearPendingTurn(sessionId);
      // Re-pull fresh state after the resubmit landed
      const freshResult = await getSessionState(sessionId);
      if (cancellation.cancelled) return;
      if (freshResult.status !== "ok") return;
      dispatchFromState(freshResult.data, sessionId, dispatch);
    } else {
      dispatch({
        type: "ERROR",
        message:
          resubmitResult.status === "error" ? resubmitResult.message : "Recovery resubmit failed",
      });
    }
    return;
  }

  if (decision.action === "resume") {
    dispatchFromState(result.data, sessionId, dispatch);
    return;
  }

  // idle — set job title only
  if (result.data.jobTitle) {
    dispatch({ type: "SET_JOB_TITLE", jobTitle: result.data.jobTitle });
  }
}

/** Dispatch RESUME or INTERVIEW_ENDED from a SessionStateResponse. */
function dispatchFromState(
  data: {
    status: SessionStatus;
    turns: Turn[];
    currentQuestion: string | null;
    turnIndex: number;
    panelState: PanelState;
    competencies: CompetencyStatus[];
    jobTitle: string;
    terminalPanelState: TerminalPanelState | null;
  },
  sessionId: string,
  dispatch: React.ActionDispatch<[action: InterviewAction]>,
): void {
  if (data.status === "completed" || data.status === "ended_early") {
    dispatch({
      type: "INTERVIEW_ENDED",
      evaluationReady: true,
      terminalPanelState: data.terminalPanelState,
      panelState: data.panelState,
      competencies: data.competencies,
    });
    return;
  }
  dispatch({
    type: "RESUME",
    sessionId,
    question: data.currentQuestion,
    turnIndex: data.turnIndex,
    panelState: data.panelState,
    competencies: data.competencies,
    turns: data.turns,
    jobTitle: data.jobTitle,
  });
}

// --- Hook ---

export function useInterviewMachine() {
  const [state, dispatch] = useReducer(interviewReducer, initialState);
  const [retrying, setRetrying] = useState(false);

  const begin = useCallback(async (sessionId: string) => {
    dispatch({ type: "BEGIN", sessionId });
    try {
      await performBegin(sessionId, dispatch);
    } catch (err) {
      dispatch({
        type: "ERROR",
        message: err instanceof Error ? err.message : "Failed to start session",
      });
    }
  }, []);

  const submitAnswer = useCallback(
    async (body: {
      clientTurnId: string;
      answerText: string;
      inputMode: InputMode;
      audioDurationMs?: number | null;
    }): Promise<boolean> => {
      // Allow submit from "answering" (normal) or "error" (manual retry after
      // retry-exhaustion: the hook dispatched ERROR but the room keeps the
      // answer visible and offers a Retry answer action).
      if ((state.phase !== "answering" && state.phase !== "error") || !state.sessionId)
        return false;
      dispatch({ type: "SUBMIT_ANSWER" });
      try {
        await performSubmitAnswer(state.sessionId, body, dispatch, setRetrying);
        // Reaching here means the POST landed (performSubmitAnswer throws on error),
        // so the caller may safely clear the crash-recovery pending-turn record.
        return true;
      } catch (err) {
        dispatch({
          type: "ERROR",
          message: err instanceof Error ? err.message : "Failed to submit answer",
        });
        return false;
      }
    },
    [state.phase, state.sessionId],
  );

  const endInterview = useCallback(async () => {
    if (!state.sessionId) return;
    if (state.phase === "answering") {
      dispatch({ type: "SUBMIT_ANSWER" });
    }
    try {
      await performEndInterview(state.sessionId, dispatch);
    } catch (err) {
      dispatch({
        type: "ERROR",
        message: err instanceof Error ? err.message : "Failed to end interview",
      });
    }
  }, [state.sessionId, state.phase]);

  const transitionToAnswering = useCallback(() => {
    dispatch({ type: "TTS_FINISHED" });
  }, []);

  const resumeSession = useCallback(
    async (sessionId: string, cancellation: { cancelled: boolean }) => {
      await performResumeSession(sessionId, dispatch, cancellation);
    },
    [],
  );

  return {
    state,
    retrying,
    begin,
    submitAnswer,
    endInterview,
    transitionToAnswering,
    resumeSession,
  };
}
