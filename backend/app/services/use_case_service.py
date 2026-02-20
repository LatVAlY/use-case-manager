from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import UseCase
from app.models.enums import UseCaseStatus
from app.schemas import UseCaseCreate, UseCaseUpdate, UseCaseStatusUpdate, UseCaseScoresUpdate
from app.repository import UseCaseRepository


class UseCaseService:
    def __init__(self, db_session: AsyncSession):
        self.repo = UseCaseRepository(db_session)

    def _compute_priority_score(self, use_case: UseCase) -> float | None:
        """
        Priority = (impact + strategic) / (effort + complexity)
        Only compute if all scores are set.
        """
        if not all([
            use_case.impact_score,
            use_case.strategic_score,
            use_case.effort_score,
            use_case.complexity_score,
        ]):
            return None
        
        numerator = use_case.impact_score + use_case.strategic_score
        denominator = use_case.effort_score + use_case.complexity_score
        
        if denominator == 0:
            return 0.0
        return numerator / denominator

    async def create_use_case(self, use_case_in: UseCaseCreate) -> UseCase:
        return await self.repo.create(use_case_in)

    async def get_use_case(self, use_case_id: UUID) -> UseCase | None:
        return await self.repo.get(use_case_id)

    async def list_use_cases(self, skip: int = 0, limit: int = 20) -> tuple[list[UseCase], int]:
        return await self.repo.list(skip, limit)

    async def list_by_company(
        self, company_id: UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[UseCase], int]:
        return await self.repo.list_by_company(company_id, skip, limit)

    async def list_by_transcript(
        self, transcript_id: UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[UseCase], int]:
        return await self.repo.list_by_transcript(transcript_id, skip, limit)

    async def list_with_filters(
        self,
        company_id: Optional[UUID] = None,
        status: Optional[UseCaseStatus] = None,
        assignee_id: Optional[UUID] = None,
        min_confidence: float = 0.0,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> tuple[list[UseCase], int]:
        return await self.repo.list_with_filters(
            company_id=company_id,
            status=status,
            assignee_id=assignee_id,
            min_confidence=min_confidence,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            order=order,
        )

    async def search_use_cases(
        self, q: str, skip: int = 0, limit: int = 20
    ) -> tuple[list[UseCase], int]:
        return await self.repo.search_by_title_or_description(q, skip, limit)

    async def update_use_case(self, use_case_id: UUID, use_case_in: UseCaseUpdate) -> UseCase | None:
        return await self.repo.update(use_case_id, use_case_in)

    async def update_status(self, use_case_id: UUID, status_in: UseCaseStatusUpdate) -> UseCase | None:
        uc = await self.repo.get(use_case_id)
        if not uc:
            return None
        uc.status = status_in.status
        self.repo.db.add(uc)
        await self.repo.db.flush()
        await self.repo.db.refresh(uc)
        return uc

    async def update_scores(self, use_case_id: UUID, scores_in: UseCaseScoresUpdate) -> UseCase | None:
        uc = await self.repo.get(use_case_id)
        if not uc:
            return None
        
        update_data = scores_in.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(uc, key, value)
        
        # Recompute priority score
        uc.priority_score = self._compute_priority_score(uc)
        
        self.repo.db.add(uc)
        await self.repo.db.flush()
        await self.repo.db.refresh(uc)
        return uc

    async def update_assignee(self, use_case_id: UUID, assignee_id: UUID | None) -> UseCase | None:
        uc = await self.repo.get(use_case_id)
        if not uc:
            return None
        uc.assignee_id = assignee_id
        self.repo.db.add(uc)
        await self.repo.db.flush()
        await self.repo.db.refresh(uc)
        return uc

    async def delete_use_case(self, use_case_id: UUID) -> bool:
        return await self.repo.delete(use_case_id)

    async def commit(self):
        await self.repo.commit()
