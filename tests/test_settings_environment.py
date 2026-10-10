import json
import os
import subprocess
import sys

import pytest

from nexus.config.settings import (
    PROJECT_ROOT,
    ConfigurationError,
    load_settings,
)


def test_load_settings_preserves_defaults_with_empty_environment():
    settings = load_settings({})

    assert settings.node_name == "NEXUS-NODE-01"
    assert settings.offline_mode is True
    assert settings.connectivity_monitor_interval == 30.0
    assert settings.connectivity_confirmation_threshold == 2


def test_load_settings_applies_supported_environment_overrides():
    settings = load_settings(
        {
            "NEXUS_NODE_NAME": "NEXUS-TEST-01",
            "NEXUS_OFFLINE_MODE": "false",
            "NEXUS_CONNECTIVITY_MONITOR_INTERVAL": "15.5",
            "NEXUS_CONNECTIVITY_CONFIRMATION_THRESHOLD": "3",
        }
    )

    assert settings.node_name == "NEXUS-TEST-01"
    assert settings.offline_mode is False
    assert settings.connectivity_monitor_interval == 15.5
    assert settings.connectivity_confirmation_threshold == 3


@pytest.mark.parametrize(
    "value",
    [
        "",
        "yes",
        "1",
        "enabled",
    ],
)
def test_load_settings_rejects_invalid_boolean(value):
    with pytest.raises(
        ConfigurationError,
        match="NEXUS_OFFLINE_MODE",
    ):
        load_settings(
            {
                "NEXUS_OFFLINE_MODE": value,
            }
        )


@pytest.mark.parametrize(
    "value",
    [
        "",
        "   ",
    ],
)
def test_load_settings_rejects_empty_node_name(value):
    with pytest.raises(
        ConfigurationError,
        match="NEXUS_NODE_NAME",
    ):
        load_settings(
            {
                "NEXUS_NODE_NAME": value,
            }
        )


@pytest.mark.parametrize(
    "value",
    [
        "0",
        "-1",
        "nan",
        "inf",
        "-inf",
    ],
)
def test_load_settings_rejects_non_positive_or_non_finite_monitor_interval(
    value,
):
    with pytest.raises(
        ConfigurationError,
        match="NEXUS_CONNECTIVITY_MONITOR_INTERVAL",
    ):
        load_settings(
            {
                "NEXUS_CONNECTIVITY_MONITOR_INTERVAL": value,
            }
        )


@pytest.mark.parametrize(
    "value",
    [
        "0",
        "1",
        "-1",
    ],
)
def test_load_settings_rejects_confirmation_threshold_below_two(
    value,
):
    with pytest.raises(
        ConfigurationError,
        match="NEXUS_CONNECTIVITY_CONFIRMATION_THRESHOLD",
    ):
        load_settings(
            {
                "NEXUS_CONNECTIVITY_CONFIRMATION_THRESHOLD": value,
            }
        )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("true", True),
        ("TRUE", True),
        (" True ", True),
        ("false", False),
        ("FALSE", False),
        (" False ", False),
    ],
)
def test_load_settings_normalizes_boolean_values(
    value,
    expected,
):
    settings = load_settings(
        {
            "NEXUS_OFFLINE_MODE": value,
        }
    )

    assert settings.offline_mode is expected


def test_load_settings_trims_node_name():
    settings = load_settings(
        {
            "NEXUS_NODE_NAME": "  NEXUS-EDGE-01  ",
        }
    )

    assert settings.node_name == "NEXUS-EDGE-01"


@pytest.mark.parametrize(
    "value",
    [
        "abc",
        "",
        "1.2.3",
    ],
)
def test_load_settings_rejects_invalid_monitor_interval_syntax(
    value,
):
    with pytest.raises(
        ConfigurationError,
        match="NEXUS_CONNECTIVITY_MONITOR_INTERVAL",
    ):
        load_settings(
            {
                "NEXUS_CONNECTIVITY_MONITOR_INTERVAL": value,
            }
        )


