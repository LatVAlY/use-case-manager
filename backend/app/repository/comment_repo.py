from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import Comment
from app.schemas import CommentCreate, CommentUpdate
from app.repository.base import BaseRepository


class CommentRepository(BaseRepository[Comment, CommentCreate, CommentUpdate]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session, Comment)

    async def list_by_use_case(
        self, use_case_id: UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[Comment], int]:
        count_stmt = select(func.count()).select_from(Comment).where(Comment.use_case_id == use_case_id)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()

        stmt = (
            select(Comment)
            .where(Comment.use_case_id == use_case_id)
            .order_by(Comment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        items = result.scalars().all()
        return items, total
