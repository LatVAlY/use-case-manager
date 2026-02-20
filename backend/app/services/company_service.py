from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Company
from app.schemas import CompanyCreate, CompanyUpdate
from app.repository import CompanyRepository


class CompanyService:
    def __init__(self, db_session: AsyncSession):
        self.repo = CompanyRepository(db_session)

    async def create_company(self, company_in: CompanyCreate) -> Company:
        return await self.repo.create(company_in)

    async def get_company(self, company_id: UUID) -> Company | None:
        return await self.repo.get(company_id)

    async def list_companies(self, skip: int = 0, limit: int = 20) -> tuple[list[Company], int]:
        return await self.repo.list(skip, limit)

    async def list_by_industry(
        self, industry_id: UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[Company], int]:
        return await self.repo.list_by_industry(industry_id, skip, limit)

    async def search_companies(self, q: str, skip: int = 0, limit: int = 20) -> tuple[list[Company], int]:
        return await self.repo.search(q, skip, limit)

    async def update_company(self, company_id: UUID, company_in: CompanyUpdate) -> Company | None:
        return await self.repo.update(company_id, company_in)

    async def delete_company(self, company_id: UUID) -> bool:
        return await self.repo.delete(company_id)

    async def commit(self):
        await self.repo.commit()
