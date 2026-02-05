"""Utilidades para construir prompts y payloads de mensajes."""

from __future__ import annotations
import structlog
logger = structlog.get_logger()

from typing import Dict, List, Optional

import re

from src.infrastructure.memory_store import InMemoryStore

def build_message_payload(
	*,
	store: InMemoryStore,
	conversation_id: str,
	max_history_messages: int,
) -> List[Dict[str, str]]:
	"""Construye el historial que se enviará al LLM, limitando mensajes recientes."""
	messages = store.list_messages_by_conversation(conversation_id)
	recent = messages[-max_history_messages:]
	return [{"role": msg.role, "content": msg.content} for msg in recent]


def build_system_prompt(
	*,
	store: InMemoryStore,
	user_id: str,
	conversation_id: str,
	pdf_focus_context: Optional[str] = None,
) -> str:
	"""Construye el prompt del sistema incluyendo contexto de conversación y PDFs."""
	user = store.get_user(user_id)
	logger.info("build_system_prompt: buscando usuario", user_id=user_id, store_user_ids=list(store.users.keys()))
	user_name = user.username if user else "desconocido"
	conversation_docs = store.list_documents_by_conversation(conversation_id)
	if conversation_docs:
		doc_lines = []
		for doc in conversation_docs:
			preview = _sanitize_pdf_text((doc.content or "").strip())
			preview = preview.replace("\n", " ")
			if len(preview) > 500:
				preview = preview[:500] + "..."
			doc_lines.append(f"- {doc.filename}: {preview}")
		doc_context = "\n".join(doc_lines)
	else:
		doc_context = "(sin PDFs asociados a esta conversación)"

	if pdf_focus_context:
		pdf_focus_block = (
			"\n\nContexto PDF prioritario (usa esto para responder preguntas sobre el PDF):\n"
			f"{pdf_focus_context}"
		)
	else:
		pdf_focus_block = ""

	logger.info(
		"build_system_prompt: contexto PDF",
		conversation_id=conversation_id,
		pdfs_count=len(conversation_docs),
		pdf_focus_included=bool(pdf_focus_context),
		pdf_focus_preview=(pdf_focus_context or "")[:300],
	)
	return (
		"Eres un agente conversacional para gestión de calendario. "
		"Usa el contexto de la conversación para responder de forma coherente. "
		f"Usuario: {user_name}. Conversación: {conversation_id}. "
		f"PDFs en esta conversación:\n{doc_context}"
		f"{pdf_focus_block}"
	)


def is_pdf_query(text: str) -> bool:
	"""Detecta si el texto del usuario menciona que quiere hablar de un PDF."""
	if not text:
		return False
	pattern = r"\b(pdf|documento|archivo|fichero|adjunto)\b"
	return re.search(pattern, text.lower()) is not None


def _sanitize_pdf_text(text: str) -> str:
	"""Normaliza texto de PDF eliminando saltos de línea y caracteres invisibles."""
	if not text:
		return ""
	cleaned = "".join(ch if ch.isprintable() else " " for ch in text)
	cleaned = re.sub(r"\s+", " ", cleaned).strip()
	return cleaned


def should_use_pdf_context(
	*,
	store: InMemoryStore,
	conversation_id: str,
	user_text: str,
) -> bool:
	"""Determina si el mensaje debe consumir contexto del PDF asociado."""
	if is_pdf_query(user_text):
		return True
	documents = store.list_documents_by_conversation(conversation_id)
	if not documents:
		return False
	recent = store.list_messages_by_conversation(conversation_id)[-3:]
	if any(is_pdf_query(msg.content) for msg in recent if msg.content):
		return True
	lower = user_text.lower()
	for doc in documents:
		if doc.filename and doc.filename.lower() in lower:
			return True
	return False


def build_pdf_focus_context(
	*,
	store: InMemoryStore,
	conversation_id: str,
	user_text: str,
	max_chars: int = 2000,
) -> Optional[str]:
	"""Construye un bloque de contexto prioritario extraído del PDF más relevante."""
	if not should_use_pdf_context(store=store, conversation_id=conversation_id, user_text=user_text):
		return None
	documents = store.list_documents_by_conversation(conversation_id)
	if not documents:
		return None

	lower = user_text.lower()
	selected = None
	for doc in documents:
		if doc.filename and doc.filename.lower() in lower:
			selected = doc
			break

	if selected is None:
		def _doc_sort_key(doc):
			match = re.search(r"(\d+)$", doc.id)
			return int(match.group(1)) if match else 0
			
		selected = sorted(documents, key=_doc_sort_key)[-1]

	content = _sanitize_pdf_text((selected.content or "").strip())
	if not content:
		logger.warning(
			"build_pdf_focus_context: sin texto legible",
			conversation_id=conversation_id,
			document_id=selected.id,
			filename=selected.filename,
		)
		return (
			f"Documento: {selected.filename}\n"
			"(No se pudo extraer texto legible del PDF. Si es un PDF escaneado, "
			"sube una versión con OCR.)"
		)
	if len(content) > max_chars:
		content = content[:max_chars] + "..."
	logger.info(
		"build_pdf_focus_context: seleccionado",
		conversation_id=conversation_id,
		document_id=selected.id,
		filename=selected.filename,
		content_length=len(content),
	)
	return f"Documento: {selected.filename}\n{content}"


def build_document_query_prompt(
	*,
	filename: str,
	content: str,
	question: str,
	max_chars: int = 4000,
) -> str:
	"""Construye el prompt que se enviará al LLM para responder preguntas sobre el PDF."""
	cleaned = _sanitize_pdf_text(content or "")
	if len(cleaned) > max_chars:
		cleaned = cleaned[:max_chars] + "..."
	return (
		"Responde la pregunta usando únicamente el contenido del documento. Analiza el contexto del documento para dar respuesta"
		"Si no consigues información para responder la pregunta, entonces responde: "
		"'No se encontró información en el documento.'\n\n"
		f"Documento: {filename}\n"
		f"Contenido:\n{cleaned}\n\n"
		f"Pregunta: {question}"
	)
