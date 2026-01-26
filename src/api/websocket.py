
"""
Módulo WebSocket para chat en tiempo real con streaming y notificaciones.

Permite la comunicación bidireccional entre el cliente y el agente conversacional, soportando mensajes en streaming y notificaciones de finalización de respuesta.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

import structlog
logger = structlog.get_logger()

from src.infrastructure.jwt_service import decode_token
from src.api.deps import get_notification_manager, get_store, send_message_use_case

router = APIRouter(tags=["websocket"])



@router.websocket("/ws/chat/{conversation_id}")
async def chat_ws(websocket: WebSocket, conversation_id: str) -> None:
	"""
	WebSocket handler para chat en tiempo real con streaming y notificaciones.

	Permite a un cliente autenticado enviar mensajes y recibir respuestas en streaming,
	así como notificaciones de finalización de respuesta para una conversación específica.
	La función es asíncrona y soporta múltiples conexiones concurrentes.

	Args:
		websocket (WebSocket): Conexión WebSocket gestionada por FastAPI.
		conversation_id (str): ID de la conversación activa.
	"""
	token = websocket.query_params.get("token")
	if not token:
		await websocket.close(code=1008)
		return
	try:
		username = decode_token(token)
	except Exception:
		await websocket.close(code=1008)
		return

	store = get_store()
	conversation = store.get_conversation(conversation_id)
	if not conversation or conversation.user_id != username:
		await websocket.close(code=1008)
		return

	# Aceptamos la conexión WebSocket de forma asíncrona.
	await websocket.accept()
	notification_manager = get_notification_manager()
	subscription = notification_manager.subscribe(conversation_id=conversation_id)

	async def send_notifications() -> None:
		"""
		Tarea asíncrona para enviar notificaciones en tiempo real al cliente.
		Espera mensajes en la cola de la subscripción y los envía por WebSocket.
		"""
		try:
			while True:
				message = await subscription.queue.get()
				await websocket.send_text(json.dumps({"type": "notification", "event": message}))
		except asyncio.CancelledError:
			return
		except Exception as exc:
			logger.exception("websocket: error en notificaciones", error=str(exc))

	# Lanzamos la tarea de notificaciones en segundo plano (asyncio.create_task).
	notifications_task = asyncio.create_task(send_notifications())

	try:
		while True:
			# Recibimos mensajes del usuario de forma asíncrona.
			payload = await websocket.receive_text()
			try:
				data: Dict[str, Any] = json.loads(payload)
			except json.JSONDecodeError:
				await websocket.send_text(json.dumps({"type": "error", "message": "Payload inválido (JSON esperado)."}))
				continue
			text = str(data.get("text") or data.get("message") or "").strip()
			if not text:
				await websocket.send_text(json.dumps({"type": "error", "message": "Texto vacío"}))
				continue

			try:
				# Ejecutamos el flujo principal (send_message_use_case) de forma asíncrona y transmitimos la respuesta en streaming.
				async for chunk in send_message_use_case.execute(
					user_id=username,
					conversation_id=conversation_id,
					text=text,
				):
					# Enviamos cada fragmento de respuesta al cliente en tiempo real (async).
					await websocket.send_text(json.dumps({"type": "chunk", "content": chunk}))
			except Exception as exc:
				logger.exception("websocket: error en use_case", error=str(exc))
				await websocket.send_text(json.dumps({"type": "error", "message": "Error interno al procesar el mensaje."}))
				continue

			# Notificamos al cliente que la respuesta ha finalizado (async).
			await notification_manager.notify_finished(conversation_id=conversation_id)
	except WebSocketDisconnect:
		# El cliente cerró la conexión WebSocket.
		pass
	finally:
		notifications_task.cancel()
		notification_manager.unsubscribe(subscription)
