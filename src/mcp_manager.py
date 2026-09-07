"""Coordinador minimo para varios clientes MCP independientes."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .mcp_client import McpClient, McpClientError


class McpManagerError(RuntimeError):
    """Error de registro o routing entre servidores MCP."""


class McpManager:
    """Mantiene clientes MCP por nombre y enruta tools con prefijo de servidor."""

    def __init__(self) -> None:
        self._clients: dict[str, McpClient] = {}
        self._tools: dict[str, dict[str, str]] = {}

    def register(self, server_name: str, client: McpClient) -> None:
        if not server_name or "." in server_name:
            raise McpManagerError("El nombre del servidor debe ser simple y no vacio.")
        if server_name in self._clients:
            raise McpManagerError(f"Ya existe un cliente para '{server_name}'.")
        self._clients[server_name] = client

    def initialize_all(self) -> dict[str, dict[str, Any]]:
        return {name: client.initialize() for name, client in self._clients.items()}

    def list_tools(self) -> dict[str, list[dict[str, Any]]]:
        tools_by_server: dict[str, list[dict[str, Any]]] = {}
        self._tools.clear()
        for server_name, client in self._clients.items():
            tools = client.list_tools()
            tools_by_server[server_name] = tools
            for tool in tools:
                tool_name = tool.get("name")
                if isinstance(tool_name, str):
                    self._tools[f"{server_name}.{tool_name}"] = {
                        "server": server_name,
                        "tool": tool_name,
                    }
        return tools_by_server

    def call_tool(self, qualified_name: str, arguments: Mapping[str, Any]) -> dict[str, Any]:
        route = self._tools.get(qualified_name)
        if route is None:
            raise McpManagerError(f"No existe la herramienta '{qualified_name}'.")
        return self._clients[route["server"]].call_tool(route["tool"], arguments)

    def close(self) -> None:
        errors: list[str] = []
        for server_name, client in self._clients.items():
            try:
                client.close()
            except McpClientError as error:
                errors.append(f"{server_name}: {error}")
        if errors:
            raise McpManagerError("; ".join(errors))

    def __enter__(self) -> "McpManager":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
