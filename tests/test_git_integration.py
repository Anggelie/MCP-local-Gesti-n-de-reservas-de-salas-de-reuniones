"""Prueba de integración opcional con el servidor oficial Git MCP."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from src.mcp_external_servers import create_git_client


def uvx_is_available() -> bool:
    """Verifica uvx en Windows sin depender de un wrapper de PowerShell."""
    try:
        result = subprocess.run(
            ["cmd", "/c", "uvx", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


@unittest.skipUnless(uvx_is_available(), "uvx no está disponible para Git MCP")
class GitMcpIntegrationTests(unittest.TestCase):
    def test_operaciones_git_principales(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory) / "demo_repository"
            repository.mkdir()
            subprocess.run(["git", "init", str(repository)], check=True, capture_output=True)
            readme = repository / "README.md"
            readme.write_text("# Git MCP Demo\n", encoding="utf-8")
            log_file = Path(directory) / "mcp.log"

            with create_git_client(log_file) as client:
                initialize = client.initialize()
                tools = client.list_tools()
                tool_names = {tool["name"] for tool in tools}
                self.assertNotIn("git_init", tool_names)
                self.assertIn("git_status", tool_names)
                self.assertIn("git_add", tool_names)
                self.assertIn("git_commit", tool_names)
                self.assertIn("git_log", tool_names)

                status_before = client.call_tool("git_status", {"repo_path": str(repository)})
                client.call_tool("git_add", {"repo_path": str(repository), "files": ["README.md"]})
                commit = client.call_tool(
                    "git_commit",
                    {"repo_path": str(repository), "message": "Agregar README de demostracion MCP"},
                )
                log = client.call_tool(
                    "git_log", {"repo_path": str(repository), "max_count": 1}
                )
                status_after = client.call_tool("git_status", {"repo_path": str(repository)})

            self.assertEqual(initialize["protocolVersion"], "2024-11-05")
            self.assertIn("content", status_before)
            self.assertIn("content", commit)
            self.assertIn("Agregar README de demostracion MCP", json.dumps(log, ensure_ascii=False))
            self.assertIn("content", status_after)
            self.assertTrue((repository / ".git").is_dir())
            self.assertTrue(log_file.is_file())
            git_log = subprocess.run(
                ["git", "-C", str(repository), "log", "-1", "--pretty=%s"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertEqual(git_log, "Agregar README de demostracion MCP")


if __name__ == "__main__":
    unittest.main()