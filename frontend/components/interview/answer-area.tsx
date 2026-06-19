"use client";

import { type RefObject, useCallback, useEffect } from "react";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

export type MicStatus =
  | "ok"
  | "browser-unsupported"
  | "permission-denied"
  | "no-hardware"
  | "network-error"
  | "no-speech-detected"
  | "mic-lost";

type AnswerAreaProps = Readonly<{
  textareaRef: RefObject<HTMLTextAreaElement | null>;
  value: string;
  onChange: (value: string) => void;
  interimTranscript: string;
  isListening: boolean;
  isEditing: boolean;
  isVoiceAvailable: boolean;
  onToggleEdit: () => void;
  onRetryVoice: () => void;
  micStatus: MicStatus;
  onSubmitRequest: () => void;
  disabled: boolean;
}>;

export function AnswerArea({
  textareaRef,
  value,
  onChange,
  interimTranscript,
  isListening,
  isEditing,
  isVoiceAvailable,
  onToggleEdit,
  onRetryVoice,
  micStatus,
  onSubmitRequest,
  disabled,
}: AnswerAreaProps) {
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        onSubmitRequest();
      }
    },
    [onSubmitRequest],
  );

  const showToggle = isVoiceAvailable;
  const effectiveEditing = isEditing || !isVoiceAvailable;

  // Auto-grow textarea to fit content, capped at 200px
  const autoResize = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [textareaRef]);

  useEffect(() => {
    autoResize();
  }, [autoResize]);

  return (
    <div className="flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium tracking-[0.02em] text-foreground-muted">
          Your answer
        </span>
        {isListening && micStatus === "ok" && <MicActiveIndicator />}
        {!isVoiceAvailable && <MicStatusNotice micStatus={micStatus} onRetryVoice={onRetryVoice} />}
      </div>

      {/* Textarea container */}
      <div className="relative">
        <Textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => {
            // If user types while in voice mode, auto-switch to edit
            if (!effectiveEditing && e.target.value !== value) {
              onToggleEdit();
            }
            onChange(e.target.value);
          }}
          placeholder={
            effectiveEditing
              ? "Type your answer..."
              : "Listening... start typing to switch to text mode"
          }
          onKeyDown={handleKeyDown}
          disabled={disabled}
          data-gramm={effectiveEditing ? undefined : "false"}
          data-gramm_editor={effectiveEditing ? undefined : "false"}
          data-enable-grammarly={effectiveEditing ? undefined : "false"}
          autoComplete={effectiveEditing ? undefined : "off"}
          spellCheck={effectiveEditing ? undefined : false}
          className={cn(
            "min-h-28 max-h-[200px] resize-none overflow-y-auto",
            "border-border bg-surface",
            effectiveEditing
              ? "focus:border-accent focus:ring-1 focus:ring-accent/30"
              : "focus:border-accent/50 focus:ring-1 focus:ring-accent/20",
            disabled && "opacity-50 cursor-not-allowed",
          )}
        />

        {/* Toggle button */}
        {showToggle && !disabled && (
          <button
            type="button"
            onClick={onToggleEdit}
            className="absolute bottom-3 right-3 flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-foreground-muted hover:bg-surface-elevated hover:text-foreground transition-colors"
            aria-label={isEditing ? "Resume voice input" : "Edit text manually"}
          >
            {isEditing ? <MicIcon className="size-3.5" /> : <PencilIcon className="size-3.5" />}
            <span>{isEditing ? "Voice" : "Edit"}</span>
          </button>
        )}
      </div>

      {/* Interim ghost text — below textarea, never overlaps */}
      {interimTranscript && isListening && !effectiveEditing && (
        <div
          aria-hidden="true"
          className="flex items-center gap-1.5 px-3 text-sm text-foreground-muted/60"
        >
          <span className="inline-block size-1.5 rounded-full bg-accent/40 motion-safe:animate-pulse" />
          <span className="truncate">{interimTranscript}</span>
        </div>
      )}
    </div>
  );
}

/* --- Mic active indicator (simple, no volume bars) --- */

function MicActiveIndicator() {
  return (
    <div className="flex items-center gap-1.5">
      <span className="relative flex size-4 items-center justify-center">
        <MicIcon className="relative size-3.5 text-accent" />
        <span
          aria-hidden="true"
          className={cn(
            "absolute inset-0 rounded-full bg-accent/20",
            "motion-safe:animate-[mic-pulse_2s_ease-in-out_infinite]",
          )}
        />
      </span>
      <span className="text-xs font-medium text-accent">Listening</span>
    </div>
  );
}

/* --- Mic status notice --- */

function MicStatusNotice({
  micStatus,
  onRetryVoice,
}: Readonly<{
  micStatus: MicStatus;
  onRetryVoice: () => void;
}>) {
  if (micStatus === "ok") return null;

  const messages: Record<Exclude<MicStatus, "ok">, { text: string; showRetry: boolean }> = {
    "browser-unsupported": {
      text: "Voice input isn't supported in this browser. Use Chrome for voice, or type your answer below.",
      showRetry: false,
    },
    "permission-denied": {
      text: "Microphone access denied. Check browser permissions, then reload.",
      showRetry: false,
    },
    "no-hardware": {
      text: "No microphone detected. Connect a mic or type your answer below.",
      showRetry: true,
    },
    "network-error": {
      text: "Voice input is unavailable in this browser. Use Chrome for voice, or type your answer below.",
      showRetry: true,
    },
    "no-speech-detected": {
      text: "Take your time. Mic is ready when you are, or type below.",
      showRetry: true,
    },
    "mic-lost": {
      text: "Voice input interrupted. You can type, or",
      showRetry: true,
    },
  };

  const { text, showRetry } = messages[micStatus];

  return (
    <div role="status" aria-live="polite" className="flex items-center gap-1.5">
      <MicOffIcon className="size-3.5 text-foreground-muted flex-shrink-0" />
      <span className="text-xs font-medium text-foreground-muted">
        {text}
        {showRetry && (
          <button
            type="button"
            onClick={onRetryVoice}
            className="ml-1 text-accent hover:text-accent/80 underline underline-offset-2"
          >
            retry voice
          </button>
        )}
      </span>
    </div>
  );
}

/* --- Inline SVG icons --- */

function MicIcon({ className }: Readonly<{ className?: string }>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
      <line x1="12" x2="12" y1="19" y2="22" />
    </svg>
  );
}

function MicOffIcon({ className }: Readonly<{ className?: string }>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <line x1="2" x2="22" y1="2" y2="22" />
      <path d="M18.89 13.23A7.12 7.12 0 0 0 19 12v-2" />
      <path d="M5 10v2a7 7 0 0 0 12 5" />
      <path d="M15 9.34V5a3 3 0 0 0-5.68-1.33" />
      <path d="M9 9v3a3 3 0 0 0 5.12 2.12" />
      <line x1="12" x2="12" y1="19" y2="22" />
    </svg>
  );
}

function PencilIcon({ className }: Readonly<{ className?: string }>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" />
      <path d="m15 5 4 4" />
    </svg>
  );
}
