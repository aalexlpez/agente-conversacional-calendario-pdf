
"""
Módulo NotificationManager para avisos de finalización de respuestas asíncronas.

Permite gestionar subscripciones y notificaciones por conversación, facilitando la comunicación en tiempo real entre el backend y los clientes (por ejemplo, para avisar que una respuesta está lista).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Dict, List



@dataclass
class Subscription:
    """
    Representa una subscripción a notificaciones para una conversación específica.
    Cada subscripción tiene una cola asíncrona para recibir eventos.
    """
    conversation_id: str
    queue: asyncio.Queue[str] = field(default_factory=asyncio.Queue)



class NotificationManager:
    """
    Gestiona subscripciones y notificaciones por conversación.

    Permite a los clientes suscribirse a eventos de finalización de respuestas para una conversación específica.
    Cuando una respuesta está lista, se notifica a todos los suscriptores mediante colas asíncronas.
    """

    def __init__(self) -> None:
        # Diccionario de listas de subscripciones por conversación.
        self._subscriptions: Dict[str, List[Subscription]] = {}

    def subscribe(self, *, conversation_id: str) -> Subscription:
        """
        Crea y registra una subscripción para una conversación.
        Returns la subscripción creada.
        """
        subscription = Subscription(conversation_id=conversation_id)
        self._subscriptions.setdefault(conversation_id, []).append(subscription)
        return subscription

    def unsubscribe(self, subscription: Subscription) -> None:
        """
        Elimina una subscripción existente de la conversación correspondiente.
        """
        items = self._subscriptions.get(subscription.conversation_id, [])
        if subscription in items:
            items.remove(subscription)
            if not items:
                self._subscriptions.pop(subscription.conversation_id, None)

    async def notify_finished(self, *, conversation_id: str) -> None:
        """
        Notifica a todos los suscriptores de una conversación que la respuesta ha finalizado.
        """
        for subscription in self._subscriptions.get(conversation_id, []):
            await subscription.queue.put("response_finished")
