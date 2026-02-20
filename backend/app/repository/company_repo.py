from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import Company
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
