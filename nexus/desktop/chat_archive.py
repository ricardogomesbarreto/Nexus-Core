"""Local opt-in text conversation archive for Nexus Core desktop.

Only bounded pairs of text are stored; no image, audio, screen pixel, consent,
terminal output or system-file content may be archived by this component.
Data are available offline and readable only by the Linux account (0600).
"""

import json
import os
import stat
import tempfile
from pathlib import Path
from threading import RLock

from nexus.config.settings import _data_directory


class ChatArchiveError(RuntimeError):
    """Sanitized local archive failure."""


def default_archive_path() -> Path:
    return _data_directory() / "chat-history.json"


class ChatArchive:
    MAX_RECORDS = 200
    MAX_ENTRY_CHARS = 1200
    MAX_FILE_BYTES = 650_000

    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path is not None else default_archive_path()
        self._lock = RLock()

    def _check_path(self) -> bool:
        if self.path.parent.is_symlink():
            raise ChatArchiveError("Pasta do histórico não pode ser um link simbólico.")
        try:
            info = self.path.lstat()
        except FileNotFoundError:
            return False
        except OSError as exc:
            raise ChatArchiveError("Não foi possível consultar o histórico local.") from exc
        if not stat.S_ISREG(info.st_mode) or info.st_size > self.MAX_FILE_BYTES:
            raise ChatArchiveError("Arquivo de histórico inseguro ou muito grande.")
        return True

    def _read(self) -> list[list[str]]:
        if not self._check_path():
            return []
        try:
            with self.path.open("rb") as stream:
                raw = stream.read(self.MAX_FILE_BYTES + 1)
            if len(raw) > self.MAX_FILE_BYTES:
                raise ChatArchiveError("Histórico excedeu o tamanho permitido.")
            data = json.loads(raw)
        except (ValueError, UnicodeError, OSError) as exc:
            raise ChatArchiveError("Histórico local está corrompido; não foi apagado.") from exc
        if not isinstance(data, dict) or data.get("version") != 1:
            raise ChatArchiveError("Formato do histórico local é incompatível.")
        records = data.get("records")
        if not isinstance(records, list) or len(records) > self.MAX_RECORDS:
            raise ChatArchiveError("Registros de histórico locais inválidos.")
        for record in records:
            if (not isinstance(record, list) or len(record) != 2
                    or any(not isinstance(v, str) or len(v) > self.MAX_ENTRY_CHARS
                           for v in record)):
                raise ChatArchiveError("Histórico local contém registro inválido.")
        return records

    def load(self) -> list[tuple[str, str]]:
        with self._lock:
            return [tuple(record) for record in self._read()]

    def _write(self, records: list[list[str]]) -> None:
        folder = self.path.parent
        try:
            if folder.is_symlink():
                raise ChatArchiveError("Pasta do histórico não pode ser um link simbólico.")
            folder.mkdir(mode=0o700, parents=True, exist_ok=True)
            if folder.is_symlink() or not folder.is_dir():
                raise ChatArchiveError("Pasta de histórico insegura.")
            folder.chmod(0o700)
            self._check_path()
            raw = json.dumps(
                {"version": 1, "records": records[-self.MAX_RECORDS:]},
                ensure_ascii=False, separators=(",", ":"),
            ).encode("utf-8")
            if len(raw) > self.MAX_FILE_BYTES:
                raise ChatArchiveError("Limite de armazenamento de histórico atingido.")
            fd, temporary = tempfile.mkstemp(prefix=".chat-", dir=str(folder))
            try:
                with os.fdopen(fd, "wb") as stream:
                    os.fchmod(stream.fileno(), 0o600)
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, self.path)
            finally:
                Path(temporary).unlink(missing_ok=True)
        except OSError as exc:
            raise ChatArchiveError("Não foi possível salvar histórico neste computador.") from exc

    def append(self, question: str, answer: str) -> None:
        if (not isinstance(question, str) or not isinstance(answer, str)
                or not question.strip() or not answer.strip()):
            raise ChatArchiveError("Registro de conversa inválido.")
        with self._lock:
            records = self._read()
            records.append([
                question[:self.MAX_ENTRY_CHARS],
                answer[:self.MAX_ENTRY_CHARS],
            ])
            self._write(records[-self.MAX_RECORDS:])

    def clear(self) -> None:
        """Permanently delete the archive after explicit UI confirmation."""
        with self._lock:
            self._check_path()
            try:
                self.path.unlink(missing_ok=True)
            except OSError as exc:
                raise ChatArchiveError("Não foi possível apagar o histórico local.") from exc
