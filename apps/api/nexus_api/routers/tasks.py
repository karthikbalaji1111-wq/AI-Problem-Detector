from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_api.audit import record_audit
from nexus_api.database import get_db
from nexus_api.dependencies import current_user, membership_for_org
from nexus_api.models import Role, Task, TaskStatus, User
from nexus_api.rbac import require_role
from nexus_api.schemas import TaskCreate, TaskRead

router = APIRouter(prefix="/organizations/{organization_id}/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead])
def list_tasks(
    organization_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> list[Task]:
    membership = membership_for_org(organization_id, user, db)
    require_role(membership, Role.VIEWER)
    return list(
        db.scalars(select(Task).where(Task.organization_id == organization_id).order_by(Task.created_at.desc()))
    )


@router.post("", response_model=TaskRead)
def create_task(
    organization_id: str,
    payload: TaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> Task:
    membership = membership_for_org(organization_id, user, db)
    require_role(membership, Role.OPERATOR)
    task = Task(
        organization_id=organization_id,
        owner_agent_id=payload.owner_agent_id,
        title=payload.title,
        description=payload.description,
        status=payload.status,
        priority=payload.priority,
        due_at=payload.due_at,
        meta={"created_by": user.id},
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    record_audit(
        db,
        organization_id=organization_id,
        actor_type="user",
        actor_id=user.id,
        action="task.created",
        target_type="task",
        target_id=task.id,
    )
    return task


@router.patch("/{task_id}/status/{new_status}", response_model=TaskRead)
def update_task_status(
    organization_id: str,
    task_id: str,
    new_status: TaskStatus,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> Task:
    membership = membership_for_org(organization_id, user, db)
    require_role(membership, Role.OPERATOR)
    task = db.get(Task, task_id)
    if not task or task.organization_id != organization_id:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = new_status.value
    task.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(task)
    record_audit(
        db,
        organization_id=organization_id,
        actor_type="user",
        actor_id=user.id,
        action="task.status_updated",
        target_type="task",
        target_id=task.id,
        metadata={"status": new_status.value},
    )
    return task

