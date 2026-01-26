

"""
Módulo de endpoints de autenticación para el agente conversacional.

Proporciona endpoints para login y extracción de usuario autenticado usando JWT.
Incluye manejo de errores y dependencias para la autenticación.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError
from pydantic import BaseModel


from src.api.deps import get_auth_login_use_case
from src.domain.exceptions import AuthServiceUnavailable, InvalidCredentials, UserNotFound
from src.infrastructure.jwt_service import decode_token
import structlog
logger = structlog.get_logger()

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class TokenResponse(BaseModel):
    """
    Respuesta estándar para el endpoint de login.
    Contiene el token de acceso JWT y el tipo de token.
    """
    access_token: str
    token_type: str = "bearer"



class TokenData(BaseModel):
    """
    Modelo auxiliar para extraer datos del token JWT.
    """
    username: Optional[str] = None


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_use_case=Depends(get_auth_login_use_case),
):
    """
    Endpoint para autenticar a un usuario y devolver un token JWT si las credenciales son válidas.

    Args:
        form_data (OAuth2PasswordRequestForm): Datos de usuario y contraseña recibidos por formulario.
        auth_service: Servicio de autenticación inyectado por dependencia.

    Returns:
        TokenResponse: Token de acceso JWT si la autenticación es exitosa.
    """
    try:
        access_token = auth_use_case.execute(
            username=form_data.username,
            password=form_data.password,
        )
    except AuthServiceUnavailable:
        logger.error("Servicio de autenticación no disponible", username=form_data.username)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Servicio de autenticación no disponible.")
    except UserNotFound as exc:
        logger.warning("Usuario no encontrado", username=form_data.username)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidCredentials:
        logger.info("Login fallido: contraseña incorrecta", username=form_data.username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    return TokenResponse(access_token=access_token)


def get_current_username(token: str = Depends(oauth2_scheme)) -> str:
    """
    Extrae el nombre de usuario del token JWT proporcionado en la cabecera Authorization.
    Lanza una excepción HTTP si el token es inválido.

    Args:
        token (str): Token JWT extraído automáticamente por FastAPI.

    Returns:
        str: Nombre de usuario autenticado.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        return decode_token(token)
    except JWTError as exc:
        raise credentials_exception from exc
