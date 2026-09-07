"""Logica MCP comun, independiente del transporte."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from .config import RESERVATIONS_FILE, ROOMS_FILE
from .json_rpc import JsonRpcValidationError, build_error_response, build_result_response, validate_message
from .reservation_service import ReservationError, ReservationService

MCP_PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "meeting-room-reservations"
SERVER_VERSION = "1.0.0"


class McpProtocolHandler:
    """Procesa mensajes MCP ya convertidos a objetos Python."""

    def __init__(self, service: ReservationService | None = None) -> None:
        self._service = service or ReservationService(ROOMS_FILE, RESERVATIONS_FILE)
        self._initialized = False

    def handle_message(self, message: Mapping[str, Any]) -> dict[str, Any] | None:
        request_id = message.get("id") if isinstance(message, Mapping) else None
        try:
            validate_message(message)
        except JsonRpcValidationError as error:
            if not isinstance(message, Mapping) or "id" not in message:
                return None
            return build_error_response(request_id, -32600, str(error))

        method = message.get("method")
        if method == "notifications/initialized":
            self._initialized = True
            return None
        if method == "initialize":
            self._initialized = True
            return build_result_response(request_id, self._initialize_result())
        if not self._initialized:
            return build_error_response(request_id, -32002, "El servidor no está inicializado.")
        if method == "tools/list":
            return build_result_response(request_id, {"tools": self._tool_definitions()})
        if method == "tools/call":
            return self._handle_tool_call(request_id, message.get("params"))
        return build_error_response(request_id, -32601, f"Método no encontrado: {method}")

    def _handle_tool_call(self, request_id: Any, params: Any) -> dict[str, Any]:
        if not isinstance(params, Mapping):
            return build_error_response(request_id, -32602, "tools/call requiere params como objeto.")
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        if not isinstance(tool_name, str) or not isinstance(arguments, Mapping):
            return build_error_response(request_id, -32602, "tools/call requiere name y arguments válidos.")
        try:
            result = self._call_tool(tool_name, arguments)
        except ReservationError as error:
            return build_result_response(request_id, self._tool_error(str(error)))
        return build_result_response(request_id, self._tool_success(result))

    def _call_tool(self, tool_name: str, arguments: Mapping[str, Any]) -> Any:
        if tool_name == "list_rooms":
            return self._service.list_rooms()
        if tool_name == "check_availability":
            return self._service.check_availability(**self._required_arguments(arguments, "room_id", "date", "start_time", "end_time"))
        if tool_name == "create_reservation":
            return self._service.create_reservation(**self._required_arguments(arguments, "room_id", "date", "start_time", "end_time", "reserved_by", "title"))
        if tool_name == "cancel_reservation":
            values = self._required_arguments(arguments, "reservation_id")
            return self._service.cancel_reservation(values["reservation_id"])
        if tool_name == "list_reservations":
            allowed = {key: arguments[key] for key in ("date", "room_id") if key in arguments}
            return self._service.list_reservations(**allowed)
        raise ReservationError(f"Herramienta no encontrada: {tool_name}")

    @staticmethod
    def _required_arguments(arguments: Mapping[str, Any], *names: str) -> dict[str, Any]:
        missing = [name for name in names if name not in arguments]
        if missing:
            raise ReservationError(f"Faltan parámetros requeridos: {', '.join(missing)}.")
        return {name: arguments[name] for name in names}

    @staticmethod
    def _tool_success(result: Any) -> dict[str, Any]:
        return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}

    @staticmethod
    def _tool_error(message: str) -> dict[str, Any]:
        return {"content": [{"type": "text", "text": message}], "isError": True}

    @staticmethod
    def _initialize_result() -> dict[str, Any]:
        return {"protocolVersion": MCP_PROTOCOL_VERSION, "capabilities": {"tools": {}}, "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION}}

    @staticmethod
    def _tool_definitions() -> list[dict[str, Any]]:
        return [
            {"name": "list_rooms", "description": "Lista las salas de reuniones y sus características.", "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
            {"name": "check_availability", "description": "Comprueba si una sala está disponible en un intervalo.", "inputSchema": {"type": "object", "properties": _interval_properties(), "required": ["room_id", "date", "start_time", "end_time"]}},
            {"name": "create_reservation", "description": "Crea una reserva para una sala de reuniones.", "inputSchema": {"type": "object", "properties": {**_interval_properties(), "reserved_by": {"type": "string"}, "title": {"type": "string"}}, "required": ["room_id", "date", "start_time", "end_time", "reserved_by", "title"]}},
            {"name": "cancel_reservation", "description": "Cancela una reserva existente.", "inputSchema": {"type": "object", "properties": {"reservation_id": {"type": "string"}}, "required": ["reservation_id"]}},
            {"name": "list_reservations", "description": "Lista reservas con filtros opcionales por fecha o sala.", "inputSchema": {"type": "object", "properties": {"date": {"type": "string"}, "room_id": {"type": "string"}}, "additionalProperties": False}},
        ]


def _interval_properties() -> dict[str, dict[str, str]]:
    return {"room_id": {"type": "string"}, "date": {"type": "string", "description": "Formato YYYY-MM-DD"}, "start_time": {"type": "string", "description": "Formato HH:MM"}, "end_time": {"type": "string", "description": "Formato HH:MM"}}
