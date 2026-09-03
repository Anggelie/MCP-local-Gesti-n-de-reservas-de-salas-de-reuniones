"""Punto de entrada del chatbot de terminal."""

from .config import APPLICATION_NAME, EXIT_COMMAND
from .conversation import ConversationHistory
from .logger import configure_logging


def generate_response(message: str) -> str:
    """Genera una respuesta temporal hasta integrar una API de LLM."""
    return f"Recibí tu mensaje: {message}"


def run() -> None:
    logger = configure_logging()
    history = ConversationHistory()

    print(f"{APPLICATION_NAME}")
    print(f"Escribe '{EXIT_COMMAND}' para terminar.")

    while True:
        try:
            message = input("Tú: ").strip()
        except EOFError:
            print()
            logger.info("La sesión terminó por fin de entrada")
            break

        if not message:
            continue

        if message.casefold() == EXIT_COMMAND:
            logger.info("La sesión terminó por solicitud del usuario")
            print("Chatbot: Hasta luego.")
            break

        history.add_user(message)
        response = generate_response(message)
        history.add_assistant(response)
        logger.info("Mensaje procesado; historial actual: %d mensajes", len(history))
        print(f"Chatbot: {response}")


if __name__ == "__main__":
    run()
