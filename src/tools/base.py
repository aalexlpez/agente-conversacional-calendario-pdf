"""
Definiciones comunes para herramientas del agente.

Incluye la interfaz `BaseTool` usada por implementaciones concretas y un
`ToolRegistry` para registrar y recuperar herramientas disponibles.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Iterable, Optional


class BaseTool(ABC):
	"""Interfaz que toda herramienta debe implementar."""
	name: str

	@abstractmethod
	async def execute(self, query: str) -> str:
		"""Ejecuta un comando textual y devuelve la respuesta como string."""
		raise NotImplementedError


class ToolRegistry:
	"""Registro sencillo para descubrir herramientas por nombre."""
	def __init__(self) -> None:
		self._tools: Dict[str, BaseTool] = {}

	def register(self, tool: BaseTool) -> None:
		"""Agrega una herramienta al registro. Reemplaza si ya existía."""
		self._tools[tool.name] = tool

	def get(self, name: str) -> Optional[BaseTool]:
		"""Devuelve la herramienta registrada con el nombre dado, o None."""
		return self._tools.get(name)

	def list(self) -> Iterable[BaseTool]:
		"""Recorre todas las herramientas registradas."""
		return self._tools.values()
