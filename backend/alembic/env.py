"""
Alembic environment configuration.

Reads the database URL from ThreatScan's Pydantic settings so that
migrations use the same connection config as the application.
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add the backend directory to sys.path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import settings  # noqa: E402
from app.database import Base  # noqa: E402

# Import all models so they register with Base.metadata
from app.models.user import User  # noqa: E402, F401
from app.models.file import File  # noqa: E402, F401
from app.models.scan_job import ScanJob  # noqa: E402, F401
from app.models.report import Report  # noqa: E402, F401
from app.models.extracted_string import ExtractedString  # noqa: E402, F401
from app.models.indicator import Indicator  # noqa: E402, F401
from app.models.file_indicator import FileIndicator  # noqa: E402, F401
from app.models.yara_match import YaraMatch  # noqa: E402, F401
from app.models.comment import Comment  # noqa: E402, F401
from app.models.tag import Tag, FileTag  # noqa: E402, F401

# Alembic Config object
config = context.config

# Override the sqlalchemy.url with our settings
config.set_main_option("sqlalchemy.url", settings.database_url_sync)

# Set up loggers
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Generates SQL scripts without connecting to the database.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates an engine and connects to the database.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
