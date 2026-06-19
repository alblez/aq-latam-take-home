"use client";

import { cn } from "@/lib/utils";

type ThinkingIndicatorProps = Readonly<{
  isVisible: boolean;
}>;

export function ThinkingIndicator({ isVisible }: ThinkingIndicatorProps) {
  if (!isVisible) return null;

  return (
    <output aria-label="Loading next question" className="flex flex-col items-center gap-3">
      {/* Dots */}
      <div className="flex items-center gap-2">
        {[0, 200, 400].map((delay) => (
          <span
            key={delay}
            className={cn(
              "size-2 rounded-full bg-accent",
              "animate-[thinking-dot_1.4s_ease-in-out_infinite]",
            )}
            style={{ animationDelay: `${delay}ms` }}
          />
        ))}
      </div>

      {/* Label */}
      <p className="text-sm text-foreground-muted">Preparing next question...</p>
    </output>
  );
}
