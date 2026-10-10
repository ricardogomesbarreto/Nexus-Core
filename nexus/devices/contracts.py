"""Strict, inert declarations of future local devices (v0.8.0).

A declaration is not a pairing, connection, discovery, or permission to execute.
No network or hardware interfaces are imported by this module.
"""
from dataclasses import dataclass
import json
import re
import unicodedata


SCHEMA = "nexus.devices.v1"
DEVICE_FAMILIES = ("arduino", "esp32")
READ_CAPABILITIES = (
    "temperature.read", "humidity.read", "motion.read",
    "position.read", "battery.read",
)
MAX_MANIFEST_BYTES = 16_384
MAX_DEVICES = 32


class DeviceContractError(ValueError):
    """Invalid untrusted device declaration, with sanitized error."""


@dataclass(frozen=True)
class DeviceDeclaration:
    device_id: str
    label: str
    family: str
    capabilities: tuple[str, ...]
    transport: str = "disabled"


@dataclass(frozen=True)
class DeviceManifest:
    schema: str
    devices: tuple[DeviceDeclaration, ...]


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise DeviceContractError("Manifesto contém chave duplicada.")
        value[key] = item
    return value


def _reject_constant(value):
    raise DeviceContractError("Manifesto contém número inválido.")


def parse_manifest(payload: str) -> DeviceManifest:
    """Parse an explicit JSON declaration; never enumerate connected devices."""
    if type(payload) is not str or not payload.strip():
        raise DeviceContractError("Informe um manifesto JSON não vazio.")
    try:
        size = len(payload.encode("utf-8", errors="strict"))
    except UnicodeError as exc:
        raise DeviceContractError("Manifesto deve usar UTF-8 válido.") from exc
    if size > MAX_MANIFEST_BYTES:
        raise DeviceContractError("Manifesto excede o tamanho permitido.")
    try:
        document = json.loads(
            payload, object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise DeviceContractError("Manifesto JSON inválido.") from exc
    if type(document) is not dict or set(document) != {"schema", "devices"}:
        raise DeviceContractError("Estrutura do manifesto inválida.")
    if document["schema"] != SCHEMA:
        raise DeviceContractError("Versão de contrato de dispositivos inválida.")
    records = document["devices"]
    if type(records) is not list or len(records) > MAX_DEVICES:
        raise DeviceContractError("Lista de dispositivos inválida.")
    seen = set()
    devices = []
    for record in records:
        if type(record) is not dict or set(record) != {
            "device_id", "label", "family", "capabilities", "transport",
        }:
            raise DeviceContractError("Declaração contém campos ausentes ou proibidos.")
        device_id = record["device_id"]
        if type(device_id) is not str or not re.fullmatch(
            r"[a-z][a-z0-9-]{2,39}", device_id, flags=re.ASCII,
        ):
            raise DeviceContractError("ID de dispositivo inválido.")
        if device_id in seen:
            raise DeviceContractError("ID de dispositivo duplicado.")
        seen.add(device_id)
        label = record["label"]
        if (
            type(label) is not str or not 1 <= len(label) <= 80
            or not label.strip()
            or any(
                not char.isprintable() or unicodedata.category(char) == "Cf"
                for char in label
            )
        ):
            raise DeviceContractError("Rótulo de dispositivo inválido.")
        family = record["family"]
        if type(family) is not str or family not in DEVICE_FAMILIES:
            raise DeviceContractError("Família de dispositivo não suportada.")
        if record["transport"] != "disabled":
            raise DeviceContractError("Transporte deve permanecer desabilitado.")
        capabilities = record["capabilities"]
        if (
            type(capabilities) is not list or not 1 <= len(capabilities) <= 5
            or any(type(cap) is not str or cap not in READ_CAPABILITIES
                   for cap in capabilities)
            or len(capabilities) != len(set(capabilities))
        ):
            raise DeviceContractError("Capacidades inválidas ou não autorizadas.")
        devices.append(DeviceDeclaration(
            device_id=device_id, label=label, family=family,
            capabilities=tuple(capabilities),
        ))
    return DeviceManifest(schema=SCHEMA, devices=tuple(devices))


def device_capabilities() -> dict:
    """Entirely passive report: no PostgreSQL, network, USB, serial or scanner."""
    return {
        "schema": SCHEMA,
        "mode": "declarative_preview_only",
        "families": list(DEVICE_FAMILIES),
        "read_capabilities": list(READ_CAPABILITIES),
        "transport_enabled": False,
        "hardware_discovery": False,
        "network_access": False,
        "device_commands_enabled": False,
        "secrets_in_manifest": False,
        "persistent_registry": False,
        "consent_required_for_future_communication": True,
        "maximum_devices": MAX_DEVICES,
    }


def preview_manifest(manifest: DeviceManifest) -> dict:
    if not isinstance(manifest, DeviceManifest):
        raise DeviceContractError("Manifesto de dispositivos inválido.")
    return {
        "schema": manifest.schema,
        "declared_only": True,
        "connected_devices": 0,
        "count": len(manifest.devices),
        "devices": [
            {
                "device_id": item.device_id,
                "family": item.family,
                "capabilities": list(item.capabilities),
                "transport": "disabled",
            }
            for item in manifest.devices
        ],
    }
