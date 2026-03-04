"""
ThreatScan — Job status endpoint.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.scan_job import ScanJob
from app.models.file import File as FileModel
from app.schemas.api import JobStatusResponse

router = APIRouter()


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Get scan job status",
    description="Check the status and progress of an analysis job.",
)
async def get_job_status(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> JobStatusResponse:
    """Return current status of a scan job."""
    result = await db.execute(
        select(ScanJob)
        .where(ScanJob.id == job_id)
        .options(selectinload(ScanJob.file))
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}",
        )

    return JobStatusResponse(
        job_id=job.id,
        sha256=job.file.sha256,
        status=job.status,
        current_stage=job.current_stage,
        progress=job.progress,
        error_message=job.error_message,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )
