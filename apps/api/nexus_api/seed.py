from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_api.models import User
from nexus_api.security import hash_password
from nexus_api.services.memory import remember
from nexus_api.services.org_factory import create_organization_with_workforce


def seed_demo(db: Session) -> None:
    existing = db.scalar(select(User).where(User.email == "founder@nexus.dev"))
    if existing:
        return
    user = User(
        email="founder@nexus.dev",
        name="NEXUS Founder",
        hashed_password=hash_password("NexusPass123!"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    organization = create_organization_with_workforce(
        db,
        owner_user_id=user.id,
        prompt="Create a manufacturing company that predicts supply chain risk, coordinates production, and improves customer delivery reliability.",
        name="Nexus Manufacturing",
    )
    remember(
        db,
        organization_id=organization.id,
        agent_id=None,
        memory_type="semantic",
        content="The organization prioritizes reliable customer delivery, supplier resilience, production throughput, and human-approved external actions.",
        importance=0.84,
        meta={"seeded": True},
    )