@pytest.mark.parametrize(
    "value",
    [
        "abc",
        "",
        "2.5",
    ],
)
def test_load_settings_rejects_invalid_confirmation_threshold_syntax(
    value,
):
    with pytest.raises(
        ConfigurationError,
        match="NEXUS_CONNECTIVITY_CONFIRMATION_THRESHOLD",
    ):
        load_settings(
            {
                "NEXUS_CONNECTIVITY_CONFIRMATION_THRESHOLD": value,
            }
        )


def test_load_settings_ignores_undeclared_environment_overrides():
    settings = load_settings(
        {
            "NEXUS_APP_NAME": "Compromised Nexus",
            "NEXUS_VERSION": "999.0.0",
            "NEXUS_PROJECT_ROOT": "/tmp/nexus",
            "NEXUS_DATA_DIR": "/tmp/nexus/data",
            "NEXUS_LOGS_DIR": "/tmp/nexus/logs",
        }
    )

    assert settings.app_name == "Nexus Core"
    assert settings.version == "0.8.4"
    assert settings.project_root == PROJECT_ROOT
    assert settings.data_dir.name == "nexus-core"
    assert settings.logs_dir.name == "logs"
    assert settings.logs_dir.parent.name == "nexus-core"

    assert settings.database_provider == "postgresql"
    assert settings.database_host == "127.0.0.1"
    assert settings.database_name == "nexus"


def test_voice_model_path_requires_absolute_path(tmp_path):
    configured = load_settings({"NEXUS_VOSK_MODEL_PATH": str(tmp_path / "model")})
    assert configured.voice_model_path == tmp_path / "model"
    with pytest.raises(ConfigurationError, match="NEXUS_VOSK_MODEL_PATH"):
        load_settings({"NEXUS_VOSK_MODEL_PATH": "relative/model"})


def test_user_data_and_logs_follow_xdg_directories(monkeypatch, tmp_path):
    from nexus.config.settings import Settings

    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    configured = Settings()
    assert configured.data_dir == tmp_path / "data" / "nexus-core"
    assert configured.logs_dir == tmp_path / "state" / "nexus-core" / "logs"


def test_load_settings_reads_process_environment_when_source_is_omitted(
    monkeypatch,
):
    monkeypatch.setenv(
        "NEXUS_NODE_NAME",
        "NEXUS-ENV-01",
    )
    monkeypatch.setenv(
        "NEXUS_OFFLINE_MODE",
        "false",
    )
    monkeypatch.setenv(
        "NEXUS_CONNECTIVITY_MONITOR_INTERVAL",
        "12.5",
    )
    monkeypatch.setenv(
        "NEXUS_CONNECTIVITY_CONFIRMATION_THRESHOLD",
        "4",
    )

    settings = load_settings()

    assert settings.node_name == "NEXUS-ENV-01"
    assert settings.offline_mode is False
    assert settings.connectivity_monitor_interval == 12.5
    assert settings.connectivity_confirmation_threshold == 4


def test_settings_singleton_loads_environment_on_fresh_process_startup():
    environment = os.environ.copy()

    environment.update(
        {
            "NEXUS_NODE_NAME": "NEXUS-PROCESS-01",
            "NEXUS_OFFLINE_MODE": "false",
            "NEXUS_CONNECTIVITY_MONITOR_INTERVAL": "7.5",
            "NEXUS_CONNECTIVITY_CONFIRMATION_THRESHOLD": "5",
            "PYTHONPATH": str(PROJECT_ROOT),
        }
    )

    code = """
import json

from nexus.config.settings import settings

print(
    json.dumps(
        {
            "node_name": settings.node_name,
            "offline_mode": settings.offline_mode,
            "connectivity_monitor_interval": (
                settings.connectivity_monitor_interval
            ),
            "connectivity_confirmation_threshold": (
                settings.connectivity_confirmation_threshold
            ),
        }
    )
)
"""

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            code,
        ],
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    )

    loaded = json.loads(result.stdout)

    assert loaded == {
        "node_name": "NEXUS-PROCESS-01",
        "offline_mode": False,
        "connectivity_monitor_interval": 7.5,
        "connectivity_confirmation_threshold": 5,
    }


