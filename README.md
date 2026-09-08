# MCP para gestión de reservas de salas de reuniones

Proyecto 1 del curso Redes CC3067 de la Universidad del Valle de Guatemala.

Este proyecto implementa un chatbot de terminal capaz de comunicarse con varios servidores MCP mediante un cliente y mensajes JSON-RPC construidos manualmente. El caso de uso principal es la gestión de reservas de salas de reuniones empresariales.

El sistema puede ejecutarse localmente mediante `stdio` y el servidor propio de reservas también puede ejecutarse mediante HTTP/HTTPS. El mismo cliente MCP manual puede comunicarse con el servidor local o con el servidor desplegado en Render.

## Objetivo del proyecto

El objetivo es aplicar conceptos de redes y comunicación entre procesos mediante:

- JSON-RPC 2.0 construido y validado manualmente.
- MCP implementado manualmente para el servidor propio y el cliente del proyecto.
- Comunicación local mediante `stdin` y `stdout`.
- Comunicación remota mediante HTTP/HTTPS.
- Integración de un chatbot con un LLM y herramientas provenientes de varios servidores MCP.
- Registro de solicitudes y respuestas para analizar posteriormente el tráfico de red.

No se utilizan FastMCP, MCP SDK ni librerías que oculten la implementación del protocolo MCP o JSON-RPC en nuestro cliente y servidor propio.

## Arquitectura

```text
Usuario en terminal
        |
        v
Chatbot Host
        |
        v
Claude mediante API de Anthropic
        |
        | tool_use con nombres unicos
        v
McpManager
        |
        +--> reservations --> McpClient --> StdioTransport o HttpTransport
        |                         |              |
        |                         |              +--> MCP local de reservas
        |                         |              +--> MCP remoto en Render
        |                         |
        +--> filesystem -------> McpClient --> Filesystem MCP oficial local
        |
        +--> git -------------> McpClient --> Git MCP oficial local
```

### Chatbot Host

`ChatbotHost` mantiene el contexto de la sesión y coordina la conversación con Claude. Recibe el catálogo unificado de herramientas desde `McpManager`, entrega ese catálogo al LLM y procesa los bloques `tool_use` que Claude solicita.

El host no conoce los detalles de `stdio`, HTTP ni JSON-RPC. Cuando Claude solicita una herramienta, el host la entrega al manager, recibe el resultado y lo devuelve a Claude como `tool_result` para que el modelo genere una respuesta natural.

### Claude

Claude se consume mediante la librería oficial de Anthropic únicamente para realizar llamadas al LLM. La librería no implementa MCP ni JSON-RPC en este proyecto.

El LLM recibe nombres de herramientas únicos, por ejemplo:

```text
reservations__list_rooms
filesystem__write_file
git__git_status
```

### McpManager

`McpManager` mantiene los clientes MCP identificados por servidor, inicializa los clientes, descubre sus herramientas y enruta las llamadas.

Los nombres internos conservan el formato:

```text
reservations.list_rooms
filesystem.write_file
git.git_status
```

La conversión hacia los nombres expuestos a Claude se construye automáticamente a partir de `tools/list`.

### Servidores MCP

El proyecto trabaja con tres servidores:

- `reservations`: servidor MCP propio para reservas.
- `filesystem`: servidor Filesystem MCP oficial, ejecutado localmente.
- `git`: servidor Git MCP oficial, ejecutado localmente.

## Implementación manual de MCP y JSON-RPC

El protocolo de comunicación del cliente y del servidor propio se implementa manualmente. El módulo `src/json_rpc.py` construye y valida:

- solicitudes;
- respuestas exitosas;
- respuestas de error;
- notificaciones;
- identificadores para correlacionar solicitudes y respuestas.

El servidor propio utiliza `McpProtocolHandler`, que contiene la lógica común de MCP:

- `initialize`;
- `notifications/initialized`;
- `tools/list`;
- `tools/call`;
- errores JSON-RPC y errores de herramientas.

