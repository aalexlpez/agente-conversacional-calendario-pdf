"""Servicios de JWT para autenticación."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt


SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key")
ALGORITHM = "HS256"
DEFAULT_EXPIRES_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))


def create_access_token(data: dict, *, expires_minutes: Optional[int] = None) -> str:
	"""Genera un token JWT firmado con expiración."""
	to_encode = data.copy()
	expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes or DEFAULT_EXPIRES_MINUTES)
	to_encode.update({"exp": expire})
	return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> str:
	"""Decodifica un token JWT y extrae el subject (username)."""
	payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
	username: Optional[str] = payload.get("sub")
	if username is None:
		raise JWTError("Token sin subject")
	return username
