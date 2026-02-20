from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi_users import exceptions, models, schemas
from fastapi_users.manager import BaseUserManager
from fastapi_users.router.common import ErrorCode
from app.schemas import UserResponse, UserCreate
from app.models.enums import UserRole

def get_register_router(get_user_manager, UserCreate, UserResponse):
    router = APIRouter()

    @router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
    async def register(
        request: Request,
        user_create: UserCreate,
        user_manager: BaseUserManager = Depends(get_user_manager),
    ):
        try:
            # Validate password first
            await user_manager.validate_password(user_create.password, user_create)

            # Check if user exists
            existing_user = await user_manager.user_db.get_by_email(user_create.email)
            if existing_user:
                raise exceptions.UserAlreadyExists()

            # Convert to dict and hash password
            user_dict = user_create.model_dump()
            password = user_dict.pop("password")
            user_dict["hashed_password"] = user_manager.password_helper.hash(password)
            user_dict.setdefault("is_active", True)
            user_dict.setdefault("is_superuser", False)
            user_dict.setdefault("is_verified", True)
            user_dict.setdefault("role", UserRole.admin)

            # Create in DB
            created_user = await user_manager.user_db.create(user_dict)
            await user_manager.on_after_register(created_user, request)

        except exceptions.UserAlreadyExists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.REGISTER_USER_ALREADY_EXISTS,
            )
        except exceptions.InvalidPasswordException as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": ErrorCode.REGISTER_INVALID_PASSWORD,
                    "reason": e.reason,
                },
            )

        return UserResponse.model_validate(created_user)
    return router