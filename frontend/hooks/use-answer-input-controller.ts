"use client";

import { type RefObject, useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { InterviewPhase } from "@/hooks/use-interview-machine";

// --- Pure helpers (exported for testability) ---

export function buildAnswerContent(base: string, interim: string): string {
  return ((base || "") + (interim ? ` ${interim}` : "")).trim();
}

export function mergeTranscript(base: string, transcript: string): string {
  if (!base) return transcript;
  const separator = base.endsWith(" ") ? "" : " ";
  return base + separator + transcript;
}

/**
 * Determine audio duration for turn submission.
 * Voice path: returns elapsed ms since mic start.
 * Text fallback (explicit edit OR unavailable STT): returns undefined.
 */
export function computeAudioDuration(
  isEditing: boolean,
  isVoiceAvailable: boolean,
  micStartTime: number,
  now: number,
): number | undefined {
  const usedVoice = !isEditing && isVoiceAvailable;
  return usedVoice ? Math.max(0, now - micStartTime) : undefined;
}

/**
 * Determine whether the Done button should be disabled.
 * Disabled when there is no content to submit (neither typed text nor interim speech).
 */
export function computeIsDoneDisabled(answerText: string, interimTranscript: string): boolean {
  return !answerText.trim() && !interimTranscript;
}

// --- Types ---

interface UseAnswerInputControllerParams {
  phase: InterviewPhase;
  transcript: string;
  interimTranscript: string;
  isVoiceAvailable: boolean;
  startListening: () => void;
  stopListening: () => void;
  resetTranscript: () => void;
  submitAnswer: (content: string, audioDurationMs?: number) => Promise<void>;
}

interface UseAnswerInputControllerReturn {
  answerText: string;
  setAnswerText: (text: string) => void;
  isEditing: boolean;
  textareaRef: RefObject<HTMLTextAreaElement | null>;
  handleToggleEdit: () => void;
  handleRetryVoice: () => void;
  handleDone: () => void;
  isDoneDisabled: boolean;
}

// --- Hook ---

export function useAnswerInputController({
  phase,
  transcript,
  interimTranscript,
  isVoiceAvailable,
  startListening,
  stopListening,
  resetTranscript,
  submitAnswer,
}: UseAnswerInputControllerParams): UseAnswerInputControllerReturn {
  const [answerText, setAnswerText] = useState("");
  const [isEditing, setIsEditing] = useState(false);
  const baseTextRef = useRef("");
  const micStartRef = useRef(0);
  const isSubmittingRef = useRef(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const focusTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const prevPhaseRef = useRef<InterviewPhase>(phase);

  // --- Edit mode transitions ---

  const enterEditMode = useCallback(() => {
    const frozen = buildAnswerContent(answerText, interimTranscript);
    setAnswerText(frozen);
    stopListening();
    resetTranscript();
    setIsEditing(true);
    focusTimerRef.current = setTimeout(() => textareaRef.current?.focus(), 50);
  }, [answerText, interimTranscript, stopListening, resetTranscript]);

  const exitEditMode = useCallback(() => {
    baseTextRef.current = answerText;
    setIsEditing(false);
    startListening();
  }, [answerText, startListening]);

  const handleToggleEdit = useCallback(() => {
    if (isEditing) {
      exitEditMode();
      return;
    }
    enterEditMode();
  }, [isEditing, enterEditMode, exitEditMode]);

  // Retry voice from mic status notice — same as exiting edit mode
  const handleRetryVoice = exitEditMode;

  // --- Submission ---

  const handleSubmitAnswer = useCallback(
    async (content: string) => {
      stopListening();
      const audioDurationMs = computeAudioDuration(
        isEditing,
        isVoiceAvailable,
        micStartRef.current,
        Date.now(),
      );
      await submitAnswer(content, audioDurationMs);
    },
    [stopListening, submitAnswer, isEditing, isVoiceAvailable],
  );

  const handleDone = useCallback(() => {
    if (isSubmittingRef.current) return;
    const content = buildAnswerContent(answerText, interimTranscript);
    if (content) {
      isSubmittingRef.current = true;
      handleSubmitAnswer(content);
      setAnswerText("");
      baseTextRef.current = "";
    }
  }, [answerText, interimTranscript, handleSubmitAnswer]);

  // --- Derived ---

  const isDoneDisabled = useMemo(
    () => computeIsDoneDisabled(answerText, interimTranscript),
    [answerText, interimTranscript],
  );

  // --- Effects ---

  // Sync STT transcript into textarea (skip while editing to avoid overwriting typed edits)
  useEffect(() => {
    if (!transcript || isEditing) return;
    setAnswerText(mergeTranscript(baseTextRef.current, transcript));
  }, [transcript, isEditing]);

  // Reset answer state on NEW answering turn only (phase transition boundary)
  useEffect(() => {
    const isNewTurn = phase === "answering" && prevPhaseRef.current !== "answering";
    prevPhaseRef.current = phase;
    if (!isNewTurn) return;

    setAnswerText("");
    setIsEditing(!isVoiceAvailable);
    baseTextRef.current = "";
    isSubmittingRef.current = false;
    resetTranscript();
    micStartRef.current = Date.now();
  }, [phase, resetTranscript, isVoiceAvailable]);

  // Voice lost mid-turn — graceful fallback to text without clearing content
  useEffect(() => {
    if (phase === "answering" && !isVoiceAvailable && !isEditing) {
      setIsEditing(true);
    }
  }, [phase, isVoiceAvailable, isEditing]);

  // Clear pending focus timeout if the component unmounts before it fires
  useEffect(() => {
    return () => {
      if (focusTimerRef.current) clearTimeout(focusTimerRef.current);
    };
  }, []);

  return {
    answerText,
    setAnswerText,
    isEditing,
    textareaRef,
    handleToggleEdit,
    handleRetryVoice,
    handleDone,
    isDoneDisabled,
  };
}
