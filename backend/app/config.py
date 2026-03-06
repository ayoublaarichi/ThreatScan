"""
ThreatScan — Application configuration.

Loads settings from environment variables with sensible defaults.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global application settings loaded from .env or environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── General ──
    environment: str = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production"
    allowed_hosts: str = "localhost,127.0.0.1"

    # ── PostgreSQL ──
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "threatscan"
    postgres_user: str = "threatscan"
    postgres_password: str = "threatscan_secret_change_me"

    # ── Redis ──
    redis_url: str = "redis://localhost:6379/0"

    # ── MinIO / S3 ──
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin_secret_change_me"
    minio_bucket: str = "threatscan-files"
    minio_use_ssl: bool = False

    # ── API ──
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    max_upload_size_mb: int = 50
    rate_limit_per_minute: int = 30

    # ── Celery ──
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    celery_task_timeout: int = 300

    @property
    def database_url(self) -> str:
        """Construct async PostgreSQL database URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        """Construct sync PostgreSQL database URL (for Alembic / Celery)."""
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def hosts_list(self) -> List[str]:
        return [h.strip() for h in self.allowed_hosts.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()


settings = get_settings()
