"""
ThreatScan — File validation and security checks.
"""

import hashlib
from typing import Tuple

from app.config import get_settings
from app.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Allowed MIME types (magic bytes validation)
ALLOWED_MIME_PREFIXES: set[str] = {
    "application/",
    "text/",
    "image/",
    "audio/",
    "video/",
    "font/",
}

# Blocked MIME types (even within allowed prefixes)
BLOCKED_MIME_TYPES: set[str] = {
    "application/x-httpd-php",
    "application/x-php",
}


def compute_hashes(data: bytes) -> Tuple[str, str, str]:
    """
    Compute SHA256, SHA1, and MD5 of file bytes.

    Returns:
        Tuple of (sha256, sha1, md5) hex digests.
    """
    sha256 = hashlib.sha256(data).hexdigest()
    sha1 = hashlib.sha1(data).hexdigest()
    md5 = hashlib.md5(data).hexdigest()
    return sha256, sha1, md5


def validate_file_size(data: bytes) -> bool:
    """Check file size is within the configured limit."""
    max_bytes = settings.max_upload_bytes
    if len(data) > max_bytes:
        logger.warning(
            "File exceeds size limit",
            size=len(data),
            max_size=max_bytes,
        )
        return False
    if len(data) == 0:
        logger.warning("Empty file upload rejected")
        return False
    return True


def validate_mime_type(mime_type: str) -> bool:
    """Validate MIME type against allow/block list."""
    if mime_type in BLOCKED_MIME_TYPES:
        logger.warning("Blocked MIME type", mime_type=mime_type)
        return False

    for prefix in ALLOWED_MIME_PREFIXES:
        if mime_type.startswith(prefix):
            return True

    logger.warning("Unrecognized MIME type", mime_type=mime_type)
    # Allow unknown types — they may be interesting samples
    return True


def get_mime_type(data: bytes) -> str:
    """Detect MIME type from magic bytes."""
    try:
        import magic
        mime = magic.from_buffer(data, mime=True)
        return mime
    except Exception as e:
        logger.error("Magic detection failed", error=str(e))
        return "application/octet-stream"


def get_magic_description(data: bytes) -> str:
    """Get human-readable file type description."""
    try:
        import magic
        return magic.from_buffer(data)
    except Exception as e:
        logger.error("Magic description failed", error=str(e))
        return "unknown"
