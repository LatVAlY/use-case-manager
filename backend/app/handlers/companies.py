import logging
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_session
from app.models import User
from app.schemas import CompanyCreate, CompanyUpdate, CompanyResponse, CompanyCreateWithIndustry, IndustryCreate, UserResponse
from app.services import CompanyService
from app.repository import IndustryRepository
from app.utils.permissions import require_maintainer, require_admin
from app.utils.pagination import PaginationMixin
from app.tasks.company_tasks import cleanup_company_data

logger = logging.getLogger(__name__)
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
    company_in: CompanyCreateWithIndustry,
    db: AsyncSession = Depends(get_async_session),
    current_user: UserResponse = Depends(require_maintainer),
):
    """Create a new company. Use industry_id for existing industry, or industry_name to create/select."""
    service = CompanyService(db)
    industry_repo = IndustryRepository(db)

    industry_id: UUID | None = company_in.industry_id
    if industry_id is None and company_in.industry_name:
        existing = await industry_repo.get_by_name(company_in.industry_name)
        if existing:
            industry_id = existing.id
        else:
            new_ind = await industry_repo.create(
                IndustryCreate(name=company_in.industry_name, description=company_in.industry_description)
            )
            industry_id = new_ind.id
    if industry_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide industry_id or industry_name")

    company_create = CompanyCreate(
        name=company_in.name,
        industry_id=industry_id,
        description=company_in.description,
        website=company_in.website,
    )
    company = await service.create_company(company_create)
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
    """Delete a company and all related data (use cases, transcripts, embeddings)."""
    service = CompanyService(db)
    # Check existence first (get_company uses same session/repo)
    company = await service.get_company(company_id)
    if not company:
        logger.warning(f"Delete company: not found | company_id={company_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company not found: {company_id}",
        )
    deleted = await service.delete_company(company_id)
    if not deleted:
        logger.error(f"Delete company: cascade failed | company_id={company_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete company",
        )
    await service.commit()
    # Trigger Celery task to clean Qdrant embeddings (DB records already deleted)
    cleanup_company_data.delay(str(company_id))
