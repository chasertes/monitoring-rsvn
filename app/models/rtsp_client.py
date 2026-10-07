"""
RTSP client ORM model.
"""

from sqlalchemy import BigInteger, ForeignKey, INET, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RtspClient(Base):
    """RTSP client detected during an SNMP measurement."""

    __tablename__ = "rtsp_clients"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    snmp_measurement_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "snmp_measurements.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    client_ip: Mapped[str] = mapped_column(
        INET,
        nullable=False,
        index=True,
    )

    client_port: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    snmp_measurement: Mapped["SnmpMeasurement"] = relationship(
        "SnmpMeasurement",
        back_populates="rtsp_clients",
    )