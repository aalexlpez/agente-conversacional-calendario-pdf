"""Parser de intención de calendario basado en LLM."""

from __future__ import annotations


import json
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

import structlog

from src.domain.entities import Event
from src.infrastructure.llm_service import AIService
from src.infrastructure.memory_store import InMemoryStore
from src.tools.base import ToolRegistry
from src.application.prompt_utils import should_use_pdf_context

logger = structlog.get_logger()


def _normalize(text: str) -> str:
    """Normaliza texto quitando acentos para comparaciones insensibles."""
    normalized = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


async def maybe_handle_calendar_llm(
    *,
    text: str,
    tool_registry: ToolRegistry,
    user_id: str,
    llm: AIService,
    messages: list[dict[str, str]],
    store: InMemoryStore,
    conversation_id: str,
) -> Optional[str]:
    """Analiza la intención de calendario y ejecuta la acción correspondiente."""
    if should_use_pdf_context(store=store, conversation_id=conversation_id, user_text=text):
        return None
    calendar_tool = tool_registry.get("calendar")
    if not calendar_tool:
        return None

    system_prompt = _build_calendar_intent_prompt()
    raw = await llm.generate_messages(system_prompt=system_prompt, messages=messages)
    intent = _parse_calendar_intent(raw)
    if not intent:
        return None

    intent = _normalize_intent_dates(intent=intent, user_text=text)

    action = (intent.get("action") or "none").lower()
    if action in ("none", "", "null"):
        return None

    if action == "create":
        title = (intent.get("title") or "Evento").strip()
        date_str = intent.get("date")
        start_time = intent.get("start_time")
        end_time = intent.get("end_time")
        if not date_str or not start_time:
            return "Para agendar necesito fecha y hora."
        starts_at = _combine_date_time_europe_madrid(date_str, start_time)
        if not starts_at:
            return "No pude interpretar la fecha u hora del evento."
        ends_at = _combine_date_time_europe_madrid(date_str, end_time) if end_time else None
        if not ends_at:
            ends_at = starts_at + timedelta(hours=1)
        try:
            event = calendar_tool.create_event(
                user_id=user_id,
                title=title,
                starts_at=starts_at,
                ends_at=ends_at,
            )
        except Exception as exc:
            logger.error("calendar_llm: error al crear", error=str(exc))
            return "No se pudo crear el evento."
        return "Evento creado en Google Calendar:\n" f"{_format_event(event)}"

    if action == "list":
        events = calendar_tool.list_events(user_id)
        range_start = intent.get("range_start")
        range_end = intent.get("range_end")
        date_str = intent.get("date")
        if range_start or range_end:
            start_dt = _start_of_day(range_start) if range_start else _start_of_day(date_str)
            end_dt = _start_of_day(range_end) if range_end else None
            if start_dt and end_dt:
                end_dt = end_dt + timedelta(days=1)
            elif start_dt and not end_dt:
                end_dt = start_dt + timedelta(days=1)
            if start_dt and end_dt:
                events = [event for event in events if start_dt <= event.starts_at < end_dt]
        elif date_str:
            day = _start_of_day(date_str)
            if day:
                next_day = day + timedelta(days=1)
                events = [event for event in events if day <= event.starts_at < next_day]
        if not events:
            return "No hay eventos en tu calendario para ese rango."
        preview = "\n".join(_format_event(event) for event in events[:10])
        return f"Eventos próximos:\n{preview}"

    if action == "delete":
        event_id = intent.get("event_id")
        title = intent.get("title")
        date_str = intent.get("date")
        range_start = intent.get("range_start")
        range_end = intent.get("range_end")
        events = calendar_tool.list_events(user_id)

        # Si hay un rango, eliminar todos los eventos en ese rango
        if range_start or range_end:
            start_dt = _start_of_day(range_start) if range_start else _start_of_day(date_str)
            end_dt = _start_of_day(range_end) if range_end else None
            if start_dt and end_dt:
                end_dt = end_dt + timedelta(days=1)
            elif start_dt and not end_dt:
                end_dt = start_dt + timedelta(days=1)
            if start_dt and end_dt:
                to_delete = [event for event in events if start_dt <= event.starts_at < end_dt]
            else:
                to_delete = []
            if not to_delete:
                return "No hay eventos en ese rango para eliminar."
            deleted_ids = []
            for event in to_delete:
                try:
                    calendar_tool.delete_event(event.id)
                    deleted_ids.append(event.id)
                except Exception as exc:
                    logger.error("calendar_llm: error al eliminar masivo", error=str(exc), event_id=event.id)
            resumen = "\n".join(_format_event(event) for event in to_delete)
            return f"Se eliminaron {len(deleted_ids)} eventos:\n{resumen}"

        # Si no hay rango, buscar por título/fecha
        if not event_id:
            match = _find_event_by_title_date(events=events, title=title, date_str=date_str)
            if match is None:
                return "No pude identificar el evento. Indica el id o más detalles."
            if isinstance(match, list):
                # Eliminar todos los que coincidan
                deleted_ids = []
                for event in match:
                    try:
                        calendar_tool.delete_event(event.id)
                        deleted_ids.append(event.id)
                    except Exception as exc:
                        logger.error("calendar_llm: error al eliminar múltiple", error=str(exc), event_id=event.id)
                resumen = "\n".join(_format_event(event) for event in match)
                return f"Se eliminaron {len(deleted_ids)} eventos:\n{resumen}"
            event_id = match.id
        try:
            deleted = calendar_tool.delete_event(event_id)
        except Exception as exc:
            logger.error("calendar_llm: error al eliminar", error=str(exc))
            return "No se pudo eliminar el evento."
        return f"Evento eliminado: {event_id}." if deleted else "Evento no encontrado."

    if action == "edit":
        events = calendar_tool.list_events(user_id)
        event_id = intent.get("event_id")
        title = intent.get("title")
        date_str = intent.get("date")
        if not event_id:
            match = _find_event_by_title_date(events=events, title=title, date_str=date_str)
            if match is None:
                return "No pude identificar el evento. Indica el id o más detalles."
            if isinstance(match, list):
                preview = "\n".join(_format_event(event) for event in match[:5])
                return "Encontré varios eventos. Indica el id para editar:\n" f"{preview}"
            event_id = match.id
            target_event = match
        else:
            target_event = next((event for event in events if event.id == event_id), None)

        updates = intent.get("update") or {}
        new_title = updates.get("title")
        new_date = updates.get("date")
        new_start_time = updates.get("start_time")
        new_end_time = updates.get("end_time")

        if not any([new_title, new_date, new_start_time, new_end_time]):
            return "Indica qué cambios deseas aplicar (título o fecha/hora)."

        starts_at = None
        ends_at = None
        if target_event:
            base_date = target_event.starts_at.date().isoformat()
            if new_date and new_start_time:
                starts_at = _combine_date_time_europe_madrid(new_date, new_start_time)
            elif new_date and not new_start_time:
                starts_at = _combine_date_time_europe_madrid(new_date, target_event.starts_at.strftime("%H:%M"))
            elif new_start_time and not new_date:
                starts_at = _combine_date_time_europe_madrid(base_date, new_start_time)

            if new_end_time:
                end_date = new_date or base_date
                ends_at = _combine_date_time_europe_madrid(end_date, new_end_time)
            elif starts_at:
                ends_at = starts_at + timedelta(hours=1)

        try:
            updated = calendar_tool.update_event(
                event_id=event_id,
                title=new_title,
                starts_at=starts_at,
                ends_at=ends_at,
            )
        except Exception as exc:
            logger.error("calendar_llm: error al actualizar", error=str(exc))
            return "No se pudo actualizar el evento."
        if not updated:
            return "Evento no encontrado."
        return "Evento actualizado:\n" f"{_format_event(updated)}"

    return None


