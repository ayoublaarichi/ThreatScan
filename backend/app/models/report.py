"""
Report model — final analysis report for a file (one-to-one).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("files.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    score: Mapped[int] = mapped_column(Integer, default=0)
    verdict: Mapped[str] = mapped_column(String(32), default="clean")
    # Verdict values: clean, suspicious, malicious
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    pe_info: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    elf_info: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    scoring_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    analysis_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    file = relationship("File", back_populates="report")

    def __repr__(self) -> str:
        return f"<Report file={self.file_id} verdict={self.verdict}>"
