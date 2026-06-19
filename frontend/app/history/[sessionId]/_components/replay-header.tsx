"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { formatDate } from "@/lib/format-date";
import type { SessionDetail } from "@/types/session";

const DATE_OPTIONS: Intl.DateTimeFormatOptions = {
  weekday: "short",
  month: "short",
  day: "numeric",
  year: "numeric",
};

type ReplayHeaderProps = Readonly<{
  session: SessionDetail;
  overallScore: number | null;
  isCompleted: boolean;
}>;

export function ReplayHeader({ session, overallScore, isCompleted }: ReplayHeaderProps) {
  return (
    <header className="sticky top-0 z-30 flex h-14 items-center border-b border-[var(--color-border)] bg-[var(--color-background)] px-4">
      <div className="mx-auto flex w-full max-w-[1200px] items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/history"
            className="inline-flex items-center gap-1.5 text-sm text-[var(--color-foreground-muted)] transition-colors hover:text-[var(--color-foreground)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-accent)]"
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
            Back to History
          </Link>
          <Separator orientation="vertical" className="h-5" />
          <h1 className="text-sm font-semibold text-[var(--color-foreground)]">
            {session.job.title}
          </h1>
        </div>

        <div className="flex items-center gap-3">
          {session.session.startedAt && (
            <span className="text-xs text-[var(--color-foreground-muted)]">
              {formatDate(session.session.startedAt, DATE_OPTIONS)}
            </span>
          )}
          <span className="font-mono text-sm font-semibold text-[var(--color-accent)]">
            {overallScore !== null ? overallScore.toFixed(1) : "\u2014"}
          </span>
          <Badge variant={isCompleted ? "success" : "warning"}>
            {isCompleted ? "Completed" : "Ended Early"}
          </Badge>
        </div>
      </div>
    </header>
  );
}
