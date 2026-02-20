from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from uuid import UUID
from typing import Optional
from app.models.enums import UseCaseStatus, RelationType


class UseCaseBase(BaseModel):
    title: str
    description: str
    expected_benefit: Optional[str] = None
    tags: Optional[list[str]] = None


class UseCaseCreate(UseCaseBase):
    company_id: UUID
    transcript_id: Optional[UUID] = None


class UseCaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    expected_benefit: Optional[str] = None
    tags: Optional[list[str]] = None


class UseCaseStatusUpdate(BaseModel):
    status: UseCaseStatus


class UseCaseScoresUpdate(BaseModel):
    effort_score: Optional[int] = Field(None, ge=1, le=5)
    impact_score: Optional[int] = Field(None, ge=1, le=5)
    complexity_score: Optional[int] = Field(None, ge=1, le=5)
    strategic_score: Optional[int] = Field(None, ge=1, le=5)


class UseCaseAssigneeUpdate(BaseModel):
    assignee_id: Optional[UUID] = None


class UseCaseRelationCreate(BaseModel):
    target_id: UUID
    relation_type: RelationType
    note: Optional[str] = None


class UseCaseResponse(UseCaseBase):
    id: UUID
    company_id: UUID
    transcript_id: Optional[UUID] = None
    assignee_id: Optional[UUID] = None
    created_by_id: UUID
    status: UseCaseStatus
    confidence_score: float
    effort_score: Optional[int] = None
    impact_score: Optional[int] = None
    complexity_score: Optional[int] = None
    strategic_score: Optional[int] = None
    priority_score: Optional[float] = None
    qdrant_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
