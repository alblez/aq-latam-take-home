"use client";

import { use, useCallback, useEffect, useMemo, useState } from "react";
import { TurnNavigator } from "@/components/history/turn-navigator";
import { TranscriptTurn } from "@/components/results/transcript-turn";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { PanelState } from "@/types/turn";
import { ReplayDecisionPanel } from "./_components/replay-decision-panel";
import { ReplayHeader } from "./_components/replay-header";
import { ReplayMobilePanel } from "./_components/replay-mobile-panel";
import { loadReplaySession } from "./replay-loader";
import { beginReplayLoad, finishReplayLoad, type ReplayPageState } from "./replay-page-state";

export default function ReplayPage({
  params,
}: Readonly<{ params: Promise<{ sessionId: string }> }>) {
  const { sessionId } = use(params);
  const [pageState, setPageState] = useState<ReplayPageState>({
    loading: true,
    session: null,
    error: null,
  });
  const { session, loading, error } = pageState;
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (!sessionId) return;
    let cancelled = false;
    // Clear any stale session/error from a previous direct load before fetching.
    setPageState((prev) => beginReplayLoad(prev));

    (async () => {
      const result = await loadReplaySession(sessionId);
      if (cancelled) return;
      // Always exits loading — import/API failures cannot trap the spinner.
      setPageState((prev) => finishReplayLoad(prev, result));
    })();

    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  const turns = session?.turns ?? [];

  // Reset navigation when the loaded session changes so a stale index from a
  // previous session never points past the new turn list (WR-05).
  // biome-ignore lint/correctness/useExhaustiveDependencies: session id is intentionally used only as a reset trigger
  useEffect(() => {
    setCurrentIndex(0);
  }, [session?.session.id]);

  // Use turn.reasoning directly — it's already PanelState | null per contract.
  // Clamp the index defensively in case it ever exceeds the loaded turn count.
  const panelState: PanelState | null = useMemo(() => {
    if (turns.length === 0) return null;
    const start = Math.min(currentIndex, turns.length - 1);
    for (let i = start; i >= 0; i--) {
      const r = turns[i]?.reasoning;
      if (r) return r;
    }
    return null;
  }, [currentIndex, turns]);

  const handlePrev = useCallback(() => setCurrentIndex((i) => Math.max(0, i - 1)), []);

  const handleNext = useCallback(
    () => setCurrentIndex((i) => Math.min(Math.max(0, turns.length - 1), i + 1)),
    [turns.length],
  );

  if (loading) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-[var(--color-background)]">
        <p className="text-sm text-[var(--color-foreground-muted)]">Loading replay...</p>
      </div>
    );
  }

  if (error || !session) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-[var(--color-background)]">
        <div className="flex flex-col items-center gap-2">
          <p className="text-lg font-semibold text-[var(--color-foreground)]">
            Could not load replay
          </p>
          <p className="text-sm text-[var(--color-foreground-muted)]">
            {error ?? "Session not found."}
          </p>
        </div>
      </div>
    );
  }

  const isCompleted = session.session.status === "completed";
  const overallScore = session.evaluation?.overallScore ?? null;

  return (
    <div className="min-h-dvh bg-[var(--color-background)]">
      <ReplayHeader session={session} overallScore={overallScore} isCompleted={isCompleted} />

      {/* Two-panel layout */}
      <div className="mx-auto flex max-w-[1200px] flex-col lg:flex-row">
        {/* Left: Transcript */}
        <div className="flex-1 border-r border-[var(--color-border)] pb-20 lg:pb-0">
          <ScrollArea className="h-[calc(100dvh-56px-56px)] lg:h-[calc(100dvh-56px)]">
            <div className="flex flex-col gap-3 p-4">
              {turns.map((turn, i) => (
                <TranscriptTurn key={turn.id} turn={turn} isHighlighted={i === currentIndex} />
              ))}
            </div>
          </ScrollArea>
        </div>

        {/* Right: Decision Panel (desktop) */}
        <ReplayDecisionPanel panelState={panelState} competencies={session.competencies} />

        {/* Mobile decision panel */}
        <ReplayMobilePanel panelState={panelState} competencies={session.competencies} />
      </div>

      {/* Turn navigator */}
      <TurnNavigator
        currentTurn={currentIndex}
        totalTurns={turns.length}
        onPrev={handlePrev}
        onNext={handleNext}
      />
    </div>
  );
}
