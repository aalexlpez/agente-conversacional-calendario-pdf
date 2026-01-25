"""Excepciones de dominio para la aplicación."""


class DomainError(Exception):
	"""Error base de dominio."""


class AuthServiceUnavailable(DomainError):
	"""El servicio de autenticación no está disponible."""


class UserNotFound(DomainError):
	"""El usuario no existe en el almacén de autenticación."""


class InvalidCredentials(DomainError):
	"""Credenciales inválidas."""


class ResourceNotFound(DomainError):
	"""Recurso no encontrado o no accesible por el usuario."""


class ExternalServiceError(DomainError):
	"""Error al comunicarse con un servicio externo."""

