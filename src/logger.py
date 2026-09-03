"""Configuración del registro de eventos de la aplicación."""

import logging
import sys

from .config import LOGS_DIRECTORY, LOG_FILE


def configure_logging() -> logging.Logger:
    """Configura un registro visible en terminal y persistido en un archivo."""
    logger = logging.getLogger("chatbot")
    if logger.handlers:
        return logger

    LOGS_DIRECTORY.mkdir(parents=True, exist_ok=True)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger
