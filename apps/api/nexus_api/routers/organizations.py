from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_api.audit import record_audit
from nexus_api.database import get_db
from nexus_api.dependencies import current_user, membership_for_org
from nexus_api.models import Agent, Membership, Organization, Role, User
from nexus_api.rbac import require_role
from nexus_api.schemas import (
    AgentRead,
    HierarchyNode,
    MembershipRead,
    OrganizationCreate,
    OrganizationDetail,
    OrganizationRead,
)
from nexus_api.services.org_factory import create_organization_with_workforce

router = APIRouter(prefix="/organizations", tags=["organizations"])


def build_hierarchy(agents: list[Agent]) -> list[HierarchyNode]:
    by_parent: dict[str | None, list[Agent]] = {}
    for agent in agents:
        by_parent.setdefault(agent.parent_id, []).append(agent)

    def node(agent: Agent) -> HierarchyNode:
        children = sorted(by_parent.get(agent.id, []), key=lambda item: item.name)
        return HierarchyNode(
            agent=AgentRead.model_validate(agent),
            children=[node(child) for child in children],
        )

    roots = sorted(by_parent.get(None, []), key=lambda item: item.name)
    return [node(root) for root in roots]


@router.get("", response_model=list[OrganizationDetail])
def list_organizations(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> list[OrganizationDetail]:
    memberships = db.scalars(select(Membership).where(Membership.user_id == user.id)).all()
    details: list[OrganizationDetail] = []
    for membership in memberships:
        organization = db.get(Organization, membership.organization_id)
        agents = db.scalars(
            select(Agent).where(Agent.organization_id == organization.id).order_by(Agent.name)
        ).all()
        details.append(
            OrganizationDetail(
                organization=OrganizationRead.model_validate(organization),
                membership=MembershipRead.model_validate(membership),
                hierarchy=build_hierarchy(list(agents)),
            )
        )
    return details


@router.post("", response_model=OrganizationDetail)
def create_organization(
    payload: OrganizationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> OrganizationDetail:
    organization = create_organization_with_workforce(
        db,
        owner_user_id=user.id,
        prompt=payload.prompt,
        name=payload.name,
    )
    membership = membership_for_org(organization.id, user, db)
    agents = db.scalars(select(Agent).where(Agent.organization_id == organization.id)).all()
    record_audit(
        db,
        organization_id=organization.id,
        actor_type="user",
        actor_id=user.id,
        action="organization.created",
        target_type="organization",
        target_id=organization.id,
        metadata={"prompt": payload.prompt},
    )
    return OrganizationDetail(
        organization=OrganizationRead.model_validate(organization),
        membership=MembershipRead.model_validate(membership),
        hierarchy=build_hierarchy(list(agents)),
    )


@router.get("/{organization_id}", response_model=OrganizationDetail)
def get_organization(
    organization_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> OrganizationDetail:
    membership = membership_for_org(organization_id, user, db)
    require_role(membership, minimum=Role.VIEWER)
    organization = db.get(Organization, organization_id)
    agents = db.scalars(select(Agent).where(Agent.organization_id == organization_id)).all()
    return OrganizationDetail(
        organization=OrganizationRead.model_validate(organization),
        membership=MembershipRead.model_validate(membership),
        hierarchy=build_hierarchy(list(agents)),
    )
