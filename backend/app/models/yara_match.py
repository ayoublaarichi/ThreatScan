"""
YaraMatch model — YARA rule hits against a file.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class YaraMatch(Base):
    __tablename__ = "yara_matches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rule_name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    rule_namespace: Mapped[str | None] = mapped_column(String(256), nullable=True)
    rule_tags: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    severity: Mapped[str] = mapped_column(String(32), default="medium")
    # Severity: low, medium, high, critical
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    matched_strings: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    score_contribution: Mapped[int] = mapped_column(Integer, default=0)
    matched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    file = relationship("File", back_populates="yara_matches")

    def __repr__(self) -> str:
        return f"<YaraMatch {self.rule_name} on {self.file_id}>"