El handler es independiente del transporte. Por eso el mismo protocolo se puede utilizar mediante `stdio` o HTTP.

## Servidor MCP de reservas

El servidor propio administra salas y reservas mediante archivos JSON. Su lógica de negocio está implementada en `ReservationService` y es reutilizada por el servidor local y por el servidor HTTP remoto.

### Herramientas

#### `list_rooms`

Lista las salas disponibles y sus características. No requiere parámetros.

#### `check_availability`

Consulta si una sala está disponible durante un intervalo.

Parámetros:

```json
{
  "room_id": "room-001",
  "date": "2099-12-15",
  "start_time": "10:00",
  "end_time": "11:00"
}
```

#### `create_reservation`

Crea una reserva si la sala existe, el intervalo es válido y no hay otra reserva superpuesta.

Parámetros:

```json
{
  "room_id": "room-001",
  "date": "2099-12-15",
  "start_time": "10:00",
  "end_time": "11:00",
  "reserved_by": "Anggelie",
  "title": "Reunión de proyecto"
}
```

La herramienta genera identificadores como `RES-0001`.

#### `cancel_reservation`

Cancela una reserva existente.

Parámetros:

```json
{
  "reservation_id": "RES-0001"
}
```

#### `list_reservations`

Lista las reservas existentes. Acepta filtros opcionales:

```json
{
  "date": "2099-12-15",
  "room_id": "room-001"
}
```

Las reglas de negocio impiden reservas superpuestas, exigen que la hora inicial sea menor que la hora final y verifican que la sala exista.

## Transporte local mediante stdio

El servidor propio puede ejecutarse localmente con:

```powershell
python -m src.mcp_server
```

El cliente `McpClient` utiliza `StdioTransport`, que inicia el proceso y transmite un mensaje JSON-RPC por línea mediante `stdin` y `stdout`.

Este transporte se utiliza para el servidor local de reservas y también como base para ejecutar servidores MCP locales externos.

## Transporte remoto mediante HTTP/HTTPS

El servidor HTTP propio puede ejecutarse localmente con:

```powershell
python -m src.mcp_http_server
```

Por defecto escucha en:

```text
HOST=127.0.0.1
PORT=8000
```

En un entorno como Render, el proceso puede recibir:

```text
HOST=0.0.0.0
PORT=<puerto inyectado por Render>
```

El servidor expone:

```text
GET /health
POST /mcp
```

`GET /health` devuelve:

```json
{
  "status": "ok"
}
```

`POST /mcp` recibe un mensaje JSON-RPC MCP con `Content-Type: application/json` y devuelve la respuesta generada por `McpProtocolHandler`. Las notificaciones sin respuesta reciben `HTTP 204 No Content`.

El cliente `HttpTransport` utiliza solicitudes HTTP `POST`, controla el timeout, valida el status HTTP y entrega la respuesta al mismo `McpClient` utilizado con `StdioTransport`.

## Configuración

### Selección local o remota de reservas

La variable `MCP_RESERVATIONS_MODE` controla qué transporte utiliza el servidor propio:

```powershell
$env:MCP_RESERVATIONS_MODE = "local"
```

Usa el servidor MCP local mediante `stdio`.

```powershell
$env:MCP_RESERVATIONS_MODE = "remote"
```

Usa el servidor MCP remoto mediante HTTP/HTTPS.

El valor predeterminado es `local`. Si se proporciona otro valor, el programa muestra un error de configuración en lugar de continuar silenciosamente.

### URL remota

La URL se configura mediante:

```powershell
$env:MCP_RESERVATIONS_URL = "https://mcp-reservas.onrender.com/mcp"
```

El valor predeterminado configurado para el cliente es el endpoint remoto de Render utilizado durante las validaciones del proyecto.

`MCP_RESERVATIONS_URL` pertenece al cliente. No es una variable necesaria para arrancar el servidor HTTP.

### API de Anthropic

Para utilizar el chatbot con Claude se debe configurar la API key en la sesión local de PowerShell:

