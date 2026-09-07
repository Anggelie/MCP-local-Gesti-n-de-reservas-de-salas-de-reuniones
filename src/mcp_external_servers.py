"""Configuración mínima para servidores MCP externos ejecutados por stdio."""

from __future__ import annotations

from pathlib import Path

from .config import MCP_LOG_FILE, PROJECT_ROOT
from .mcp_client import McpClient
from .mcp_interaction_logger import McpInteractionLogger
from .mcp_transport import StdioTransport


FILESYSTEM_SERVER_PACKAGE = "@modelcontextprotocol/server-filesystem"


def filesystem_command(allowed_directory: Path | str) -> list[str]:
    """Construye el comando de Windows para el servidor oficial Filesystem MCP."""
    return [
        "cmd",
        "/c",
        "npx",
        "-y",
        FILESYSTEM_SERVER_PACKAGE,
        str(Path(allowed_directory).resolve()),
    ]


def create_filesystem_client(
    allowed_directory: Path | str,
    log_file: Path = MCP_LOG_FILE,
) -> McpClient:
    """Crea un cliente manual conectado al servidor oficial Filesystem MCP."""
    transport = StdioTransport(
        command=filesystem_command(allowed_directory),
        working_directory=PROJECT_ROOT,
    )
    return McpClient(transport, McpInteractionLogger(log_file))