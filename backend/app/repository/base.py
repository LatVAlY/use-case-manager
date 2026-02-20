from typing import TypeVar, Generic, Type
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, func

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, db_session: AsyncSession, model_class: Type[ModelType]):
        self.db = db_session
        self.model_class = model_class

    async def get(self, id: UUID) -> ModelType | None:
        stmt = select(self.model_class).where(self.model_class.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, skip: int = 0, limit: int = 20) -> tuple[list[ModelType], int]:
        # Get total count
        count_stmt = select(func.count()).select_from(self.model_class)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()

        # Get items
        stmt = select(self.model_class).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        items = result.scalars().all()
        return items, total

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        db_obj = self.model_class(**obj_in.dict(exclude_unset=True))
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, id: UUID, obj_in: UpdateSchemaType) -> ModelType | None:
        db_obj = await self.get(id)
        if not db_obj:
            return None
        update_data = obj_in.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_obj, key, value)
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, id: UUID) -> bool:
        db_obj = await self.get(id)
        if not db_obj:
            return False
        await self.db.delete(db_obj)
        await self.db.flush()
        return True

    async def commit(self):
        await self.db.commit()

    async def rollback(self):
        await self.db.rollback()