def test_settings_singleton_fails_fast_on_invalid_process_environment():
    environment = os.environ.copy()

    environment.update(
        {
            "NEXUS_CONNECTIVITY_CONFIRMATION_THRESHOLD": "1",
            "PYTHONPATH": str(PROJECT_ROOT),
        }
    )

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from nexus.config.settings import settings",
        ],
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert (
        "NEXUS_CONNECTIVITY_CONFIRMATION_THRESHOLD"
        in result.stderr
    )
    assert "ConfigurationError" in result.stderr


def test_database_defaults_are_postgresql_local():
    settings = load_settings({})

    assert settings.database_provider == "postgresql"
    assert settings.database_host == "127.0.0.1"
    assert settings.database_port == 5432
    assert settings.database_name == "nexus"
    assert settings.database_user == "nexus"
    assert settings.database_password is None
    assert settings.database_connect_timeout == 5.0


def test_load_settings_reads_postgresql_environment():
    password = "database-test-secret"

    settings = load_settings(
        {
            "NEXUS_DATABASE_PROVIDER": "postgresql",
            "NEXUS_DATABASE_HOST": "127.0.0.1",
            "NEXUS_DATABASE_PORT": "5433",
            "NEXUS_DATABASE_NAME": "nexus_test",
            "NEXUS_DATABASE_USER": "nexus_app",
            "NEXUS_DATABASE_PASSWORD": password,
            "NEXUS_DATABASE_CONNECT_TIMEOUT": "7.5",
        }
    )

    assert settings.database_provider == "postgresql"
    assert settings.database_host == "127.0.0.1"
    assert settings.database_port == 5433
    assert settings.database_name == "nexus_test"
    assert settings.database_user == "nexus_app"
    assert settings.database_password == password
    assert settings.database_connect_timeout == 7.5

    assert password not in repr(settings)


def test_load_settings_rejects_unsupported_database_provider():
    with pytest.raises(
        ConfigurationError,
        match="NEXUS_DATABASE_PROVIDER",
    ):
        load_settings(
            {
                "NEXUS_DATABASE_PROVIDER": "mysql",
            }
        )


def test_load_settings_rejects_remote_database_host():
    with pytest.raises(
        ConfigurationError,
        match="NEXUS_DATABASE_HOST",
    ):
        load_settings(
            {
                "NEXUS_DATABASE_HOST": "database.example.com",
            }
        )


@pytest.mark.parametrize(
    "value",
    [
        "abc",
        "0",
        "65536",
        "2.5",
    ],
)
def test_load_settings_rejects_invalid_database_port(value):
    with pytest.raises(
        ConfigurationError,
        match="NEXUS_DATABASE_PORT",
    ):
        load_settings(
            {
                "NEXUS_DATABASE_PORT": value,
            }
        )


@pytest.mark.parametrize(
    "environment_name",
    [
        "NEXUS_DATABASE_NAME",
        "NEXUS_DATABASE_USER",
        "NEXUS_DATABASE_PASSWORD",
    ],
)
def test_load_settings_rejects_empty_database_values(
    environment_name,
):
    with pytest.raises(
        ConfigurationError,
        match=environment_name,
    ):
        load_settings(
            {
                environment_name: "",
            }
        )


@pytest.mark.parametrize(
    "value",
    [
        "abc",
        "0",
        "-1",
        "nan",
        "inf",
    ],
)
def test_load_settings_rejects_invalid_database_connect_timeout(
    value,
):
    with pytest.raises(
        ConfigurationError,
        match="NEXUS_DATABASE_CONNECT_TIMEOUT",
    ):
        load_settings(
            {
                "NEXUS_DATABASE_CONNECT_TIMEOUT": value,
            }
        )
