"""InMemoryStore: almacenamiento simple en memoria usando diccionarios.

Persistencia en memoria:
	- Cada entidad (usuarios, conversaciones, mensajes, eventos, documentos)
	  se guarda en un diccionario durante la vida del proceso.
	- El contexto de conversación se reconstruye leyendo los mensajes asociados
	  al conversation_id.
	- Los eventos del calendario quedan vinculados al user_id.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from src.domain.entities import Conversation, Document, Event, Message, User


class InMemoryStore:
	def __init__(self) -> None:
		self.users: Dict[str, User] = {}
		self.conversations: Dict[str, Conversation] = {}
		self.messages: Dict[str, Message] = {}
		self.events: Dict[str, Event] = {}
		self.documents: Dict[str, Document] = {}

	def add_user(self, user: User) -> None:
		self.users[user.id] = user

	def get_user(self, user_id: str) -> Optional[User]:
		return self.users.get(user_id)

	def add_conversation(self, conversation: Conversation) -> None:
		self.conversations[conversation.id] = conversation

	def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
		return self.conversations.get(conversation_id)

	def add_message(self, message: Message) -> None:
		self.messages[message.id] = message
		conversation = self.conversations.get(message.conversation_id)
		if conversation:
			conversation.message_ids.append(message.id)
			# Persistencia del contexto: cada conversación mantiene su historial
			# de mensajes mediante message_ids.

	def list_messages_by_conversation(self, conversation_id: str) -> List[Message]:
		return [
			message
			for message in self.messages.values()
			if message.conversation_id == conversation_id
		]

	def add_event(self, event: Event) -> None:
		self.events[event.id] = event

	def list_events_by_user(self, user_id: str) -> Iterable[Event]:
		return [event for event in self.events.values() if event.user_id == user_id]

	def add_document(self, document: Document) -> None:
		self.documents[document.id] = document

	def get_document(self, document_id: str) -> Optional[Document]:
		return self.documents.get(document_id)

	def list_documents_by_user(self, user_id: str) -> List[Document]:
		return [doc for doc in self.documents.values() if doc.user_id == user_id]

	def list_documents_by_conversation(self, conversation_id: str) -> List[Document]:
		return [
			doc
			for doc in self.documents.values()
			if doc.conversation_id == conversation_id
		]

