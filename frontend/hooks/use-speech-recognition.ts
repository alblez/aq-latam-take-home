"use client";

import { useCallback, useEffect, useRef, useState } from "react";

// --- Web Speech API type declarations (not in default DOM lib) ---

interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionResultList extends Iterable<SpeechRecognitionResult> {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  isFinal: boolean;
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: Event) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
  abort(): void;
}

interface SpeechRecognitionConstructor {
  new (): SpeechRecognition;
  prototype: SpeechRecognition;
}

type SpeechRecognitionGlobal = typeof globalThis & {
  SpeechRecognition?: SpeechRecognitionConstructor;
  webkitSpeechRecognition?: SpeechRecognitionConstructor;
};

// --- Error classification ---

const FATAL_ERRORS = new Set(["not-allowed", "audio-capture", "network", "service-not-allowed"]);
const TRANSIENT_ERRORS = new Set(["no-speech", "aborted"]);

// --- Constants ---

const HARD_STOP_MS = 120_000; // 2 minutes with no onresult
const ERROR_RESTART_MAX = 5;
const RESTART_DELAY_MS = 300;
const RETRY_DELAY_MS = 200;
const RETRY_ELAPSED_THRESHOLD_MS = 100;

// --- Exported types ---

export type SpeechErrorType =
  | "none"
  | "not-supported"
  | "not-allowed"
  | "audio-capture"
  | "network"
  | "transient";

export interface UseSpeechRecognitionReturn {
  isListening: boolean;
  transcript: string;
  interimTranscript: string;
  startListening: () => void;
  stopListening: () => void;
  resetTranscript: () => void;
  isSupported: boolean;
  errorType: SpeechErrorType;
  hasEverRecognized: boolean;
}

// --- Hook ---

