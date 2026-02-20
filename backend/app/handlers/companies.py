from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_session
from app.models import User
from app.schemas import CompanyCreate, CompanyUpdate, CompanyResponse, UserResponse
from app.services import CompanyService
from app.utils.permissions import require_maintainer, require_admin
from app.utils.pagination import PaginationMixin

router = APIRouter(prefix="/companies", tags=["companies"])


class CompanyListParams(PaginationMixin):
    industry_id: Optional[UUID] = None
    q: Optional[str] = None


@router.get("", response_model=dict)
async def list_companies(
    params: CompanyListParams = Depends(),
    db: AsyncSession = Depends(get_async_session),
):
    """List all companies with optional filters"""
    service = CompanyService(db)
    
    if params.q:
        items, total = await service.search_companies(params.q, params.skip, params.limit)
    elif params.industry_id:
        items, total = await service.list_by_industry(params.industry_id, params.skip, params.limit)
    else:
        items, total = await service.list_companies(params.skip, params.limit)
    
    await db.commit()
    return {
        "items": [CompanyResponse.model_validate(c) for c in items],
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "total_pages": (total + params.page_size - 1) // params.page_size,
    }


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    company_in: CompanyCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: UserResponse = Depends(require_maintainer),
):
    """Create a new company"""
    service = CompanyService(db)
    company = await service.create_company(company_in)
    await service.commit()
    return CompanyResponse.model_validate(company)


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """Get a specific company"""
    service = CompanyService(db)
    company = await service.get_company(company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return CompanyResponse.model_validate(company)


@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: UUID,
    company_in: CompanyUpdate,
    current_user: UserResponse = Depends(require_maintainer),
    db: AsyncSession = Depends(get_async_session),
):
    """Update a company"""
    service = CompanyService(db)
    company = await service.update_company(company_id, company_in)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    await service.commit()
    return CompanyResponse.model_validate(company)


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: UUID,
    current_user: UserResponse = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    """Delete a company"""
    service = CompanyService(db)
    deleted = await service.delete_company(company_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    await service.commit()
