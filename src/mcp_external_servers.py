"""Configuración mínima para servidores MCP externos ejecutados por stdio."""

from __future__ import annotations

import sys
import os
from pathlib import Path

from .config import DEFAULT_RESERVATIONS_URL, MCP_LOG_FILE, PROJECT_ROOT
from .mcp_client import McpClient
from .mcp_interaction_logger import McpInteractionLogger
from .mcp_http_transport import HttpTransport
from .mcp_transport import StdioTransport


FILESYSTEM_SERVER_PACKAGE = "@modelcontextprotocol/server-filesystem"
GIT_SERVER_PACKAGE = "mcp-server-git"


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
    return McpClient(transport, McpInteractionLogger(log_file, "filesystem"))


def git_command() -> list[str]:
    """Construye el comando del servidor oficial Git MCP para uvx."""
    return ["uvx", GIT_SERVER_PACKAGE]


def create_git_client(
    log_file: Path = MCP_LOG_FILE,
) -> McpClient:
    """Crea un cliente manual conectado al servidor oficial Git MCP."""
    transport = StdioTransport(command=git_command(), working_directory=PROJECT_ROOT)
    return McpClient(transport, McpInteractionLogger(log_file, "git"))


def create_reservations_client(log_file: Path = MCP_LOG_FILE) -> McpClient:
    """Crea un cliente para el servidor local de reservas."""
    transport = StdioTransport(
        command=[sys.executable, "-m", "src.mcp_server"],
        working_directory=PROJECT_ROOT,
    )
    return McpClient(transport, McpInteractionLogger(log_file, "reservations"))


def create_remote_reservations_client(
    url: str | None = None,
    log_file: Path = MCP_LOG_FILE,
    timeout: float = 10.0,
) -> McpClient:
    """Crea un cliente manual para el mismo MCP mediante HTTP."""
    remote_url = url or os.getenv("MCP_RESERVATIONS_URL", DEFAULT_RESERVATIONS_URL)
    return McpClient(
        HttpTransport(remote_url, timeout=timeout),
        McpInteractionLogger(log_file, "reservations_remote"),
    )