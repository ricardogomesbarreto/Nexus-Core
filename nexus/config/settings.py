import math
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path


from nexus.config.local_endpoint import (
    normalize_local_http_origin,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _user_directory(variable: str, fallback: Path) -> Path:
    configured = os.environ.get(variable)
    root = Path(configured) if configured else fallback
    if not root.is_absolute():
        root = fallback
    return root / "nexus-core"


def _data_directory() -> Path:
    return _user_directory(
        "XDG_DATA_HOME", Path.home() / ".local" / "share"
    )


def _logs_directory() -> Path:
    return _user_directory(
        "XDG_STATE_HOME", Path.home() / ".local" / "state"
    ) / "logs"


class ConfigurationError(ValueError):
    """
    Erro de configuração externa inválida.
    """


@dataclass(frozen=True)
class Settings:
    """
    Configurações principais do Nexus.
    """

    app_name: str = "Nexus Core"
    version: str = "0.6.2"
    node_name: str = "NEXUS-NODE-01"

    project_root: Path = PROJECT_ROOT

    data_dir: Path = field(default_factory=_data_directory)
    logs_dir: Path = field(default_factory=_logs_directory)

    database_provider: str = "postgresql"
    database_host: str = "127.0.0.1"
    database_port: int = 5432
    database_name: str = "nexus"
    database_user: str = "nexus"
    database_password: str | None = field(
        default=None,
        repr=False,
    )
    database_connect_timeout: float = 5.0

    offline_mode: bool = True

    connectivity_monitor_interval: float = 30.0
    connectivity_confirmation_threshold: int = 2

    local_model_name: str = "qwen3:1.7b"
    local_model_base_url: str = "http://127.0.0.1:11434"
    local_model_timeout: float = 120.0
    voice_model_path: Path | None = None


def _parse_bool(
    environment_name: str,
    value: str,
) -> bool:
    normalized = value.strip().lower()

    if normalized == "true":
        return True

    if normalized == "false":
        return False

    raise ConfigurationError(
        f"{environment_name} deve ser 'true' ou 'false'"
    )


def load_settings(
    environment: Mapping[str, str] | None = None,
) -> Settings:
    """
    Carrega configurações com overrides explícitos de ambiente.

    Quando environment não é fornecido, utiliza os.environ.
    """

    source = os.environ if environment is None else environment
    defaults = Settings()

    node_name = defaults.node_name
    if "NEXUS_NODE_NAME" in source:
        node_name = source["NEXUS_NODE_NAME"].strip()

        if not node_name:
            raise ConfigurationError(
                "NEXUS_NODE_NAME não pode ser vazio"
            )

    offline_mode = defaults.offline_mode
    if "NEXUS_OFFLINE_MODE" in source:
        offline_mode = _parse_bool(
            "NEXUS_OFFLINE_MODE",
            source["NEXUS_OFFLINE_MODE"],
        )

    monitor_interval = defaults.connectivity_monitor_interval
    if "NEXUS_CONNECTIVITY_MONITOR_INTERVAL" in source:
        try:
            monitor_interval = float(
                source["NEXUS_CONNECTIVITY_MONITOR_INTERVAL"]
            )
        except ValueError as exc:
            raise ConfigurationError(
                "NEXUS_CONNECTIVITY_MONITOR_INTERVAL deve ser um número"
            ) from exc

        if (
            not math.isfinite(monitor_interval)
            or monitor_interval <= 0
        ):
            raise ConfigurationError(
                "NEXUS_CONNECTIVITY_MONITOR_INTERVAL "
                "deve ser finito e maior que zero"
            )

    confirmation_threshold = (
        defaults.connectivity_confirmation_threshold
    )
    if "NEXUS_CONNECTIVITY_CONFIRMATION_THRESHOLD" in source:
        try:
            confirmation_threshold = int(
                source[
                    "NEXUS_CONNECTIVITY_CONFIRMATION_THRESHOLD"
                ]
            )
        except ValueError as exc:
            raise ConfigurationError(
                "NEXUS_CONNECTIVITY_CONFIRMATION_THRESHOLD "
                "deve ser um inteiro"
            ) from exc

        if confirmation_threshold < 2:
            raise ConfigurationError(
                "NEXUS_CONNECTIVITY_CONFIRMATION_THRESHOLD "
                "deve ser maior ou igual a 2"
            )

    database_provider = defaults.database_provider
    if "NEXUS_DATABASE_PROVIDER" in source:
        database_provider = source[
            "NEXUS_DATABASE_PROVIDER"
        ].strip().lower()

        if database_provider != "postgresql":
            raise ConfigurationError(
                "NEXUS_DATABASE_PROVIDER deve ser 'postgresql'"
            )

    database_host = defaults.database_host
    if "NEXUS_DATABASE_HOST" in source:
        database_host = source[
            "NEXUS_DATABASE_HOST"
        ].strip().lower()

        if database_host not in {
            "127.0.0.1",
            "localhost",
            "::1",
        }:
            raise ConfigurationError(
                "NEXUS_DATABASE_HOST deve apontar para loopback local"
            )

    database_port = defaults.database_port
    if "NEXUS_DATABASE_PORT" in source:
        try:
            database_port = int(
                source["NEXUS_DATABASE_PORT"]
            )
        except ValueError as exc:
            raise ConfigurationError(
                "NEXUS_DATABASE_PORT deve ser um inteiro"
            ) from exc

        if not 1 <= database_port <= 65535:
            raise ConfigurationError(
                "NEXUS_DATABASE_PORT deve estar entre 1 e 65535"
            )

    database_name = defaults.database_name
    if "NEXUS_DATABASE_NAME" in source:
        database_name = source[
            "NEXUS_DATABASE_NAME"
        ].strip()

        if not database_name:
            raise ConfigurationError(
                "NEXUS_DATABASE_NAME não pode ser vazio"
            )

    database_user = defaults.database_user
    if "NEXUS_DATABASE_USER" in source:
        database_user = source[
            "NEXUS_DATABASE_USER"
        ].strip()

        if not database_user:
            raise ConfigurationError(
                "NEXUS_DATABASE_USER não pode ser vazio"
            )

    database_password = defaults.database_password
    if "NEXUS_DATABASE_PASSWORD" in source:
        database_password = source[
            "NEXUS_DATABASE_PASSWORD"
        ]

        if not database_password.strip():
            raise ConfigurationError(
                "NEXUS_DATABASE_PASSWORD não pode ser vazio"
            )

    database_connect_timeout = (
        defaults.database_connect_timeout
    )
    if "NEXUS_DATABASE_CONNECT_TIMEOUT" in source:
        try:
            database_connect_timeout = float(
                source["NEXUS_DATABASE_CONNECT_TIMEOUT"]
            )
        except ValueError as exc:
            raise ConfigurationError(
                "NEXUS_DATABASE_CONNECT_TIMEOUT deve ser um número"
            ) from exc

        if (
            not math.isfinite(database_connect_timeout)
            or database_connect_timeout <= 0
        ):
            raise ConfigurationError(
                "NEXUS_DATABASE_CONNECT_TIMEOUT "
                "deve ser finito e maior que zero"
            )

    local_model_name = defaults.local_model_name
    if "NEXUS_LOCAL_MODEL_NAME" in source:
        local_model_name = source[
            "NEXUS_LOCAL_MODEL_NAME"
        ].strip()

        if not local_model_name:
            raise ConfigurationError(
                "NEXUS_LOCAL_MODEL_NAME não pode ser vazio"
            )

    local_model_base_url = defaults.local_model_base_url
    if "NEXUS_LOCAL_MODEL_BASE_URL" in source:
        try:
            local_model_base_url = (
                normalize_local_http_origin(
                    source[
                        "NEXUS_LOCAL_MODEL_BASE_URL"
                    ]
                )
            )
        except ValueError as exc:
            raise ConfigurationError(
                "NEXUS_LOCAL_MODEL_BASE_URL inválida"
            ) from exc

    local_model_timeout = defaults.local_model_timeout
    if "NEXUS_LOCAL_MODEL_TIMEOUT" in source:
        try:
            local_model_timeout = float(
                source["NEXUS_LOCAL_MODEL_TIMEOUT"]
            )
        except ValueError as exc:
            raise ConfigurationError(
                "NEXUS_LOCAL_MODEL_TIMEOUT deve ser um número"
            ) from exc

        if (
            not math.isfinite(local_model_timeout)
            or local_model_timeout <= 0
        ):
            raise ConfigurationError(
                "NEXUS_LOCAL_MODEL_TIMEOUT deve ser "
                "finito e maior que zero"
            )

    voice_model_path = defaults.voice_model_path
    if "NEXUS_VOSK_MODEL_PATH" in source:
        candidate = Path(source["NEXUS_VOSK_MODEL_PATH"].strip()).expanduser()
        if not source["NEXUS_VOSK_MODEL_PATH"].strip() or not candidate.is_absolute():
            raise ConfigurationError("NEXUS_VOSK_MODEL_PATH deve ser absoluto")
        voice_model_path = candidate

    return Settings(
        node_name=node_name,
        database_provider=database_provider,
        database_host=database_host,
        database_port=database_port,
        database_name=database_name,
        database_user=database_user,
        database_password=database_password,
        database_connect_timeout=database_connect_timeout,
        offline_mode=offline_mode,
        connectivity_monitor_interval=monitor_interval,
        connectivity_confirmation_threshold=confirmation_threshold,
        local_model_name=local_model_name,
        local_model_base_url=local_model_base_url,
        local_model_timeout=local_model_timeout,
        voice_model_path=voice_model_path,
    )


settings = load_settings()
