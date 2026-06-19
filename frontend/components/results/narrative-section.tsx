"use client";

import { Button } from "@/components/ui/button";
import { evidenceChipLabel, getUsableTurnIds } from "@/lib/results/evidence";
import { cn } from "@/lib/utils";
import type { Turn } from "@/types/turn";

type NarrativeItem = { competencyId: string; text: string; turnIds: string[] };

type NarrativeSectionProps = Readonly<{
  title: string;
  items: NarrativeItem[];
  variant?: "positive" | "negative";
  turnLookup?: Map<string, Turn>;
  onEvidenceClick?: (turnId: string) => void;
  nullScore?: boolean;
}>;

export function NarrativeSection({
  title,
  items,
  variant = "positive",
  turnLookup,
  onEvidenceClick,
  nullScore,
}: NarrativeSectionProps) {
  const dotColor = variant === "positive" ? "text-success" : "text-warning";

  return (
    <div>
      <h3 className="mb-3 text-lg font-semibold text-foreground">{title}</h3>

      {nullScore && items.length > 0 && (
        <p className="mb-3 text-sm text-foreground-muted">
          Feedback below is based on the evidence available in this session.
        </p>
      )}

      {items.length === 0 ? (
        <p className="text-sm italic text-foreground-muted">No items</p>
      ) : (
        <ul className="space-y-2">
          {items.map((item) => {
            const usableIds =
              turnLookup && item.turnIds.length > 0
                ? getUsableTurnIds(item.turnIds, turnLookup)
                : [];

            return (
              <li key={item.competencyId} className="flex items-start gap-2.5">
                <span
                  className={cn("mt-1.5 block size-1.5 shrink-0 rounded-full", dotColor)}
                  aria-hidden="true"
                />
                <div className="flex flex-col gap-sm">
                  <span className="text-base leading-relaxed text-foreground">{item.text}</span>
                  {usableIds.length > 0 && turnLookup && onEvidenceClick && (
                    <div className="flex flex-wrap gap-sm">
                      {usableIds.map((turnId) => {
                        const turn = turnLookup.get(turnId);
                        if (!turn) return null;
                        const label = evidenceChipLabel(turn);
                        return (
                          <Button
                            key={turnId}
                            variant="ghost"
                            size="sm"
                            aria-label={label.accessible}
                            onClick={() => onEvidenceClick(turnId)}
                          >
                            {label.visible}
                          </Button>
                        );
                      })}
                    </div>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
