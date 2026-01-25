"""Protocols abstractos para repositorios, herramientas externas y LLM."""

from __future__ import annotations

from typing import Iterable, Optional, Protocol, TypeVar

T = TypeVar("T")


class Repository(Protocol[T]):
	def add(self, item: T) -> None: ...

	def get(self, item_id: str) -> Optional[T]: ...

	def list(self) -> Iterable[T]: ...


class Tool(Protocol):
	name: str

	async def execute(self, query: str) -> str: ...


class LLM(Protocol):
	async def generate(self, prompt: str) -> str: ...

