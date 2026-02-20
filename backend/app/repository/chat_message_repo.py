from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import ChatMessage
from app.schemas.chat_message import ChatMessageCreate
from app.repository.base import BaseRepository


class ChatMessageRepository(BaseRepository[ChatMessage, ChatMessageCreate, ChatMessageCreate]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session, ChatMessage)

    async def list_by_user_and_company(
        self,
        user_id: UUID,
        company_id: Optional[UUID] = None,
        limit: int = 100,
    ) -> list[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.user_id == user_id)
            .where(
                (ChatMessage.company_id == company_id)
                if company_id is not None
                else (ChatMessage.company_id.is_(None))
            )
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
