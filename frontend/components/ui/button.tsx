import { type ButtonHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils";

type ButtonVariant = "primary" | "secondary" | "outline" | "ghost" | "destructive";
type ButtonSize = "sm" | "default" | "lg";

type ButtonProps = Readonly<
  ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: ButtonVariant;
    size?: ButtonSize;
  }
>;

const variantStyles: Record<ButtonVariant, string> = {
  primary: "bg-accent text-background font-medium hover:brightness-110 active:brightness-95",
  secondary: "bg-surface text-foreground border border-border hover:bg-surface-elevated",
  outline: "bg-transparent text-foreground border border-border hover:bg-surface",
  ghost: "bg-transparent text-foreground hover:bg-surface",
  destructive: "bg-destructive text-background font-medium hover:brightness-110",
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: "h-8 px-3 text-sm rounded-md relative after:absolute after:inset-y-[-6px] after:inset-x-0 after:content-['']",
  default:
    "h-10 px-[18px] text-sm rounded-md relative after:absolute after:inset-y-[-2px] after:inset-x-0 after:content-['']",
  lg: "h-12 px-6 text-base rounded-md",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "default", ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center gap-2 whitespace-nowrap transition-[color,background-color,border-color,box-shadow,opacity,filter] duration-150 ease-[cubic-bezier(0.16,1,0.3,1)]",
          "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
          "disabled:pointer-events-none disabled:opacity-50",
          variantStyles[variant],
          sizeStyles[size],
          className,
        )}
        {...props}
      />
    );
  },
);

Button.displayName = "Button";
