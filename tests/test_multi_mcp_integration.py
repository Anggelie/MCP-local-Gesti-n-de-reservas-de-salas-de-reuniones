"""Integracion opcional de Filesystem MCP y Git MCP mediante McpManager."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from src.mcp_external_servers import create_filesystem_client, create_git_client
from src.mcp_manager import McpManager


def external_servers_available() -> bool:
    """Comprueba los ejecutables necesarios para la integracion real."""
    return all(shutil.which(command) is not None for command in ("git", "uvx", "npx"))


@unittest.skipUnless(external_servers_available(), "Faltan git, uvx o npx")
class MultiMcpIntegrationTests(unittest.TestCase):
    def test_flujo_filesystem_y_git(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            allowed_directory = root / "multi_mcp_demo"
            allowed_directory.mkdir()
            repository = allowed_directory / "demo_repository"
            readme = repository / "README.md"
            log_file = root / "mcp.log"
            manager = McpManager()
            filesystem = create_filesystem_client(allowed_directory, log_file)
            git = create_git_client(log_file)
            try:
                manager.register("filesystem", filesystem)
                manager.register("git", git)
                manager.initialize_all()
                tools = manager.list_tools()
                self.assertIn("create_directory", {tool["name"] for tool in tools["filesystem"]})
                self.assertIn("git_commit", {tool["name"] for tool in tools["git"]})

                manager.call_tool("filesystem.create_directory", {"path": str(repository)})
                manager.call_tool(
                    "filesystem.write_file",
                    {"path": str(readme), "content": "# MCP Multi Server Demo\n"},
                )
                read_result = manager.call_tool(
                    "filesystem.read_text_file", {"path": str(readme)}
                )

                subprocess.run(["git", "init", str(repository)], check=True, capture_output=True)

                manager.call_tool("git.git_status", {"repo_path": str(repository)})
                manager.call_tool(
                    "git.git_add",
                    {"repo_path": str(repository), "files": ["README.md"]},
                )
                commit_result = manager.call_tool(
                    "git.git_commit",
                    {
                        "repo_path": str(repository),
                        "message": "Agregar README mediante servidores MCP",
                    },
                )
                log_result = manager.call_tool(
                    "git.git_log", {"repo_path": str(repository), "max_count": 1}
                )
                final_status = manager.call_tool(
                    "git.git_status", {"repo_path": str(repository)}
                )

                self.assertIn("MCP Multi Server Demo", json.dumps(read_result, ensure_ascii=False))
                self.assertIn("Changes committed successfully", json.dumps(commit_result))
                self.assertIn("Agregar README", json.dumps(log_result, ensure_ascii=False))
                self.assertIn("working tree clean", json.dumps(final_status))
                self.assertTrue(readme.is_file())
                physical_log = subprocess.run(
                    ["git", "-C", str(repository), "log", "-1", "--pretty=%s"],
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip()
                self.assertEqual(physical_log, "Agregar README mediante servidores MCP")
                self.assertTrue(log_file.is_file())

                records = [
                    json.loads(line)
                    for line in log_file.read_text(encoding="utf-8").splitlines()
                ]
                servers = {record.get("server") for record in records}
                self.assertEqual(servers, {"filesystem", "git"})
            finally:
                manager.close()


if __name__ == "__main__":
    unittest.main()
