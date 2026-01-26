
"""
Módulo de dependencias compartidas para la API del agente conversacional.

Define singletons y funciones de acceso para servicios, herramientas y casos de uso.
Permite la inyección de dependencias en los endpoints de FastAPI.
"""

from __future__ import annotations

import os

import structlog

from dotenv import load_dotenv

from src.application.conversation_manager import ConversationManager
from src.application.use_cases import CreateConversationUseCase, GetConversationHistoryUseCase, SendMessageUseCase
from src.application.api_use_cases import AuthLoginUseCase, ConversationUseCase, DocumentUseCase, EventUseCase
from src.infrastructure.auth import AuthService
from src.infrastructure.jwt_service import create_access_token
from src.infrastructure.llm_service import AIService
from src.infrastructure.memory_store import InMemoryStore
from src.tools.base import ToolRegistry
from src.tools.pdf_tool import PDFTool
from src.api.notification_manager import NotificationManager

load_dotenv()

logger = structlog.get_logger()


# Instancia global de almacenamiento en memoria para usuarios, conversaciones y documentos.
_store = InMemoryStore()

# Registro global de herramientas externas (plugins).
_tool_registry = ToolRegistry()

# Configuración y registro de herramientas externas y servicios globales.
credentials_path = os.getenv("GOOGLE_CALENDAR_CREDENTIALS")
calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")
calendar_timezone = os.getenv("GOOGLE_CALENDAR_TIMEZONE", "UTC")
calendar_scopes = os.getenv("GOOGLE_CALENDAR_SCOPES")
scopes = calendar_scopes.split(",") if calendar_scopes else None
from src.tools.google_calendar_tool import GoogleCalendarTool
_calendar_tool = GoogleCalendarTool(
    credentials_path=credentials_path,
    calendar_id=calendar_id,
    timezone_name=calendar_timezone,
    scopes=scopes,
)

# Herramienta para análisis de PDFs, asociada al store global.
_pdf_tool = PDFTool(_store)
# Registro de herramientas en el plugin registry.
_tool_registry.register(_calendar_tool)
_tool_registry.register(_pdf_tool)
# Servicio de IA para procesamiento de lenguaje natural.
_llm_service = AIService(
    tool_registry=_tool_registry,
    model_name=os.getenv("APIFREELLM_MODEL", "apifreellm"),
    api_key=os.getenv("APIFREELLM_API_KEY"),
)
# Gestor de conversaciones y servicios auxiliares.
_conversation_manager = ConversationManager(_store)
_auth_service = AuthService()
_notification_manager = NotificationManager()

# Casos de uso principales para inyección en endpoints.
_auth_login_use_case = AuthLoginUseCase(
    auth_service=_auth_service,
    store=_store,
    token_factory=create_access_token,
)
_conversation_use_case = ConversationUseCase(store=_store)
_document_use_case = DocumentUseCase(store=_store, pdf_tool=_pdf_tool, llm=_llm_service)
_event_use_case = EventUseCase(calendar_tool=_calendar_tool)

create_conversation_use_case = CreateConversationUseCase(
	store=_store,
	conversation_manager=_conversation_manager,
)
get_conversation_history_use_case = GetConversationHistoryUseCase(store=_store)
send_message_use_case = SendMessageUseCase(
	store=_store,
	llm=_llm_service,
	tool_registry=_tool_registry,
	conversation_manager=_conversation_manager,
)


def get_store() -> InMemoryStore:
	"""
	Devuelve la instancia global de almacenamiento en memoria.
	"""
	return _store


def get_tool_registry() -> ToolRegistry:
	"""
	Devuelve el registro global de herramientas externas (plugins).
	"""
	return _tool_registry


def get_calendar_tool() -> GoogleCalendarTool:
	"""
	Devuelve la herramienta de integración con Google Calendar.
	"""
	return _calendar_tool


def get_pdf_tool() -> PDFTool:
	"""
	Devuelve la herramienta de análisis de PDFs.
	"""
	return _pdf_tool


def get_auth_service() -> AuthService:
	"""
	Devuelve el servicio de autenticación.
	"""
	return _auth_service



def get_auth_login_use_case() -> AuthLoginUseCase:
	"""
	Devuelve el caso de uso de login de autenticación.
	"""
	return _auth_login_use_case



def get_conversation_use_case() -> ConversationUseCase:
	"""
	Devuelve el caso de uso para gestión de conversaciones.
	"""
	return _conversation_use_case



def get_document_use_case() -> DocumentUseCase:
	"""
	Devuelve el caso de uso para gestión y consulta de documentos PDF.
	"""
	return _document_use_case



def get_event_use_case() -> EventUseCase:
	"""
	Devuelve el caso de uso para gestión de eventos de calendario.
	"""
	return _event_use_case



def get_notification_manager() -> NotificationManager:
	"""
	Devuelve el gestor global de notificaciones para respuestas asíncronas.
	"""
	return _notification_manager
