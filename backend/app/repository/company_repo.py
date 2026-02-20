from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from app.models import Company, Transcript, UseCase, ChatMessage
from app.schemas import CompanyCreate, CompanyUpdate
from app.repository.base import BaseRepository


class CompanyRepository(BaseRepository[Company, CompanyCreate, CompanyUpdate]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session, Company)

    async def list_by_industry(
        self, industry_id: UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[Company], int]:
        count_stmt = select(func.count()).select_from(Company).where(Company.industry_id == industry_id)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()

        stmt = select(Company).where(Company.industry_id == industry_id).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        items = result.scalars().all()
        return items, total

    async def search(self, q: str, skip: int = 0, limit: int = 20) -> tuple[list[Company], int]:
        count_stmt = (
            select(func.count()).select_from(Company).where(Company.name.ilike(f"%{q}%"))
        )
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()

        stmt = select(Company).where(Company.name.ilike(f"%{q}%")).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        items = result.scalars().all()
        return items, total

    async def delete_company_cascade(self, company_id: UUID) -> bool:
        """Delete company and all related data (use_cases, transcripts, chat_messages)."""
        company = await self.get(company_id)
        if not company:
            return False
        await self.db.execute(delete(UseCase).where(UseCase.company_id == company_id))
        await self.db.execute(delete(Transcript).where(Transcript.company_id == company_id))
        await self.db.execute(delete(ChatMessage).where(ChatMessage.company_id == company_id))
        await self.db.delete(company)
        await self.db.flush()
        return True
