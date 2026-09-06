"""Cliente MCP manual para el servidor local de reservas."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .config import MCP_LOG_FILE
from .json_rpc import (
    build_notification,
    build_request,
    response_matches_request,
    validate_response,
)
from .mcp_interaction_logger import McpInteractionLogger
from .mcp_transport import StdioTransport


class McpClientError(RuntimeError):
    """Error general del cliente MCP."""


class McpProtocolError(McpClientError):
    """Error JSON-RPC devuelto por el servidor MCP."""


class McpToolError(McpClientError):
    """Error de ejecución de una herramienta MCP."""


class McpClient:
    """Gestiona el ciclo de vida MCP y las llamadas a herramientas."""

    def __init__(
        self,
        transport: StdioTransport | Any | None = None,
        interaction_logger: McpInteractionLogger | None = None,
    ) -> None:
        self._transport = transport or StdioTransport()
        self._logger = interaction_logger or McpInteractionLogger(MCP_LOG_FILE)
        self._next_id = 1
        self._initialized = False
        self._closed = False

    def initialize(self) -> dict[str, Any]:
        """Ejecuta initialize y la notificación initialized del ciclo MCP."""
        result = self._request("initialize", {})
        self._notify("notifications/initialized")
        self._initialized = True
        return result

    def list_tools(self) -> list[dict[str, Any]]:
        """Descubre las herramientas publicadas por el servidor."""
        self._require_initialized()
        result = self._request("tools/list", {})
        tools = result.get("tools")
        if not isinstance(tools, list):
            raise McpClientError("La respuesta de tools/list no contiene una lista de tools.")
        return tools

    def call_tool(self, name: str, arguments: Mapping[str, Any]) -> dict[str, Any]:
        """Invoca una herramienta y devuelve su resultado MCP."""
        self._require_initialized()
        result = self._request("tools/call", {"name": name, "arguments": dict(arguments)})
        if result.get("isError"):
            message = self._extract_tool_error(result)
            raise McpToolError(message)
        return result

    def close(self) -> None:
        """Cierra el transporte una sola vez."""
        if not self._closed:
            self._transport.close()
            self._closed = True

    def _request(self, method: str, params: Mapping[str, Any]) -> dict[str, Any]:
        request = build_request(self._next_id, method, dict(params))
        self._next_id += 1
        self._send(request)
        response = self._receive()
        validate_response(response)
        if not response_matches_request(request, response):
            raise McpClientError(
                f"La respuesta de {method} tiene un id que no coincide con la solicitud."
            )
        if "error" in response:
            error = response["error"]
            raise McpProtocolError(f"Error JSON-RPC {error['code']}: {error['message']}")
        result = response.get("result")
        if not isinstance(result, dict):
            raise McpClientError(f"La respuesta de {method} no contiene un result válido.")
        return result

    def _notify(self, method: str) -> None:
        self._send(build_notification(method))

    def _send(self, message: dict[str, Any]) -> None:
        if self._closed:
            raise McpClientError("El cliente MCP ya está cerrado.")
        self._logger.log("CLIENT_TO_SERVER", message)
        self._transport.send(message)

    def _receive(self) -> dict[str, Any]:
        message = self._transport.receive()
        self._logger.log("SERVER_TO_CLIENT", message)
        return message

    def _require_initialized(self) -> None:
        if not self._initialized:
            raise McpClientError("El cliente MCP debe inicializarse antes de usar tools.")

    @staticmethod
    def _extract_tool_error(result: Mapping[str, Any]) -> str:
        content = result.get("content", [])
        if content and isinstance(content[0], Mapping):
            return str(content[0].get("text", "Error desconocido de la herramienta."))
        return "La herramienta MCP devolvió un error."

    def __enter__(self) -> "McpClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()