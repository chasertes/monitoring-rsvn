"""Asynchronous SNMP scanner.

This module contains only SNMP protocol communication.

The scanner does not:

* access PostgreSQL;
* read Excel files;
* write JSON files;
* calculate application-level camera status;
* contain FastAPI logic.

Business logic and persistence belong to the service layer.
"""

import asyncio
import ipaddress
from dataclasses import dataclass, field

from pysnmp.hlapi.v3arch.asyncio import (
CommunityData,
ContextData,
SnmpEngine,
UdpTransportTarget,
bulk_cmd,
get_cmd,
)
from pysnmp.proto.rfc1902 import OctetString
from pysnmp.smi.rfc1902 import ObjectIdentity, ObjectType

from app.config import Settings, get_settings
from app.logging_config import get_logger

logger = get_logger("snmp_scanner")

SCALAR_METRICS = {
"sys_descr": "1.3.6.1.2.1.1.1.0",
"sys_uptime": "1.3.6.1.2.1.1.3.0",
"sys_name": "1.3.6.1.2.1.1.5.0",
"ip_in_receives": "1.3.6.1.2.1.4.3.0",
"ip_in_hdr_errors": "1.3.6.1.2.1.4.4.0",
"ip_in_addr_errors": "1.3.6.1.2.1.4.5.0",
"ip_out_requests": "1.3.6.1.2.1.4.10.0",
"icmp_in_msgs": "1.3.6.1.2.1.5.1.0",
"icmp_out_echo_reps": "1.3.6.1.2.1.5.22.0",
"mac_address_v6": "1.3.6.1.2.1.55.1.5.1.8.2",
"mac_address_v4": "1.3.6.1.2.1.2.2.1.6.2",
"interface_speed": "1.3.6.1.2.1.2.2.1.5.2",
}

TCP_BASE_OID = (1, 3, 6, 1, 2, 1, 6)

MAC_OIDS = {
SCALAR_METRICS["mac_address_v6"],
SCALAR_METRICS["mac_address_v4"],
}

@dataclass(frozen=True)
class RtspClient:
"""A client connected to the camera's RTSP port."""


client_ip: str
client_port: int


@dataclass
class SnmpScanResult:
"""Structured result returned by the SNMP scanner."""


ip: str
metrics: dict[str, str] = field(default_factory=dict)
active_rtsp_sessions_count: int = 0
connected_clients: list[RtspClient] = field(
    default_factory=list,
)


class SnmpScanner:
"""Asynchronous SNMP scanner with bounded concurrency."""


def __init__(
    self,
    settings: Settings | None = None,
) -> None:
    """Initialize the scanner with application settings."""

    self.settings = settings or get_settings()
    self._semaphore = asyncio.Semaphore(
        self.settings.snmp_concurrency,
    )

async def scan(
    self,
    ip: str,
) -> SnmpScanResult | None:
    """Scan one camera by IP address.

    Returns None when the camera cannot be queried successfully.
    """

    async with self._semaphore:
        logger.info("SNMP scan started: %s", ip)

        engine = SnmpEngine()

        try:
            metrics = await self._fetch_scalars(
                ip,
                engine,
            )

            if not metrics:
                logger.warning(
                    "SNMP scalar query failed: %s",
                    ip,
                )
                return None

            rtsp_data = await self._scan_rtsp_connections(
                ip,
                engine,
            )

            result = SnmpScanResult(
                ip=ip,
                metrics=metrics,
                active_rtsp_sessions_count=(
                    rtsp_data["active_rtsp_sessions_count"]
                ),
                connected_clients=rtsp_data["connected_clients"],
            )

            logger.info(
                "SNMP scan completed: %s",
                ip,
            )

            return result

        except Exception:
            logger.exception(
                "SNMP scan failed: %s",
                ip,
            )
            return None

        finally:
            engine.close_dispatcher()

async def scan_many(
    self,
    ips: list[str],
) -> list[SnmpScanResult]:
    """Scan multiple cameras concurrently.

    Individual camera failures are isolated and do not stop the
    complete scan.
    """

    results = await asyncio.gather(
        *(self.scan(ip) for ip in ips),
        return_exceptions=False,
    )

    return [
        result
        for result in results
        if result is not None
    ]

