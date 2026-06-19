"use client";

import { History } from "lucide-react";
import Link from "next/link";
import { use, useCallback, useEffect, useRef, useState } from "react";
import { PanelRenderer } from "@/components/interview/decision-panel";
import { CompetencyScoreCard } from "@/components/results/competency-score-card";
import { EvaluationLimitations } from "@/components/results/evaluation-limitations";
import { NarrativeSection } from "@/components/results/narrative-section";
import { TranscriptTurn } from "@/components/results/transcript-turn";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { buildTurnLookup } from "@/lib/results/evidence";
import { isInsufficientSignal, verdictBadgeVariant, verdictLabel } from "@/lib/results/verdict";
import type { CompetencyScore } from "@/types/evaluation";
import type { SessionDetail } from "@/types/session";
import type { PanelState, Turn } from "@/types/turn";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return iso;
  }
}

// Build a map from competencyId → label for transcript badges
function buildCompetencyLabelMap(scores: CompetencyScore[]): Map<string, string> {
  const map = new Map<string, string>();
  for (const s of scores) {
    map.set(s.competencyId, s.name);
  }
  return map;
}

/** Type predicate: narrows Turn to one with reasoning guaranteed present. */
function hasReasoning(turn: Turn): turn is Turn & { reasoning: PanelState } {
  return turn.role === "interviewer" && turn.reasoning != null;
}

// ---------------------------------------------------------------------------
// Loading skeleton
// ---------------------------------------------------------------------------

