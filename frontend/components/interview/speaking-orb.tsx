"use client";

import { cn } from "@/lib/utils";

export type OrbState = "static" | "pulse" | "active";

type SpeakingOrbProps = Readonly<{
  state: OrbState;
  size?: "default" | "large";
}>;

const stateLabels: Record<OrbState, string> = {
  static: "Ready",
  pulse: "Thinking",
  active: "Speaking",
};

/**
 * Ring animation config per state.
 * Use project CSS classes so keyframes ship with globals.css reliably.
 */
const ringAnimation = {
  static: "",
  pulse: "orb-animate-think",
  active: "orb-animate-speak",
} as const;

const stateClass: Record<OrbState, string> = {
  static: "orb-state-static",
  pulse: "orb-state-pulse",
  active: "orb-state-active",
};

const rings = [
  { name: "outer", className: "orb-ring orb-ring-outer", delay: "0ms" },
  { name: "middle", className: "orb-ring orb-ring-middle", delay: "140ms" },
] as const;

export function SpeakingOrb({ state, size = "default" }: SpeakingOrbProps) {
  const dimension = size === "large" ? "size-[180px]" : "size-[120px]";
  const isActive = state !== "static";

  return (
    <output
      aria-label={`AI interviewer: ${stateLabels[state]}`}
      className="flex flex-col items-center gap-3"
    >
      <div
        aria-hidden="true"
        className={cn("relative isolate rounded-full", dimension, stateClass[state])}
      >
        {rings.map((ring) => (
          <span
            key={ring.name}
            className={cn(ring.className, isActive && ringAnimation[state])}
            style={isActive ? { animationDelay: ring.delay } : undefined}
          />
        ))}
      </div>

      <span
        aria-hidden="true"
        className="font-mono text-xs font-medium uppercase tracking-[0.12em] text-foreground-muted"
      >
        {stateLabels[state]}
      </span>
      <span className="sr-only">{stateLabels[state]}</span>
    </output>
  );
}
