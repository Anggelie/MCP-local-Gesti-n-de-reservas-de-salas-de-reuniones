"""Orquestación entre el chatbot, Claude y el cliente MCP."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any

from .conversation import ConversationHistory
from .llm_client import ClaudeClient
from .mcp_client import McpToolError
from .mcp_manager import McpManager


class ChatbotHost:
    """Decide cuándo usar una herramienta y devuelve respuestas naturales."""

    def __init__(
        self,
        claude: ClaudeClient,
        mcp_manager: McpManager,
        history: ConversationHistory | None = None,
    ) -> None:
        self._claude = claude
        self._mcp_manager = mcp_manager
        self._history = history or ConversationHistory()
        self._llm_tools: list[dict[str, Any]] = []

    def initialize(self) -> None:
        """Prepara el catálogo de tools de un manager ya inicializado."""
        self._llm_tools = [
            self._to_llm_tool(tool) for tool in self._mcp_manager.tool_catalog()
        ]

    def respond(self, user_message: str) -> str:
        """Procesa un mensaje y ejecuta como máximo cuatro rondas de tool use."""
        self._history.add_user(user_message)

        for _ in range(4):
            content = self._claude.generate_content(
                self._history.messages(), self._llm_tools
            )
            self._history.add_assistant(content)
            tool_uses = [block for block in content if block.get("type") == "tool_use"]
            if not tool_uses:
                return self._text_from_content(content)

            tool_results = [self._execute_tool(tool_use) for tool_use in tool_uses]
            self._history.add_user(tool_results)

        raise RuntimeError("Claude superó el máximo de rondas de herramientas permitidas.")

    def clear_context(self) -> None:
        """Reinicia el contexto conversacional de la sesión actual."""
        self._history.clear()

    def _execute_tool(self, tool_use: Mapping[str, Any]) -> dict[str, Any]:
        tool_use_id = tool_use.get("id")
        name = tool_use.get("name")
        arguments = tool_use.get("input", {})
        try:
            route = self._mcp_manager.resolve_llm_tool(name)
            result = self._mcp_manager.call_tool(route, arguments)
            return {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": json.dumps(result, ensure_ascii=False),
            }
        except McpToolError as error:
            return {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": str(error),
                "is_error": True,
            }

    @staticmethod
    def _to_llm_tool(tool: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "name": tool["llm_name"],
            "description": tool.get("description", ""),
            "input_schema": tool.get("inputSchema", {"type": "object"}),
        }

    @staticmethod
    def _sanitize_text(text: str) -> str:
        return re.sub(
            r"[\U0001F300-\U0001FAFF\U00002600-\U000026FF\U00002700-\U000027BF\u200d\ufe0f]",
            "",
            text,
        )

    @staticmethod
    def _text_from_content(content: list[Mapping[str, Any]]) -> str:
        text = "".join(
            str(block.get("text", ""))
            for block in content
            if block.get("type") == "text"
        )
        if not text:
            raise RuntimeError("Claude no devolvió texto después de procesar la solicitud.")
        return ChatbotHost._sanitize_text(text).strip()