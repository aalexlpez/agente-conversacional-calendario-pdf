import pytest

from src.application.api_use_cases import AuthLoginUseCase
from src.domain.exceptions import InvalidCredentials, UserNotFound
from src.infrastructure.auth import AuthService
from src.infrastructure.memory_store import InMemoryStore


def test_auth_login_use_case_success_creates_user() -> None:
	store = InMemoryStore()
	auth_service = AuthService(users={"alice": "secret"})
	use_case = AuthLoginUseCase(
		auth_service=auth_service,
		store=store,
		token_factory=lambda payload: f"token:{payload['sub']}",
	)

	token = use_case.execute(username="alice", password="secret")

	assert token == "token:alice"
	assert store.get_user("alice") is not None


def test_auth_login_use_case_invalid_credentials() -> None:
	store = InMemoryStore()
	auth_service = AuthService(users={"alice": "secret"})
	use_case = AuthLoginUseCase(
		auth_service=auth_service,
		store=store,
		token_factory=lambda payload: "token",
	)

	with pytest.raises(InvalidCredentials):
		use_case.execute(username="alice", password="wrong")


def test_auth_login_use_case_user_not_found() -> None:
	store = InMemoryStore()
	auth_service = AuthService(users={"alice": "secret"})
	use_case = AuthLoginUseCase(
		auth_service=auth_service,
		store=store,
		token_factory=lambda payload: "token",
	)

	with pytest.raises(UserNotFound):
		use_case.execute(username="bob", password="secret")
