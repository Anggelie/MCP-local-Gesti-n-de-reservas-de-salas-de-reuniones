"""Pruebas unitarias del módulo JSON-RPC manual."""

import unittest

from src.json_rpc import (
    JsonRpcValidationError,
    build_error_response,
    build_notification,
    build_request,
    build_result_response,
    response_matches_request,
    validate_request,
    validate_response,
)


class JsonRpcTests(unittest.TestCase):
    def test_request_valido(self) -> None:
        request = build_request(1, "tools/list", {"cursor": None})

        self.assertEqual(request["jsonrpc"], "2.0")
        self.assertEqual(request["id"], 1)
        self.assertEqual(request["method"], "tools/list")
        self.assertEqual(request["params"], {"cursor": None})

    def test_response_valido(self) -> None:
        response = build_result_response(1, {"tools": []})

        validate_response(response)
        self.assertEqual(response["result"], {"tools": []})
        self.assertNotIn("error", response)

    def test_error_valido(self) -> None:
        response = build_error_response(1, -32601, "Método no encontrado")

        validate_response(response)
        self.assertEqual(response["error"]["code"], -32601)
        self.assertEqual(response["error"]["message"], "Método no encontrado")

    def test_version_incorrecta(self) -> None:
        with self.assertRaises(JsonRpcValidationError):
            validate_request({"jsonrpc": "1.0", "id": 1, "method": "ping"})

    def test_request_sin_method(self) -> None:
        with self.assertRaises(JsonRpcValidationError):
            validate_request({"jsonrpc": "2.0", "id": 1})

    def test_correlacion_por_id(self) -> None:
        request = build_request("abc-123", "ping")
        matching_response = build_result_response("abc-123", "pong")
        different_response = build_result_response("other-id", "pong")

        self.assertTrue(response_matches_request(request, matching_response))
        self.assertFalse(response_matches_request(request, different_response))

    def test_notificacion_sin_id(self) -> None:
        notification = build_notification("notifications/updated", [])

        self.assertNotIn("id", notification)


if __name__ == "__main__":
    unittest.main()