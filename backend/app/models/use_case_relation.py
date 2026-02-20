import uuid
from sqlalchemy import ForeignKey, Enum as SAEnum, Text
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.models.base import Base, TimestampMixin
from app.models.enums import RelationType


class UseCaseRelation(TimestampMixin, Base):
    __tablename__ = "use_case_relations"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("use_cases.id", ondelete="CASCADE"))
    target_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("use_cases.id", ondelete="CASCADE"))
    relation_type: Mapped[RelationType] = mapped_column(SAEnum(RelationType))
    note: Mapped[str | None] = mapped_column(Text)
    source: Mapped["UseCase"] = relationship(foreign_keys=[source_id], back_populates="outgoing_relations")
    target: Mapped["UseCase"] = relationship(foreign_keys=[target_id], back_populates="incoming_relations")