function ResultSkeleton() {
  return (
    <div className="mx-auto w-full max-w-4xl space-y-8 px-4 py-8">
      {/* Header skeleton */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton className="h-7 w-56" />
          <Skeleton className="h-4 w-40" />
        </div>
        <Skeleton className="h-12 w-24" />
      </div>

      <Separator />

      {/* Tabs skeleton */}
      <div className="flex gap-2">
        <Skeleton className="h-9 w-28" />
        <Skeleton className="h-9 w-28" />
        <Skeleton className="h-9 w-28" />
      </div>

      {/* Content skeleton */}
      <div className="space-y-4">
        {["skel-a", "skel-b", "skel-c", "skel-d"].map((id) => (
          <div key={id} className="rounded-lg border border-border p-4 space-y-3">
            <Skeleton className="h-5 w-1/3" />
            <Skeleton className="h-2 w-full" />
            <Skeleton className="h-4 w-2/3" />
          </div>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function ResultPage({
  params,
}: Readonly<{ params: Promise<{ sessionId: string }> }>) {
  const { sessionId } = use(params);
  const [session, setSession] = useState<SessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const [activeTab, setActiveTab] = useState("evaluation");
  const [highlightedTurnId, setHighlightedTurnId] = useState<string | null>(null);
  const turnRefs = useRef<Map<string, HTMLDivElement>>(new Map());

  const registerTurnRef = useCallback((turnId: string, node: HTMLDivElement | null) => {
    if (node) {
      turnRefs.current.set(turnId, node);
    } else {
      turnRefs.current.delete(turnId);
    }
  }, []);

  const jumpToTurn = useCallback((turnId: string) => {
    setActiveTab("transcript");
    setHighlightedTurnId(turnId);
    requestAnimationFrame(() => {
      const target = turnRefs.current.get(turnId);
      target?.scrollIntoView({ behavior: "smooth", block: "center" });
      target?.focus({ preventScroll: true });
    });
  }, []);

  // Fetch session data
  // biome-ignore lint/correctness/useExhaustiveDependencies: retryCount is only a refetch trigger, not read inside the effect
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    (async () => {
      try {
        const { getEvaluation } = await import("@/lib/api/evaluation");
        const result = await getEvaluation(sessionId);
        if (cancelled) return;
        if (result.status === "error") {
          setError(result.message);
        } else {
          setSession(result.data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load results");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [sessionId, retryCount]);

  // --- Loading ---
  if (loading) {
    return (
      <div className="flex min-h-dvh flex-col bg-background">
        <ResultSkeleton />
      </div>
    );
  }

  // --- Error ---
  if (error) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-background">
        <ErrorState
          title="Could not load results"
          message={error}
          onRetry={() => globalThis.location.reload()}
        />
      </div>
    );
  }

  // --- Pending evaluation ---
  if (!session?.evaluation) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-background">
        <EmptyState
          title="Evaluation still preparing"
          description="We do not have enough evaluation data to show results yet. Check again in a moment."
          action={{ label: "Check results again", onClick: () => setRetryCount((c) => c + 1) }}
        />
      </div>
    );
  }

  const { evaluation, job, turns, competencies } = session;
  const { overallScore, competencyScores, narrative } = evaluation;
  const wasEndedEarly = session.session.status === "ended_early";
  const competencyLabelMap = buildCompetencyLabelMap(competencyScores);
  const reasonedTurns = turns.filter(hasReasoning);
  const turnLookup = buildTurnLookup(turns);
  const nullScore = isInsufficientSignal(evaluation);

  return (
    <div className="flex min-h-dvh flex-col bg-background">
      <div className="mx-auto w-full max-w-4xl px-4 py-8">
        {/* Navigation links */}
        <div className="mb-6 flex gap-sm">
          <Link href="/">
            <Button variant="ghost" size="sm">
              &larr; Back to home
            </Button>
          </Link>
          <Link href="/history">
            <Button variant="ghost" size="sm">
              <History className="size-4" aria-hidden="true" />
              View history
            </Button>
          </Link>
        </div>

        {/* Header */}
        <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <h1 className="text-2xl font-bold tracking-tight text-foreground">{job.title}</h1>
            <div className="flex flex-wrap items-center gap-3 text-sm text-foreground-muted">
              {session.session.startedAt && <span>{formatDate(session.session.startedAt)}</span>}
              {wasEndedEarly && <span className="font-medium text-warning">Ended early</span>}
            </div>
          </div>

          <div className="flex flex-col items-end gap-2">
            {isInsufficientSignal(evaluation) ? (
              <div className="flex max-w-[75ch] flex-col items-end gap-3 text-right">
                <h2 className="font-display text-[40px] font-normal leading-[1.08] text-foreground">
                  Limited evidence result
                </h2>
                <Badge variant={verdictBadgeVariant(narrative.overallVerdict)}>
                  {verdictLabel(narrative.overallVerdict)}
                </Badge>
                <p className="max-w-prose text-base leading-relaxed text-foreground-muted">
                  There was not enough evidence to calculate a reliable score. Review the verdict
                  and cited feedback below.
                </p>
              </div>
            ) : (
              <>
                <div className="flex items-center gap-3">
                  <span className="text-5xl font-bold tabular-nums text-accent">
                    {overallScore}
                  </span>
                  <Badge variant={verdictBadgeVariant(narrative.overallVerdict)}>
                    {verdictLabel(narrative.overallVerdict)}
                  </Badge>
                </div>
                <span className="text-sm text-foreground-muted">Overall Score</span>
              </>
            )}
          </div>
        </header>

        <Separator className="my-6" />

        <EvaluationLimitations evaluation={evaluation} competencyLabelMap={competencyLabelMap} />

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-6">
          <TabsList variant="line">
            <TabsTrigger value="evaluation">Evaluation</TabsTrigger>
            <TabsTrigger value="transcript">Transcript</TabsTrigger>
            <TabsTrigger value="decision-log">Decision Log</TabsTrigger>
          </TabsList>

          {/* --- Evaluation tab --- */}
          <TabsContent value="evaluation" className="mt-6 space-y-8">
            {/* Competency scores */}
            <section>
              <h2 className="mb-4 text-lg font-semibold text-foreground">Competency Scores</h2>
              <div className="grid gap-4 sm:grid-cols-2">
                {competencyScores.map((cs) => (
                  <CompetencyScoreCard key={cs.competencyId} competencyScore={cs} />
                ))}
              </div>
            </section>

            <Separator />

            {/* Narrative */}
            <section className="grid gap-8 sm:grid-cols-2">
              <NarrativeSection
                title="Strengths"
                items={narrative.strengths}
                variant="positive"
                turnLookup={turnLookup}
                onEvidenceClick={jumpToTurn}
                nullScore={nullScore}
              />
              <NarrativeSection
                title="Areas for Improvement"
                items={narrative.concerns}
                variant="negative"
                turnLookup={turnLookup}
                onEvidenceClick={jumpToTurn}
                nullScore={nullScore}
              />
            </section>
          </TabsContent>

          {/* --- Transcript tab --- */}
          <TabsContent value="transcript" className="mt-6">
            <ScrollArea className="h-[600px] pr-4">
              <div className="space-y-6">
                {turns.map((turn) => (
                  <TranscriptTurn
                    key={turn.id}
                    turn={turn}
                    isHighlighted={highlightedTurnId === turn.id}
                    competencyLabel={
                      turn.competencyId ? competencyLabelMap.get(turn.competencyId) : undefined
                    }
                    registerTurnRef={registerTurnRef}
                  />
                ))}
              </div>
            </ScrollArea>
          </TabsContent>

          {/* --- Decision Log tab --- */}
          <TabsContent value="decision-log" className="mt-6">
            <div className="space-y-6">
              {reasonedTurns.map((turn) => (
                <div key={turn.id} className="rounded-lg border border-border p-4">
                  <h3 className="mb-3 text-sm font-medium text-foreground">
                    Turn {turn.turnIndex + 1}
                  </h3>
                  <PanelRenderer
                    panelState={turn.reasoning}
                    competencies={competencies}
                    mode="replay"
                  />
                </div>
              ))}

              {reasonedTurns.length === 0 && (
                <p className="text-sm italic text-foreground-muted">
                  No decision reasoning recorded for this session.
                </p>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
