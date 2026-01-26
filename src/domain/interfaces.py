"""Protocols abstractos para repositorios, herramientas externas y LLM."""

from __future__ import annotations

from typing import Iterable, Optional, Protocol, TypeVar

T = TypeVar("T")


class Repository(Protocol[T]):
	"""Contrato básico que admiten los almacenes de entidades."""
	def add(self, item: T) -> None: ...

	def get(self, item_id: str) -> Optional[T]: ...

	def list(self) -> Iterable[T]: ...


class Tool(Protocol):
	"""Representa una herramienta externa invocable por el agente."""
	name: str

	async def execute(self, query: str) -> str: ...


class LLM(Protocol):
	"""Interfaz mínima que debe exponer un servicio de modelo de lenguaje."""
	async def generate(self, prompt: str) -> str: ...

