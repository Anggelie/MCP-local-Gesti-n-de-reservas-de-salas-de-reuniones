"""Pruebas del ciclo MCP manual para el servidor de reservas."""

import json
import tempfile
import unittest
from pathlib import Path

from src.json_rpc import build_notification, build_request
from src.mcp_server import MeetingRoomMcpServer
from src.reservation_service import ReservationService


class McpServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        root = Path(self.directory.name)
        rooms_file = root / "rooms.json"
        reservations_file = root / "reservations.json"
        rooms_file.write_text(json.dumps([{"room_id": "room-001", "name": "Sala Atitlán"}], ensure_ascii=False), encoding="utf-8")
        reservations_file.write_text("[]", encoding="utf-8")
        service = ReservationService(rooms_file, reservations_file)
        self.server = MeetingRoomMcpServer(service)

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_initialize_y_tools_list(self) -> None:
        initialize = self.server.handle_message(build_request(1, "initialize", {}))
        tools_list = self.server.handle_message(build_request(2, "tools/list", {}))

        self.assertEqual(initialize["result"]["capabilities"], {"tools": {}})
        self.assertEqual(tools_list["result"]["tools"][0]["name"], "list_rooms")

    def test_notification_initialized_no_responde(self) -> None:
        self.server.handle_message(build_request(1, "initialize", {}))
        response = self.server.handle_message(build_notification("notifications/initialized"))

        self.assertIsNone(response)

    def test_tools_call_devuelve_error_de_herramienta(self) -> None:
        self.server.handle_message(build_request(1, "initialize", {}))
        response = self.server.handle_message(
            build_request(2, "tools/call", {"name": "cancel_reservation", "arguments": {"reservation_id": "RES-9999"}})
        )

        self.assertTrue(response["result"]["isError"])


if __name__ == "__main__":
    unittest.main()