import uuid
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.models.base import Base, TimestampMixin


class Company(TimestampMixin, Base):
    __tablename__ = "companies"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("industries.id"), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(String(512))
    industry: Mapped["Industry"] = relationship(back_populates="companies")
    transcripts: Mapped[list["Transcript"]] = relationship(back_populates="company")
    use_cases: Mapped[list["UseCase"]] = relationship(back_populates="company")
