from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_session
from app.models import User, UseCase, UseCaseRelation
from app.models.enums import UseCaseStatus, RelationType
from app.schemas import (
    UseCaseCreate,
    UseCaseUpdate,
    UseCaseStatusUpdate,
    UseCaseScoresUpdate,
    UseCaseAssigneeUpdate,
    UseCaseRelationCreate,
    UseCaseResponse,
    UserResponse,
)
from app.services import UseCaseService
from app.utils.permissions import require_maintainer, require_admin
from app.utils.pagination import PaginationMixin

router = APIRouter(prefix="/use-cases", tags=["use-cases"])


class UseCaseListParams(PaginationMixin):
    company_id: Optional[UUID] = None
    industry_id: Optional[UUID] = None
    status: Optional[UseCaseStatus] = None
    assignee_id: Optional[UUID] = None
    min_confidence: float = 0.0
    tags: Optional[str] = None
    q: Optional[str] = None
    sort_by: str = "created_at"
    order: str = "desc"


@router.get("", response_model=dict)
async def list_use_cases(
    params: UseCaseListParams = Depends(),
    db: AsyncSession = Depends(get_async_session),
):
    """List use cases with optional filters"""
    service = UseCaseService(db)
    
    if params.q:
            items, total = await service.search_use_cases(
                params.q, skip=params.skip, limit=params.limit
            )
    else:
        items, total = await service.list_with_filters(
            company_id=params.company_id,
            status=params.status,
            assignee_id=params.assignee_id,
            min_confidence=params.min_confidence,
            skip=params.skip,
            limit=params.limit,
            sort_by=params.sort_by,
            order=params.order,
        )


    return {
        "items": [UseCaseResponse.model_validate(uc) for uc in items],
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "total_pages": (total + params.page_size - 1) // params.page_size,
    }


@router.post("", response_model=UseCaseResponse, status_code=status.HTTP_201_CREATED)
async def create_use_case(
    use_case_in: UseCaseCreate,
    current_user: UserResponse = Depends(require_maintainer),
    db: AsyncSession = Depends(get_async_session),
):
    """Create a new use case manually"""
    service = UseCaseService(db)
    use_case_in_dict = use_case_in.dict()
    use_case_in_dict["created_by_id"] = current_user.id
    uc = await service.create_use_case(UseCaseCreate(**use_case_in_dict))
    await service.commit()
    return UseCaseResponse.model_validate(uc)


@router.get("/{use_case_id}", response_model=UseCaseResponse)
async def get_use_case(
    use_case_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """Get a specific use case"""
    service = UseCaseService(db)
    uc = await service.get_use_case(use_case_id)
    if not uc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Use case not found")
    return UseCaseResponse.model_validate(uc)


@router.patch("/{use_case_id}", response_model=UseCaseResponse)
async def update_use_case(
    use_case_id: UUID,
    use_case_in: UseCaseUpdate,
    current_user: UserResponse = Depends(require_maintainer),
    db: AsyncSession = Depends(get_async_session),
):
    """Update a use case"""
    service = UseCaseService(db)
    uc = await service.update_use_case(use_case_id, use_case_in)
    if not uc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Use case not found")
    await service.commit()
    return UseCaseResponse.model_validate(uc)


@router.delete("/{use_case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_use_case(
    use_case_id: UUID,
    current_user: UserResponse = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    """Delete a use case"""
    service = UseCaseService(db)
    deleted = await service.delete_use_case(use_case_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Use case not found")
    await service.commit()


@router.patch("/{use_case_id}/status", response_model=UseCaseResponse)
async def update_status(
    use_case_id: UUID,
    status_in: UseCaseStatusUpdate,
    current_user: UserResponse = Depends(require_maintainer),
    db: AsyncSession = Depends(get_async_session),
):
    """Update use case status"""
    service = UseCaseService(db)
    uc = await service.update_status(use_case_id, status_in)
    if not uc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Use case not found")
    await service.commit()
    return UseCaseResponse.model_validate(uc)


@router.patch("/{use_case_id}/scores", response_model=UseCaseResponse)
async def update_scores(
    use_case_id: UUID,
    scores_in: UseCaseScoresUpdate,
    current_user: UserResponse = Depends(require_maintainer),
    db: AsyncSession = Depends(get_async_session),
):
    """Update use case scores"""
    service = UseCaseService(db)
    uc = await service.update_scores(use_case_id, scores_in)
    if not uc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Use case not found")
    await service.commit()
    return UseCaseResponse.model_validate(uc)


@router.patch("/{use_case_id}/assignee", response_model=UseCaseResponse)
async def update_assignee(
    use_case_id: UUID,
    assignee_in: UseCaseAssigneeUpdate,
    current_user: UserResponse = Depends(require_maintainer),
    db: AsyncSession = Depends(get_async_session),
):
    """Assign use case to a team member"""
    service = UseCaseService(db)
    uc = await service.update_assignee(use_case_id, assignee_in.assignee_id)
    if not uc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Use case not found")
    await service.commit()
    return UseCaseResponse.model_validate(uc)


@router.post("/{use_case_id}/relations")
async def create_relation(
    use_case_id: UUID,
    relation_in: UseCaseRelationCreate,
    current_user: UserResponse = Depends(require_maintainer),
    db: AsyncSession = Depends(get_async_session),
):
    """Create a relation between two use cases"""
    service = UseCaseService(db)
    
    # Verify both UCs exist
    source = await service.get_use_case(use_case_id)
    target = await service.get_use_case(relation_in.target_id)
    
    if not source or not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Use case not found")
    
    # Create relation
    relation = UseCaseRelation(
        source_id=use_case_id,
        target_id=relation_in.target_id,
        relation_type=relation_in.relation_type,
        note=relation_in.note,
    )
    db.add(relation)
    await db.commit()
    
    return {"id": relation.id, "source_id": relation.source_id, "target_id": relation.target_id}


@router.delete("/{use_case_id}/relations/{relation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_relation(
    use_case_id: UUID,
    relation_id: UUID,
    current_user: UserResponse = Depends(require_maintainer),
    db: AsyncSession = Depends(get_async_session),
):
    """Delete a relation"""
    relation = await db.get(UseCaseRelation, relation_id)
    if not relation or relation.source_id != use_case_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relation not found")
    
    await db.delete(relation)
    await db.commit()
