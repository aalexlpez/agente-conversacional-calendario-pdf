import pytest

from src.application.api_use_cases import DocumentUseCase
from src.domain.entities import Conversation
from src.domain.exceptions import ResourceNotFound
from src.infrastructure.memory_store import InMemoryStore
from src.tools.pdf_tool import PDFTool


@pytest.mark.asyncio
async def test_document_use_case_query_success() -> None:
	store = InMemoryStore()
	pdf_tool = PDFTool(store)
	use_case = DocumentUseCase(store=store, pdf_tool=pdf_tool)

	conv_id = "conv-1"
	store.add_conversation(
		conversation=Conversation(
			id=conv_id,
			user_id="user-1",
			title=None,
		),
	)
	doc = pdf_tool.add_document(
		user_id="user-1",
		conversation_id=conv_id,
		filename="doc.pdf",
		content="Hola mundo. Hola agente.",
	)

	result = await use_case.query(
		user_id="user-1",
		conversation_id=conv_id,
		document_id=doc.id,
		keyword="hola",
	)

	assert "Coincidencias" in result


@pytest.mark.asyncio
async def test_document_use_case_query_not_found() -> None:
	store = InMemoryStore()
	pdf_tool = PDFTool(store)
	use_case = DocumentUseCase(store=store, pdf_tool=pdf_tool)

	store.add_conversation(
		conversation=Conversation(
			id="conv-1",
			user_id="user-1",
			title=None,
		),
	)

	with pytest.raises(ResourceNotFound):
		await use_case.query(
			user_id="user-1",
			conversation_id="conv-1",
			document_id="doc_999",
			keyword="hola",
		)
