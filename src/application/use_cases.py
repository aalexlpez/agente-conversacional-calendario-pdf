"""Casos de uso core del agente conversacional.

Persistencia:
	Todas las entidades se almacenan en memoria mediante InMemoryStore.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from typing import AsyncIterator, List, Optional

import structlog

from src.domain.entities import Conversation, Message
from src.application.prompt_utils import build_message_payload, build_system_prompt, build_pdf_focus_context, should_use_pdf_context
from src.infrastructure.llm_service import AIService
from src.infrastructure.memory_store import InMemoryStore
from src.tools.base import ToolRegistry
from src.application.conversation_manager import ConversationManager
from src.application.calendar_nlp import maybe_handle_calendar_llm

logger = structlog.get_logger()


@dataclass
class UseCaseConfig:
	"""Configuración opcional de parámetros compartidos entre casos de uso."""
	max_history_messages: int = 10
	notify_on_complete: bool = True


class CreateConversationUseCase:
	"""Caso de uso para crear conversaciones nuevas y mantener la consistencia."""
	def __init__(self, *, store: InMemoryStore, conversation_manager: ConversationManager) -> None:
		self._store = store
		self._conversation_manager = conversation_manager

	def execute(self, *, user_id: str, title: Optional[str] = None) -> Conversation:
		"""Delegar la creación al ConversationManager y devolver la conversación creada."""
		return self._conversation_manager.create_conversation(user_id=user_id, title=title)


class GetConversationHistoryUseCase:
	"""Caso de uso para consultar el historial de mensajes de una conversación."""
	def __init__(self, *, store: InMemoryStore) -> None:
		self._store = store

	def execute(self, *, conversation_id: str, limit: Optional[int] = None) -> List[Message]:
		"""Devuelve los últimos mensajes de la conversación, con límite opcional."""
		messages = self._store.list_messages_by_conversation(conversation_id)
		return messages[-limit:] if limit else messages



# Esta clase orquesta el flujo principal de mensajes del agente.
# Es asíncrona porque puede involucrar operaciones de red (LLM, herramientas externas)
# y debe permitir streaming de respuestas y concurrencia sin bloquear el event loop.
class SendMessageUseCase:
	"""Orquesta el flujo de mensajes del agente con streaming y herramientas externas."""

	def __init__(
		self,
		*,
		store: InMemoryStore,
		llm: AIService,
		tool_registry: ToolRegistry,
		conversation_manager: ConversationManager,
		config: Optional[UseCaseConfig] = None,
		) -> None:
		"""Construye el caso de uso con dependencias inyectadas y configuración opcional."""
		self._store = store
		self._llm = llm
		self._tool_registry = tool_registry
		self._conversation_manager = conversation_manager
		self._config = config or UseCaseConfig()

	async def execute(
		self,
		*,
		user_id: str,
		conversation_id: Optional[str],
		text: str,
	) -> AsyncIterator[str]:
		# Este método es asíncrono porque puede involucrar llamadas a servicios externos (LLM, tools)
		# y debe permitir streaming de respuestas sin bloquear el event loop.
		try:
			conversation = self._resolve_conversation(user_id=user_id, conversation_id=conversation_id)
			self._conversation_manager.set_active_conversation(user_id=user_id, conversation_id=conversation.id)
		except Exception as exc:
			logger.exception("send_message: error resolviendo conversación", error=str(exc))
			yield "Error interno al iniciar la conversación. Intenta nuevamente."
			if self._config.notify_on_complete:
				yield "\n[Respuesta finalizada]"
			return

		user_message = Message(
			id=f"msg_{len(self._store.messages) + 1}",
			conversation_id=conversation.id,
			role="user",
			content=text,
		)
		self._store.add_message(user_message)

		# 1) Ejecutar tool si el usuario la invoca explícitamente.
		# Si el usuario invoca explícitamente una herramienta, la ejecutamos de forma asíncrona.
		try:
			tool_response = await self._maybe_call_tool(text)
		except Exception as exc:
			logger.exception("send_message: error ejecutando tool", error=str(exc))
			tool_response = "Ocurrió un error al ejecutar la herramienta solicitada."
		if tool_response is not None:
			await self._persist_assistant_message(conversation.id, tool_response)
			yield tool_response
			if self._config.notify_on_complete:
				yield "\n[Respuesta finalizada]"
			return

		# 1.1) Interpretación de lenguaje natural para calendario.
		# Si el mensaje no es sobre PDF, intentamos extraer intención de calendario usando LLM (async).
		if not should_use_pdf_context(store=self._store, conversation_id=conversation.id, user_text=text):
			messages_payload = build_message_payload(
				store=self._store,
				conversation_id=conversation.id,
				max_history_messages=self._config.max_history_messages,
			)
			# Llamada asíncrona al parser de intención de calendario (puede involucrar LLM externo).
			try:
				llm_calendar_response = await maybe_handle_calendar_llm(
					text=text,
					tool_registry=self._tool_registry,
					user_id=user_id,
					llm=self._llm,
					messages=messages_payload,
					store=self._store,
					conversation_id=conversation.id,
				)
			except Exception as exc:
				logger.exception("send_message: error calendario", error=str(exc))
				llm_calendar_response = "No pude procesar la acción de calendario por un error interno."
			if llm_calendar_response is not None:
				await self._persist_assistant_message(conversation.id, llm_calendar_response)
				yield llm_calendar_response
				if self._config.notify_on_complete:
					yield "\n[Respuesta finalizada]"
				return

		# 2) Llamar al LLM con contexto + historial.
		# Si el mensaje es sobre PDF, construimos el contexto PDF prioritario (sincrónico, rápido).
		pdf_focus_context = build_pdf_focus_context(
			store=self._store,
			conversation_id=conversation.id,
			user_text=text,
		)
		# Construimos el system prompt para el LLM, incluyendo contexto PDF si aplica.
		system_prompt = build_system_prompt(
			store=self._store,
			user_id=user_id,
			conversation_id=conversation.id,
			pdf_focus_context=pdf_focus_context,
		)
		logger.info(
			"send_message: system_prompt listo",
			conversation_id=conversation.id,
			pdf_focus_included=bool(pdf_focus_context),
			pdf_focus_preview=(pdf_focus_context or "")[:300],
		)
		messages_payload = build_message_payload(
			store=self._store,
			conversation_id=conversation.id,
			max_history_messages=self._config.max_history_messages,
		)

		assistant_content = ""
		# Streaming asíncrono de la respuesta del LLM: permite enviar la respuesta al usuario en tiempo real.
		try:
			async for chunk in self._llm.stream_messages(
				system_prompt=system_prompt,
				messages=messages_payload,
			):
				assistant_content += chunk
				yield chunk
				await asyncio.sleep(0)
		except Exception as exc:
			logger.exception("send_message: error LLM", error=str(exc))
			error_message = "Ocurrió un error al generar la respuesta. Intenta nuevamente."
			await self._persist_assistant_message(conversation.id, error_message)
			yield error_message
			if self._config.notify_on_complete:
				yield "\n[Respuesta finalizada]"
			return

		# Guardamos la respuesta del asistente en memoria (async por consistencia, aunque sea rápido).
		await self._persist_assistant_message(conversation.id, assistant_content)

		if self._config.notify_on_complete:
			yield "\n[Respuesta finalizada]"

	def _resolve_conversation(self, *, user_id: str, conversation_id: Optional[str]) -> Conversation:
		"""Identifica o crea la conversación que se debe usar para el mensaje."""
		if conversation_id:
			conversation = self._store.get_conversation(conversation_id)
			if conversation:
				return conversation
			# si no existe, crear una nueva
			return self._conversation_manager.create_conversation(user_id=user_id)
		active = self._conversation_manager.get_active_conversation(user_id=user_id)
		if active:
			return active
		return self._conversation_manager.create_conversation(user_id=user_id)


	# Persistencia asíncrona del mensaje del asistente (por consistencia y para futuras extensiones I/O).
	async def _persist_assistant_message(self, conversation_id: str, content: str) -> None:
		"""Guarda mensajes generados por el asistente en memoria."""
		assistant_message = Message(
			id=f"msg_{len(self._store.messages) + 1}",
			conversation_id=conversation_id,
			role="assistant",
			content=content,
		)
		self._store.add_message(assistant_message)

	# Llamada asíncrona a herramientas externas (pueden ser I/O o APIs de terceros).
	async def _maybe_call_tool(self, user_text: str) -> Optional[str]:
		"""Invoca herramientas externas cuando el usuario lo solicita mediante el prefijo tool:."""
		match = re.match(r"^tool:(?P<name>[a-zA-Z0-9_\-]+)\s*[: ]\s*(?P<query>.+)$", user_text)
		if not match:
			return None
		tool_name = match.group("name").strip()
		query = match.group("query").strip()
		tool = self._tool_registry.get(tool_name)
		if not tool:
			return f"Herramienta no encontrada: {tool_name}"
		try:
			result = await tool.execute(query)
			return f"Resultado de herramienta ({tool_name}): {result}"
		except Exception as exc:
			logger.exception("send_message: error en tool", tool=tool_name, error=str(exc))
			return f"Error al ejecutar la herramienta {tool_name}."
