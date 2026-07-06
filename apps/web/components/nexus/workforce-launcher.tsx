"use client";

import { FormEvent, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Play, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import type { Agent, AgentRun } from "@/lib/types";

export function WorkforceLauncher({
  token,
  organizationId,
  agents,
  onRun
}: {
  token: string;
  organizationId: string;
  agents: Agent[];
  onRun: (run: AgentRun) => void;
}) {
  const [objective, setObjective] = useState(
    "Evaluate supplier delay risk for the next production cycle, delegate work to the right teams, and prepare a human-approved mitigation plan."
  );
  const queryClient = useQueryClient();
  const ceo = agents.find((agent) => agent.role_key === "ceo_agent") || agents[0];
  const run = useMutation({
    mutationFn: () => api.runAgent(token, organizationId, ceo.id, objective),
    onSuccess: async (created) => {
      onRun(created);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["analytics", organizationId] }),
        queryClient.invalidateQueries({ queryKey: ["tasks", organizationId] }),
        queryClient.invalidateQueries({ queryKey: ["approvals", organizationId] })
      ]);
    }
  });

  function submit(event: FormEvent) {
    event.preventDefault();
    if (!ceo || !objective.trim()) return;
    run.mutate();
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-cyan" />
          Workforce Objective
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={submit} className="space-y-3">
          <Textarea
            value={objective}
            onChange={(event) => setObjective(event.target.value)}
            className="min-h-28"
          />
          <div className="flex items-center justify-between gap-3">
            <p className="text-xs text-muted">
              Runs through CEO, Supervisor, Planner, Research, Critic, Verifier, Execution, and Learning agents.
            </p>
            <Button type="submit" variant="primary" disabled={run.isPending || !ceo}>
              <Play className="h-4 w-4" />
              {run.isPending ? "Running" : "Run"}
            </Button>
          </div>
          {run.error && <p className="text-xs text-coral">{run.error.message}</p>}
        </form>
      </CardContent>
    </Card>
  );
}