export function useSpeechRecognition(): UseSpeechRecognitionReturn {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [interimTranscript, setInterimTranscript] = useState("");
  const [errorType, setErrorType] = useState<SpeechErrorType>("none");
  const [hasEverRecognized, setHasEverRecognized] = useState(false);

  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const shouldBeListeningRef = useRef(false);
  const startTimeRef = useRef(0);
  const lastResultTimeRef = useRef(0);
  const hasEverRecognizedRef = useRef(false);
  const restartTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const errorRestartCountRef = useRef(0);
  const unknownErrorStreakRef = useRef(0);
  const lastErrorCauseRef = useRef<string | null>(null);
  const latestInterimRef = useRef("");
  const rafRef = useRef<number | null>(null);

  const speechGlobal = globalThis as SpeechRecognitionGlobal;
  const isSupported =
    "SpeechRecognition" in speechGlobal || "webkitSpeechRecognition" in speechGlobal;

  // --- Helpers ---

  const getRecognition = useCallback((): SpeechRecognition | null => {
    if (!isSupported) return null;
    const Ctor = speechGlobal.SpeechRecognition ?? speechGlobal.webkitSpeechRecognition;
    if (!Ctor) return null;
    const r = new Ctor();
    r.continuous = true;
    r.interimResults = true;
    r.lang = "en-US";
    return r;
  }, [isSupported]);

  const clearAllTimers = useCallback(() => {
    if (restartTimerRef.current) {
      clearTimeout(restartTimerRef.current);
      restartTimerRef.current = null;
    }
    if (retryTimerRef.current) {
      clearTimeout(retryTimerRef.current);
      retryTimerRef.current = null;
    }
    if (rafRef.current != null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
  }, []);

  const setupRecognition = useCallback(
    (recognition: SpeechRecognition) => {
      recognition.onresult = (event: SpeechRecognitionEvent) => {
        let finalText = "";
        let interimText = "";

        for (const result of event.results) {
          if (result.isFinal) {
            finalText += result[0].transcript;
          } else {
            interimText += result[0].transcript;
          }
        }

        if (finalText) {
          // Final result — update immediately, reset counters
          lastResultTimeRef.current = Date.now();
          errorRestartCountRef.current = 0;
          unknownErrorStreakRef.current = 0;

          if (!hasEverRecognizedRef.current) {
            hasEverRecognizedRef.current = true;
            setHasEverRecognized(true);
          }

          setTranscript(finalText);
        }

        // Interim — throttle via RAF
        latestInterimRef.current = interimText;
        rafRef.current ??= requestAnimationFrame(() => {
          rafRef.current = null;
          setInterimTranscript(latestInterimRef.current);
        });
      };

      recognition.onerror = (event: Event) => {
        const err = event as { error?: string; message?: string };
        const errorCode = err.error ?? "unknown";
        console.warn("[STT] onerror:", errorCode, err.message ?? "");

        if (FATAL_ERRORS.has(errorCode)) {
          console.warn("[STT] Fatal error:", errorCode);
          shouldBeListeningRef.current = false;
          setIsListening(false);
          setErrorType(errorCode as SpeechErrorType);
          return;
        }

        if (TRANSIENT_ERRORS.has(errorCode)) {
          // Track cause so onend can decide whether to count toward restart limit
          lastErrorCauseRef.current = errorCode;
          return;
        }

        // Unknown error — track streak, escalate after 3 consecutive
        unknownErrorStreakRef.current += 1;
        if (unknownErrorStreakRef.current >= 3) {
          console.warn("[STT] Unknown error streak >= 3, treating as fatal");
          shouldBeListeningRef.current = false;
          setIsListening(false);
          setErrorType("transient");
        }
      };

      recognition.onend = () => {
        // Stale instance guard
        if (recognitionRef.current !== recognition) {
          return;
        }

        if (!shouldBeListeningRef.current) {
          setIsListening(false);
          return;
        }

        // Hard stop: 2 minutes with zero onresult events
        const now = Date.now();
        if (lastResultTimeRef.current > 0 && now - lastResultTimeRef.current > HARD_STOP_MS) {
          console.warn("[STT] Hard stop: no results for 2 minutes");
          shouldBeListeningRef.current = false;
          setIsListening(false);
          setErrorType("transient");
          return;
        }

        // Chrome TTS→STT quirk: if onend fires within 100ms of start(), retry once
        const elapsed = now - startTimeRef.current;
        if (elapsed < RETRY_ELAPSED_THRESHOLD_MS) {
          retryTimerRef.current = setTimeout(() => {
            retryTimerRef.current = null;
            if (!shouldBeListeningRef.current) return;
            try {
              recognition.start();
              startTimeRef.current = Date.now();
            } catch (e) {
              console.warn("[STT] Retry start failed:", e);
              setIsListening(false);
            }
          }, RETRY_DELAY_MS);
          return;
        }

        // Error restart counter (max 5 — no-speech exempt, aborted/unknown count)
        const restartCause = lastErrorCauseRef.current;
        lastErrorCauseRef.current = null;
        if (restartCause && restartCause !== "no-speech") {
          errorRestartCountRef.current += 1;
        }
        if (errorRestartCountRef.current >= ERROR_RESTART_MAX) {
          console.warn("[STT] Max error restarts reached, stopping");
          shouldBeListeningRef.current = false;
          setIsListening(false);
          setErrorType("transient");
          return;
        }

        // Normal restart
        restartTimerRef.current = setTimeout(() => {
          restartTimerRef.current = null;
          if (!shouldBeListeningRef.current) return;
          try {
            // Create fresh instance
            const fresh = getRecognition();
            if (!fresh) {
              shouldBeListeningRef.current = false;
              setIsListening(false);
              return;
            }
            setupRecognition(fresh);
            recognitionRef.current = fresh;
            fresh.start();
            startTimeRef.current = Date.now();
          } catch (e) {
            console.warn("[STT] Restart start failed:", e);
            setIsListening(false);
          }
        }, RESTART_DELAY_MS);
      };
    },
    [getRecognition],
  );

  // --- Actions ---

  const startListening = useCallback(() => {
    if (!isSupported) {
      console.warn("[STT] SpeechRecognition not supported");
      setErrorType("not-supported");
      return;
    }

    clearAllTimers();

    shouldBeListeningRef.current = true;
    setErrorType("none");
    setTranscript("");
    setInterimTranscript("");
    latestInterimRef.current = "";
    errorRestartCountRef.current = 0;
    unknownErrorStreakRef.current = 0;
    lastErrorCauseRef.current = null;
    startTimeRef.current = Date.now();
    lastResultTimeRef.current = Date.now();

    const recognition = getRecognition();
    if (!recognition) {
      console.warn("[STT] Could not create recognition instance");
      setErrorType("not-supported");
      shouldBeListeningRef.current = false;
      return;
    }

    setupRecognition(recognition);
    recognitionRef.current = recognition;

    try {
      recognition.start();
      setIsListening(true);
    } catch (e) {
      if (e instanceof DOMException && e.name === "InvalidStateError") {
        console.warn("[STT] InvalidStateError on start — recognition already started");
      } else {
        console.warn("[STT] start() failed:", e);
      }
      shouldBeListeningRef.current = false;
      setIsListening(false);
    }
  }, [isSupported, clearAllTimers, getRecognition, setupRecognition]);

  const stopListening = useCallback(() => {
    shouldBeListeningRef.current = false;

    if (restartTimerRef.current) {
      clearTimeout(restartTimerRef.current);
      restartTimerRef.current = null;
    }
    if (retryTimerRef.current) {
      clearTimeout(retryTimerRef.current);
      retryTimerRef.current = null;
    }

    const recognition = recognitionRef.current;
    if (recognition) {
      recognition.stop();
      recognitionRef.current = null;
    }

    setIsListening(false);
  }, []);

  const resetTranscript = useCallback(() => {
    setTranscript("");
    setInterimTranscript("");
    latestInterimRef.current = "";
  }, []);

  // --- Cleanup on unmount ---

  useEffect(() => {
    return () => {
      shouldBeListeningRef.current = false;
      clearAllTimers();
      const recognition = recognitionRef.current;
      if (recognition) {
        recognition.abort();
        recognitionRef.current = null;
      }
    };
  }, [clearAllTimers]);

  return {
    isListening,
    transcript,
    interimTranscript,
    startListening,
    stopListening,
    resetTranscript,
    isSupported,
    errorType,
    hasEverRecognized,
  };
}
