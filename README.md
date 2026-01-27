# Agente Conversacional para Gestión de Calendario

Este repositorio implementa un agente conversacional en Python capaz de gestionar eventos de calendario, mantener conversaciones contextuales y responder preguntas sobre documentos PDF. El diseño sigue principios SOLID, utiliza asincronía (`async/await`) y es fácilmente extensible mediante un sistema de plugins para herramientas externas.

---

## Para evaluadores (TL;DR)

- El proyecto **cumple los requisitos funcionales y de diseño** solicitados en la prueba técnica.
- Arquitectura basada en **controladores delgados**, **principios SOLID** e **inversión de dependencias**.
- Soporte para **múltiples conversaciones concurrentes**, asincronía y **streaming vía WebSocket**.
- Sistema de **herramientas extensible** mediante registro de plugins, sin modificar el núcleo del agente.
- La **parte teórica** solicitada en la prueba se encuentra documentada en el archivo `RESPUESTAS_TECNICAS.md`.

Para una revisión rápida, se recomienda consultar:
1. Arquitectura del Agente Conversacional
2. Persistencia
3. Herramientas externas y extensibilidad
4. Pruebas

---

## Índice

### Uso y ejecución
- [Guía paso a paso](#guía-paso-a-paso)
- [Instalación](#instalación)
- [Ejecución](#ejecución)
- [Proveedores de LLM soportados](#proveedores-de-llm-soportados)
- [Anotaciones extra (ejecución sencilla)](#anotaciones-extra-ejecución-sencilla)
- [Ejemplos rápidos](#ejemplos-rápidos-para-un-cliente-como-postman-o-swagger)

### Funcionalidades
- [Características principales](#características-principales)
- [Endpoints principales](#endpoints-principales)
- [Uso del agente vía WebSocket](#uso-del-agente-vía-websocket)
- [Responder sobre un PDF](#responder-sobre-un-pdf-subida-y-consultas-con-memoria)
- [Instrucciones ejemplo para agente de calendario](#instrucciones-ejemplo-para-agente-de-calendario)

### Diseño y arquitectura
- [Persistencia](#persistencia)
- [Herramientas externas y extensibilidad](#herramientas-externas-y-extensibilidad)
- [Arquitectura del Agente Conversacional](#arquitectura-del-agente-conversacional)
- [Estructura del proyecto](#estructura-del-proyecto)

### Calidad y evaluación
- [Pruebas](#pruebas)
- [Parte teórica](#parte-teórica)
- [Usuarios y contraseñas de ejemplo](#usuarios-y-contraseñas-de-ejemplo)

---


## Parte teórica

Las respuestas a la **parte teórica solicitada en la prueba técnica** se encuentran en el archivo **`RESPUESTAS_TECNICAS.md`**, incluido en este repositorio.

---

## Guía paso a paso

### 1) Levantar la aplicación en local
Sigue en orden las secciones **Instalación** y **Ejecución**. Al final, abre la documentación interactiva en:

- http://localhost:8000/docs

### 2) Probar la aplicación en Render

- https://agente-conversacional-calendario-pdf.onrender.com/docs

**Nota:** el servicio se activa bajo demanda. Las primeras peticiones pueden tardar unos segundos y, al utilizar almacenamiento en memoria, los datos se pierden al reiniciar el servidor.

### 3) Probar funcionalidades
Puedes usar los ejemplos de la sección **Ejemplos rápidos** o las rutas descritas en **Endpoints principales**.

---

## Características principales

- Autenticación de usuarios (simulada con almacén local)
- Gestión de múltiples conversaciones con contexto independiente
- Almacenamiento en memoria para usuarios, eventos y documentos
- Integración de herramientas externas (calendario, PDFs)
- Arquitectura extensible mediante plugins
- Pruebas unitarias y de integración incluidas

---

## Instalación

1. Clona el repositorio:
```sh
git clone https://github.com/aalexlpez/agente-conversacional-calendario-pdf.git
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

---

## Ejecución

```sh
uvicorn src.api.main:app --reload
```

Accede a Swagger en `http://localhost:8000/docs`.

---

## Proveedores de LLM soportados

El agente soporta múltiples proveedores de modelos de lenguaje (LLM) para la comprensión y generación de texto. Puedes alternar entre proveedores configurando la variable `LLM_PROVIDER` en tu archivo `.env`.

- **APIFreeLLM** (modelo limitado; incluido como alternativa de prueba)
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

---

## Persistencia

Actualmente, **toda la información del agente (usuarios, eventos, conversaciones, documentos PDF, etc.) se almacena en memoria RAM** usando diccionarios Python. Esto significa que los datos existen solo mientras la aplicación está en ejecución: **al reiniciar o apagar el servidor, toda la información se pierde**.

### ¿Cómo está implementada la persistencia?
- El almacenamiento en memoria está abstraído principalmente en la clase `Storage` y su implementación concreta `InMemoryStore` (ver `src/infrastructure/memory_store.py`).
- Todas las operaciones de guardado, consulta y borrado pasan por esta capa, lo que permite desacoplar la lógica de negocio del mecanismo de persistencia.
- El resto del sistema (casos de uso, endpoints, herramientas) interactúa solo con la interfaz de almacenamiento, nunca directamente con los diccionarios.

### Ventajas del enfoque actual
- **Simplicidad y velocidad:** Ideal para desarrollo, pruebas y despliegues temporales.
- **Fácil de extender:** Puedes reemplazar la implementación de `Storage` por una basada en base de datos relacional (PostgreSQL, SQLite), NoSQL (MongoDB), archivos, Redis, etc., sin modificar el núcleo de la aplicación.

### Limitaciones
- **No persistente:** Todos los datos se borran al reiniciar el servidor.

### ¿Cómo migrar a una persistencia real?
1. Implementa una nueva clase que herede de la interfaz `Storage` y utilice el backend deseado (por ejemplo, una base de datos SQL).
2. Sustituye la instancia de `InMemoryStore` por tu nueva clase en la inicialización de la app.
3. El resto del sistema funcionará igual, ya que depende solo de la interfaz.

### Ubicación del código relevante
- Abstracción y lógica de almacenamiento: `src/infrastructure/memory_store.py`
- Uso en la aplicación: ver inyección de dependencias y casos de uso en `src/application/` y `src/api/`

---

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

---

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

---

## Uso del agente vía WebSocket

El agente permite **streaming de respuestas y concurrencia** mediante WebSocket, permitiendo que el usuario cambie de conversación mientras se procesa otra.

### URL de conexión

```text
ws://localhost:8000/ws/chat/{CONVERSATION_ID}?token={TOKEN}
```

En producción (por ejemplo, usando Postman u otro cliente WebSocket): 

```text
wss://agente-conversacional-calendario-pdf.onrender.com/ws/chat/{CONVERSATION_ID}?token={TOKEN}

con este formato para enviarle mensaje:

{
    "text": "Mensaje al LLM"
}
```

### Flujo típico

1. Autenticarse y obtener un token JWT.
2. Crear una conversación (`conversation_id`).
3. Conectarse al WebSocket usando el `conversation_id` y el token.
4. Enviar mensajes de texto; el agente responderá de forma progresiva.
5. El sistema notifica cuando la respuesta ha finalizado.

Este enfoque permite manejar múltiples conversaciones simultáneas sin bloquear el hilo principal.

---

## Pruebas

El proyecto incluye una suite de **pruebas automáticas** organizadas en la carpeta `tests/`. Estas pruebas cubren tanto la lógica de negocio como la integración de los principales casos de uso del agente.

### Tipos de pruebas

- **Pruebas unitarias:** Verifican el funcionamiento aislado de componentes clave como utilidades, servicios, herramientas y lógica de dominio.
  - Ejemplo: `test_jwt_service.py`, `test_prompt_utils.py`, `test_notification_manager.py`, `test_conversation_manager.py`.
- **Pruebas de integración:** Evalúan el comportamiento de los endpoints y la interacción entre componentes, simulando flujos completos de usuario.
  - Ejemplo: `test_api.py`, `test_api_use_cases_auth.py`, `test_api_use_cases_conversations.py`, `test_api_use_cases_documents.py`, `test_api_use_cases_events.py`, `test_send_message_use_case.py`.
- **Pruebas de herramientas externas:** Validan la integración con utilidades como la extracción de PDFs.
  - Ejemplo: `test_integration_pdf_extraction.py`.

### Ejecución de pruebas

Para ejecutar todos los tests:
```sh
python -m pytest
```
Esto buscará y ejecutará automáticamente todos los archivos que comiencen con `test_` en la carpeta `tests/`.

Puedes ejecutar un archivo de test específico, por ejemplo:
```sh
python -m pytest tests/test_api_use_cases_documents.py
```

### Cobertura

Las pruebas cubren:
- Autenticación y generación/validación de tokens JWT.
- Gestión de conversaciones y tareas.
- Subida, extracción y consulta de PDFs.
- Integración con el LLM y herramientas externas.
- Notificaciones y eventos de calendario.

En un flujo de CI/CD, las pruebas unitarias e integración se ejecutarían en cada pull request, mientras que las pruebas end-to-end se reservarían para entornos previos a producción.

---

## Anotaciones extra (ejecución sencilla)

- **.env recomendado:** copia `.env.example` a `.env` y completa claves. Si no usas Google Calendar, puedes dejar esas variables vacías.
- **Uvicorn en Windows:** usa `uvicorn src.api.main:app --reload` desde el entorno virtual activado.
- **[Credenciales demo:](#usuarios-y-contraseñas-de-ejemplo)** por defecto existen usuarios `user1`/`pass1`, `user2`/`pass2`, etc. (ver `AuthService`).
- **PDFs:** la extracción usa `pdfminer.six`; si no está instalado, la extracción devolverá vacío.
- **WebSocket:** conecta a `ws://localhost:8000/ws/chat/{conversation_id}?token=<TOKEN>` para chat en tiempo real.
- **Swagger:** `http://localhost:8000/docs` para explorar endpoints y probarlos.

---

## Estructura del proyecto

- `src/domain/`: Entidades y contratos de dominio (modelos, interfaces, abstracciones)
- `src/infrastructure/`: Implementaciones concretas (almacenamiento, autenticación, herramientas externas)
- `src/application/`: Lógica de aplicación, orquestación y servicios
- `src/api/`: Endpoints y controladores FastAPI
- `tests/`: Pruebas unitarias y de integración

---

## Arquitectura del Agente Conversacional

La arquitectura sigue una separación clara por capas (API, Application, Domain, Infrastructure), favoreciendo mantenibilidad, testabilidad y extensibilidad.

### Diagrama Visual (ASCII) — Capas y Conexiones

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                   API Layer                                 │
│  FastAPI REST + WebSocket                                                   │
│  - auth.py (JWT login)                                                      │
│  - conversations.py (CRUD conversaciones)                                   │
│  - documents.py (upload/query PDF)                                          │
│  - websocket.py (chat streaming)                                            │
└───────────────┬─────────────────────────────────────────────────────────────┘
                │ Depends / Inyección
┌───────────────▼─────────────────────────────────────────────────────────────┐
│                             Application Layer                               │
│  - SendMessageUseCase (orquestador)                                         │
│  - ConversationUseCase / DocumentUseCase / EventUseCase                     │
│  - AuthLoginUseCase                                                         │
│  - ConversationManager (concurrencia & estado activo)                       │
│  - NotificationManager (finalización de respuesta)                          │
└───────────┬──────────────────────────┬──────────────────────────────────────┘
            │                          │
            │                          │
┌───────────▼───────────┐  ┌───────────▼─────────────────────────────────────┐
│  Infrastructure Layer │  │                 Tools (Plugins)                 │
│  - InMemoryStore      │  │  - ToolRegistry                                 │
│  - AIService (LLM)    │  │  - PDFTool (pdfminer.six)                       │
│  - AuthService        │  │  - GoogleCalendarTool (Google API)              │
│  - JWT Service        │  │                                                 │
└───────────┬───────────┘  └───────────┬─────────────────────────────────────┘
            │                          │
            │                          │
┌───────────▼────────────────────────────────────────────────────────────────┐
│                               Domain Layer                                 │
│  - Entities (User, Conversation, Message, Event, Document)                 │
│  - Interfaces (Protocols)                                                  │
│  - Exceptions (DomainError, ResourceNotFound, etc.)                        │
└────────────────────────────────────────────────────────────────────────────┘
            │
            │ Integraciones externas
┌───────────▼────────────────────────────────────────────────────────────────┐
│  External Services                                                         │
│  - APIFreeLLM / Groq                                                       │
│  - Google Calendar API                                                     │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Responder sobre un PDF (subida y consultas con memoria)

El agente permite responder preguntas y realizar búsquedas sobre el contenido de documentos PDF subidos por el usuario. Esta funcionalidad es clave para escenarios donde se necesita extraer información específica, buscar palabras clave o responder consultas contextuales basadas en documentos.

### ¿Cómo funciona?

1. **Subida y extracción:**
   - El usuario sube un PDF mediante el endpoint `/documents/upload`.
   - El sistema extrae automáticamente el texto del PDF usando la herramienta `PDFTool (pdfminer.six)`.
   - El texto extraído se almacena en memoria como un objeto `Document`, asociado al usuario y a la conversación activa.

2. **Consulta y respuesta:**
   - El usuario puede realizar consultas sobre el PDF usando el endpoint `/documents/query`, indicando el `document_id`, la `conversation_id` y la palabra clave o pregunta.
   - **Si hay un LLM configurado:** El agente construye un prompt con el contenido del PDF y la pregunta del usuario, y delega la generación de la respuesta al LLM. Así, la respuesta es inteligente y contextual, no solo una búsqueda literal de palabras clave.
   - **Si NO hay LLM disponible:** El sistema recurre a la herramienta `PDFTool` para realizar una búsqueda simple de palabras clave en el texto extraído (por ejemplo, contar ocurrencias o extraer fragmentos relevantes).
   - Si el PDF no tiene texto extraíble (por ejemplo, es un escaneo sin OCR), el sistema informa al usuario que no se pudo extraer texto legible.

> **Resumen:** Por defecto, el endpoint `/documents/query` responde usando el LLM para generar respuestas inteligentes sobre el contenido del PDF. Solo si no hay LLM disponible, se realiza una búsqueda literal de palabras clave.

### Integración con la memoria del agente

- Todos los documentos PDF y su contenido extraído se almacenan en la memoria interna (`InMemoryStore`) del agente.
- Cada documento está vinculado a un usuario y a una conversación, permitiendo que el agente recuerde y reutilice el contenido en interacciones futuras sin necesidad de volver a procesar el archivo.
- Cuando el usuario realiza una consulta sobre un PDF, el agente accede a la memoria, recupera el documento y utiliza la herramienta de búsqueda para responder de forma rápida y precisa.

### Ejemplo de flujo

1. El usuario sube un archivo PDF a través de `/documents/upload`.
2. El agente extrae el texto y lo almacena en memoria.
3. El usuario pregunta: "¿Cuántas veces aparece la palabra 'contrato' en el PDF?" usando `/documents/query`.
4. El agente busca en el texto almacenado y responde con el número de coincidencias.
5. En una conversación, el agente puede usar el contenido del PDF para dar respuestas contextuales, por ejemplo: "¿Qué dice la cláusula 5 del documento?".

### Ejemplos de endpoints y abstracción

- **POST /documents/upload** (multipart/form-data)
  - Campos: `file` (PDF), `conversation_id`
  - Resultado: devuelve `document_id` y metadatos.
- **GET /documents**
  - Opcional: `conversation_id` para filtrar documentos por conversación.
- **POST /documents/query** (JSON)
  - Campos: `conversation_id`, `document_id`, `keyword`
  - Resultado: respuesta basada en el contenido del PDF.

`PDFTool` encapsula la extracción y búsqueda del contenido. Si más adelante quieres cambiar el motor (por ejemplo, usar embeddings o un servicio externo), solo necesitas reemplazar la implementación de `PDFTool` manteniendo la misma interfaz.

### Ubicación del código relevante

- Endpoints: `src/api/documents.py`
- Herramienta de extracción y búsqueda: `src/tools/pdf_tool.py`
- Memoria del agente: `src/infrastructure/memory_store.py`

---

## Instrucciones ejemplo para agente de calendario

<p align="center">
  <b>-----------------------------¡¡¡NOTA IMPORTANTE!!!-----------------------------</b>
</p>

> Nota: la integración con Google Calendar utiliza credenciales de desarrollo y no representa un flujo OAuth multiusuario completo. En un entorno productivo, cada usuario debería autorizar su propia cuenta.
> 
> Se incluyen dos imágenes en la raíz del proyecto a modo ilustrativo de interacciones reales con el calendario.


<b>Agregar evento:</b>

"Agrega un evento llamado [nombre] el [fecha] a las [hora]."
Ejemplo: "Agrega un evento llamado Reunión el 28 de enero a las 10 am."

<b>Listar eventos:</b>

"Muéstrame los eventos del [fecha]."
"¿Qué eventos tengo el [fecha]?"
Ejemplo: "Lista los eventos del 30 de enero." (Este flujo presenta algunos comportamientos no deseados)

<b>Editar evento:</b>

"Edita el evento [nombre o fecha] y cámbialo a [nuevo nombre/fecha/hora]."
Ejemplo: "Cambia el evento del 28 de enero a las 12 pm al 29 de enero a las 10 am"

<b>Eliminar evento:</b>

"Elimina el evento [nombre] del [fecha]."
"Borra el evento del [fecha]."
Ejemplo: "Elimina el evento Reunión del 28 de enero."
Ejemplo: "Borra el evento del 30 de enero."

---

## Ejemplos rápidos (para un cliente como Postman o Swagger)

Los siguientes ejemplos representan flujos mínimos de validación funcional.

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

---

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

