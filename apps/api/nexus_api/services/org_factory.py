import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_api.models import Agent, Membership, Organization, Role
from nexus_api.services.agent_catalog import AgentDefinition, all_agent_definitions


@dataclass(frozen=True)
class OrganizationSpec:
    name: str
    slug: str
    domain: str
    description: str
    risk_tolerance: float


DOMAIN_KEYWORDS = {
    "manufacturing": ("manufacturing", "factory", "supply", "procurement", "production"),
    "finance": ("finance", "bank", "fund", "insurance", "accounting"),
    "healthcare": ("health", "hospital", "clinic", "patient", "medical"),
    "government": ("government", "city", "municipal", "public", "citizen"),
    "ngo": ("ngo", "nonprofit", "charity", "relief", "humanitarian"),
    "education": ("school", "university", "education", "learning", "student"),
    "agriculture": ("farm", "agriculture", "crop", "soil", "irrigation"),
    "disaster_management": ("disaster", "emergency", "flood", "wildfire", "earthquake"),
    "concierge": ("personal", "family", "calendar", "travel", "executive assistant"),
    "software": ("software", "saas", "developer", "engineering", "product"),
}


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "nexus-organization"


def infer_domain(prompt: str) -> str:
    normalized = prompt.lower()
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return domain
    return "freestyle"


def infer_name(prompt: str, explicit_name: str | None = None) -> str:
    if explicit_name:
        return explicit_name.strip()
    cleaned = prompt.strip().rstrip(".")
    match = re.search(r"create (?:an? |the )?(.+?)(?: company| organization| team| agency)?$", cleaned, re.I)
    if match:
        candidate = match.group(1).strip()
        return candidate[:1].upper() + candidate[1:]
    return "NEXUS Workforce"


def unique_slug(db: Session, base: str) -> str:
    slug = slugify(base)
    existing = set(db.scalars(select(Organization.slug).where(Organization.slug.like(f"{slug}%"))))
    if slug not in existing:
        return slug
    index = 2
    while f"{slug}-{index}" in existing:
        index += 1
    return f"{slug}-{index}"


def build_spec(db: Session, prompt: str, name: str | None) -> OrganizationSpec:
    org_name = infer_name(prompt, name)
    domain = infer_domain(prompt)
    risk_tolerance = 0.45 if domain in {"healthcare", "government", "disaster_management"} else 0.58
    return OrganizationSpec(
        name=org_name,
        slug=unique_slug(db, org_name),
        domain=domain,
        description=prompt.strip(),
        risk_tolerance=risk_tolerance,
    )


def create_agent_from_definition(
    db: Session,
    organization_id: str,
    definition: AgentDefinition,
    role_to_agent_id: dict[str, str],
) -> Agent:
    parent_id = role_to_agent_id.get(definition.parent_role_key or "")
    agent = Agent(
        organization_id=organization_id,
        parent_id=parent_id,
        name=definition.name,
        role_key=definition.role_key,
        mission=definition.mission,
        system_prompt=definition.prompt,
        memory_policy=definition.memory_policy(),
        planning_policy=definition.planning_policy(),
        reflection_policy=definition.reflection_policy(),
        tool_access=list(definition.tool_access),
        retry_policy=definition.retry_policy(),
        evaluation_policy=definition.evaluation_policy(),
        confidence_floor=definition.confidence_floor,
    )
    db.add(agent)
    db.flush()
    role_to_agent_id[definition.role_key] = agent.id
    return agent


def create_organization_with_workforce(
    db: Session,
    *,
    owner_user_id: str,
    prompt: str,
    name: str | None = None,
) -> Organization:
    spec = build_spec(db, prompt, name)
    organization = Organization(
        name=spec.name,
        slug=spec.slug,
        domain=spec.domain,
        description=spec.description,
        risk_tolerance=spec.risk_tolerance,
    )
    db.add(organization)
    db.flush()
    membership = Membership(
        user_id=owner_user_id,
        organization_id=organization.id,
        role=Role.OWNER.value,
    )
    db.add(membership)
    role_to_agent_id: dict[str, str] = {}
    for definition in all_agent_definitions():
        create_agent_from_definition(db, organization.id, definition, role_to_agent_id)
    db.commit()
    db.refresh(organization)
    return organization

