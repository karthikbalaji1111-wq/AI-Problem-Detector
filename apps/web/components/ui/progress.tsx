import { cn } from "@/lib/utils";

export function Progress({ value, className }: { value: number; className?: string }) {
  const width = Math.max(0, Math.min(100, Math.round(value * 100)));
  return (
    <div className={cn("h-2 overflow-hidden rounded-full bg-white/8", className)}>
      <div
        className="h-full rounded-full bg-gradient-to-r from-cyan via-success to-amber transition-all"
        style={{ width: `${width}%` }}
      />
    </div>
  );
}

