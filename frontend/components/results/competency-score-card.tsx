"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { CompetencyScore } from "@/types/evaluation";
import { ScoreBar } from "./score-bar";

export function CompetencyScoreCard({
  competencyScore,
}: Readonly<{ competencyScore: CompetencyScore }>) {
  const { name, category, score, assessed, notes } = competencyScore;

  return (
    <div className={cn("rounded-lg border border-border p-4", !assessed && "opacity-60")}>
      <div className="mb-3 flex items-center justify-between gap-3">
        <h3 className="font-semibold text-foreground">{name}</h3>
        <Badge variant="accent">{category}</Badge>
      </div>

      {assessed && score !== null ? (
        <ScoreBar score={score} />
      ) : (
        <div className="flex items-center gap-2">
          <span className="text-sm text-foreground-muted">Not assessed</span>
        </div>
      )}

      {notes && <p className="mt-2 text-sm text-foreground-muted">{notes}</p>}
    </div>
  );
}
