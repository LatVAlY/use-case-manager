from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Optional


class ChatMessageCreate(BaseModel):
    user_id: UUID
    role: str
    content: str
    company_id: Optional[UUID] = None


class ChatMessageResponse(BaseModel):
    id: UUID
    user_id: UUID
    company_id: Optional[UUID] = None
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
