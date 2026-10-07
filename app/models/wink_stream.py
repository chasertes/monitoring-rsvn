"""
WINK stream ORM model.
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Double,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class WinkStream(Base):
    """Individual media stream detected during a WINK measurement."""

    __tablename__ = "wink_streams"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    wink_measurement_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "wink_measurements.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    ssrc: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    media_type: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    codec: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    payload_type: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    clock_rate: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    packets_total: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    packets_lost_estimated: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    packets_out_of_order: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    packets_duplicated: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    jitter_ms_avg: Mapped[float | None] = mapped_column(
        Double,
        nullable=True,
    )

    jitter_ms_max: Mapped[float | None] = mapped_column(
        Double,
        nullable=True,
    )

    bitrate_kbps_avg: Mapped[float | None] = mapped_column(
        Double,
        nullable=True,
    )

    bitrate_kbps_instant: Mapped[float | None] = mapped_column(
        Double,
        nullable=True,
    )

    first_seq: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    last_seq: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    first_packet_ts: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_packet_ts: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    burst_avg_per_100ms: Mapped[float | None] = mapped_column(
        Double,
        nullable=True,
    )

    burst_max_per_100ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    burst_ratio: Mapped[float | None] = mapped_column(
        Double,
        nullable=True,
    )

    burst_status: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    clock_drift_ms: Mapped[float | None] = mapped_column(
        Double,
        nullable=True,
    )

    clock_drift_trend_ms_per_min: Mapped[float | None] = mapped_column(
        Double,
        nullable=True,
    )

    clock_drift_status: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    fingerprint: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    wink_measurement: Mapped["WinkMeasurement"] = relationship(
        "WinkMeasurement",
        back_populates="streams",
    )