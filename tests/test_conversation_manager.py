"""Pruebas de ConversationManager y tareas activas."""

import asyncio

import pytest

from src.application.conversation_manager import ConversationManager
from src.infrastructure.memory_store import InMemoryStore


@pytest.mark.asyncio
async def test_conversation_manager_tracks_active_and_tasks() -> None:
	"""
	Prueba la gestión de conversaciones activas y tareas asociadas:
	- Marca una conversación como activa.
	- Asocia una tarea asíncrona y verifica el seguimiento.
	- Al completar la tarea, debe reflejarse el estado correctamente.
	"""
	store = InMemoryStore()
	manager = ConversationManager(store)
	conversation = manager.create_conversation(user_id="user-1", title="demo")

	assert manager.get_active_conversation(user_id="user-1") == conversation

	# Asocia una tarea simulada y verifica el seguimiento
	task = asyncio.create_task(asyncio.sleep(0.01, result="ok"))
	manager.track_task(conversation_id=conversation.id, task=task)
	assert manager.has_pending_response(conversation_id=conversation.id)

	await task
	assert not manager.has_pending_response(conversation_id=conversation.id)
	manager.complete_task(conversation_id=conversation.id)
	assert manager.get_task(conversation_id=conversation.id) is None
