"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { cn } from "@/lib/utils";
import type { CompetencyCoverage, CompetencyStatus } from "@/types/competency";
import type { PanelState, TerminalPanelState } from "@/types/turn";

// --- Pure helpers (exported for testability) ---

/** Build a Map from competency UUID → display name */
export function buildNameMap(competencies: CompetencyStatus[]): Map<string, string> {
  return new Map(competencies.map((c) => [c.id, c.name]));
}

/** Row shape for the coverage section */
export type CoverageRow = { name: string; coverage: CompetencyCoverage };

/** Resolve rubricSnapshot UUID arrays into named coverage rows */
export function coverageRows(
  rubricSnapshot: PanelState["rubricSnapshot"],
  nameMap: Map<string, string>,
): CoverageRow[] {
  const resolve = (id: string) => nameMap.get(id) ?? id;
  const rows: CoverageRow[] = [];
  for (const id of rubricSnapshot.covered) {
    rows.push({ name: resolve(id), coverage: "covered" });
  }
  for (const id of rubricSnapshot.inProgress) {
    rows.push({ name: resolve(id), coverage: "in-progress" });
  }
  for (const id of rubricSnapshot.gaps) {
    rows.push({ name: resolve(id), coverage: "not-reached" });
  }
  return rows;
}

/** Extract follow-up budget info from policyState */
export function budgetInfo(policyState: PanelState["policyState"]): {
  followUpCount: number;
  maxFollowUpsPerCompetency: number;
  eligibleToEnd: boolean;
} {
  return {
    followUpCount: policyState.followUpCount,
    maxFollowUpsPerCompetency: policyState.maxFollowUpsPerCompetency,
    eligibleToEnd: policyState.eligibleToEnd,
  };
}

/** Replay-only fields with explicit null guards (Pitfall 4) */
export function replayFields(panelState: PanelState): {
  generation: PanelState["generation"];
  trigger: PanelState["trigger"];
  failureMode: string | null;
  sourcePackItemId: string | null;
} {
  return {
    generation: panelState.generation,
    trigger: panelState.trigger !== null ? panelState.trigger : null,
    failureMode: panelState.failureMode !== null ? panelState.failureMode : null,
    sourcePackItemId: panelState.sourcePackItemId !== null ? panelState.sourcePackItemId : null,
  };
}

/** Resolve targetCompetencyId to a display name (or fallback to uuid/null) */
export function resolveTargetName(
  targetCompetencyId: string | null,
  nameMap: Map<string, string>,
): string | null {
  if (targetCompetencyId === null) return null;
  return nameMap.get(targetCompetencyId) ?? targetCompetencyId;
}

// --- Styling ---

const coverageStyles: Record<CompetencyCoverage, string> = {
  covered: "bg-success-muted text-success border border-transparent",
  "in-progress": "bg-warning-muted text-warning border border-transparent",
  "not-reached": "bg-surface text-foreground-muted border border-border",
};

// --- PanelRenderer: shared contract-typed renderer (D-08, D-09) ---

type PanelRendererProps = Readonly<{
  panelState: PanelState | TerminalPanelState | null;
  competencies: CompetencyStatus[];
  mode: "live" | "replay";
}>;

/** Shared renderer for contract PanelState — used by live panel and replay */
export function PanelRenderer({ panelState, competencies, mode }: PanelRendererProps) {
  if (!panelState) {
    return (
      <div className="flex h-full items-center justify-center p-6">
        <p className="text-sm text-foreground-muted">Waiting for first turn...</p>
      </div>
    );
  }

  const nameMap = buildNameMap(competencies);
  const rows = coverageRows(panelState.rubricSnapshot, nameMap);
  const budget = budgetInfo(panelState.policyState);
  const targetName = resolveTargetName(panelState.targetCompetencyId, nameMap);

  return (
    <ScrollArea className="h-full">
      <div className="flex flex-col gap-5 p-5">
        {/* Coverage grid */}
        <CoverageSection rows={rows} />

        <Separator />

        {/* Current flags */}
        <FlagsSection flags={panelState.flags} />

        <Separator />

        {/* Next action */}
        <ActionSection action={panelState.action} targetName={targetName} />

        <Separator />

        {/* Follow-up budget */}
        <BudgetSection budget={budget} />

        <Separator />

        {/* Rationale */}
        <RationaleSection rationale={panelState.rationale} />

        {/* Replay-only block (D-09/D-10) */}
        {mode === "replay" && <ReplaySection panelState={panelState} />}
      </div>
    </ScrollArea>
  );
}

