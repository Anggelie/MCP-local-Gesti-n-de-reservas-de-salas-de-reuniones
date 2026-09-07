"""Pruebas unitarias de la configuración de servidores MCP externos."""

import tempfile
import unittest
from pathlib import Path
from src.mcp_external_servers import (
    FILESYSTEM_SERVER_PACKAGE,
    GIT_SERVER_PACKAGE,
    filesystem_command,
    git_command,
)


class ExternalServerConfigurationTests(unittest.TestCase):
    def test_filesystem_command_usa_paquete_oficial_y_directorio_absoluto(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            allowed_directory = Path(directory)

            command = filesystem_command(allowed_directory)

        self.assertEqual(command[:5], ["cmd", "/c", "npx", "-y", FILESYSTEM_SERVER_PACKAGE])
        self.assertEqual(command[5], str(allowed_directory.resolve()))

    def test_git_command_usa_servidor_oficial_con_uvx(self) -> None:
        self.assertEqual(git_command(), ["uvx", GIT_SERVER_PACKAGE])


if __name__ == "__main__":
    unittest.main()