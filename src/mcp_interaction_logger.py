"""Registro estructurado de las interacciones entre cliente y servidor MCP."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class McpInteractionLogger:
    """Escribe cada mensaje MCP como un registro JSON independiente."""

    def __init__(self, log_file: Path) -> None:
        self._log_file = log_file
        self._log_file.parent.mkdir(parents=True, exist_ok=True)

    def log(self, direction: str, message: dict[str, Any]) -> None:
        """Registra dirección, metadatos y mensaje completo en formato JSON Lines."""
        if direction not in {"CLIENT_TO_SERVER", "SERVER_TO_CLIENT"}:
            raise ValueError(f"Dirección MCP inválida: {direction}")

        record: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "direction": direction,
            "message": message,
        }
        if "method" in message:
            record["method"] = message["method"]
        if "id" in message:
            record["id"] = message["id"]

        with self._log_file.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")