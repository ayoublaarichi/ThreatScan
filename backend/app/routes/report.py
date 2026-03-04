"""
ThreatScan — Report endpoints.

Serves analysis reports, community features, and relations.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.logging import get_logger
from app.models.comment import Comment
from app.models.file import File as FileModel
from app.models.file_indicator import FileIndicator
from app.models.indicator import Indicator
from app.models.report import Report
from app.models.tag import FileTag, Tag
from app.models.yara_match import YaraMatch
from app.schemas.api import (
    CommentCreate,
    CommentResponse,
    FileInfo,
    IndicatorSchema,
    RelationsResponse,
    ReportResponse,
    TagCreate,
    TagResponse,
    YaraMatchSchema,
)

logger = get_logger(__name__)
router = APIRouter()


async def _get_file_by_sha256(sha256: str, db: AsyncSession) -> FileModel:
    """Helper: fetch a file by SHA256 or raise 404."""
    result = await db.execute(
        select(FileModel)
        .where(FileModel.sha256 == sha256.lower())
        .options(
            selectinload(FileModel.report),
            selectinload(FileModel.yara_matches),
            selectinload(FileModel.indicators).selectinload(FileIndicator.indicator),
            selectinload(FileModel.comments),
            selectinload(FileModel.file_tags).selectinload(FileTag.tag),
        )
    )
    file_record = result.scalar_one_or_none()
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No report found for SHA256: {sha256}",
        )
    return file_record


@router.get(
    "/report/{sha256}",
    response_model=ReportResponse,
    summary="Get analysis report",
    description="Returns the full analysis report for a given SHA256 hash.",
)
async def get_report(
    sha256: str,
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    """Serve the analysis report for a file."""
    file_record = await _get_file_by_sha256(sha256, db)
    report = file_record.report

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not yet completed for this file",
        )

    # Build file info
    file_info = FileInfo(
        sha256=file_record.sha256,
        sha1=file_record.sha1,
        md5=file_record.md5,
        file_name=file_record.file_name,
        file_size=file_record.file_size,
        mime_type=file_record.mime_type,
        magic_description=file_record.magic_description,
        entropy=file_record.entropy,
        upload_count=file_record.upload_count,
        first_seen=file_record.first_seen,
        last_seen=file_record.last_seen,
    )

    # Build YARA matches
    yara_matches = [
        YaraMatchSchema(
            rule_name=m.rule_name,
            rule_namespace=m.rule_namespace,
            rule_tags=m.rule_tags,
            severity=m.severity,
            description=m.description,
            matched_strings=m.matched_strings,
            score_contribution=m.score_contribution,
        )
        for m in file_record.yara_matches
    ]

    # Build indicators
    indicators = []
    for fi in file_record.indicators:
        ind = fi.indicator
        indicators.append(
            IndicatorSchema(
                indicator_type=ind.indicator_type,
                value=ind.value,
                reputation=ind.reputation,
                context=fi.context,
                sample_count=ind.sample_count,
                first_seen=ind.first_seen,
                last_seen=ind.last_seen,
            )
        )

    # Build tags
    tags = [
        TagResponse(id=ft.tag.id, name=ft.tag.name, color=ft.tag.color)
        for ft in file_record.file_tags
    ]

    # Build comments
    comments = [
        CommentResponse(
            id=c.id,
            content=c.content,
            author_name=c.author_name,
            created_at=c.created_at,
        )
        for c in file_record.comments
    ]

    return ReportResponse(
        file=file_info,
        score=report.score,
        verdict=report.verdict,
        summary=report.summary,
        pe_info=report.pe_info,
        elf_info=report.elf_info,
        scoring_details=report.scoring_details,
        yara_matches=yara_matches,
        indicators=indicators,
        tags=tags,
        comments=comments,
        analysis_duration_ms=report.analysis_duration_ms,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


@router.get(
    "/report/{sha256}/relations",
    response_model=RelationsResponse,
    summary="Get related indicators and files",
)
async def get_relations(
    sha256: str,
    db: AsyncSession = Depends(get_db),
) -> RelationsResponse:
    """Get indicators related to a file and other files sharing those indicators."""
    file_record = await _get_file_by_sha256(sha256, db)

    # Get all indicators for this file
    fi_result = await db.execute(
        select(FileIndicator)
        .where(FileIndicator.file_id == file_record.id)
        .options(selectinload(FileIndicator.indicator))
    )
    file_indicators = fi_result.scalars().all()

    indicators = []
    related_file_ids = set()

    for fi in file_indicators:
        ind = fi.indicator
        indicators.append(
            IndicatorSchema(
                indicator_type=ind.indicator_type,
                value=ind.value,
                reputation=ind.reputation,
                context=fi.context,
                sample_count=ind.sample_count,
            )
        )

        # Find other files sharing this indicator
        other_fi_result = await db.execute(
            select(FileIndicator)
            .where(
                FileIndicator.indicator_id == ind.id,
                FileIndicator.file_id != file_record.id,
            )
        )
        for other_fi in other_fi_result.scalars().all():
            related_file_ids.add(other_fi.file_id)

    # Fetch related files
    related_files = []
    if related_file_ids:
        files_result = await db.execute(
            select(FileModel).where(FileModel.id.in_(related_file_ids))
        )
        for f in files_result.scalars().all():
            related_files.append(
                FileInfo(
                    sha256=f.sha256,
                    sha1=f.sha1,
                    md5=f.md5,
                    file_name=f.file_name,
                    file_size=f.file_size,
                    mime_type=f.mime_type,
                    entropy=f.entropy,
                    upload_count=f.upload_count,
                    first_seen=f.first_seen,
                    last_seen=f.last_seen,
                )
            )

    return RelationsResponse(
        sha256=sha256,
        indicators=indicators,
        related_files=related_files,
    )


@router.post(
    "/report/{sha256}/comment",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a comment to a report",
)
async def add_comment(
    sha256: str,
    body: CommentCreate,
    db: AsyncSession = Depends(get_db),
) -> CommentResponse:
    """Add a community comment to a file report."""
    file_record = await _get_file_by_sha256(sha256, db)

    comment = Comment(
        file_id=file_record.id,
        content=body.content,
        author_name=body.author_name,
    )
    db.add(comment)
    await db.flush()

    return CommentResponse(
        id=comment.id,
        content=comment.content,
        author_name=comment.author_name,
        created_at=comment.created_at,
    )


@router.post(
    "/report/{sha256}/tag",
    response_model=TagResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a tag to a report",
)
async def add_tag(
    sha256: str,
    body: TagCreate,
    db: AsyncSession = Depends(get_db),
) -> TagResponse:
    """Add a tag to a file. Creates the tag if it doesn't exist."""
    file_record = await _get_file_by_sha256(sha256, db)

    # Get or create tag
    result = await db.execute(select(Tag).where(Tag.name == body.name.lower()))
    tag = result.scalar_one_or_none()

    if not tag:
        tag = Tag(name=body.name.lower())
        db.add(tag)
        await db.flush()

    # Check if already tagged
    existing = await db.execute(
        select(FileTag).where(
            FileTag.file_id == file_record.id,
            FileTag.tag_id == tag.id,
        )
    )
    if not existing.scalar_one_or_none():
        file_tag = FileTag(file_id=file_record.id, tag_id=tag.id)
        db.add(file_tag)

    return TagResponse(id=tag.id, name=tag.name, color=tag.color)
