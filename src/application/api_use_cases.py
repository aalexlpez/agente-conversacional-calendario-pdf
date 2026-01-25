"""Casos de uso para la capa de API (sin lógica de transporte)."""

from __future__ import annotations

import asyncio
import os
import tempfile
from datetime import datetime
from typing import List, Optional

from src.domain.entities import Conversation, Document, Event, Message, User
from src.domain.exceptions import (
	AuthServiceUnavailable,
	ExternalServiceError,
	InvalidCredentials,
	ResourceNotFound,
	UserNotFound,
)
from src.domain.interfaces import LLM
from src.infrastructure.auth import AuthService
from src.infrastructure.memory_store import InMemoryStore
from src.application.prompt_utils import build_document_query_prompt
from src.tools.google_calendar_tool import GoogleCalendarTool
from src.tools.pdf_tool import PDFTool


class AuthLoginUseCase:
	"""Autenticación y emisión de token JWT."""

	def __init__(self, *, auth_service: AuthService, store: InMemoryStore, token_factory) -> None:
		self._auth_service = auth_service
		self._store = store
		self._token_factory = token_factory

	def execute(self, *, username: str, password: str) -> str:
		try:
			ok = self._auth_service.authenticate(username, password)
		except AttributeError as exc:
			raise AuthServiceUnavailable("Servicio de autenticación no disponible") from exc
		except AuthService.AuthError as exc:
			raise UserNotFound(str(exc)) from exc
		if not ok:
			raise InvalidCredentials("Credenciales inválidas")

		if not self._store.get_user(username):
			user = User(id=username, username=username)
			self._store.add_user(user)

		return self._token_factory({"sub": username})


class ConversationUseCase:
	"""Casos de uso CRUD para conversaciones."""

	def __init__(self, *, store: InMemoryStore) -> None:
		self._store = store

	def create(self, *, user_id: str, title: Optional[str] = None) -> Conversation:
		conversation = Conversation(
			id=f"conv_{len(self._store.conversations) + 1}",
			user_id=user_id,
			title=title,
		)
		self._store.add_conversation(conversation)
		return conversation

	def list(self, *, user_id: str) -> List[Conversation]:
		return [c for c in self._store.conversations.values() if c.user_id == user_id]

	def get_with_messages(self, *, conversation_id: str, user_id: str) -> tuple[Conversation, List[Message]]:
		conversation = self._store.get_conversation(conversation_id)
		if not conversation or conversation.user_id != user_id:
			raise ResourceNotFound("Conversación no encontrada")
		messages = sorted(
			self._store.list_messages_by_conversation(conversation_id),
			key=lambda msg: msg.created_at,
		)
		return conversation, messages

	def update(self, *, conversation_id: str, user_id: str, title: Optional[str]) -> Conversation:
		conversation = self._store.get_conversation(conversation_id)
		if not conversation or conversation.user_id != user_id:
			raise ResourceNotFound("Conversación no encontrada")
		if title is not None:
			conversation.title = title
		return conversation

	def delete(self, *, conversation_id: str, user_id: str) -> None:
		conversation = self._store.get_conversation(conversation_id)
		if not conversation or conversation.user_id != user_id:
			raise ResourceNotFound("Conversación no encontrada")
		self._store.conversations.pop(conversation_id, None)


