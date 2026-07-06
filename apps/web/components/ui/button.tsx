import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex h-10 items-center justify-center gap-2 rounded-md border px-3 text-sm font-medium transition focus:outline-none focus:ring-2 focus:ring-cyan/40 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary: "border-cyan/40 bg-cyan text-slate-950 shadow-glow hover:bg-cyan/90",
        secondary: "border-white/10 bg-white/8 text-foreground hover:bg-white/12",
        ghost: "border-transparent bg-transparent text-muted hover:bg-white/8 hover:text-foreground",
        danger: "border-coral/50 bg-coral/15 text-coral hover:bg-coral/22"
      },
      size: {
        sm: "h-8 px-2 text-xs",
        md: "h-10 px-3",
        lg: "h-12 px-5"
      }
    },
    defaultVariants: {
      variant: "secondary",
      size: "md"
    }
  }
);

export type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants>;

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button className={cn(buttonVariants({ variant, size }), className)} ref={ref} {...props} />
  )
);
Button.displayName = "Button";

