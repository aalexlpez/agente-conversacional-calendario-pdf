from __future__ import annotations
import structlog
logger = structlog.get_logger()
"""Servicio LLM con soporte de API real y fallback simulado.

Nota:
	Si hay API key configurada, se llama a APIFreeLLM. Si no, se usa un mock.
"""


import asyncio
import os
import re
from typing import AsyncIterator, Dict, List, Optional

import httpx
from openai import OpenAI

from src.tools.base import ToolRegistry


def _build_prompt(
	*,
	system_prompt: str,
	messages: List[Dict[str, str]],
	last_user: str,
) -> str:
	lines: List[str] = []
	if system_prompt:
		lines.append(f"System: {system_prompt}")
	for message in messages:
		role = message.get("role", "user")
		content = message.get("content", "")
		if not content:
			continue
		lines.append(f"{role.title()}: {content}")
	prompt = last_user if not lines else "\n".join(lines)
	# Logging del prompt/contexto enviado al LLM
	conversation_id = None
	# Buscar conversation_id en los mensajes si está presente
	for message in messages:
		if "conversation_id" in message:
			conversation_id = message["conversation_id"]
			break
	logger.info("Prompt enviado al LLM", prompt=prompt, conversation_id=conversation_id)
	return prompt


async def _call_apifreellm_provider(
	*,
	api_key: Optional[str],
	base_url: str,
	model_name: str,
	system_prompt: str,
	messages: List[Dict[str, str]],
	last_user: str,
) -> str:
	if not api_key:
		return "Error LLM: API key faltante."
	prompt = _build_prompt(system_prompt=system_prompt, messages=messages, last_user=last_user)
	headers = {
		"Content-Type": "application/json",
		"Authorization": f"Bearer {api_key}",
	}
	payload = {"message": prompt}
	if model_name:
		payload["model"] = model_name

	async with httpx.AsyncClient(timeout=30.0) as client:
		response = await client.post(base_url, headers=headers, json=payload)
		if response.status_code == 401:
			return "Error LLM: API key inválida."
		if response.status_code == 429:
			return "Error LLM: rate limit. Espera 5 segundos y reintenta."
		if response.status_code == 400:
			return "Error LLM: solicitud inválida (parámetros faltantes)."
		response.raise_for_status()
		data = response.json()
		return _extract_response_text(data)


async def _call_groq_provider(
	*,
	api_key: Optional[str],
	system_prompt: str,
	messages: List[Dict[str, str]],
	last_user: str,
) -> str:
	if not api_key:
		return "Error LLM: API key faltante."
	prompt = _build_prompt(system_prompt=system_prompt, messages=messages, last_user=last_user)
	model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
	client = OpenAI(
		api_key=api_key,
		base_url="https://api.groq.com/openai/v1",
	)
	response = client.responses.create(
		input=prompt,
		model=model,
	)
	return getattr(response, "output_text", None) or str(response)


def _extract_response_text(data: object) -> str:
	if isinstance(data, dict):
		for key in ("response", "message", "content", "text", "reply"):
			value = data.get(key)
			if isinstance(value, str) and value.strip():
				return value
		# fallback por si la API devuelve otra estructura
		return str(data)
	return str(data)


class AIService:
	"""Cliente LLM con fallback simulado y streaming por chunks."""

	def __init__(
		self,
		*,
		tool_registry: Optional[ToolRegistry] = None,
		model_name: str = "apifreellm",
		chunk_size: int = 40,
		api_key: Optional[str] = None,
		base_url: str = "https://apifreellm.com/api/v1/chat",
		provider: Optional[str] = None,
	) -> None:
		self._tool_registry = tool_registry
		self._model_name = model_name
		self._chunk_size = chunk_size
		self._provider = (provider or os.getenv("LLM_PROVIDER") or "apifreellm").lower()
		self._api_key = api_key or os.getenv("APIFREELLM_API_KEY")
		self._base_url = base_url
		self._groq_api_key = os.getenv("GROQ_API_KEY")
		self._providers = {
			"apifreellm": self._call_apifreellm,
			"groq": self._call_groq,
		}

	async def generate(self, prompt: str) -> str:
		"""API simple compatible con el protocolo LLM del dominio."""
		return await self.generate_messages(system_prompt="", messages=[{"role": "user", "content": prompt}])

	async def generate_messages(
		self,
		*,
		system_prompt: str,
		messages: List[Dict[str, str]],
	) -> str:
		"""Genera una respuesta real si hay API key; si no, usa el mock."""
		last_user = self._get_last_user_message(messages)
		if not last_user:
			return "No hay mensaje de usuario para responder."

		provider_call = self._providers.get(self._provider)
		if provider_call:
			return await provider_call(
				system_prompt=system_prompt,
				messages=messages,
				last_user=last_user,
			)

		tool_response = await self._maybe_call_tool(last_user)
		if tool_response is not None:
			return tool_response

		# Respuesta simulada con contexto básico.
		context_hint = ""
		if system_prompt:
			context_hint = " Contexto aplicado."
		return f"Respuesta simulada{context_hint}: {last_user}"

	async def stream_messages(
		self,
		*,
		system_prompt: str,
		messages: List[Dict[str, str]],
	) -> AsyncIterator[str]:
		"""Devuelve la respuesta por chunks para simular streaming."""
		response = await self.generate_messages(system_prompt=system_prompt, messages=messages)
		for idx in range(0, len(response), self._chunk_size):
			await asyncio.sleep(0)  # cede el control al event loop
			yield response[idx : idx + self._chunk_size]

	async def _call_apifreellm(
		self,
		*,
		system_prompt: str,
		messages: List[Dict[str, str]],
		last_user: str,
	) -> str:
		return await _call_apifreellm_provider(
			api_key=self._api_key,
			base_url=self._base_url,
			model_name=self._model_name,
			system_prompt=system_prompt,
			messages=messages,
			last_user=last_user,
		)

	async def _call_groq(
		self,
		*,
		system_prompt: str,
		messages: List[Dict[str, str]],
		last_user: str,
	) -> str:
		return await _call_groq_provider(
			api_key=self._groq_api_key,
			system_prompt=system_prompt,
			messages=messages,
			last_user=last_user,
		)

	def _get_last_user_message(self, messages: List[Dict[str, str]]) -> str:
		for message in reversed(messages):
			if message.get("role") == "user":
				return message.get("content", "")
		return ""

	async def _maybe_call_tool(self, user_text: str) -> Optional[str]:
		"""Ejecuta una herramienta si el usuario la invoca explícitamente.

		Formato esperado:
			tool:<tool_name>:<query>
			tool:<tool_name> <query>
		"""
		match = re.match(r"^tool:(?P<name>[a-zA-Z0-9_\-]+)\s*[: ]\s*(?P<query>.+)$", user_text)
		if not match:
			return None
		if not self._tool_registry:
			return "No hay registro de herramientas disponible."

		tool_name = match.group("name").strip()
		query = match.group("query").strip()
		tool = self._tool_registry.get(tool_name)
		if not tool:
			return f"Herramienta no encontrada: {tool_name}"
		result = await tool.execute(query)
		return f"Resultado de herramienta ({tool_name}): {result}"

