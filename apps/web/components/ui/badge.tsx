import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type BadgeTone = "cyan" | "amber" | "coral" | "green" | "neutral";

const tones: Record<BadgeTone, string> = {
  cyan: "border-cyan/30 bg-cyan/12 text-cyan",
  amber: "border-amber/35 bg-amber/12 text-amber",
  coral: "border-coral/35 bg-coral/12 text-coral",
  green: "border-success/35 bg-success/12 text-success",
  neutral: "border-white/10 bg-white/8 text-muted"
};

export function Badge({
  tone = "neutral",
  className,
  children
}: {
  tone?: BadgeTone;
  className?: string;
  children: ReactNode;
}) {
  return (
    <span
      className={cn(
        "inline-flex h-6 items-center rounded-md border px-2 text-xs font-medium",
        tones[tone],
        className
      )}
    >
      {children}
    </span>
  );
}