class DocumentUseCase:
	"""Casos de uso para documentos PDF."""

	def __init__(self, *, store: InMemoryStore, pdf_tool: PDFTool, llm: Optional[LLM] = None) -> None:
		self._store = store
		self._pdf_tool = pdf_tool
		self._llm = llm

	async def upload(self, *, user_id: str, conversation_id: str, filename: str, content: bytes) -> Document:
		conversation = self._store.get_conversation(conversation_id)
		if not conversation or conversation.user_id != user_id:
			raise ResourceNotFound("Conversación no encontrada")

		extracted = ""
		temp_path: Optional[str] = None
		try:
			with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
				temp_file.write(content)
				temp_file.flush()
				temp_path = temp_file.name
			# Extracción de texto es bloqueante: se envía a un hilo.
			extracted = await asyncio.to_thread(self._pdf_tool.extract_text, temp_path)
		except Exception:
			extracted = ""
		finally:
			try:
				if temp_path:
					os.unlink(temp_path)
			except Exception:
				pass

		document = self._pdf_tool.add_document(
			user_id=user_id,
			conversation_id=conversation_id,
			filename=filename,
			content=extracted,
		)
		return document

	def list(self, *, user_id: str, conversation_id: Optional[str] = None) -> List[Document]:
		if conversation_id:
			conversation = self._store.get_conversation(conversation_id)
			if not conversation or conversation.user_id != user_id:
				raise ResourceNotFound("Conversación no encontrada")
			return self._store.list_documents_by_conversation(conversation_id)
		return self._store.list_documents_by_user(user_id)

	async def query(self, *, user_id: str, conversation_id: str, document_id: str, keyword: str) -> str:
		conversation = self._store.get_conversation(conversation_id)
		if not conversation or conversation.user_id != user_id:
			raise ResourceNotFound("Conversación no encontrada")
		document = self._store.get_document(document_id)
		if (
			not document
			or document.user_id != user_id
			or document.conversation_id != conversation_id
		):
			raise ResourceNotFound("Documento no encontrado")
		if not self._llm:
			return await self._pdf_tool.execute(f"search:{document_id}:{keyword}")
		content = (document.content or "").strip()
		if not content:
			return (
				"No se pudo extraer texto legible del PDF. "
				"Si es un PDF escaneado, sube una versión con OCR."
			)
		prompt = build_document_query_prompt(
			filename=document.filename or "documento",
			content=content,
			question=keyword,
		)
		return await self._llm.generate(prompt)


class EventUseCase:
	"""Casos de uso CRUD para eventos de calendario."""

	def __init__(self, *, calendar_tool: GoogleCalendarTool) -> None:
		self._calendar_tool = calendar_tool

	def create(self, *, user_id: str, title: str, starts_at: datetime, ends_at: datetime) -> Event:
		try:
			return self._calendar_tool.create_event(
				user_id=user_id,
				title=title,
				starts_at=starts_at,
				ends_at=ends_at,
			)
		except RuntimeError as exc:
			raise ExternalServiceError(str(exc)) from exc

	def list(self, *, user_id: str) -> List[Event]:
		try:
			return self._calendar_tool.list_events(user_id)
		except RuntimeError as exc:
			raise ExternalServiceError(str(exc)) from exc

	def get(self, *, event_id: str, user_id: str) -> Event:
		try:
			event = self._calendar_tool.get_event(event_id=event_id, user_id=user_id)
		except RuntimeError as exc:
			raise ExternalServiceError(str(exc)) from exc
		if not event:
			raise ResourceNotFound("Evento no encontrado")
		return event

	def update(
		self,
		*,
		event_id: str,
		user_id: str,
		title: Optional[str],
		starts_at: Optional[datetime],
		ends_at: Optional[datetime],
	) -> Event:
		try:
			updated = self._calendar_tool.update_event(
				event_id=event_id,
				title=title,
				starts_at=starts_at,
				ends_at=ends_at,
			)
		except RuntimeError as exc:
			raise ExternalServiceError(str(exc)) from exc
		if not updated:
			raise ResourceNotFound("Evento no encontrado")
		if not updated.user_id:
			updated.user_id = user_id
		return updated

	def delete(self, *, event_id: str, user_id: str) -> None:
		try:
			deleted = self._calendar_tool.delete_event(event_id)
		except RuntimeError as exc:
			raise ExternalServiceError(str(exc)) from exc
		if not deleted:
			raise ResourceNotFound("Evento no encontrado")
