import { FileSearch, GitBranch } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { compactDate, percent } from "@/lib/utils";
import type { Analytics } from "@/lib/types";

export function TracingPanel({ analytics }: { analytics?: Analytics }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <GitBranch className="h-4 w-4 text-cyan" />
          Traces and Logs
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3 lg:grid-cols-2">
        <div className="space-y-2">
          {(analytics?.traces || []).slice(0, 5).map((trace) => (
            <div key={trace.id} className="rounded-md border border-white/10 bg-white/5 p-3">
              <div className="flex items-center justify-between gap-2">
                <Badge tone={trace.status === "succeeded" ? "green" : trace.status === "waiting_approval" ? "amber" : "cyan"}>
                  {trace.status}
                </Badge>
                <span className="text-xs text-muted">{compactDate(trace.created_at)}</span>
              </div>
              <div className="mt-2 font-mono text-xs text-muted">{trace.trace_id}</div>
              <div className="mt-2 text-xs text-muted">
                Confidence {percent(trace.confidence)} · Risk {percent(trace.risk_score)}
              </div>
            </div>
          ))}
        </div>
        <div className="space-y-2">
          {(analytics?.logs || []).slice(0, 6).map((log) => (
            <div key={log.id} className="flex items-start gap-2 rounded-md border border-white/10 bg-white/5 p-3">
              <FileSearch className="mt-0.5 h-4 w-4 shrink-0 text-cyan" />
              <div className="min-w-0">
                <div className="truncate text-sm font-medium">{log.action}</div>
                <div className="text-xs text-muted">
                  {log.actor_type} · {compactDate(log.created_at)}
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

