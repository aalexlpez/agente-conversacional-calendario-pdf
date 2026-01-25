# Agente Conversacional para Gestión de Calendario

Este repositorio implementa un agente conversacional en Python capaz de gestionar eventos de calendario, mantener conversaciones contextuales y responder preguntas sobre documentos PDF. El diseño sigue principios SOLID, utiliza asincronía y es fácilmente extensible mediante un sistema de plugins para herramientas externas.

## Índice

- [Guía paso a paso](#guía-paso-a-paso)
- [Características principales](#características-principales)
- [Instalación](#instalación)
- [Ejecución](#ejecución)
- [Proveedores de LLM soportados](#proveedores-de-llm-soportados)
- [Persistencia](#persistencia)
- [Herramientas externas y extensibilidad](#herramientas-externas-y-extensibilidad)
- [Endpoints principales](#endpoints-principales)
- [Pruebas](#pruebas)
- [Notas y anotaciones extra (ejecución sencilla)](#notas-y-anotaciones-extra-ejecución-sencilla)
- [Estructura del proyecto](#estructura-del-proyecto)
- [PDF: subida y consultas (con memoria)](#pdf-subida-y-consultas-con-memoria)
- [Instrucciones ejemplo para agente de calendario](#instrucciones-ejemplo-para-agente-de-calendario)
- [Extensión por herramientas externas (plugins)](#extensión-por-herramientas-externas-plugins)
- [Ejemplos rápidos (para un cliente como postman, swagger o cualquiera)](#ejemplos-rápidos-para-un-cliente-como-postman-swagger-o-cualquiera)
- [Despliegue en Railway (Docker)](#despliegue-en-railway-docker)
- [Usuarios y contraseñas para la obtención de tokens](#usuarios-y-contraseñas-de-ejemplo)

## Guía paso a paso

### 1) Levantar la aplicación en local
Sigue en orden las secciones **Instalación** y **Ejecución**. Al final, abre la documentación interactiva en:

- http://localhost:8000/docs

### 2) Probar la aplicación en Render
Si prefieres probar directamente en el entorno desplegado, usa la documentación interactiva aquí:

- https://agente-conversacional-calendario-pdf.onrender.com/docs

NOTA: Es probable que las primeras peticiones fallen o tarden debido al servidio de Render.com, que activa el servidor al recibir las peticiones.

### 3) Probar funcionalidades
Puedes usar los ejemplos de la sección **Ejemplos rápidos** o las rutas descritas en **Endpoints principales** y **PDF: subida y consultas (con memoria)**.

## Características principales

- **Autenticación de usuarios** (simulada con almacén local)
- **Gestión de múltiples conversaciones**: cada una con su propio contexto y memoria
- **Almacenamiento en memoria** para usuarios, eventos y conversaciones
- **Integración de herramientas externas** (ejemplo: calendario, análisis de PDF)
- **Extensible mediante registro de plugins** para nuevas herramientas
- **Pruebas unitarias y de integración** incluidas (solo pruebas básicas)

## Instalación

1. Clona el repositorio:
  ```sh
  git clone https://github.com/tu_usuario/agente-conversacional.git
  cd agente-conversacional
  ```
2. Crea y activa un entorno virtual:
  ```sh
  python -m venv venv
  # En Windows
  venv\Scripts\activate
  # En Unix/Mac
  source venv/bin/activate
  ```
3. Instala las dependencias:
  ```sh
  python -m pip install -r requirements.txt
  ```
4. Copia el archivo `.env.example` a `.env` y configura las variables necesarias (por ejemplo, API_BASE_URL, JWT_SECRET_KEY, etc.).

## Ejecución

1. Inicia el servidor FastAPI con Uvicorn:
  ```sh
  uvicorn src.api.main:app --reload
  ```
2. Accede a la documentación interactiva (swagger) en [http://localhost:8000/docs](http://localhost:8000/docs)

## Proveedores de LLM soportados

El agente soporta múltiples proveedores de modelos de lenguaje (LLM) para la comprensión y generación de texto. Puedes alternar entre proveedores configurando la variable `LLM_PROVIDER` en tu archivo `.env`.

- **APIFreeLLM** (modelo limitado. No me ha funcionado muy bien)
- **Groq** (recomendado, por ejemplo: `llama-3.1-8b-instant` y posee varios LLM para hacer test)

Ejemplo de configuración para Groq:
```dotenv
LLM_PROVIDER=groq
GROQ_API_KEY=tu_api_key
GROQ_MODEL=llama-3.1-8b-instant
```

Ejemplo de configuración para APIFreeLLM:
```dotenv
LLM_PROVIDER=apifreellm
APIFREELLM_API_KEY=tu_api_key
APIFREELLM_MODEL=apifreellm
```

**Nota:** Si no se configura correctamente la API key o el modelo, el agente mostrará un error al intentar generar respuestas.

## Persistencia

El proyecto usa almacenamiento en memoria (diccionarios) abstraído en la clase `Storage`, lo que permite sustituir el mecanismo de persistencia sin modificar el núcleo.

## Herramientas externas y extensibilidad

El registro de herramientas (`ToolRegistry`) permite agregar nuevas integraciones sin modificar el núcleo. Todas las herramientas deben heredar de la clase abstracta `BaseTool` y registrarse en el `ToolRegistry`.

### Ejemplo para agregar una nueva herramienta
```python
from src.tools.base import BaseTool

class WeatherTool(BaseTool):
   name = "weather"
   async def execute(self, query: str) -> str:
      # Lógica para consultar el clima
      return "Soleado"

from src.tools.base import ToolRegistry
_tool_registry = ToolRegistry()
_tool_registry.register(WeatherTool())
```

## Endpoints principales

### Calendario
- Agregar evento: "Agrega un evento llamado [nombre] el [fecha] a las [hora]."
- Listar eventos: "¿Qué eventos tengo el [fecha]?"
- Editar evento: "Edita el evento [nombre] y cámbialo a [nuevo dato]."
- Eliminar evento: "Elimina el evento [nombre] del [fecha]."

### PDF: subida y consultas
- **POST /documents/upload**: Sube un PDF y lo asocia a una conversación.
- **GET /documents**: Lista documentos, opcionalmente filtrados por conversación.
- **POST /documents/query**: Busca palabras clave en el contenido de un PDF.

## Pruebas

Para ejecutar los tests unitarios y de integración:
```sh
python -m pytest
```
Puedes configurar la URL base de la API en el archivo `.env` usando la variable `API_BASE_URL`.

## Notas y anotaciones extra (ejecución sencilla)

- **.env recomendado:** copia `.env.example` a `.env` y completa claves. Si no usas Google Calendar, puedes dejar esas variables vacías.
- **Uvicorn en Windows:** usa `uvicorn src.api.main:app --reload` desde el entorno virtual activado.
- **Credenciales demo:** por defecto existen usuarios `user1`/`pass1`, `user2`/`pass2`, etc. (ver `AuthService`).
- **PDFs:** la extracción usa `pdfminer.six`; si no está instalado, la extracción devolverá vacío.
- **WebSocket:** conecta a `ws://localhost:8000/ws/chat/{conversation_id}?token=<TOKEN>` para chat en tiempo real.
- **Swagger:** `http://localhost:8000/docs` para explorar endpoints y probarlos.

## Estructura del proyecto

- `src/domain/`: Entidades y contratos de dominio (modelos, interfaces, abstracciones)
- `src/infrastructure/`: Implementaciones concretas (almacenamiento, autenticación, herramientas externas)
- `src/application/`: Lógica de aplicación, orquestación y servicios
- `src/api/`: Endpoints y controladores FastAPI
- `tests/`: Pruebas unitarias y de integración


## PDF: subida y consultas (con memoria)
La funcionalidad de PDFs ya está implementada mediante un endpoint de subida y otro de consulta. La extracción y búsqueda se encapsulan en `PDFTool` (implementación de `BaseTool`), y el contenido se persiste en memoria para que el agente lo use en conversaciones posteriores.

### Endpoints disponibles
- **POST /documents/upload** (multipart/form-data)
  - Campos: `file` (PDF), `conversation_id`
  - Resultado: devuelve `document_id` y metadatos.
- **GET /documents**
  - Opcional: `conversation_id` para filtrar documentos por conversación.
- **POST /documents/query** (JSON)
  - Campos: `conversation_id`, `document_id`, `keyword`
  - Resultado: respuesta basada en el contenido del PDF.

### Abstracción de la herramienta
`PDFTool` encapsula la extracción y búsqueda del contenido. Si más adelante quieres cambiar el motor (por ejemplo, usar embeddings o un servicio externo), solo necesitas reemplazar la implementación de `PDFTool` manteniendo la misma interfaz.

### Integración con la memoria del agente
- Al subir un PDF, el texto extraído se almacena como `Document` en `InMemoryStore` asociado al `user_id` y `conversation_id`.
- Al consultar, el endpoint recupera el documento desde memoria y delega a `PDFTool` la búsqueda.
- Esto permite reutilizar el contenido del PDF en la misma conversación sin re-procesar el archivo.

> Ubicación del código:
> - Endpoints: `src/api/documents.py`
> - Herramienta: `src/tools/pdf_tool.py`
> - Memoria: `src/infrastructure/memory_store.py`

## Instrucciones ejemplo para agente de calendario

 <p align="center">
  <b>-----------------------------¡¡¡NOTA IMPORTANTE!!!-----------------------------</b>
</p>


> Los endpoints de eventos <b>no van a funcionar</b>, ya que actualmente la integración con Google Calendar utiliza mi acceso personal de Google Cloud Platform. En un entorno real, cada usuario debería autenticar su propia cuenta de Google y autorizar el acceso a su calendario personal para gestionar sus eventos de forma independiente. 
> He dejado dos imagenes en la ruta raíz para apreciar interacciones que he tenido en mi google calendar. En la imagen 1, van a ver una interacción con el LLM a través de postman para organizar reuniones. En la imagen 2, van a ver mi google calendar con los eventos organizados.

<b>Agregar evento:</b>

"Agrega un evento llamado [nombre] el [fecha] a las [hora]."
Ejemplo: "Agrega un evento llamado Reunión el 28 de enero a las 10 am."

<b>Listar eventos:</b>

"Muéstrame los eventos del [fecha]."
"¿Qué eventos tengo el [fecha]?"
Ejemplo: "Lista los eventos del 30 de enero." (En este caso he conseguido algunos bugs)

<b>Editar evento:</b>

"Edita el evento [nombre o fecha] y cámbialo a [nuevo nombre/fecha/hora]."
Ejemplo: "Cambia el evento del 28 de enero a las 12 pm al 29 de enero a las 10 am"

<b>Eliminar evento:</b>

"Elimina el evento [nombre] del [fecha]."
"Borra el evento del [fecha]."
Ejemplo: "Elimina el evento Reunión del 28 de enero."
Ejemplo: "Borra el evento del 30 de enero."

## Extensión por herramientas externas (plugins)

El agente está diseñado para ser fácilmente extensible con nuevas herramientas externas (por ejemplo, APIs, servicios, utilidades) sin modificar el núcleo del sistema. Esto se logra mediante un patrón de registro de plugins:

### ¿Cómo funciona?
- **Interfaz común:** Todas las herramientas deben heredar de la clase abstracta `BaseTool` (ver `src/tools/base.py`).
- **Registro dinámico:** Las herramientas se registran en el `ToolRegistry`, que permite al agente descubrirlas y utilizarlas sin acoplamiento directo.
- **Desacoplamiento:** El núcleo del agente (gestión de conversaciones, LLM, etc.) interactúa solo con el `ToolRegistry`, nunca con implementaciones concretas.

### Pasos para agregar una nueva herramienta
1. **Crear una clase que herede de `BaseTool`:**

    ```python
    from src.tools.base import BaseTool

    class WeatherTool(BaseTool):
        name = "weather"
        async def execute(self, query: str) -> str:
            # Lógica para consultar el clima
            return "Soleado"
    ```

2. **Registrar la herramienta en el `ToolRegistry`:**

    ```python
    from src.tools.base import ToolRegistry
    from src.tools.weather_tool import WeatherTool

    _tool_registry = ToolRegistry()
    _tool_registry.register(WeatherTool())
    ```

3. **El agente ya podrá usar la nueva herramienta sin cambios adicionales en el núcleo.**

> **Resumen:** Para incorporar nuevas herramientas, solo implementa la interfaz `BaseTool` y regístrala en el `ToolRegistry`. El núcleo del agente permanece inalterado.

## Ejemplos rápidos (para un cliente como postman, swagger o cualquiera)

### 1) Login y token (curl)
```sh
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user1&password=pass1"
```

### 2) Crear conversación
```sh
curl -X POST http://localhost:8000/conversations \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Mi conversación"}'
```

### 3) Subir PDF
```sh
curl -X POST http://localhost:8000/documents/upload \
  -H "Authorization: Bearer <TOKEN>" \
  -F "file=@mi_archivo.pdf" \
  -F "conversation_id=<CONVERSATION_ID>"
```

### 4) Buscar en PDF
```sh
curl -X POST http://localhost:8000/documents/query \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id":"<CONVERSATION_ID>","document_id":"<DOCUMENT_ID>","keyword":"hola"}'
```

### 5) Crear evento de calendario 
```sh
curl -X POST http://localhost:8000/events \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Reunión","starts_at":"2026-01-25T10:00:00Z","ends_at":"2026-01-25T11:00:00Z"}'
```

## Despliegue en Railway (Docker)

Puedes desplegar este agente en Railway usando el Dockerfile incluido. Railway permite levantar servicios backend en Python fácilmente y tiene un plan gratuito.

### Pasos para desplegar en Railway

1. **Sube tu repositorio a GitHub** (o GitLab).
2. **Crea un proyecto en Railway**:
   - Ve a https://railway.app/
   - Inicia sesión y haz clic en "New Project" > "Deploy from GitHub repo".
   - Selecciona tu repositorio.
3. **Railway detectará el Dockerfile automáticamente** y construirá la imagen.
4. **Configura variables de entorno** en la sección "Variables" de Railway (por ejemplo, claves de API, secretos, etc.).
5. **El servicio se expondrá en el puerto 8000** (por defecto). Railway asigna una URL pública.
6. **Accede a tu agente desplegado** usando la URL que te da Railway (por ejemplo, `https://tu-proyecto.up.railway.app/docs`).

#### Ejemplo de despliegue local con Docker

```sh
# Construye la imagen
 docker build -t agente-conversacional .
# Ejecuta el contenedor
 docker run -p 8000:8000 --env-file .env agente-conversacional
```

> **Nota:** Si usas Google Calendar o LLM externos, asegúrate de subir los archivos de credenciales y configurar las variables de entorno necesarias en Railway.

## Usuarios y contraseñas de ejemplo

La autenticación está basada en un almacén local en memoria. Puedes iniciar sesión con cualquiera de los siguientes usuarios y contraseñas por defecto:

| Usuario  | Contraseña |
|----------|------------|
| admin    | admin123   |
| user1    | pass1      |
| user2    | pass2      |
| user3    | pass3      |
| user4    | pass4      |
| user5    | pass5      |
| user6    | pass6      |
| user7    | pass7      |
| user8    | pass8      |
| user9    | pass9      |
| user10   | pass10     |

Puedes modificar estos valores en el archivo `src/infrastructure/auth.py` si necesitas otros usuarios.