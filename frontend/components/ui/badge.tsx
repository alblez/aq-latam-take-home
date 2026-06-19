import { forwardRef, type HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type BadgeVariant = "default" | "accent" | "success" | "warning" | "muted";

type BadgeProps = Readonly<
  HTMLAttributes<HTMLSpanElement> & {
    variant?: BadgeVariant;
  }
>;

const variantStyles: Record<BadgeVariant, string> = {
  default: "bg-surface-elevated text-foreground border border-border",
  accent: "bg-accent-muted text-accent-foreground",
  success: "bg-success-muted text-success",
  warning: "bg-warning-muted text-warning",
  muted: "bg-surface text-foreground-muted border border-border",
};

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = "default", ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={cn(
          "inline-flex items-center rounded-full px-3 py-xs text-xs font-medium leading-[1.4] tracking-[0.02em]",
          variantStyles[variant],
          className,
        )}
        {...props}
      />
    );
  },
);

Badge.displayName = "Badge";
