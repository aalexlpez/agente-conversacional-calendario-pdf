"""Endpoints de eventos de calendario (CRUD)."""

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
    title: str
    starts_at: datetime
    ends_at: datetime


class EventUpdate(BaseModel):
    title: Optional[str] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None


class EventResponse(BaseModel):
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
    try:
        event_use_case.delete(event_id=event_id, user_id=username)
    except ResourceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ExternalServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return None
