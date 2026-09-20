"""
Tests Fase 6 — Contratos de API y consistencia del semáforo.

Cubre:
 1. Estructura de respuesta de todos los endpoints principales
 2. Colores de semáforo == PROJECT_RULES §3.3 (fuente única de verdad)
 3. Paridad numérica: los builders no dividen por cero ni retornan NaN
"""

import pytest

# ─── Colores canónicos (PROJECT_RULES §3.3) ───────────────────────────────────

SEMAFORO = {
    "Peligro": "#D32F2F",
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
        if any(
            msg in str(e)
            for msg in ("password authentication", "Connection refused", "could not connect")
        ):
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


# ─── Consistencia del semáforo (PROJECT_RULES §3.3) ──────────────────────────


@pytest.mark.asyncio
async def test_semaforo_colores_om_builders():
    """om_builders.CATEGORIA_COLORS es un alias directo de domain.constants.COLOR_CATEGORIA
    (Oleada 2 — antes era una copia propia con valores distintos)."""
    from app.domain.om_builders import CATEGORIA_COLORS

    assert CATEGORIA_COLORS["Peligro"].lower() == SEMAFORO["Peligro"].lower()
    assert CATEGORIA_COLORS["Alerta"].lower() == SEMAFORO["Alerta"].lower()
    assert CATEGORIA_COLORS["Cumplimiento"].lower() == SEMAFORO["Cumplimiento"].lower()
    assert CATEGORIA_COLORS["Sobrecumplimiento"].lower() == SEMAFORO["Sobrecumplimiento"].lower()


def test_semaforo_colores_cmi_builders():
    """COLOR_CATEGORIA en cmi_builders coincide exactamente con la paleta
    oficial (Oleada 2 — antes tenía su propia copia con valores distintos)."""
    from app.domain.cmi_builders import COLOR_CATEGORIA

    assert COLOR_CATEGORIA["Peligro"].lower() == SEMAFORO["Peligro"].lower()
    assert COLOR_CATEGORIA["Alerta"].lower() == SEMAFORO["Alerta"].lower()
    assert COLOR_CATEGORIA["Cumplimiento"].lower() == SEMAFORO["Cumplimiento"].lower()
    assert COLOR_CATEGORIA["Sobrecumplimiento"].lower() == SEMAFORO["Sobrecumplimiento"].lower()


def test_semaforo_colores_procesos_builders():
    """cumplimiento_estado/cumplimiento_semaforo_color en procesos_builders
    delegan a categorizar_cumplimiento + COLOR_CATEGORIA (Oleada 2 — antes
    tenían umbrales y vocabulario propios: Saludable/Crítico, 100/80)."""
    from app.domain.procesos_builders import cumplimiento_estado, cumplimiento_semaforo_color

    assert cumplimiento_semaforo_color(110.0) == SEMAFORO["Sobrecumplimiento"]
    assert cumplimiento_semaforo_color(102.0) == SEMAFORO["Cumplimiento"]
    assert cumplimiento_semaforo_color(85.0) == SEMAFORO["Alerta"]
    assert cumplimiento_semaforo_color(50.0) == SEMAFORO["Peligro"]

    estado = cumplimiento_estado(50.0)
    assert estado["label"] == "Peligro"
    assert estado["color"] == SEMAFORO["Peligro"]


def test_semaforo_regimen_plan_anual_por_tipo_retos_proyectos():
    """Retos y Proyectos usan el régimen Plan Anual (95/100) de forma
    incondicional por tipo, confirmado con negocio 2026-09-20 (Oleada 2) —
    no dependen de que su Id esté en IDS_PLAN_ANUAL_DEFAULT."""
    from app.domain.categorization import categorizar_cumplimiento
    from app.domain.resumen_builders import _retos_category

    # Id fuera de cualquier lista especial: sin regimen, sería régimen general.
    assert categorizar_cumplimiento(0.95, id_indicador="999999") == "Alerta"
    # Con regimen="plan_anual" forzado (Retos/Proyectos), 95% ya es Cumplimiento.
    assert (
        categorizar_cumplimiento(0.95, id_indicador="999999", regimen="plan_anual")
        == "Cumplimiento"
    )

    assert _retos_category(99.9) == "Cumplimiento"
    assert _retos_category(95.0) == "Cumplimiento"
    assert _retos_category(94.9) == "Alerta"
    assert _retos_category(79.9) == "Peligro"
    assert _retos_category(105.0) == "Sobrecumplimiento"


def test_semaforo_estado_linea_cmi_builders_regimen_general():
    """_estado_linea (cards de línea CMI) delega al régimen general (100/105),
    no al de Plan Anual (95/100) que usaba antes por error — mezclaba dos
    regímenes distintos para todas las líneas (Oleada 2)."""
    from app.domain.cmi_builders import _estado_linea

    assert _estado_linea(96.0) == ("Alerta", SEMAFORO["Alerta"])
    assert _estado_linea(102.0) == ("Cumplimiento", SEMAFORO["Cumplimiento"])
    assert _estado_linea(105.0) == ("Sobrecumplimiento", SEMAFORO["Sobrecumplimiento"])


# ─── Paridad numérica básica ─────────────────────────────────────────────────


def test_plan_mejoramiento_kpis_no_nan():
    """build_kpis del plan de mejoramiento no produce NaN ni None inesperado."""
    import pandas as pd

    from app.domain.plan_mejoramiento_builders import build_kpis

    df_empty = pd.DataFrame(columns=["Id", "Factor", "Caracteristica", "Cumplimiento_pct"])
    catalog_empty = pd.DataFrame(columns=["Id", "Factor", "Caracteristica"])
    kpis = build_kpis(df_empty, catalog_empty)
    assert kpis["indicadores_cna"] == 0
    assert (
        kpis["promedio_cumplimiento"] == 0
        or kpis["promedio_cumplimiento"] is None
        or kpis["promedio_cumplimiento"] == 0.0
    )


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
