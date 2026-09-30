"""Tests calidad de datos — builders."""

import pandas as pd

from app.domain.calidad_builders import (
    _estado_calidad,
    _score_calidad,
    build_calidad_dashboard,
    filter_calidad,
)


def test_score_calidad_cumple():
    assert _score_calidad("CUMPLE") == 1.0
    assert _score_calidad("NO CUMPLE") == 0.0
    assert _score_calidad("CUMPLE PARCIALMENTE") == 0.5


def test_estado_calidad():
    assert _estado_calidad(95) == "CUMPLE"
    assert _estado_calidad(75) == "CUMPLE PARCIALMENTE"
    assert _estado_calidad(50) == "NO CUMPLE"


def test_build_calidad_dashboard():
    df = pd.DataFrame(
        {
            "Proceso": ["P1", "P1"],
            "Subproceso": ["S1", "S2"],
            "pct_calidad": [95.0, 80.0],
            "Estado calidad": ["CUMPLE", "CUMPLE PARCIALMENTE"],
            "I. OPORTUNIDAD": ["CUMPLE", "CUMPLE"],
            "II. COMPLETITUD": ["CUMPLE", "CUMPLE PARCIALMENTE"],
            "III. CONSISTENCIA": ["CUMPLE", "CUMPLE"],
            "IV. PRECISIÓN": ["CUMPLE", "NO CUMPLE"],
            "V. PROTOCOLO": ["CUMPLE", "CUMPLE"],
        }
    )
    dash = build_calidad_dashboard(df)
    assert dash["disponible"] is True
    # score_global replica la fórmula del Streamlit legacy: media de las 4
    # dimensiones de la pestaña (Completitud 75, Consistencia 100,
    # Oportunidad 100, Exactitud 50) -> (75+100+100+50)/4 = 81.25
    assert dash["score_global"] == 81.2
    assert dash["dim_scores"] == {
        "Completitud": 75.0,
        "Consistencia": 100.0,
        "Oportunidad": 100.0,
        "Exactitud": 50.0,
    }
    assert len(dash["por_proceso"]) == 1
    assert len(dash["detalle_indicadores"]) == 2
    assert any(a["tipo"] == "critica" for a in dash["alertas"])
    assert {r["prioridad"] for r in dash["recomendaciones"]} == {"Alta", "Media", "Baja"}


def test_filter_calidad_proceso():
    df = pd.DataFrame({"Proceso": ["A", "B"], "pct_calidad": [90, 70]})
    out = filter_calidad(df, proceso="A")
    assert len(out) == 1
