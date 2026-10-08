"""Monitoring worker entry point.

The worker is currently only an application bootstrap skeleton.
Monitoring services and scanners will be connected here after the
logging and scanner layers are implemented.
"""

import asyncio

from app.config import get_settings


async def run_worker() -> None:
    """Initialize the monitoring worker application.

    The actual monitoring cycle is intentionally not implemented yet.
    Keeping the lifecycle entry point separate from monitoring services
    allows the worker to remain a thin orchestrator when those services
    are introduced.
    """

    settings = get_settings()

    # Monitoring services will be invoked here in a later stage.
    # Do not add scanner, SQL, or business logic to this entry point.
    _ = settings.monitoring_interval


def main() -> None:
    """Run the monitoring worker application."""

    asyncio.run(run_worker())


if __name__ == "__main__":
    main()