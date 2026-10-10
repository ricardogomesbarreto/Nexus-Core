"""In-memory registry of explicitly declared devices; it never opens a transport."""
from threading import RLock

from .contracts import DeviceContractError, DeviceDeclaration, DeviceManifest, SCHEMA


class DeviceRegistry:
    """Atomic local inventory, with no discovery, connection or persistence."""

    def __init__(self):
        self._lock = RLock()
        self._devices: dict[str, DeviceDeclaration] = {}

    def replace_declared(self, manifest: DeviceManifest) -> None:
        # Do not treat manually constructed, unvalidated dataclasses as trusted.
        if not isinstance(manifest, DeviceManifest) or manifest.schema != SCHEMA:
            raise DeviceContractError("Manifesto não autorizado.")
        from .contracts import parse_manifest
        import json
        validated = parse_manifest(json.dumps({
            "schema": manifest.schema,
            "devices": [
                {
                    "device_id": item.device_id, "label": item.label,
                    "family": item.family,
                    "capabilities": list(item.capabilities),
                    "transport": item.transport,
                }
                for item in manifest.devices
            ],
        }, ensure_ascii=False))
        with self._lock:
            self._devices = {item.device_id: item for item in validated.devices}

    def snapshot(self) -> tuple[DeviceDeclaration, ...]:
        with self._lock:
            return tuple(self._devices[key] for key in sorted(self._devices))

    def forget(self, device_id: str) -> bool:
        if type(device_id) is not str:
            raise DeviceContractError("ID de dispositivo inválido.")
        with self._lock:
            return self._devices.pop(device_id, None) is not None
