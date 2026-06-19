"use client";

import { Button } from "@/components/ui/button";

type DoneButtonProps = Readonly<{
  onClick: () => void;
  disabled: boolean;
}>;

export function DoneButton({ onClick, disabled }: DoneButtonProps) {
  return (
    <div className="flex flex-col items-center gap-1">
      <Button
        variant="primary"
        size="lg"
        onClick={onClick}
        disabled={disabled}
        className="min-w-[180px] px-8"
      >
        I&apos;m Done
      </Button>
      <span className="text-xs text-foreground-muted">Ctrl+Enter to submit</span>
    </div>
  );
}
