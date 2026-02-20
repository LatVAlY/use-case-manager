import uuid
from sqlalchemy import Text, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.models.base import Base, TimestampMixin


class Comment(TimestampMixin, Base):
    __tablename__ = "comments"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    use_case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("use_cases.id", ondelete="CASCADE"))
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    use_case: Mapped["UseCase"] = relationship(back_populates="comments")
