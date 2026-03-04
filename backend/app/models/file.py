"""
File model — represents an uploaded sample, uniquely identified by SHA256.
"""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class File(Base):
    __tablename__ = "files"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    sha256: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    sha1: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    md5: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    file_name: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(256), nullable=True)
    magic_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    entropy: Mapped[float | None] = mapped_column(Float, nullable=True)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    upload_count: Mapped[int] = mapped_column(default=1)
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    scan_jobs = relationship("ScanJob", back_populates="file", lazy="selectin")
    report = relationship("Report", back_populates="file", uselist=False, lazy="selectin")
    strings = relationship("ExtractedString", back_populates="file", lazy="noload")
    indicators = relationship("FileIndicator", back_populates="file", lazy="selectin")
    yara_matches = relationship("YaraMatch", back_populates="file", lazy="selectin")
    comments = relationship("Comment", back_populates="file", lazy="selectin")
    file_tags = relationship("FileTag", back_populates="file", lazy="selectin")

    def __repr__(self) -> str:
        return f"<File {self.sha256[:16]}…>"
