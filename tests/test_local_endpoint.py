import pytest

from nexus.config.local_endpoint import (
    normalize_local_http_origin,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (
            "http://127.0.0.1:11434",
            "http://127.0.0.1:11434",
        ),
        (
            "http://127.0.0.1:11434/",
            "http://127.0.0.1:11434",
        ),
        (
            "  http://localhost:11434  ",
            "http://localhost:11434",
        ),
        (
            "http://[::1]:11434",
            "http://[::1]:11434",
        ),
    ],
)
def test_normalize_local_http_origin_accepts_loopback_origins(
    value,
    expected,
):
    assert normalize_local_http_origin(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
        "https://127.0.0.1:11434",
        "http://example.com:11434",
        "http://192.168.1.10:11434",
        "http://10.0.0.25:11434",
        "ftp://127.0.0.1:11434",
        "http://user:password@127.0.0.1:11434",
        "http://127.0.0.1:11434/custom",
        "http://127.0.0.1:11434?token=value",
        "http://127.0.0.1:11434#fragment",
    ],
)
def test_normalize_local_http_origin_rejects_unsafe_origins(
    value,
):
    with pytest.raises(ValueError):
        normalize_local_http_origin(value)
