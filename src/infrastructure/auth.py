"""Autenticación simple basada en un diccionario de usuarios hardcodeado y configurable.

Este módulo expone un servicio para validar credenciales en memoria (útil para pruebas y demos)
sin depender de un proveedor de identidad externo.
"""

from __future__ import annotations

from typing import Dict, Optional


class AuthService:
    """
    Servicio de autenticación simple basado en un diccionario de usuarios en memoria.
    Permite validar credenciales de usuario contra un almacén local hardcodeado o personalizado.
    """

    class AuthError(Exception):
        """Excepción personalizada cuando no se encuentra el usuario solicitado."""
        pass

    def __init__(self, users: Optional[Dict[str, str]] = None) -> None:
        """
        Inicializa el servicio de autenticación con un diccionario de usuarios.
        Si no se proporciona, se usa un conjunto de usuarios por defecto.

        Args:
            users (Optional[Dict[str, str]]): Diccionario de usuarios {usuario: contraseña}.
        """
        self._users = users or {
            "admin": "admin123",
            "user1": "pass1",
            "user2": "pass2",
            "user3": "pass3",
            "user4": "pass4",
            "user5": "pass5",
            "user6": "pass6",
            "user7": "pass7",
            "user8": "pass8",
            "user9": "pass9",
            "user10": "pass10",
        }

    def authenticate(self, username: str, password: str) -> bool:
        """
        Valida si las credenciales proporcionadas corresponden a un usuario registrado.

        Args:
            username (str): Nombre de usuario.
            password (str): Contraseña.

        Returns:
            bool: True si las credenciales son válidas, False en caso contrario.

        Raises:
            AuthService.AuthError: Si el usuario no existe en el almacén local.
        """
        if username not in self._users:
            raise AuthService.AuthError(f"Usuario '{username}' no encontrado en el almacén local.")
        expected = self._users.get(username)
        return expected == password
