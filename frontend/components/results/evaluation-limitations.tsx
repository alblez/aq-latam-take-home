"use client";

import { Clock } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { buildLimitations } from "@/lib/results/limitations";
import { cn } from "@/lib/utils";
import type { Evaluation } from "@/types/evaluation";

// --- Severity-to-component mapping ---

const badgeVariantByKind = {
  info: "muted",
  warning: "warning",
  muted: "muted",
} as const;

const textColorByKind = {
  info: "text-foreground",
  warning: "text-warning",
  muted: "text-foreground-muted",
} as const;

type LimitationKind = keyof typeof badgeVariantByKind;

// --- Component ---

type EvaluationLimitationsProps = Readonly<{
  evaluation: Evaluation;
  competencyLabelMap: Map<string, string>;
}>;

export function EvaluationLimitations({
  evaluation,
  competencyLabelMap,
}: EvaluationLimitationsProps) {
  const limitations = buildLimitations(evaluation, competencyLabelMap);

  if (limitations.length === 0) {
    return null;
  }

  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <h2 className="mb-3 text-xl font-semibold leading-[1.3] text-foreground">
        Evaluation limitations
      </h2>

      <ul className="space-y-2">
        {limitations.map((limitation, _idx) => {
          const kind = limitation.kind as LimitationKind;
          const isEarlyEnd = limitation.kind === "info";
          const isUnresolved = limitation.unresolved === true;

          return (
            <li key={`${limitation.kind}-${limitation.text}`} className="flex items-start gap-2">
              {isEarlyEnd && (
                <Clock
                  className="mt-0.5 h-4 w-4 shrink-0 text-foreground-muted"
                  aria-hidden="true"
                />
              )}
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={badgeVariantByKind[kind]}>{limitation.label}</Badge>
                <span
                  className={cn(
                    "text-base leading-relaxed",
                    textColorByKind[kind],
                    isUnresolved && "font-mono",
                  )}
                >
                  {limitation.text}
                </span>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
