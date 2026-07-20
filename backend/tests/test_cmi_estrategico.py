"""Tests CMI Estratégico — pipeline y endpoints."""

import pandas as pd
import pytest

from app.domain.cmi_builders import (
    build_alertas,
    build_cumplimiento_por_linea,
    build_distribucion_nivel,
    calcular_kpis,
    default_corte,
    linea_color,
)

def test_calcular_kpis_basic():
    df = pd.DataFrame(
        {
            "cumplimiento_pct": [100.0, 85.0, 50.0],
            "Nivel de cumplimiento": ["Sobrecumplimiento", "Alerta", "Peligro"],
            "Linea": ["Calidad", "Calidad", "Expansión"],
            "Objetivo": ["O1", "O1", "O2"],
        }
    )
    kpis = calcular_kpis(df)
    assert kpis["total"] == 3
    assert kpis["con_dato"] == 3
    assert kpis["en_riesgo"] == 2
    assert kpis["promedio"] == pytest.approx(78.3, abs=0.2)


def test_build_alertas_only_peligro_alerta():
    df = pd.DataFrame(
        {
            "Id": ["1", "2", "3"],
            "Indicador": ["A", "B", "C"],
            "cumplimiento_pct": [100, 85, 50],
            "Nivel de cumplimiento": ["Cumplimiento", "Alerta", "Peligro"],
            "Linea": ["Calidad", "Calidad", "Expansión"],
        }
    )
    alertas = build_alertas(df)
    assert alertas["peligro"] == 1
    assert alertas["alerta"] == 1
    assert len(alertas["items"]) == 2


def test_linea_color_calidad():
    assert linea_color("Calidad") == "#EC0677"


def test_default_corte_past_year():
    assert default_corte(2020) == "Diciembre"


def test_build_distribucion_nivel():
    df = pd.DataFrame({"Nivel de cumplimiento": ["Cumplimiento", "Cumplimiento", "Alerta"]})
    dist = build_distribucion_nivel(df)
    assert sum(d["cantidad"] for d in dist) == 3


def test_build_linea_analisis_narrativa():
    from app.domain.cmi_builders import build_linea_analisis, generate_linea_narrativa_heuristica

    df = pd.DataFrame(
        {
            "Id": ["1", "2"],
            "Linea": ["Calidad", "Calidad"],
            "Indicador": ["Ind A", "Ind B"],
            "Objetivo": ["O1", "O1"],
            "cumplimiento_pct": [50.0, 100.0],
            "Nivel de cumplimiento": ["Peligro", "Cumplimiento"],
        }
    )
    narr = generate_linea_narrativa_heuristica("Calidad", 75.0, 2, 1, df)
    assert narr["titulo"] == "Insights y Directrices Estratégicas"
    assert "Ind A" in narr["texto_html"]
    assert len(narr["directrices"]) == 2

    analisis = build_linea_analisis(df, pd.DataFrame(), anio=2025, mes=12)
    assert analisis["cumplimiento_actual"] == 75.0
    assert len(analisis["indicadores_riesgo"]) == 1


def test_previous_corte():
    from app.domain.cmi_builders import previous_corte

    assert previous_corte(2025, 12) == (2025, 6)
    assert previous_corte(2025, 6) == (2024, 12)


def test_build_cumplimiento_por_linea():
    df = pd.DataFrame(
        {
            "Linea": ["Calidad", "Calidad", "Expansión"],
            "cumplimiento_pct": [100.0, 80.0, 90.0],
        }
    )
    bars = build_cumplimiento_por_linea(df)
    assert len(bars) == 2
    assert all("color" in b for b in bars)


@pytest.mark.asyncio
async def test_cmi_filtros_endpoint(client, auth_as_calidad):
    response = await client.get("/api/v1/cmi/filtros")
    assert response.status_code == 200
    data = response.json()
    assert "anios" in data
    assert "corte_default" in data


@pytest.mark.asyncio
async def test_cmi_dashboard_endpoint(client, auth_as_calidad):
    filtros = await client.get("/api/v1/cmi/filtros")
    anio = filtros.json()["anio_default"]
    response = await client.get(
        "/api/v1/cmi/estrategico-dashboard",
        params={"anio": anio, "corte": "Diciembre"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["anio"] == anio
    assert data["mes"] == 12
    assert "kpis" in data
    assert "indicadores" in data
    assert "alertas" in data
    if data["lineas_detalle"]:
        linea0 = data["lineas_detalle"][0]
        assert "analisis" in linea0
        assert "narrativa" in linea0["analisis"]


@pytest.mark.asyncio
async def test_cmi_alertas_filtra_estrategico(client, auth_as_calidad):
    filtros = await client.get("/api/v1/cmi/filtros")
    anio = filtros.json()["anio_default"]
    dash = await client.get(
        "/api/v1/cmi/estrategico-dashboard",
        params={"anio": anio, "corte": "Diciembre"},
    )
    alertas = await client.get(
        "/api/v1/cmi/alertas",
        params={"anio": anio, "corte": "Diciembre", "limit": 500},
    )
    assert alertas.status_code == 200
    a_data = alertas.json()
    d_data = dash.json()
    assert a_data["total"] == d_data["alertas"]["peligro"] + d_data["alertas"]["alerta"]
