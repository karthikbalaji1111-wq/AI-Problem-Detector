import { Activity, Radio } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { compactDate, percent } from "@/lib/utils";
import type { AgentMessage, Analytics } from "@/lib/types";

export function ActivityFeed({
  analytics,
  streamedMessages
}: {
  analytics?: Analytics;
  streamedMessages: AgentMessage[];
}) {
  const timeline = streamedMessages.length
    ? streamedMessages.map((message) => ({
        id: message.id,
        type: message.message_type,
        content: message.content,
        confidence: message.confidence,
        created_at: message.created_at
      }))
    : analytics?.timeline || [];

  return (
    <Card className="h-full">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-cyan" />
          Live Agent Activity
        </CardTitle>
        <Badge tone="green" className="gap-1">
          <Radio className="h-3 w-3" />
          live
        </Badge>
      </CardHeader>
      <CardContent className="max-h-[430px] space-y-3 overflow-auto">
        {timeline.length === 0 && (
          <div className="rounded-md border border-white/10 bg-white/5 p-3 text-sm text-muted">
            Start a workforce run to watch agents plan, delegate, critique, verify, and execute.
          </div>
        )}
        {timeline.map((item) => (
          <div key={item.id} className="rounded-md border border-white/10 bg-white/5 p-3">
            <div className="mb-2 flex items-center justify-between gap-3">
              <Badge tone={item.type === "critique" ? "amber" : item.type === "verification" ? "coral" : "cyan"}>
                {item.type}
              </Badge>
              <span className="text-xs text-muted">{compactDate(item.created_at)}</span>
            </div>
            <p className="text-sm leading-6 text-foreground">{item.content}</p>
            <div className="mt-3 flex items-center gap-3">
              <Progress value={item.confidence} className="flex-1" />
              <span className="w-10 text-right text-xs text-muted">{percent(item.confidence)}</span>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

