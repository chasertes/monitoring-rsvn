"""WINK RTSP statistics scanner.

This module executes the external wink-rtsp-stats program and returns
its JSON result as structured Python data.

The scanner does not:

* access PostgreSQL;
* write JSON files;
* read Excel files;
* calculate application-level camera status;
* contain FastAPI logic.
"""

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import Settings, get_settings
from app.logging_config import get_logger


logger = get_logger("wink_scanner")


@dataclass
class WinkScanResult:
    """Structured result returned by the WINK scanner."""

    target: str
    data: dict[str, Any] | None = None
    status: str = "success"
    error: str | None = None
    exit_code: int | None = None


class WinkScanner:
    """Execute WINK measurements with bounded concurrency."""

    def __init__(
        self,
        settings: Settings | None = None,
    ) -> None:
        """Initialize the scanner with application settings."""

        self.settings = settings or get_settings()

        self._semaphore = asyncio.Semaphore(
            self.settings.wink_concurrency,
        )

    async def scan(
        self,
        rtsp_url: str,
    ) -> WinkScanResult:
        """Run one WINK measurement."""

        async with self._semaphore:
            logger.info("WINK scan started")

            executable = Path(self.settings.wink_executable)

            if not executable.exists():
                error = (
                    f"WINK executable not found: {executable}"
                )

                logger.error(error)

                return WinkScanResult(
                    target=rtsp_url,
                    status="executable_not_found",
                    error=error,
                )

            command = [
                str(executable),
                "monitor",
                rtsp_url.strip(),
                "--duration",
                f"{self.settings.wink_measure_duration}s",
                "--output",
                "json",
            ]

            process: asyncio.subprocess.Process | None = None

            try:
                process = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.settings.wink_timeout,
                )

            except asyncio.TimeoutError:
                if process is not None:
                    process.kill()
                    await process.wait()

                logger.error("WINK scan timeout")

                return WinkScanResult(
                    target=rtsp_url,
                    status="timeout",
                    error="WINK process timed out",
                )

            except OSError as exc:
                logger.exception(
                    "WINK process failed to start",
                )

                return WinkScanResult(
                    target=rtsp_url,
                    status="process_error",
                    error=str(exc),
                )

            except Exception as exc:
                logger.exception(
                    "Unexpected WINK scanner error",
                )

                return WinkScanResult(
                    target=rtsp_url,
                    status="scanner_error",
                    error=str(exc),
                )

            exit_code = process.returncode

            stdout_text = stdout.decode(
                "utf-8",
                errors="replace",
            ).strip()

            stderr_text = stderr.decode(
                "utf-8",
                errors="replace",
            ).strip()

            if not stdout_text:
                error = stderr_text or "WINK returned empty output"

                logger.error(
                    "WINK scan failed with exit code %s",
                    exit_code,
                )

                return WinkScanResult(
                    target=rtsp_url,
                    status="failed",
                    error=error,
                    exit_code=exit_code,
                )

            try:
                metrics_data = json.loads(stdout_text)

            except json.JSONDecodeError as exc:
                logger.error("WINK returned invalid JSON")

                return WinkScanResult(
                    target=rtsp_url,
                    status="bad_json",
                    error=str(exc),
                    exit_code=exit_code,
                )

            if not isinstance(metrics_data, dict):
                logger.error(
                    "WINK returned unexpected JSON type",
                )

                return WinkScanResult(
                    target=rtsp_url,
                    status="invalid_result",
                    error="WINK JSON root must be an object",
                    exit_code=exit_code,
                )

            if exit_code not in (0, None):
                logger.error(
                    "WINK process exited with code %s",
                    exit_code,
                )

                return WinkScanResult(
                    target=rtsp_url,
                    data=metrics_data,
                    status="process_failed",
                    error=stderr_text or "WINK process failed",
                    exit_code=exit_code,
                )

            logger.info("WINK scan completed")

            return WinkScanResult(
                target=rtsp_url,
                data=metrics_data,
                status="success",
                exit_code=exit_code,
            )

    async def scan_many(
        self,
        rtsp_urls: list[str],
    ) -> list[WinkScanResult]:
        """Run WINK measurements concurrently."""

        return await asyncio.gather(
            *(self.scan(rtsp_url) for rtsp_url in rtsp_urls),
        )