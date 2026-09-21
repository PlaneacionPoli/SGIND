"""Rol 'administrador' (ADMIN_EMAILS) y restriccion del rol 'procesos'.

'procesos' solo accede a Resumen, CMI Estrategico, CMI por Procesos, Informe y
Plan de Mejoramiento: Seguimiento Operativo y Gestion OM responden 403.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config import Settings
from app.models.user import Role
from app.services.auth_service import AuthService

ENDPOINTS_OPERATIVOS = [
    "/api/v1/seguimiento/filtros",
    "/api/v1/seguimiento/dashboard",
    "/api/v1/seguimiento/export",
    "/api/v1/om",
    "/api/v1/om/matriz",
    "/api/v1/om/plan-accion",
]

ADMINS = "Admin1@poligran.edu.co, admin2@poligran.edu.co"


# ─── Bloqueo por rol en la API ───────────────────────────────────────────────


@pytest.mark.parametrize("path", ENDPOINTS_OPERATIVOS)
@pytest.mark.asyncio
async def test_procesos_recibe_403_en_pantallas_operativas(client, auth_as_procesos, path):
    resp = await client.get(path)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_administrador_accede_a_seguimiento(client, auth_as_administrador):
    resp = await client.get("/api/v1/seguimiento/filtros")
    assert resp.status_code != 403


@pytest.mark.asyncio
async def test_calidad_sigue_accediendo_a_seguimiento(client, auth_as_calidad):
    resp = await client.get("/api/v1/seguimiento/filtros")
    assert resp.status_code != 403


@pytest.mark.asyncio
async def test_procesos_sigue_leyendo_pantallas_permitidas(client, auth_as_procesos):
    for path in (
        "/api/v1/cmi/filtros",
        "/api/v1/informe/filtros",
        "/api/v1/plan-mejoramiento/filtros",
    ):
        resp = await client.get(path)
        assert resp.status_code != 403, path


# ─── ADMIN_EMAILS ────────────────────────────────────────────────────────────


def test_admin_emails_set_normaliza_mayusculas_y_espacios():
    assert Settings(admin_emails=ADMINS).admin_emails_set == {
        "admin1@poligran.edu.co",
        "admin2@poligran.edu.co",
    }


def test_admin_emails_vacio_por_defecto():
    assert Settings(admin_emails="").admin_emails_set == set()


def _result(value):
    r = MagicMock()
    r.scalar_one_or_none.return_value = value
    return r


def _db(*results):
    db = MagicMock()
    db.execute = AsyncMock(side_effect=[_result(v) for v in results])
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    return db


def _user(role_name: str, role_id: int):
    user = MagicMock()
    user.name = "N"
    user.azure_oid = None
    user.role = MagicMock()
    user.role.name = role_name
    user.role_id = role_id
    return user


def _service():
    return AuthService(Settings(admin_emails=ADMINS))


@pytest.mark.asyncio
async def test_usuario_nuevo_en_admin_emails_recibe_rol_administrador():
    db = _db(None, Role(id=9, name="administrador"))
    user = await _service()._get_or_create_user(
        db, email="ADMIN1@poligran.edu.co", name=None, azure_oid=None
    )
    assert user.role_id == 9


@pytest.mark.asyncio
async def test_usuario_nuevo_fuera_de_la_lista_recibe_procesos():
    db = _db(None, Role(id=1, name="procesos"))
    user = await _service()._get_or_create_user(
        db, email="otro@poligran.edu.co", name=None, azure_oid=None
    )
    assert user.role_id == 1


@pytest.mark.asyncio
async def test_usuario_existente_es_promovido_al_entrar_a_la_lista():
    existing = _user("procesos", 1)
    db = _db(existing, Role(id=9, name="administrador"))
    await _service()._get_or_create_user(
        db, email="admin2@poligran.edu.co", name=None, azure_oid=None
    )
    assert existing.role_id == 9


@pytest.mark.asyncio
async def test_administrador_fuera_de_la_lista_vuelve_a_procesos():
    existing = _user("administrador", 9)
    db = _db(existing, Role(id=1, name="procesos"))
    await _service()._get_or_create_user(
        db, email="exadmin@poligran.edu.co", name=None, azure_oid=None
    )
    assert existing.role_id == 1


@pytest.mark.asyncio
async def test_calidad_fuera_de_la_lista_no_se_toca():
    existing = _user("calidad", 2)
    db = _db(existing)
    await _service()._get_or_create_user(
        db, email="calidad@poligran.edu.co", name=None, azure_oid=None
    )
    assert existing.role_id == 2
    assert db.execute.await_count == 1
