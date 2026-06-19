"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type WelcomeScreenProps = Readonly<{
  jobTitle: string;
  onBegin: () => void;
  isLoading: boolean;
}>;

export function WelcomeScreen({ jobTitle, onBegin, isLoading }: WelcomeScreenProps) {
  // Optimistic default: Chrome users see no warning flash
  const [supportsSpeech, setSupportsSpeech] = useState(true);

  type MicCheckState = "idle" | "checking" | "granted" | "denied" | "unsupported";
  const [micCheck, setMicCheck] = useState<MicCheckState>("idle");

  const handleBeginClick = useCallback(async () => {
    if (!supportsSpeech) {
      onBegin();
      return;
    }

    setMicCheck("checking");

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((t) => {
        t.stop();
      });
      setMicCheck("granted");
      setTimeout(() => {
        onBegin();
      }, 600);
    } catch {
      setMicCheck("denied");
    }
  }, [supportsSpeech, onBegin]);

  useEffect(() => {
    if (typeof navigator === "undefined") return;
    const ua = navigator.userAgent;
    const chromium = /Chrome|Chromium|CriOS/.test(ua) && !/Edg|OPR/.test(ua);
    setSupportsSpeech(chromium);
  }, []);

  return (
    <section
      className="relative flex min-h-[calc(100dvh-64px)] flex-col px-md sm:px-lg"
      aria-labelledby="welcome-heading"
    >
      {/* Navigation — escape hatch */}
      <nav className="py-md">
        <Link
          href="/"
          className="inline-flex items-center gap-xs text-sm text-foreground-muted transition-colors duration-150 hover:text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
        >
          <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path
              d="M10.25 6.75L4.75 12L10.25 17.25"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M19.25 12H5"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          Choose a different role
        </Link>
      </nav>

      {/* Main content — vertically centered in remaining space */}
      <div className="flex flex-1 flex-col items-center justify-center pb-2xl motion-safe:animate-[fade-up_0.5s_cubic-bezier(0.16,1,0.3,1)_both]">
        {/* Heading zone */}
        <div className="relative">
          <h1
            id="welcome-heading"
            className="text-center font-display text-[clamp(1.75rem,4vw,2.5rem)] font-normal leading-[1.08] tracking-[-0.01em] text-foreground"
          >
            {jobTitle}
          </h1>
        </div>

        {/* Instruction — tight coupling to heading */}
        <p className="mt-md max-w-[48ch] text-center text-base leading-[1.6] text-foreground-muted">
          Listen to each question, then press Done when you&apos;ve finished answering.
        </p>

        {/* Action zone — generous separation from instruction */}
        <div className="mt-xl flex flex-col items-center gap-md" aria-live="polite">
          <Button
            variant="primary"
            size="lg"
            onClick={micCheck === "denied" ? onBegin : handleBeginClick}
            disabled={isLoading || micCheck === "checking" || micCheck === "granted"}
            className={cn(
              "min-w-[10rem]",
              (isLoading || micCheck === "checking" || micCheck === "granted") && "cursor-wait",
            )}
          >
            {micCheck === "checking" && "Checking mic\u2026"}
            {micCheck === "granted" && "Starting\u2026"}
            {micCheck === "denied" && "Continue without mic"}
            {(micCheck === "idle" || micCheck === "unsupported") &&
              (isLoading ? "Starting\u2026" : "Begin Interview")}
          </Button>

          {/* Mic check status feedback */}
          {micCheck === "checking" && (
            <p className="flex items-center gap-1.5 text-xs font-medium tracking-[0.02em] text-foreground-muted">
              <SpinnerIcon className="size-3.5 animate-spin" />
              Checking microphone…
            </p>
          )}

          {micCheck === "granted" && (
            <p className="flex items-center gap-1.5 text-xs font-medium tracking-[0.02em] text-[oklch(0.610_0.135_155)]">
              <CheckIcon className="size-3.5" />
              Mic ready
            </p>
          )}

          {micCheck === "denied" && (
            <p className="max-w-[44ch] text-center text-xs font-medium leading-relaxed text-foreground-muted">
              Microphone unavailable — you can still type your answers.
            </p>
          )}

          {/* Browser compatibility — spec D19: non-Chrome notice */}
          {!supportsSpeech && (
            <p className="max-w-[44ch] text-center text-xs leading-relaxed text-foreground-muted">
              Voice input works best in Chrome. A text fallback is always available.
            </p>
          )}
        </div>
      </div>
    </section>
  );
}

function SpinnerIcon({ className }: Readonly<{ className?: string }>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      className={className}
      aria-hidden="true"
    >
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  );
}

function CheckIcon({ className }: Readonly<{ className?: string }>) {
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
      <path d="M20 6 9 17l-5-5" />
    </svg>
  );
}
