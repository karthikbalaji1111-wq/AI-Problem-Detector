import { Brain, Cpu, Database, Repeat, Shield } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Agent } from "@/lib/types";

const policyIcons = [
  ["Memory", Brain],
  ["Planning", Cpu],
  ["Reflection", Repeat],
  ["Evaluation", Shield],
  ["Tools", Database]
] as const;

export function MemoryExplorer({ agents }: { agents: Agent[] }) {
  const featured = agents.slice(0, 6);
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="h-4 w-4 text-cyan" />
          Memory Explorer
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {featured.map((agent) => (
          <div key={agent.id} className="rounded-md border border-white/10 bg-white/5 p-3">
            <div className="flex items-start justify-between gap-2">
              <div>
                <div className="text-sm font-medium">{agent.name}</div>
                <p className="mt-1 line-clamp-3 text-xs leading-5 text-muted">{agent.mission}</p>
              </div>
              <Badge tone="cyan">{Math.round(agent.confidence_floor * 100)}</Badge>
            </div>
            <div className="mt-3 grid grid-cols-5 gap-2">
              {policyIcons.map(([label, Icon]) => (
                <div
                  key={label}
                  title={label}
                  className="flex h-8 items-center justify-center rounded-md border border-white/10 bg-black/20"
                >
                  <Icon className="h-4 w-4 text-muted" />
                </div>
              ))}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

