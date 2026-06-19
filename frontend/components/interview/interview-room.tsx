"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { MicStatus } from "@/components/interview/answer-area";
import { AnswerArea } from "@/components/interview/answer-area";
import { DecisionPanel, PanelRenderer } from "@/components/interview/decision-panel";
import { DoneButton } from "@/components/interview/done-button";
import { EarlyEndDialog } from "@/components/interview/early-end-dialog";
import { InterviewHeader } from "@/components/interview/interview-header";
import { QuestionDisplay } from "@/components/interview/question-display";
import { SpeakingOrb } from "@/components/interview/speaking-orb";
import { ThinkingIndicator } from "@/components/interview/thinking-indicator";
import { WelcomeScreen } from "@/components/interview/welcome-screen";
import { ErrorState } from "@/components/shared/error-state";
import { Button } from "@/components/ui/button";
import { useAnswerInputController } from "@/hooks/use-answer-input-controller";
import type { InterviewPhase } from "@/hooks/use-interview-machine";
import { useInterviewMachine } from "@/hooks/use-interview-machine";
import { useEnsureOwnerId } from "@/hooks/use-owner-id";
import { useSpeechRecognition } from "@/hooks/use-speech-recognition";
import { useSpeechSynthesis } from "@/hooks/use-speech-synthesis";
import { clearPendingTurn, readPendingTurn, writePendingTurn } from "@/lib/pending-turn";
import { cn } from "@/lib/utils";

// --- Sub-components ---

/** Retry-exhausted notice: shows when auto-retry fails, keeps answer preserved. */
function RetryExhaustedNotice({
  onRetry,
  retrying,
}: Readonly<{ onRetry: () => void; retrying: boolean }>) {
  return (
    <div className="flex w-full max-w-[720px] flex-col items-center gap-4">
      <div role="status" aria-live="polite" className="text-sm text-foreground-muted">
        We could not save this answer yet. Your text is still here.
      </div>
      <Button
        variant="primary"
        size="lg"
        onClick={onRetry}
        disabled={retrying}
        className="min-w-[180px] px-8"
      >
        Retry answer
      </Button>
    </div>
  );
}

// --- Module-level constants ---

const ORB_STATE_MAP: Record<InterviewPhase, "active" | "pulse" | "static"> = {
  welcome: "static",
  thinking: "pulse",
  speaking: "active",
  answering: "static",
  ended: "static",
  error: "static",
};

// --- Component ---

type InterviewRoomProps = Readonly<{
  sessionId: string;
}>;

