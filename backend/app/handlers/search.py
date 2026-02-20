from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database import get_async_session
from app.models import UseCase
from app.schemas import UseCaseResponse
from app.services import UseCaseService
from app.utils.pagination import PaginationMixin

router = APIRouter(prefix="/search", tags=["search"])


class SearchQuery(BaseModel):
    query: str
    filters: Optional[dict] = None
    limit: int = 10


@router.post("/use-cases", response_model=dict)
async def search_use_cases(
    search_in: SearchQuery,
    db: AsyncSession = Depends(get_async_session),
):
    """Hybrid semantic + keyword search for use cases"""
    service = UseCaseService(db)
    
    items, total = await service.search_use_cases(
        search_in.query,
        skip=0,
        limit=search_in.limit,
    )
    
    await db.commit()
    return {
        "items": [UseCaseResponse.model_validate(uc) for uc in items],
        "total": total,
    }


@router.get("/similar/{use_case_id}", response_model=dict)
async def find_similar(
    use_case_id: UUID,
    limit: int = 10,
    db: AsyncSession = Depends(get_async_session),
):
    """Find use cases similar to a given one"""
    service = UseCaseService(db)
    
    # Get the reference UC
    ref_uc = await service.get_use_case(use_case_id)
    if not ref_uc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Use case not found")
    
    # Search by description keywords
    items, total = await service.search_use_cases(ref_uc.title, skip=0, limit=limit)
    
    # Filter out the original
    items = [uc for uc in items if uc.id != use_case_id]
    
    await db.commit()
    return {
        "similar": [UseCaseResponse.model_validate(uc) for uc in items],
        "count": len(items),
    }


@router.post("/cross-industry")
async def cross_industry_theme(
    theme: str,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Surface a theme across industries.
    """
    service = UseCaseService(db)
    
    # Search by theme
    items, total = await service.search_use_cases(theme, skip=0, limit=100)
    
    # Group by industry
    by_industry = {}
    for uc in items:
        industry_name = uc.company.industry.name if uc.company and uc.company.industry else "Unknown"
        if industry_name not in by_industry:
            by_industry[industry_name] = []
        by_industry[industry_name].append(UseCaseResponse.model_validate(uc))
    
    await db.commit()
    return {
        "theme": theme,
        "by_industry": by_industry,
        "total_count": len(items),
    }
