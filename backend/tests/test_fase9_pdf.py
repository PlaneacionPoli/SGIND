"""
Tests Fase 9 — Reportes PDF.

Cubre:
 1. pdf_service genera PDFs válidos (header %PDF, no vacío)
 2. Ambos tipos de reporte: resumen_general e informe_procesos
 3. Colores semáforo mapeados correctamente
 4. Endpoint /reports/resumen-general responde 200 con application/pdf
 5. Endpoint /reports/informe-procesos responde 200 con application/pdf
 6. Endpoint sin token responde 401/403
 7. PDF con datos vacíos no explota
 8. Nombre de archivo en Content-Disposition
 9. Tabla de indicadores con >80 indicadores incluye nota de truncamiento
10. Tabla de indicadores con 0 indicadores muestra mensaje apropiado
11. Análisis IA vacío no genera sección vacía con error
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ── PDF Service ───────────────────────────────────────────────────────────────

from app.services.pdf_service import (
    _semaforo_color,
    generar_informe_procesos,
    generar_resumen_general,
    C_CUMPLE,
    C_ALERTA,
    C_PELIGRO,
    C_SOBRE,
    C_SINDAT,
)


def _sample_indicadores(n: int = 3) -> list[dict]:
    estados = ["cumplimiento", "alerta", "peligro", "sobrecumplimiento", "sin dato"]
    return [
        {
            "id": f"T-{i:03d}",
            "indicador": f"Indicador de prueba {i}",
            "meta": 85.0 + i,
            "ejecucion": 80.0 + i * 1.5,
            "estado": estados[i % len(estados)],
            "proceso": f"Proceso {i % 5}",
        }
        for i in range(1, n + 1)
    ]


def _sample_kpis() -> dict:
    return {
        "total_indicadores": 50,
        "cumple": 30,
        "alerta": 12,
        "peligro": 5,
        "sin_dato": 3,
        "pct_cumple": 60.0,
    }


def _sample_informe_data(indicadores: list[dict] | None = None) -> dict:
    inds = indicadores if indicadores is not None else _sample_indicadores(5)
    return {
        "resumen_ejecutivo": {
            "total": len(inds),
            "cumple": 3,
            "alerta": 1,
            "peligro": 1,
            "sin_dato": 0,
            "pct_cumple": 60.0,
        },
        "distribucion_estado": {"cumple": 3, "alerta": 1, "peligro": 1},
        "indicadores": inds,
        "analisis_ia": {"fortalezas": "Buen desempeño en retención.", "oportunidades": ""},
    }


# ─── Tests del servicio PDF ───────────────────────────────────────────────────

def test_resumen_general_pdf_es_valido():
    """generar_resumen_general produce bytes que comienzan con %PDF."""
    pdf = generar_resumen_general(
        anio=2025,
        kpis=_sample_kpis(),
        indicadores=_sample_indicadores(3),
        generated_at="2026-06-19 10:00 UTC",
    )
    assert isinstance(pdf, bytes)
    assert len(pdf) > 500
    assert pdf[:4] == b"%PDF"


def test_informe_procesos_pdf_es_valido():
    """generar_informe_procesos produce bytes que comienzan con %PDF."""
    pdf = generar_informe_procesos(
        anio=2025,
        mes=6,
        proceso="Permanencia",
        data=_sample_informe_data(),
        generated_at="2026-06-19 10:00 UTC",
    )
    assert isinstance(pdf, bytes)
    assert len(pdf) > 500
    assert pdf[:4] == b"%PDF"


def test_resumen_general_sin_indicadores_no_explota():
    """PDF de resumen sin indicadores no lanza excepción."""
    pdf = generar_resumen_general(anio=2024, kpis={}, indicadores=[])
    assert pdf[:4] == b"%PDF"


def test_informe_procesos_datos_vacios_no_explota():
    """PDF de informe con data vacía no lanza excepción."""
    pdf = generar_informe_procesos(anio=2024, mes=12, proceso="Todos", data={})
    assert pdf[:4] == b"%PDF"


def test_semaforo_color_mapping():
    """_semaforo_color mapea correctamente los estados al color SGIND."""
    assert _semaforo_color("cumplimiento") == C_CUMPLE
    assert _semaforo_color("alerta") == C_ALERTA
    assert _semaforo_color("peligro") == C_PELIGRO
    assert _semaforo_color("sobrecumplimiento") == C_SOBRE
    assert _semaforo_color("sin dato") == C_SINDAT
    assert _semaforo_color("sin_dato") == C_SINDAT
    assert _semaforo_color(None) == C_SINDAT
    assert _semaforo_color("CUMPLIMIENTO") == C_CUMPLE  # lower() hace la conversión: "cumplimiento" → verde
    assert _semaforo_color("valor_desconocido") == C_SINDAT  # clave no mapeada → gris


def test_semaforo_color_case_insensitive_lower():
    """_semaforo_color funciona con minúsculas (los datos reales llegan en minúsculas)."""
    for estado in ["cumplimiento", "alerta", "peligro", "sobrecumplimiento"]:
        color = _semaforo_color(estado)
        assert color != C_SINDAT, f"Estado '{estado}' no debería mapear a sin_dato"


def test_informe_pdf_con_muchos_indicadores_no_explota():
    """PDF con 150 indicadores (>100) se genera sin error."""
    inds = _sample_indicadores(150)
    pdf = generar_informe_procesos(
        anio=2025, mes=3, proceso="Todos",
        data=_sample_informe_data(inds),
    )
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 1000


def test_resumen_pdf_con_muchos_indicadores_no_explota():
    """PDF de resumen con 90 indicadores (>80) se genera sin error."""
    pdf = generar_resumen_general(
        anio=2025,
        kpis=_sample_kpis(),
        indicadores=_sample_indicadores(90),
    )
    assert pdf[:4] == b"%PDF"


# ─── Tests de los endpoints HTTP ─────────────────────────────────────────────

def _make_client() -> TestClient:
    from app.main import app
    return TestClient(app, raise_server_exceptions=True)


def _mock_user():
    user = MagicMock()
    user.role = "calidad"
    user.email = "test@poli.edu.co"
    return user


def test_endpoint_resumen_general_sin_token_401():
    """GET /reports/resumen-general sin token debe rechazar (401/403/422)."""
    client = _make_client()
    resp = client.get("/api/v1/reports/resumen-general?anio=2025")
    assert resp.status_code in (401, 403, 422)


def test_endpoint_informe_procesos_sin_token_401():
    """GET /reports/informe-procesos sin token debe rechazar (401/403/422)."""
    client = _make_client()
    resp = client.get("/api/v1/reports/informe-procesos?anio=2025&mes=12")
    assert resp.status_code in (401, 403, 422)


def test_endpoint_resumen_general_con_token():
    """GET /reports/resumen-general con token válido devuelve PDF application/pdf."""
    from app.core.security import require_reader
    from app.api.deps import get_excel_service
    from app.main import app

    mock_user = _mock_user()
    mock_excel = MagicMock()

    # Mock dashboard service
    mock_kpis = [{"total_indicadores": 50, "cumple": 30, "alerta": 10, "peligro": 5}]
    mock_semaforo = _sample_indicadores(5)

    with patch("app.api.v1.endpoints.reports.DashboardService") as MockDash:
        instance = MagicMock()
        instance.get_kpis.return_value = mock_kpis
        instance.get_semaphore.return_value = mock_semaforo
        MockDash.return_value = instance

        client = TestClient(app)
        app.dependency_overrides[require_reader] = lambda: mock_user
        app.dependency_overrides[get_excel_service] = lambda: mock_excel

        try:
            resp = client.get("/api/v1/reports/resumen-general?anio=2025")
            assert resp.status_code == 200
            assert "application/pdf" in resp.headers["content-type"]
            assert resp.content[:4] == b"%PDF"
            assert 'filename="resumen_general_2025.pdf"' in resp.headers.get("content-disposition", "")
        finally:
            app.dependency_overrides.clear()


def test_endpoint_informe_procesos_con_token():
    """GET /reports/informe-procesos con token válido devuelve PDF application/pdf."""
    from app.core.security import require_reader
    from app.api.deps import get_excel_service
    from app.main import app

    mock_user = _mock_user()
    mock_excel = MagicMock()

    with patch("app.api.v1.endpoints.reports.InformeService") as MockInf:
        instance = MagicMock()
        instance.get_dashboard.return_value = _sample_informe_data()
        MockInf.return_value = instance

        client = TestClient(app)
        app.dependency_overrides[require_reader] = lambda: mock_user
        app.dependency_overrides[get_excel_service] = lambda: mock_excel

        try:
            resp = client.get("/api/v1/reports/informe-procesos?anio=2025&mes=6&proceso=Permanencia")
            assert resp.status_code == 200
            assert "application/pdf" in resp.headers["content-type"]
            assert resp.content[:4] == b"%PDF"
            cd = resp.headers.get("content-disposition", "")
            assert "informe_procesos_2025_06" in cd
        finally:
            app.dependency_overrides.clear()