export function InterviewRoom({ sessionId }: InterviewRoomProps) {
  const router = useRouter();
  const mainRef = useRef<HTMLElement>(null);
  const [showEndDialog, setShowEndDialog] = useState(false);
  const [isPanelOpen, setIsPanelOpen] = useState(true);
  const [retryExhausted, setRetryExhausted] = useState(false);

  useEnsureOwnerId();

  // Core interview state machine
  const {
    state: machineState,
    retrying,
    begin,
    submitAnswer: machineSubmitAnswer,
    endInterview,
    transitionToAnswering,
    resumeSession,
  } = useInterviewMachine();

  const phase = machineState.phase;
  const currentQuestion = machineState.currentQuestion;
  const competencies = machineState.competencies;
  const panelState = machineState.panelState;
  const evaluationReady = machineState.evaluationReady;
  const terminalPanelState = machineState.terminalPanelState;
  const error = machineState.error;
  const jobTitle = machineState.jobTitle ?? "Interview";

  // Pending-turn ref: holds the clientTurnId generated once per Done press (D-05)
  const pendingClientTurnIdRef = useRef<string>("");

  // Speech recognition (STT — optional Chrome enhancement for live preview)
  const {
    isListening,
    transcript,
    interimTranscript,
    startListening,
    stopListening,
    resetTranscript,
    isSupported: isSTTSupported,
    errorType,
    hasEverRecognized,
  } = useSpeechRecognition();

  // Derive mic status from STT error state
  const micStatus: MicStatus = useMemo(() => {
    if (!isSTTSupported) return "browser-unsupported";
    if (errorType === "not-allowed") return "permission-denied";
    if (errorType === "audio-capture") return "no-hardware";
    if (errorType === "network") return "network-error";
    if (errorType === "transient" && !hasEverRecognized) return "no-speech-detected";
    if (errorType === "transient" && hasEverRecognized) return "mic-lost";
    return "ok";
  }, [isSTTSupported, errorType, hasEverRecognized]);

  // Voice available = STT mic status only (Pitfall 1 — never from MediaRecorder support)
  const isVoiceAvailable = micStatus === "ok";

  // Wrapped submitAnswer for the text-path controller (SESS-03/04, D-05):
  // Reads the once-generated clientTurnId from ref, determines inputMode, persists pending-turn.
  const submitAnswerWrapped = useCallback(
    async (content: string, audioDurationMs?: number) => {
      const clientTurnId = pendingClientTurnIdRef.current;
      const inputMode: "voice" | "text" = audioDurationMs === undefined ? "text" : "voice";
      const pending = { clientTurnId, answerText: content, inputMode, audioDurationMs };
      writePendingTurn(sessionId, pending);
      const ok = await machineSubmitAnswer(pending);
      // Only clear the crash-recovery record when the POST actually landed;
      // otherwise the answer stays re-submittable on reload (WR-04).
      if (ok) {
        clearPendingTurn(sessionId);
        setRetryExhausted(false);
      } else {
        // Submit failed after auto-retry — mark exhaustion so the room shows
        // the manual Retry answer affordance instead of the generic error state.
        setRetryExhausted(true);
      }
    },
    [sessionId, machineSubmitAnswer],
  );

  // Manual retry handler: resubmits the same pending-turn record (same
  // clientTurnId, same answer text) without generating a new id.
  const handleRetryAnswer = useCallback(async () => {
    const pending = readPendingTurn(sessionId);
    if (!pending) return;
    setRetryExhausted(false);
    const ok = await machineSubmitAnswer(pending);
    if (ok) clearPendingTurn(sessionId);
    else setRetryExhausted(true);
  }, [sessionId, machineSubmitAnswer]);

  // Answer input controller (text state, edit mode, text-path submission)
  const {
    answerText,
    setAnswerText,
    isEditing,
    textareaRef,
    handleToggleEdit,
    handleRetryVoice,
    handleDone: handleTextDone,
    isDoneDisabled,
  } = useAnswerInputController({
    phase,
    transcript,
    interimTranscript,
    isVoiceAvailable,
    startListening,
    stopListening,
    resetTranscript,
    submitAnswer: submitAnswerWrapped,
  });

  // Speech synthesis (TTS)
  const { speak, cancel: cancelSpeech } = useSpeechSynthesis();

  // --- Derived render booleans ---
  const orbState = ORB_STATE_MAP[phase];
  const hasStarted = phase !== "welcome";
  const isActiveInterview = phase !== "welcome" && phase !== "ended";

  // --- State transition handlers ---

  const handleBegin = useCallback(async () => {
    await begin(sessionId);
  }, [sessionId, begin]);

  // Unified Done handler: delegates to controller text path
  const handleDone = useCallback(async () => {
    // Generate clientTurnId ONCE per logical answer (D-05)
    const clientTurnId = crypto.randomUUID();
    pendingClientTurnIdRef.current = clientTurnId;

    // Delegate to controller (wrapper reads pendingClientTurnIdRef)
    handleTextDone();
  }, [handleTextDone]);

  // Handle end interview
  const handleEndInterview = useCallback(async () => {
    setShowEndDialog(false);
    cancelSpeech();
    stopListening();
    await endInterview();
  }, [endInterview, cancelSpeech, stopListening]);

  // --- Effects ---

  // When we get a new question and enter "speaking" state, speak it
  useEffect(() => {
    if (phase === "speaking" && currentQuestion) {
      speak(currentQuestion, () => {
        transitionToAnswering();
        startListening();
      });
    }
  }, [phase, currentQuestion, speak, startListening, transitionToAnswering]);

  // Focus management on state transitions
  useEffect(() => {
    if (phase === "answering") {
      textareaRef.current?.focus();
    } else if (phase === "ended") {
      mainRef.current?.focus();
    }
  }, [phase, textareaRef]);

  // Restart STT when tab returns from background (optional Chrome enhancement)
  useEffect(() => {
    const handleVisibility = () => {
      const shouldRestart =
        document.visibilityState === "visible" &&
        phase === "answering" &&
        !isListening &&
        !isEditing &&
        micStatus === "ok";
      if (shouldRestart) {
        startListening();
      }
    };
    document.addEventListener("visibilitychange", handleVisibility);
    return () => document.removeEventListener("visibilitychange", handleVisibility);
  }, [phase, isListening, isEditing, micStatus, startListening]);

  // Navigate to results only when evaluation is ready (D-01/D-03)
  useEffect(() => {
    if (phase === "ended" && evaluationReady) {
      router.push(`/interview/${sessionId}/result`);
    }
  }, [phase, evaluationReady, sessionId, router]);

  // Restore answer text from pending-turn when retry is exhausted.
  // The controller's handleDone clears answerText immediately (before the
  // async submit resolves), so we pull it back from localStorage.
  useEffect(() => {
    if (!retryExhausted) return;
    const pending = readPendingTurn(sessionId);
    if (pending?.answerText) {
      setAnswerText(pending.answerText);
    }
  }, [retryExhausted, sessionId, setAnswerText]);

  // Global Cmd/Ctrl+Enter shortcut for Done
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter" && phase === "answering") {
        e.preventDefault();
        handleDone();
      }
    }
    globalThis.addEventListener("keydown", handleKeyDown);
    return () => globalThis.removeEventListener("keydown", handleKeyDown);
  }, [phase, handleDone]);

  // Session resumption: check for in-progress session on mount
  useEffect(() => {
    if (phase !== "welcome") return;
    const cancellation = { cancelled: false };
    resumeSession(sessionId, cancellation);
    return () => {
      cancellation.cancelled = true;
    };
  }, [sessionId, phase, resumeSession]);

  // Uncovered competencies for early end dialog
  const uncoveredCompetencies = competencies
    .filter((c) => c.status !== "covered")
    .map((c) => c.name);

  // --- Error state ---
  // When retryExhausted is true, the submit failed after auto-retry but the
  // answer is still available — show the retry UI instead of the fatal error.
  if (error && !retryExhausted) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-background px-4">
        <ErrorState
          title="Interview Error"
          message={error}
          onRetry={() => globalThis.location.reload()}
        />
      </div>
    );
  }

  return (
    <div className="relative flex min-h-dvh flex-col bg-background">
      {/* Header — visible once started (including during ended redirect) */}
      {hasStarted && (
        <InterviewHeader
          jobTitle={jobTitle}
          competencies={competencies}
          onEndInterview={() => setShowEndDialog(true)}
          state={phase}
        />
      )}

      {/* Main content area */}
      <main
        ref={mainRef}
        id="main-content"
        tabIndex={-1}
        className="flex flex-1 flex-col items-center justify-center px-4 py-8"
      >
        {/* Welcome state */}
        {phase === "welcome" && (
          <WelcomeScreen jobTitle={jobTitle} onBegin={handleBegin} isLoading={false} />
        )}

        {/* Active interview states */}
        {isActiveInterview && (
          <div
            className={cn(
              "flex w-full max-w-[720px] flex-col items-center",
              phase === "answering" ? "gap-4" : "gap-8",
            )}
          >
            {/* Orb — hidden in answering state (mic indicator takes over) */}
            {phase !== "answering" && <SpeakingOrb state={orbState} size="default" />}

            {/* Thinking indicator */}
            <ThinkingIndicator isVisible={phase === "thinking"} />

            {/* Auto-retry status (visible during bounded retry) */}
            {retrying && (
              <div role="status" aria-live="polite" className="text-sm text-foreground-muted">
                Saving answer. Retrying once with the same answer.
              </div>
            )}

            {/* Question display */}
            <QuestionDisplay
              question={currentQuestion}
              isVisible={phase === "speaking" || phase === "answering"}
            />

            {/* Answer area (visible during answering) */}
            {phase === "answering" && (
              <div className="w-full space-y-4">
                <AnswerArea
                  textareaRef={textareaRef}
                  value={answerText}
                  onChange={(val) => setAnswerText(val)}
                  interimTranscript={interimTranscript}
                  isListening={isListening}
                  isEditing={isEditing}
                  isVoiceAvailable={isVoiceAvailable}
                  onToggleEdit={handleToggleEdit}
                  onRetryVoice={handleRetryVoice}
                  micStatus={micStatus}
                  onSubmitRequest={handleDone}
                  disabled={false}
                />
                <div className="flex justify-center">
                  <DoneButton onClick={handleDone} disabled={isDoneDisabled || retrying} />
                </div>
              </div>
            )}
          </div>
        )}

        {/* Ended state: terminal panel or hold screen */}
        {phase === "ended" && (
          <div className="flex w-full max-w-[720px] flex-col items-center gap-6">
            {evaluationReady ? (
              <>
                <div className="text-2xl font-semibold tracking-tight">Interview complete</div>
                {terminalPanelState && (
                  <div className="w-full rounded-lg border border-border bg-surface">
                    <PanelRenderer
                      panelState={terminalPanelState}
                      competencies={competencies}
                      mode="replay"
                    />
                  </div>
                )}
                <p className="text-sm text-foreground-muted">Redirecting to your results...</p>
              </>
            ) : (
              <div className="flex flex-col items-center gap-4 text-center">
                <div className="size-8 animate-spin rounded-full border-2 border-surface border-t-accent" />
                <div className="text-2xl font-semibold tracking-tight">Preparing your results</div>
                <p className="text-sm text-foreground-muted">
                  Your evaluation is being generated...
                </p>
              </div>
            )}
          </div>
        )}

        {/* Retry-exhausted state: answer preserved, manual retry available */}
        {retryExhausted && <RetryExhaustedNotice onRetry={handleRetryAnswer} retrying={retrying} />}
      </main>

      {/* Decision panel */}
      {isActiveInterview && (
        <DecisionPanel
          panelState={panelState}
          competencies={competencies}
          isOpen={isPanelOpen}
          onToggle={() => setIsPanelOpen(!isPanelOpen)}
        />
      )}

      {/* Early end dialog */}
      <EarlyEndDialog
        open={showEndDialog}
        onOpenChange={setShowEndDialog}
        uncoveredCompetencies={uncoveredCompetencies}
        onConfirm={handleEndInterview}
      />
    </div>
  );
}
