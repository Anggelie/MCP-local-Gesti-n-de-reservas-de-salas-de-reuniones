"""Estructuras para conservar el historial de conversación."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Message:
    """Representa un mensaje intercambiado durante la sesión."""

    role: str
    content: str


class ConversationHistory:
    """Almacena los mensajes de una sesión en memoria."""

    def __init__(self) -> None:
        self._messages: list[Message] = []

    def add(self, role: str, content: str) -> None:
        self._messages.append(Message(role=role, content=content))

    def add_user(self, content: str) -> None:
        self.add("user", content)

    def add_assistant(self, content: str) -> None:
        self.add("assistant", content)

    def as_dicts(self) -> list[dict[str, str]]:
        return [asdict(message) for message in self._messages]

    def __len__(self) -> int:
        return len(self._messages)
