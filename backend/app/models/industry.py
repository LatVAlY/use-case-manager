import uuid
from sqlalchemy import String, Text
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.models.base import Base, TimestampMixin


class Industry(TimestampMixin, Base):
    __tablename__ = "industries"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    companies: Mapped[list["Company"]] = relationship(back_populates="industry")
