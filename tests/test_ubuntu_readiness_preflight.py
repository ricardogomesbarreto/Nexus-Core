"""v0.8.4 Ubuntu preflight: no writes, downloads or sensitive output."""
import json
from types import SimpleNamespace

import pytest

from nexus.platforms import preflight


def config(**overrides):
    fields = dict(database_provider="postgresql", database_host="127.0.0.1",
                  database_port=5432, database_name="nexus",
                  database_user="nexus", database_password="secret-value")
    fields.update(overrides)
    return SimpleNamespace(**fields)


class Cursor:
    def __init__(self, value=(1,)):
        self.value = value
    def fetchone(self):
        return self.value


class Db:
    def __init__(self, *, result=(1,)):
        self.closed = False
        self.sql = []
        self.result = result
    def execute(self, sql):
        self.sql.append(sql)
        return Cursor(self.result)
    def close(self):
        self.closed = True


def test_postgres_auth_is_fixed_loopback_read_only_and_closes():
    db = Db()
    kwargs = {}
    def connect(**params):
        kwargs.update(params)
        return db
    result = preflight.postgres_auth_probe(configuration=config(), connect=connect)
    assert result == {"status": "authenticated_read_only", "authenticated": True}
    assert kwargs["host"] == "127.0.0.1"
    assert kwargs["port"] == 5432
    assert kwargs["connect_timeout"] == 3
    assert kwargs["options"] == "-c default_transaction_read_only=on"
    assert db.sql == ["SELECT 1"]
    assert db.closed


@pytest.mark.parametrize("host", ["example.com", "10.0.0.1", "192.168.0.1", "evil.local"])
def test_postgres_refuses_remote_address_without_connection(host):
    result = preflight.postgres_auth_probe(
        configuration=config(database_host=host),
        connect=lambda **kw: pytest.fail("Do not connect outside loopback"),
    )
    assert result["authenticated"] is False
    assert result["status"] == "unsupported_local_configuration"


def test_postgres_no_credentials_no_login():
    result = preflight.postgres_auth_probe(
        configuration=config(database_password=None),
        connect=lambda **kw: pytest.fail("No authentication without credentials"),
    )
    assert result["status"] == "credentials_missing"


def test_postgres_errors_never_leak_password_or_user():
    def fail(**kwargs):
        raise RuntimeError("Password=secret-value; username=nexus")
    result = preflight.postgres_auth_probe(configuration=config(), connect=fail)
    assert result == {"status": "connection_or_auth_failure", "authenticated": False}
    assert "secret-value" not in json.dumps(result)


def test_postgres_bad_query_does_not_pass():
    db = Db(result=None)
    result = preflight.postgres_auth_probe(configuration=config(),
                                           connect=lambda **kw: db)
    assert result["status"] == "query_failed"
    assert db.closed is True


class Response:
    def __init__(self, body, status=200):
        self.body, self.status = body, status
    def read(self, n):
        return self.body[:n]


class LocalConnection:
    all = []
    body = b'{"models":[{"name":"qwen3:1.7b"},{"name":"gemma3:4b"}]}'
    code = 200
    def __init__(self, host, port, timeout):
        self.host, self.port, self.timeout = host, port, timeout
        self.calls = []
        self.closed = False
        self.all.append(self)
    def request(self, method, url):
        self.calls.append((method, url))
    def getresponse(self):
        return Response(self.body, self.code)
    def close(self):
        self.closed = True


def test_ollama_check_uses_loopback_and_only_get_tags():
    LocalConnection.all.clear()
    result = preflight.ollama_model_probe(model_name="qwen3:1.7b",
                                          connect=LocalConnection)
    assert result == {"status": "model_listed", "installed": True}
    connection = LocalConnection.all[-1]
    assert (connection.host, connection.port, connection.timeout) == (
        "127.0.0.1", 11434, 3,
    )
    assert connection.calls == [("GET", "/api/tags")]
    assert connection.closed


def test_other_valid_model_is_not_falsely_listed():
    result = preflight.ollama_model_probe(model_name="absent:latest",
                                          connect=LocalConnection)
    assert result == {"status": "model_not_listed", "installed": False}


