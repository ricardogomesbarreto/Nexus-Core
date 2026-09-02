from dataclasses import dataclass
from urllib.request import Request, urlopen


@dataclass
class ConnectivityStatus:
    """
    Representa o estado atual da conectividade do Nexus Core.
    """

    online: bool = False
    latency_ms: float | None = None
    endpoint: str | None = None


class ConnectivityManager:
    """
    Gerencia verificações de conectividade externa.
    """

    def __init__(
        self,
        endpoint: str = "https://www.google.com",
        timeout: float = 3.0,
    ):
        self.endpoint = endpoint
        self.timeout = timeout

    def check(self) -> ConnectivityStatus:
        """
        Verifica se o Nexus possui acesso externo.
        """

        request = Request(
            self.endpoint,
            method="HEAD",
        )

        try:
            with urlopen(
                request,
                timeout=self.timeout,
            ):
                return ConnectivityStatus(
                    online=True,
                    endpoint=self.endpoint,
                )

        except Exception:
            return ConnectivityStatus(
                online=False,
                endpoint=self.endpoint,
            )
