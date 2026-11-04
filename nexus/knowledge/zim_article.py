"""Leitura pontual de artigo ZIM usando zimdump local, sem servidor.

Apenas um ZIM selecionado pelo usuário e uma URL de artigo informada.
O descritor autorizado é herdado por subprocesso para impedir TOCTOU.
Nenhum comando shell, download, porta de rede, cache ou importação automática.
"""
from __future__ import annotations

import os
import re
import select
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from time import monotonic

from nexus.security.paths import PathSecurity


class ZimArticleError(ValueError):
    """Erro sanitizado de leitura de material offline."""


class _TextOnly(HTMLParser):
    """Extrai texto superficial, descartando conteúdo ativo de HTML."""
    SKIP = frozenset(("script", "style", "svg", "noscript", "template"))

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._skipping = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() in self.SKIP:
            self._skipping += 1
        elif tag.lower() in ("p", "br", "h1", "h2", "h3", "li") and not self._skipping:
            self._parts.append("\n")

    def handle_endtag(self, tag):
        if tag.lower() in self.SKIP and self._skipping:
            self._skipping -= 1

    def handle_data(self, data):
        if not self._skipping:
            self._parts.append(data)

    def text(self, limit: int = 14000) -> str:
        return re.sub(r"\n{3,}", "\n\n", " ".join(self._parts)).strip()[:limit]


class LocalZimReader:
    MAX_CAPTURE = 96 * 1024
    MAX_SECONDS = 8
    ARTICLE_URL = re.compile(r"[A-Za-z0-9][A-Za-z0-9._~/%+-]{0,199}\Z")

    def __init__(self, paths: PathSecurity | None = None):
        self.paths = paths if paths is not None else PathSecurity()

    def read(self, path: str | Path, article_url: str) -> str:
        if not isinstance(path, (str, Path)) or Path(path).suffix.lower() != ".zim":
            raise ZimArticleError("Selecione um arquivo ZIM.")
        if (not isinstance(article_url, str)
                or not self.ARTICLE_URL.fullmatch(article_url)
                or any(segment in (".", "..") for segment in article_url.split("/"))):
            raise ZimArticleError("URL de artigo ZIM inválida.")
        tool = shutil.which("zimdump")
        if not tool:
            raise ZimArticleError("Instale opcionalmente zim-tools para ler artigos ZIM.")
        try:
            with self.paths.open_regular_file(path) as (fd, _):
                if os.fstat(fd).st_size < 80:
                    raise ZimArticleError("Arquivo ZIM inválido ou incompleto.")
                # Keep the same verified inode open for the entire subprocess.
                process = subprocess.Popen(
                    [tool, "show", "--url=" + article_url, "--",
                     f"/proc/self/fd/{fd}"],
                    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL, pass_fds=(fd,),
                    close_fds=True,
                )
                payload = bytearray()
                completed = False
                try:
                    deadline = monotonic() + self.MAX_SECONDS
                    while True:
                        if monotonic() > deadline:
                            raise ZimArticleError("Consulta ZIM excedeu o tempo limite.")
                        readable, _, _ = select.select([process.stdout], [], [], 0.2)
                        if not readable:
                            if process.poll() is not None:
                                break
                            continue
                        block = os.read(process.stdout.fileno(), 8192)
                        if not block:
                            break
                        payload.extend(block)
                        if len(payload) > self.MAX_CAPTURE:
                            raise ZimArticleError(
                                "Artigo acima do limite de leitura local."
                            )
                    completed = True
                finally:
                    if not completed and process.poll() is None:
                        process.kill()
                    try:
                        process.wait(timeout=1 if completed else 3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=3)
                    process.stdout.close()
                if process.returncode != 0:
                    raise ZimArticleError("Artigo não encontrado ou ZIM incompatível.")
        except ZimArticleError:
            raise
        except (OSError, PermissionError, subprocess.SubprocessError,
                ValueError) as exc:
            raise ZimArticleError("Não foi possível consultar o ZIM autorizado.") from exc
        try:
            source = payload.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise ZimArticleError("Artigo não contém texto UTF-8 válido.") from exc
        if "<html" in source.lower() or "<p" in source.lower():
            parser = _TextOnly()
            parser.feed(source)
            result = parser.text()
        else:
            result = source.strip()[:14000]
        if not result:
            raise ZimArticleError("Artigo ZIM sem conteúdo textual.")
        return result
