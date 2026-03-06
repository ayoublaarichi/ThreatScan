"""
Unit tests for the file validation service.
"""

import hashlib

from app.services.validation import (
    compute_hashes,
    validate_file_size,
    validate_mime_type,
)


class TestComputeHashes:
    """Tests for hash computation."""

    def test_compute_hashes_returns_all_three(self):
        data = b"hello world"
        sha256, sha1, md5 = compute_hashes(data)
        assert len(sha256) == 64
        assert len(sha1) == 40
        assert len(md5) == 32

    def test_compute_hashes_sha256_correct(self):
        data = b"hello world"
        sha256, _, _ = compute_hashes(data)
        expected = hashlib.sha256(data).hexdigest()
        assert sha256 == expected

    def test_compute_hashes_sha1_correct(self):
        data = b"test data"
        _, sha1, _ = compute_hashes(data)
        expected = hashlib.sha1(data).hexdigest()
        assert sha1 == expected

    def test_compute_hashes_md5_correct(self):
        data = b"test data"
        _, _, md5 = compute_hashes(data)
        expected = hashlib.md5(data).hexdigest()
        assert md5 == expected

    def test_compute_hashes_empty_bytes(self):
        data = b""
        sha256, _, _ = compute_hashes(data)
        assert sha256 == hashlib.sha256(b"").hexdigest()

    def test_compute_hashes_large_data(self):
        data = b"\x00" * (1024 * 1024)  # 1 MB of zeros
        sha256, sha1, md5 = compute_hashes(data)
        assert len(sha256) == 64
        assert len(sha1) == 40
        assert len(md5) == 32


class TestValidateFileSize:
    """Tests for file size validation."""

    def test_valid_small_file(self):
        assert validate_file_size(b"\x00" * 1024) is True  # 1 KB

    def test_valid_at_limit(self):
        content = b"\x00" * (50 * 1024 * 1024)  # 50 MB
        assert validate_file_size(content) is True

    def test_invalid_over_limit(self):
        content = b"\x00" * (50 * 1024 * 1024 + 1)
        assert validate_file_size(content) is False

    def test_zero_size(self):
        # Zero-byte files should be rejected
        assert validate_file_size(b"") is False


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
