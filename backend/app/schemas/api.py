"""
ThreatScan — Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ── Health ──
class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    services: dict[str, str] = {}


# ── Upload ──
class UploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: UUID
    sha256: str
    file_name: str
    status: str
    message: str


# ── Job ──
class JobStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: UUID
    sha256: str
    status: str
    current_stage: Optional[str] = None
    progress: int = 0
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# ── File Info ──
class FileInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sha256: str
    sha1: Optional[str] = None
    md5: Optional[str] = None
    file_name: str
    file_size: int
    mime_type: Optional[str] = None
    magic_description: Optional[str] = None
    entropy: Optional[float] = None
    upload_count: int = 1
    first_seen: datetime
    last_seen: datetime


# ── YARA Match ──
class YaraMatchSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rule_name: str
    rule_namespace: Optional[str] = None
    rule_tags: Optional[list[str]] = None
    severity: str
    description: Optional[str] = None
    matched_strings: Optional[list[Any]] = None
    score_contribution: int = 0


# ── Indicator ──
class IndicatorSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    indicator_type: str
    value: str
    reputation: Optional[str] = None
    context: Optional[str] = None
    sample_count: int = 1
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None


# ── String ──
class ExtractedStringSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    value: str
    encoding: str = "ascii"
    offset: Optional[int] = None
    length: int
    category: Optional[str] = None


# ── Comment ──
class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    author_name: Optional[str] = Field(None, max_length=128)


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    content: str
    author_name: Optional[str] = None
    created_at: datetime


# ── Tag ──
class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128, pattern=r"^[a-zA-Z0-9_\-\.]+$")


class TagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    color: str


# ── Report ──
class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    file: FileInfo
    score: int
    verdict: str
    summary: Optional[str] = None
    pe_info: Optional[dict] = None
    elf_info: Optional[dict] = None
    scoring_details: Optional[dict] = None
    yara_matches: list[YaraMatchSchema] = []
    indicators: list[IndicatorSchema] = []
    tags: list[TagResponse] = []
    comments: list[CommentResponse] = []
    analysis_duration_ms: Optional[int] = None
    created_at: datetime
    updated_at: datetime


# ── Relations ──
class RelationsResponse(BaseModel):
    sha256: str
    indicators: list[IndicatorSchema] = []
    related_files: list[FileInfo] = []


# ── Indicator Pivot ──
class IndicatorPivotResponse(BaseModel):
    indicator: IndicatorSchema
    files: list[FileInfo] = []


# ── Search ──
class SearchResult(BaseModel):
    result_type: str  # file, indicator
    sha256: Optional[str] = None
    indicator_type: Optional[str] = None
    indicator_value: Optional[str] = None
    file_name: Optional[str] = None
    verdict: Optional[str] = None
    score: Optional[int] = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult] = []
    total: int = 0


# ── Admin ──
class AdminJobsResponse(BaseModel):
    jobs: list[JobStatusResponse] = []
    total: int = 0


class DeleteResponse(BaseModel):
    sha256: str
    deleted: bool
    message: str
