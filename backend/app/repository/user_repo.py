from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import User
from sqlalchemy.orm import Session


class UserRepository:
    """Thin wrapper around fastapi-users default functionality"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get(self, id: UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def list(self, skip: int = 0, limit: int = 20) -> tuple[list[User], int]:
        from sqlalchemy import func
        count_result = await self.db.execute(select(func.count()).select_from(User))
        total = count_result.scalar()

        result = await self.db.execute(select(User).offset(skip).limit(limit))
        items = result.scalars().all()
        return items, total
