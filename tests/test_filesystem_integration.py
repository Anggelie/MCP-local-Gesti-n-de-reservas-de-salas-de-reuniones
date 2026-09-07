"""Pruebas de integración opcionales con el servidor oficial Filesystem MCP."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from src.mcp_external_servers import create_filesystem_client


def npx_is_available() -> bool:
    """Verifica npx mediante cmd para evitar la ExecutionPolicy de PowerShell."""
    try:
        result = subprocess.run(
            ["cmd", "/c", "npx", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


@unittest.skipUnless(npx_is_available(), "npx no está disponible para Filesystem MCP")
class FilesystemMcpIntegrationTests(unittest.TestCase):
    def test_crea_escribe_y_lee_archivo(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            allowed_directory = Path(directory)
            log_file = allowed_directory / "mcp.log"
            repository_directory = allowed_directory / "demo_repository"
            readme_file = repository_directory / "README.md"

            with create_filesystem_client(allowed_directory, log_file) as client:
                client.initialize()
                tools = {tool["name"] for tool in client.list_tools()}
                self.assertTrue(
                    {"list_allowed_directories", "create_directory", "write_file", "read_text_file"}
                    <= tools
                )

                client.call_tool("list_allowed_directories", {})
                client.call_tool("create_directory", {"path": str(repository_directory)})
                client.call_tool(
                    "write_file",
                    {"path": str(readme_file), "content": "# MCP Filesystem Demo\n"},
                )
                result = client.call_tool("read_text_file", {"path": str(readme_file)})

            self.assertTrue(readme_file.is_file())
            self.assertIn("MCP Filesystem Demo", json.dumps(result, ensure_ascii=False))
            self.assertTrue(log_file.is_file())


if __name__ == "__main__":
    unittest.main()