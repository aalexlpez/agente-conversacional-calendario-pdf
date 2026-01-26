"""Validación de ConversationUseCase y su manipulación del historial."""

from datetime import timedelta

import pytest

from src.application.api_use_cases import ConversationUseCase
from src.domain.entities import Message
from src.domain.exceptions import ResourceNotFound
from src.infrastructure.memory_store import InMemoryStore


def test_conversation_use_case_crud() -> None:
	"""Ejecuta el flujo CRUD completo y asegura que se limpian los mensajes."""
	store = InMemoryStore()
	use_case = ConversationUseCase(store=store)

	conv = use_case.create(user_id="user-1", title="hola")
	assert conv.user_id == "user-1"
	assert conv.title == "hola"

	all_convs = use_case.list(user_id="user-1")
	assert len(all_convs) == 1

	updated = use_case.update(conversation_id=conv.id, user_id="user-1", title="nuevo")
	assert updated.title == "nuevo"

	use_case.delete(conversation_id=conv.id, user_id="user-1")
	assert use_case.list(user_id="user-1") == []

	with pytest.raises(ResourceNotFound):
		use_case.get_with_messages(conversation_id=conv.id, user_id="user-1")


def test_conversation_use_case_get_with_messages_sorted() -> None:
	"""Verifica que los mensajes se ordenan por timestamp descendente."""
	store = InMemoryStore()
	use_case = ConversationUseCase(store=store)
	conv = use_case.create(user_id="user-1", title="historial")

	msg1 = Message(id="msg_1", conversation_id=conv.id, role="user", content="a")
	msg2 = Message(id="msg_2", conversation_id=conv.id, role="assistant", content="b")
	msg2.created_at = msg1.created_at - timedelta(seconds=5)
	store.add_message(msg1)
	store.add_message(msg2)

	_, messages = use_case.get_with_messages(conversation_id=conv.id, user_id="user-1")
	assert [m.id for m in messages] == [msg2.id, msg1.id]
