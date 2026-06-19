"use client";

import { Badge } from "@/components/ui/badge";
import { formatDate } from "@/lib/format-date";
import { cn } from "@/lib/utils";
import type { SessionSummary } from "@/types/session";

type SessionCardProps = Readonly<{
  session: SessionSummary;
}>;

function formatDuration(durationMs: number): string {
  const totalSeconds = Math.round(durationMs / 1000);
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return s > 0 ? `${m}m ${s}s` : `${m}m`;
}

export function SessionCard({ session }: SessionCardProps) {
  const isCompleted = session.status === "completed";

  return (
    <article
      className={cn(
        "w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4 text-left",
        "transition-shadow duration-200 hover:shadow-[var(--shadow-hover)]",
      )}
    >
      {/* Row 1: title + date */}
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-sm font-semibold text-[var(--color-foreground)]">
          {session.jobTitle}
        </span>
        <span className="shrink-0 text-xs text-[var(--color-foreground-muted)]">
          {formatDate(session.startedAt)}
        </span>
      </div>

      {/* Row 2: score + coverage + status + duration */}
      <div className="mt-2 flex items-center gap-3">
        <span className="font-mono text-base font-semibold text-[var(--color-accent)]">
          {session.overallScore === null ? "\u2014" : session.overallScore.toFixed(1)}
        </span>
        <span className="text-xs text-[var(--color-foreground-muted)]">
          {session.coveragePercent === null ? "\u2014" : `${session.coveragePercent}% coverage`}
        </span>
        <Badge variant={isCompleted ? "success" : "warning"}>
          {isCompleted ? "Completed" : "Ended Early"}
        </Badge>
        <span className="ml-auto text-xs text-[var(--color-foreground-muted)]">
          {session.durationMs === null ? "\u2014" : formatDuration(session.durationMs)}
        </span>
      </div>
    </article>
  );
}