// --- Section sub-components (extract for complexity budget) ---

function CoverageSection({ rows }: Readonly<{ rows: CoverageRow[] }>) {
  return (
    <section>
      <h3 className="mb-3 text-xs font-medium tracking-wider uppercase text-foreground-muted">
        Coverage
      </h3>
      <div className="flex flex-col gap-2">
        {rows.map((row) => (
          <div key={row.name} className="flex items-center justify-between">
            <span className="text-sm text-foreground">{row.name}</span>
            <span
              className={cn(
                "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors duration-200",
                coverageStyles[row.coverage],
              )}
            >
              {row.coverage}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}

function FlagsSection({ flags }: Readonly<{ flags: PanelState["flags"] }>) {
  return (
    <section>
      <h3 className="mb-3 text-xs font-medium tracking-wider uppercase text-foreground-muted">
        Current Flags
      </h3>
      {flags.length > 0 ? (
        <div className="flex flex-col gap-2">
          {flags.map((flag) => (
            <div key={`${flag.flag}-${flag.detail.slice(0, 30)}`} className="flex flex-col gap-0.5">
              <Badge variant="default" className="w-fit font-mono text-xs">
                {flag.flag.replaceAll("_", " ")}
              </Badge>
              <span className="text-sm text-foreground-muted">{flag.detail}</span>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-foreground-muted">No active flags</p>
      )}
    </section>
  );
}

function ActionSection({
  action,
  targetName,
}: Readonly<{ action: PanelState["action"]; targetName: string | null }>) {
  return (
    <section>
      <h3 className="mb-3 text-xs font-medium tracking-wider uppercase text-foreground-muted">
        Next Action
      </h3>
      <div className="flex items-center gap-2">
        <Badge
          variant={action === "follow_up" ? "warning" : "default"}
          className="font-mono text-xs"
        >
          {action.replaceAll("_", " ")}
        </Badge>
        {targetName !== null && (
          <span className="text-xs text-foreground-muted">→ {targetName}</span>
        )}
      </div>
    </section>
  );
}

function BudgetSection({
  budget,
}: Readonly<{
  budget: { followUpCount: number; maxFollowUpsPerCompetency: number; eligibleToEnd: boolean };
}>) {
  const total = budget.maxFollowUpsPerCompetency;
  const used = budget.followUpCount;
  const pct = total > 0 ? Math.min((used / total) * 100, 100) : 0;

  return (
    <section>
      <h3 className="mb-3 text-xs font-medium tracking-wider uppercase text-foreground-muted">
        Follow-up Budget
      </h3>
      <div className="flex items-center gap-3">
        <div className="h-2 flex-1 overflow-hidden rounded-full bg-surface">
          <div
            className="h-full rounded-full bg-accent transition-all duration-300"
            style={{ width: `${pct}%` }}
          />
        </div>
        <span className="shrink-0 font-mono text-sm text-foreground-muted">
          {used}/{total} used
        </span>
      </div>
      {budget.eligibleToEnd && <p className="mt-1 text-xs text-success">Eligible to end</p>}
    </section>
  );
}

function RationaleSection({ rationale }: Readonly<{ rationale: string }>) {
  return (
    <section>
      <h3 className="mb-3 text-xs font-medium tracking-wider uppercase text-foreground-muted">
        Rationale
      </h3>
      <blockquote className="rounded-md bg-surface-elevated pl-3 pr-3 py-2 font-mono text-sm text-foreground-muted">
        {rationale}
      </blockquote>
    </section>
  );
}

function ReplaySection({ panelState }: Readonly<{ panelState: PanelState }>) {
  const fields = replayFields(panelState);

  return (
    <>
      <Separator />
      <section>
        <h3 className="mb-3 text-xs font-medium tracking-wider uppercase text-foreground-muted">
          Replay Details
        </h3>
        <div className="flex flex-col gap-2 text-sm">
          <div>
            <span className="text-foreground-muted">Generation: </span>
            <span className="font-mono text-foreground">{fields.generation.mode}</span>
            {fields.generation.fallbackMode !== null &&
              fields.generation.fallbackMode !== undefined && (
                <span className="text-foreground-muted">
                  {" "}
                  (fallback: {fields.generation.fallbackMode})
                </span>
              )}
          </div>

          {fields.failureMode !== null && (
            <div>
              <span className="text-foreground-muted">Failure Mode: </span>
              <span className="font-mono text-foreground">{fields.failureMode}</span>
            </div>
          )}

          {fields.trigger !== null && (
            <div className="flex flex-col gap-0.5">
              <span className="text-foreground-muted">Trigger:</span>
              <span className="font-mono text-xs text-foreground">
                &ldquo;{fields.trigger.answerExcerpt}&rdquo;
              </span>
              <span className="text-xs text-foreground-muted">{fields.trigger.reason}</span>
            </div>
          )}

          {fields.sourcePackItemId !== null && (
            <div>
              <span className="text-foreground-muted">Source Pack Item: </span>
              <span className="font-mono text-xs text-foreground">{fields.sourcePackItemId}</span>
            </div>
          )}
        </div>
      </section>
    </>
  );
}

// --- DecisionPanel shell (desktop aside + mobile Sheet) ---

type DecisionPanelProps = Readonly<{
  panelState: PanelState | TerminalPanelState | null;
  competencies: CompetencyStatus[];
  isOpen: boolean;
  onToggle: () => void;
}>;

export function DecisionPanel({ panelState, competencies, isOpen, onToggle }: DecisionPanelProps) {
  return (
    <>
      {/* Desktop sidebar */}
      <aside
        className={cn(
          "hidden lg:flex fixed right-0 top-14 bottom-0 w-80 flex-col border-l border-border bg-surface z-30 transition-transform duration-300 ease-in-out",
          isOpen ? "translate-x-0" : "translate-x-full",
        )}
      >
        <div className="flex h-14 shrink-0 items-center justify-between border-b border-border px-5">
          <h2 className="text-sm font-semibold text-foreground">Decision Panel</h2>
          <Button variant="ghost" size="sm" onClick={onToggle}>
            <ChevronIcon className={cn("size-4", isOpen && "rotate-180")} />
          </Button>
        </div>
        <PanelRenderer panelState={panelState} competencies={competencies} mode="live" />
      </aside>

      {/* Mobile sheet */}
      <div className="lg:hidden">
        <Sheet>
          <SheetTrigger asChild>
            <Button variant="secondary" size="sm" className="fixed bottom-4 right-4 z-40">
              Panel
            </Button>
          </SheetTrigger>
          <SheetContent side="bottom" className="h-[70vh]">
            <SheetHeader>
              <SheetTitle>Decision Panel</SheetTitle>
            </SheetHeader>
            <div className="flex-1 overflow-hidden">
              <PanelRenderer panelState={panelState} competencies={competencies} mode="live" />
            </div>
          </SheetContent>
        </Sheet>
      </div>

      {/* Desktop toggle button (when panel is closed) */}
      {!isOpen && (
        <Button
          variant="secondary"
          size="sm"
          onClick={onToggle}
          className="hidden lg:flex fixed right-4 top-16 z-40 gap-1.5"
        >
          Panel
          <ChevronIcon className="size-3.5" />
        </Button>
      )}
    </>
  );
}

function ChevronIcon({ className }: Readonly<{ className?: string }>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="m9 18 6-6-6-6" />
    </svg>
  );
}
