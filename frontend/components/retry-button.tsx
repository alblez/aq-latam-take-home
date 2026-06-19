"use client";

import { useRouter } from "next/navigation";

export function RetryButton() {
  const router = useRouter();

  return (
    <button
      type="button"
      onClick={() => router.refresh()}
      className="inline-flex h-10 items-center justify-center rounded-md border border-border bg-surface px-[18px] text-sm font-medium text-foreground transition-colors duration-150 hover:bg-surface-elevated focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent relative after:absolute after:inset-y-[-2px] after:inset-x-0 after:content-['']"
    >
      Try again
    </button>
  );
}
