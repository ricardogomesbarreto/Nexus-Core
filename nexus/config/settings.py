from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    """
    Configurações principais do Nexus.
    """

    app_name: str = "Nexus Core"
    version: str = "0.2.2"
    node_name: str = "NEXUS-NODE-01"

    project_root: Path = PROJECT_ROOT

    data_dir: Path = PROJECT_ROOT / "data"
    logs_dir: Path = PROJECT_ROOT / "logs"

    database_dir: Path = PROJECT_ROOT / "data" / "database"
    database_file: Path = PROJECT_ROOT / "data" / "database" / "nexus.db"

    offline_mode: bool = True

    connectivity_monitor_interval: float = 30.0


settings = Settings()
