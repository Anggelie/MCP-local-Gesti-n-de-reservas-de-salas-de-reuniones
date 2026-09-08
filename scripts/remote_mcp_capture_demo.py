"""Prueba controlada de trafico MCP remoto para una futura captura Wireshark."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.mcp_client import McpClient
from src.mcp_http_transport import HttpTransport
from src.mcp_interaction_logger import McpInteractionLogger

DEFAULT_URL = "https://mcp-reservas.onrender.com/mcp"
CAPTURE_LOG = PROJECT_ROOT / "logs" / "wireshark_mcp_capture.log"


def result_text(result: dict[str, object]) -> str:
    content = result.get("content", [])
    if content and isinstance(content[0], dict):
        return str(content[0].get("text", ""))
    return ""


def main() -> None:
    url = os.getenv("MCP_RESERVATIONS_URL", DEFAULT_URL)
    if not url.startswith("https://"):
        raise RuntimeError("La prueba de captura requiere una URL HTTPS remota.")

    logger = McpInteractionLogger(CAPTURE_LOG, "reservations_remote")
    client = McpClient(HttpTransport(url, timeout=60.0), logger)
    try:
        client.initialize()
        print("[1] initialize enviado")
        print(f"Protocolo negociado: {client.negotiated_protocol_version}")
        print(f"Servidor: {json.dumps(client.server_info, ensure_ascii=False)}")
        print(f"Capacidades: {json.dumps(client.server_capabilities, ensure_ascii=False)}")

        print("[2] notifications/initialized enviado")
        tools = client.list_tools()
        print("[3] tools/list enviado")
        print(f"Tools disponibles: {len(tools)}")

        rooms = client.call_tool("list_rooms", {})
        print("[4] list_rooms ejecutado")
        print(f"Salas recibidas: {result_text(rooms)}")

        availability = client.call_tool(
            "check_availability",
            {
                "room_id": "room-001",
                "date": "2099-12-15",
                "start_time": "10:00",
                "end_time": "11:00",
            },
        )
        print("[5] check_availability ejecutado")
        print(f"Disponibilidad: {result_text(availability)}")

        records = [
            json.loads(line)
            for line in CAPTURE_LOG.read_text(encoding="utf-8").splitlines()
        ]
        methods = [record.get("method") for record in records if record.get("method")]
        print(f"Métodos registrados: {', '.join(methods)}")
        print(f"Log de captura: {CAPTURE_LOG}")
        print("Prueba MCP remota completada")
    finally:
        client.close()


if __name__ == "__main__":
    main()
