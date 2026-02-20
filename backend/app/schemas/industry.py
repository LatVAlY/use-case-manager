from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Optional


class IndustryBase(BaseModel):
    name: str
    description: Optional[str] = None


class IndustryCreate(IndustryBase):
    pass


class IndustryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class IndustryResponse(IndustryBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
