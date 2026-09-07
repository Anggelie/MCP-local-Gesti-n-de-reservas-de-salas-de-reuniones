"""Pruebas de HOST y PORT para ejecución local y Render."""

import os
import unittest
from unittest.mock import patch

from src.mcp_http_server import get_http_address


class HttpConfigTests(unittest.TestCase):
    def test_defaults_locales(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(get_http_address(), ("127.0.0.1", 8000))

    def test_usa_host_y_port_del_entorno(self) -> None:
        with patch.dict(os.environ, {"HOST": "0.0.0.0", "PORT": "8765"}, clear=True):
            self.assertEqual(get_http_address(), ("0.0.0.0", 8765))


if __name__ == "__main__":
    unittest.main()