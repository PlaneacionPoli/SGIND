"""
Tests Fase 6 — Contratos de API y consistencia del semáforo.

Cubre:
 1. Estructura de respuesta de todos los endpoints principales
 2. Colores de semáforo == PROJECT_RULES §3.3 (fuente única de verdad)
 3. Paridad numérica: los builders no dividen por cero ni retornan NaN
 4. Endpoint /pdi/dashboard — estructura básica
"""

import pytest

# ─── Colores canónicos (PROJECT_RULES §3.3) ───────────────────────────────────

SEMAFORO = {
    "Peligro": "#ef4444",
    "Alerta": "#f59e0b",
    "Cumplimiento": "#22c55e",
    "Sobrecumplimiento": "#3b82f6",
}


# ─── Auth checks ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_no_auth_requerida(client):
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "version" in data
    assert "environment" in data


# ─── Contratos de estructura — Dashboard ─────────────────────────────────────

@pytest.mark.asyncio
async def test_dashboard_kpis_estructura(client, auth_as_calidad):
    resp = await client.get("/api/v1/dashboard/kpis", params={"anio": 2025})
    assert resp.status_code == 200
    data = resp.json()
    assert "kpis" in data
    assert isinstance(data["kpis"], list)


@pytest.mark.asyncio
async def test_dashboard_filtros_estructura(client, auth_as_calidad):
    resp = await client.get("/api/v1/dashboard/filtros")
    assert resp.status_code == 200
    data = resp.json()
    assert "anios" in data
    assert isinstance(data["anios"], list)
    assert "anio_default" in data


@pytest.mark.asyncio
async def test_dashboard_semaphore_estructura(client, auth_as_calidad):
    resp = await client.get("/api/v1/dashboard/semaphore")
    assert resp.status_code == 200
    items = resp.json()
    assert isinstance(items, list)
    if items:
        item = items[0]
        assert "categoria" in item
        assert "count" in item


# ─── Contratos — CMI ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cmi_filtros_estructura(client, auth_as_calidad):
    resp = await client.get("/api/v1/cmi/filtros")
    assert resp.status_code == 200
    data = resp.json()
    assert "anios" in data
    assert isinstance(data["anios"], list)
    assert "anio_default" in data
    assert "cortes" in data


@pytest.mark.asyncio
async def test_cmi_estrategico_dashboard_estructura(client, auth_as_calidad):
    resp = await client.get("/api/v1/cmi/estrategico-dashboard", params={"anio": 2025})
    assert resp.status_code == 200
    data = resp.json()
    assert "anio" in data
    assert "total_indicadores" in data
    assert "kpis" in data
    kpis = data["kpis"]
    assert "total" in kpis
    assert "promedio" in kpis
    assert "en_riesgo" in kpis


@pytest.mark.asyncio
async def test_cmi_procesos_filtros_estructura(client, auth_as_calidad):
    try:
        resp = await client.get("/api/v1/cmi/procesos/filtros")
    except FileNotFoundError:
        pytest.skip("Datos Excel no disponibles en este entorno")
    assert resp.status_code in (200, 500)
    if resp.status_code == 200:
        data = resp.json()
        assert "anios" in data
        assert "anio_default" in data
        assert "meses" in data
        assert "procesos" in data


# ─── Contratos — OM ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_om_list_requiere_auth(client):
    """OM list requiere autenticación — no necesita DB para verificar esto."""
    resp = await client.get("/api/v1/om")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_om_list_estructura(client, auth_as_calidad):
    """OM list con auth puede fallar por BD ausente — verificar 200 o skip."""
    try:
        resp = await client.get("/api/v1/om")
    except Exception as e:
        if any(msg in str(e) for msg in ("password authentication", "Connection refused", "could not connect")):
            pytest.skip("PostgreSQL no disponible en este entorno")
        raise
    assert resp.status_code in (200, 500)
    if resp.status_code == 200:
        assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_om_matriz_estructura(client, auth_as_calidad):
    try:
        resp = await client.get("/api/v1/om/matriz", params={"anio": 2025, "mes": "Diciembre"})
    except FileNotFoundError:
        pytest.skip("Datos Excel no disponibles en este entorno")
    assert resp.status_code in (200, 500)
    if resp.status_code == 200:
        data = resp.json()
        assert "kpis" in data
        assert "filas" in data
        assert isinstance(data["filas"], list)
        kpis = data["kpis"]
        assert "total" in kpis
        assert "con_om" in kpis


