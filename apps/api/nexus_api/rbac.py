from fastapi import HTTPException, status

from nexus_api.models import Membership, Role


ROLE_RANK = {
    Role.VIEWER.value: 10,
    Role.OPERATOR.value: 20,
    Role.ADMIN.value: 30,
    Role.OWNER.value: 40,
}


def require_role(membership: Membership, minimum: Role) -> None:
    if ROLE_RANK.get(membership.role, 0) < ROLE_RANK[minimum.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{minimum.value} role required",
        )

