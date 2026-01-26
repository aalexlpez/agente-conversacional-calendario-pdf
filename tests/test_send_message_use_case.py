"""Pruebas críticas para SendMessageUseCase (streaming y herramientas)."""

from __future__ import annotations

import asyncio
from typing import AsyncIterator, List

import pytest

from src.application.conversation_manager import ConversationManager
from src.application.use_cases import SendMessageUseCase, UseCaseConfig
from src.infrastructure.memory_store import InMemoryStore
from src.tools.base import BaseTool, ToolRegistry


class FakeLLM:
	"""
	LLM simulado que devuelve los chunks dados, para probar el flujo de streaming.
	"""

	def __init__(self, chunks: List[str]) -> None:
		self._chunks = chunks

	async def stream_messages(self, *, system_prompt: str, messages: List[dict]) -> AsyncIterator[str]:
		for chunk in self._chunks:
			await asyncio.sleep(0)
			yield chunk


class EchoTool(BaseTool):
	"""
	Herramienta de prueba que simplemente responde con el texto recibido.
	"""
	name = "echo"

	async def execute(self, query: str) -> str:
		return f"ok:{query}"


@pytest.mark.asyncio
async def test_send_message_use_case_streams_and_persists() -> None:
	"""
	Prueba el flujo principal de SendMessageUseCase:
	- El mensaje del usuario se almacena y se crea una conversación.
	- El LLM simulado responde en chunks (streaming).
	- El mensaje del asistente se persiste correctamente.
	"""
	store = InMemoryStore()
	manager = ConversationManager(store)
	registry = ToolRegistry()
	llm = FakeLLM(["hola", " mundo"])
	use_case = SendMessageUseCase(
		store=store,
		llm=llm,
		tool_registry=registry,
		conversation_manager=manager,
		config=UseCaseConfig(notify_on_complete=False),
	)

	chunks = [chunk async for chunk in use_case.execute(user_id="user-1", conversation_id=None, text="saludo")]
	assert "".join(chunks) == "hola mundo"
	assert len(store.conversations) == 1
	assert len(store.messages) == 2  # user + assistant
	assistant_message = list(store.messages.values())[-1]
	assert assistant_message.role == "assistant"
	assert assistant_message.content == "hola mundo"


@pytest.mark.asyncio
async def test_send_message_use_case_executes_tool() -> None:
	"""
	Prueba que SendMessageUseCase ejecuta una herramienta externa si el mensaje lo solicita:
	- El mensaje 'tool:echo:hola' debe invocar la herramienta y devolver su resultado.
	- El mensaje del asistente debe reflejar la respuesta de la herramienta.
	"""
	store = InMemoryStore()
	manager = ConversationManager(store)
	registry = ToolRegistry()
	registry.register(EchoTool())
	llm = FakeLLM(["no debe usarse"])
	use_case = SendMessageUseCase(
		store=store,
		llm=llm,
		tool_registry=registry,
		conversation_manager=manager,
		config=UseCaseConfig(notify_on_complete=False),
	)

	chunks = [chunk async for chunk in use_case.execute(user_id="user-1", conversation_id=None, text="tool:echo:hola")]
	response = "".join(chunks)
	assert "Resultado de herramienta (echo): ok:hola" in response
	assert len(store.messages) == 2
	assistant_message = list(store.messages.values())[-1]
	assert assistant_message.content == response
