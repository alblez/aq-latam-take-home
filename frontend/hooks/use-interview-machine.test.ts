import { describe, expect, it } from "vitest";
import {
  type InterviewAction,
  type InterviewMachineState,
  interviewReducer,
} from "@/hooks/use-interview-machine";
import {
  makeCompetencyStatus,
  makePanelState,
  makeTerminalPanelState,
  makeTurn,
} from "@/test/fixtures";
import type { PanelState } from "@/types/turn";

// --- Contract-shaped fixtures (D-14) ---

const mockCompetencies = [makeCompetencyStatus()];

const mockPanelState = makePanelState();

const mockTerminalPanelState = makeTerminalPanelState();

const mockTurns = [
  makeTurn({
    id: "t1",
    role: "interviewer",
    turnIndex: 0,
    competencyId: "c1",
    content: "Tell me about system design",
  }),
];

function makeState(overrides: Partial<InterviewMachineState> = {}): InterviewMachineState {
  return {
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
    ...overrides,
  };
}

describe("interviewReducer", () => {
  describe("initial state", () => {
    it("has evaluationReady false and terminalPanelState null", () => {
      const state = makeState();
      expect(state.evaluationReady).toBe(false);
      expect(state.terminalPanelState).toBeNull();
    });
  });

  describe("BEGIN", () => {
    it("transitions welcome → thinking", () => {
      const state = makeState({ phase: "welcome" });
      const result = interviewReducer(state, { type: "BEGIN", sessionId: "s1" });
      expect(result.phase).toBe("thinking");
      expect(result.sessionId).toBe("s1");
      expect(result.error).toBeNull();
    });

    it("ignores BEGIN if not in welcome phase", () => {
      const state = makeState({ phase: "thinking" });
      const result = interviewReducer(state, { type: "BEGIN", sessionId: "s1" });
      expect(result).toBe(state);
    });
  });

  describe("QUESTION_RECEIVED", () => {
    it("transitions thinking → speaking with question data", () => {
      const state = makeState({ phase: "thinking" });
      const action: InterviewAction = {
        type: "QUESTION_RECEIVED",
        question: "Tell me about X",
        turnIndex: 0,
        panelState: mockPanelState,
        competencies: mockCompetencies,
        turns: mockTurns,
        jobTitle: "Backend Engineer",
      };
      const result = interviewReducer(state, action);
      expect(result.phase).toBe("speaking");
      expect(result.currentQuestion).toBe("Tell me about X");
      expect(result.turnIndex).toBe(0);
      expect(result.competencies).toBe(mockCompetencies);
      expect(result.jobTitle).toBe("Backend Engineer");
    });

    it("ignores if not in thinking phase", () => {
      const state = makeState({ phase: "speaking" });
      const action: InterviewAction = {
        type: "QUESTION_RECEIVED",
        question: "Q",
        turnIndex: 0,
        panelState: mockPanelState,
        competencies: mockCompetencies,
        turns: mockTurns,
      };
      const result = interviewReducer(state, action);
      expect(result).toBe(state);
    });
  });

  describe("TTS_FINISHED", () => {
    it("transitions speaking → answering", () => {
      const state = makeState({ phase: "speaking" });
      const result = interviewReducer(state, { type: "TTS_FINISHED" });
      expect(result.phase).toBe("answering");
    });

    it("ignores if not speaking", () => {
      const state = makeState({ phase: "answering" });
      const result = interviewReducer(state, { type: "TTS_FINISHED" });
      expect(result).toBe(state);
    });
  });

  describe("SUBMIT_ANSWER", () => {
    it("transitions answering → thinking", () => {
      const state = makeState({ phase: "answering", error: "stale error" });
      const result = interviewReducer(state, { type: "SUBMIT_ANSWER" });
      expect(result.phase).toBe("thinking");
      expect(result.error).toBeNull();
    });

    it("ignores if not answering", () => {
      const state = makeState({ phase: "thinking" });
      const result = interviewReducer(state, { type: "SUBMIT_ANSWER" });
      expect(result).toBe(state);
    });
  });

  describe("INTERVIEW_ENDED", () => {
    it("sets evaluationReady true and terminalPanelState when provided", () => {
      const state = makeState({ phase: "answering", panelState: mockPanelState });
      const result = interviewReducer(state, {
        type: "INTERVIEW_ENDED",
        evaluationReady: true,
        terminalPanelState: mockTerminalPanelState,
      });
      expect(result.phase).toBe("ended");
      expect(result.evaluationReady).toBe(true);
      expect(result.terminalPanelState).toBe(mockTerminalPanelState);
    });

    it("sets evaluationReady false and terminalPanelState null (hold path)", () => {
      const state = makeState({ phase: "answering", panelState: mockPanelState });
      const result = interviewReducer(state, {
        type: "INTERVIEW_ENDED",
        evaluationReady: false,
        terminalPanelState: null,
      });
      expect(result.phase).toBe("ended");
      expect(result.evaluationReady).toBe(false);
      expect(result.terminalPanelState).toBeNull();
    });

    it("preserves existing panel state via panelState fallback", () => {
      const state = makeState({ phase: "answering", panelState: mockPanelState });
      const result = interviewReducer(state, {
        type: "INTERVIEW_ENDED",
        evaluationReady: true,
        terminalPanelState: mockTerminalPanelState,
      });
      expect(result.panelState).toBe(mockPanelState);
    });

    it("updates panelState when explicitly provided", () => {
      const state = makeState({ phase: "answering", panelState: mockPanelState });
      const newPanel: PanelState = { ...mockPanelState, rationale: "Final" };
      const result = interviewReducer(state, {
        type: "INTERVIEW_ENDED",
        evaluationReady: true,
        terminalPanelState: mockTerminalPanelState,
        panelState: newPanel,
        competencies: mockCompetencies,
      });
      expect(result.panelState).toBe(newPanel);
    });
  });

  describe("ERROR", () => {
    it("sets error phase and message", () => {
      const state = makeState({ phase: "thinking" });
      const result = interviewReducer(state, { type: "ERROR", message: "Network failed" });
      expect(result.phase).toBe("error");
      expect(result.error).toBe("Network failed");
    });
  });

  describe("RESUME", () => {
    it("transitions welcome → speaking with full session state", () => {
      const state = makeState({ phase: "welcome" });
      const result = interviewReducer(state, {
        type: "RESUME",
        sessionId: "s1",
        question: "Where were we?",
        turnIndex: 3,
        panelState: mockPanelState,
        competencies: mockCompetencies,
        turns: mockTurns,
        jobTitle: "Frontend",
      });
      expect(result.phase).toBe("speaking");
      expect(result.sessionId).toBe("s1");
      expect(result.currentQuestion).toBe("Where were we?");
      expect(result.jobTitle).toBe("Frontend");
    });

    it("ignores if not in welcome phase", () => {
      const state = makeState({ phase: "thinking" });
      const result = interviewReducer(state, {
        type: "RESUME",
        sessionId: "s1",
        question: "Q",
        turnIndex: 0,
        panelState: mockPanelState,
        competencies: mockCompetencies,
        turns: mockTurns,
        jobTitle: "X",
      });
      expect(result).toBe(state);
    });
  });

  describe("RESET", () => {
    it("returns initial state", () => {
      const state = makeState({ phase: "ended", sessionId: "s1", error: "old" });
      const result = interviewReducer(state, { type: "RESET" });
      expect(result.phase).toBe("welcome");
      expect(result.sessionId).toBeNull();
      expect(result.error).toBeNull();
      expect(result.evaluationReady).toBe(false);
      expect(result.terminalPanelState).toBeNull();
    });
  });
});

