"""Cliente modular para comunicarse con la API de Anthropic."""

import anthropic
from typing import Any

from .config import get_anthropic_api_key, get_anthropic_model


class ClaudeClient:
    """Encapsula las solicitudes de conversación a Claude."""

    def __init__(self) -> None:
        self._model = get_anthropic_model()
        self._client = anthropic.Anthropic(api_key=get_anthropic_api_key())

    def generate_response(self, messages: list[dict[str, str]]) -> str:
        """Envía el historial a Claude y devuelve una respuesta de texto."""
        content = self.generate_content(messages)
        text = [block["text"] for block in content if block.get("type") == "text"]
        if not text:
            raise RuntimeError("Claude devolvió una respuesta sin contenido de texto.")
        return "".join(text)

    def generate_content(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Solicita contenido a Claude, incluyendo tools cuando están disponibles."""
        request: dict[str, Any] = {
            "model": self._model,
            "max_tokens": 1024,
            "messages": messages,
        }
        if tools:
            request["tools"] = tools

        try:
            response = self._client.messages.create(**request)
        except anthropic.APIError as error:
            raise RuntimeError(
                f"No fue posible obtener una respuesta de Claude: {error}"
            ) from error

        return [self._block_to_dict(block) for block in response.content]

    @staticmethod
    def _block_to_dict(block: Any) -> dict[str, Any]:
        if isinstance(block, dict):
            return block
        if hasattr(block, "model_dump"):
            return block.model_dump(exclude_none=True)
        result: dict[str, Any] = {"type": block.type}
        for field in ("text", "id", "name", "input"):
            if hasattr(block, field):
                result[field] = getattr(block, field)
        return result