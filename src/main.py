"""Punto de entrada del chatbot de terminal."""

from .config import APPLICATION_NAME, EXIT_COMMAND
from .conversation import ConversationHistory
from .llm_client import ClaudeClient
from .logger import configure_logging


def run() -> None:
    logger = configure_logging()
    history = ConversationHistory()

    try:
        claude = ClaudeClient()
    except ValueError as error:
        logger.error("Configuración inválida: %s", error)
        print(f"Error de configuración: {error}")
        return

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
        try:
            response = claude.generate_response(history.messages())
        except RuntimeError as error:
            history.remove_last()
            logger.error("Error al consultar Claude: %s", error)
            print(f"Error al consultar Claude: {error}")
            continue

        history.add_assistant(response)
        logger.info("Mensaje procesado; historial actual: %d mensajes", len(history))
        print(f"Chatbot: {response}")


if __name__ == "__main__":
    run()
