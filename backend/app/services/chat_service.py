from uuid import UUID
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatMessage
from app.schemas import ChatMessageCreate, ChatMessageResponse
from app.repository import ChatMessageRepository


class ChatService:
    def __init__(self, db_session: AsyncSession):
        self.repo = ChatMessageRepository(db_session)

    async def list_messages(
        self,
        user_id: UUID,
        company_id: Optional[UUID] = None,
        limit: int = 100,
    ) -> list[ChatMessageResponse]:
        items = await self.repo.list_by_user_and_company(user_id, company_id, limit)
        return [ChatMessageResponse.model_validate(m) for m in items]

    async def add_message(
        self,
        user_id: UUID,
        role: str,
        content: str,
        company_id: Optional[UUID] = None,
    ) -> ChatMessageResponse:
        msg = await self.repo.create(
            ChatMessageCreate(
                user_id=user_id,
                role=role,
                content=content,
                company_id=company_id,
            )
        )
        await self.repo.commit()
        return ChatMessageResponse.model_validate(msg)

    async def commit(self):
        await self.repo.commit()
