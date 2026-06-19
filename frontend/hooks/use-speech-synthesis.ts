"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface SpeechSynthesisResult {
  isSpeaking: boolean;
  speak: (text: string, onEnd?: () => void) => void;
  cancel: () => void;
  isSupported: boolean;
}

/**
 * Wraps the SpeechSynthesis API for text-to-speech output.
 * Auto-selects a natural English voice when available.
 * Fires optional onEnd callback when utterance completes.
 */
export function useSpeechSynthesis(): SpeechSynthesisResult {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const onEndCallbackRef = useRef<(() => void) | null>(null);

  const isSupported = "speechSynthesis" in globalThis;

  const selectVoice = useCallback((): SpeechSynthesisVoice | null => {
    if (!isSupported) return null;

    const voices = globalThis.speechSynthesis.getVoices();
    if (voices.length === 0) return null;

    // Prefer natural-sounding English voices
    const preferred = voices.find(
      (v) =>
        v.lang.startsWith("en") &&
        (v.name.includes("Natural") ||
          v.name.includes("Google") ||
          v.name.includes("Samantha") ||
          v.name.includes("Daniel")),
    );

    if (preferred) return preferred;

    // Fallback: any English voice
    const english = voices.find((v) => v.lang.startsWith("en"));
    if (english) return english;

    // Fallback: first available voice
    return voices[0] ?? null;
  }, [isSupported]);

  const safetyTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const watchdogTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // --- Extracted helpers (Consolidate Duplicate Conditional Fragments) ---

  const clearSpeechTimers = useCallback(() => {
    if (safetyTimerRef.current) {
      clearTimeout(safetyTimerRef.current);
      safetyTimerRef.current = null;
    }
    if (watchdogTimerRef.current) {
      clearTimeout(watchdogTimerRef.current);
      watchdogTimerRef.current = null;
    }
  }, []);

  const finishSpeech = useCallback(() => {
    clearSpeechTimers();
    setIsSpeaking(false);
    const cb = onEndCallbackRef.current;
    onEndCallbackRef.current = null;
    cb?.();
  }, [clearSpeechTimers]);

  // --- Main API ---

  const speak = useCallback(
    (text: string, onEnd?: () => void) => {
      if (!isSupported || !text.trim()) {
        // If not supported, immediately call onEnd so state machine progresses
        onEnd?.();
        return;
      }

      // Cancel any in-progress speech
      globalThis.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      const voice = selectVoice();
      if (voice) {
        utterance.voice = voice;
      } else {
        console.warn("[TTS] No voice available — safety timeout will handle transition");
      }
      utterance.rate = 1;
      utterance.pitch = 1;

      onEndCallbackRef.current = onEnd ?? null;

      // Safety timeout: if onstart never fires within 2s, TTS silently failed.
      // First-utterance voice loading can take 500-1000ms; 500ms was too aggressive.
      clearSpeechTimers();
      safetyTimerRef.current = setTimeout(() => {
        console.warn("[TTS] Safety timeout — onstart never fired, forcing transition");
        finishSpeech();
      }, 2000);

      utterance.onstart = () => {
        // TTS is actually playing — clear safety timer, start watchdog
        if (safetyTimerRef.current) {
          clearTimeout(safetyTimerRef.current);
          safetyTimerRef.current = null;
        }
        setIsSpeaking(true);

        // Watchdog: if speaking for >20s without onend, force transition
        if (watchdogTimerRef.current) clearTimeout(watchdogTimerRef.current);
        watchdogTimerRef.current = setTimeout(() => {
          console.warn("[TTS] Watchdog: speaking >20s without onend — forcing transition");
          globalThis.speechSynthesis.cancel();
          finishSpeech();
        }, 20000);
      };

      utterance.onend = () => finishSpeech();

      utterance.onerror = (e) => {
        console.warn("[TTS] onerror fired:", e);
        finishSpeech();
      };

      globalThis.speechSynthesis.speak(utterance);
    },
    [isSupported, selectVoice, clearSpeechTimers, finishSpeech],
  );

  const cancel = useCallback(() => {
    if (!isSupported) return;
    // Clear callback BEFORE cancel — browser may synchronously emit onerror on cancel
    onEndCallbackRef.current = null;
    clearSpeechTimers();
    globalThis.speechSynthesis.cancel();
    setIsSpeaking(false);
  }, [isSupported, clearSpeechTimers]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      onEndCallbackRef.current = null;
      clearSpeechTimers();
      if (isSupported) {
        globalThis.speechSynthesis.cancel();
      }
    };
  }, [isSupported, clearSpeechTimers]);

  // Load voices (Chrome loads async)
  useEffect(() => {
    if (!isSupported) return;
    globalThis.speechSynthesis.getVoices();
  }, [isSupported]);

  return { isSpeaking, speak, cancel, isSupported };
}
