from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Industry
from app.schemas import IndustryCreate, IndustryUpdate
from app.repository.base import BaseRepository


class IndustryRepository(BaseRepository[Industry, IndustryCreate, IndustryUpdate]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session, Industry)

    async def get_by_name(self, name: str) -> Industry | None:
        stmt = select(Industry).where(Industry.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
