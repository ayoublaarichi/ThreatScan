"""
ThreatScan — Search endpoint.

Queries files and indicators by hash, domain, IP, or URL.
"""

import re

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.logging import get_logger
from app.models.file import File as FileModel
from app.models.indicator import Indicator
from app.models.report import Report
from app.schemas.api import SearchResponse, SearchResult

logger = get_logger(__name__)
router = APIRouter()

# Regex patterns for query classification
SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")
SHA1_RE = re.compile(r"^[a-fA-F0-9]{40}$")
MD5_RE = re.compile(r"^[a-fA-F0-9]{32}$")
IP_RE = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
URL_RE = re.compile(r"^https?://", re.IGNORECASE)
DOMAIN_RE = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$")


def classify_query(q: str) -> str:
    """Classify the type of search query."""
    q = q.strip()
    if SHA256_RE.match(q):
        return "sha256"
    if SHA1_RE.match(q):
        return "sha1"
    if MD5_RE.match(q):
        return "md5"
    if IP_RE.match(q):
        return "ip"
    if URL_RE.match(q):
        return "url"
    if DOMAIN_RE.match(q):
        return "domain"
    return "generic"


@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Search files and indicators",
    description="Search by SHA256, SHA1, MD5, domain, IP, URL, or filename.",
)
async def search(
    q: str = Query(..., min_length=1, max_length=512, description="Search query"),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """Search across files and indicators."""
    query_type = classify_query(q)
    results: list[SearchResult] = []

    # Search files by hash
    if query_type in ("sha256", "sha1", "md5"):
        hash_field = {
            "sha256": FileModel.sha256,
            "sha1": FileModel.sha1,
            "md5": FileModel.md5,
        }[query_type]

        file_result = await db.execute(
            select(FileModel, Report)
            .outerjoin(Report, Report.file_id == FileModel.id)
            .where(hash_field == q.lower())
        )

        for file_record, report in file_result.all():
            results.append(
                SearchResult(
                    result_type="file",
                    sha256=file_record.sha256,
                    file_name=file_record.file_name,
                    verdict=report.verdict if report else None,
                    score=report.score if report else None,
                )
            )

    # Search indicators
    if query_type in ("ip", "url", "domain", "generic"):
        indicator_result = await db.execute(
            select(Indicator).where(
                or_(
                    Indicator.value.ilike(f"%{q}%"),
                    Indicator.indicator_type == query_type,
                )
            ).limit(50)
        )

        for ind in indicator_result.scalars().all():
            results.append(
                SearchResult(
                    result_type="indicator",
                    indicator_type=ind.indicator_type,
                    indicator_value=ind.value,
                )
            )

    # Also search filenames for generic queries
    if query_type == "generic":
        file_result = await db.execute(
            select(FileModel, Report)
            .outerjoin(Report, Report.file_id == FileModel.id)
            .where(FileModel.file_name.ilike(f"%{q}%"))
            .limit(50)
        )

        for file_record, report in file_result.all():
            results.append(
                SearchResult(
                    result_type="file",
                    sha256=file_record.sha256,
                    file_name=file_record.file_name,
                    verdict=report.verdict if report else None,
                    score=report.score if report else None,
                )
            )

    return SearchResponse(query=q, results=results, total=len(results))
