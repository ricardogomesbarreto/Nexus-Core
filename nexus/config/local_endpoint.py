from ipaddress import ip_address
from urllib.parse import urlsplit


def normalize_local_http_origin(
    value: str,
) -> str:
    """
    Valida e normaliza uma origem HTTP estritamente local.

    São permitidos somente hosts loopback, sem credenciais,
    path arbitrário, query ou fragment.
    """

    if (
        not isinstance(value, str)
        or not value.strip()
    ):
        raise ValueError(
            "endpoint deve ser texto não vazio"
        )

    normalized = value.strip()

    try:
        parsed = urlsplit(normalized)
        port = parsed.port
    except ValueError as exc:
        raise ValueError(
            "endpoint possui URL inválida"
        ) from exc

    if parsed.scheme != "http":
        raise ValueError(
            "endpoint deve utilizar HTTP"
        )

    if (
        parsed.username is not None
        or parsed.password is not None
    ):
        raise ValueError(
            "endpoint não pode conter credenciais"
        )

    if (
        parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(
            "endpoint deve apontar somente "
            "para uma origem local"
        )

    hostname = parsed.hostname

    if not hostname:
        raise ValueError(
            "endpoint deve possuir host"
        )

    if hostname != "localhost":
        try:
            address = ip_address(hostname)
        except ValueError as exc:
            raise ValueError(
                "endpoint deve utilizar host loopback"
            ) from exc

        if not address.is_loopback:
            raise ValueError(
                "endpoint deve utilizar host loopback"
            )

    if port is not None and not (
        1 <= port <= 65535
    ):
        raise ValueError(
            "endpoint possui porta inválida"
        )

    return normalized.rstrip("/")
