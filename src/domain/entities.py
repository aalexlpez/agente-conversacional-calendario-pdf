"""Entidades básicas del dominio."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class User:
	id: str
	username: str
	full_name: Optional[str] = None
	created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Message:
	id: str
	conversation_id: str
	role: str
	content: str
	created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Conversation:
	id: str
	user_id: str
	title: Optional[str] = None
	message_ids: List[str] = field(default_factory=list)
	created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Event:
	id: str
	user_id: str
	title: str
	starts_at: datetime
	ends_at: datetime
	metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class Document:
	id: str
	user_id: str
	filename: str
	content: str
	conversation_id: Optional[str] = None
	metadata: Dict[str, str] = field(default_factory=dict)
	uploaded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

