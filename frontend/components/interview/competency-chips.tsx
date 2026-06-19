"use client";

import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import type { CompetencyCoverage, CompetencyStatus } from "@/types/competency";

const coverageStyles: Record<CompetencyCoverage, string> = {
  covered: "bg-[var(--color-success-muted)] text-[var(--color-success)] border border-transparent",
  "in-progress":
    "bg-[var(--color-warning-muted)] text-[var(--color-warning)] border border-transparent",
  "not-reached":
    "bg-[var(--color-surface)] text-[var(--color-foreground-muted)] border border-[var(--color-border)]",
};

type CompetencyChipsProps = Readonly<{
  competencies: CompetencyStatus[];
}>;

export function CompetencyChips({ competencies }: CompetencyChipsProps) {
  if (competencies.length === 0) {
    return (
      <div className="flex items-center gap-2 py-1">
        {[20, 24, 16, 28].map((w) => (
          <Skeleton key={w} className={`h-[34px] w-${w} shrink-0 rounded-full`} />
        ))}
        <output className="sr-only">Loading competency data...</output>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <ScrollArea className="w-full">
        <div className="flex items-center gap-2 py-1">
          {competencies.map((cs) => (
            <Tooltip key={cs.id}>
              <TooltipTrigger asChild>
                <span
                  className={cn(
                    "inline-flex shrink-0 items-center rounded-full px-3 py-2 text-xs font-medium transition-colors duration-200 ease-in-out min-h-[44px]",
                    coverageStyles[cs.status],
                  )}
                >
                  {cs.name}
                </span>
              </TooltipTrigger>
              <TooltipContent>
                <p className="max-w-xs text-xs">{cs.category}</p>
              </TooltipContent>
            </Tooltip>
          ))}
        </div>
        <ScrollBar orientation="horizontal" />
      </ScrollArea>
    </TooltipProvider>
  );
}
