import * as React from "react";
import { cn } from "@/lib/utils";

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "h-10 w-full rounded-md border border-white/10 bg-white/6 px-3 text-sm text-foreground outline-none transition placeholder:text-muted focus:border-cyan/50 focus:ring-2 focus:ring-cyan/20",
        className
      )}
      {...props}
    />
  )
);
Input.displayName = "Input";

export const Textarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        "min-h-24 w-full rounded-md border border-white/10 bg-white/6 px-3 py-2 text-sm text-foreground outline-none transition placeholder:text-muted focus:border-cyan/50 focus:ring-2 focus:ring-cyan/20",
        className
      )}
      {...props}
    />
  )
);
Textarea.displayName = "Textarea";