// --- Recovery pure helper tests ---

import {
  decideRecovery,
  decideSubmitOutcome,
  isLandedResubmit,
} from "@/hooks/use-interview-machine";
import type { PendingTurn } from "@/lib/pending-turn";

const mockPendingTurn: PendingTurn = {
  clientTurnId: "ct-123",
  answerText: "My answer",
  inputMode: "text",
  audioDurationMs: undefined,
};

describe("decideRecovery", () => {
  it("returns resubmit when needsRecovery and pending exists", () => {
    const result = decideRecovery({ needsRecovery: true, hasTurns: true }, mockPendingTurn);
    expect(result).toEqual({ action: "resubmit", payload: mockPendingTurn });
  });

  it("returns resume when needsRecovery but no pending", () => {
    const result = decideRecovery({ needsRecovery: true, hasTurns: true }, null);
    expect(result).toEqual({ action: "resume" });
  });

  it("returns resume when no needsRecovery and turns present", () => {
    const result = decideRecovery({ needsRecovery: false, hasTurns: true }, mockPendingTurn);
    expect(result).toEqual({ action: "resume" });
  });

  it("returns idle when no needsRecovery and no turns", () => {
    const result = decideRecovery({ needsRecovery: false, hasTurns: false }, null);
    expect(result).toEqual({ action: "idle" });
  });
});

describe("isLandedResubmit", () => {
  it("returns true for ok result", () => {
    expect(isLandedResubmit({ status: "ok" as const })).toBe(true);
  });

  it("returns true for 409 turn_already_submitted", () => {
    expect(isLandedResubmit({ status: "error" as const, code: "turn_already_submitted" })).toBe(
      true,
    );
  });

  it("returns false for other error codes", () => {
    expect(isLandedResubmit({ status: "error" as const, code: "model_unavailable" })).toBe(false);
  });

  it("returns false for error without code", () => {
    expect(isLandedResubmit({ status: "error" as const })).toBe(false);
  });
});

// --- Safe-retry submit decision helper (RETRY-01) ---

describe("decideSubmitOutcome", () => {
  it('returns "landed" for ok result', () => {
    expect(decideSubmitOutcome({ status: "ok" as const }, false)).toBe("landed");
  });

  it('returns "landed" for 409 turn_already_submitted on first attempt', () => {
    expect(
      decideSubmitOutcome({ status: "error" as const, code: "turn_already_submitted" }, false),
    ).toBe("landed");
  });

  it('returns "landed" for 409 turn_already_submitted after retry', () => {
    expect(
      decideSubmitOutcome({ status: "error" as const, code: "turn_already_submitted" }, true),
    ).toBe("landed");
  });

  it('returns "retry" for first model_unavailable failure', () => {
    expect(
      decideSubmitOutcome({ status: "error" as const, code: "model_unavailable" }, false),
    ).toBe("retry");
  });

  it('returns "error" for model_unavailable when already retried once', () => {
    expect(decideSubmitOutcome({ status: "error" as const, code: "model_unavailable" }, true)).toBe(
      "error",
    );
  });

  it('returns "error" for non-transient validation_error', () => {
    expect(decideSubmitOutcome({ status: "error" as const, code: "validation_error" }, false)).toBe(
      "error",
    );
  });

  it('returns "error" for network/unknown error with no code', () => {
    expect(decideSubmitOutcome({ status: "error" as const, code: null }, false)).toBe("error");
  });
});
