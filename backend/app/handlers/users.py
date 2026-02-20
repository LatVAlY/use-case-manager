from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_session
from app.models import User
from app.schemas import UserResponse, UserUpdateRole
from app.repository import UserRepository
from app.utils.permissions import require_admin
from app.dependencies import current_active_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user: UserResponse = Depends(current_active_user)):
    """Get current authenticated user"""
    return current_user


@router.get("/users", response_model=dict)
async def list_users(
    page: int = 1,
    page_size: int = 20,
    current_user: UserResponse = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    """List all team members (admin only)"""
    repo = UserRepository(db)
    skip = (page - 1) * page_size
    items, total = await repo.list(skip, page_size)
    await db.commit()
    return {
        "items": [UserResponse.model_validate(u) for u in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """Get a specific user"""
    repo = UserRepository(db)
    user = await repo.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_validate(user)


@router.patch("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: UUID,
    role_in: UserUpdateRole,
    current_user: UserResponse = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    """Update user role (admin only)"""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user.role = role_in.role
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    current_user: UserResponse = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    """Delete a user (admin only)"""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    await db.delete(user)
    await db.commit()
