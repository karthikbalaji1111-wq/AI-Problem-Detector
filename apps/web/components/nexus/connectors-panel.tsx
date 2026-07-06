import {
  CalendarDays,
  Cloud,
  Database,
  Github,
  Mail,
  MapPinned,
  MessageSquare,
  Newspaper,
  Phone
} from "lucide-react";
import type { ComponentType } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Connector } from "@/lib/types";

const iconByConnector: Record<string, ComponentType<{ className?: string }>> = {
  slack: MessageSquare,
  discord: MessageSquare,
  teams: MessageSquare,
  gmail: Mail,
  google_calendar: CalendarDays,
  github: Github,
  jira: Cloud,
  linear: Cloud,
  notion: Cloud,
  drive: Cloud,
  dropbox: Cloud,
  weather: Cloud,
  news: Newspaper,
  twilio: Phone,
  maps: MapPinned,
  supabase: Database,
  pinecone: Database,
  qdrant: Database,
  postgres: Database
};

export function ConnectorsPanel({ connectors }: { connectors: Connector[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Cloud className="h-4 w-4 text-cyan" />
          Tool Mesh
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
        {connectors.map((connector) => {
          const Icon = iconByConnector[connector.connector_key] || Cloud;
          return (
            <div key={connector.connector_key} className="rounded-md border border-white/10 bg-white/5 p-3">
              <div className="flex items-center justify-between gap-2">
                <div className="flex min-w-0 items-center gap-2">
                  <Icon className="h-4 w-4 shrink-0 text-cyan" />
                  <span className="truncate text-sm font-medium">{connector.connector_key}</span>
                </div>
                <Badge tone={connector.configured ? "green" : "neutral"}>
                  {connector.configured ? "ready" : "env"}
                </Badge>
              </div>
              <p className="mt-2 line-clamp-2 text-xs text-muted">{connector.actions.join(", ")}</p>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
