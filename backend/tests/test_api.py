"""
API endpoint tests for the upload route.
"""

import io
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from httpx import AsyncClient


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    @pytest.mark.api
    async def test_health_check(self, client: AsyncClient):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestUploadEndpoint:
    """Tests for the file upload endpoint."""

    @pytest.mark.api
    async def test_upload_no_file(self, client: AsyncClient):
        """Upload request without a file should fail."""
        response = await client.post("/api/v1/upload")
        assert response.status_code == 422  # Validation error

    @pytest.mark.api
    async def test_upload_empty_file(self, client: AsyncClient):
        """Upload an empty file should be rejected."""
        files = {"file": ("empty.exe", b"", "application/octet-stream")}
        response = await client.post("/api/v1/upload", files=files)
        assert response.status_code in (400, 422)

    @pytest.mark.api
    async def test_upload_oversized_file(self, client: AsyncClient):
        """File exceeding 50 MB should be rejected."""
        # Create a file just over 50 MB
        big_data = b"\x00" * (50 * 1024 * 1024 + 1)
        files = {"file": ("huge.exe", big_data, "application/octet-stream")}
        response = await client.post("/api/v1/upload", files=files)
        assert response.status_code == 400

    @pytest.mark.api
    async def test_upload_valid_file(
        self, client: AsyncClient, mock_storage, mock_celery, sample_file_bytes
    ):
        """Valid PE file upload should return 202 with job_id."""
        files = {
            "file": ("test.exe", sample_file_bytes, "application/octet-stream")
        }
        response = await client.post("/api/v1/upload", files=files)
        assert response.status_code in (200, 202)
        data = response.json()
        assert "sha256" in data
        assert len(data["sha256"]) == 64

    @pytest.mark.api
    async def test_upload_duplicate_file(
        self, client: AsyncClient, mock_storage, mock_celery, sample_file_bytes
    ):
        """Uploading the same file twice should detect duplication."""
        files = {
            "file": ("test.exe", sample_file_bytes, "application/octet-stream")
        }
        # First upload
        r1 = await client.post("/api/v1/upload", files=files)
        assert r1.status_code in (200, 202)

        # Second upload — same content
        files2 = {
            "file": ("test.exe", sample_file_bytes, "application/octet-stream")
        }
        r2 = await client.post("/api/v1/upload", files=files2)
        assert r2.status_code == 200
        assert r2.json()["sha256"] == r1.json()["sha256"]


class TestReportEndpoint:
    """Tests for the report retrieval endpoint."""

    @pytest.mark.api
    async def test_report_not_found(self, client: AsyncClient, sample_sha256):
        response = await client.get(f"/api/v1/report/{sample_sha256}")
        assert response.status_code == 404

    @pytest.mark.api
    async def test_report_invalid_sha256(self, client: AsyncClient):
        """Invalid SHA256 format should return 422 or 404."""
        response = await client.get("/api/v1/report/not-a-sha256")
        assert response.status_code in (404, 422)


class TestSearchEndpoint:
    """Tests for the search endpoint."""

    @pytest.mark.api
    async def test_search_empty_query(self, client: AsyncClient):
        response = await client.get("/api/v1/search?q=")
        assert response.status_code in (200, 400, 422)

    @pytest.mark.api
    async def test_search_by_hash(self, client: AsyncClient, sample_sha256):
        response = await client.get(f"/api/v1/search?q={sample_sha256}")
        assert response.status_code == 200
        data = response.json()
        assert "files" in data
        assert "indicators" in data

    @pytest.mark.api
    async def test_search_by_ip(self, client: AsyncClient):
        response = await client.get("/api/v1/search?q=185.123.45.67")
        assert response.status_code == 200

    @pytest.mark.api
    async def test_search_by_domain(self, client: AsyncClient):
        response = await client.get("/api/v1/search?q=malware.example.com")
        assert response.status_code == 200


class TestJobsEndpoint:
    """Tests for the job status endpoint."""

    @pytest.mark.api
    async def test_job_not_found(self, client: AsyncClient, sample_job_id):
        response = await client.get(f"/api/v1/jobs/{sample_job_id}")
        assert response.status_code == 404

    @pytest.mark.api
    async def test_job_invalid_uuid(self, client: AsyncClient):
        response = await client.get("/api/v1/jobs/not-a-uuid")
        assert response.status_code in (404, 422)


class TestAdminEndpoint:
    """Tests for the admin endpoint."""

    @pytest.mark.api
    async def test_admin_jobs_list(self, client: AsyncClient):
        response = await client.get("/api/v1/admin/jobs")
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert "total" in data

    @pytest.mark.api
    async def test_admin_delete_not_found(self, client: AsyncClient, sample_sha256):
        response = await client.post(f"/api/v1/admin/delete/{sample_sha256}")
        assert response.status_code == 404
