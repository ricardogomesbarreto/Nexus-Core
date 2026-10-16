import json
from json import JSONDecodeError
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from nexus.config.local_endpoint import (
    normalize_local_http_origin,
)


class OllamaTransportError(RuntimeError):
    """
    Erro base do transporte Ollama.
    """


class OllamaUnavailableError(OllamaTransportError):
    """
    O servidor Ollama não pôde ser alcançado.
    """


class OllamaTimeoutError(OllamaTransportError):
    """
    A requisição ao Ollama excedeu o timeout.
    """


class OllamaHTTPError(OllamaTransportError):
    """Ollama local returned HTTP failure without exposing private response data."""

    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class OllamaInvalidJSONError(OllamaTransportError):
    """
    O Ollama respondeu com JSON inválido.
    """


class OllamaTransport:
    """
    Transporte HTTP para a API local do Ollama.
    """

    MAX_CHAT_RESPONSE_BYTES = 8 * 1024 * 1024

    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:11434",
        opener=urlopen,
    ) -> None:
        self.base_url = normalize_local_http_origin(
            base_url
        )
        self.opener = opener

    def chat(
        self,
        *,
        payload,
        timeout: float,
    ):
        request = Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with self.opener(
                request,
                timeout=timeout,
            ) as response:
                body = response.read(self.MAX_CHAT_RESPONSE_BYTES + 1)
        except HTTPError as exc:
            raise OllamaHTTPError(
                f"Ollama respondeu HTTP {exc.code}",
                status_code=exc.code,
            ) from exc
        except TimeoutError as exc:
            raise OllamaTimeoutError(
                "timeout ao acessar o Ollama"
            ) from exc
        except URLError as exc:
            if isinstance(
                exc.reason,
                TimeoutError,
            ):
                raise OllamaTimeoutError(
                    "timeout ao acessar o Ollama"
                ) from exc

            raise OllamaUnavailableError(
                "Ollama indisponível"
            ) from exc

        if len(body) > self.MAX_CHAT_RESPONSE_BYTES:
            raise OllamaInvalidJSONError("Resposta do Ollama excedeu o limite de tamanho")

        try:
            return json.loads(
                body.decode("utf-8")
            )
        except (
            UnicodeDecodeError,
            JSONDecodeError,
        ) as exc:
            raise OllamaInvalidJSONError(
                "Ollama retornou JSON inválido"
            ) from exc

    def list_models(self, *, timeout: float = 5.0) -> list[str]:
        """Read installed Ollama model names on loopback only (no pulls)."""
        request = Request(f"{self.base_url}/api/tags", method="GET")
        try:
            with self.opener(request, timeout=timeout) as response:
                raw = response.read(512 * 1024 + 1)
        except HTTPError as exc:
            raise OllamaHTTPError(f"Ollama respondeu HTTP {exc.code}", status_code=exc.code) from exc
        except (TimeoutError, URLError, OSError) as exc:
            raise OllamaUnavailableError("Ollama local indisponível.") from exc
        if len(raw) > 512 * 1024:
            raise OllamaInvalidJSONError("Lista de modelos excedeu o limite.")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, JSONDecodeError) as exc:
            raise OllamaInvalidJSONError("Resposta dos modelos é inválida.") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("models"), list):
            raise OllamaInvalidJSONError("Ollama não retornou a lista de modelos.")
        return [
            entry["name"] for entry in payload["models"]
            if isinstance(entry, dict) and isinstance(entry.get("name"), str)
        ]
