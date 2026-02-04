"""
Herramienta de integración con Google Calendar API.

Soporta OAuth de usuario y service account para realizar CRUD sobre eventos.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import os

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.domain.entities import Event
from src.tools.base import BaseTool
import structlog
logger = structlog.get_logger()


class GoogleCalendarTool(BaseTool):
	"""Expone métodos para manipular eventos en Google Calendar."""
	name = "calendar"

	def __init__(
		self,
		*,
		credentials_path: Optional[str] = None,
		calendar_id: str = "primary",
		timezone_name: str = "UTC",
		scopes: Optional[list[str]] = None,
	) -> None:
		"""Configura credenciales, calendario y cliente para la herramienta."""
		env_calendar_id = os.getenv("GOOGLE_CALENDAR_ID")
		env_timezone = os.getenv("GOOGLE_CALENDAR_TIMEZONE")
		env_scopes = os.getenv("GOOGLE_CALENDAR_SCOPES")
		self._calendar_id = env_calendar_id or calendar_id
		self._timezone = env_timezone or timezone_name
		self._scopes = scopes or (env_scopes.split(",") if env_scopes else None) or [
			"https://www.googleapis.com/auth/calendar",
		]

		access_token = os.getenv("GOOGLE_OAUTH_ACCESS_TOKEN")
		refresh_token = os.getenv("GOOGLE_OAUTH_REFRESH_TOKEN")
		client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
		client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
		if access_token and refresh_token and client_id and client_secret:
			credentials = Credentials(
				token=access_token,
				refresh_token=refresh_token,
				token_uri="https://oauth2.googleapis.com/token",
				client_id=client_id,
				client_secret=client_secret,
				scopes=self._scopes,
			)
			self._is_user_oauth = True
			logger.info("google_calendar_tool: usando OAuth de usuario", calendar_id=self._calendar_id)
		else:
			if not credentials_path:
				raise ValueError("Faltan credenciales OAuth o ruta de service account")
			credentials = ServiceAccountCredentials.from_service_account_file(
				credentials_path,
				scopes=self._scopes,
			)
			self._is_user_oauth = False
			logger.info("google_calendar_tool: usando service account", calendar_id=self._calendar_id)
		self._credentials = credentials
		self._ensure_credentials_valid()
		self._service = build("calendar", "v3", credentials=self._credentials, cache_discovery=False)

	def create_event(
		self,
		*,
		user_id: str,
		title: str,
		starts_at: datetime,
		ends_at: datetime,
		metadata: Optional[dict[str, str]] = None,
	) -> Event:
		"""Inserta un evento en el calendario y devuelve el resultado en forma de Event."""
		self._ensure_credentials_valid()
		body = {
			"summary": title,
			"start": self._build_datetime(starts_at),
			"end": self._build_datetime(ends_at),
			"extendedProperties": {"private": metadata or {}},
		}
		try:
			logger.info("google_calendar_tool: insertando evento", calendar_id=self._calendar_id, body=body)
			created = self._service.events().insert(
				calendarId=self._calendar_id,
				body=body,
			).execute()
			logger.info("google_calendar_tool: evento creado en Google", response=created)
		except HttpError as exc:
			logger.error("google_calendar_tool: error al crear evento", error=str(exc), calendar_id=self._calendar_id, body=body)
			raise RuntimeError(f"Error Google Calendar al crear evento: {exc}") from exc

		return Event(
			id=created.get("id", ""),
			user_id=user_id,
			title=created.get("summary", title),
			starts_at=self._parse_datetime(created.get("start")),
			ends_at=self._parse_datetime(created.get("end")),
			metadata=(created.get("extendedProperties", {}) or {}).get("private", {}) or {},
		)

	def update_event(
		self,
		*,
		event_id: str,
		title: Optional[str] = None,
		starts_at: Optional[datetime] = None,
		ends_at: Optional[datetime] = None,
	) -> Optional[Event]:
		"""Actualiza los campos proporcionados de un evento existente."""
		self._ensure_credentials_valid()
		payload: dict[str, object] = {}
		if title is not None:
			payload["summary"] = title
		if starts_at is not None:
			payload["start"] = self._build_datetime(starts_at)
		if ends_at is not None:
			payload["end"] = self._build_datetime(ends_at)
		if not payload:
			return self.get_event(event_id=event_id, user_id="")

		try:
			updated = self._service.events().patch(
				calendarId=self._calendar_id,
				eventId=event_id,
				body=payload,
			).execute()
		except HttpError as exc:
			if exc.resp is not None and exc.resp.status == 404:
				return None
			raise RuntimeError(f"Error Google Calendar al actualizar evento: {exc}") from exc

		return Event(
			id=updated.get("id", event_id),
			user_id="",
			title=updated.get("summary", ""),
			starts_at=self._parse_datetime(updated.get("start")),
			ends_at=self._parse_datetime(updated.get("end")),
			metadata=(updated.get("extendedProperties", {}) or {}).get("private", {}) or {},
		)

	def delete_event(self, event_id: str) -> bool:
		"""Elimina un evento y devuelve True si se borró correctamente."""
		self._ensure_credentials_valid()
		try:
			self._service.events().delete(
				calendarId=self._calendar_id,
				eventId=event_id,
			).execute()
			return True
		except HttpError as exc:
			if exc.resp is not None and exc.resp.status == 404:
				return False
			raise RuntimeError(f"Error Google Calendar al eliminar evento: {exc}") from exc

	def list_events(self, user_id: str) -> list[Event]:
		"""Lista eventos del calendario ordenados por hora de inicio."""
		self._ensure_credentials_valid()
		try:
			result = self._service.events().list(
				calendarId=self._calendar_id,
				singleEvents=True,
				orderBy="startTime",
			).execute()
		except HttpError as exc:
			raise RuntimeError(f"Error Google Calendar al listar eventos: {exc}") from exc

		items = result.get("items", [])
		return [
			Event(
				id=item.get("id", ""),
				user_id=user_id,
				title=item.get("summary", ""),
				starts_at=self._parse_datetime(item.get("start")),
				ends_at=self._parse_datetime(item.get("end")),
				metadata=(item.get("extendedProperties", {}) or {}).get("private", {}) or {},
			)
			for item in items
		]

	def get_event(self, *, event_id: str, user_id: str) -> Optional[Event]:
		"""Obtiene un evento por ID o devuelve None si no existe."""
		self._ensure_credentials_valid()
		try:
			item = self._service.events().get(
				calendarId=self._calendar_id,
				eventId=event_id,
			).execute()
		except HttpError as exc:
			if exc.resp is not None and exc.resp.status == 404:
				return None
			raise RuntimeError(f"Error Google Calendar al obtener evento: {exc}") from exc

		return Event(
			id=item.get("id", ""),
			user_id=user_id,
			title=item.get("summary", ""),
			starts_at=self._parse_datetime(item.get("start")),
			ends_at=self._parse_datetime(item.get("end")),
			metadata=(item.get("extendedProperties", {}) or {}).get("private", {}) or {},
		)

	def _build_datetime(self, value: datetime) -> dict[str, str]:
		"""Construye el payload temporal requerido por la API."""
		if value.tzinfo is None:
			value = value.replace(tzinfo=timezone.utc)
		return {
			"dateTime": value.isoformat(),
			"timeZone": self._timezone,
		}

	def _parse_datetime(self, payload: Optional[dict]) -> datetime:
		"""Parsea el diccionario de la API como datetime con zona UTC."""
		if not payload:
			return datetime.now(tz=timezone.utc)
		value = payload.get("dateTime") or payload.get("date")
		if not value:
			return datetime.now(tz=timezone.utc)
		try:
			return datetime.fromisoformat(value.replace("Z", "+00:00"))
		except ValueError:
			return datetime.now(tz=timezone.utc)

	def _ensure_credentials_valid(self) -> None:
		"""Refresca el access token si caducó (OAuth de usuario)."""
		if not getattr(self, "_is_user_oauth", False):
			return
		if self._credentials is None:
			return
		if self._credentials.valid:
			return
		if self._credentials.expired and self._credentials.refresh_token:
			logger.info("google_calendar_tool: access token expirado, refrescando")
			self._credentials.refresh(Request())
			return
		raise RuntimeError("El refresh token no es válido o no existe.")

	async def execute(self, query: str) -> str:
		"""Interface textual mínima; se recomienda usar los métodos específicos."""
		return (
			"GoogleCalendarTool listo. Usa create_event(), update_event(), delete_event(), "
			"list_events()."
		)
