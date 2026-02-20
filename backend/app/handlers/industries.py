from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_session
from app.models import User, Industry
from app.schemas import IndustryCreate, IndustryUpdate, IndustryResponse, UserResponse
from app.repository import IndustryRepository
from app.utils.permissions import require_maintainer, require_admin
from app.utils.pagination import PaginationMixin
from app.dependencies import current_active_user

router = APIRouter(prefix="/industries", tags=["industries"])


class IndustryListParams(PaginationMixin):
    pass


@router.get("", response_model=dict)
async def list_industries(
    params: IndustryListParams = Depends(),
    db: AsyncSession = Depends(get_async_session),
):
    """List all industries"""
    repo = IndustryRepository(db)
    items, total = await repo.list(params.skip, params.limit)
    await db.commit()
    return {
        "items": [IndustryResponse.model_validate(i) for i in items],
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "total_pages": (total + params.page_size - 1) // params.page_size,
    }


@router.post("", response_model=IndustryResponse, status_code=status.HTTP_201_CREATED)
async def create_industry(
    industry_in: IndustryCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: UserResponse = Depends(require_maintainer),
):
    """Create a new industry"""
    repo = IndustryRepository(db)
    industry = await repo.create(industry_in)
    await repo.commit()
    return IndustryResponse.model_validate(industry)


@router.get("/{industry_id}", response_model=IndustryResponse)
async def get_industry(
    industry_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """Get a specific industry"""
    repo = IndustryRepository(db)
    industry = await repo.get(industry_id)
    if not industry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Industry not found")
    return IndustryResponse.model_validate(industry)


@router.patch("/{industry_id}", response_model=IndustryResponse)
async def update_industry(
    industry_id: UUID,
    industry_in: IndustryUpdate,
    current_user: UserResponse = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    """Update an industry"""
    repo = IndustryRepository(db)
    industry = await repo.update(industry_id, industry_in)
    if not industry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Industry not found")
    await repo.commit()
    return IndustryResponse.model_validate(industry)


@router.delete("/{industry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_industry(
    industry_id: UUID,
    current_user: UserResponse = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    """Delete an industry"""
    repo = IndustryRepository(db)
    deleted = await repo.delete(industry_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Industry not found")
    await repo.commit()
