"""FastAPI application entry point.

This module is intentionally limited to application bootstrap.
Business logic, monitoring operations, database queries, and API routes
belong to their respective layers and will be added in later stages.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.database import close_database


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Manage application-level resources during startup and shutdown."""

    # Initialize settings during application startup.
    # Database connectivity is intentionally not checked here yet.
    get_settings()

    yield

    await close_database()


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)


def main() -> None:
    """Run the FastAPI application through Uvicorn."""

    import uvicorn

    uvicorn.run(
        app,
        host=settings.app_host,
        port=settings.app_port,
    )


if __name__ == "__main__":
    main()