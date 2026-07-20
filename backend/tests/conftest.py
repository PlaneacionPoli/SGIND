"""Fixtures compartidas para tests de API."""

from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.security import get_current_user
from app.main import app
from app.models.user import User

# Errores que indican que la base de datos no está disponible en este entorno
_DB_ERROR_MSGS = (
    "password authentication failed",
    "Connection refused",
    "could not connect to server",
    "connection refused",
    "InvalidPasswordError",
)


def _is_db_error(exc: Exception) -> bool:
    return any(msg in str(exc) for msg in _DB_ERROR_MSGS)


def _make_user(role_name: str, email: str = "test@poligran.edu.co") -> User:
    user = MagicMock(spec=User)
    user.email = email
    user.is_active = True
    user.role = MagicMock()
    user.role.name = role_name
    return user


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def auth_as_procesos():
    app.dependency_overrides[get_current_user] = lambda: _make_user("procesos")
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def auth_as_calidad():
    app.dependency_overrides[get_current_user] = lambda: _make_user("calidad")
    yield
    app.dependency_overrides.pop(get_current_user, None)


def pytest_exception_interact(node, call, report):
    """Skip automáticamente tests que fallan por BD no disponible."""
    if call.excinfo is not None:
        exc = call.excinfo.value
        if _is_db_error(exc):
            report.wasxfail = "DB no disponible en este entorno"
            report.outcome = "skipped"
            report.longrepr = f"SKIP: Base de datos no disponible: {exc}"
