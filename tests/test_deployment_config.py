"""Pruebas de configuración para ejecución local y Render."""

import importlib
import os
import unittest
from pathlib import Path
from unittest.mock import patch

import src.config as config


class DeploymentConfigTests(unittest.TestCase):
    def test_data_directory_usa_valor_local_por_defecto(self) -> None:
        with patch.dict(os.environ, {"MCP_DATA_DIR": ""}, clear=False):
            importlib.reload(config)
            self.assertTrue(str(config.DATA_DIRECTORY).endswith(os.path.join("data")))

    def test_data_directory_acepta_variable_de_entorno(self) -> None:
        with patch.dict(os.environ, {"MCP_DATA_DIR": "C:/render-data"}, clear=False):
            importlib.reload(config)
            self.assertEqual(Path(config.DATA_DIRECTORY), Path("C:/render-data"))
        importlib.reload(config)


if __name__ == "__main__":
    unittest.main()
