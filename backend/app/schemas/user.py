from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Optional
from fastapi_users import schemas
from app.models.enums import UserRole


class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None


class UserCreate(schemas.BaseUserCreate):
   full_name: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None


class UserResponse(UserBase):
    id: UUID
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdateRole(BaseModel):
    role: UserRole
