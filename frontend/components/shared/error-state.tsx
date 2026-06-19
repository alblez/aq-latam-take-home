"use client";

import { Button } from "@/components/ui/button";

type ErrorStateProps = Readonly<{
  title?: string;
  message: string;
  onRetry?: () => void;
}>;

export function ErrorState({ title = "Something went wrong", message, onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-[360px] text-center">
        {/* Warning triangle icon */}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          stroke="currentColor"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
          className="mx-auto mb-4 size-8 text-destructive"
          strokeWidth={1.5}
          viewBox="0 0 24 24"
        >
          <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3M12 9v4m0 4h.01" />
        </svg>

        <h2 className="mb-2 text-lg font-semibold text-foreground">{title}</h2>

        <p className="mb-6 text-sm text-foreground-muted">{message}</p>

        {onRetry && (
          <Button variant="secondary" onClick={onRetry}>
            Try again
          </Button>
        )}
      </div>
    </div>
  );
}
