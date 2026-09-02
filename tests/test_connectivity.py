from nexus.core.connectivity import (
    ConnectivityManager,
    ConnectivityStatus,
)


def test_connectivity_status_default():
    status = ConnectivityStatus()

    assert status.online is False
    assert status.latency_ms is None
    assert status.endpoint is None


def test_connectivity_manager_configuration():
    manager = ConnectivityManager(
        endpoint="https://example.com",
        timeout=5.0,
    )

    assert manager.endpoint == "https://example.com"
    assert manager.timeout == 5.0


def test_connectivity_check_online(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

    def fake_urlopen(request, timeout):
        assert request.full_url == "https://example.com"
        assert timeout == 3.0
        return FakeResponse()

    monkeypatch.setattr(
        "nexus.core.connectivity.urlopen",
        fake_urlopen,
    )

    manager = ConnectivityManager(
        endpoint="https://example.com",
    )

    status = manager.check()

    assert status.online is True
    assert status.endpoint == "https://example.com"


def test_connectivity_check_offline(monkeypatch):
    def fake_urlopen(request, timeout):
        raise OSError("Network unavailable")

    monkeypatch.setattr(
        "nexus.core.connectivity.urlopen",
        fake_urlopen,
    )

    manager = ConnectivityManager(
        endpoint="https://example.com",
    )

    status = manager.check()

    assert status.online is False
    assert status.endpoint == "https://example.com"