async def _fetch_scalars(
    self,
    ip: str,
    engine: SnmpEngine,
) -> dict[str, str] | None:
    """Fetch configured scalar SNMP metrics."""

    try:
        community_data = CommunityData(
            self.settings.snmp_community,
            mpModel=1,
        )

        transport = await UdpTransportTarget.create(
            (ip, self.settings.snmp_port),
            timeout=self.settings.snmp_timeout,
            retries=self.settings.snmp_retries,
        )

        (
            error_indication,
            error_status,
            _,
            var_binds,
        ) = await get_cmd(
            engine,
            community_data,
            transport,
            ContextData(),
            *[
                ObjectType(ObjectIdentity(oid))
                for oid in SCALAR_METRICS.values()
            ],
        )

        if (
            error_indication
            or error_status
            or not var_binds
        ):
            return None

        results: dict[str, str] = {}

        for var_bind in var_binds:
            oid_obj = var_bind[0]
            value_obj = var_bind[1]
            oid_str = str(oid_obj)

            value_str = self._format_value(
                oid_str,
                value_obj,
            )

            for name, target_oid in SCALAR_METRICS.items():
                if oid_str.endswith(
                    target_oid.lstrip("."),
                ):
                    results[name] = value_str
                    break

        return results

    except Exception:
        logger.exception(
            "SNMP scalar query failed: %s",
            ip,
        )
        return None

@staticmethod
def _format_value(
    oid: str,
    value: object,
) -> str:
    """Convert a PySNMP value into a stable string representation."""

    if isinstance(value, OctetString) and any(
        mac_oid in oid
        for mac_oid in MAC_OIDS
    ):
        return value.asOctets().hex()

    return str(value)

async def _scan_rtsp_connections(
    self,
    ip: str,
    engine: SnmpEngine,
) -> dict[str, object]:
    """Walk the TCP table and find established RTSP connections."""

    rtsp_clients: list[RtspClient] = []

    try:
        community_data = CommunityData(
            self.settings.snmp_community,
            mpModel=1,
        )

        transport = await UdpTransportTarget.create(
            (ip, self.settings.snmp_port),
            timeout=self.settings.snmp_timeout,
            retries=self.settings.snmp_retries,
        )

        current_oid = ObjectType(
            ObjectIdentity("1.3.6.1.2.1.6"),
        )

        is_walking = True

        while is_walking:
            (
                error_indication,
                error_status,
                _,
                var_binds_table,
            ) = await bulk_cmd(
                engine,
                community_data,
                transport,
                ContextData(),
                0,
                50,
                current_oid,
                lexicographicMode=True,
            )

            if (
                error_indication
                or error_status
                or not var_binds_table
            ):
                break

            flat_var_binds = []

            for item in var_binds_table:
                if isinstance(item, (list, tuple)):
                    flat_var_binds.extend(item)
                else:
                    flat_var_binds.append(item)

            for var_bind in flat_var_binds:
                try:
                    oid_obj = var_bind[0]
                    value_obj = var_bind[1]
                except (IndexError, TypeError):
                    continue

                oid_tuples = tuple(oid_obj)
                state_value = str(value_obj).lower()

                if oid_tuples[:7] != TCP_BASE_OID:
                    is_walking = False
                    break

                current_oid = ObjectType(
                    ObjectIdentity(oid_tuples),
                )

                if (
                    "5" not in state_value
                    and "established" not in state_value
                ):
                    continue

                client = self._extract_rtsp_client(
                    oid_tuples,
                )

                if client is not None:
                    if not self._is_filtered_client(
                        client.client_ip,
                    ):
                        if client not in rtsp_clients:
                            rtsp_clients.append(client)

    except Exception:
        logger.exception(
            "RTSP TCP table scan failed: %s",
            ip,
        )

    return {
        "active_rtsp_sessions_count": len(rtsp_clients),
        "connected_clients": rtsp_clients,
    }

@staticmethod
def _extract_rtsp_client(
    oid_tuples: tuple[int, ...],
) -> RtspClient | None:
    """Extract an RTSP client from supported TCP table formats."""

    # Classic tcpConnTable (.13).
    if len(oid_tuples) == 20 and oid_tuples[7] == 13:
        local_port = oid_tuples[14]

        if local_port != 554:
            return None

        remote_ip = ".".join(
            str(part)
            for part in oid_tuples[15:19]
        )
        remote_port = oid_tuples[19]

        return RtspClient(
            client_ip=remote_ip,
            client_port=int(remote_port),
        )

    # Modern tcpConnectionTable (.19).
    if len(oid_tuples) == 24 and oid_tuples[7] == 19:
        local_port = oid_tuples[16]

        if local_port != 554:
            return None

        remote_ip = ".".join(
            str(part)
            for part in oid_tuples[19:23]
        )
        remote_port = oid_tuples[23]

        return RtspClient(
            client_ip=remote_ip,
            client_port=int(remote_port),
        )

    return None

def _is_filtered_client(
    self,
    client_ip: str,
) -> bool:
    """Return True when a client belongs to an excluded network."""

    if self.settings.except_our_networks != 0:
        return False

    try:
        client_address = ipaddress.ip_address(client_ip)

        for network in self.settings.our_networks_list:
            if "/" not in network:
                if (
                    client_address
                    == ipaddress.ip_address(network)
                ):
                    return True

                continue

            network_object = ipaddress.ip_network(
                network,
                strict=False,
            )

            if client_address in network_object:
                return True

    except ValueError:
        logger.warning(
            "Invalid client IP encountered: %s",
            client_ip,
        )

    return False