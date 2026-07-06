"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import {
  Activity,
  Bell,
  Bot,
  Building2,
  Gauge,
  LogOut,
  Plus,
  ShieldAlert,
  Workflow
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Textarea } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { MetricCard } from "@/components/nexus/metric-card";
import { RiskMap } from "@/components/nexus/risk-map";
import { OrgHierarchy } from "@/components/nexus/org-hierarchy";
import { ActivityFeed } from "@/components/nexus/activity-feed";
import { TaskKanban } from "@/components/nexus/task-kanban";
import { ApprovalsPanel } from "@/components/nexus/approvals-panel";
import { ConnectorsPanel } from "@/components/nexus/connectors-panel";
import { MemoryExplorer } from "@/components/nexus/memory-explorer";
import { TracingPanel } from "@/components/nexus/tracing-panel";
import { CalendarPanel } from "@/components/nexus/calendar-panel";
import { WorkforceLauncher } from "@/components/nexus/workforce-launcher";
import { api } from "@/lib/api";
import { clearSession, getStoredToken } from "@/lib/auth";
import { streamRunMessages } from "@/lib/stream";
import type { Agent, AgentMessage, AgentRun, OrganizationDetail } from "@/lib/types";
import { percent } from "@/lib/utils";

function flattenAgents(detail?: OrganizationDetail) {
  const agents: Agent[] = [];
  const visit = (nodes: OrganizationDetail["hierarchy"]) => {
    for (const node of nodes) {
      agents.push(node.agent);
      visit(node.children);
    }
  };
  if (detail) visit(detail.hierarchy);
  return agents;
}

