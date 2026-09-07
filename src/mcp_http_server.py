"""Servidor HTTP local para el MCP manual de reservas."""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .mcp_protocol_handler import McpProtocolHandler

MAX_BODY_BYTES = 1_048_576
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


def get_http_address(host: str | None = None, port: int | None = None) -> tuple[str, int]:
    """Obtiene bind host/port locales o los valores inyectados por Render."""
    bind_host = host or os.getenv("HOST") or DEFAULT_HOST
    bind_port = port if port is not None else int(os.getenv("PORT") or DEFAULT_PORT)
    return bind_host, bind_port


class McpHttpRequestHandler(BaseHTTPRequestHandler):
    """Adaptador HTTP que delega el protocolo en McpProtocolHandler."""

    protocol_handler = McpProtocolHandler()

    def do_GET(self) -> None:
        if self.path != "/health":
            self._send_json(404, {"error": "Ruta no encontrada."})
            return
        self._send_json(200, {"status": "ok"})

    def do_POST(self) -> None:
        if self.path != "/mcp":
            self._send_json(404, {"error": "Ruta no encontrada."})
            return
        if self.headers.get_content_type() != "application/json":
            self._send_json(415, {"error": "Content-Type debe ser application/json."})
            return
        try:
            length = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            self._send_json(400, {"error": "Content-Length inválido."})
            return
        if length < 0 or length > MAX_BODY_BYTES:
            self._send_json(413, {"error": "El cuerpo de la solicitud es demasiado grande."})
            return
        try:
            message = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(message, dict):
                raise ValueError("El mensaje debe ser un objeto JSON.")
            response = self.protocol_handler.handle_message(message)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            self._send_json(400, {"error": f"JSON inválido: {error}"})
            return
        except Exception:
            self._send_json(500, {"error": "Error interno del servidor."})
            return
        if response is None:
            self.send_response(204)
            self.end_headers()
            return
        self._send_json(200, response)

    def log_message(self, *_: Any) -> None:
        return

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve_http(host: str | None = None, port: int | None = None) -> None:
    bind_host, bind_port = get_http_address(host, port)
    print(f"Starting MCP HTTP server on {bind_host}:{bind_port}", flush=True)
    server = ThreadingHTTPServer((bind_host, bind_port), McpHttpRequestHandler)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    serve_http()
