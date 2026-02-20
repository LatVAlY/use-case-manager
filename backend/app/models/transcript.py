import uuid
from sqlalchemy import String, Text, ForeignKey, Enum as SAEnum, Integer
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.models.base import Base, TimestampMixin
from app.models.enums import TranscriptStatus


class Transcript(TimestampMixin, Base):
    __tablename__ = "transcripts"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String(512))
    raw_text: Mapped[str] = mapped_column(Text)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id"), nullable=False)
    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[TranscriptStatus] = mapped_column(
        SAEnum(TranscriptStatus), default=TranscriptStatus.uploaded
    )
    task_id: Mapped[str | None] = mapped_column(String(255))
    chunk_count: Mapped[int | None] = mapped_column(Integer)
    chunks_processed: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    company: Mapped["Company"] = relationship(back_populates="transcripts")
    use_cases: Mapped[list["UseCase"]] = relationship(back_populates="transcript")
