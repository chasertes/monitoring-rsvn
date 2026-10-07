"""
Database configuration and SQLAlchemy infrastructure.

This module contains only the database infrastructure:
- asynchronous SQLAlchemy engine;
- session factory;
- declarative ORM Base;
- database lifecycle helpers.

Application models must be placed in app/models/.
"""

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


# ---------------------------------------------------------------------------
# SQLAlchemy naming convention
# ---------------------------------------------------------------------------
#
# Explicit constraint names make Alembic migrations predictable and easier
# to maintain, especially when constraints have to be modified later.
#
# Example generated names:
#
#   pk_cameras
#   uq_cameras_ip
#   ix_cameras_operator
#
# This is especially useful with PostgreSQL and Alembic.
#

NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


# ---------------------------------------------------------------------------
# ORM Base
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.

    All models under app/models/ must inherit from this class.
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


def create_database_engine() -> AsyncEngine:
    """
    Create the asynchronous SQLAlchemy engine.

    PostgreSQL is accessed through asyncpg.
    """

    settings = get_settings()

    return create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
    )


engine: AsyncEngine = create_database_engine()


# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------


AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# ---------------------------------------------------------------------------
# FastAPI / service dependency
# ---------------------------------------------------------------------------


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an asynchronous SQLAlchemy session.

    The session is automatically closed after the caller finishes using it.

    Typical FastAPI usage:

        async def endpoint(
            session: AsyncSession = Depends(get_db_session),
        ):
            ...
    """

    async with AsyncSessionFactory() as session:
        yield session


# ---------------------------------------------------------------------------
# Database lifecycle
# ---------------------------------------------------------------------------


async def check_database_connection() -> None:
    """
    Check that PostgreSQL is reachable.

    Raises an exception if the database connection cannot be established.
    """

    from sqlalchemy import text

    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))


async def close_database() -> None:
    """
    Dispose the SQLAlchemy connection pool.

    This should be called during application shutdown.
    """

    await engine.dispose()


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def get_engine_info() -> dict[str, Any]:
    """
    Return non-sensitive database engine information.

    Passwords and complete connection strings are deliberately excluded.
    """

    settings = get_settings()

    return {
        "driver": engine.url.drivername,
        "host": engine.url.host,
        "port": engine.url.port,
        "database": engine.url.database,
        "pool_size": settings.database_pool_size,
        "max_overflow": settings.database_max_overflow,
    }
