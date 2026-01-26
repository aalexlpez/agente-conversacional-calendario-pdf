"""Pruebas críticas del NotificationManager."""

import pytest

from src.api.notification_manager import NotificationManager


@pytest.mark.asyncio
async def test_notification_manager_subscribe_notify_unsubscribe() -> None:
	"""
	Verifica el ciclo completo de suscripción, notificación y desuscripción:
	- El suscriptor recibe la notificación.
	- Tras desuscribirse, no recibe más notificaciones.
	"""
	manager = NotificationManager()
	subscription = manager.subscribe(conversation_id="conv-1")

	# Debe recibir la notificación enviada
	await manager.notify_finished(conversation_id="conv-1")
	message = await subscription.queue.get()
	assert message == "response_finished"

	# Tras desuscribirse, la cola debe quedar vacía aunque se notifique
	manager.unsubscribe(subscription)
	await manager.notify_finished(conversation_id="conv-1")
	assert subscription.queue.empty()
