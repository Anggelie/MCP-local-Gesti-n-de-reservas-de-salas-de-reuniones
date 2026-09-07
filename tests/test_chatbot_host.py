"""Pruebas del host que coordina Claude y varios servidores MCP."""

import unittest
from typing import Any

from src.chatbot_host import ChatbotHost
from src.mcp_client import McpToolError


TOOLS = [
    {"server": "reservations", "mcp_name": "list_rooms", "llm_name": "reservations__list_rooms", "description": "Lista salas", "inputSchema": {"type": "object"}},
    {"server": "filesystem", "mcp_name": "write_file", "llm_name": "filesystem__write_file", "description": "Escribe archivos", "inputSchema": {"type": "object"}},
    {"server": "git", "mcp_name": "git_status", "llm_name": "git__git_status", "description": "Consulta Git", "inputSchema": {"type": "object"}},
]


class FakeClaude:
    def __init__(self, responses: list[list[dict[str, Any]]]) -> None:
        self.responses = iter(responses)
        self.messages: list[list[dict[str, Any]]] = []
        self.tools: list[dict[str, Any]] = []

    def generate_content(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        self.messages.append(messages)
        self.tools = tools
        return next(self.responses)


class FakeManager:
    def __init__(self, result: dict[str, Any] | None = None, error: str | None = None) -> None:
        self.initialized = False
        self.initialize_calls = 0
        self.catalog = TOOLS
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.result = result or {"content": [{"type": "text", "text": "ok"}]}
        self.error = error

    def initialize_all(self) -> dict[str, dict[str, Any]]:
        self.initialize_calls += 1
        self.initialized = True
        return {}

    def tool_catalog(self) -> list[dict[str, Any]]:
        return self.catalog

    def resolve_llm_tool(self, name: str) -> str:
        for tool in self.catalog:
            if tool["llm_name"] == name:
                return f"{tool['server']}.{tool['mcp_name']}"
        raise RuntimeError(f"No existe {name}")

    def call_tool(self, route: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((route, arguments))
        if self.error:
            raise McpToolError(self.error)
        return self.result


def tool_use(name: str, input_data: dict[str, Any]) -> list[dict[str, Any]]:
    return [{"type": "tool_use", "id": "tool-1", "name": name, "input": input_data}]


class ChatbotHostTests(unittest.TestCase):
    def host(self, responses: list[list[dict[str, Any]]], manager: FakeManager | None = None) -> tuple[ChatbotHost, FakeManager, FakeClaude]:
        fake_manager = manager or FakeManager()
        fake_claude = FakeClaude(responses)
        host = ChatbotHost(fake_claude, fake_manager)
        host.initialize()
        return host, fake_manager, fake_claude

    def test_pregunta_general_no_usa_tool(self) -> None:
        host, manager, _ = self.host([[{"type": "text", "text": "Alan Turing fue un matemático."}]])

        response = host.respond("¿Quién fue Alan Turing?")

        self.assertIn("Alan Turing", response)
        self.assertEqual(manager.calls, [])
        self.assertEqual(manager.initialize_calls, 0)

    def test_expone_catalogo_unificado_a_claude(self) -> None:
        host, _, claude = self.host([[{"type": "text", "text": "Listo."}]])

        host.respond("Hola")

        self.assertEqual(
            {tool["name"] for tool in claude.tools},
            {"reservations__list_rooms", "filesystem__write_file", "git__git_status"},
        )

    def test_claude_llama_tool_de_reservas(self) -> None:
        host, manager, _ = self.host([tool_use("reservations__list_rooms", {}), [{"type": "text", "text": "Hay salas."}]])

        host.respond("¿Qué salas tenemos?")

        self.assertEqual(manager.calls[0][0], "reservations.list_rooms")

    def test_claude_llama_tool_de_filesystem(self) -> None:
        arguments = {"path": "workspace/README.md", "content": "# Demo"}
        host, manager, _ = self.host([tool_use("filesystem__write_file", arguments), [{"type": "text", "text": "Archivo creado."}]])

        host.respond("Crea el README")

        self.assertEqual(manager.calls, [("filesystem.write_file", arguments)])

    def test_claude_llama_tool_de_git(self) -> None:
        arguments = {"repo_path": "workspace", "max_count": 1}
        host, manager, _ = self.host([tool_use("git__git_status", arguments), [{"type": "text", "text": "Estado limpio."}]])

        host.respond("Revisa Git")

        self.assertEqual(manager.calls, [("git.git_status", arguments)])

    def test_error_de_tool_regresa_al_llm(self) -> None:
        host, manager, claude = self.host(
            [tool_use("reservations__list_rooms", {}), [{"type": "text", "text": "No se pudo consultar."}]],
            FakeManager(error="Error de prueba"),
        )

        response = host.respond("Consulta las salas")

        self.assertIn("No se pudo", response)
        self.assertEqual(len(claude.messages), 2)
        self.assertTrue(manager.calls)

    def test_limita_rondas_de_herramientas(self) -> None:
        host, _, _ = self.host([tool_use("git__git_status", {})] * 4)

        with self.assertRaisesRegex(RuntimeError, "máximo"):
            host.respond("Repite")


if __name__ == "__main__":
    unittest.main()