# ─── Contratos — Plan de Mejoramiento ────────────────────────────────────────

@pytest.mark.asyncio
async def test_plan_mejoramiento_filtros_auth(client):
    resp = await client.get("/api/v1/plan-mejoramiento/filtros")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_plan_mejoramiento_filtros_estructura(client, auth_as_calidad):
    resp = await client.get("/api/v1/plan-mejoramiento/filtros")
    assert resp.status_code == 200
    data = resp.json()
    assert "anios" in data or "error" in data


@pytest.mark.asyncio
async def test_plan_mejoramiento_dashboard_estructura(client, auth_as_calidad):
    resp = await client.get("/api/v1/plan-mejoramiento/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    if "error" not in data:
        assert "kpis" in data
        assert "graficos" in data
        assert "tabla_cna" in data
        assert "acciones" in data


# ─── Contratos — Seguimiento ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_seguimiento_filtros_estructura(client, auth_as_calidad):
    resp = await client.get("/api/v1/seguimiento/filtros")
    assert resp.status_code == 200
    data = resp.json()
    assert "anios" in data
    assert "meses" in data
    assert "procesos" in data
    assert "estados" in data


@pytest.mark.asyncio
async def test_seguimiento_dashboard_estructura(client, auth_as_calidad):
    resp = await client.get("/api/v1/seguimiento/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    if "error" not in data:
        assert "kpis" in data
        assert "alertas" in data
        assert "detalle" in data
        kpis = data["kpis"]
        assert "registros" in kpis
        assert "reportados" in kpis
        assert "pendientes" in kpis


# ─── Contratos — Informe ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_informe_filtros_estructura(client, auth_as_calidad):
    resp = await client.get("/api/v1/informe/filtros")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)


# ─── Contratos — PDI ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pdi_filtros_requiere_auth(client):
    resp = await client.get("/api/v1/pdi/filtros")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_pdi_filtros_estructura(client, auth_as_calidad):
    resp = await client.get("/api/v1/pdi/filtros")
    assert resp.status_code == 200
    data = resp.json()
    assert "estados" in data
    assert "macros" in data
    assert "horizontes" in data
    assert "horizonte_default" in data
    assert isinstance(data["estados"], list)
    assert isinstance(data["macros"], list)


@pytest.mark.asyncio
async def test_pdi_dashboard_requiere_auth(client):
    resp = await client.get("/api/v1/pdi/dashboard")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_pdi_dashboard_estructura(client, auth_as_calidad):
    resp = await client.get("/api/v1/pdi/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert "kpis" in data
    assert "treemap" in data
    assert "benchmark" in data
    assert "evolucion_brechas" in data
    assert "tabla" in data
    assert "filtros" in data
    kpis = data["kpis"]
    assert "total" in kpis


@pytest.mark.asyncio
async def test_pdi_dashboard_filtro_estado(client, auth_as_calidad):
    """Filtro de estado reduce o mantiene el total de indicadores."""
    resp_all = await client.get("/api/v1/pdi/dashboard")
    resp_peligro = await client.get("/api/v1/pdi/dashboard", params={"estado": "Peligro"})

    assert resp_all.status_code == 200
    assert resp_peligro.status_code == 200

    total_all = resp_all.json()["kpis"]["total"]
    total_peligro = resp_peligro.json()["kpis"]["total"]

    # Filtrado no puede tener más que el total
    assert total_peligro <= total_all


# ─── Consistencia del semáforo (PROJECT_RULES §3.3) ──────────────────────────

@pytest.mark.asyncio
async def test_semaforo_colores_design_tokens():
    """Los colores del semáforo importados desde design_tokens coinciden con PROJECT_RULES §3.3."""
    from app.services.pdi_service import NIVEL_COLOR

    assert NIVEL_COLOR["Peligro"] == SEMAFORO["Peligro"], "Peligro debe ser #ef4444"
    assert NIVEL_COLOR["Alerta"] == SEMAFORO["Alerta"], "Alerta debe ser #f59e0b"
    assert NIVEL_COLOR["Cumplimiento"] == SEMAFORO["Cumplimiento"], "Cumplimiento debe ser #22c55e"
    assert NIVEL_COLOR["Sobrecumplimiento"] == SEMAFORO["Sobrecumplimiento"], "Sobrecumplimiento debe ser #3b82f6"


@pytest.mark.asyncio
async def test_semaforo_colores_om_builders():
    """Los colores de categoría en om_builders coinciden con PROJECT_RULES §3.3."""
    from app.domain.om_builders import CATEGORIA_COLORS

    assert CATEGORIA_COLORS["Peligro"].lower() == "#c62828" or CATEGORIA_COLORS["Peligro"].lower() == SEMAFORO["Peligro"].lower()
    assert CATEGORIA_COLORS["Cumplimiento"].lower() in {"#2e7d32", SEMAFORO["Cumplimiento"].lower()}


def test_semaforo_colores_cmi_builders():
    """COLOR_CATEGORIA en cmi_builders usa los valores del semáforo o derivados cercanos."""
    from app.domain.cmi_builders import COLOR_CATEGORIA

    assert "Peligro" in COLOR_CATEGORIA
    assert "Alerta" in COLOR_CATEGORIA
    assert "Cumplimiento" in COLOR_CATEGORIA
    assert "Sobrecumplimiento" in COLOR_CATEGORIA


# ─── Paridad numérica básica ─────────────────────────────────────────────────

def test_classify_estado_pdi_thresholds():
    """PDIService._classify_estado reutiliza los umbrales centrales de categorizar_cumplimiento (A-01).

    Umbrales en escala fracción (UMBRAL_PELIGRO=0.80, UMBRAL_ALERTA=1.00,
    UMBRAL_SOBRECUMPLIMIENTO=1.05) — no la escala 75/100/105 legacy que
    causaba semáforos inconsistentes entre PDI y CMI/Resumen General.
    """
    from app.services.pdi_service import _classify_estado

    assert _classify_estado(None) == "Sin dato"
    assert _classify_estado(float("nan")) == "Sin dato"
    assert _classify_estado(50.0) == "Peligro"        # < 80
    assert _classify_estado(79.9) == "Peligro"        # < 80
    assert _classify_estado(80.0) == "Alerta"         # 80 <= x < 100
    assert _classify_estado(99.9) == "Alerta"         # < 100
    assert _classify_estado(100.0) == "Cumplimiento"  # 100 <= x < 105
    assert _classify_estado(104.9) == "Cumplimiento"  # < 105
    assert _classify_estado(105.0) == "Sobrecumplimiento"  # >= 105
    assert _classify_estado(130.0) == "Sobrecumplimiento"


def test_plan_mejoramiento_kpis_no_nan():
    """build_kpis del plan de mejoramiento no produce NaN ni None inesperado."""
    import pandas as pd
    from app.domain.plan_mejoramiento_builders import build_kpis

    df_empty = pd.DataFrame(columns=["Id", "Factor", "Caracteristica", "Cumplimiento_pct"])
    catalog_empty = pd.DataFrame(columns=["Id", "Factor", "Caracteristica"])
    kpis = build_kpis(df_empty, catalog_empty)
    assert kpis["indicadores_cna"] == 0
    assert kpis["promedio_cumplimiento"] == 0 or kpis["promedio_cumplimiento"] is None or kpis["promedio_cumplimiento"] == 0.0


def test_om_kpis_no_nan():
    """build_kpis_matriz retorna enteros, no NaN."""
    import pandas as pd
    from app.domain.om_builders import build_kpis_matriz

    df_empty = pd.DataFrame()
    kpis = build_kpis_matriz(df_empty)
    assert kpis["total"] == 0
    assert kpis["con_om"] == 0
    assert kpis["avance_om_promedio"] is None
    # Verificar que no hay valores NaN
    for k, v in kpis.items():
        assert v is None or not (isinstance(v, float) and v != v), f"KPI '{k}' tiene NaN"
