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

    def messages(self) -> list[dict[str, str]]:
        """Devuelve una copia del historial con el formato esperado por el LLM."""
        return self.as_dicts()

    def remove_last(self) -> None:
        """Retira el último mensaje cuando una solicitud no pudo completarse."""
        if self._messages:
            self._messages.pop()

    def __len__(self) -> int:
        return len(self._messages)
