"use client";

import { PanelRenderer } from "@/components/interview/decision-panel";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { CompetencyStatus } from "@/types/competency";
import type { PanelState } from "@/types/turn";

type ReplayDecisionPanelProps = Readonly<{
  panelState: PanelState | null;
  competencies: CompetencyStatus[];
}>;

export function ReplayDecisionPanel({ panelState, competencies }: ReplayDecisionPanelProps) {
  return (
    <aside className="hidden w-80 shrink-0 flex-col lg:flex">
      <div className="flex h-12 items-center border-b border-[var(--color-border)] px-5">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-[var(--color-foreground-muted)]">
          Decision Panel
        </h2>
      </div>
      <ScrollArea className="h-[calc(100dvh-56px-48px-56px)]">
        <PanelRenderer panelState={panelState} competencies={competencies} mode="replay" />
      </ScrollArea>
    </aside>
  );
}
