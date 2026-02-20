from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID


class CommentCreate(BaseModel):
    body: str


class CommentUpdate(BaseModel):
    body: str


class CommentResponse(BaseModel):
    id: UUID
    body: str
    use_case_id: UUID
    author_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
