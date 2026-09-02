import logging
from pathlib import Path

from nexus.config.settings import settings


def setup_logger() -> logging.Logger:
    """
    Inicializa o sistema de logging do Nexus.
    """

    settings.logs_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("nexus")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    log_file = Path(settings.logs_dir) / "nexus.log"

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
