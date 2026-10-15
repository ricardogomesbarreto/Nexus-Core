"""v0.8.3: Ubuntu first-run doctor is read-only, bounded and loopback-only."""
import json
import subprocess
from types import SimpleNamespace

import pytest

from nexus.platforms import LinuxProfile
from nexus.platforms import doctor


class Response:
    def __init__(self, status=200, body=b'{"version":"0.11.0"}'):
        self.status = status
        self.body = body
    def read(self, n):
        return self.body[:n]


class LocalOllama:
    instances = []
    def __init__(self, host, port, *, timeout):
        self.address = (host, port)
        self.timeout = timeout
        self.requests = []
        self.response = Response()
        self.closed = False
        self.instances.append(self)
    def request(self, method, path):
        self.requests.append((method, path))
    def getresponse(self):
        return self.response
    def close(self):
        self.closed = True


def test_postgres_uses_fixed_loopback_and_no_credentials():
    calls = []
    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0)
    result = doctor.postgres_readiness(run=run, which=lambda cmd: "/usr/bin/pg_isready")
    assert result == {"status": "accepting_connections", "reachable": True}
    argv, kwargs = calls[0]
    assert argv == ["/usr/bin/pg_isready", "-h", "127.0.0.1", "-p", "5432", "-t", "2"]
    assert kwargs["timeout"] == 3
    assert kwargs["stdin"] == subprocess.DEVNULL
    assert kwargs["stdout"] == subprocess.DEVNULL
    assert kwargs.get("shell") is None


@pytest.mark.parametrize("returncode", [1, 2, 3])
def test_postgres_unready_does_not_expose_subprocess_output(returncode):
    def run(args, **kwargs):
        return subprocess.CompletedProcess(args, returncode, stdout=b"password")
    result = doctor.postgres_readiness(run=run, which=lambda _: "/usr/bin/pg_isready")
    assert result == {"status": "unavailable", "reachable": False}
    assert "password" not in json.dumps(result)


def test_postgres_missing_client_and_timeout():
    assert doctor.postgres_readiness(which=lambda _: None) == {
        "status": "missing_client", "reachable": False,
    }
    def timeout(*args, **kw):
        raise subprocess.TimeoutExpired(args[0], 3)
    assert doctor.postgres_readiness(run=timeout, which=lambda _: "pg_isready")["reachable"] is False


def test_ollama_only_checks_static_local_version_without_remote_redirects():
    LocalOllama.instances.clear()
    result = doctor.ollama_readiness(connect=LocalOllama)
    assert result == {"status": "reachable", "reachable": True}
    instance = LocalOllama.instances[0]
    assert instance.address == ("127.0.0.1", 11434)
    assert instance.timeout == 2
    assert instance.requests == [("GET", "/api/version")]
    assert instance.closed is True


@pytest.mark.parametrize("status,body,expected", [
    (302, b"", "unavailable"),
    (404, b"", "unavailable"),
    (200, b'{}', "invalid_response"),
    (200, b'{"version":null}', "invalid_response"),
    (200, b'{"version":true}', "invalid_response"),
    (200, b'{"secret":"token-value"}', "invalid_response"),
    (200, b"invalid", "unavailable"),
    (200, b"x" * 2049, "invalid_response"),
])
def test_ollama_invalid_or_redirected_reply_is_rejected(status, body, expected):
    class Fake(LocalOllama):
        def __init__(self, *args, **kw):
            super().__init__(*args, **kw)
            self.response = Response(status, body)
    result = doctor.ollama_readiness(connect=Fake)
    assert result["status"] == expected
    assert result["reachable"] is False
    assert "token-value" not in json.dumps(result)


def test_ollama_connection_errors_are_diagnostic_not_fatal():
    class ConnectionFailure(LocalOllama):
        def request(self, *a):
            raise ConnectionRefusedError("service down")
    assert doctor.ollama_readiness(connect=ConnectionFailure)["reachable"] is False


def fake_platform(*, profile):
    return {
        "missing_required": ["python3-tk", "pg_isready"],
    }


def test_doctor_reports_actionable_but_no_changes_to_system():
    profile = LinuxProfile("Linux", "ubuntu", "24.04", "wayland", True)
    report = doctor.ubuntu_doctor(
        profile=profile, inspect=fake_platform,
        postgres=lambda: {"status": "unavailable", "reachable": False},
        ollama=lambda: {"status": "unavailable", "reachable": False},
    )
    assert report["schema"] == "nexus.ubuntu-doctor.v1"
    assert report["core_services_ready_to_try"] is False
    assert report["missing_packages"] == ["pg_isready", "python3-tk"]
    assert report["blockers"] == [
        "missing_desktop_packages", "postgresql_not_ready", "ollama_not_ready"
    ]
    assert report["external_network_used"] is False
    assert report["services_started"] is False
    assert report["packages_installed"] is False
    assert report["database_changed"] is False
    assert report["microphone_tested"] is False
    assert report["camera_tested"] is False
    assert report["postgresql_authentication_tested"] is False
    assert report["ollama_model_tested"] is False
    assert any("X11" in item for item in report["recommendations"])


def test_doctor_ready_does_not_claim_model_or_hardware_tested():
    profile = LinuxProfile("Linux", "ubuntu", "24.04", "x11", True)
    report = doctor.ubuntu_doctor(
        profile=profile, inspect=lambda **kw: {"missing_required": []},
        postgres=lambda: {"status": "accepting_connections", "reachable": True},
        ollama=lambda: {"status": "reachable", "reachable": True},
    )
    assert report["core_services_ready_to_try"] is True
    assert report["blockers"] == []
    assert report["ollama_model_tested"] is False
    assert report["microphone_tested"] is False
    assert report["postgresql_authentication_tested"] is False


def test_doctor_does_not_authorize_other_distros():
    profile = LinuxProfile("Linux", "steamos", "3.7", "x11", False)
    report = doctor.ubuntu_doctor(
        profile=profile, inspect=lambda **kw: {"missing_required": []},
        postgres=lambda: {"status": "accepting_connections", "reachable": True},
        ollama=lambda: {"status": "reachable", "reachable": True},
    )
    assert "ubuntu_24_04_not_confirmed" in report["blockers"]


def test_cli_doctor_does_not_initialize_application(monkeypatch, capsys):
    import nexus.main as entry
    import nexus.platforms as platforms
    monkeypatch.setattr(entry, "build_application",
                        lambda: pytest.fail("must not start app"))
    monkeypatch.setattr(platforms, "ubuntu_doctor",
                        lambda: {"schema": "nexus.ubuntu-doctor.v1", "mode": "local_read_only"})
    entry.cli(["--ubuntu-doctor"])
    data = json.loads(capsys.readouterr().out)
    assert data["schema"] == "nexus.ubuntu-doctor.v1"


@pytest.mark.parametrize("args", [
    ["--ubuntu-doctor", "--desktop"], ["--ubuntu-doctor", "--status"],
    ["--ubuntu-doctor", "--memory-list"],
    ["--ubuntu-doctor", "--vision-question", "abc"],
    ["--ubuntu-doctor", "--knowledge-search", "abc"],
])
def test_doctor_rejects_other_actions(args):
    from nexus.main import cli
    with pytest.raises(SystemExit) as raised:
        cli(args)
    assert raised.value.code == 2
