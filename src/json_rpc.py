"""Construcción y validación manual de mensajes JSON-RPC 2.0."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


JSONRPC_VERSION = "2.0"
_UNSET = object()


class JsonRpcValidationError(ValueError):
    """Indica que un mensaje no cumple las reglas básicas de JSON-RPC 2.0."""


def build_request(
    request_id: str | int | None,
    method: str,
    params: Any = _UNSET,
) -> dict[str, Any]:
    """Construye una solicitud JSON-RPC con identificador."""
    request = {"jsonrpc": JSONRPC_VERSION, "id": request_id, "method": method}
    if params is not _UNSET:
        request["params"] = params
    validate_request(request)
    return request


def build_result_response(request_id: str | int | None, result: Any) -> dict[str, Any]:
    """Construye una respuesta exitosa asociada a una solicitud."""
    response = {"jsonrpc": JSONRPC_VERSION, "id": request_id, "result": result}
    validate_response(response)
    return response


def build_error_response(
    request_id: str | int | None,
    code: int,
    message: str,
    data: Any = _UNSET,
) -> dict[str, Any]:
    """Construye una respuesta de error asociada a una solicitud."""
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not _UNSET:
        error["data"] = data

    response = {"jsonrpc": JSONRPC_VERSION, "id": request_id, "error": error}
    validate_response(response)
    return response


def build_notification(method: str, params: Any = _UNSET) -> dict[str, Any]:
    """Construye una notificación, que no contiene identificador."""
    notification = {"jsonrpc": JSONRPC_VERSION, "method": method}
    if params is not _UNSET:
        notification["params"] = params
    validate_notification(notification)
    return notification


def validate_request(message: Mapping[str, Any]) -> None:
    """Valida los campos básicos de una solicitud JSON-RPC."""
    _validate_object(message)
    _validate_version(message)
    _validate_id(message, required=True)
    _validate_method(message)
    _validate_params(message)


def validate_response(message: Mapping[str, Any]) -> None:
    """Valida los campos básicos de una respuesta JSON-RPC."""
    _validate_object(message)
    _validate_version(message)
    _validate_id(message, required=True)

    has_result = "result" in message
    has_error = "error" in message
    if has_result == has_error:
        raise JsonRpcValidationError(
            "Una respuesta debe contener exactamente uno de result o error."
        )

    if has_error:
        _validate_error(message["error"])


def validate_notification(message: Mapping[str, Any]) -> None:
    """Valida los campos básicos de una notificación JSON-RPC."""
    _validate_object(message)
    _validate_version(message)
    if "id" in message:
        raise JsonRpcValidationError("Una notificación no debe contener id.")
    _validate_method(message)
    _validate_params(message)


def validate_message(message: Mapping[str, Any]) -> None:
    """Valida una solicitud, respuesta o notificación según sus campos."""
    _validate_object(message)
    if "method" in message:
        if "id" in message:
            validate_request(message)
        else:
            validate_notification(message)
        return
    validate_response(message)


def response_matches_request(
    request: Mapping[str, Any], response: Mapping[str, Any]
) -> bool:
    """Comprueba que una respuesta corresponde a una solicitud por medio de id."""
    validate_request(request)
    validate_response(response)
    return request["id"] == response["id"]


def _validate_object(message: Mapping[str, Any]) -> None:
    if not isinstance(message, Mapping):
        raise JsonRpcValidationError("El mensaje debe ser un objeto JSON.")


def _validate_version(message: Mapping[str, Any]) -> None:
    if message.get("jsonrpc") != JSONRPC_VERSION:
        raise JsonRpcValidationError('El campo jsonrpc debe ser "2.0".')


def _validate_id(message: Mapping[str, Any], required: bool) -> None:
    if required and "id" not in message:
        raise JsonRpcValidationError("Falta el campo id.")
    if "id" in message and not _is_valid_id(message["id"]):
        raise JsonRpcValidationError("id debe ser una cadena, un número o null.")


def _is_valid_id(value: Any) -> bool:
    return value is None or (isinstance(value, (str, int)) and not isinstance(value, bool))


def _validate_method(message: Mapping[str, Any]) -> None:
    method = message.get("method")
    if not isinstance(method, str) or not method:
        raise JsonRpcValidationError("Falta el campo method o no es válido.")


def _validate_params(message: Mapping[str, Any]) -> None:
    if "params" in message and not isinstance(message["params"], (Mapping, list)):
        raise JsonRpcValidationError("params debe ser un objeto o un arreglo.")


def _validate_error(error: Any) -> None:
    if not isinstance(error, Mapping):
        raise JsonRpcValidationError("error debe ser un objeto.")
    if not isinstance(error.get("code"), int) or isinstance(error.get("code"), bool):
        raise JsonRpcValidationError("error.code debe ser un número entero.")
    if not isinstance(error.get("message"), str) or not error["message"]:
        raise JsonRpcValidationError("error.message debe ser texto no vacío.")