import { Columns3 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Task } from "@/lib/types";

const columns = [
  ["backlog", "Backlog"],
  ["planning", "Planning"],
  ["in_progress", "Active"],
  ["review", "Review"],
  ["done", "Done"],
  ["blocked", "Blocked"]
] as const;

const toneByStatus: Record<string, "neutral" | "cyan" | "amber" | "green" | "coral"> = {
  backlog: "neutral",
  planning: "cyan",
  in_progress: "amber",
  review: "coral",
  done: "green",
  blocked: "coral"
};

export function TaskKanban({ tasks }: { tasks: Task[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Columns3 className="h-4 w-4 text-cyan" />
          Task Graph
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
          {columns.map(([status, label]) => {
            const columnTasks = tasks.filter((task) => task.status === status);
            return (
              <div key={status} className="min-h-40 rounded-lg border border-white/10 bg-white/5 p-2">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-xs font-medium text-muted">{label}</span>
                  <Badge tone={toneByStatus[status]}>{columnTasks.length}</Badge>
                </div>
                <div className="space-y-2">
                  {columnTasks.slice(0, 4).map((task) => (
                    <div key={task.id} className="rounded-md border border-white/10 bg-black/20 p-2">
                      <div className="line-clamp-2 text-xs font-medium">{task.title}</div>
                      <p className="mt-1 line-clamp-3 text-xs text-muted">{task.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

