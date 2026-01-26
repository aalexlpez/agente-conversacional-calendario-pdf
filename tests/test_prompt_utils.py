"""Pruebas para utilidades de prompt y contexto PDF."""

from datetime import datetime, timezone

from src.application.prompt_utils import build_pdf_focus_context, build_system_prompt, should_use_pdf_context
from src.domain.entities import Conversation, Document, Message, User
from src.infrastructure.memory_store import InMemoryStore


def _seed_store_with_conversation(store: InMemoryStore) -> Conversation:
	# Crea y almacena un usuario y una conversación de prueba en el store.
	user = User(id="user-1", username="alice")
	store.add_user(user)
	conversation = Conversation(id="conv-1", user_id=user.id, title="demo")
	store.add_conversation(conversation)
	return conversation


def test_build_system_prompt_includes_user_and_pdf_preview() -> None:
	# Verifica que el prompt generado incluya el usuario y una vista previa del PDF.
	store = InMemoryStore()
	conversation = _seed_store_with_conversation(store)
	doc = Document(
		id="doc-1",
		user_id="user-1",
		conversation_id=conversation.id,
		filename="manual.pdf",
		content="Linea 1\nLinea 2",
	)
	store.add_document(doc)

	prompt = build_system_prompt(
		store=store,
		user_id="user-1",
		conversation_id=conversation.id,
		pdf_focus_context=None,
	)

	assert "alice" in prompt  # El nombre de usuario debe estar en el prompt
	assert "manual.pdf" in prompt  # El nombre del PDF debe aparecer
	assert "Linea 1 Linea 2" in prompt  # El contenido del PDF debe estar normalizado


def test_should_use_pdf_context_by_keyword_and_filename() -> None:
	# Debe detectar contexto PDF por palabra clave o por nombre de archivo mencionado.
	store = InMemoryStore()
	conversation = _seed_store_with_conversation(store)
	doc = Document(
		id="doc-2",
		user_id="user-1",
		conversation_id=conversation.id,
		filename="reporte.pdf",
		content="contenido",
	)
	store.add_document(doc)

	assert should_use_pdf_context(store=store, conversation_id=conversation.id, user_text="Revisa el PDF")
	assert should_use_pdf_context(store=store, conversation_id=conversation.id, user_text="que dice reporte.pdf")


def test_should_use_pdf_context_with_recent_mentions() -> None:
	# Si el usuario mencionó PDF recientemente, debe activar el contexto PDF.
	store = InMemoryStore()
	conversation = _seed_store_with_conversation(store)
	store.add_document(
		Document(
			id="doc-3",
			user_id="user-1",
			conversation_id=conversation.id,
			filename="plan.pdf",
			content="contenido",
		)
	)
	store.add_message(
		Message(
			id="msg-1",
			conversation_id=conversation.id,
			role="user",
			content="Hablemos del pdf",
			created_at=datetime.now(timezone.utc),
		)
	)

	assert should_use_pdf_context(store=store, conversation_id=conversation.id, user_text="continua")


def test_build_pdf_focus_context_selects_latest_when_not_explicit() -> None:
	# Si no se menciona explícitamente, debe seleccionar el PDF más reciente.
	store = InMemoryStore()
	conversation = _seed_store_with_conversation(store)
	store.add_document(
		Document(
			id="doc_1",
			user_id="user-1",
			conversation_id=conversation.id,
			filename="uno.pdf",
			content="primero",
		)
	)
	store.add_document(
		Document(
			id="doc_2",
			user_id="user-1",
			conversation_id=conversation.id,
			filename="dos.pdf",
			content="segundo",
		)
	)

	context = build_pdf_focus_context(
		store=store,
		conversation_id=conversation.id,
		user_text="consulta del pdf",
	)

	assert context is not None
	assert "dos.pdf" in context
