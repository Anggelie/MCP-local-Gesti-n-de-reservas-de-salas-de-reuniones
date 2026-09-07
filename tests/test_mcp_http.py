"""Pruebas del servidor y transporte HTTP MCP manual."""

import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from pathlib import Path

from src.mcp_client import McpClient, McpProtocolError, McpToolError
from src.mcp_http_server import McpHttpRequestHandler
from src.mcp_http_transport import HttpTransport, HttpTransportError
from src.mcp_protocol_handler import McpProtocolHandler
from src.reservation_service import ReservationService


class HttpFixture:
    def __init__(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        root = Path(self.directory.name)
        rooms = root / "rooms.json"
        reservations = root / "reservations.json"
        rooms.write_text(json.dumps([{"room_id": "room-001", "name": "Sala Atitlán"}], ensure_ascii=False), encoding="utf-8")
        reservations.write_text("[]", encoding="utf-8")
        handler_type = type("TestHandler", (McpHttpRequestHandler,), {})
        handler_type.protocol_handler = McpProtocolHandler(ReservationService(rooms, reservations))
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler_type)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.directory.cleanup()


class HttpMcpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = HttpFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def test_health_y_mcp_con_cliente_manual(self) -> None:
        with urlopen(self.fixture.url + "/health", timeout=2) as response:
            self.assertEqual(json.loads(response.read()), {"status": "ok"})

        transport = HttpTransport(self.fixture.url + "/mcp")
        client = McpClient(transport)
        client.initialize()
        tools = client.list_tools()
        rooms = client.call_tool("list_rooms", {})
        client.close()

        self.assertTrue(any(tool["name"] == "list_rooms" for tool in tools))
        self.assertIn("Sala Atitlán", rooms["content"][0]["text"])

    def test_notification_http_204(self) -> None:
        payload = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}).encode()
        request = Request(self.fixture.url + "/mcp", data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=2) as response:
            self.assertEqual(response.status, 204)

    def test_error_de_tool_via_http(self) -> None:
        transport = HttpTransport(self.fixture.url + "/mcp")
        client = McpClient(transport)
        client.initialize()
        with self.assertRaises(McpToolError):
            client.call_tool("check_availability", {"room_id": "missing", "date": "2026-09-15", "start_time": "10:00", "end_time": "11:00"})
        client.close()

    def test_create_reservation_via_http(self) -> None:
        transport = HttpTransport(self.fixture.url + "/mcp")
        client = McpClient(transport)
        client.initialize()
        result = client.call_tool("create_reservation", {"room_id": "room-001", "date": "2026-09-15", "start_time": "10:00", "end_time": "11:00", "reserved_by": "Prueba", "title": "HTTP"})
        client.close()
        self.assertIn("RES-0001", result["content"][0]["text"])

    def test_status_http_invalido(self) -> None:
        transport = HttpTransport(self.fixture.url + "/missing")
        with self.assertRaises(HttpTransportError):
            transport.send({"jsonrpc": "2.0", "id": 1, "method": "ping"})

    def test_timeout_o_conexion(self) -> None:
        transport = HttpTransport("http://127.0.0.1:1/mcp", timeout=0.1)
        with self.assertRaises(HttpTransportError):
            transport.send({"jsonrpc": "2.0", "id": 1, "method": "ping"})


if __name__ == "__main__":
    unittest.main()
