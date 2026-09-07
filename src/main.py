"""Punto de entrada del chatbot de terminal."""

from .chatbot_host import ChatbotHost
from .config import APPLICATION_NAME, CLEAR_COMMAND, EXIT_COMMAND
from .llm_client import ClaudeClient
from .logger import configure_logging
from .mcp_client import McpClient


def run() -> None:
    logger = configure_logging()

    try:
        claude = ClaudeClient()
    except ValueError as error:
        logger.error("Configuración inválida: %s", error)
        print(f"Error de configuración: {error}")
        return

    mcp_client = McpClient()
    host = ChatbotHost(claude, mcp_client)
    try:
        host.initialize()
    except RuntimeError as error:
        logger.error("No fue posible inicializar MCP: %s", error)
        print(f"Error al inicializar MCP: {error}")
        mcp_client.close()
        return

    print(f"{APPLICATION_NAME}")
    print(f"Escribe '{EXIT_COMMAND}' para terminar.")
    print(f"Escribe '{CLEAR_COMMAND}' para reiniciar el contexto.")

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

        if message.casefold() == CLEAR_COMMAND:
            host.clear_context()
            logger.info("El contexto de conversación fue reiniciado")
            print("Chatbot: El contexto de esta sesión fue reiniciado.")
            continue

        try:
            response = host.respond(message)
        except RuntimeError as error:
            logger.error("Error al consultar Claude: %s", error)
            print(f"Error al consultar Claude: {error}")
            continue

        logger.info("Mensaje procesado por el host")
        print(f"Chatbot: {response}")

    mcp_client.close()


if __name__ == "__main__":
    run()
