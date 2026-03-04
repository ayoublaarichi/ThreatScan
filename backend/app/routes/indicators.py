"""
ThreatScan — Indicator pivot endpoint.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.file import File as FileModel
from app.models.file_indicator import FileIndicator
from app.models.indicator import Indicator
from app.schemas.api import FileInfo, IndicatorPivotResponse, IndicatorSchema

router = APIRouter()


@router.get(
    "/indicator/{indicator_type}/{value:path}",
    response_model=IndicatorPivotResponse,
    summary="Pivot on an indicator",
    description="Find all files related to a specific indicator (domain, IP, URL).",
)
async def get_indicator(
    indicator_type: str,
    value: str,
    db: AsyncSession = Depends(get_db),
) -> IndicatorPivotResponse:
    """Look up an indicator and list all related file samples."""

    # Validate indicator type
    valid_types = {"domain", "ip", "url", "email"}
    if indicator_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid indicator type. Must be one of: {', '.join(valid_types)}",
        )

    # Find the indicator
    result = await db.execute(
        select(Indicator).where(
            Indicator.indicator_type == indicator_type,
            Indicator.value == value,
        )
    )
    indicator = result.scalar_one_or_none()

    if not indicator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Indicator not found: {indicator_type}:{value}",
        )

    # Get all files linked to this indicator
    fi_result = await db.execute(
        select(FileIndicator)
        .where(FileIndicator.indicator_id == indicator.id)
        .options(selectinload(FileIndicator.file))
    )

    files = []
    for fi in fi_result.scalars().all():
        f = fi.file
        files.append(
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

    indicator_schema = IndicatorSchema(
        indicator_type=indicator.indicator_type,
        value=indicator.value,
        reputation=indicator.reputation,
        sample_count=indicator.sample_count,
        first_seen=indicator.first_seen,
        last_seen=indicator.last_seen,
    )

    return IndicatorPivotResponse(indicator=indicator_schema, files=files)
