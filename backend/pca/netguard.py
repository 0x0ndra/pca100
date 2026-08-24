"""Origin/Host allow-listing for the local API. Bottom layer: imports nothing from pca."""
import contextlib
import ipaddress
import socket
from urllib.parse import urlsplit

UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def _host_of(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlsplit(value if "//" in value else f"//{value}")
    return (parsed.hostname or "").lower() or None


def _host_allowed(host: str | None, remote_access: bool, lan_ips: frozenset[str]) -> bool:
    """Whether `host` may reach the API: loopback always, LAN only opt-in.

    A DNS name (other than "localhost") is never accepted, even on the LAN
    allow-list: an attacker who controls a name can rebind it to the
    operator's machine after the browser's same-origin check has passed, so
    only literal IP addresses are trusted here.
    """
    if host is None:
        return False
    if host == "localhost":
        return True
    try:
        addr = ipaddress.ip_address(host)
    except ValueError:
        return False
    if addr.is_loopback:
        return True
    if not remote_access:
        return False
    return host in lan_ips or addr.is_private or addr.is_link_local


def is_allowed_origin(origin: str | None, remote_access: bool, lan_ips: frozenset[str]) -> bool:
    """Whether a browser Origin may read live data or change instrument state.

    A missing Origin is a non-browser client (curl, a native app), which no
    hostile web page can drive, so it is allowed. A present Origin must
    resolve to loopback, or to a private/LAN address with `remote_access` on:
    WebSockets and form-shaped POSTs bypass CORS entirely, so without this
    check any site the operator happens to visit could stream measurements
    or stop a running calibration.
    """
    if origin is None:
        return True
    return _host_allowed(_host_of(origin), remote_access, lan_ips)


def is_allowed_host(
    host_header: str | None, remote_access: bool, port: int, lan_ips: frozenset[str]
) -> bool:
    """Whether the Host header names this machine, closing DNS-rebinding.

    A page on an attacker-controlled DNS name can point that name's A record
    at 127.0.0.1 *after* the browser trusted it, bypassing an Origin-only
    check entirely. Validating Host against loopback/known-LAN literals on
    every request defeats that regardless of what Origin claims.
    """
    del port  # kept for call-site clarity/future port pinning; not needed to decide
    return _host_allowed(_host_of(host_header), remote_access, lan_ips)


def local_ipv4s() -> frozenset[str]:
    """Best-effort set of this machine's LAN IPv4 addresses.

    Uses the primary-route address (open a UDP socket toward a public IP and
    read the local end; no packet is sent, no name is resolved). Hostname
    resolution is deliberately avoided: ``gethostbyname_ex`` blocks for the
    system DNS timeout on hosts whose name does not resolve (CI runners, some
    laptops), which would hang the remote-access toggle handler.
    """
    with contextlib.suppress(OSError):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.connect(("8.8.8.8", 80))
            return frozenset({sock.getsockname()[0]})
        finally:
            sock.close()
    return frozenset()


_PREFERRED_NETWORKS = (
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("10.0.0.0/8"),
)


def _preference_class(addr: ipaddress.IPv4Address) -> int:
    for rank, network in enumerate(_PREFERRED_NETWORKS):
        if addr in network:
            return rank
    return len(_PREFERRED_NETWORKS)


def ranked_connect_ips(ips: frozenset[str]) -> list[str]:
    """Order candidate IPv4 addresses for a phone to connect to.

    Loopback is dropped outright - a phone can never reach it. The rest are
    ranked so a typical home/office Wi-Fi network (192.168.0.0/16) sorts
    first, then 172.16.0.0/12, then 10.0.0.0/8, then anything else; stable
    (alphabetic) within each class.
    """
    candidates: list[ipaddress.IPv4Address] = []
    for ip in ips:
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            continue
        if isinstance(addr, ipaddress.IPv4Address) and not addr.is_loopback:
            candidates.append(addr)
    ordered = sorted(candidates, key=lambda addr: (_preference_class(addr), str(addr)))
    return [str(addr) for addr in ordered]
