"""Pruebas del handler MCP independiente del transporte."""

import json
import tempfile
import unittest
from pathlib import Path

from src.json_rpc import build_notification, build_request
from src.mcp_protocol_handler import McpProtocolHandler
from src.reservation_service import ReservationService


class ProtocolHandlerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        root = Path(self.directory.name)
        rooms = root / "rooms.json"
        reservations = root / "reservations.json"
        rooms.write_text(json.dumps([{"room_id": "room-001", "name": "Sala Atitlán"}], ensure_ascii=False), encoding="utf-8")
        reservations.write_text("[]", encoding="utf-8")
        self.handler = McpProtocolHandler(ReservationService(rooms, reservations))

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_ciclo_mcp_y_tools_call(self) -> None:
        initialize = self.handler.handle_message(build_request(1, "initialize", {}))
        initialized = self.handler.handle_message(build_notification("notifications/initialized"))
        tools = self.handler.handle_message(build_request(2, "tools/list", {}))
        rooms = self.handler.handle_message(build_request(3, "tools/call", {"name": "list_rooms", "arguments": {}}))

        self.assertEqual(initialize["result"]["protocolVersion"], "2024-11-05")
        self.assertIsNone(initialized)
        self.assertTrue(any(tool["name"] == "list_rooms" for tool in tools["result"]["tools"]))
        self.assertIn("Sala Atitlán", rooms["result"]["content"][0]["text"])

    def test_metodo_desconocido_y_request_invalido(self) -> None:
        self.handler.handle_message(build_request(1, "initialize", {}))
        unknown = self.handler.handle_message(build_request(2, "unknown", {}))
        invalid = self.handler.handle_message({"jsonrpc": "1.0", "id": 3, "method": "tools/list"})

        self.assertEqual(unknown["error"]["code"], -32601)
        self.assertEqual(invalid["error"]["code"], -32600)


if __name__ == "__main__":
    unittest.main()
