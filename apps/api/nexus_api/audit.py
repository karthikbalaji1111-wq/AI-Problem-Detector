from sqlalchemy.orm import Session

from nexus_api.models import AuditLog


def record_audit(
    db: Session,
    *,
    organization_id: str | None,
    actor_type: str,
    actor_id: str | None,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    metadata: dict | None = None,
) -> AuditLog:
    entry = AuditLog(
        organization_id=organization_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        meta=metadata or {},
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
