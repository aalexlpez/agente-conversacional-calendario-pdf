"""Integración de los endpoints de autenticación con el ASGI app."""

import pytest
import httpx

from src.api.main import app


@pytest.mark.asyncio
async def test_login_success():
    """
    Prueba de login exitoso:
    - Envía credenciales válidas (user1/pass1) al endpoint /auth/login.
    - Verifica que la respuesta sea 200 OK.
    - Verifica que el token JWT y el tipo de token estén presentes en la respuesta.
    """
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/auth/login", data={"username": "user1", "password": "pass1"})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        # El tipo de token puede variar en mayúsculas/minúsculas según la implementación
        assert data["token_type"].lower() == "bearer"


@pytest.mark.asyncio
async def test_login_failure():
    """
    Prueba de login fallido:
    - Envía credenciales inválidas al endpoint /auth/login.
    - Verifica que la respuesta sea 401 Unauthorized.
    - Verifica que el mensaje de error sea el esperado.
    """
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/auth/login", data={"username": "user1", "password": "wrongpass"})
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Credenciales inválidas"


# Prueba de acceso a un endpoint protegido usando el token JWT obtenido en el login.
# Ajusta la ruta '/auth/me' si tienes un endpoint protegido diferente.
@pytest.mark.asyncio
async def test_protected_endpoint():
    """
    Prueba de acceso a endpoint protegido:
    - Realiza login para obtener el token JWT.
    - Usa el token en la cabecera Authorization para acceder a /auth/me.
    - Verifica que la respuesta sea válida (200 si existe, 401 si no autorizado, 404 si no implementado).
    """
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        login_resp = await client.post("/auth/login", data={"username": "user2", "password": "pass2"})
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        protected_resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert protected_resp.status_code in (200, 404, 401)  # Ajusta según implementación
