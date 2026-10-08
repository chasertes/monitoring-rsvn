"""Centralized application logging configuration.

This module configures the standard Python logging subsystem for both
the Web application and the monitoring Worker.

Logging configuration is intentionally kept separate from application
business logic so that all application components use the same logging
rules.
"""

import logging
import logging.handlers
from pathlib import Path

from app.config import get_settings

LOGGER_NAME = "monitoring_rsvn"
LOG_FILE_NAME = "monitoring-rsvn.log"

LOG_FORMAT = (
"%(asctime)s | %(levelname)s | %(name)s | "
"%(message)s"
)

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def _resolve_log_level(level: str) -> int:
"""Convert a textual log level to a logging constant."""


normalized_level = level.upper().strip()

log_level = getattr(logging, normalized_level, None)

if not isinstance(log_level, int):
    return logging.INFO

return log_level


def configure_logging() -> None:
"""Configure console and file logging for the application.


Logging is configured centrally and can safely be called by both
the Web and Worker entry points.
"""

settings = get_settings()
log_level = _resolve_log_level(settings.log_level)

settings.log_dir.mkdir(parents=True, exist_ok=True)

log_file = Path(settings.log_dir) / LOG_FILE_NAME

formatter = logging.Formatter(
    fmt=LOG_FORMAT,
    datefmt=DATE_FORMAT,
)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

file_handler = logging.handlers.RotatingFileHandler(
    filename=log_file,
    maxBytes=10 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8",
)
file_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(log_level)

# Avoid creating duplicate handlers when the application is
# initialized more than once during tests or development.
existing_handler_types = {
    type(handler)
    for handler in logger.handlers
}

if logging.StreamHandler not in existing_handler_types:
    logger.addHandler(console_handler)

if logging.handlers.RotatingFileHandler not in existing_handler_types:
    logger.addHandler(file_handler)


def get_logger(name: str | None = None) -> logging.Logger:
"""Return an application logger.


If no name is provided, the root application logger is returned.
"""

if name:
    return logging.getLogger(f"{LOGGER_NAME}.{name}")

return logging.getLogger(LOGGER_NAME)