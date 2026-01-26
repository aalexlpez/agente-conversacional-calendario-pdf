

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from src.api.auth import get_current_username
from src.api.deps import get_document_use_case
from src.domain.exceptions import ResourceNotFound

"""
Integración con memoria:
    - El PDF se almacena en InMemoryStore como Document y queda asociado al user_id.
    - Las consultas se resuelven leyendo el contenido persistido en memoria.
"""

"""
Módulo de endpoints para gestión y consulta de documentos PDF.

Permite subir documentos PDF y realizar búsquedas o consultas sobre su contenido.
La integración con la memoria se realiza a través de InMemoryStore, asociando cada documento al usuario y conversación.
"""

router = APIRouter(prefix="/documents", tags=["documents"])

class DocumentResponse(BaseModel):
    """
    Respuesta estándar para endpoints de documentos PDF.
    """
    id: str
    user_id: str
    conversation_id: str
    filename: str



class DocumentQuery(BaseModel):
    """
    Modelo para realizar una consulta sobre un documento PDF.
    """
    conversation_id: str
    document_id: str
    keyword: str



class DocumentQueryResponse(BaseModel):
    """
    Respuesta para una consulta sobre el contenido de un documento PDF.
    """
    result: str



@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    conversation_id: str = Form(...),
    username: str = Depends(get_current_username),
    document_use_case=Depends(get_document_use_case),
):
    """
    Endpoint para subir un documento PDF y asociarlo a una conversación y usuario.
    El archivo se almacena en memoria y queda disponible para consultas posteriores.

    Args:
        file (UploadFile): Archivo PDF subido por el usuario.
        conversation_id (str): ID de la conversación asociada.
        username (str): Usuario autenticado extraído del token.
        document_use_case: Caso de uso de documentos inyectado.

    Returns:
        DocumentResponse: Detalles del documento almacenado.
    """
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
    """
    Lista todos los documentos PDF asociados al usuario y, opcionalmente, a una conversación.

    Args:
        conversation_id (str | None): ID de la conversación (opcional).
        username (str): Usuario autenticado extraído del token.
        document_use_case: Caso de uso de documentos inyectado.

    Returns:
        List[DocumentResponse]: Lista de documentos encontrados.
    """
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
    """
    Realiza una consulta sobre el contenido de un documento PDF previamente subido.
    Permite buscar palabras clave o frases dentro del documento asociado al usuario y conversación.

    Args:
        data (DocumentQuery): Parámetros de la consulta (conversación, documento, keyword).
        username (str): Usuario autenticado extraído del token.
        document_use_case: Caso de uso de documentos inyectado.

    Returns:
        DocumentQueryResponse: Resultado de la búsqueda o consulta.
    """
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
