"""Pruebas unitarias del coordinador multi-MCP."""

import unittest
from typing import Any

from src.mcp_manager import McpManager


class FakeClient:
    def __init__(self, name: str) -> None:
        self.name = name
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.closed = False
        self.initialize_count = 0

    def initialize(self) -> dict[str, Any]:
        self.initialize_count += 1
        return {"serverInfo": {"name": self.name}}

    def list_tools(self) -> list[dict[str, Any]]:
        return [{"name": f"tool_{self.name}"}]

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((name, arguments))
        return {"server": self.name, "tool": name}

    def close(self) -> None:
        self.closed = True


class McpManagerTests(unittest.TestCase):
    def test_inicializa_descubre_y_enruta_dos_clientes(self) -> None:
        filesystem = FakeClient("filesystem")
        git = FakeClient("git")
        manager = McpManager()
        manager.register("filesystem", filesystem)
        manager.register("git", git)

        initialized = manager.initialize_all()
        tools = manager.list_tools()
        result = manager.call_tool("git.tool_git", {"repo_path": "demo"})

        self.assertEqual(set(initialized), {"filesystem", "git"})
        self.assertEqual(filesystem.initialize_count, 1)
        self.assertEqual(git.initialize_count, 1)
        self.assertEqual(set(tools), {"filesystem", "git"})
        catalog = manager.tool_catalog()
        filesystem_entry = next(item for item in catalog if item["server"] == "filesystem")
        self.assertEqual(filesystem_entry["llm_name"], "filesystem__tool_filesystem")
        self.assertEqual(
            manager.resolve_llm_tool("git__tool_git"), "git.tool_git"
        )
        self.assertEqual(git.calls, [("tool_git", {"repo_path": "demo"})])
        self.assertEqual(result["server"], "git")

    def test_cierra_todos_los_clientes(self) -> None:
        filesystem = FakeClient("filesystem")
        git = FakeClient("git")
        manager = McpManager()
        manager.register("filesystem", filesystem)
        manager.register("git", git)

        manager.close()

        self.assertTrue(filesystem.closed)
        self.assertTrue(git.closed)


if __name__ == "__main__":
    unittest.main()
