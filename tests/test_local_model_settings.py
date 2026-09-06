import pytest

from nexus.config.settings import (
    ConfigurationError,
    load_settings,
)


def test_local_model_settings_preserve_safe_defaults():
    settings = load_settings({})

    assert settings.local_model_name == "qwen3:1.7b"
    assert (
        settings.local_model_base_url
        == "http://127.0.0.1:11434"
    )
    assert settings.local_model_timeout == 120.0


def test_local_model_settings_apply_supported_environment_overrides():
    settings = load_settings(
        {
            "NEXUS_LOCAL_MODEL_NAME": "qwen3:4b",
            "NEXUS_LOCAL_MODEL_BASE_URL": (
                "http://localhost:11434"
            ),
            "NEXUS_LOCAL_MODEL_TIMEOUT": "45.5",
        }
    )

    assert settings.local_model_name == "qwen3:4b"
    assert (
        settings.local_model_base_url
        == "http://localhost:11434"
    )
    assert settings.local_model_timeout == 45.5


@pytest.mark.parametrize(
    "model_name",
    [
        "",
        " ",
        "\n",
        "\t",
    ],
)
def test_local_model_settings_reject_blank_model_name(
    model_name,
):
    with pytest.raises(
        ConfigurationError,
        match="NEXUS_LOCAL_MODEL_NAME",
    ):
        load_settings(
            {
                "NEXUS_LOCAL_MODEL_NAME": model_name,
            }
        )


@pytest.mark.parametrize(
    "timeout",
    [
        "",
        "abc",
        "0",
        "-1",
        "nan",
        "inf",
        "-inf",
    ],
)
def test_local_model_settings_reject_invalid_timeout(
    timeout,
):
    with pytest.raises(
        ConfigurationError,
        match="NEXUS_LOCAL_MODEL_TIMEOUT",
    ):
        load_settings(
            {
                "NEXUS_LOCAL_MODEL_TIMEOUT": timeout,
            }
        )


@pytest.mark.parametrize(
    "base_url",
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
def test_local_model_settings_reject_unsafe_base_url(
    base_url,
):
    with pytest.raises(
        ConfigurationError,
        match="NEXUS_LOCAL_MODEL_BASE_URL",
    ):
        load_settings(
            {
                "NEXUS_LOCAL_MODEL_BASE_URL": base_url,
            }
        )


@pytest.mark.parametrize(
    "base_url",
    [
        "http://127.0.0.1:11434",
        "http://127.0.0.1:11434/",
        "http://localhost:11434",
        "http://[::1]:11434",
    ],
)
def test_local_model_settings_accept_loopback_base_url(
    base_url,
):
    settings = load_settings(
        {
            "NEXUS_LOCAL_MODEL_BASE_URL": base_url,
        }
    )

    assert settings.local_model_base_url


def test_local_model_settings_normalize_text_overrides():
    settings = load_settings(
        {
            "NEXUS_LOCAL_MODEL_NAME": "  qwen3:1.7b  ",
            "NEXUS_LOCAL_MODEL_BASE_URL": (
                "  http://localhost:11434  "
            ),
        }
    )

    assert settings.local_model_name == "qwen3:1.7b"
    assert (
        settings.local_model_base_url
        == "http://localhost:11434"
    )
