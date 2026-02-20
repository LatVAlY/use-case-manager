from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Optional
from app.models.enums import TranscriptStatus


class TranscriptCreate(BaseModel):
    filename: str
    raw_text: str
    company_id: UUID
    uploaded_by_id: UUID 


class TranscriptUpdate(BaseModel):
    filename: Optional[str] = None


class TranscriptResponse(BaseModel):
    id: UUID
    filename: str
    company_id: UUID
    uploaded_by_id: UUID
    status: TranscriptStatus
    task_id: Optional[str] = None
    chunk_count: Optional[int] = None
    chunks_processed: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
