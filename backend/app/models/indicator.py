"""
Indicator model — unique IOCs (domains, IPs, URLs, emails).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Indicator(Base):
    __tablename__ = "indicators"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    indicator_type: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )
    # Types: domain, ip, url, email
    value: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    reputation: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # Reputation: clean, suspicious, malicious, unknown
    enrichment_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    sample_count: Mapped[int] = mapped_column(Integer, default=1)
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    file_indicators = relationship("FileIndicator", back_populates="indicator", lazy="selectin")

    class Meta:
        unique_together = ("indicator_type", "value")

    def __repr__(self) -> str:
        return f"<Indicator {self.indicator_type}:{self.value[:32]}>"
