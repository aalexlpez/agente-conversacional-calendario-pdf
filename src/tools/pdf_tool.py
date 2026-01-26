"""
Herramienta básica para extracción y búsqueda en PDFs.

Usa pdfminer.six para extraer texto, almacena el contenido en memoria y permite
búsquedas de palabras clave mediante queries textuales.
"""

from __future__ import annotations

import os
import re

import structlog

from src.domain.entities import Document
from src.infrastructure.memory_store import InMemoryStore
from src.tools.base import BaseTool



class PDFTool(BaseTool):
	"""Herramienta que extrae texto y busca palabras clave en documentos PDF."""
	name = "pdf"

	logger = structlog.get_logger()

	def __init__(self, store: InMemoryStore) -> None:
		"""Recibe la instancia de memoria donde guardará los Documentos."""
		self._store = store

	def add_document(
		self,
		*,
		user_id: str,
		conversation_id: str,
		filename: str,
		content: str,
	) -> Document:
		"""Crea una entidad Document y la persiste en el InMemoryStore."""
		doc = Document(
			id=f"doc_{len(self._store.documents) + 1}",
			user_id=user_id,
			conversation_id=conversation_id,
			filename=filename,
			content=content,
		)
		self._store.add_document(doc)
		return doc

	def extract_text(self, file_path: str) -> str:
		"""Extrae texto del PDF usando pdfminer.six e informa el resultado."""
		file_size = None
		try:
			file_size = os.path.getsize(file_path)
		except OSError:
			file_size = None

		self.logger.info(
			"pdf_tool: inicio extracción",
			file_path=file_path,
			file_size=file_size,
		)
		try:
			from pdfminer.high_level import extract_text as pdfminer_extract_text
		except ImportError as exc:
			self.logger.error(
				"pdf_tool: pdfminer.six no disponible",
				file_path=file_path,
				error=str(exc),
			)
			raise ImportError("pdfminer.six es requerido para extracción de PDFs") from exc

		try:
			text = pdfminer_extract_text(file_path) or ""
			self.logger.info(
				"pdf_tool: extracción completada",
				file_path=file_path,
				text_length=len(text),
			)
			if not text.strip():
				self.logger.warning(
					"pdf_tool: extracción vacía",
					file_path=file_path,
					file_size=file_size,
				)
			return text
		except Exception as exc:
			self.logger.exception(
				"pdf_tool: error en extracción",
				file_path=file_path,
				file_size=file_size,
				text_length=0,
				error=str(exc),
			)
			return ""

	def search_keyword(self, text: str, keyword: str) -> int:
		"""Cuenta coincidencias de `keyword` en el texto con sensibilidad reducida."""
		pattern = re.escape(keyword)
		return len(re.findall(pattern, text, flags=re.IGNORECASE))

	async def execute(self, query: str) -> str:
		"""Permite buscar palabras clave en documentos previamente cargados.

		Formato esperado: 'search:<document_id>:<keyword>'
		"""
		if not query.startswith("search:"):
			return "Formato inválido. Usa search:<document_id>:<keyword>"
		_, rest = query.split("search:", 1)
		try:
			document_id, keyword = rest.split(":", 1)
		except ValueError:
			return "Formato inválido. Usa search:<document_id>:<keyword>"
		document = self._store.get_document(document_id.strip())
		if not document:
			return "Documento no encontrado"
		count = self.search_keyword(document.content, keyword.strip())
		return f"Coincidencias: {count}"
