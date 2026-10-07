"""
WINK measurement ORM model.
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Double,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class WinkMeasurement(Base):
    """WINK measurement result for a camera."""

    __tablename__ = "wink_measurements"

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

    start_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    duration_s: Mapped[float | None] = mapped_column(
        Double,
        nullable=True,
    )

    rtsp_connect_time_ms: Mapped[float | None] = mapped_column(
        Double,
        nullable=True,
    )

    first_rtp_time_ms: Mapped[float | None] = mapped_column(
        Double,
        nullable=True,
    )

    streams_detected: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    total_bitrate_kbps_avg: Mapped[float | None] = mapped_column(
        Double,
        nullable=True,
    )

    total_packets: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    total_packets_lost_estimated: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    ssrc_stable: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    transport_mode: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    rtcp_received: Mapped[bool | None] = mapped_column(
        Boolean,
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
        back_populates="wink_measurements",
    )

    streams: Mapped[list["WinkStream"]] = relationship(
        "WinkStream",
        back_populates="wink_measurement",
        cascade="all, delete-orphan",
    )