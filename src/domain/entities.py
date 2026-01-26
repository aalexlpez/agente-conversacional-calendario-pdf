"""Entidades centrales del dominio del agente conversacional.

Cada dataclass representa un agregado o valor que se comparte entre capas,
manteniendo campos inmutables (como IDs) y timestamps UTC para trazabilidad.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class User:
	"""Representa al usuario autenticado dentro del agente."""
	id: str
	username: str
	full_name: Optional[str] = None
	created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Message:
	"""Mensaje que intercambian usuario y asistente dentro de una conversación."""
	id: str
	conversation_id: str
	role: str
	content: str
	created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Conversation:
	"""Agrupa un historial de mensajes para un usuario y permite títulos opcionales."""
	id: str
	user_id: str
	title: Optional[str] = None
	message_ids: List[str] = field(default_factory=list)
	created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Event:
	"""Evento de calendario asociado a un usuario con metadata arbitraria."""
	id: str
	user_id: str
	title: str
	starts_at: datetime
	ends_at: datetime
	metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class Document:
	"""Representa un PDF subido, con texto extraído y metadatos."""
	id: str
	user_id: str
	filename: str
	content: str
	conversation_id: Optional[str] = None
	metadata: Dict[str, str] = field(default_factory=dict)
	uploaded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

