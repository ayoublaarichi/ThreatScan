"""
ExtractedString model — strings found during static analysis.
"""

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ExtractedString(Base):
    __tablename__ = "strings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False, index=True
    )
    value: Mapped[str] = mapped_column(Text, nullable=False)
    encoding: Mapped[str] = mapped_column(String(16), default="ascii")  # ascii, utf-16
    offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    length: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Categories: url, ip, email, path, registry, suspicious, generic

    # Relationships
    file = relationship("File", back_populates="strings")

    def __repr__(self) -> str:
        return f"<ExtractedString {self.value[:32]}…>"
