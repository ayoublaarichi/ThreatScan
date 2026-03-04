"""
ThreatScan — Upload endpoint.

Handles file upload, validation, deduplication, and job creation.
"""

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.logging import get_logger
from app.models.file import File as FileModel
from app.models.scan_job import ScanJob
from app.schemas.api import UploadResponse
from app.services.storage import storage_service
from app.services.validation import (
    compute_hashes,
    get_magic_description,
    get_mime_type,
    validate_file_size,
    validate_mime_type,
)
from app.worker.tasks import run_analysis_pipeline

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a file for analysis",
    description="Upload a suspicious file. Returns a job ID for tracking analysis progress.",
)
async def upload_file(
    request: Request,
    file: UploadFile = File(..., description="The file to analyze"),
    db: AsyncSession = Depends(get_db),
) -> UploadResponse:
    """Handle file upload, validate, store, and enqueue analysis."""

    # 1. Read file content
    content = await file.read()

    # 2. Validate file size
    if not validate_file_size(content):
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds maximum upload size of 50MB",
        )

    # 3. Detect and validate MIME type via magic bytes
    mime_type = get_mime_type(content)
    if not validate_mime_type(mime_type):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{mime_type}' is not allowed",
        )

    # 4. Compute hashes
    sha256, sha1, md5 = compute_hashes(content)
    file_name = file.filename or "unnamed"
    magic_desc = get_magic_description(content)

    logger.info(
        "File uploaded",
        sha256=sha256,
        file_name=file_name,
        size=len(content),
        mime_type=mime_type,
    )

    # 5. Check for existing file (deduplication by SHA256)
    result = await db.execute(select(FileModel).where(FileModel.sha256 == sha256))
    existing_file = result.scalar_one_or_none()

    if existing_file:
        # Increment upload count, return existing report link
        existing_file.upload_count += 1
        existing_file.last_seen = None  # triggers onupdate=func.now()

        # Check if there's already a pending/processing job
        job_result = await db.execute(
            select(ScanJob)
            .where(ScanJob.file_id == existing_file.id)
            .order_by(ScanJob.created_at.desc())
            .limit(1)
        )
        existing_job = job_result.scalar_one_or_none()

        if existing_job and existing_job.status in ("pending", "processing"):
            return UploadResponse(
                job_id=existing_job.id,
                sha256=sha256,
                file_name=file_name,
                status=existing_job.status,
                message="File already queued for analysis",
            )

        if existing_job and existing_job.status == "completed":
            return UploadResponse(
                job_id=existing_job.id,
                sha256=sha256,
                file_name=file_name,
                status="completed",
                message="File already analyzed. View report at /report/" + sha256,
            )

    # 6. Store file in MinIO
    storage_path = f"samples/{sha256[:2]}/{sha256}"
    storage_service.upload_file(storage_path, content, mime_type)

    # 7. Create file record
    if not existing_file:
        file_record = FileModel(
            sha256=sha256,
            sha1=sha1,
            md5=md5,
            file_name=file_name,
            file_size=len(content),
            mime_type=mime_type,
            magic_description=magic_desc,
            storage_path=storage_path,
        )
        db.add(file_record)
        await db.flush()
    else:
        file_record = existing_file

    # 8. Create scan job
    scan_job = ScanJob(
        file_id=file_record.id,
        status="pending",
        current_stage="queued",
    )
    db.add(scan_job)
    await db.flush()

    # 9. Dispatch to Celery worker
    run_analysis_pipeline.delay(str(scan_job.id), str(file_record.id), sha256)

    return UploadResponse(
        job_id=scan_job.id,
        sha256=sha256,
        file_name=file_name,
        status="pending",
        message="File accepted. Analysis queued.",
    )
