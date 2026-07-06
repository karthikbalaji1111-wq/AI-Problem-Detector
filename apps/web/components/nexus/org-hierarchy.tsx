import { Bot, ChevronRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { HierarchyNode } from "@/lib/types";

function Node({ node, depth = 0 }: { node: HierarchyNode; depth?: number }) {
  return (
    <div>
      <div
        className="flex items-center gap-2 rounded-md border border-white/8 bg-white/5 px-2 py-2"
        style={{ marginLeft: depth * 14 }}
      >
        <Bot className="h-4 w-4 shrink-0 text-cyan" />
        <div className="min-w-0 flex-1">
          <div className="truncate text-sm font-medium">{node.agent.name}</div>
          <div className="truncate text-xs text-muted">{node.agent.mission}</div>
        </div>
        <Badge tone={node.agent.status === "active" ? "green" : "neutral"}>{node.agent.status}</Badge>
      </div>
      {node.children.length > 0 && (
        <div className="mt-2 space-y-2">
          {node.children.map((child) => (
            <Node key={child.agent.id} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

export function OrgHierarchy({ hierarchy }: { hierarchy: HierarchyNode[] }) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ChevronRight className="h-4 w-4 text-cyan" />
          Organization Hierarchy
        </CardTitle>
      </CardHeader>
      <CardContent className="max-h-[520px] space-y-2 overflow-auto">
        {hierarchy.map((node) => (
          <Node key={node.agent.id} node={node} />
        ))}
      </CardContent>
    </Card>
  );
}

