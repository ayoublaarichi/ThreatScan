"""
Unit tests for the database models.
"""

import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file import File
from app.models.scan_job import ScanJob
from app.models.report import Report
from app.models.indicator import Indicator
from app.models.tag import Tag
from app.models.comment import Comment


class TestFileModel:
    """Tests for the File model."""

    async def test_create_file(self, db_session: AsyncSession):
        file = File(
            sha256="a" * 64,
            sha1="b" * 40,
            md5="c" * 32,
            file_name="test.exe",
            file_size=1024,
            mime_type="application/x-dosexec",
        )
        db_session.add(file)
        await db_session.flush()

        assert file.id is not None
        assert file.upload_count == 1

    async def test_file_sha256_unique(self, db_session: AsyncSession):
        """SHA256 should be unique."""
        sha = "d" * 64
        f1 = File(sha256=sha, sha1="e" * 40, md5="f" * 32,
                   file_name="a.exe", file_size=100, mime_type="application/octet-stream")
        f2 = File(sha256=sha, sha1="g" * 40, md5="h" * 32,
                   file_name="b.exe", file_size=200, mime_type="application/octet-stream")
        db_session.add(f1)
        await db_session.flush()
        db_session.add(f2)
        with pytest.raises(Exception):
            await db_session.flush()


class TestScanJobModel:
    """Tests for the ScanJob model."""

    async def test_create_scan_job(self, db_session: AsyncSession):
        file = File(
            sha256="1" * 64, sha1="2" * 40, md5="3" * 32,
            file_name="job_test.exe", file_size=512,
            mime_type="application/octet-stream",
        )
        db_session.add(file)
        await db_session.flush()

        job = ScanJob(
            file_id=file.id,
            status="queued",
            stage="pending",
            progress=0,
        )
        db_session.add(job)
        await db_session.flush()

        assert job.id is not None
        assert job.status == "queued"
        assert job.progress == 0


class TestIndicatorModel:
    """Tests for the Indicator model."""

    async def test_create_indicator(self, db_session: AsyncSession):
        ind = Indicator(
            indicator_type="ip",
            value="185.123.45.67",
        )
        db_session.add(ind)
        await db_session.flush()

        assert ind.id is not None
        assert ind.indicator_type == "ip"

    async def test_indicator_type_value_unique(self, db_session: AsyncSession):
        """Same type+value should be unique."""
        i1 = Indicator(indicator_type="domain", value="evil.com")
        i2 = Indicator(indicator_type="domain", value="evil.com")
        db_session.add(i1)
        await db_session.flush()
        db_session.add(i2)
        with pytest.raises(Exception):
            await db_session.flush()


class TestTagModel:
    """Tests for the Tag model."""

    async def test_create_tag(self, db_session: AsyncSession):
        tag = Tag(name="trojan", color="#ef4444")
        db_session.add(tag)
        await db_session.flush()

        assert tag.id is not None
        assert tag.name == "trojan"
