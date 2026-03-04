"""
Unit tests for the file validation service.
"""

import hashlib
import pytest
from unittest.mock import patch, MagicMock

from app.services.validation import (
    compute_hashes,
    validate_file_size,
    validate_mime_type,
)


class TestComputeHashes:
    """Tests for hash computation."""

    def test_compute_hashes_returns_all_three(self):
        data = b"hello world"
        hashes = compute_hashes(data)
        assert "sha256" in hashes
        assert "sha1" in hashes
        assert "md5" in hashes

    def test_compute_hashes_sha256_correct(self):
        data = b"hello world"
        hashes = compute_hashes(data)
        expected = hashlib.sha256(data).hexdigest()
        assert hashes["sha256"] == expected

    def test_compute_hashes_sha1_correct(self):
        data = b"test data"
        hashes = compute_hashes(data)
        expected = hashlib.sha1(data).hexdigest()
        assert hashes["sha1"] == expected

    def test_compute_hashes_md5_correct(self):
        data = b"test data"
        hashes = compute_hashes(data)
        expected = hashlib.md5(data).hexdigest()
        assert hashes["md5"] == expected

    def test_compute_hashes_empty_bytes(self):
        data = b""
        hashes = compute_hashes(data)
        assert hashes["sha256"] == hashlib.sha256(b"").hexdigest()

    def test_compute_hashes_large_data(self):
        data = b"\x00" * (1024 * 1024)  # 1 MB of zeros
        hashes = compute_hashes(data)
        assert len(hashes["sha256"]) == 64
        assert len(hashes["sha1"]) == 40
        assert len(hashes["md5"]) == 32


class TestValidateFileSize:
    """Tests for file size validation."""

    def test_valid_small_file(self):
        assert validate_file_size(1024) is True  # 1 KB

    def test_valid_at_limit(self):
        limit = 50 * 1024 * 1024  # 50 MB
        assert validate_file_size(limit) is True

    def test_invalid_over_limit(self):
        limit = 50 * 1024 * 1024 + 1
        assert validate_file_size(limit) is False

    def test_zero_size(self):
        # Zero-byte files should be rejected
        assert validate_file_size(0) is False

    def test_negative_size(self):
        assert validate_file_size(-1) is False


class TestValidateMimeType:
    """Tests for MIME type validation."""

    def test_valid_pe_executable(self):
        assert validate_mime_type("application/x-dosexec") is True

    def test_valid_elf_executable(self):
        assert validate_mime_type("application/x-executable") is True

    def test_valid_pdf(self):
        assert validate_mime_type("application/pdf") is True

    def test_valid_zip(self):
        assert validate_mime_type("application/zip") is True

    def test_valid_octet_stream(self):
        assert validate_mime_type("application/octet-stream") is True

    def test_invalid_image(self):
        assert validate_mime_type("image/png") is False

    def test_invalid_video(self):
        assert validate_mime_type("video/mp4") is False

    def test_invalid_text_html(self):
        assert validate_mime_type("text/html") is False

    def test_invalid_empty_string(self):
        assert validate_mime_type("") is False
