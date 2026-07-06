import { ShieldCheck } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { percent } from "@/lib/utils";
import type { Approval } from "@/lib/types";

export function ApprovalsPanel({
  token,
  organizationId,
  approvals
}: {
  token: string;
  organizationId: string;
  approvals: Approval[];
}) {
  const queryClient = useQueryClient();
  const decide = useMutation({
    mutationFn: (input: { approvalId: string; status: "approved" | "rejected" | "changes_requested" }) =>
      api.decideApproval(token, organizationId, input.approvalId, input.status, "Decided from NEXUS Mission Control."),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["approvals", organizationId] }),
        queryClient.invalidateQueries({ queryKey: ["analytics", organizationId] }),
        queryClient.invalidateQueries({ queryKey: ["tasks", organizationId] })
      ]);
    }
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-cyan" />
          Human Approval
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {approvals.length === 0 && (
          <div className="rounded-md border border-white/10 bg-white/5 p-3 text-sm text-muted">
            No approval gates are waiting.
          </div>
        )}
        {approvals.slice(0, 4).map((approval) => (
          <div key={approval.id} className="rounded-md border border-white/10 bg-white/5 p-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-sm font-medium">{approval.title}</div>
                <p className="mt-1 text-xs leading-5 text-muted">{approval.rationale}</p>
              </div>
              <Badge tone={approval.status === "pending" ? "amber" : "green"}>{approval.status}</Badge>
            </div>
            <div className="mt-3 flex items-center justify-between text-xs text-muted">
              <span>Risk {percent(approval.risk_score)}</span>
              {approval.status === "pending" && (
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="primary"
                    disabled={decide.isPending}
                    onClick={() => decide.mutate({ approvalId: approval.id, status: "approved" })}
                  >
                    Approve
                  </Button>
                  <Button
                    size="sm"
                    variant="danger"
                    disabled={decide.isPending}
                    onClick={() => decide.mutate({ approvalId: approval.id, status: "rejected" })}
                  >
                    Reject
                  </Button>
                </div>
              )}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

