"""Transporte local de mensajes JSON-RPC mediante stdin y stdout."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from .config import PROJECT_ROOT


class McpTransportError(RuntimeError):
    """Error de comunicación con el proceso del servidor MCP."""


class StdioTransport:
    """Ejecuta un servidor MCP local y transporta un mensaje JSON por línea."""

    def __init__(
        self,
        command: list[str] | None = None,
        working_directory: Path = PROJECT_ROOT,
    ) -> None:
        self._command = command or [sys.executable, "-m", "src.mcp_server"]
        self._process = subprocess.Popen(
            self._command,
            cwd=working_directory,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=sys.stderr,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )

    def send(self, message: dict[str, Any]) -> None:
        """Serializa y envía un mensaje al servidor."""
        if self._process.stdin is None:
            raise McpTransportError("El canal de entrada del servidor no está disponible.")
        try:
            self._process.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
            self._process.stdin.flush()
        except OSError as error:
            raise McpTransportError(f"No se pudo enviar el mensaje MCP: {error}") from error

    def receive(self) -> dict[str, Any]:
        """Lee y analiza una respuesta JSON del servidor."""
        if self._process.stdout is None:
            raise McpTransportError("El canal de salida del servidor no está disponible.")
        line = self._process.stdout.readline()
        if not line:
            raise McpTransportError("El servidor MCP cerró la comunicación inesperadamente.")
        try:
            message = json.loads(line)
        except json.JSONDecodeError as error:
            raise McpTransportError(f"El servidor devolvió JSON inválido: {error.msg}") from error
        if not isinstance(message, dict):
            raise McpTransportError("El servidor MCP no devolvió un objeto JSON.")
        return message

    def close(self) -> None:
        """Cierra los canales y termina el proceso local del servidor."""
        if self._process.stdin is not None and not self._process.stdin.closed:
            self._process.stdin.close()
        if self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait()

    def __enter__(self) -> "StdioTransport":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()