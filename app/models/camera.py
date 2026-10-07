"""
Camera ORM model.
"""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Camera(Base):
    """Camera configuration and identity."""

    __tablename__ = "cameras"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    camera_number: Mapped[int] = mapped_column(
        Integer,
        unique=True,
        nullable=False,
    )

    name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    ip_address: Mapped[str] = mapped_column(
        INET,
        nullable=False,
        index=True,
    )

    manufacturer: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    model: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    operator: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    order_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    rtsp_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    credentials: Mapped["CameraCredential | None"] = relationship(
        "CameraCredential",
        back_populates="camera",
        uselist=False,
        cascade="all, delete-orphan",
    )

    snmp_measurements: Mapped[list["SnmpMeasurement"]] = relationship(
        "SnmpMeasurement",
        back_populates="camera",
        cascade="all, delete-orphan",
    )

    wink_measurements: Mapped[list["WinkMeasurement"]] = relationship(
        "WinkMeasurement",
        back_populates="camera",
        cascade="all, delete-orphan",
    )