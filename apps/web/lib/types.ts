export type User = {
  id: string;
  email: string;
  name: string;
  is_active: boolean;
  created_at: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: "bearer";
  user: User;
};

export type Organization = {
  id: string;
  name: string;
  slug: string;
  domain: string;
  description: string;
  risk_tolerance: number;
  created_at: string;
};

export type Membership = {
  id: string;
  organization_id: string;
  role: "owner" | "admin" | "operator" | "viewer";
  created_at: string;
};

export type Agent = {
  id: string;
  organization_id: string;
  parent_id: string | null;
  name: string;
  role_key: string;
  mission: string;
  system_prompt: string;
  memory_policy: Record<string, unknown>;
  planning_policy: Record<string, unknown>;
  reflection_policy: Record<string, unknown>;
  tool_access: string[];
  retry_policy: Record<string, unknown>;
  evaluation_policy: Record<string, unknown>;
  confidence_floor: number;
  status: string;
  created_at: string;
};

export type HierarchyNode = {
  agent: Agent;
  children: HierarchyNode[];
};

export type OrganizationDetail = {
  organization: Organization;
  membership: Membership;
  hierarchy: HierarchyNode[];
};

export type AgentRun = {
  id: string;
  organization_id: string;
  root_agent_id: string;
  requested_by_id: string;
  objective: string;
  status: "queued" | "running" | "waiting_approval" | "succeeded" | "failed";
  confidence: number;
  risk_score: number;
  state: Record<string, unknown>;
  trace_id: string;
  created_at: string;
  completed_at: string | null;
};

export type AgentMessage = {
  id: string;
  run_id: string;
  organization_id: string;
  agent_id: string | null;
  sequence: number;
  message_type: string;
  content: string;
  confidence: number;
  meta: Record<string, unknown>;
  created_at: string;
};

export type Task = {
  id: string;
  organization_id: string;
  owner_agent_id: string | null;
  title: string;
  description: string;
  status: "backlog" | "planning" | "in_progress" | "review" | "done" | "blocked";
  priority: number;
  due_at: string | null;
  meta: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type Approval = {
  id: string;
  organization_id: string;
  run_id: string;
  requested_by_agent_id: string | null;
  approver_id: string | null;
  title: string;
  rationale: string;
  risk_score: number;
  status: "pending" | "approved" | "rejected" | "changes_requested";
  decision_notes: string | null;
  decided_at: string | null;
  created_at: string;
};

export type Connector = {
  connector_key: string;
  configured: boolean;
  actions: string[];
};

export type Analytics = {
  active_agents: number;
  running_workflows: number;
  pending_approvals: number;
  open_tasks: number;
  average_confidence: number;
  risk_index: number;
  timeline: Array<{
    id: string;
    type: string;
    content: string;
    confidence: number;
    created_at: string;
  }>;
  traces: Array<{
    id: string;
    trace_id: string;
    status: string;
    confidence: number;
    risk_score: number;
    created_at: string;
  }>;
  notifications: Array<{
    id: string;
    title: string;
    body: string;
    severity: string;
    created_at: string;
  }>;
  logs: Array<{
    id: string;
    action: string;
    actor_type: string;
    target_type: string | null;
    metadata: Record<string, unknown>;
    created_at: string;
  }>;
};

