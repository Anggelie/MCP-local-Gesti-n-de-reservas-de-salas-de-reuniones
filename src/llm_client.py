"""Cliente modular para comunicarse con la API de Anthropic."""

import anthropic

from .config import get_anthropic_api_key, get_anthropic_model


class ClaudeClient:
    """Encapsula las solicitudes de conversación a Claude."""

    def __init__(self) -> None:
        self._model = get_anthropic_model()
        self._client = anthropic.Anthropic(api_key=get_anthropic_api_key())

    def generate_response(self, messages: list[dict[str, str]]) -> str:
        """Envía el historial a Claude y devuelve el texto de su respuesta."""
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                messages=messages,
            )
        except anthropic.APIError as error:
            raise RuntimeError(
                f"No fue posible obtener una respuesta de Claude: {error}"
            ) from error

        text_blocks = [block.text for block in response.content if block.type == "text"]
        if not text_blocks:
            raise RuntimeError("Claude devolvió una respuesta sin contenido de texto.")
        return "".join(text_blocks)