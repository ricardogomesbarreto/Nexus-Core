"""Versioned, atomic and private desktop preferences for offline Linux use.

Preference persistence is independent of PostgreSQL, Ollama, network and
captured media. Only allowlisted presentation/voice settings are written.
"""
from __future__ import annotations

import json
import os
import re
import stat
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path


class PreferenceStoreError(RuntimeError):
    """Readable failure that never discloses local settings or file contents."""


@dataclass(frozen=True)
class DesktopPreferences:
    voice: str = "Feminina"
    speech_enabled: bool = True
    wake_required: bool = False
    audio_backend: str = "auto"
    listening_enabled: bool = True
    geometry: str = "980x720"
    remember_history: bool = False

    MAX_BYTES = 4096
    VERSION = 1
    VALID_VOICES = frozenset(("Feminina", "Masculina"))
    VALID_AUDIO = frozenset(("auto", "pipewire", "alsa"))
    GEOMETRY = re.compile(r"^(\d{3,4})x(\d{3,4})$")

    @classmethod
    def from_dict(cls, document: object) -> DesktopPreferences:
        if not isinstance(document, dict) or document.get("version") != cls.VERSION:
            raise PreferenceStoreError("Configurações locais incompatíveis ou inválidas.")
        raw = document.get("preferences")
        if not isinstance(raw, dict):
            raise PreferenceStoreError("Configurações locais inválidas.")
        allowed = set(cls.__dataclass_fields__)
        if set(raw) - allowed:
            raise PreferenceStoreError("Configurações locais contêm campos desconhecidos.")
        try:
            instance = cls(**raw)
        except TypeError as exc:
            raise PreferenceStoreError("Configurações locais incompletas ou inválidas.") from exc
        instance.validate()
        return instance

    def validate(self) -> None:
        if self.voice not in self.VALID_VOICES or not isinstance(self.voice, str):
            raise PreferenceStoreError("A opção de voz salva é inválida.")
        for key in ("speech_enabled", "wake_required", "listening_enabled", "remember_history"):
            if type(getattr(self, key)) is not bool:
                raise PreferenceStoreError(f"A preferência '{key}' é inválida.")
        if self.audio_backend not in self.VALID_AUDIO or not isinstance(self.audio_backend, str):
            raise PreferenceStoreError("A fonte de microfone salva é inválida.")
        if not isinstance(self.geometry, str):
            raise PreferenceStoreError("O tamanho da janela é inválido.")
        match = self.GEOMETRY.fullmatch(self.geometry)
        if match is None or not (770 <= int(match[1]) <= 3840 and 570 <= int(match[2]) <= 2160):
            raise PreferenceStoreError("O tamanho da janela está fora do intervalo permitido.")


def default_preferences_path() -> Path:
    env = os.environ.get("XDG_CONFIG_HOME", "")
    root = Path(env).expanduser() if env else Path.home() / ".config"
    if not root.is_absolute():
        root = Path.home() / ".config"
    return root / "nexus-core" / "preferences.json"


class DesktopPreferenceStore:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path is not None else default_preferences_path()

    def _ensure_directory(self) -> None:
        folder = self.path.parent
        if folder.is_symlink():
            raise PreferenceStoreError("A pasta de configurações não pode ser um link simbólico.")
        try:
            folder.mkdir(mode=0o700, parents=True, exist_ok=True)
            if not folder.is_dir() or folder.is_symlink():
                raise PreferenceStoreError("A pasta de configurações é insegura.")
            folder.chmod(0o700)
        except OSError as exc:
            raise PreferenceStoreError("Não foi possível acessar a pasta local de configurações.") from exc

    def _check_file(self) -> bool:
        try:
            info = self.path.lstat()
        except FileNotFoundError:
            return False
        except OSError as exc:
            raise PreferenceStoreError("Não foi possível consultar configurações locais.") from exc
        if not stat.S_ISREG(info.st_mode) or info.st_size > DesktopPreferences.MAX_BYTES:
            raise PreferenceStoreError("Arquivo de configurações inseguro ou muito grande.")
        return True

    def load(self) -> DesktopPreferences:
        if self.path.parent.is_symlink():
            raise PreferenceStoreError("A pasta de configurações não pode ser um link simbólico.")
        if not self._check_file():
            return DesktopPreferences()
        try:
            with self.path.open("r", encoding="utf-8") as stream:
                data = stream.read(DesktopPreferences.MAX_BYTES + 1)
            if len(data.encode("utf-8")) > DesktopPreferences.MAX_BYTES:
                raise PreferenceStoreError("Arquivo de configurações muito grande.")
            parsed = json.loads(data)
        except (OSError, ValueError, UnicodeError) as exc:
            raise PreferenceStoreError("Configurações inválidas: restaure pelo arquivo local.") from exc
        return DesktopPreferences.from_dict(parsed)

    def save(self, value: DesktopPreferences) -> None:
        value.validate()
        self._ensure_directory()
        self._check_file()  # Reject existing symlinks and non-regular files.
        body = json.dumps(
            {"version": DesktopPreferences.VERSION, "preferences": asdict(value)},
            ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")
        if len(body) > DesktopPreferences.MAX_BYTES:
            raise PreferenceStoreError("Configurações locais excederam o tamanho permitido.")
        filename = None
        try:
            fd, filename = tempfile.mkstemp(prefix=".preferences-", dir=str(self.path.parent))
            with os.fdopen(fd, "wb") as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(body)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(filename, self.path)
        except OSError as exc:
            raise PreferenceStoreError("Não foi possível salvar configurações neste computador.") from exc
        finally:
            if filename is not None:
                try:
                    Path(filename).unlink(missing_ok=True)
                except OSError:
                    pass
