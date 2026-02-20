import uuid
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import String, Enum as SAEnum
from sqlalchemy.orm import mapped_column, Mapped
from app.models.base import Base, TimestampMixin
from app.models.enums import UserRole


class User(SQLAlchemyBaseUserTableUUID, TimestampMixin, Base):
    __tablename__ = "users"
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole), default=UserRole.reader, nullable=False
    )
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
