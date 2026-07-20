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
    assert dash["score_global"] == 87.5
    assert len(dash["por_proceso"]) == 1


def test_filter_calidad_proceso():
    df = pd.DataFrame({"Proceso": ["A", "B"], "pct_calidad": [90, 70]})
    out = filter_calidad(df, proceso="A")
    assert len(out) == 1
