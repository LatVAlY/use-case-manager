from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import Transcript
from app.models.enums import TranscriptStatus
from app.schemas import TranscriptCreate, TranscriptUpdate
from app.repository.base import BaseRepository


class TranscriptRepository(BaseRepository[Transcript, TranscriptCreate, TranscriptUpdate]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session, Transcript)

    async def list_by_company(
        self, company_id: UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[Transcript], int]:
        count_stmt = select(func.count()).select_from(Transcript).where(Transcript.company_id == company_id)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()

        stmt = select(Transcript).where(Transcript.company_id == company_id).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        items = result.scalars().all()
        return items, total

    async def list_by_status(
        self, status: TranscriptStatus, skip: int = 0, limit: int = 20
    ) -> tuple[list[Transcript], int]:
        count_stmt = select(func.count()).select_from(Transcript).where(Transcript.status == status)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()

        stmt = select(Transcript).where(Transcript.status == status).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        items = result.scalars().all()
        return items, total

    async def get_by_task_id(self, task_id: str) -> Transcript | None:
        stmt = select(Transcript).where(Transcript.task_id == task_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
