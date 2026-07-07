import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_api.audit import record_audit
from nexus_api.config import get_settings
from nexus_api.database import get_db
from nexus_api.dependencies import current_user, membership_for_org
from nexus_api.models import Agent, AgentMessage, AgentRun, Memory, Role, User
from nexus_api.rbac import require_role
from nexus_api.schemas import AgentMessageRead, AgentRead, AgentRunCreate, AgentRunRead, MemoryRead
from nexus_api.services.agent_runtime import AgentRuntime
from nexus_api.worker import enqueue_agent_workflow

router = APIRouter(prefix="/organizations/{organization_id}/agents", tags=["agents"])


def dispatch_agent_run(db: Session, run: AgentRun) -> str:
    settings = get_settings()
    if settings.agent_execution_mode != "inline":
        queued = enqueue_agent_workflow(run.id)
        if queued:
            run.state = {
                "queued": True,
                "celery_task_id": queued.id,
                "trace_id": run.trace_id,
            }
            db.commit()
            return "queue"
        if settings.agent_execution_mode == "queue":
            raise HTTPException(status_code=503, detail="Workflow queue is unavailable")
    AgentRuntime(db).run(run=run)
    return "inline"


@router.get("", response_model=list[AgentRead])
def list_agents(
    organization_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> list[Agent]:
    membership = membership_for_org(organization_id, user, db)
    require_role(membership, Role.VIEWER)
    return list(
        db.scalars(select(Agent).where(Agent.organization_id == organization_id).order_by(Agent.name))
    )


@router.post("/{agent_id}/runs", response_model=AgentRunRead)
def run_agent(
    organization_id: str,
    agent_id: str,
    payload: AgentRunCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> AgentRun:
    membership = membership_for_org(organization_id, user, db)
    require_role(membership, Role.OPERATOR)
    agent = db.get(Agent, agent_id)
    if not agent or agent.organization_id != organization_id:
        raise HTTPException(status_code=404, detail="Agent not found")
    run = AgentRun(
        organization_id=organization_id,
        root_agent_id=agent.id,
        requested_by_id=user.id,
        objective=payload.objective,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    record_audit(
        db,
        organization_id=organization_id,
        actor_type="user",
        actor_id=user.id,
        action="agent_run.created",
        target_type="agent_run",
        target_id=run.id,
        metadata={"objective": payload.objective, "root_agent_id": agent.id},
    )
    mode = dispatch_agent_run(db, run)
    record_audit(
        db,
        organization_id=organization_id,
        actor_type="system",
        actor_id=None,
        action=f"agent_run.dispatched.{mode}",
        target_type="agent_run",
        target_id=run.id,
        metadata={"trace_id": run.trace_id},
    )
    db.refresh(run)
    return run


@router.get("/runs/{run_id}", response_model=AgentRunRead)
def get_run(
    organization_id: str,
    run_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> AgentRun:
    membership = membership_for_org(organization_id, user, db)
    require_role(membership, Role.VIEWER)
    run = db.get(AgentRun, run_id)
    if not run or run.organization_id != organization_id:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/runs/{run_id}/messages", response_model=list[AgentMessageRead])
def list_run_messages(
    organization_id: str,
    run_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> list[AgentMessage]:
    membership = membership_for_org(organization_id, user, db)
    require_role(membership, Role.VIEWER)
    return list(
        db.scalars(
            select(AgentMessage)
            .where(AgentMessage.organization_id == organization_id, AgentMessage.run_id == run_id)
            .order_by(AgentMessage.sequence)
        )
    )


@router.get("/runs/{run_id}/stream")
async def stream_run(
    organization_id: str,
    run_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> StreamingResponse:
    membership = membership_for_org(organization_id, user, db)
    require_role(membership, Role.VIEWER)

    async def events():
        last_sequence = 0
        last_status = None
        while True:
            db.expire_all()
            run = db.get(AgentRun, run_id)
            if run and run.status != last_status:
                last_status = run.status
                yield f"event: status\ndata: {json.dumps({'status': run.status})}\n\n"
            messages = list(
                db.scalars(
                    select(AgentMessage)
                    .where(
                        AgentMessage.organization_id == organization_id,
                        AgentMessage.run_id == run_id,
                        AgentMessage.sequence > last_sequence,
                    )
                    .order_by(AgentMessage.sequence)
                )
            )
            for message in messages:
                last_sequence = message.sequence
                payload = AgentMessageRead.model_validate(message).model_dump(mode="json")
                yield f"event: message\ndata: {json.dumps(payload)}\n\n"
            if run and run.status in {"succeeded", "failed", "waiting_approval"} and not messages:
                yield f"event: status\ndata: {json.dumps({'status': run.status})}\n\n"
                break
            if not messages:
                yield f"event: heartbeat\ndata: {json.dumps({'status': last_status or 'queued'})}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(events(), media_type="text/event-stream")


@router.get("/{agent_id}/memories", response_model=list[MemoryRead])
def list_agent_memories(
    organization_id: str,
    agent_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> list[Memory]:
    membership = membership_for_org(organization_id, user, db)
    require_role(membership, Role.VIEWER)
    return list(
        db.scalars(
            select(Memory)
            .where(Memory.organization_id == organization_id, Memory.agent_id == agent_id)
            .order_by(Memory.created_at.desc())
            .limit(100)
        )
    )
