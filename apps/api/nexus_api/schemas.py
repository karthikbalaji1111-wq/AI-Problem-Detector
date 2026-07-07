from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserRead"


class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=10, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    name: str
    is_active: bool
    created_at: datetime


class OrganizationCreate(BaseModel):
    prompt: str = Field(min_length=6, max_length=1200)
    name: str | None = Field(default=None, max_length=255)


class OrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    domain: str
    description: str
    risk_tolerance: float
    created_at: datetime


class MembershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    role: str
    created_at: datetime


class AgentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    parent_id: str | None
    name: str
    role_key: str
    mission: str
    system_prompt: str
    memory_policy: dict[str, Any]
    planning_policy: dict[str, Any]
    reflection_policy: dict[str, Any]
    tool_access: list[str]
    retry_policy: dict[str, Any]
    evaluation_policy: dict[str, Any]
    confidence_floor: float
    status: str
    created_at: datetime


class HierarchyNode(BaseModel):
    agent: AgentRead
    children: list["HierarchyNode"] = Field(default_factory=list)


class OrganizationDetail(BaseModel):
    organization: OrganizationRead
    membership: MembershipRead
    hierarchy: list[HierarchyNode]


class AgentRunCreate(BaseModel):
    objective: str = Field(min_length=3, max_length=2000)


class AgentRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    root_agent_id: str
    requested_by_id: str
    objective: str
    status: str
    confidence: float
    risk_score: float
    state: dict[str, Any]
    trace_id: str
    created_at: datetime
    completed_at: datetime | None


class AgentMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    organization_id: str
    agent_id: str | None
    sequence: int
    message_type: str
    content: str
    confidence: float
    meta: dict[str, Any]
    created_at: datetime


class TaskCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=1, max_length=4000)
    owner_agent_id: str | None = None
    status: str = "backlog"
    priority: int = Field(default=2, ge=1, le=5)
    due_at: datetime | None = None


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    owner_agent_id: str | None
    title: str
    description: str
    status: str
    priority: int
    due_at: datetime | None
    meta: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class MemoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    agent_id: str | None
    memory_type: str
    content: str
    importance: float
    embedding: list[float]
    meta: dict[str, Any]
    created_at: datetime


class ApprovalDecision(BaseModel):
    status: str = Field(pattern="^(approved|rejected|changes_requested)$")
    notes: str = Field(default="", max_length=2000)


class ApprovalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    run_id: str
    requested_by_agent_id: str | None
    approver_id: str | None
    title: str
    rationale: str
    risk_score: float
    status: str
    decision_notes: str | None
    decided_at: datetime | None
    created_at: datetime


class ConnectorUpsert(BaseModel):
    connector_key: str = Field(min_length=2, max_length=80)
    config: dict[str, Any]


class ConnectorInvoke(BaseModel):
    action: str = Field(min_length=2, max_length=80)
    payload: dict[str, Any] = Field(default_factory=dict)


class ConnectorRead(BaseModel):
    connector_key: str
    configured: bool
    actions: list[str]


class AnalyticsRead(BaseModel):
    active_agents: int
    running_workflows: int
    pending_approvals: int
    open_tasks: int
    average_confidence: float
    risk_index: float
    timeline: list[dict[str, Any]]
    traces: list[dict[str, Any]]
    notifications: list[dict[str, Any]]
    logs: list[dict[str, Any]]


class GoogleAuthStart(BaseModel):
    authorization_url: str


TokenResponse.model_rebuild()
HierarchyNode.model_rebuild()
