"""Pruebas críticas para el servicio JWT."""

import pytest
from jose import JWTError

from src.infrastructure.jwt_service import create_access_token, decode_token


def test_create_and_decode_token_roundtrip() -> None:
	"""
	Crea un JWT con un subject y verifica que al decodificarlo se obtiene el mismo subject.
	Esto asegura la integridad del ciclo de emisión y validación de tokens.
	"""
	token = create_access_token({"sub": "user-123"}, expires_minutes=5)
	assert decode_token(token) == "user-123"


def test_decode_token_missing_subject_raises() -> None:
	"""
	Si el JWT no contiene el claim 'sub', la función debe lanzar JWTError.
	Esto valida el control de errores ante tokens malformados o incompletos.
	"""
	token = create_access_token({}, expires_minutes=5)
	with pytest.raises(JWTError):
		decode_token(token)
