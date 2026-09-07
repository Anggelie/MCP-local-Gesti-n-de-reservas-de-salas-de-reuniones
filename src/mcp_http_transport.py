"""Transporte HTTP manual para McpClient."""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from typing import Any


class HttpTransportError(RuntimeError):
    """Error controlado del transporte HTTP MCP."""


class HttpTransport:
    """Envía cada mensaje JSON-RPC mediante POST y guarda su respuesta."""

    def __init__(self, url: str, timeout: float = 10.0) -> None:
        self._url = url
        self._timeout = timeout
        self._pending_response: dict[str, Any] | None = None
        self._closed = False

    def send(self, message: dict[str, Any]) -> None:
        if self._closed:
            raise HttpTransportError("El transporte HTTP ya está cerrado.")
        payload = json.dumps(message, ensure_ascii=True).encode("utf-8")
        request = Request(self._url, data=payload, headers={"Content-Type": "application/json", "Accept": "application/json"}, method="POST")
        try:
            with urlopen(request, timeout=self._timeout) as response:
                status = response.status
                body = response.read()
        except HTTPError as error:
            error.close()
            raise HttpTransportError(f"El servidor MCP devolvió HTTP {error.code}.") from error
        except (URLError, TimeoutError, OSError) as error:
            raise HttpTransportError(f"No se pudo conectar con el servidor MCP HTTP: {error}") from error
        if status < 200 or status >= 300:
            raise HttpTransportError(f"El servidor MCP devolvió HTTP {status}.")
        if not message.get("method") or "id" not in message:
            self._pending_response = None
            return
        try:
            parsed = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise HttpTransportError("El servidor HTTP devolvió una respuesta JSON inválida.") from error
        if not isinstance(parsed, dict):
            raise HttpTransportError("El servidor HTTP no devolvió un objeto JSON.")
        self._pending_response = parsed

    def receive(self) -> dict[str, Any]:
        if self._pending_response is None:
            raise HttpTransportError("No hay una respuesta HTTP pendiente.")
        response = self._pending_response
        self._pending_response = None
        return response

    def close(self) -> None:
        self._closed = True
        self._pending_response = None
