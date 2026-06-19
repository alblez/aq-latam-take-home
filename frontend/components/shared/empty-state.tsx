"use client";

import type { ReactNode } from "react";
import { Button } from "@/components/ui/button";

type EmptyStateProps = Readonly<{
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: { label: string; href?: string; onClick?: () => void };
}>;

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center px-4 py-12 text-center">
      {icon && (
        <div className="mb-4 flex size-12 items-center justify-center text-[var(--color-foreground-muted)]">
          {icon}
        </div>
      )}

      <h3 className="mb-1 text-lg font-semibold text-[var(--color-foreground)]">{title}</h3>

      {description && (
        <p className="mb-6 max-w-[44ch] text-sm text-[var(--color-foreground-muted)]">
          {description}
        </p>
      )}

      {action?.onClick && (
        <Button variant="primary" onClick={action.onClick}>
          {action.label}
        </Button>
      )}
      {action?.href && !action.onClick && (
        <a
          href={action.href}
          className="inline-flex h-10 items-center justify-center gap-2 whitespace-nowrap rounded-md bg-[var(--color-accent)] px-[18px] text-sm font-medium text-[var(--color-background)] transition-all duration-150 hover:brightness-110 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-accent)]"
        >
          {action.label}
        </a>
      )}
    </div>
  );
}
