"""Pruebas del host que coordina Claude y las herramientas MCP."""

import unittest
from typing import Any

from src.chatbot_host import ChatbotHost
from src.mcp_client import McpToolError


TOOLS = [
    {"name": "list_rooms", "description": "Lista salas", "inputSchema": {"type": "object"}},
    {"name": "check_availability", "description": "Consulta disponibilidad", "inputSchema": {"type": "object"}},
    {"name": "create_reservation", "description": "Crea reserva", "inputSchema": {"type": "object"}},
    {"name": "cancel_reservation", "description": "Cancela reserva", "inputSchema": {"type": "object"}},
]


class FakeClaude:
    def __init__(self, responses: list[list[dict[str, Any]]]) -> None:
        self.responses = iter(responses)
        self.messages: list[list[dict[str, Any]]] = []

    def generate_content(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        self.messages.append(messages)
        return next(self.responses)


class FakeMcpClient:
    def __init__(self, result: dict[str, Any] | None = None, error: str | None = None) -> None:
        self.initialized = False
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.result = result or {"content": [{"type": "text", "text": "ok"}]}
        self.error = error

    def initialize(self) -> None:
        self.initialized = True

    def list_tools(self) -> list[dict[str, Any]]:
        return TOOLS

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((name, arguments))
        if self.error:
            raise McpToolError(self.error)
        return self.result


def tool_use(name: str, input_data: dict[str, Any]) -> list[dict[str, Any]]:
    return [{"type": "tool_use", "id": "tool-1", "name": name, "input": input_data}]


class ChatbotHostTests(unittest.TestCase):
    def host(self, responses: list[list[dict[str, Any]]], mcp: FakeMcpClient | None = None) -> tuple[ChatbotHost, FakeMcpClient, FakeClaude]:
        fake_mcp = mcp or FakeMcpClient()
        fake_claude = FakeClaude(responses)
        host = ChatbotHost(fake_claude, fake_mcp)
        host.initialize()
        return host, fake_mcp, fake_claude

    def test_pregunta_general_no_usa_tool(self) -> None:
        host, mcp, _ = self.host([[{"type": "text", "text": "Alan Turing fue un matemático."}]])

        response = host.respond("¿Quién fue Alan Turing?")

        self.assertIn("Alan Turing", response)
        self.assertEqual(mcp.calls, [])

    def test_consulta_de_salas(self) -> None:
        host, mcp, _ = self.host([tool_use("list_rooms", {}), [{"type": "text", "text": "Tenemos tres salas."}]])

        host.respond("¿Qué salas tenemos?")

        self.assertEqual(mcp.calls[0][0], "list_rooms")

    def test_consulta_de_disponibilidad(self) -> None:
        arguments = {"room_id": "room-001", "date": "2026-09-15", "start_time": "10:00", "end_time": "11:00"}
        host, mcp, _ = self.host([tool_use("check_availability", arguments), [{"type": "text", "text": "Está disponible."}]])

        host.respond("¿Está disponible la Sala Atitlán?")

        self.assertEqual(mcp.calls, [("check_availability", arguments)])

    def test_creacion_de_reserva(self) -> None:
        arguments = {"room_id": "room-001", "date": "2026-09-15", "start_time": "10:00", "end_time": "11:00", "reserved_by": "Anggelie", "title": "Reunión de proyecto"}
        host, mcp, _ = self.host([tool_use("create_reservation", arguments), [{"type": "text", "text": "Reserva creada."}]])

        host.respond("Reserva la Sala Atitlán.")

        self.assertEqual(mcp.calls[0], ("create_reservation", arguments))

    def test_cancelacion(self) -> None:
        host, mcp, _ = self.host([tool_use("cancel_reservation", {"reservation_id": "RES-0001"}), [{"type": "text", "text": "Reserva cancelada."}]])

        host.respond("Cancela la reserva RES-0001.")

        self.assertEqual(mcp.calls[0][0], "cancel_reservation")

    def test_error_por_superposicion_regresa_al_llm(self) -> None:
        host, mcp, claude = self.host([tool_use("create_reservation", {"room_id": "room-001"}), [{"type": "text", "text": "No se pudo reservar porque existe un traslape."}]], FakeMcpClient(error="La sala ya está reservada durante ese intervalo."))

        response = host.respond("Reserva la sala en ese horario.")

        self.assertIn("traslape", response)
        self.assertEqual(len(claude.messages), 2)
        self.assertTrue(mcp.calls)


if __name__ == "__main__":
    unittest.main()