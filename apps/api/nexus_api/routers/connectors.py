from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_api.audit import record_audit
from nexus_api.database import get_db
from nexus_api.dependencies import current_user, membership_for_org
from nexus_api.models import ConnectorCredential, Role, User
from nexus_api.rbac import require_role
from nexus_api.schemas import ConnectorInvoke, ConnectorRead, ConnectorUpsert
from nexus_api.security import Encryptor
from nexus_api.services.connectors import CONNECTORS, build_connector, connector_actions

router = APIRouter(prefix="/organizations/{organization_id}/connectors", tags=["connectors"])


@router.get("", response_model=list[ConnectorRead])
def list_connectors(
    organization_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> list[ConnectorRead]:
    membership = membership_for_org(organization_id, user, db)
    require_role(membership, Role.VIEWER)
    configured = set(
        db.scalars(
            select(ConnectorCredential.connector_key).where(
                ConnectorCredential.organization_id == organization_id
            )
        )
    )
    return [
        ConnectorRead(connector_key=key, configured=key in configured, actions=actions)
        for key, actions in connector_actions().items()
    ]


@router.put("/{connector_key}", response_model=ConnectorRead)
def upsert_connector(
    organization_id: str,
    connector_key: str,
    payload: ConnectorUpsert,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> ConnectorRead:
    membership = membership_for_org(organization_id, user, db)
    require_role(membership, Role.ADMIN)
    if connector_key != payload.connector_key or connector_key not in CONNECTORS:
        raise HTTPException(status_code=404, detail="Connector not found")
    encryptor = Encryptor()
    credential = db.scalar(
        select(ConnectorCredential).where(
            ConnectorCredential.organization_id == organization_id,
            ConnectorCredential.connector_key == connector_key,
        )
    )
    encrypted = encryptor.encrypt_json(payload.config)
    if credential:
        credential.encrypted_config = encrypted
    else:
        credential = ConnectorCredential(
            organization_id=organization_id,
            connector_key=connector_key,
            encrypted_config=encrypted,
            created_by_id=user.id,
        )
        db.add(credential)
    db.commit()
    record_audit(
        db,
        organization_id=organization_id,
        actor_type="user",
        actor_id=user.id,
        action="connector.upserted",
        target_type="connector",
        target_id=connector_key,
    )
    return ConnectorRead(
        connector_key=connector_key,
        configured=True,
        actions=list(CONNECTORS[connector_key].actions),
    )


@router.post("/{connector_key}/invoke")
async def invoke_connector(
    organization_id: str,
    connector_key: str,
    payload: ConnectorInvoke,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    membership = membership_for_org(organization_id, user, db)
    require_role(membership, Role.OPERATOR)
    if connector_key not in CONNECTORS:
        raise HTTPException(status_code=404, detail="Connector not found")
    credential = db.scalar(
        select(ConnectorCredential).where(
            ConnectorCredential.organization_id == organization_id,
            ConnectorCredential.connector_key == connector_key,
        )
    )
    config = Encryptor().decrypt_json(credential.encrypted_config) if credential else {}
    connector = build_connector(connector_key, config)
    result = await connector.execute(payload.action, payload.payload)
    record_audit(
        db,
        organization_id=organization_id,
        actor_type="user",
        actor_id=user.id,
        action="connector.invoked",
        target_type="connector",
        target_id=connector_key,
        metadata={"action": payload.action, "ok": result.ok, "status": result.status},
    )
    return {
        "connector": result.connector,
        "action": result.action,
        "ok": result.ok,
        "status": result.status,
        "data": result.data,
    }

