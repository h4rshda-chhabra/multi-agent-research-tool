import uuid
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    # pending | running | complete | failed
    status: Mapped[str] = mapped_column(String(50), default="pending")
    markdown_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="reports")  # noqa: F821
    sources: Mapped[list["Source"]] = relationship(back_populates="report", cascade="all, delete-orphan")  # noqa: F821
    agent_runs: Mapped[list["AgentRun"]] = relationship(back_populates="report", cascade="all, delete-orphan")  # noqa: F821
    saved_by: Mapped[list["SavedReport"]] = relationship(back_populates="report", cascade="all, delete-orphan")  # noqa: F821
