"""Dependencias compartidas para la API (singletons en memoria)."""

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

_store = InMemoryStore()
_tool_registry = ToolRegistry()

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

_pdf_tool = PDFTool(_store)
_tool_registry.register(_calendar_tool)
_tool_registry.register(_pdf_tool)
_llm_service = AIService(
	tool_registry=_tool_registry,
	model_name=os.getenv("APIFREELLM_MODEL", "apifreellm"),
	api_key=os.getenv("APIFREELLM_API_KEY"),
)
_conversation_manager = ConversationManager(_store)
_auth_service = AuthService()
_notification_manager = NotificationManager()

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
	return _store

def get_tool_registry() -> ToolRegistry:
	return _tool_registry

def get_calendar_tool() -> GoogleCalendarTool:
	return _calendar_tool

def get_pdf_tool() -> PDFTool:
	return _pdf_tool

def get_auth_service() -> AuthService:
	return _auth_service


def get_auth_login_use_case() -> AuthLoginUseCase:
	return _auth_login_use_case


def get_conversation_use_case() -> ConversationUseCase:
	return _conversation_use_case


def get_document_use_case() -> DocumentUseCase:
	return _document_use_case


def get_event_use_case() -> EventUseCase:
	return _event_use_case


def get_notification_manager() -> NotificationManager:
	return _notification_manager
