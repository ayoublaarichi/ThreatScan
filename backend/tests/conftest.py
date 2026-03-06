"""
ThreatScan test configuration and shared fixtures.
"""

import asyncio
import os
import uuid
from typing import Any, AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session

# Ensure test environment
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_DB", "threatscan_test")
os.environ.setdefault("POSTGRES_USER", "threatscan")
os.environ.setdefault("POSTGRES_PASSWORD", "test_password")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
os.environ.setdefault("MINIO_ENDPOINT", "localhost:9000")
os.environ.setdefault("MINIO_ACCESS_KEY", "minioadmin")
os.environ.setdefault("MINIO_SECRET_KEY", "minioadmin")
os.environ.setdefault("MINIO_BUCKET", "threatscan-test")

from app.config import get_settings
from app.database import Base, get_db
from app.main import app

settings = get_settings()


# ─── Event loop ─────────────────────────────────────────────
@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ─── Database Engine ────────────────────────────────────────
@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


# ─── Database Session ───────────────────────────────────────
@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create an isolated database session for each test."""
    session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        async with session.begin():
            yield session
        await session.rollback()


# ─── HTTP Client ────────────────────────────────────────────
@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create an HTTP test client with overridden DB dependency."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ─── Mock Storage ───────────────────────────────────────────
@pytest.fixture
def mock_storage():
    """Mock MinIO storage service."""
    with patch("app.services.storage.storage_client") as mock:
        mock.upload_file = AsyncMock(return_value="samples/test_sha256")
        mock.download_file = AsyncMock(return_value=b"fake file content")
        mock.delete_file = AsyncMock(return_value=True)
        mock.file_exists = AsyncMock(return_value=True)
        yield mock


# ─── Mock Celery ────────────────────────────────────────────
@pytest.fixture
def mock_celery():
    """Mock Celery task dispatch."""
    with patch("app.worker.tasks.run_analysis_pipeline.delay") as mock:
        mock.return_value = MagicMock(id=str(uuid.uuid4()))
        yield mock


# ─── Sample Data Factories ──────────────────────────────────
@pytest.fixture
def sample_file_bytes() -> bytes:
    """Return a minimal PE file header for testing."""
    # MZ header + minimal PE stub
    return (
        b"MZ"
        + b"\x00" * 58
        + b"\x80\x00\x00\x00"  # PE offset at 0x80
        + b"\x00" * 60
        + b"PE\x00\x00"  # PE signature
        + b"\x4c\x01"  # Machine: i386
        + b"\x00" * 200
    )


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Return minimal PDF bytes for testing."""
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF"


@pytest.fixture
def sample_sha256() -> str:
    """Return a consistent test SHA256."""
    return "a" * 64


@pytest.fixture
def sample_job_id() -> str:
    """Return a consistent test job UUID."""
    return "12345678-1234-1234-1234-123456789012"