```powershell
$env:ANTHROPIC_API_KEY = "tu_clave_real_de_anthropic"
$env:ANTHROPIC_MODEL = "claude-3-5-haiku-latest"
```

Nunca se debe escribir una clave real en el código, en el README, en Git ni en los logs. `.env.example` contiene únicamente valores de ejemplo.

El servidor MCP HTTP de reservas no necesita `ANTHROPIC_API_KEY` porque no utiliza Claude.

### Directorio de datos

La persistencia utiliza JSON. Por defecto se emplea:

```text
data/rooms.json
data/reservations.json
```

La ruta puede configurarse mediante:

```powershell
$env:MCP_DATA_DIR = "C:\ruta\de\datos"
```

Si la ruta no existe, el servicio crea el directorio y genera las salas iniciales junto con un archivo vacío de reservas. En Render, el filesystem puede ser efímero; la persistencia permanente no forma parte de esta fase.

## Despliegue en Render

El servidor HTTP está preparado como Web Service en Render mediante `render.yaml`.

Configuración utilizada:

```yaml
buildCommand: pip install -r requirements.txt
startCommand: python -m src.mcp_http_server
healthCheckPath: /health
```

El endpoint remoto validado en el proyecto es:

```text
https://mcp-reservas.onrender.com/mcp
```

El health check remoto es:

```text
https://mcp-reservas.onrender.com/health
```

Para el servidor remoto no se requiere `ANTHROPIC_API_KEY`. Render inyecta el valor de `PORT`; no se fija un puerto cloud específico en el código ni en `render.yaml`.

## Filesystem MCP oficial

Filesystem MCP se ejecuta como servidor local oficial mediante `npx` y transporte `stdio`. El proyecto lo configura con un directorio permitido, por ejemplo:

```text
sandbox/chatbot_workspace
```

El servidor solo puede operar dentro del directorio configurado. Entre sus herramientas disponibles se encuentran:

```text
read_file
read_text_file
write_file
create_directory
list_directory
search_files
get_file_info
list_allowed_directories
```

El acceso no se extiende automáticamente a todo el disco.

## Git MCP oficial

Git MCP se ejecuta localmente mediante `uvx mcp-server-git` y utiliza el cliente MCP manual del proyecto.

Sus herramientas incluyen:

```text
git_status
git_add
git_commit
git_log
git_diff
git_branch
git_checkout
git_show
```

El servidor oficial `mcp-server-git` no proporciona una herramienta `git_init`. Por eso, cuando una demostración necesita un repositorio nuevo, se ejecuta externamente:

```powershell
git init ruta\del\repositorio
```

Después de ese paso, las operaciones de estado, staging, commit e historial se realizan mediante Git MCP.

## Nombres de herramientas expuestos a Claude

Para evitar colisiones entre servidores, Claude recibe nombres con el servidor como prefijo:

```text
reservations__list_rooms
reservations__check_availability
reservations__create_reservation

filesystem__write_file
filesystem__read_text_file
filesystem__create_directory

git__git_status
git__git_add
git__git_commit
git__git_log
```

El manager transforma internamente esos nombres a rutas MCP:

```text
filesystem__write_file -> filesystem.write_file
git__git_status        -> git.git_status
reservations__list_rooms -> reservations.list_rooms
```

Claude solo recibe el catálogo de herramientas. No conoce el transporte ni construye JSON-RPC.

## Logs de interacciones MCP

Las interacciones se registran en:

```text
logs/mcp_interactions.log
```

Cada registro puede incluir:

- `timestamp`;
- `server`;
- `direction` (`CLIENT_TO_SERVER` o `SERVER_TO_CLIENT`);
- `method`;
- `id`;
- mensaje JSON completo.

Los servidores lógicos se identifican como:

```text
reservations
reservations_remote
filesystem
git
```

El script de captura remota utiliza un archivo separado:

```text
logs/wireshark_mcp_capture.log
```

Los archivos de logs están excluidos de Git.

## Captura y análisis de red

