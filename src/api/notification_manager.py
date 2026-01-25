"""NotificationManager para avisos de finalización de respuestas."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Subscription:
    conversation_id: str
    queue: asyncio.Queue[str] = field(default_factory=asyncio.Queue)


class NotificationManager:
    """Gestiona subscripciones y notificaciones por conversación."""

    def __init__(self) -> None:
        self._subscriptions: Dict[str, List[Subscription]] = {}

    def subscribe(self, *, conversation_id: str) -> Subscription:
        subscription = Subscription(conversation_id=conversation_id)
        self._subscriptions.setdefault(conversation_id, []).append(subscription)
        return subscription

    def unsubscribe(self, subscription: Subscription) -> None:
        items = self._subscriptions.get(subscription.conversation_id, [])
        if subscription in items:
            items.remove(subscription)
            if not items:
                self._subscriptions.pop(subscription.conversation_id, None)

    async def notify_finished(self, *, conversation_id: str) -> None:
        for subscription in self._subscriptions.get(conversation_id, []):
            await subscription.queue.put("response_finished")
