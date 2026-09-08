"""Configuración central de la aplicación."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIRECTORY = PROJECT_ROOT / "logs"
LOG_FILE = LOGS_DIRECTORY / "chatbot.log"
MCP_LOG_FILE = LOGS_DIRECTORY / "mcp_interactions.log"
DATA_DIRECTORY = Path(os.getenv("MCP_DATA_DIR") or str(PROJECT_ROOT / "data"))
ROOMS_FILE = DATA_DIRECTORY / "rooms.json"
RESERVATIONS_FILE = DATA_DIRECTORY / "reservations.json"
EXIT_COMMAND = "salir"
CLEAR_COMMAND = "/clear"
APPLICATION_NAME = "Chatbot MCP de reservas"
DEFAULT_ANTHROPIC_MODEL = "claude-3-5-haiku-latest"
DEFAULT_RESERVATIONS_URL = "http://127.0.0.1:8000/mcp"
DEFAULT_RESERVATIONS_MODE = "local"


def get_anthropic_api_key() -> str:
	"""Obtiene la clave de Anthropic sin almacenarla en el código."""
	api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
	if not api_key:
		raise ValueError(
			"No se encontró ANTHROPIC_API_KEY. "
			"Configúrala como variable de entorno antes de iniciar el chatbot."
		)
	return api_key


def get_anthropic_model() -> str:
	"""Obtiene el modelo configurado o utiliza un valor predeterminado."""
	return os.getenv("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL).strip()
