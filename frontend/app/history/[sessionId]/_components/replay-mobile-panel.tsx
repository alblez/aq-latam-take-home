"use client";

import { PanelRenderer } from "@/components/interview/decision-panel";
import type { CompetencyStatus } from "@/types/competency";
import type { PanelState } from "@/types/turn";

type ReplayMobilePanelProps = Readonly<{
  panelState: PanelState | null;
  competencies: CompetencyStatus[];
}>;

export function ReplayMobilePanel({ panelState, competencies }: ReplayMobilePanelProps) {
  return (
    <div className="border-t border-[var(--color-border)] p-4 pb-20 lg:hidden">
      <h2 className="mb-4 text-xs font-semibold uppercase tracking-wider text-[var(--color-foreground-muted)]">
        Decision Panel
      </h2>
      <PanelRenderer panelState={panelState} competencies={competencies} mode="replay" />
    </div>
  );
}
