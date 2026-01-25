"""BaseTool abstracta y registro de herramientas."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Iterable, Optional


class BaseTool(ABC):
	name: str

	@abstractmethod
	async def execute(self, query: str) -> str:
		"""Ejecuta la herramienta con un query en texto."""
		raise NotImplementedError


class ToolRegistry:
	def __init__(self) -> None:
		self._tools: Dict[str, BaseTool] = {}

	def register(self, tool: BaseTool) -> None:
		self._tools[tool.name] = tool

	def get(self, name: str) -> Optional[BaseTool]:
		return self._tools.get(name)

	def list(self) -> Iterable[BaseTool]:
		return self._tools.values()
