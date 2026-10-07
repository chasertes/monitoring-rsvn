"""
Application configuration.

All runtime settings are loaded from environment variables or .env file.

The configuration is intentionally centralized here so that:
- application code does not contain hardcoded paths;
- SNMP concurrency is controlled by asyncio;
- WINK process concurrency is configured separately;
- database connection settings are kept outside the source code;
- deployment-specific values can be changed without modifying Python files.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root directory.
#
# config.py is located at:
#     <project_root>/app/config.py
#
# Therefore:
#     Path(__file__).resolve().parent.parent
# points to <project_root>.
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------

    app_name: str = "monitoring-rsvn"
    app_version: str = "0.1.0"

    app_host: str = "127.0.0.1"
    app_port: int = Field(default=8000, ge=1, le=65535)

    log_level: str = "INFO"

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------

    # Example:
    # postgresql+asyncpg://monitoring:password@127.0.0.1:5432/monitoring_rsvn
    #
    # This value MUST be supplied through environment/.env in a real
    # deployment. There is deliberately no real database password here.
    database_url: str = (
        "postgresql+asyncpg://monitoring:change-me@127.0.0.1:5432/"
        "monitoring_rsvn"
    )

    database_pool_size: int = Field(default=10, ge=1)
    database_max_overflow: int = Field(default=20, ge=0)

    # ------------------------------------------------------------------
    # Runtime paths
    # ------------------------------------------------------------------

    # All paths are based on the project root rather than the current
    # working directory.
    #
    # This is important for systemd: the application must work correctly
    # even when started from a different working directory.
    data_dir: Path = PROJECT_ROOT / "data"
    log_dir: Path = PROJECT_ROOT / "logs"

    # Temporary directory for generated/intermediate files.
    temp_dir: Path = PROJECT_ROOT / "tmp"

    # ------------------------------------------------------------------
    # Camera import/export
    # ------------------------------------------------------------------

    cameras_xlsx: Path = PROJECT_ROOT / "data" / "cameras.xlsx"

    # ------------------------------------------------------------------
    # SNMP
    # ------------------------------------------------------------------

    snmp_community: str = "public"
    snmp_port: int = Field(default=161, ge=1, le=65535)

    # Network timeout for a single SNMP operation.
    snmp_timeout: float = Field(default=2.0, gt=0)

    # Number of SNMP retries.
    snmp_retries: int = Field(default=1, ge=0)

    # IMPORTANT:
    # This replaces the old ThreadPoolExecutor(max_workers=50).
    #
    # SNMP scanning will use:
    #
    #     asyncio.Semaphore(snmp_concurrency)
    #
    # instead of creating a thread pool and calling asyncio.run()
    # inside every worker.
    snmp_concurrency: int = Field(default=50, ge=1)

    # ------------------------------------------------------------------
    # WINK / RTSP statistics
    # ------------------------------------------------------------------

    # Path to the external wink-rtsp-stats executable.
    #
    # Example:
    #     /opt/monitoring-rsvn/bin/wink-rtsp-stats.exe
    #
    # The executable is intentionally NOT bundled into the Python
    # project and is NOT a Python dependency.
    wink_executable: Path = (
        PROJECT_ROOT / "bin" / "wink-rtsp-stats.exe"
    )

    # Maximum number of external WINK processes running simultaneously.
    #
    # Unlike SNMP, WINK invokes a blocking external executable, so a
    # bounded process pool/concurrency limit is appropriate here.
    wink_concurrency: int = Field(default=4, ge=1)

    # Maximum time allowed for one WINK measurement.
    wink_timeout: float = Field(default=300.0, gt=0)

    # ------------------------------------------------------------------
    # Monitoring worker
    # ------------------------------------------------------------------

    # Delay between complete monitoring cycles.
    #
    # Example:
    #     300 = run every 5 minutes
    monitoring_interval: int = Field(default=300, ge=1)

    # Number of attempts when a monitoring operation fails.
    monitoring_retries: int = Field(default=1, ge=0)

    # ------------------------------------------------------------------
    # Network filters
    # ------------------------------------------------------------------

    # Whether the "our networks" filter is enabled.
    #
    # 0 = disabled
    # 1 = enabled
    except_our_networks: int = Field(default=0, ge=0, le=1)

    # Comma-separated list in environment:
    #
    # OUR_NETWORKS=10.35.2.0/24,10.0.70.10
    #
    # Internally this becomes a tuple of strings.
    our_networks: str = "10.35.2.0/24,10.0.70.10"

    # ------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------

    # Whether ordinary application logs may include RTSP URLs.
    #
    # Keep disabled by default because RTSP URLs may contain credentials.
    log_sensitive_urls: bool = False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def our_networks_list(self) -> tuple[str, ...]:
        """Return configured network/IP filters as a tuple."""

        return tuple(
            network.strip()
            for network in self.our_networks.split(",")
            if network.strip()
        )

    def ensure_directories(self) -> None:
        """Create required runtime directories if they do not exist."""

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """
    Return the cached application settings instance.

    Using a cached singleton prevents every service/request from
    independently parsing environment variables.
    """

    settings = Settings()
    settings.ensure_directories()

    return settings
