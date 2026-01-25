"""Endpoints de documentos PDF (upload + query).

Integración con memoria:
    - El PDF se almacena en InMemoryStore como Document y queda asociado al user_id.
    - Las consultas se resuelven leyendo el contenido persistido en memoria.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from src.api.auth import get_current_username
from src.api.deps import get_document_use_case
from src.domain.exceptions import ResourceNotFound

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentResponse(BaseModel):
    id: str
    user_id: str
    conversation_id: str
    filename: str


class DocumentQuery(BaseModel):
    conversation_id: str
    document_id: str
    keyword: str


class DocumentQueryResponse(BaseModel):
    result: str


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    conversation_id: str = Form(...),
    username: str = Depends(get_current_username),
    document_use_case=Depends(get_document_use_case),
):
    # Lectura asíncrona del archivo para no bloquear el event loop.
    content = await file.read()
    try:
        document = await document_use_case.upload(
            user_id=username,
            conversation_id=conversation_id,
            filename=file.filename,
            content=content,
        )
    except ResourceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return DocumentResponse(
        id=document.id,
        user_id=document.user_id,
        conversation_id=document.conversation_id or "",
        filename=document.filename,
    )


@router.get("/", response_model=List[DocumentResponse])
def list_documents(
    conversation_id: str | None = None,
    username: str = Depends(get_current_username),
    document_use_case=Depends(get_document_use_case),
):
    try:
        documents = document_use_case.list(user_id=username, conversation_id=conversation_id)
    except ResourceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [
        DocumentResponse(
            id=doc.id,
            user_id=doc.user_id,
            conversation_id=doc.conversation_id or "",
            filename=doc.filename,
        )
        for doc in documents
    ]


@router.post("/query", response_model=DocumentQueryResponse)
async def query_document(
    data: DocumentQuery,
    username: str = Depends(get_current_username),
    document_use_case=Depends(get_document_use_case),
):
    try:
        result = await document_use_case.query(
            user_id=username,
            conversation_id=data.conversation_id,
            document_id=data.document_id,
            keyword=data.keyword,
        )
    except ResourceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return DocumentQueryResponse(result=result)