def _build_calendar_intent_prompt() -> str:
    """Construye el prompt del sistema que debe devolver la intención en JSON."""
    today = datetime.now(tz=timezone.utc).date().isoformat()
    return (
        "Eres un extractor de intención para un calendario. "
        "Debes responder SOLO JSON válido, sin texto adicional. "
        "Si no es una solicitud de calendario, responde action='none'. "
        f"Hoy es {today} (UTC). "
        "La zona horaria de todos los eventos es Europa/Madrid (España, UTC+1 o UTC+2 en verano). "
        "Resuelve fechas relativas (hoy, mañana, pasado mañana, este viernes) y horas como hora local de España. "
        "Formato obligatorio de salida:\n"
        "{\n"
        "  \"action\": \"create|list|edit|delete|none\",\n"
        "  \"title\": \"string|null\",\n"
        "  \"date\": \"YYYY-MM-DD|null\",\n"
        "  \"start_time\": \"HH:MM|null\",\n"
        "  \"end_time\": \"HH:MM|null\",\n"
        "  \"event_id\": \"string|null\",\n"
        "  \"range_start\": \"YYYY-MM-DD|null\",\n"
        "  \"range_end\": \"YYYY-MM-DD|null\",\n"
        "  \"update\": {\n"
        "    \"title\": \"string|null\",\n"
        "    \"date\": \"YYYY-MM-DD|null\",\n"
        "    \"start_time\": \"HH:MM|null\",\n"
        "    \"end_time\": \"HH:MM|null\"\n"
        "  }\n"
        "}"
    )


