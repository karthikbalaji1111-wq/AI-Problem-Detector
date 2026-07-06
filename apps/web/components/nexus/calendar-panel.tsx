import { CalendarDays } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Task } from "@/lib/types";
import { compactDate } from "@/lib/utils";

export function CalendarPanel({ tasks }: { tasks: Task[] }) {
  const scheduled = tasks.filter((task) => task.due_at).slice(0, 6);
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CalendarDays className="h-4 w-4 text-cyan" />
          Calendar
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {scheduled.length === 0 && (
          <div className="rounded-md border border-white/10 bg-white/5 p-3 text-sm text-muted">
            Agent-owned due dates appear here as the workforce plans work.
          </div>
        )}
        {scheduled.map((task) => (
          <div key={task.id} className="flex items-center justify-between gap-3 rounded-md border border-white/10 bg-white/5 p-3">
            <div className="min-w-0">
              <div className="truncate text-sm font-medium">{task.title}</div>
              <div className="text-xs text-muted">{task.due_at ? compactDate(task.due_at) : ""}</div>
            </div>
            <Badge tone={task.status === "done" ? "green" : "amber"}>{task.status}</Badge>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

