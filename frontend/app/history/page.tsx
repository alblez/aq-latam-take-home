"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { EmptyHistory } from "@/components/history/empty-history";
import { JobFilter } from "@/components/history/role-filter";
import { ScoreTrendChart } from "@/components/history/score-trend-chart";
import { SessionCard } from "@/components/history/session-card";
import { Skeleton } from "@/components/ui/skeleton";
import type { SessionSummary } from "@/types/session";

type PageState = "loading" | "empty" | "error" | "populated";

export default function HistoryPage() {
  const [pageState, setPageState] = useState<PageState>("loading");
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [selectedRole, setSelectedRole] = useState("__all__");

  useEffect(() => {
    let cancelled = false;
    setPageState("loading");

    (async () => {
      const { getHistory } = await import("@/lib/api/history");
      const result = await getHistory();
      if (cancelled) return;
      if (result.status === "error") {
        setPageState("error");
      } else if (result.data.length === 0) {
        setPageState("empty");
      } else {
        setSessions(result.data);
        setPageState("populated");
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  const roles = useMemo(() => Array.from(new Set(sessions.map((s) => s.jobTitle))), [sessions]);

  const filtered = useMemo(
    () =>
      selectedRole === "__all__" ? sessions : sessions.filter((s) => s.jobTitle === selectedRole),
    [sessions, selectedRole],
  );

  // --- Loading state ---
  if (pageState === "loading") {
    return (
      <div className="mx-auto max-w-[800px] px-4 py-8 sm:px-6">
        <div className="mb-6 flex items-center justify-between">
          <Skeleton className="h-7 w-44" />
          <Skeleton className="h-8 w-36" />
        </div>
        <div className="flex flex-col gap-4">
          {["skeleton-a", "skeleton-b", "skeleton-c"].map((id) => (
            <div
              key={id}
              className="flex flex-col gap-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4"
            >
              <div className="flex items-baseline justify-between">
                <Skeleton className="h-5 w-48" />
                <Skeleton className="h-3 w-20" />
              </div>
              <div className="flex items-center gap-3">
                <Skeleton className="h-5 w-8" />
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-5 w-20 rounded-full" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // --- Error state ---
  if (pageState === "error") {
    return (
      <div className="mx-auto max-w-[800px] px-4 py-8 sm:px-6">
        <div className="flex flex-col items-center justify-center py-20">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            stroke="currentColor"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
            className="mb-4 size-8 text-[var(--color-destructive)]"
            strokeWidth={1.5}
            viewBox="0 0 24 24"
          >
            <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3M12 9v4m0 4h.01" />
          </svg>
          <h2 className="mb-2 text-lg font-semibold text-[var(--color-foreground)]">
            Something went wrong
          </h2>
          <p className="mb-6 text-sm text-[var(--color-foreground-muted)]">
            Could not load your interview history.
          </p>
        </div>
      </div>
    );
  }

  // --- Empty state ---
  if (pageState === "empty" || sessions.length === 0) {
    return (
      <div className="mx-auto max-w-[800px] px-4 py-8 sm:px-6">
        <EmptyHistory />
      </div>
    );
  }

  // --- Populated state ---
  return (
    <div className="mx-auto max-w-[800px] px-4 py-8 sm:px-6">
      {/* Header */}
      <header className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold leading-tight tracking-tight text-[var(--color-foreground)]">
          Your Interviews
        </h1>
        <JobFilter jobTitles={roles} selected={selectedRole} onChange={setSelectedRole} />
      </header>

      {/* Session list */}
      {filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16">
          <p className="text-sm text-[var(--color-foreground-muted)]">
            No interviews match this filter.
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {filtered.map((session) => (
            <Link
              key={session.id}
              href={`/history/${session.id}`}
              className="block rounded-lg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-accent)]"
            >
              <SessionCard session={session} />
            </Link>
          ))}
        </div>
      )}

      {/* Score trend */}
      <div className="mt-8">
        <ScoreTrendChart sessions={sessions} />
      </div>
    </div>
  );
}
