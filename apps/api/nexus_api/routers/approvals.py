from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_api.audit import record_audit
from nexus_api.database import get_db
from nexus_api.dependencies import current_user, membership_for_org
from nexus_api.models import AgentRun, Approval, ApprovalStatus, Role, RunStatus, User
from nexus_api.rbac import require_role
from nexus_api.schemas import ApprovalDecision, ApprovalRead
from nexus_api.services.agent_runtime import AgentRuntime

router = APIRouter(prefix="/organizations/{organization_id}/approvals", tags=["approvals"])


@router.get("", response_model=list[ApprovalRead])
def list_approvals(
    organization_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> list[Approval]:
    membership = membership_for_org(organization_id, user, db)
    require_role(membership, Role.VIEWER)
    return list(
        db.scalars(
            select(Approval)
            .where(Approval.organization_id == organization_id)
            .order_by(Approval.created_at.desc())
        )
    )


@router.post("/{approval_id}/decision", response_model=ApprovalRead)
def decide_approval(
    organization_id: str,
    approval_id: str,
    payload: ApprovalDecision,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> Approval:
    membership = membership_for_org(organization_id, user, db)
    require_role(membership, Role.ADMIN)
    approval = db.get(Approval, approval_id)
    if not approval or approval.organization_id != organization_id:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != ApprovalStatus.PENDING.value:
        raise HTTPException(status_code=409, detail="Approval already decided")
    approval.status = payload.status
    approval.approver_id = user.id
    approval.decision_notes = payload.notes
    approval.decided_at = datetime.now(UTC)
    run = db.get(AgentRun, approval.run_id)
    if payload.status == ApprovalStatus.APPROVED.value and run:
        AgentRuntime(db).resume_after_approval(run=run)
    elif run and run.status == RunStatus.WAITING_APPROVAL.value:
        run.status = RunStatus.FAILED.value
        run.completed_at = datetime.now(UTC)
    db.commit()
    db.refresh(approval)
    record_audit(
        db,
        organization_id=organization_id,
        actor_type="user",
        actor_id=user.id,
        action="approval.decided",
        target_type="approval",
        target_id=approval.id,
        metadata={"status": payload.status},
    )
    return approval