El script [`scripts/remote_mcp_capture_demo.py`](scripts/remote_mcp_capture_demo.py) genera tráfico MCP remoto controlado. Ejecuta únicamente operaciones de lectura:

```powershell
python scripts/remote_mcp_capture_demo.py
```

La secuencia es:

```text
initialize
notifications/initialized
tools/list
tools/call list_rooms
tools/call check_availability
```

No crea ni cancela reservas.

Para un análisis de red se pueden observar las siguientes capas:

- DNS, si se resuelve el dominio durante la captura;
- TCP, incluyendo IPs, puertos y establecimiento de conexión;
- TLS, incluyendo el handshake HTTPS;
- tráfico cifrado de aplicación.

El contenido JSON-RPC/MCP viaja dentro de HTTPS y normalmente no puede leerse directamente en Wireshark sin configurar descifrado TLS. El log de aplicación permite correlacionar las operaciones MCP (`initialize`, `tools/list` y `tools/call`) con los tiempos y paquetes observados en la captura.

No se desactiva la validación TLS ni se configura descifrado en esta fase.

## Instalación y ejecución en Windows

Requisitos principales:

- Python 3.10 o superior;
- Node.js y `npx` para Filesystem MCP;
- `uv` y `uvx` para Git MCP;
- Git.

Desde PowerShell, en la raíz del proyecto:

```powershell
python -m pip install -r requirements.txt
```

Para ejecutar el chatbot local:

```powershell
$env:MCP_RESERVATIONS_MODE = "local"
python -m src.main
```

Para utilizar el servidor remoto de reservas, sin cambiar Filesystem MCP ni Git MCP:

```powershell
$env:MCP_RESERVATIONS_MODE = "remote"
$env:MCP_RESERVATIONS_URL = "https://mcp-reservas.onrender.com/mcp"
python -m src.main
```

Comandos útiles para ejecutar solo el servidor propio:

```powershell
python -m src.mcp_server
python -m src.mcp_http_server
```

El chatbot termina con:

```text
salir
```

El contexto de conversación se reinicia con:

```text
/clear
```

## Pruebas

Para ejecutar toda la suite:

```powershell
python -m unittest discover -s tests -v
```

También se pueden ejecutar las validaciones estáticas:

```powershell
python -m compileall -q src tests
git diff --check
```

La suite cubre JSON-RPC, el servidor de reservas, el cliente MCP, los transportes stdio y HTTP, los servidores externos, el coordinador multi-MCP y las integraciones locales controladas.

## Estructura principal

```text
.
|-- data/
|   |-- rooms.json
|   `-- reservations.json
|-- scripts/
|   `-- remote_mcp_capture_demo.py
|-- src/
|   |-- chatbot_host.py
|   |-- config.py
|   |-- conversation.py
|   |-- json_rpc.py
|   |-- llm_client.py
|   |-- main.py
|   |-- mcp_client.py
|   |-- mcp_external_servers.py
|   |-- mcp_http_server.py
|   |-- mcp_http_transport.py
|   |-- mcp_interaction_logger.py
|   |-- mcp_manager.py
|   |-- mcp_protocol_handler.py
|   |-- mcp_server.py
|   |-- mcp_transport.py
|   `-- reservation_service.py
|-- tests/
|-- .env.example
|-- .gitignore
|-- render.yaml
|-- requirements.txt
`-- README.md
```

## Conclusiones

El proyecto demuestra un flujo completo de comunicación MCP construido manualmente. El mismo servidor de reservas puede utilizarse localmente mediante `stdio` y remotamente mediante HTTP/HTTPS, sin duplicar la lógica de reservas ni depender de un SDK MCP.

La integración con Filesystem MCP y Git MCP permite coordinar herramientas de distintos servidores mediante un catálogo unificado. Los logs de aplicación y el script de captura permiten relacionar las operaciones JSON-RPC/MCP con el tráfico de red. La persistencia actual en archivos JSON es suficiente para la demostración, pero puede ser efímera en Render y deberá reemplazarse por una solución persistente en una fase posterior si el proyecto lo requiere.
