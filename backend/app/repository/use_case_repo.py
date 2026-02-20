from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models import UseCase
from app.models.enums import UseCaseStatus
from app.schemas import UseCaseCreate, UseCaseUpdate
from app.repository.base import BaseRepository


class UseCaseRepository(BaseRepository[UseCase, UseCaseCreate, UseCaseUpdate]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session, UseCase)

    async def list_by_company(
        self, company_id: UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[UseCase], int]:
        count_stmt = select(func.count()).select_from(UseCase).where(UseCase.company_id == company_id)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()

        stmt = select(UseCase).where(UseCase.company_id == company_id).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        items = result.scalars().all()
        return items, total

    async def list_by_transcript(
        self, transcript_id: UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[UseCase], int]:
        count_stmt = select(func.count()).select_from(UseCase).where(UseCase.transcript_id == transcript_id)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()

        stmt = select(UseCase).where(UseCase.transcript_id == transcript_id).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        items = result.scalars().all()
        return items, total

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
        conditions = []
        if company_id:
            conditions.append(UseCase.company_id == company_id)
        if status:
            conditions.append(UseCase.status == status)
        if assignee_id:
            conditions.append(UseCase.assignee_id == assignee_id)
        if min_confidence > 0.0:
            conditions.append(UseCase.confidence_score >= min_confidence)

        where_clause = and_(*conditions) if conditions else True

        count_stmt = select(func.count()).select_from(UseCase).where(where_clause)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()

        # Build sort
        if sort_by == "priority_score":
            sort_col = UseCase.priority_score
        elif sort_by == "confidence_score":
            sort_col = UseCase.confidence_score
        elif sort_by == "status":
            sort_col = UseCase.status
        else:
            sort_col = UseCase.created_at

        if order == "asc":
            stmt = (
                select(UseCase)
                .where(where_clause)
                .order_by(sort_col.asc())
                .offset(skip)
                .limit(limit)
            )
        else:
            stmt = (
                select(UseCase)
                .where(where_clause)
                .order_by(sort_col.desc())
                .offset(skip)
                .limit(limit)
            )

        result = await self.db.execute(stmt)
        items = result.scalars().all()
        return items, total

    async def search_by_title_or_description(
        self, q: str, skip: int = 0, limit: int = 20
    ) -> tuple[list[UseCase], int]:
        count_stmt = (
            select(func.count())
            .select_from(UseCase)
            .where(
                (UseCase.title.ilike(f"%{q}%")) | (UseCase.description.ilike(f"%{q}%"))
            )
        )
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()

        stmt = (
            select(UseCase)
            .where((UseCase.title.ilike(f"%{q}%")) | (UseCase.description.ilike(f"%{q}%")))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        items = result.scalars().all()
        return items, total
