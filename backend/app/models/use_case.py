import uuid
from sqlalchemy import String, Text, ForeignKey, Enum as SAEnum, Float, Integer, JSON
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.models.base import Base, TimestampMixin
from app.models.enums import UseCaseStatus


class UseCase(TimestampMixin, Base):
    __tablename__ = "use_cases"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    expected_benefit: Mapped[str | None] = mapped_column(Text)

    status: Mapped[UseCaseStatus] = mapped_column(
        SAEnum(UseCaseStatus), default=UseCaseStatus.new
    )

    confidence_score: Mapped[float] = mapped_column(Float, default=1.0)
    effort_score: Mapped[int | None] = mapped_column(Integer)
    impact_score: Mapped[int | None] = mapped_column(Integer)
    complexity_score: Mapped[int | None] = mapped_column(Integer)
    strategic_score: Mapped[int | None] = mapped_column(Integer)
    priority_score: Mapped[float | None] = mapped_column(Float)

    tags: Mapped[list | None] = mapped_column(JSON, default=list)
    qdrant_id: Mapped[str | None] = mapped_column(String(255))

    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id"), nullable=False)
    transcript_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("transcripts.id"))
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    company: Mapped["Company"] = relationship(back_populates="use_cases")
    transcript: Mapped["Transcript"] = relationship(back_populates="use_cases")
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="use_case", cascade="all, delete-orphan"
    )
    outgoing_relations: Mapped[list["UseCaseRelation"]] = relationship(
        foreign_keys="UseCaseRelation.source_id",
        back_populates="source",
        cascade="all, delete-orphan"
    )
    incoming_relations: Mapped[list["UseCaseRelation"]] = relationship(
        foreign_keys="UseCaseRelation.target_id",
        back_populates="target",
        cascade="all, delete-orphan"
    )
