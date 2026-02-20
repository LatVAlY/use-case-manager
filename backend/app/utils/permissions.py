"""
Permission helpers. Role checks (require_admin, require_maintainer) live in
app.dependencies so they can use current_active_user without circular imports;
they are re-exported here for backward compatibility.
"""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.params import Param

from app.dependencies import current_active_user
from app.models.enums import UserRole
from app.schemas import UserResponse

from app.dependencies import require_admin, require_maintainer


async def require_roles(*roles: UserRole):
    """Factory for role-based permission checks (user from session, not from body)."""
    async def checker(
        current_user: Annotated[
            UserResponse,
            Depends(current_active_user),
            Param(include_in_schema=False),
        ],
    ) -> UserResponse:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {[r.value for r in roles]}",
            )
        return current_user
    return checker


__all__ = ["require_admin", "require_maintainer", "require_roles"]