function CreateOrganization({
  token,
  onCreated
}: {
  token: string;
  onCreated: (detail: OrganizationDetail) => void;
}) {
  const [name, setName] = useState("Nexus Manufacturing");
  const [prompt, setPrompt] = useState(
    "Create a manufacturing company that predicts supply chain risk, coordinates production, and improves customer delivery reliability."
  );
  const create = useMutation({
    mutationFn: () => api.createOrganization(token, prompt, name),
    onSuccess: onCreated
  });

  function submit(event: FormEvent) {
    event.preventDefault();
    create.mutate();
  }

  return (
    <main className="nexus-grid flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-4 w-4 text-cyan" />
            Create Autonomous Organization
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="space-y-3">
            <Input value={name} onChange={(event) => setName(event.target.value)} />
            <Textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} />
            <Button type="submit" variant="primary" disabled={create.isPending}>
              <Plus className="h-4 w-4" />
              {create.isPending ? "Generating workforce" : "Generate workforce"}
            </Button>
            {create.error && <p className="text-xs text-coral">{create.error.message}</p>}
          </form>
        </CardContent>
      </Card>
    </main>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [token, setToken] = useState<string | null>(null);
  const [selectedOrgId, setSelectedOrgId] = useState<string | null>(null);
  const [activeRun, setActiveRun] = useState<AgentRun | null>(null);
  const [streamedMessages, setStreamedMessages] = useState<AgentMessage[]>([]);
  const [streamStatus, setStreamStatus] = useState<string | null>(null);

  useEffect(() => {
    const stored = getStoredToken();
    if (!stored) {
      router.push("/login");
      return;
    }
    setToken(stored);
  }, [router]);

  const orgs = useQuery({
    queryKey: ["organizations"],
    queryFn: () => api.organizations(token as string),
    enabled: Boolean(token)
  });

  useEffect(() => {
    if (!selectedOrgId && orgs.data?.[0]) {
      setSelectedOrgId(orgs.data[0].organization.id);
    }
  }, [orgs.data, selectedOrgId]);

  const selected = orgs.data?.find((item) => item.organization.id === selectedOrgId) || orgs.data?.[0];
  const organizationId = selected?.organization.id;
  const agents = useMemo(() => flattenAgents(selected), [selected]);

  const tasks = useQuery({
    queryKey: ["tasks", organizationId],
    queryFn: () => api.tasks(token as string, organizationId as string),
    enabled: Boolean(token && organizationId)
  });
  const approvals = useQuery({
    queryKey: ["approvals", organizationId],
    queryFn: () => api.approvals(token as string, organizationId as string),
    enabled: Boolean(token && organizationId)
  });
  const connectors = useQuery({
    queryKey: ["connectors", organizationId],
    queryFn: () => api.connectors(token as string, organizationId as string),
    enabled: Boolean(token && organizationId)
  });
  const analytics = useQuery({
    queryKey: ["analytics", organizationId],
    queryFn: () => api.analytics(token as string, organizationId as string),
    enabled: Boolean(token && organizationId),
    refetchInterval: 5000
  });

  useEffect(() => {
    if (!token || !organizationId || !activeRun) return;
    const controller = new AbortController();
    setStreamedMessages([]);
    setStreamStatus(activeRun.status);
    void streamRunMessages(
      api.streamUrl(organizationId, activeRun.id),
      token,
      (message) => setStreamedMessages((existing) => [...existing, message]),
      (status) => {
        setStreamStatus(status);
        void queryClient.invalidateQueries({ queryKey: ["analytics", organizationId] });
      },
      controller.signal
    ).catch(() => undefined);
    return () => controller.abort();
  }, [activeRun, organizationId, queryClient, token]);

  if (!token || orgs.isLoading) {
    return (
      <main className="nexus-grid flex min-h-screen items-center justify-center bg-background text-muted">
        Initializing NEXUS runtime
      </main>
    );
  }

  if (!selected) {
    return (
      <CreateOrganization
        token={token}
        onCreated={(detail) => {
          void queryClient.invalidateQueries({ queryKey: ["organizations"] });
          setSelectedOrgId(detail.organization.id);
        }}
      />
    );
  }

  function logout() {
    clearSession();
    router.push("/login");
  }

  return (
    <main className="nexus-grid min-h-screen bg-background p-3 text-foreground md:p-5">
      <div className="mx-auto max-w-[1800px] space-y-4">
        <header className="glass flex flex-col gap-4 rounded-lg px-4 py-3 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-cyan/30 bg-cyan/12">
              <Workflow className="h-5 w-5 text-cyan" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-semibold tracking-normal">NEXUS Mission Control</h1>
                <Badge tone="cyan">autonomous OS</Badge>
              </div>
              <p className="text-xs text-muted">
                {selected.organization.name} · {selected.organization.domain} · risk tolerance{" "}
                {percent(selected.organization.risk_tolerance)}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <select
              className="h-10 rounded-md border border-white/10 bg-white/8 px-3 text-sm outline-none"
              value={selected.organization.id}
              onChange={(event) => setSelectedOrgId(event.target.value)}
            >
              {orgs.data?.map((item) => (
                <option key={item.organization.id} value={item.organization.id} className="bg-slate-950">
                  {item.organization.name}
                </option>
              ))}
            </select>
            <Button variant="ghost" onClick={logout}>
              <LogOut className="h-4 w-4" />
              Sign out
            </Button>
          </div>
        </header>

        <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
          <MetricCard
            label="Active agents"
            value={analytics.data?.active_agents || agents.length}
            detail="Specialists with memory and tools"
            icon={Bot}
            tone="cyan"
          />
          <MetricCard
            label="Open tasks"
            value={analytics.data?.open_tasks || tasks.data?.length || 0}
            detail="Delegated work items"
            icon={Workflow}
            tone="amber"
          />
          <MetricCard
            label="Pending approvals"
            value={analytics.data?.pending_approvals || approvals.data?.filter((item) => item.status === "pending").length || 0}
            detail="Human gates"
            icon={ShieldAlert}
            tone="coral"
          />
          <MetricCard
            label="Confidence"
            value={percent(analytics.data?.average_confidence || 0)}
            detail="Mean run quality"
            icon={Gauge}
            tone="green"
          />
          <MetricCard
            label="Notifications"
            value={analytics.data?.notifications.length || 0}
            detail="Recent operating events"
            icon={Bell}
            tone="neutral"
          />
        </section>

        <section className="grid gap-4 xl:grid-cols-[390px_1fr_430px]">
          <div className="space-y-4">
            <WorkforceLauncher
              token={token}
              organizationId={selected.organization.id}
              agents={agents}
              onRun={setActiveRun}
            />
            <OrgHierarchy hierarchy={selected.hierarchy} />
          </div>
          <div className="space-y-4">
            <RiskMap />
            <TaskKanban tasks={tasks.data || []} />
            <MemoryExplorer agents={agents} />
          </div>
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-4 w-4 text-cyan" />
                  Run State
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border border-white/10 bg-white/5 p-3 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-muted">Current run</span>
                    <Badge tone={streamStatus === "waiting_approval" ? "amber" : streamStatus ? "green" : "neutral"}>
                      {streamStatus || "idle"}
                    </Badge>
                  </div>
                  <div className="mt-2 font-mono text-xs text-muted">{activeRun?.trace_id || "no active trace"}</div>
                </div>
              </CardContent>
            </Card>
            <ActivityFeed analytics={analytics.data} streamedMessages={streamedMessages} />
            <ApprovalsPanel
              token={token}
              organizationId={selected.organization.id}
              approvals={approvals.data || []}
            />
            <CalendarPanel tasks={tasks.data || []} />
          </div>
        </section>

        <section className="grid gap-4 xl:grid-cols-[1fr_520px]">
          <ConnectorsPanel connectors={connectors.data || []} />
          <TracingPanel analytics={analytics.data} />
        </section>
      </div>
    </main>
  );
}