@pytest.mark.parametrize("body,status,expected", [
    (b'{"models":[]}', 200, "model_not_listed"),
    (b'{"models":{}}', 200, "invalid_response"),
    (b'{"models":[1]}', 200, "invalid_response"),
    (b'{"models":[{"name":null}]}', 200, "invalid_response"),
    (b'{"models":[{"name":"secret-token"}]}', 200, "model_not_listed"),
    (b"invalid", 200, "service_unavailable"),
    (b"x" * (preflight.MAX_TAGS_BYTES + 1), 200, "invalid_response"),
    (b"redirect", 302, "service_unavailable"),
])
def test_ollama_rejects_malformed_or_bounded_replies(body, status, expected):
    class Fake(LocalConnection):
        def getresponse(self):
            return Response(body, status)
    result = preflight.ollama_model_probe(model_name="qwen3:1.7b", connect=Fake)
    assert result["status"] == expected
    assert "secret-token" not in json.dumps(result)


def test_ollama_refuses_untrusted_model_config():
    assert preflight.ollama_model_probe(model_name="x" * 130)["status"] == (
        "invalid_model_configuration"
    )


def base_ready():
    return {"core_services_ready_to_try": True}


def voice_ready():
    return {"recognition_ready_to_try": True, "speech_ready_to_try": True}


def test_preflight_success_is_only_a_trial_not_hardware_acceptance():
    result = preflight.ubuntu_preflight(
        doctor=base_ready,
        database=lambda: {"status": "authenticated_read_only", "authenticated": True},
        model=lambda: {"status": "model_listed", "installed": True},
        voice=voice_ready,
    )
    assert result["schema"] == "nexus.ubuntu-preflight.v1"
    assert result["text_chat_dependencies_ready_to_try"] is True
    assert result["voice_chat_dependencies_ready_to_try"] is True
    assert result["full_hardware_or_model_inference_tested"] is False
    assert result["microphone_opened"] is False
    assert result["camera_opened"] is False
    assert result["model_downloaded"] is False
    assert result["postgresql_data_modified"] is False
    assert result["external_network_used"] is False
    assert result["unmet"] == []


def test_preflight_can_show_voice_degradation_separately():
    result = preflight.ubuntu_preflight(
        doctor=base_ready,
        database=lambda: {"status": "authenticated_read_only", "authenticated": True},
        model=lambda: {"status": "model_listed", "installed": True},
        voice=lambda: {"recognition_ready_to_try": False,
                       "speech_ready_to_try": True},
    )
    assert result["text_chat_dependencies_ready_to_try"] is True
    assert result["voice_chat_dependencies_ready_to_try"] is False
    assert result["unmet"] == ["voice_input_dependencies"]


def test_preflight_returns_no_secrets_or_model_list():
    result = preflight.ubuntu_preflight(
        doctor=lambda: {"core_services_ready_to_try": False, "secret": "private"},
        database=lambda: {"status": "invalid", "authenticated": False,
                          "password": "secret-value"},
        model=lambda: {"status": "unknown", "installed": False,
                       "models": ["private-model"]},
        voice=lambda: {"recognition_ready_to_try": False,
                       "speech_ready_to_try": False},
    )
    encoded = json.dumps(result)
    assert "private" not in encoded
    assert "secret-value" not in encoded
    assert "check_failed" in encoded


def test_preflight_cli_is_isolated_without_booting_application(monkeypatch, capsys):
    import nexus.main as entry
    import nexus.platforms as platforms
    monkeypatch.setattr(entry, "build_application",
                        lambda: pytest.fail("Must not initialize app"))
    monkeypatch.setattr(platforms, "ubuntu_preflight",
                        lambda: {"schema": "nexus.ubuntu-preflight.v1"})
    entry.cli(["--ubuntu-preflight"])
    assert json.loads(capsys.readouterr().out) == {
        "schema": "nexus.ubuntu-preflight.v1",
    }


@pytest.mark.parametrize("arguments", [
    ["--ubuntu-preflight", "--desktop"],
    ["--ubuntu-preflight", "--memory-list"],
    ["--ubuntu-preflight", "--vision-camera", "0"],
    ["--ubuntu-preflight", "--knowledge-list"],
    ["--ubuntu-preflight", "--workspace", "/tmp"],
])
def test_preflight_cli_refuses_combined_actions(arguments):
    from nexus.main import cli
    with pytest.raises(SystemExit) as caught:
        cli(arguments)
    assert caught.value.code == 2
