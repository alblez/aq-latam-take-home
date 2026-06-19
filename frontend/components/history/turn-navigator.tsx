"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";

type TurnNavigatorProps = Readonly<{
  currentTurn: number;
  totalTurns: number;
  onPrev: () => void;
  onNext: () => void;
}>;

export function TurnNavigator({ currentTurn, totalTurns, onPrev, onNext }: TurnNavigatorProps) {
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === "ArrowLeft" && currentTurn > 0) {
        onPrev();
      } else if (e.key === "ArrowRight" && currentTurn < totalTurns - 1) {
        onNext();
      }
    }

    globalThis.addEventListener("keydown", handleKey);
    return () => globalThis.removeEventListener("keydown", handleKey);
  }, [currentTurn, totalTurns, onPrev, onNext]);

  return (
    <div className="fixed bottom-0 left-0 right-0 z-10 flex h-14 items-center justify-center gap-4 border-t border-[var(--color-border)] bg-[var(--color-background)]">
      <Button
        variant="secondary"
        size="sm"
        onClick={onPrev}
        disabled={currentTurn === 0}
        aria-label="Previous turn"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
          className="size-4"
          aria-hidden="true"
        >
          <path d="m15 18-6-6 6-6" />
        </svg>
        Prev
      </Button>

      <span className="min-w-[100px] text-center text-sm text-[var(--color-foreground-muted)]">
        Turn {currentTurn + 1} of {totalTurns}
      </span>

      <Button
        variant="secondary"
        size="sm"
        onClick={onNext}
        disabled={currentTurn >= totalTurns - 1}
        aria-label="Next turn"
      >
        Next
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
          className="size-4"
          aria-hidden="true"
        >
          <path d="m9 18 6-6-6-6" />
        </svg>
      </Button>
    </div>
  );
}
