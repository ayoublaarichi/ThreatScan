"""
Unit tests for the configuration module.
"""

import os
import pytest


class TestConfig:
    """Tests for Pydantic settings."""

    def test_settings_loads(self):
        from app.config import settings
        assert settings is not None
        assert settings.environment == "testing"

    def test_database_url_format(self):
        from app.config import settings
        url = settings.database_url
        assert url.startswith("postgresql+asyncpg://")

    def test_database_url_sync_format(self):
        from app.config import settings
        url = settings.database_url_sync
        assert url.startswith("postgresql://")

    def test_debug_mode(self):
        from app.config import settings
        assert settings.debug is True

    def test_max_upload_size(self):
        from app.config import settings
        assert settings.max_upload_size_mb > 0
        assert settings.max_upload_size_mb == 50

    def test_rate_limit(self):
        from app.config import settings
        assert settings.rate_limit_per_minute > 0
