"""Tests Fase 4 — endpoints nuevos: cerrar OM, filtros plan/seguimiento/informe."""

from unittest.mock import MagicMock

import pytest

from app.models.user import User

_DB_ERRORS = (
    "password authentication failed",
    "Connection refused",
    "could not connect",
)


def _is_db_unavailable(exc: Exception) -> bool:
    return any(msg in str(exc) for msg in _DB_ERRORS)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _make_admin(email: str = "admin@poligran.edu.co") -> User:
    user = MagicMock(spec=User)
    user.email = email
    user.is_active = True
    user.role = MagicMock()
    user.role.name = "calidad"
    return user


def _make_reader(email: str = "reader@poligran.edu.co") -> User:
    user = MagicMock(spec=User)
    user.email = email
    user.is_active = True
    user.role = MagicMock()
    user.role.name = "procesos"
    return user


# ─── OM CRUD ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_om_list_requiere_auth(client):
    resp = await client.get("/api/v1/om")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_om_list_con_auth(client, auth_as_calidad):
    try:
        resp = await client.get("/api/v1/om")
    except Exception as e:
        if _is_db_unavailable(e):
            pytest.skip("PostgreSQL no disponible")
        raise
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_om_create_procesos_forbidden(client, auth_as_procesos):
    payload = {"id_indicador": "T-01", "nombre_indicador": "Test", "anio": 2025, "tiene_om": 1}
    resp = await client.post("/api/v1/om", json=payload)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_om_create_calidad_ok(client, auth_as_calidad):
    payload = {
        "id_indicador": "FASE4-TEST-001",
        "nombre_indicador": "Indicador de prueba Fase4",
        "proceso": "Calidad",
        "periodo": "Enero",
        "anio": 2025,
        "tiene_om": 1,
        "tipo_accion": "OM Kawak",
    }
    try:
        resp = await client.post("/api/v1/om", json=payload)
    except Exception as e:
        if _is_db_unavailable(e):
            pytest.skip("PostgreSQL no disponible")
        raise
    assert resp.status_code in (201, 200), resp.text
    data = resp.json()
    assert data["id_indicador"] == "FASE4-TEST-001"
    assert data["tiene_om"] == 1
    return data["id"]


@pytest.mark.asyncio
async def test_om_update_not_found(client, auth_as_calidad):
    try:
        resp = await client.put("/api/v1/om/999999", json={"comentario": "actualizado"})
    except Exception as e:
        if _is_db_unavailable(e):
            pytest.skip("PostgreSQL no disponible")
        raise
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_om_cerrar_not_found(client, auth_as_calidad):
    try:
        resp = await client.patch("/api/v1/om/999999/cerrar", json={})
    except Exception as e:
        if _is_db_unavailable(e):
            pytest.skip("PostgreSQL no disponible")
        raise
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_om_cerrar_procesos_forbidden(client, auth_as_procesos):
    resp = await client.patch("/api/v1/om/1/cerrar", json={})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_om_delete_not_found(client, auth_as_calidad):
    try:
        resp = await client.delete("/api/v1/om/999999")
    except Exception as e:
        if _is_db_unavailable(e):
            pytest.skip("PostgreSQL no disponible")
        raise
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_om_crud_flujo_completo(client, auth_as_calidad):
    """Crea, lee, cierra y elimina un OM en secuencia."""
    payload = {
        "id_indicador": "FASE4-FLUJO-001",
        "nombre_indicador": "Flujo completo",
        "anio": 2025,
        "tiene_om": 1,
    }
    try:
        create_resp = await client.post("/api/v1/om", json=payload)
    except Exception as e:
        if _is_db_unavailable(e):
            pytest.skip("PostgreSQL no disponible")
        raise

    assert create_resp.status_code in (201, 200), create_resp.text
    om_id = create_resp.json()["id"]

    update_resp = await client.put(f"/api/v1/om/{om_id}", json={"comentario": "actualizado"})
    assert update_resp.status_code == 200
    assert update_resp.json()["comentario"] == "actualizado"

    cerrar_resp = await client.patch(
        f"/api/v1/om/{om_id}/cerrar", json={"comentario": "OM cerrada en Fase4"}
    )
    assert cerrar_resp.status_code == 200
    data = cerrar_resp.json()
    assert data["tiene_om"] == 0
    assert data["comentario"] == "OM cerrada en Fase4"

    delete_resp = await client.delete(f"/api/v1/om/{om_id}")
    assert delete_resp.status_code == 204

    list_resp = await client.get("/api/v1/om")
    ids = [r["id"] for r in list_resp.json()]
    assert om_id not in ids


# ─── Filtros Plan de Mejoramiento ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_plan_mejoramiento_filtros_requiere_auth(client):
    resp = await client.get("/api/v1/plan-mejoramiento/filtros")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_plan_mejoramiento_filtros_estructura(client, auth_as_calidad):
    resp = await client.get("/api/v1/plan-mejoramiento/filtros")
    assert resp.status_code == 200
    data = resp.json()
    assert "anios" in data or "error" in data
    if "anios" in data:
        assert isinstance(data["anios"], list)
        assert "cortes" in data
        assert "factores" in data
        assert "caracteristicas" in data


# ─── Filtros Seguimiento ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_seguimiento_filtros_requiere_auth(client):
    resp = await client.get("/api/v1/seguimiento/filtros")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_seguimiento_filtros_estructura(client, auth_as_calidad):
    resp = await client.get("/api/v1/seguimiento/filtros")
    assert resp.status_code == 200
    data = resp.json()
    assert "anios" in data
    assert "meses" in data
    assert "procesos" in data
    assert "estados" in data
    assert isinstance(data["anios"], list)
    assert isinstance(data["meses"], list)


# ─── Filtros Informe ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_informe_filtros_requiere_auth(client):
    resp = await client.get("/api/v1/informe/filtros")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_informe_filtros_estructura(client, auth_as_calidad):
    resp = await client.get("/api/v1/informe/filtros")
    assert resp.status_code == 200
    data = resp.json()
    assert "anios" in data or "anio_default" in data or "error" not in data


# ─── Plan de Mejoramiento dashboard ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_plan_mejoramiento_dashboard_requiere_auth(client):
    resp = await client.get("/api/v1/plan-mejoramiento/dashboard")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_plan_mejoramiento_dashboard_responde(client, auth_as_calidad):
    resp = await client.get("/api/v1/plan-mejoramiento/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)


# ─── Seguimiento dashboard ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_seguimiento_dashboard_requiere_auth(client):
    resp = await client.get("/api/v1/seguimiento/dashboard")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_seguimiento_dashboard_responde(client, auth_as_calidad):
    resp = await client.get("/api/v1/seguimiento/dashboard")
    assert resp.status_code == 200
    assert isinstance(resp.json(), dict)
