import type { LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export function MetricCard({
  label,
  value,
  detail,
  icon: Icon,
  tone = "cyan"
}: {
  label: string;
  value: string | number;
  detail: string;
  icon: LucideIcon;
  tone?: "cyan" | "amber" | "coral" | "green" | "neutral";
}) {
  return (
    <Card>
      <CardContent className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs text-muted">{label}</p>
          <div className="mt-2 text-2xl font-semibold tracking-normal text-foreground">{value}</div>
          <p className="mt-1 text-xs text-muted">{detail}</p>
        </div>
        <Badge tone={tone} className="h-9 w-9 justify-center px-0">
          <Icon className="h-4 w-4" />
        </Badge>
      </CardContent>
    </Card>
  );
}

