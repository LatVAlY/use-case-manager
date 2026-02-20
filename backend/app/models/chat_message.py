import uuid
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped


from app.models.base import Base, TimestampMixin


class ChatMessage(TimestampMixin, Base):
    __tablename__ = "chat_messages"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("companies.id"), nullable=True
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)  # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
