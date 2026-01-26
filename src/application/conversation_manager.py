"""Gestión de múltiples conversaciones activas.

Mantiene el estado en memoria y permite cambiar de conversación
mientras hay respuestas en curso.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.domain.entities import Conversation
from src.infrastructure.memory_store import InMemoryStore


@dataclass
class ConversationState:
	"""Estado ligero de una conversación activa con referencia a su tarea pendiente."""
	conversation_id: str
	pending_task: Optional[asyncio.Task[str]] = None
	updated_at: float = field(default_factory=lambda: asyncio.get_event_loop().time())


	# Esta clase coordina conversaciones activas y tareas pendientes por conversación.
	# Aunque la mayoría de métodos son síncronos, está diseñada para usarse en flujos asíncronos
	# y gestionar tareas concurrentes (asyncio.Task) de forma segura.
class ConversationManager:
	"""Gestiona conversaciones activas y tareas pendientes para cada usuario."""

	def __init__(self, store: InMemoryStore) -> None:
		"""Inicializa el manager con el almacenamiento en memoria compartido."""
		self._store = store
		self._active_by_user: Dict[str, ConversationState] = {}
		self._tasks_by_conversation: Dict[str, asyncio.Task[str]] = {}

	def create_conversation(self, *, user_id: str, title: Optional[str] = None) -> Conversation:
		"""Crea y marca como activa una nueva conversación para el usuario."""
		conversation = Conversation(
			id=f"conv_{len(self._store.conversations) + 1}",
			user_id=user_id,
			title=title,
		)
		self._store.add_conversation(conversation)
		self.set_active_conversation(user_id=user_id, conversation_id=conversation.id)
		return conversation

	def set_active_conversation(self, *, user_id: str, conversation_id: str) -> None:
		"""Asigna una conversación como la activa del usuario."""
		state = ConversationState(conversation_id=conversation_id)
		self._active_by_user[user_id] = state

	def get_active_conversation(self, *, user_id: str) -> Optional[Conversation]:
		"""Devuelve la conversación activa del usuario o None si no hay ninguna."""
		state = self._active_by_user.get(user_id)
		if not state:
			return None
		return self._store.get_conversation(state.conversation_id)

	def list_active_conversations(self) -> List[Conversation]:
		"""Enumera las conversaciones marcadas como activas (para monitorización)."""
		return [
			conversation
			for state in self._active_by_user.values()
			if (conversation := self._store.get_conversation(state.conversation_id))
		]

	def track_task(self, *, conversation_id: str, task: asyncio.Task[str]) -> None:
		"""Asocia la tarea de respuesta actual con una conversación."""
		self._tasks_by_conversation[conversation_id] = task

	def get_task(self, *, conversation_id: str) -> Optional[asyncio.Task[str]]:
		"""Recupera la tarea pendiente (si existe) de una conversación."""
		return self._tasks_by_conversation.get(conversation_id)

	def complete_task(self, *, conversation_id: str) -> None:
		"""Marca como completada una conversación eliminando su tarea."""
		self._tasks_by_conversation.pop(conversation_id, None)

	def has_pending_response(self, *, conversation_id: str) -> bool:
		"""Indica si una conversación tiene una respuesta aún en curso."""
		task = self._tasks_by_conversation.get(conversation_id)
		return bool(task and not task.done())
