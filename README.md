# Chatbot MCP para gestión de reservas de salas de reuniones

Proyecto 1 del curso Redes CC3067 de la Universidad del Valle de Guatemala.

## Fase 1

Esta fase contiene la estructura base de un chatbot ejecutable desde terminal.
Permite escribir mensajes, conservar el historial de la sesión en memoria y
registrar eventos en consola y en `logs/chatbot.log`.

La respuesta actual es local y temporal. La conexión con un LLM, la
implementación manual de MCP/JSON-RPC y el servidor de reservas se agregarán en
fases posteriores.

## Restricciones

- Python como lenguaje de implementación.
- No se utiliza FastMCP ni ningún SDK de MCP.
- Esta fase no implementa servidores MCP ni conexión con la nube.
- Esta fase no requiere dependencias externas.

## Requisitos

- Python 3.10 o superior.

## Ejecución

Desde la raíz del repositorio:

```bash
python -m src.main
```

Escribe mensajes en la terminal. Para terminar la sesión, escribe:

```text
salir
```

## Estructura

```text
src/
|-- config.py        # Configuración y rutas de la aplicación
|-- conversation.py  # Historial de mensajes en memoria
|-- logger.py        # Registro en consola y archivo
|-- main.py          # Punto de entrada del chatbot
```
