"""
FileIndicator model — many-to-many bridge between files and indicators.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FileIndicator(Base):
    __tablename__ = "file_indicators"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False, index=True
    )
    indicator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("indicators.id", ondelete="CASCADE"), nullable=False, index=True
    )
    context: Mapped[str | None] = mapped_column(String(256), nullable=True)
    # Context: where the indicator was found (e.g., "strings", "pe_imports", "url_in_macro")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    file = relationship("File", back_populates="indicators")
    indicator = relationship("Indicator", back_populates="file_indicators")

    def __repr__(self) -> str:
        return f"<FileIndicator file={self.file_id} indicator={self.indicator_id}>"
