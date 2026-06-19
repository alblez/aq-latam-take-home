import { forwardRef, type HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export const Skeleton = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => {
    return (
      <div
        ref={ref}
        aria-hidden="true"
        className={cn("animate-skeleton rounded-md bg-border", className)}
        {...props}
      />
    );
  },
);

Skeleton.displayName = "Skeleton";
