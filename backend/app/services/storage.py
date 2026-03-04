"""
ThreatScan — MinIO / S3 storage service.
"""

from io import BytesIO
from typing import Optional

from minio import Minio
from minio.error import S3Error

from app.config import get_settings
from app.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class StorageService:
    """Handles file upload/download to MinIO (S3-compatible) storage."""

    def __init__(self) -> None:
        self.client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_use_ssl,
        )
        self.bucket = settings.minio_bucket

    def ensure_bucket(self) -> None:
        """Create the bucket if it doesn't exist."""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                logger.info("Created MinIO bucket", bucket=self.bucket)
        except S3Error as e:
            logger.error("Failed to ensure bucket", error=str(e))
            raise

    def upload_file(self, object_name: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """
        Upload file bytes to MinIO.

        Args:
            object_name: The key/path in the bucket (e.g., "samples/<sha256>")
            data: Raw file bytes
            content_type: MIME type of the file

        Returns:
            The object path in storage.
        """
        self.ensure_bucket()
        stream = BytesIO(data)
        self.client.put_object(
            bucket_name=self.bucket,
            object_name=object_name,
            data=stream,
            length=len(data),
            content_type=content_type,
        )
        logger.info("Uploaded file to storage", object_name=object_name, size=len(data))
        return f"{self.bucket}/{object_name}"

    def download_file(self, object_name: str) -> Optional[bytes]:
        """
        Download file bytes from MinIO.

        Args:
            object_name: The key/path in the bucket

        Returns:
            Raw file bytes, or None if not found.
        """
        try:
            response = self.client.get_object(self.bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            logger.error("Failed to download file", object_name=object_name, error=str(e))
            return None

    def delete_file(self, object_name: str) -> bool:
        """Delete a file from MinIO."""
        try:
            self.client.remove_object(self.bucket, object_name)
            logger.info("Deleted file from storage", object_name=object_name)
            return True
        except S3Error as e:
            logger.error("Failed to delete file", object_name=object_name, error=str(e))
            return False

    def file_exists(self, object_name: str) -> bool:
        """Check if a file exists in MinIO."""
        try:
            self.client.stat_object(self.bucket, object_name)
            return True
        except S3Error:
            return False


# Module-level singleton
storage_service = StorageService()
