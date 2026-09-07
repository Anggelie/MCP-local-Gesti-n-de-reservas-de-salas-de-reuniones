"""Servidor MCP de reservas sobre transporte stdio."""

from __future__ import annotations

import json
import sys

from .json_rpc import build_error_response
from .mcp_protocol_handler import McpProtocolHandler

MeetingRoomMcpServer = McpProtocolHandler


def serve_forever(handler: McpProtocolHandler | None = None) -> None:
    """Lee una solicitud JSON por línea y escribe su respuesta por línea."""
    protocol_handler = handler or McpProtocolHandler()
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            message = json.loads(line)
            response = protocol_handler.handle_message(message)
        except json.JSONDecodeError as error:
            response = build_error_response(None, -32700, f"JSON inválido: {error.msg}")
        except Exception:
            response = build_error_response(None, -32603, "Error interno del servidor.")
        if response is not None:
            print(json.dumps(response, ensure_ascii=True), flush=True)


if __name__ == "__main__":
    serve_forever()
