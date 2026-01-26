"""Exposición directa del registro de herramientas para inyección en la API.

Este módulo permite mantener un único punto de importación para ToolRegistry,
favoreciendo la inyección de plugins desde la capa de infraestructura o la API.
"""

from __future__ import annotations

from src.tools.base import ToolRegistry

__all__ = ["ToolRegistry"]
