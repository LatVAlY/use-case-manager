from typing import Annotated
import uuid

from fastapi import Depends
from fastapi.params import Param
from app.services.users.transport import BearerWithRefreshTransport, RefreshAuthenticationBackend
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTStrategy, AuthenticationBackend
from fastapi_users.db import SQLAlchemyUserDatabase

from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, exceptions
from fastapi import HTTPException, status

from app.config import settings
from app.database import AsyncSessionLocal
from app.models import User
from app.models.enums import UserRole
from app.schemas import UserResponse


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.SECRET
    verification_token_secret = settings.SECRET

async def get_user_db():
    async with AsyncSessionLocal() as session:
        yield SQLAlchemyUserDatabase(session, User)

async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)



bearer_transport = BearerWithRefreshTransport(tokenUrl="auth/jwt/login")

jwt_strategy = JWTStrategy(secret=settings.SECRET, lifetime_seconds=3600)
jwt_refresh_strategy = JWTStrategy(secret=settings.SECRET, lifetime_seconds=86400 * 30)  # 30 days

auth_backend = RefreshAuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=lambda: jwt_strategy,
    get_refresh_strategy=lambda: jwt_refresh_strategy,
)
fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])  # ← correct

# Export the current user dependency
current_active_user = fastapi_users.current_user(active=True)


# ============================================================================
# Role checks (user from session only — not from request body)
# ============================================================================
def require_maintainer(
    current_user: UserResponse = Depends(current_active_user),
) -> UserResponse:
    """Require maintainer or admin role."""
    if current_user.role not in (UserRole.maintainer, UserRole.admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Maintainer or Admin role required",
        )
    return current_user


def require_admin(
     current_user: UserResponse = Depends(current_active_user),
) -> UserResponse:
    """Require admin role."""
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return current_user


CurrentUser = Annotated[
    UserResponse,
    Depends(current_active_user),
    Param(include_in_schema=False),
]
CurrentUserMaintainer = Annotated[
    UserResponse,
    Depends(require_maintainer),
    Param(include_in_schema=False),
]
CurrentUserAdmin = Annotated[
    UserResponse,
    Depends(require_admin),
    Param(include_in_schema=False),
]
