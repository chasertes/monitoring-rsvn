"""Create initial database schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the initial monitoring database schema."""

    # ------------------------------------------------------------------
    # cameras
    # ------------------------------------------------------------------

    op.create_table(
        "cameras",
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "camera_number",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "ip_address",
            postgresql.INET(),
            nullable=False,
        ),
        sa.Column(
            "manufacturer",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "model",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "operator",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "order_number",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "rtsp_url",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "enabled",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_cameras"),
        ),
        sa.UniqueConstraint(
            "camera_number",
            name=op.f("uq_cameras_camera_number"),
        ),
    )

    op.create_index(
        op.f("ix_cameras_ip_address"),
        "cameras",
        ["ip_address"],
        unique=False,
    )

    op.create_index(
        op.f("ix_cameras_enabled"),
        "cameras",
        ["enabled"],
        unique=False,
    )

    # ------------------------------------------------------------------
    # camera_credentials
    # ------------------------------------------------------------------

    op.create_table(
        "camera_credentials",
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "camera_id",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "username",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "password",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "snmp_community",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["camera_id"],
            ["cameras.id"],
            name=op.f(
                "fk_camera_credentials_camera_id_cameras"
            ),
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_camera_credentials"),
        ),
        sa.UniqueConstraint(
            "camera_id",
            name=op.f("uq_camera_credentials_camera_id"),
        ),
    )

    # ------------------------------------------------------------------
    # snmp_measurements
    # ------------------------------------------------------------------

    op.create_table(
        "snmp_measurements",
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "camera_id",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "measured_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "sys_descr",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "sys_uptime_ticks",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "sys_name",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "ip_in_receives",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "ip_in_hdr_errors",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "ip_in_addr_errors",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "ip_out_requests",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "icmp_in_msgs",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "icmp_out_echo_reps",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "mac_address",
            sa.String(length=32),
            nullable=True,
        ),
        sa.Column(
            "interface_speed",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "active_rtsp_sessions_count",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "scan_duration_ms",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["camera_id"],
            ["cameras.id"],
            name=op.f(
                "fk_snmp_measurements_camera_id_cameras"
            ),
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_snmp_measurements"),
        ),
    )

    op.create_index(
        op.f("ix_snmp_measurements_measured_at"),
        "snmp_measurements",
        ["measured_at"],
        unique=False,
    )

    op.create_index(
        op.f("ix_snmp_measurements_status"),
        "snmp_measurements",
        ["status"],
        unique=False,
    )

    op.create_index(
        "ix_snmp_measurements_camera_id_measured_at",
        "snmp_measurements",
        ["camera_id", "measured_at"],
        unique=False,
    )

    # ------------------------------------------------------------------
    # rtsp_clients
    # ------------------------------------------------------------------

    op.create_table(
        "rtsp_clients",
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "snmp_measurement_id",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "client_ip",
            postgresql.INET(),
            nullable=False,
        ),
        sa.Column(
            "client_port",
            sa.Integer(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["snmp_measurement_id"],
            ["snmp_measurements.id"],
            name=op.f(
                "fk_rtsp_clients_snmp_measurement_id_snmp_measurements"
            ),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_rtsp_clients"),
        ),
    )

    op.create_index(
        op.f("ix_rtsp_clients_client_ip"),
        "rtsp_clients",
        ["client_ip"],
        unique=False,
    )

    op.create_index(
        "ix_rtsp_clients_snmp_measurement_id",
        "rtsp_clients",
        ["snmp_measurement_id"],
        unique=False,
    )

    # ------------------------------------------------------------------
    # wink_measurements
    # ------------------------------------------------------------------

    op.create_table(
        "wink_measurements",
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "camera_id",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "measured_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "start_time",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "end_time",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "duration_s",
            sa.Double(),
            nullable=True,
        ),
        sa.Column(
            "rtsp_connect_time_ms",
            sa.Double(),
            nullable=True,
        ),
        sa.Column(
            "first_rtp_time_ms",
            sa.Double(),
            nullable=True,
        ),
        sa.Column(
            "streams_detected",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "total_bitrate_kbps_avg",
            sa.Double(),
            nullable=True,
        ),
        sa.Column(
            "total_packets",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "total_packets_lost_estimated",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "ssrc_stable",
            sa.Boolean(),
            nullable=True,
        ),
        sa.Column(
            "transport_mode",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "rtcp_received",
            sa.Boolean(),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["camera_id"],
            ["cameras.id"],
            name=op.f(
                "fk_wink_measurements_camera_id_cameras"
            ),
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_wink_measurements"),
        ),
    )

    op.create_index(
        op.f("ix_wink_measurements_measured_at"),
        "wink_measurements",
        ["measured_at"],
        unique=False,
    )

    op.create_index(
        op.f("ix_wink_measurements_status"),
        "wink_measurements",
        ["status"],
        unique=False,
    )

    op.create_index(
        "ix_wink_measurements_camera_id_measured_at",
        "wink_measurements",
        ["camera_id", "measured_at"],
        unique=False,
    )

    # ------------------------------------------------------------------
    # wink_streams
    # ------------------------------------------------------------------

    op.create_table(
        "wink_streams",
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "wink_measurement_id",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "ssrc",
            sa.String(length=32),
            nullable=True,
        ),
        sa.Column(
            "media_type",
            sa.String(length=32),
            nullable=True,
        ),
        sa.Column(
            "codec",
            sa.String(length=64),
            nullable=True,
        ),
        sa.Column(
            "payload_type",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "clock_rate",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "packets_total",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "packets_lost_estimated",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "packets_out_of_order",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "packets_duplicated",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "jitter_ms_avg",
            sa.Double(),
            nullable=True,
        ),
        sa.Column(
            "jitter_ms_max",
            sa.Double(),
            nullable=True,
        ),
        sa.Column(
            "bitrate_kbps_avg",
            sa.Double(),
            nullable=True,
        ),
        sa.Column(
            "bitrate_kbps_instant",
            sa.Double(),
            nullable=True,
        ),
        sa.Column(
            "first_seq",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "last_seq",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "first_packet_ts",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_packet_ts",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "burst_avg_per_100ms",
            sa.Double(),
            nullable=True,
        ),
        sa.Column(
            "burst_max_per_100ms",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "burst_ratio",
            sa.Double(),
            nullable=True,
        ),
        sa.Column(
            "burst_status",
            sa.String(length=32),
            nullable=True,
        ),
        sa.Column(
            "clock_drift_ms",
            sa.Double(),
            nullable=True,
        ),
        sa.Column(
            "clock_drift_trend_ms_per_min",
            sa.Double(),
            nullable=True,
        ),
        sa.Column(
            "clock_drift_status",
            sa.String(length=32),
            nullable=True,
        ),
        sa.Column(
            "fingerprint",
            sa.Text(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["wink_measurement_id"],
            ["wink_measurements.id"],
            name=op.f(
                "fk_wink_streams_wink_measurement_id_wink_measurements"
            ),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_wink_streams"),
        ),
    )

    op.create_index(
        op.f("ix_wink_streams_wink_measurement_id"),
        "wink_streams",
        ["wink_measurement_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_wink_streams_ssrc"),
        "wink_streams",
        ["ssrc"],
        unique=False,
    )

    op.create_index(
        op.f("ix_wink_streams_codec"),
        "wink_streams",
        ["codec"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the initial monitoring database schema."""

    op.drop_index(
        op.f("ix_wink_streams_codec"),
        table_name="wink_streams",
    )
    op.drop_index(
        op.f("ix_wink_streams_ssrc"),
        table_name="wink_streams",
    )
    op.drop_index(
        op.f("ix_wink_streams_wink_measurement_id"),
        table_name="wink_streams",
    )
    op.drop_table("wink_streams")

    op.drop_index(
        "ix_wink_measurements_camera_id_measured_at",
        table_name="wink_measurements",
    )
    op.drop_index(
        op.f("ix_wink_measurements_status"),
        table_name="wink_measurements",
    )
    op.drop_index(
        op.f("ix_wink_measurements_measured_at"),
        table_name="wink_measurements",
    )
    op.drop_table("wink_measurements")

    op.drop_index(
        "ix_rtsp_clients_snmp_measurement_id",
        table_name="rtsp_clients",
    )
    op.drop_index(
        op.f("ix_rtsp_clients_client_ip"),
        table_name="rtsp_clients",
    )
    op.drop_table("rtsp_clients")

    op.drop_index(
        "ix_snmp_measurements_camera_id_measured_at",
        table_name="snmp_measurements",
    )
    op.drop_index(
        op.f("ix_snmp_measurements_status"),
        table_name="snmp_measurements",
    )
    op.drop_index(
        op.f("ix_snmp_measurements_measured_at"),
        table_name="snmp_measurements",
    )
    op.drop_table("snmp_measurements")

    op.drop_table("camera_credentials")

    op.drop_index(
        op.f("ix_cameras_enabled"),
        table_name="cameras",
    )
    op.drop_index(
        op.f("ix_cameras_ip_address"),
        table_name="cameras",
    )
    op.drop_table("cameras")