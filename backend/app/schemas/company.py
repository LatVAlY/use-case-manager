from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Optional
from app.schemas.industry import IndustryResponse


class CompanyBase(BaseModel):
    name: str
    industry_id: UUID
    description: Optional[str] = None
    website: Optional[str] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyCreateWithIndustry(BaseModel):
    """Create company with optional inline industry (create if new)."""
    name: str
    industry_id: Optional[UUID] = None  # existing industry
    industry_name: Optional[str] = None  # create new industry with this name
    industry_description: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    industry_id: Optional[UUID] = None
    description: Optional[str] = None
    website: Optional[str] = None


class CompanyResponse(CompanyBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
