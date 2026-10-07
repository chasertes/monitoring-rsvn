"""
Alembic migration environment.

This module connects Alembic with the application's SQLAlchemy metadata
and database configuration.

Database credentials are loaded from application settings and are not
stored in alembic.ini or migration files.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import get_settings
from app.database import Base
from app import models  # noqa: F401


# ---------------------------------------------------------------------------
# Alembic configuration
# ---------------------------------------------------------------------------

config = context.config


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# ---------------------------------------------------------------------------
# SQLAlchemy metadata
# ---------------------------------------------------------------------------
#
# Importing app.models above registers all ORM models with Base.metadata.
#
# target_metadata is then used by Alembic for:
#
#   - autogenerate migrations;
#   - detecting new tables;
#   - detecting changed columns;
#   - detecting changed indexes and constraints.
#

target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Database URL
# ---------------------------------------------------------------------------


def get_database_url() -> str:
    """
    Return the database URL from application settings.

    The URL is intentionally not stored in alembic.ini.
    """

    settings = get_settings()

    return settings.database_url


# ---------------------------------------------------------------------------
# Offline migrations
# ---------------------------------------------------------------------------


def run_migrations_offline() -> None:
    """
    Run migrations without creating a database connection.

    This mode generates SQL statements instead of executing them directly.
    """

    database_url = get_database_url()

    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migrations
# ---------------------------------------------------------------------------


def run_migrations_sync(connection) -> None:
    """
    Configure Alembic using an active synchronous connection.

    Alembic itself operates synchronously, while the application database
    layer uses SQLAlchemy's asynchronous engine.
    """

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    Run migrations using an asynchronous SQLAlchemy engine.
    """

    database_url = get_database_url()

    connectable = create_async_engine(
        database_url,
        poolclass=pool.NullPool,
    )

    try:
        async with connectable.connect() as connection:
            await connection.run_sync(run_migrations_sync)
    finally:
        await connectable.dispose()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())