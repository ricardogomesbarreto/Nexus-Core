"""v0.8.0: declarations never become device access or autonomy."""
import io
import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

from nexus.core.application import NexusApplication
from nexus.devices import (
    DeviceContractError, DeviceRegistry,
    device_capabilities, parse_manifest, preview_manifest,
)


def valid(device_id="sensor-001", family="esp32", caps=None):
    return {
        "device_id": device_id, "label": "Temperatura estábulo",
        "family": family,
        "capabilities": caps or ["temperature.read", "battery.read"],
        "transport": "disabled",
    }


def payload(devices=None):
    return json.dumps({
        "schema": "nexus.devices.v1",
        "devices": [valid()] if devices is None else devices,
    }, ensure_ascii=False)


def test_valid_arduino_and_esp32_inert_inventory():
    manifest = parse_manifest(payload([
        valid("arduino-001", "arduino", ["motion.read"]),
        valid("sensor-001"),
    ]))
    assert manifest.schema == "nexus.devices.v1"
    assert [d.device_id for d in manifest.devices] == ["arduino-001", "sensor-001"]
    assert all(d.transport == "disabled" for d in manifest.devices)
    assert preview_manifest(manifest) == {
        "schema": "nexus.devices.v1",
        "declared_only": True,
        "connected_devices": 0,
        "count": 2,
        "devices": [
            {"device_id": "arduino-001", "family": "arduino",
             "capabilities": ["motion.read"], "transport": "disabled"},
            {"device_id": "sensor-001", "family": "esp32",
             "capabilities": ["temperature.read", "battery.read"],
             "transport": "disabled"},
        ],
    }


@pytest.mark.parametrize("mutate", [
    lambda d: d.update({"endpoint": "http://127.0.0.1:1234"}),
    lambda d: d.update({"secret": "password"}),
    lambda d: d.update({"transport": "serial"}),
    lambda d: d.update({"transport": "mqtt"}),
    lambda d: d.update({"family": "raspberry-pi"}),
    lambda d: d.update({"device_id": "a"}),
    lambda d: d.update({"device_id": "../config"}),
    lambda d: d.update({"device_id": "A_VALID"}),
    lambda d: d.update({"device_id": True}),
    lambda d: d.update({"label": ""}),
    lambda d: d.update({"label": "evil\u202e"}),
    lambda d: d.update({"capabilities": ["relay.write"]}),
    lambda d: d.update({"capabilities": ["temperature.read", "temperature.read"]}),
    lambda d: d.update({"capabilities": []}),
    lambda d: d.update({"capabilities": [3]}),
    lambda d: d.update({"capabilities": [["temperature.read"]]}),
])
def test_rejects_injected_or_malformed_device(mutate):
    record = valid()
    mutate(record)
    with pytest.raises(DeviceContractError):
        parse_manifest(payload([record]))


@pytest.mark.parametrize("raw", [
    "", " ", "[]", "null", "123", "{}",
    '{"schema":"nexus.devices.v1","schema":"nexus.devices.v1","devices":[]}',
    '{"schema":"nexus.devices.v1","devices":[],"network":true}',
    '{"schema":"nexus.devices.v1","devices":{}}',
    '{"schema":"nexus.devices.v2","devices":[]}',
    '{"schema":"nexus.devices.v1","devices":[{"device_id":"a","device_id":"b"}]}',
    '{"schema":"nexus.devices.v1","devices":NaN}',
    '{"schema":"nexus.devices.v1","devices":Infinity}',
    "x" * 16385,
])
def test_malformed_json_fails_closed(raw):
    with pytest.raises(DeviceContractError):
        parse_manifest(raw)


def test_duplicate_ids_and_excessive_devices_denied():
    with pytest.raises(DeviceContractError, match="duplicado"):
        parse_manifest(payload([valid(), valid()]))
    with pytest.raises(DeviceContractError):
        parse_manifest(payload([valid("node-%03d" % i) for i in range(33)]))


def test_registry_is_explicit_atomic_and_ephemeral():
    registry = DeviceRegistry()
    assert registry.snapshot() == ()
    original = parse_manifest(payload([valid("sensor-001"), valid("arduino-001", "arduino")]))
    registry.replace_declared(original)
    assert [d.device_id for d in registry.snapshot()] == ["arduino-001", "sensor-001"]
    with pytest.raises(DeviceContractError):
        registry.replace_declared(replace(original, devices=(
            replace(original.devices[0], transport="wifi"),
        )))
    assert len(registry.snapshot()) == 2  # rejected replacement is atomic
    assert registry.forget("arduino-001") is True
    assert registry.forget("arduino-001") is False
    assert [d.device_id for d in registry.snapshot()] == ["sensor-001"]
    assert DeviceRegistry().snapshot() == ()  # no persistence


def test_capability_report_is_passive_and_cannot_claim_hardware():
    values = device_capabilities()
    assert values["mode"] == "declarative_preview_only"
    assert values["transport_enabled"] is False
    assert values["hardware_discovery"] is False
    assert values["network_access"] is False
    assert values["device_commands_enabled"] is False
    assert values["persistent_registry"] is False


def test_application_installs_inert_registry_without_device_tools():
    application = NexusApplication(SimpleNamespace())
    assert isinstance(application.device_registry, DeviceRegistry)
    assert application.device_registry.snapshot() == ()
    assert not any(
        "device" in name for name in application.tool_registry.list_tools()
    )


def test_cli_device_check_does_not_initialize_app_or_access_hardware(monkeypatch, capsys):
    import nexus.main as entry
    monkeypatch.setattr(entry, "build_application",
                        lambda: pytest.fail("Application must not initialize"))
    entry.cli(["--devices-check"])
    result = json.loads(capsys.readouterr().out)
    assert result["schema"] == "nexus.devices.v1"
    assert result["hardware_discovery"] is False


def test_cli_preview_reads_explicit_stdin_and_never_connects(monkeypatch, capsys):
    import nexus.main as entry
    monkeypatch.setattr(entry, "build_application",
                        lambda: pytest.fail("Application must not initialize"))
    monkeypatch.setattr(entry.sys, "stdin", io.StringIO(payload()))
    entry.cli(["--devices-preview-stdin"])
    result = json.loads(capsys.readouterr().out)
    assert result["count"] == 1
    assert result["connected_devices"] == 0


@pytest.mark.parametrize("args", [
    ["--devices-check", "--status"],
    ["--devices-check", "--vision-question", "abc"],
    ["--devices-check", "--memory-list"],
    ["--devices-check", "--knowledge-list"],
    ["--devices-preview-stdin", "--devices-check"],
])
def test_device_actions_reject_conflicting_options(args):
    from nexus.main import cli
    with pytest.raises(SystemExit) as err:
        cli(args)
    assert err.value.code == 2


def test_cli_preview_rejects_bad_manifest_without_leaking_payload(monkeypatch, capsys):
    from nexus.main import cli
    secret = '{"schema":"nexus.devices.v1","devices":[],"token":"secret-value"}'
    monkeypatch.setattr("sys.stdin", io.StringIO(secret))
    with pytest.raises(SystemExit) as err:
        cli(["--devices-preview-stdin"])
    assert err.value.code == 2
    captured = capsys.readouterr()
    assert "secret-value" not in captured.err
    assert captured.out == ""
