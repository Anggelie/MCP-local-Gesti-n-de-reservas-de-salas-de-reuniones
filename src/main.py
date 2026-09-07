"""Punto de entrada del chatbot de terminal."""

from .chatbot_host import ChatbotHost
from .config import APPLICATION_NAME, CLEAR_COMMAND, EXIT_COMMAND, PROJECT_ROOT
from .mcp_external_servers import (
    create_filesystem_client,
    create_git_client,
    create_reservations_client,
)
from .llm_client import ClaudeClient
from .logger import configure_logging
from .mcp_manager import McpManager


def run() -> None:
    logger = configure_logging()

    try:
        claude = ClaudeClient()
    except ValueError as error:
        logger.error("Configuración inválida: %s", error)
        print(f"Error de configuración: {error}")
        return

    manager = McpManager()
    try:
        workspace = PROJECT_ROOT / "sandbox" / "chatbot_workspace"
        manager.register("reservations", create_reservations_client())
        manager.register("filesystem", create_filesystem_client(workspace))
        manager.register("git", create_git_client())
        manager.initialize_all()
        host = ChatbotHost(claude, manager)
        host.initialize()
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
    except RuntimeError as error:
        logger.error("No fue posible iniciar MCP: %s", error)
        print(f"Error al iniciar MCP: {error}")
    finally:
        manager.close()


if __name__ == "__main__":
    run()
