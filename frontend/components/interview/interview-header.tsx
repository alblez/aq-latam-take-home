"use client";

import { CompetencyChips } from "@/components/interview/competency-chips";
import { Button } from "@/components/ui/button";
import type { CompetencyStatus } from "@/types/competency";
import type { InterviewPhase } from "@/types/session";

type InterviewHeaderProps = Readonly<{
  jobTitle: string;
  competencies: CompetencyStatus[];
  onEndInterview: () => void;
  state: InterviewPhase;
}>;

export function InterviewHeader({
  jobTitle,
  competencies,
  onEndInterview,
  state,
}: InterviewHeaderProps) {
  const showEndButton = state !== "welcome" && state !== "ended";

  return (
    <header className="sticky top-0 z-40 flex flex-col shrink-0 border-b border-[var(--color-border)] bg-[var(--color-background)]">
      <div className="flex h-14 items-center px-4">
        {/* Desktop layout */}
        <div className="hidden w-full items-center gap-4 md:flex">
          <h1 className="shrink-0 text-lg font-semibold text-[var(--color-foreground)]">
            {jobTitle}
          </h1>

          <div className="min-w-0 flex-1">
            <CompetencyChips competencies={competencies} />
          </div>

          {showEndButton && (
            <Button variant="destructive" size="sm" onClick={onEndInterview}>
              End
            </Button>
          )}
        </div>

        {/* Mobile layout */}
        <div className="flex w-full items-center justify-between md:hidden">
          <h1 className="truncate text-lg font-semibold text-[var(--color-foreground)]">
            {jobTitle}
          </h1>

          {showEndButton && (
            <Button variant="destructive" size="sm" onClick={onEndInterview}>
              End
            </Button>
          )}
        </div>
      </div>

      {/* Mobile chips row */}
      <div className="border-t border-[var(--color-border)] px-4 py-2 md:hidden">
        <CompetencyChips competencies={competencies} />
      </div>
    </header>
  );
}
