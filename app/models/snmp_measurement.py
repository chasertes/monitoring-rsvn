"""
SNMP measurement ORM model.
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Integer,
    String,
    Text,
    ForeignKey,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SnmpMeasurement(Base):
    """SNMP measurement result for a camera."""

    __tablename__ = "snmp_measurements"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    camera_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("cameras.id"),
        nullable=False,
    )

    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    sys_descr: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    sys_uptime_ticks: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    sys_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    ip_in_receives: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    ip_in_hdr_errors: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    ip_in_addr_errors: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    ip_out_requests: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    icmp_in_msgs: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    icmp_out_echo_reps: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    mac_address: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    interface_speed: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    active_rtsp_sessions_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    scan_duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    camera: Mapped["Camera"] = relationship(
        "Camera",
        back_populates="snmp_measurements",
    )

    rtsp_clients: Mapped[list["RtspClient"]] = relationship(
        "RtspClient",
        back_populates="snmp_measurement",
        cascade="all, delete-orphan",
    )