from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Comment
from app.schemas import CommentCreate, CommentUpdate
from app.repository import CommentRepository


class CommentService:
    def __init__(self, db_session: AsyncSession):
        self.repo = CommentRepository(db_session)

    async def create_comment(self, comment_in: CommentCreate) -> Comment:
        return await self.repo.create(comment_in)

    async def get_comment(self, comment_id: UUID) -> Comment | None:
        return await self.repo.get(comment_id)

    async def list_comments(self, skip: int = 0, limit: int = 20) -> tuple[list[Comment], int]:
        return await self.repo.list(skip, limit)

    async def list_by_use_case(
        self, use_case_id: UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[Comment], int]:
        return await self.repo.list_by_use_case(use_case_id, skip, limit)

    async def update_comment(self, comment_id: UUID, comment_in: CommentUpdate) -> Comment | None:
        return await self.repo.update(comment_id, comment_in)

    async def delete_comment(self, comment_id: UUID) -> bool:
        return await self.repo.delete(comment_id)

    async def commit(self):
        await self.repo.commit()
