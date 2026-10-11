"""Asynchronous SNMP scanner.

This module handles SNMP communication only.

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
    is_end_of_mib,
)
from pysnmp.proto.rfc1902 import OctetString
from pysnmp.proto.rfc1905 import NoSuchInstance, NoSuchObject
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

# tcpConnState: deprecated IPv4 TCP table.
TCP_CONN_STATE_PREFIX = TCP_BASE_OID + (13, 1, 1)

# tcpConnectionState: modern IP-version-neutral TCP table.
TCP_CONNECTION_STATE_PREFIX = TCP_BASE_OID + (19, 1, 7)

MAC_OIDS = {
    SCALAR_METRICS["mac_address_v6"],
    SCALAR_METRICS["mac_address_v4"],
}

RTSP_PORT = 554
TCP_WALK_MAX_REPETITIONS = 50
TCP_WALK_MAX_REQUESTS = 1000


@dataclass(frozen=True)
class RtspClient:
    """A client connected to the camera's RTSP port."""

    client_ip: str
    client_port: int


@dataclass
class RtspScanResult:
    """Result of scanning the TCP table for RTSP clients."""

    connected_clients: list[RtspClient] = field(
        default_factory=list,
    )

    @property
    def active_rtsp_sessions_count(self) -> int:
        """Return the number of distinct discovered RTSP clients."""

        return len(self.connected_clients)


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
        """Scan one camera.

        Return None when the scalar query or TCP table walk fails.
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

                rtsp_result = await self._scan_rtsp_connections(
                    ip,
                    engine,
                )

                if rtsp_result is None:
                    logger.warning(
                        "SNMP RTSP connection scan failed: %s",
                        ip,
                    )
                    return None

                result = SnmpScanResult(
                    ip=ip,
                    metrics=metrics,
                    active_rtsp_sessions_count=(
                        rtsp_result.active_rtsp_sessions_count
                    ),
                    connected_clients=rtsp_result.connected_clients,
                )

                logger.info("SNMP scan completed: %s", ip)
                return result

            except Exception:
                logger.exception("SNMP scan failed: %s", ip)
                return None

            finally:
                engine.close_dispatcher()

    async def scan_many(
        self,
        ips: list[str],
    ) -> list[SnmpScanResult]:
        """Scan multiple cameras concurrently.

        A failed camera does not prevent other scans from completing.
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

            if error_indication or error_status or not var_binds:
                logger.warning(
                    "SNMP scalar request returned an error for %s: %s",
                    ip,
                    error_indication or error_status or "empty response",
                )
                return None

            # Map only exact OID matches. Do not accept an unrelated OID
            # just because its text happens to end with a requested OID.
            oid_to_name = {
                oid: name
                for name, oid in SCALAR_METRICS.items()
            }
            results: dict[str, str] = {}

            for var_bind in var_binds:
                try:
                    oid_obj = var_bind[0]
                    value_obj = var_bind[1]
                except (IndexError, TypeError):
                    logger.warning(
                        "Malformed SNMP scalar response from %s",
                        ip,
                    )
                    continue

                if isinstance(
                    value_obj,
                    (NoSuchObject, NoSuchInstance),
                ):
                    logger.debug(
                        "SNMP metric is unavailable on %s: %s",
                        ip,
                        oid_obj,
                    )
                    continue

                oid_str = str(oid_obj)
                metric_name = oid_to_name.get(oid_str)

                if metric_name is None:
                    logger.debug(
                        "Unexpected OID in scalar response from %s: %s",
                        ip,
                        oid_str,
                    )
                    continue

                results[metric_name] = self._format_value(
                    oid_str,
                    value_obj,
                )

            if not results:
                logger.warning(
                    "SNMP scalar response contained no usable metrics: %s",
                    ip,
                )
                return None

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

        if oid in MAC_OIDS and isinstance(value, OctetString):
            return value.asOctets().hex()

        return str(value)

    async def _scan_rtsp_connections(
        self,
        ip: str,
        engine: SnmpEngine,
    ) -> RtspScanResult | None:
        """Walk the TCP subtree and find established RTSP connections.

        Return None if the walk fails or does not make forward progress.
        An empty RtspScanResult means the walk succeeded but no matching
        RTSP connections were found.
        """

        rtsp_clients: list[RtspClient] = []
        last_oid: tuple[int, ...] | None = None
        current_oid = ObjectType(
            ObjectIdentity(TCP_BASE_OID),
        )

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

            for _ in range(TCP_WALK_MAX_REQUESTS):
                (
                    error_indication,
                    error_status,
                    _,
                    var_binds,
                ) = await bulk_cmd(
                    engine,
                    community_data,
                    transport,
                    ContextData(),
                    0,
                    TCP_WALK_MAX_REPETITIONS,
                    current_oid,
                    lexicographicMode=True,
                )

                if error_indication or error_status:
                    logger.warning(
                        "SNMP TCP table walk failed for %s: %s",
                        ip,
                        error_indication or error_status,
                    )
                    return None

                if not var_binds:
                    # A successful empty response ends the walk.
                    return RtspScanResult(
                        connected_clients=rtsp_clients,
                    )

                reached_end_of_mib = False
                reached_end_of_subtree = False

                for var_bind in var_binds:
                    try:
                        oid_obj = var_bind[0]
                        value_obj = var_bind[1]
                    except (IndexError, TypeError):
                        logger.warning(
                            "Malformed SNMP TCP table response from %s",
                            ip,
                        )
                        return None

                    # endOfMibView is a protocol marker, not a real table
                    # entry. Check it before comparing OID progress.
                    if is_end_of_mib((var_bind,)):
                        reached_end_of_mib = True
                        break

                    oid_tuples = tuple(oid_obj)

                    # GETBULK results must advance in lexicographic order.
                    if (
                        last_oid is not None
                        and oid_tuples <= last_oid
                    ):
                        logger.warning(
                            "SNMP TCP walk returned a non-increasing "
                            "OID for %s: %s",
                            ip,
                            oid_tuples,
                        )
                        return None

                    last_oid = oid_tuples

                    # The first OID outside the requested TCP subtree marks
                    # normal completion of this lexicographic walk.
                    if oid_tuples[:len(TCP_BASE_OID)] != TCP_BASE_OID:
                        reached_end_of_subtree = True
                        break

                    current_oid = ObjectType(
                        ObjectIdentity(oid_tuples),
                    )

                    state_value = str(value_obj).strip().lower()
                    if state_value not in {
                        "5",
                        "established",
                        "established(5)",
                    }:
                        continue

                    client = self._extract_rtsp_client(oid_tuples)
                    if client is None:
                        continue

                    if self._is_filtered_client(client.client_ip):
                        continue

                    if client not in rtsp_clients:
                        rtsp_clients.append(client)

                if reached_end_of_mib or reached_end_of_subtree:
                    return RtspScanResult(
                        connected_clients=rtsp_clients,
                    )

            logger.warning(
                "SNMP TCP table walk exceeded the request limit for %s",
                ip,
            )
            return None

        except Exception:
            logger.exception(
                "RTSP TCP table scan failed: %s",
                ip,
            )
            return None

    @staticmethod
    def _extract_rtsp_client(
        oid_tuples: tuple[int, ...],
    ) -> RtspClient | None:
        """Extract a client from a TCP state-column OID.

        Supports the classic IPv4 tcpConnTable and the modern
        tcpConnectionTable, including IPv4, IPv6, IPv4z and IPv6z
        address indexes in the modern table.
        """

        # Classic tcpConnState:
        # .1.3.6.1.2.1.6.13.1.1.<local IPv4>.<local port>
        #     .<remote IPv4>.<remote port>
        if oid_tuples[:10] == TCP_CONN_STATE_PREFIX:
            if len(oid_tuples) != 20:
                return None

            local_port = oid_tuples[14]
            remote_address = oid_tuples[15:19]
            remote_port = oid_tuples[19]

            if local_port != RTSP_PORT:
                return None

            if not 0 <= remote_port <= 65535:
                return None

            try:
                client_ip = str(
                    ipaddress.IPv4Address(bytes(remote_address)),
                )
            except (ValueError, ipaddress.AddressValueError):
                return None

            return RtspClient(
                client_ip=client_ip,
                client_port=remote_port,
            )

        # Modern tcpConnectionState:
        # .1.3.6.1.2.1.6.19.1.7.<index>
        #
        # The variable-length InetAddress index includes a length
        # subidentifier. This means fixed offsets are not safe for IPv6.
        if oid_tuples[:10] != TCP_CONNECTION_STATE_PREFIX:
            return None

        cursor = 10

        try:
            # Local address type and variable-length local address.
            _local_address_type = oid_tuples[cursor]
            cursor += 1

            local_address_length = oid_tuples[cursor]
            cursor += 1

            if local_address_length < 1:
                return None

            cursor += local_address_length

            # Local port.
            local_port = oid_tuples[cursor]
            cursor += 1

            # Remote address type and variable-length remote address.
            remote_address_type = oid_tuples[cursor]
            cursor += 1

            remote_address_length = oid_tuples[cursor]
            cursor += 1

            if remote_address_length < 1:
                return None

            remote_address = oid_tuples[
                cursor:cursor + remote_address_length
            ]
            cursor += remote_address_length

            # Remote port must be the final index component.
            remote_port = oid_tuples[cursor]
            cursor += 1

        except IndexError:
            return None

        if cursor != len(oid_tuples):
            return None

        if local_port != RTSP_PORT:
            return None

        if not 0 <= remote_port <= 65535:
            return None

        try:
            if remote_address_type == 1 and remote_address_length == 4:
                client_ip = str(
                    ipaddress.IPv4Address(bytes(remote_address)),
                )

            elif (
                remote_address_type == 2
                and remote_address_length == 16
            ):
                client_ip = str(
                    ipaddress.IPv6Address(bytes(remote_address)),
                )

            elif (
                remote_address_type == 3
                and remote_address_length == 8
            ):
                # IPv4z consists of a 4-byte IPv4 address followed by
                # a 4-byte zone index. The zone is not part of the IP.
                client_ip = str(
                    ipaddress.IPv4Address(
                        bytes(remote_address[:4]),
                    ),
                )

            elif (
                remote_address_type == 4
                and remote_address_length == 20
            ):
                # IPv6z consists of a 16-byte IPv6 address followed by
                # a 4-byte zone index.
                client_ip = str(
                    ipaddress.IPv6Address(
                        bytes(remote_address[:16]),
                    ),
                )

            else:
                # Unsupported address type or malformed index.
                return None

        except ValueError:
            return None

        return RtspClient(
            client_ip=client_ip,
            client_port=remote_port,
        )

    def _is_filtered_client(
        self,
        client_ip: str,
    ) -> bool:
        """Return True when a client belongs to an excluded network."""

        # Preserve the existing configuration semantics.
        if self.settings.except_our_networks != 0:
            return False

        try:
            client_address = ipaddress.ip_address(client_ip)
        except ValueError:
            logger.warning(
                "Invalid client IP encountered: %s",
                client_ip,
            )
            return False

        for network in self.settings.our_networks_list:
            try:
                if "/" not in network:
                    network_address = ipaddress.ip_address(network)
                    if client_address == network_address:
                        return True
                    continue

                network_object = ipaddress.ip_network(
                    network,
                    strict=False,
                )

                if client_address in network_object:
                    return True

            except ValueError:
                # One invalid network entry should not prevent checking
                # the remaining configured networks.
                logger.warning(
                    "Invalid network in SNMP client filter: %s",
                    network,
                )

        return False