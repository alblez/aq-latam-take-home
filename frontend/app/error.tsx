"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";

export default function GlobalError({
  error,
  unstable_retry,
}: Readonly<{
  error: Error & { digest?: string };
  unstable_retry: () => void;
}>) {
  useEffect(() => {
    console.error("Root error boundary caught an error", error);
  }, [error]);

  return (
    <main
      id="main-content"
      className="flex min-h-dvh items-center justify-center bg-background px-md py-xl text-foreground"
      tabIndex={-1}
    >
      <section
        aria-labelledby="global-error-title"
        className="w-full max-w-md rounded-lg border border-border bg-surface p-lg text-center"
        role="alert"
      >
        <div className="space-y-md">
          <div className="space-y-sm">
            <p className="font-mono text-foreground-muted text-sm">System recovery</p>
            <h1 className="font-semibold text-2xl text-foreground" id="global-error-title">
              Something went wrong
            </h1>
            <p className="text-foreground-muted text-sm">
              The page stopped unexpectedly. You can retry the request or return home.
            </p>
          </div>

          <div className="flex flex-col justify-center gap-sm sm:flex-row">
            <Button onClick={unstable_retry} type="button">
              Try again
            </Button>
            <Button
              onClick={() => globalThis.location.assign("/")}
              type="button"
              variant="secondary"
            >
              Return home
            </Button>
          </div>
        </div>
      </section>
    </main>
  );
}
