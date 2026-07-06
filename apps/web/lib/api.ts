import type {
  Agent,
  AgentMessage,
  AgentRun,
  Analytics,
  Approval,
  AuthResponse,
  Connector,
  OrganizationDetail,
  Task
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    super(typeof detail === "string" ? detail : "API request failed");
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(path: string, options: RequestInit = {}, token?: string | null): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers
    }
  });
  if (!response.ok) {
    let detail: unknown = response.statusText;
    try {
      detail = await response.json();
    } catch {
      detail = await response.text();
    }
    throw new ApiError(response.status, detail);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export const api = {
  login(email: string, password: string) {
    return request<AuthResponse>("/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    });
  },
  register(email: string, name: string, password: string) {
    return request<AuthResponse>("/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, name, password })
    });
  },
  me(token: string) {
    return request<AuthResponse["user"]>("/v1/auth/me", {}, token);
  },
  googleStart() {
    return request<{ authorization_url: string }>("/v1/auth/google/start");
  },
  organizations(token: string) {
    return request<OrganizationDetail[]>("/v1/organizations", {}, token);
  },
  createOrganization(token: string, prompt: string, name?: string) {
    return request<OrganizationDetail>(
      "/v1/organizations",
      {
        method: "POST",
        body: JSON.stringify({ prompt, name: name || null })
      },
      token
    );
  },
  agents(token: string, organizationId: string) {
    return request<Agent[]>(`/v1/organizations/${organizationId}/agents`, {}, token);
  },
  runAgent(token: string, organizationId: string, agentId: string, objective: string) {
    return request<AgentRun>(
      `/v1/organizations/${organizationId}/agents/${agentId}/runs`,
      {
        method: "POST",
        body: JSON.stringify({ objective })
      },
      token
    );
  },
  runMessages(token: string, organizationId: string, runId: string) {
    return request<AgentMessage[]>(
      `/v1/organizations/${organizationId}/agents/runs/${runId}/messages`,
      {},
      token
    );
  },
  tasks(token: string, organizationId: string) {
    return request<Task[]>(`/v1/organizations/${organizationId}/tasks`, {}, token);
  },
  approvals(token: string, organizationId: string) {
    return request<Approval[]>(`/v1/organizations/${organizationId}/approvals`, {}, token);
  },
  decideApproval(
    token: string,
    organizationId: string,
    approvalId: string,
    status: "approved" | "rejected" | "changes_requested",
    notes: string
  ) {
    return request<Approval>(
      `/v1/organizations/${organizationId}/approvals/${approvalId}/decision`,
      {
        method: "POST",
        body: JSON.stringify({ status, notes })
      },
      token
    );
  },
  connectors(token: string, organizationId: string) {
    return request<Connector[]>(`/v1/organizations/${organizationId}/connectors`, {}, token);
  },
  analytics(token: string, organizationId: string) {
    return request<Analytics>(`/v1/organizations/${organizationId}/analytics`, {}, token);
  },
  streamUrl(organizationId: string, runId: string) {
    return `${API_BASE}/v1/organizations/${organizationId}/agents/runs/${runId}/stream`;
  }
};

