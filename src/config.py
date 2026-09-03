"""Configuración central de la aplicación."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIRECTORY = PROJECT_ROOT / "logs"
LOG_FILE = LOGS_DIRECTORY / "chatbot.log"
EXIT_COMMAND = "salir"
APPLICATION_NAME = "Chatbot MCP de reservas"