def _normalize_intent_dates(*, intent: Dict[str, Any], user_text: str) -> Dict[str, Any]:
    """Agrega el año faltante a fechas relativas si no se menciona explícitamente."""
    if not intent:
        return intent
    if _user_mentions_year(user_text):
        return intent

    def _adjust(field: str) -> None:
        value = intent.get(field)
        if not value:
            return
        adjusted = _adjust_date_if_year_missing(value)
        if adjusted:
            intent[field] = adjusted

    _adjust("date")
    _adjust("range_start")
    _adjust("range_end")

    update = intent.get("update")
    if isinstance(update, dict) and update.get("date"):
        adjusted = _adjust_date_if_year_missing(update.get("date"))
        if adjusted:
            update["date"] = adjusted
            intent["update"] = update

    return intent


def _user_mentions_year(text: str) -> bool:
    """Detecta si el usuario indicó un año para evitar recalculo."""
    return bool(re.search(r"\b(19|20)\d{2}\b", text))


def _adjust_date_if_year_missing(date_str: str) -> Optional[str]:
    """Ajusta la fecha agregando el año correcto si falta y no es pasada."""
    try:
        date_value = datetime.fromisoformat(date_str).date()
    except ValueError:
        return None
    today_local = datetime.now(ZoneInfo("Europe/Madrid")).date()
    candidate = date_value.replace(year=today_local.year)
    if candidate < today_local:
        candidate = candidate.replace(year=today_local.year + 1)
    return candidate.isoformat()


def _parse_calendar_intent(raw: str) -> Optional[Dict[str, Any]]:
    """Intenta decodificar el JSON devuelto por el LLM y soluciona texto extra."""
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        extracted = _extract_json_from_text(raw)
        if not extracted:
            return None
        try:
            return json.loads(extracted)
        except json.JSONDecodeError:
            return None


def _extract_json_from_text(text: str) -> Optional[str]:
    """Extrae el primer objeto JSON válido que encuentre en un texto mixto."""
    if "{" not in text or "}" not in text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return text[start : end + 1]



def _combine_date_time_europe_madrid(date_str: str, time_str: str) -> Optional[datetime]:
    """Combina fecha y hora locales de Madrid y devuelve UTC para el calendario."""
    if not date_str or not time_str:
        return None
    normalized_time = time_str
    if not re.match(r"^\d{1,2}:\d{2}$", time_str.strip()):
        parsed = _parse_time(time_str)
        if parsed:
            normalized_time = parsed
    try:
        # Crear datetime naive (sin zona)
        naive = datetime.fromisoformat(f"{date_str} {normalized_time}")
    except ValueError:
        return None
    # Asignar zona horaria de España
    madrid = ZoneInfo("Europe/Madrid")
    local_dt = naive.replace(tzinfo=madrid)
    # Convertir a UTC para Google Calendar
    utc_dt = local_dt.astimezone(timezone.utc)
    return utc_dt


def _start_of_day(date_str: Optional[str]) -> Optional[datetime]:
    """Devuelve el inicio del día en formato datetime UTC si la fecha es válida."""
    if not date_str:
        return None
    try:
        value = datetime.fromisoformat(date_str)
    except ValueError:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.replace(hour=0, minute=0, second=0, microsecond=0)


def _find_event_by_title_date(
    *,
    events: list[Event],
    title: Optional[str],
    date_str: Optional[str],
) -> Optional[Event | list[Event]]:
    """Busca eventos que coincidan con título y/o fecha para operaciones de edición o eliminación."""
    if not events:
        return None
    filtered = events
    if date_str:
        try:
            date_value = datetime.fromisoformat(date_str).date()
            filtered = [event for event in filtered if event.starts_at.date() == date_value]
        except ValueError:
            filtered = events
    if title:
        title_norm = _normalize(title)
        for event in filtered:
            if title_norm in _normalize(event.title):
                return event
    if len(filtered) == 1:
        return filtered[0]
    if len(filtered) > 1:
        return filtered
    return None


def _parse_time(text: str) -> Optional[str]:
    """Normaliza horarios libres como '5pm' o '17:30'."""
    match = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", text, flags=re.IGNORECASE)
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    meridiem = (match.group(3) or "").lower()
    if meridiem == "pm" and hour < 12:
        hour += 12
    if meridiem == "am" and hour == 12:
        hour = 0
    return f"{hour:02d}:{minute:02d}"


def _format_event(event: Event) -> str:
    """Formatea eventos para respuestas de usuario (ID, título y rango horario)."""
    return (
        f"- {event.id}: {event.title} "
        f"({event.starts_at.isoformat()} - {event.ends_at.isoformat()})"
    )
