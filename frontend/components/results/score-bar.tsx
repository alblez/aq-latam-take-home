"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

type ScoreBarProps = Readonly<{
  score: number;
  maxScore?: number;
  label?: string;
}>;

function getScoreColor(score: number): string {
  if (score <= 6) return "bg-destructive";
  if (score <= 8) return "bg-warning";
  return "bg-success";
}

export function ScoreBar({ score, maxScore = 10, label }: ScoreBarProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // Trigger animation on mount
    const id = requestAnimationFrame(() => setMounted(true));
    return () => cancelAnimationFrame(id);
  }, []);

  const percent = Math.min((score / maxScore) * 100, 100);

  return (
    <div className="flex flex-col gap-1.5">
      {label && <span className="text-xs font-medium text-foreground-muted">{label}</span>}
      <div className="flex items-center gap-3">
        <div className="relative h-2 w-full">
          <progress
            className="sr-only"
            value={score}
            max={maxScore}
            aria-label={label ?? "Score"}
          />
          <div className="h-full w-full overflow-hidden rounded-full bg-surface" aria-hidden="true">
            <div
              className={cn(
                "h-full rounded-full transition-all duration-500 ease-out",
                getScoreColor(score),
              )}
              style={{ width: mounted ? `${percent}%` : "0%" }}
            />
          </div>
        </div>
        <span className="shrink-0 font-mono text-sm font-medium text-foreground tabular-nums">
          {score}/{maxScore}
        </span>
      </div>
    </div>
  );
}
