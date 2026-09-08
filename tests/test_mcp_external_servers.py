"""Pruebas unitarias de la configuración de servidores MCP externos."""

import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from src.mcp_external_servers import (
    FILESYSTEM_SERVER_PACKAGE,
    GIT_SERVER_PACKAGE,
    filesystem_command,
    git_command,
    create_configured_reservations_client,
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

    @patch("src.mcp_external_servers.create_reservations_client")
    def test_modo_local_usa_factory_local(self, create_local) -> None:
        create_local.return_value = "local-client"

        result = create_configured_reservations_client(mode="local")

        self.assertEqual(result, "local-client")
        create_local.assert_called_once()

    @patch("src.mcp_external_servers.create_remote_reservations_client")
    def test_modo_remoto_usa_factory_remota(self, create_remote) -> None:
        create_remote.return_value = "remote-client"

        result = create_configured_reservations_client(mode="remote")

        self.assertEqual(result, "remote-client")
        create_remote.assert_called_once()

    def test_modo_invalido_falla_claramente(self) -> None:
        with self.assertRaisesRegex(ValueError, "MCP_RESERVATIONS_MODE inválido"):
            create_configured_reservations_client(mode="cloud")

    @patch("src.mcp_external_servers.McpClient")
    @patch("src.mcp_external_servers.HttpTransport")
    def test_url_remota_usa_mcp_reservations_url(self, http_transport, mcp_client) -> None:
        with patch.dict("os.environ", {"MCP_RESERVATIONS_URL": "https://example.test/mcp"}):
            create_configured_reservations_client(mode="remote")

        http_transport.assert_called_once_with("https://example.test/mcp", timeout=10.0)
        mcp_client.assert_called_once()


if __name__ == "__main__":
    unittest.main()