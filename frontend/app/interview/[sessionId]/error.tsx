"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";

export default function InterviewError({
  error,
  unstable_retry,
}: Readonly<{
  error: Error & { digest?: string };
  unstable_retry: () => void;
}>) {
  useEffect(() => {
    console.error("Interview error boundary caught an error", error);
  }, [error]);

  return (
    <main
      id="main-content"
      className="flex min-h-dvh items-center justify-center bg-background px-md py-xl text-foreground"
      tabIndex={-1}
    >
      <section
        aria-labelledby="interview-error-title"
        className="w-full max-w-md rounded-lg border border-border bg-surface p-lg text-center"
        role="alert"
      >
        <div className="space-y-md">
          <div className="space-y-sm">
            <p className="font-mono text-foreground-muted text-sm">Interview recovery</p>
            <h1 className="font-semibold text-2xl text-foreground" id="interview-error-title">
              Interview interrupted
            </h1>
            <p className="text-foreground-muted text-sm">
              The interview view stopped unexpectedly. Your session can be resumed from here.
            </p>
          </div>

          <div className="flex flex-col justify-center gap-sm sm:flex-row">
            <Button onClick={unstable_retry} type="button">
              Resume interview
            </Button>
            <Button
              onClick={() => globalThis.location.assign("/")}
              type="button"
              variant="secondary"
            >
              Choose another role
            </Button>
          </div>
        </div>
      </section>
    </main>
  );
}
