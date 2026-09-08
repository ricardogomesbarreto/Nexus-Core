import math
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


from nexus.config.local_endpoint import (
    normalize_local_http_origin,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


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
    version: str = "0.3.1"
    node_name: str = "NEXUS-NODE-01"

    project_root: Path = PROJECT_ROOT

    data_dir: Path = PROJECT_ROOT / "data"
    logs_dir: Path = PROJECT_ROOT / "logs"

    database_dir: Path = PROJECT_ROOT / "data" / "database"
    database_file: Path = PROJECT_ROOT / "data" / "database" / "nexus.db"

    offline_mode: bool = True

    connectivity_monitor_interval: float = 30.0
    connectivity_confirmation_threshold: int = 2

    local_model_name: str = "qwen3:1.7b"
    local_model_base_url: str = "http://127.0.0.1:11434"
    local_model_timeout: float = 120.0


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

    return Settings(
        node_name=node_name,
        offline_mode=offline_mode,
        connectivity_monitor_interval=monitor_interval,
        connectivity_confirmation_threshold=confirmation_threshold,
        local_model_name=local_model_name,
        local_model_base_url=local_model_base_url,
        local_model_timeout=local_model_timeout,
    )


settings = load_settings()
