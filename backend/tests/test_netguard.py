import pytest

from pca.netguard import is_allowed_host, is_allowed_origin, local_ipv4s, ranked_connect_ips

LAN = frozenset({"192.168.1.50"})


def test_loopback_origin_always_allowed() -> None:
    assert is_allowed_origin("http://127.0.0.1:5175", False, LAN) is True
    assert is_allowed_origin("http://127.0.0.1:5175", True, LAN) is True
    assert is_allowed_origin("http://localhost:5175", False, LAN) is True
    assert is_allowed_origin("http://[::1]:5175", False, LAN) is True


def test_loopback_host_always_allowed() -> None:
    assert is_allowed_host("127.0.0.1:8320", False, 8320, LAN) is True
    assert is_allowed_host("localhost:8320", False, 8320, LAN) is True


def test_missing_origin_allowed_for_non_browser_client() -> None:
    assert is_allowed_origin(None, False, LAN) is True


def test_lan_origin_gated_on_remote_access() -> None:
    assert is_allowed_origin("http://192.168.1.50:5175", False, LAN) is False
    assert is_allowed_origin("http://192.168.1.50:5175", True, LAN) is True


def test_private_ip_gated_on_remote_access_even_when_not_in_lan_list() -> None:
    assert is_allowed_origin("http://10.0.0.5", False, LAN) is False
    assert is_allowed_origin("http://10.0.0.5", True, LAN) is True


def test_public_ip_never_allowed() -> None:
    assert is_allowed_origin("https://8.8.8.8", True, LAN) is False


@pytest.mark.parametrize(
    "origin",
    [
        "http://evil.local",
        "http://x.home",
        "http://y.lan",
        "http://z.internal",
        "http://pca.local:5175",
        "http://booth-pc.lan",
    ],
)
def test_dns_names_never_allowed(origin: str) -> None:
    assert is_allowed_origin(origin, True, LAN) is False


@pytest.mark.parametrize("origin", ["null", "", "not a url", "https://evil.example.com"])
def test_opaque_and_remote_origins_rejected(origin: str) -> None:
    assert is_allowed_origin(origin, True, LAN) is False


def test_hostname_matching_is_case_insensitive() -> None:
    assert is_allowed_origin("http://LocalHost:5175", False, LAN) is True


def test_rebinding_host_rejected() -> None:
    assert is_allowed_host("attacker.com", True, 8320, LAN) is False


def test_lan_host_gated_on_remote_access() -> None:
    assert is_allowed_host("192.168.1.50:8320", True, 8320, LAN) is True
    assert is_allowed_host("192.168.1.50:8320", False, 8320, LAN) is False


def test_missing_host_header_rejected() -> None:
    assert is_allowed_host(None, True, 8320, LAN) is False


def test_local_ipv4s_returns_frozenset_of_str() -> None:
    result = local_ipv4s()
    assert isinstance(result, frozenset)
    assert all(isinstance(ip, str) for ip in result)


def test_local_ipv4s_returns_empty_without_hanging_when_no_route(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import socket as socket_module

    class _NoRouteSocket:
        def __init__(self, *_: object) -> None:
            pass

        def connect(self, *_: object) -> None:
            raise OSError("network is unreachable")

        def close(self) -> None:
            pass

    monkeypatch.setattr(socket_module, "socket", _NoRouteSocket)
    assert local_ipv4s() == frozenset()


def test_ranked_connect_ips_drops_loopback_and_prefers_home_wifi() -> None:
    mixed = frozenset({"127.0.0.1", "10.211.55.2", "192.168.1.50"})
    result = ranked_connect_ips(mixed)
    assert "127.0.0.1" not in result
    assert result[0] == "192.168.1.50"
    assert result[1] == "10.211.55.2"


def test_ranked_connect_ips_orders_by_class_192_then_172_then_10_then_other() -> None:
    mixed = frozenset({"203.0.113.5", "10.0.0.1", "172.20.0.1", "192.168.0.1"})
    assert ranked_connect_ips(mixed) == [
        "192.168.0.1",
        "172.20.0.1",
        "10.0.0.1",
        "203.0.113.5",
    ]


def test_ranked_connect_ips_stable_within_class() -> None:
    mixed = frozenset({"192.168.1.50", "192.168.1.10"})
    assert ranked_connect_ips(mixed) == ["192.168.1.10", "192.168.1.50"]


def test_ranked_connect_ips_only_loopback_returns_empty() -> None:
    assert ranked_connect_ips(frozenset({"127.0.0.1"})) == []


def test_ranked_connect_ips_empty_input_returns_empty() -> None:
    assert ranked_connect_ips(frozenset()) == []
