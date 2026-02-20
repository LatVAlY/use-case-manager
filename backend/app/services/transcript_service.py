from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Transcript
from app.models.enums import TranscriptStatus
from app.schemas import TranscriptCreate, TranscriptUpdate
from app.repository import TranscriptRepository


class TranscriptService:
    def __init__(self, db_session: AsyncSession):
        self.repo = TranscriptRepository(db_session)

    async def create_transcript(self, transcript_in: TranscriptCreate) -> Transcript:
        return await self.repo.create(transcript_in)

    async def get_transcript(self, transcript_id: UUID) -> Transcript | None:
        return await self.repo.get(transcript_id)

    async def list_transcripts(self, skip: int = 0, limit: int = 20) -> tuple[list[Transcript], int]:
        return await self.repo.list(skip, limit)

    async def list_by_company(
        self, company_id: UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[Transcript], int]:
        return await self.repo.list_by_company(company_id, skip, limit)

    async def list_by_status(
        self, status: TranscriptStatus, skip: int = 0, limit: int = 20
    ) -> tuple[list[Transcript], int]:
        return await self.repo.list_by_status(status, skip, limit)

    async def get_by_task_id(self, task_id: str) -> Transcript | None:
        return await self.repo.get_by_task_id(task_id)

    async def update_transcript(self, transcript_id: UUID, transcript_in: TranscriptUpdate) -> Transcript | None:
        return await self.repo.update(transcript_id, transcript_in)

    async def update_status(self, transcript_id: UUID, status: TranscriptStatus) -> Transcript | None:
        transcript = await self.repo.get(transcript_id)
        if not transcript:
            return None
        transcript.status = status
        self.repo.db.add(transcript)
        await self.repo.db.flush()
        await self.repo.db.refresh(transcript)
        return transcript

    async def update_task_id(self, transcript_id: UUID, task_id: str) -> Transcript | None:
        transcript = await self.repo.get(transcript_id)
        if not transcript:
            return None
        transcript.task_id = task_id
        self.repo.db.add(transcript)
        await self.repo.db.flush()
        await self.repo.db.refresh(transcript)
        return transcript

    async def update_progress(
        self, transcript_id: UUID, chunk_count: int | None = None, chunks_processed: int | None = None
    ) -> Transcript | None:
        transcript = await self.repo.get(transcript_id)
        if not transcript:
            return None
        if chunk_count is not None:
            transcript.chunk_count = chunk_count
        if chunks_processed is not None:
            transcript.chunks_processed = chunks_processed
        self.repo.db.add(transcript)
        await self.repo.db.flush()
        await self.repo.db.refresh(transcript)
        return transcript

    async def set_error(self, transcript_id: UUID, error_message: str) -> Transcript | None:
        transcript = await self.repo.get(transcript_id)
        if not transcript:
            return None
        transcript.status = TranscriptStatus.failed
        transcript.error_message = error_message
        self.repo.db.add(transcript)
        await self.repo.db.flush()
        await self.repo.db.refresh(transcript)
        return transcript

    async def delete_transcript(self, transcript_id: UUID) -> bool:
        return await self.repo.delete(transcript_id)

    async def commit(self):
        await self.repo.commit()
