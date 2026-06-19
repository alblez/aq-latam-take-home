"""SQLAlchemy ORM models mapping to canonical schema.sql tables."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class JobModel(Base):
    __tablename__ = "jobs"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    competencies: Mapped[list[CompetencyModel]] = relationship(back_populates="job", lazy="select")


class CompetencyModel(Base):
    __tablename__ = "competencies"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    job_id: Mapped[UUID] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(
        Enum("behavioral", "technical", name="competency_category", create_type=False)
    )
    description: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    job: Mapped[JobModel] = relationship(back_populates="competencies")
    question_pack_items: Mapped[list[QuestionPackItemModel]] = relationship(
        back_populates="competency", lazy="select"
    )


class QuestionPackItemModel(Base):
    __tablename__ = "question_pack_items"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    competency_id: Mapped[UUID] = mapped_column(ForeignKey("competencies.id", ondelete="CASCADE"))
    prompt_text: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    competency: Mapped[CompetencyModel] = relationship(back_populates="question_pack_items")


class SessionModel(Base):
    __tablename__ = "sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    job_id: Mapped[UUID] = mapped_column(ForeignKey("jobs.id", ondelete="RESTRICT"))
    owner_id: Mapped[UUID] = mapped_column()
    status: Mapped[str] = mapped_column(
        Enum("in_progress", "completed", "ended_early", name="session_status", create_type=False)
    )
    completion_reason: Mapped[str | None] = mapped_column(
        Enum(
            "all_competencies_covered",
            "question_cap",
            "ended_early",
            name="completion_reason",
            create_type=False,
        ),
        nullable=True,
    )
    model_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    controller_config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    terminal_panel_state: Mapped[dict | None] = mapped_column(
        JSONB(none_as_null=True), nullable=True
    )
    evaluation_narrative: Mapped[dict | None] = mapped_column(
        JSONB(none_as_null=True), nullable=True
    )

    turns: Mapped[list[TurnModel]] = relationship(back_populates="session", lazy="select")


class TurnModel(Base):
    __tablename__ = "turns"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    session_id: Mapped[UUID] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"))
    client_turn_id: Mapped[UUID | None] = mapped_column(nullable=True)
    turn_index: Mapped[int] = mapped_column(Integer)
    role: Mapped[str] = mapped_column(
        Enum("interviewer", "candidate", name="turn_role", create_type=False)
    )
    competency_id: Mapped[UUID] = mapped_column(ForeignKey("competencies.id", ondelete="RESTRICT"))
    content: Mapped[str] = mapped_column(Text)
    input_mode: Mapped[str | None] = mapped_column(
        Enum("voice", "text", name="answer_input_mode", create_type=False),
        nullable=True,
    )
    audio_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    action: Mapped[str | None] = mapped_column(
        Enum("new_topic", "follow_up", "end", name="policy_action", create_type=False),
        nullable=True,
    )
    source_pack_item_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("question_pack_items.id", ondelete="RESTRICT"), nullable=True
    )
    reasoning: Mapped[dict | None] = mapped_column(JSONB(none_as_null=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    session: Mapped[SessionModel] = relationship(back_populates="turns")


class SessionCompetencyScoreModel(Base):
    __tablename__ = "session_competency_scores"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    session_id: Mapped[UUID] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"))
    competency_id: Mapped[UUID] = mapped_column(ForeignKey("competencies.id", ondelete="RESTRICT"))
    assessed: Mapped[bool] = mapped_column(Boolean)
    score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[dict | None] = mapped_column(JSONB(none_as_null=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
