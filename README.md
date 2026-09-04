# Chatbot MCP para gestión de reservas de salas de reuniones

Proyecto 1 del curso Redes CC3067 de la Universidad del Valle de Guatemala.

## Fase 1: chatbot con Claude

Esta fase contiene un chatbot ejecutable desde terminal conectado a la API de
Anthropic Claude. Conserva el historial de la sesión en memoria y registra
eventos en consola y en `logs/chatbot.log`.

La implementación manual de MCP/JSON-RPC y el servidor de reservas se agregarán
en fases posteriores.

## Restricciones

- Python como lenguaje de implementación.
- No se utiliza FastMCP ni ningún SDK de MCP.
- Esta fase no implementa servidores MCP ni conexión MCP.
- La librería de Anthropic se utiliza únicamente para consumir el LLM.

## Requisitos

- Python 3.10 o superior.
- Una API key de Anthropic.

## Configuración

La API key nunca debe escribirse en el código ni confirmarse en Git. Puedes
copiar `.env.example` como referencia, pero el programa lee las variables del
entorno del proceso.

En PowerShell:

```powershell
$env:ANTHROPIC_API_KEY = "tu_clave_real_de_anthropic"
$env:ANTHROPIC_MODEL = "claude-3-5-haiku-latest"
```

La variable `ANTHROPIC_MODEL` es opcional. Si no se define, se utiliza
`claude-3-5-haiku-latest`.

## Ejecución

Desde la raíz del repositorio:

```bash
python -m pip install -r requirements.txt
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
|-- llm_client.py    # Cliente de la API de Anthropic
|-- logger.py        # Registro en consola y archivo
|-- main.py          # Punto de entrada del chatbot
```
