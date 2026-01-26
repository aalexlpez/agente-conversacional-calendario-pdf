
"""
Módulo de endpoints para la gestión de eventos de calendario.

Permite crear, listar, obtener, actualizar y eliminar eventos asociados al usuario.
Incluye manejo de errores y dependencias para la gestión de eventos.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.api.auth import get_current_username
from src.api.deps import get_event_use_case
from src.domain.exceptions import ExternalServiceError, ResourceNotFound

router = APIRouter(prefix="/events", tags=["events"])



class EventCreate(BaseModel):
    """
    Modelo para la creación de un nuevo evento de calendario.
    """
    title: str
    starts_at: datetime
    ends_at: datetime



class EventUpdate(BaseModel):
    """
    Modelo para la actualización de un evento existente.
    """
    title: Optional[str] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None



class EventResponse(BaseModel):
    """
    Respuesta estándar para endpoints de eventos de calendario.
    """
    id: str
    user_id: str
    title: str
    starts_at: datetime
    ends_at: datetime



@router.post("/", response_model=EventResponse)
def create_event(
    data: EventCreate,
    username: str = Depends(get_current_username),
    event_use_case=Depends(get_event_use_case),
):
    """
    Crea un nuevo evento de calendario para el usuario autenticado.

    Args:
        data (EventCreate): Datos para el nuevo evento.
        username (str): Usuario autenticado extraído del token.
        event_use_case: Caso de uso de eventos inyectado.

    Returns:
        EventResponse: Detalles del evento creado.
    """
    # Si el servicio externo falla, respondemos con 502.
    try:
        event = event_use_case.create(
            user_id=username,
            title=data.title,
            starts_at=data.starts_at,
            ends_at=data.ends_at,
        )
    except ExternalServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return EventResponse(
        id=event.id,
        user_id=event.user_id,
        title=event.title,
        starts_at=event.starts_at,
        ends_at=event.ends_at,
    )



@router.get("/", response_model=List[EventResponse])
def list_events(
    username: str = Depends(get_current_username),
    event_use_case=Depends(get_event_use_case),
):
    """
    Lista todos los eventos de calendario asociados al usuario autenticado.

    Args:
        username (str): Usuario autenticado extraído del token.
        event_use_case: Caso de uso de eventos inyectado.

    Returns:
        List[EventResponse]: Lista de eventos encontrados.
    """
    try:
        events = event_use_case.list(user_id=username)
    except ExternalServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return [
        EventResponse(
            id=event.id,
            user_id=event.user_id,
            title=event.title,
            starts_at=event.starts_at,
            ends_at=event.ends_at,
        )
        for event in events
    ]



@router.get("/{event_id}", response_model=EventResponse)
def get_event(
    event_id: str,
    username: str = Depends(get_current_username),
    event_use_case=Depends(get_event_use_case),
):
    """
    Obtiene los detalles de un evento de calendario específico.

    Args:
        event_id (str): ID del evento.
        username (str): Usuario autenticado extraído del token.
        event_use_case: Caso de uso de eventos inyectado.

    Returns:
        EventResponse: Detalles del evento solicitado.
    """
    try:
        event = event_use_case.get(event_id=event_id, user_id=username)
    except ResourceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ExternalServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return EventResponse(
        id=event.id,
        user_id=event.user_id,
        title=event.title,
        starts_at=event.starts_at,
        ends_at=event.ends_at,
    )



@router.put("/{event_id}", response_model=EventResponse)
def update_event(
    event_id: str,
    data: EventUpdate,
    username: str = Depends(get_current_username),
    event_use_case=Depends(get_event_use_case),
):
    """
    Actualiza los datos de un evento de calendario existente.

    Args:
        event_id (str): ID del evento a actualizar.
        data (EventUpdate): Datos de actualización.
        username (str): Usuario autenticado extraído del token.
        event_use_case: Caso de uso de eventos inyectado.

    Returns:
        EventResponse: Detalles del evento actualizado.
    """
    try:
        updated = event_use_case.update(
            event_id=event_id,
            user_id=username,
            title=data.title,
            starts_at=data.starts_at,
            ends_at=data.ends_at,
        )
    except ResourceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ExternalServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return EventResponse(
        id=updated.id,
        user_id=updated.user_id,
        title=updated.title,
        starts_at=updated.starts_at,
        ends_at=updated.ends_at,
    )



@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: str,
    username: str = Depends(get_current_username),
    event_use_case=Depends(get_event_use_case),
):
    """
    Elimina un evento de calendario existente del usuario autenticado.

    Args:
        event_id (str): ID del evento a eliminar.
        username (str): Usuario autenticado extraído del token.
        event_use_case: Caso de uso de eventos inyectado.

    Returns:
        None
    """
    try:
        event_use_case.delete(event_id=event_id, user_id=username)
    except ResourceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ExternalServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return None
