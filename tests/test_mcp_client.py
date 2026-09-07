"""Pruebas del cliente MCP manual y su logger de interacciones."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from src.json_rpc import build_error_response, build_result_response
from src.mcp_client import (
    CLIENT_NAME,
    CLIENT_PROTOCOL_VERSION,
    CLIENT_VERSION,
    McpClient,
    McpProtocolError,
)
from src.mcp_interaction_logger import McpInteractionLogger
from src.mcp_transport import McpTransportError, StdioTransport


class FakeTransport:
    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.sent: list[dict[str, Any]] = []
        self._responses = iter(responses)
        self.closed = False

    def send(self, message: dict[str, Any]) -> None:
        self.sent.append(message)

    def receive(self) -> dict[str, Any]:
        return next(self._responses)

    def close(self) -> None:
        self.closed = True


class McpClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.log_file = Path(self.directory.name) / "mcp.log"

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_inicializa_lista_y_llama_tool(self) -> None:
        responses = [
            build_result_response(
                1,
                {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {"tools": {"listChanged": True}},
                    "serverInfo": {"name": "servidor-prueba", "version": "2.0.0"},
                },
            ),
            build_result_response(2, {"tools": [{"name": "list_rooms"}]}),
            build_result_response(3, {"content": [{"type": "text", "text": "disponible"}]}),
        ]
        transport = FakeTransport(responses)
        client = McpClient(transport, McpInteractionLogger(self.log_file))

        client.initialize()
        tools = client.list_tools()
        result = client.call_tool("check_availability", {"room_id": "room-001"})

        self.assertEqual(tools[0]["name"], "list_rooms")
        self.assertFalse(result.get("isError", False))
        self.assertEqual(transport.sent[1]["method"], "notifications/initialized")
        self.assertEqual(transport.sent[2]["id"], 2)
        initialize_params = transport.sent[0]["params"]
        self.assertEqual(initialize_params["protocolVersion"], CLIENT_PROTOCOL_VERSION)
        self.assertEqual(initialize_params["capabilities"], {})
        self.assertEqual(
            initialize_params["clientInfo"],
            {"name": CLIENT_NAME, "version": CLIENT_VERSION},
        )
        self.assertEqual(client.negotiated_protocol_version, "2025-06-18")
        self.assertEqual(client.server_capabilities, {"tools": {"listChanged": True}})
        self.assertEqual(client.server_info, {"name": "servidor-prueba", "version": "2.0.0"})
        client.close()

    def test_correlaciona_respuesta_y_maneja_error(self) -> None:
        transport = FakeTransport([build_error_response(1, -32601, "Método no encontrado")])
        client = McpClient(transport, McpInteractionLogger(self.log_file))

        with self.assertRaises(McpProtocolError):
            client.initialize()
        client.close()

    def test_logger_registra_direccion_y_mensaje_completo(self) -> None:
        logger = McpInteractionLogger(self.log_file)
        message = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}

        logger.log("CLIENT_TO_SERVER", message)
        record = json.loads(self.log_file.read_text(encoding="utf-8"))

        self.assertEqual(record["direction"], "CLIENT_TO_SERVER")
        self.assertEqual(record["method"], "tools/list")
        self.assertEqual(record["id"], 1)
        self.assertEqual(record["message"], message)
        self.assertIn("timestamp", record)

    def test_stdio_transport_acepta_comando_personalizado(self) -> None:
        command = [sys.executable, "-c", "import sys; sys.stdin.readline()"]
        transport = StdioTransport(command=command, working_directory=Path.cwd())

        self.assertEqual(transport._command, command)
        transport.close()

    def test_stdio_transport_reporta_ejecutable_inexistente(self) -> None:
        with self.assertRaisesRegex(McpTransportError, "No se encontró"):
            StdioTransport(command=["ejecutable-que-no-existe-mcp"])

    def test_stdio_transport_reporta_proceso_terminado(self) -> None:
        with self.assertRaisesRegex(McpTransportError, "terminó inmediatamente"):
            StdioTransport(command=[sys.executable, "-c", "pass"])


if __name__ == "__main__":
    unittest.main()