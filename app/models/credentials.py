"""
Camera credentials ORM model.
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CameraCredential(Base):
    """Credentials and SNMP data associated with a camera."""

    __tablename__ = "camera_credentials"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    camera_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("cameras.id"),
        unique=True,
        nullable=False,
    )

    username: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    password: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    snmp_community: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
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

    camera: Mapped["Camera"] = relationship(
        "Camera",
        back_populates="credentials",
    )