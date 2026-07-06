from sqlalchemy import func, select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends

from nexus_api.database import get_db
from nexus_api.dependencies import current_user, membership_for_org
from nexus_api.models import (
    Agent,
    AgentMessage,
    AgentRun,
    Approval,
    ApprovalStatus,
    AuditLog,
    Notification,
    Role,
    RunStatus,
    Task,
    TaskStatus,
    User,
)
from nexus_api.rbac import require_role
from nexus_api.schemas import AnalyticsRead

router = APIRouter(prefix="/organizations/{organization_id}/analytics", tags=["analytics"])


@router.get("", response_model=AnalyticsRead)
def get_analytics(
    organization_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> AnalyticsRead:
    membership = membership_for_org(organization_id, user, db)
    require_role(membership, Role.VIEWER)
    active_agents = db.scalar(
        select(func.count()).select_from(Agent).where(Agent.organization_id == organization_id)
    ) or 0
    running_workflows = db.scalar(
        select(func.count())
        .select_from(AgentRun)
        .where(AgentRun.organization_id == organization_id, AgentRun.status == RunStatus.RUNNING.value)
    ) or 0
    pending_approvals = db.scalar(
        select(func.count())
        .select_from(Approval)
        .where(
            Approval.organization_id == organization_id,
            Approval.status == ApprovalStatus.PENDING.value,
        )
    ) or 0
    open_tasks = db.scalar(
        select(func.count())
        .select_from(Task)
        .where(Task.organization_id == organization_id, Task.status != TaskStatus.DONE.value)
    ) or 0
    average_confidence = db.scalar(
        select(func.avg(AgentRun.confidence)).where(AgentRun.organization_id == organization_id)
    ) or 0.0
    risk_index = db.scalar(
        select(func.avg(AgentRun.risk_score)).where(AgentRun.organization_id == organization_id)
    ) or 0.0
    messages = db.scalars(
        select(AgentMessage)
        .where(AgentMessage.organization_id == organization_id)
        .order_by(AgentMessage.created_at.desc())
        .limit(20)
    ).all()
    runs = db.scalars(
        select(AgentRun)
        .where(AgentRun.organization_id == organization_id)
        .order_by(AgentRun.created_at.desc())
        .limit(10)
    ).all()
    notifications = db.scalars(
        select(Notification)
        .where(Notification.organization_id == organization_id)
        .order_by(Notification.created_at.desc())
        .limit(10)
    ).all()
    logs = db.scalars(
        select(AuditLog)
        .where(AuditLog.organization_id == organization_id)
        .order_by(AuditLog.created_at.desc())
        .limit(20)
    ).all()
    return AnalyticsRead(
        active_agents=active_agents,
        running_workflows=running_workflows,
        pending_approvals=pending_approvals,
        open_tasks=open_tasks,
        average_confidence=round(float(average_confidence), 2),
        risk_index=round(float(risk_index), 2),
        timeline=[
            {
                "id": message.id,
                "type": message.message_type,
                "content": message.content,
                "confidence": message.confidence,
                "created_at": message.created_at.isoformat(),
            }
            for message in reversed(messages)
        ],
        traces=[
            {
                "id": run.id,
                "trace_id": run.trace_id,
                "status": run.status,
                "confidence": run.confidence,
                "risk_score": run.risk_score,
                "created_at": run.created_at.isoformat(),
            }
            for run in runs
        ],
        notifications=[
            {
                "id": item.id,
                "title": item.title,
                "body": item.body,
                "severity": item.severity,
                "created_at": item.created_at.isoformat(),
            }
            for item in notifications
        ],
        logs=[
            {
                "id": log.id,
                "action": log.action,
                "actor_type": log.actor_type,
                "target_type": log.target_type,
                "metadata": log.meta,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
    )

