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
    """
    O Ollama respondeu com erro HTTP.
    """


class OllamaInvalidJSONError(OllamaTransportError):
    """
    O Ollama respondeu com JSON inválido.
    """


class OllamaTransport:
    """
    Transporte HTTP para a API local do Ollama.
    """

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
                body = response.read()
        except HTTPError as exc:
            raise OllamaHTTPError(
                f"Ollama respondeu HTTP {exc.code}"
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
