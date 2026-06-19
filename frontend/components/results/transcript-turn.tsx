"use client";

import { cn } from "@/lib/utils";
import type { Turn } from "@/types/turn";

type TranscriptTurnProps = Readonly<{
  turn: Turn;
  isHighlighted?: boolean;
  competencyLabel?: string;
  registerTurnRef?: (turnId: string, node: HTMLDivElement | null) => void;
}>;

export function TranscriptTurn({
  turn,
  isHighlighted,
  competencyLabel,
  registerTurnRef,
}: TranscriptTurnProps) {
  const isInterviewer = turn.role === "interviewer";

  return (
    <div
      ref={(node) => registerTurnRef?.(turn.id, node)}
      tabIndex={-1}
      className={cn(
        "rounded-lg border px-4 py-3 transition-colors duration-150",
        "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
        isHighlighted
          ? "border-[var(--color-accent)] bg-[var(--color-accent-muted)]"
          : "border-[var(--color-border)] bg-[var(--color-surface)]",
      )}
    >
      {/* Header */}
      <div className="mb-1.5 flex items-center gap-2">
        <span
          className={cn(
            "text-xs font-semibold uppercase tracking-wider",
            isInterviewer ? "text-[var(--color-accent)]" : "text-[var(--color-foreground-muted)]",
          )}
        >
          {isInterviewer ? "Interviewer" : "You"}
        </span>
        {(competencyLabel || turn.competencyId) && (
          <span className="rounded-full bg-[var(--color-surface)] px-2 py-0.5 font-mono text-[10px] text-[var(--color-foreground-muted)]">
            {competencyLabel ?? turn.competencyId}
          </span>
        )}
      </div>

      {/* Content */}
      <p className="text-sm leading-relaxed text-[var(--color-foreground)]">{turn.content}</p>
    </div>
  );
}
