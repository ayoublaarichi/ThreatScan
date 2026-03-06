"""
ThreatScan — Admin endpoints.

Protected routes for managing jobs and samples.
"""

import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import delete, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.database import get_db
from app.logging import get_logger
from app.models.file import File as FileModel
from app.models.scan_job import ScanJob
from app.schemas.api import AdminJobsResponse, DeleteResponse, JobStatusResponse
from app.services.storage import storage_service

logger = get_logger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin_password(
    x_admin_password: str | None = Header(default=None, alias="X-Admin-Password"),
) -> None:
    settings = get_settings()

    if not settings.admin_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin password is not configured",
        )

    if not x_admin_password or not secrets.compare_digest(x_admin_password, settings.admin_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin password",
        )


@router.get(
    "/jobs",
    response_model=AdminJobsResponse,
    summary="List all scan jobs",
)
async def list_jobs(
    status_filter: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _admin_auth: None = Depends(require_admin_password),
) -> AdminJobsResponse:
    """List all scan jobs with optional status filtering."""
    query = select(ScanJob).options(selectinload(ScanJob.file)).order_by(ScanJob.created_at.desc())

    if status_filter:
        query = query.where(ScanJob.status == status_filter)

    # Get total count
    count_query = select(func.count(ScanJob.id))
    if status_filter:
        count_query = count_query.where(ScanJob.status == status_filter)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    result = await db.execute(query.limit(limit).offset(offset))
    jobs = result.scalars().all()

    job_responses = [
        JobStatusResponse(
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
        for job in jobs
    ]

    return AdminJobsResponse(jobs=job_responses, total=total)


@router.post(
    "/delete/{sha256}",
    response_model=DeleteResponse,
    summary="Delete a sample and all related data",
)
async def delete_sample(
    sha256: str,
    db: AsyncSession = Depends(get_db),
    _admin_auth: None = Depends(require_admin_password),
) -> DeleteResponse:
    """Delete a file sample, its report, and all associated data."""
    result = await db.execute(
        select(FileModel).where(FileModel.sha256 == sha256.lower())
    )
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {sha256}",
        )

    # Delete from storage
    storage_path = file_record.storage_path.replace(f"{storage_service.bucket}/", "")
    storage_service.delete_file(storage_path)

    # Delete from database (cascades to all related tables)
    await db.execute(delete(FileModel).where(FileModel.id == file_record.id))

    logger.info("Deleted sample", sha256=sha256)

    return DeleteResponse(
        sha256=sha256,
        deleted=True,
        message="Sample and all related data deleted successfully",
    )
