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


def test_load_settings_ignores_unsupported_environment_overrides():
    settings = load_settings(
        {
            "NEXUS_APP_NAME": "Compromised Nexus",
            "NEXUS_VERSION": "999.0.0",
            "NEXUS_PROJECT_ROOT": "/tmp/nexus",
            "NEXUS_DATA_DIR": "/tmp/nexus/data",
            "NEXUS_LOGS_DIR": "/tmp/nexus/logs",
            "NEXUS_DATABASE_DIR": "/tmp/nexus/database",
            "NEXUS_DATABASE_FILE": "/tmp/nexus/database/evil.db",
        }
    )

    assert settings.app_name == "Nexus Core"
    assert settings.version == "0.2.4"
    assert settings.project_root == PROJECT_ROOT
    assert settings.data_dir == PROJECT_ROOT / "data"
    assert settings.logs_dir == PROJECT_ROOT / "logs"
    assert settings.database_dir == PROJECT_ROOT / "data" / "database"
    assert (
        settings.database_file
        == PROJECT_ROOT / "data" / "database" / "nexus.db"
    )


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
