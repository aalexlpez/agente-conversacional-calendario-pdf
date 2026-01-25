"""Endpoints de conversaciones (CRUD básico)."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.api.auth import get_current_username
from src.api.deps import get_conversation_use_case
from src.domain.exceptions import ResourceNotFound

router = APIRouter(prefix="/conversations", tags=["conversations"])


class ConversationCreate(BaseModel):
    title: str = ""


class ConversationUpdate(BaseModel):
    title: Optional[str] = None


class ConversationResponse(BaseModel):
    id: str
    user_id: str
    title: Optional[str]


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


class ConversationDetailResponse(BaseModel):
    id: str
    user_id: str
    title: Optional[str]
    messages: List[MessageResponse]


@router.post("/", response_model=ConversationResponse)
def create_conversation(
    data: ConversationCreate,
    username: str = Depends(get_current_username),
    conversation_use_case=Depends(get_conversation_use_case),
):
    conversation = conversation_use_case.create(user_id=username, title=data.title)
    return ConversationResponse(id=conversation.id, user_id=conversation.user_id, title=conversation.title)


@router.get("/", response_model=List[ConversationResponse])
def list_conversations(
    username: str = Depends(get_current_username),
    conversation_use_case=Depends(get_conversation_use_case),
):
    conversations = conversation_use_case.list(user_id=username)
    return [ConversationResponse(id=c.id, user_id=c.user_id, title=c.title) for c in conversations]


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(
    conversation_id: str,
    username: str = Depends(get_current_username),
    conversation_use_case=Depends(get_conversation_use_case),
):
    try:
        conversation, messages = conversation_use_case.get_with_messages(
            conversation_id=conversation_id,
            user_id=username,
        )
    except ResourceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ConversationDetailResponse(
        id=conversation.id,
        user_id=conversation.user_id,
        title=conversation.title,
        messages=[
            MessageResponse(
                id=message.id,
                role=message.role,
                content=message.content,
                created_at=message.created_at.isoformat(),
            )
            for message in messages
        ],
    )


@router.put("/{conversation_id}", response_model=ConversationResponse)
def update_conversation(
    conversation_id: str,
    data: ConversationUpdate,
    username: str = Depends(get_current_username),
    conversation_use_case=Depends(get_conversation_use_case),
):
    try:
        conversation = conversation_use_case.update(
            conversation_id=conversation_id,
            user_id=username,
            title=data.title,
        )
    except ResourceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ConversationResponse(id=conversation.id, user_id=conversation.user_id, title=conversation.title)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str,
    username: str = Depends(get_current_username),
    conversation_use_case=Depends(get_conversation_use_case),
):
    try:
        conversation_use_case.delete(conversation_id=conversation_id, user_id=username)
    except ResourceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return None
