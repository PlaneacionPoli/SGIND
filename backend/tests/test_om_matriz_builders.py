"""Gestión OM: conteo por proceso e historial por indicador (sin Excel ni BD)."""

from __future__ import annotations

import pandas as pd

from app.domain.om_builders import build_historial, build_por_proceso


def test_por_proceso_cuenta_con_y_sin_om_y_ordena_por_pendientes():
    df = pd.DataFrame(
        {
            "proceso": ["A", "A", "B", "B", "B", ""],
            "tiene_om": [1, 0, 0, 0, 1, 0],
        }
    )
    res = build_por_proceso(df)
    assert [r["proceso"] for r in res] == [
        "B",
        "A",
        "Sin proceso",
    ]  # 2, 1 y 1 pendientes; el empate se resuelve por total
    por = {r["proceso"]: r for r in res}
    assert por["A"] == {"proceso": "A", "total": 2, "con_om": 1, "sin_om": 1}
    assert por["B"]["sin_om"] == 2 and por["B"]["total"] == 3
    assert por["Sin proceso"]["sin_om"] == 1
    assert build_por_proceso(pd.DataFrame()) == []


def test_historial_toma_ultimos_periodos_hasta_el_corte():
    filas = []
    for m in range(1, 13):
        filas.append(
            {
                "Id": "7",
                "Anio": 2025,
                "Mes": m,
                "Cumplimiento_pct": m * 5,
                "Ejecucion": m,
                "Meta": 10,
                "Categoria": "Peligro",
            }
        )
    filas.append(
        {
            "Id": "7",
            "Anio": 2026,
            "Mes": 1,
            "Cumplimiento_pct": 99,
            "Ejecucion": 1,
            "Meta": 1,
            "Categoria": "Cumplimiento",
        }
    )
    filas.append(
        {
            "Id": "8",
            "Anio": 2025,
            "Mes": "Marzo",
            "Cumplimiento_pct": 10,
            "Ejecucion": 1,
            "Meta": 10,
            "Categoria": "Peligro",
        }
    )
    h = build_historial(pd.DataFrame(filas), ["7"], anio=2025, mes="Diciembre", n=6)
    assert list(h) == ["7"]
    assert [p["periodo"] for p in h["7"]] == [
        "Jul 2025",
        "Ago 2025",
        "Sep 2025",
        "Oct 2025",
        "Nov 2025",
        "Dic 2025",
    ]
    assert h["7"][-1]["cumplimiento_pct"] == 60.0  # el 2026 queda fuera del corte
    assert build_historial(pd.DataFrame(), ["7"], anio=2025, mes="Diciembre") == {}
    assert (
        build_historial(pd.DataFrame(filas), ["8"], anio=2025, mes="Diciembre")["8"][0]["periodo"]
        == "Mar 2025"
    )


def test_filtros_usan_el_corte_mas_reciente_con_datos_y_no_cuentan_sin_dato():
    from app.domain.om_builders import build_filtros

    df = pd.DataFrame(
        {
            "Anio": [2025, 2026, 2026, 2026, 2026],
            "Mes": ["Diciembre", "Junio", "Septiembre", "Diciembre", 3],
            "Categoria": ["Peligro", "Alerta", "Peligro", "Sin dato", "Cumplimiento"],
            "Proceso": ["A"] * 5,
        }
    )
    f = build_filtros(df)
    assert f["anios"] == ["2025", "2026"]
    assert f["anio_default"] == "2026"
    assert f["mes_default"] == "Septiembre"  # Diciembre 2026 solo tiene «Sin dato»
    assert f["meses_por_anio"]["2026"] == ["Marzo", "Junio", "Septiembre"]
    assert build_filtros(pd.DataFrame())["anio_default"] == "2025"


def test_cumplimiento_usa_cumplimiento_norm_del_historico_real():
    from app.domain.om_builders import merge_om_registros

    riesgo = pd.DataFrame(
        [
            {
                "Id": "86",
                "Indicador": "X",
                "Proceso": "P",
                "Meta": 100,
                "Ejecucion": 3,
                "Cumplimiento_norm": 0.03,
                "Categoria": "Peligro",
            }
        ]
    )
    fila = merge_om_registros(riesgo, [], {}).iloc[0]
    assert fila["cumplimiento_pct"] == 3.0
    h = build_historial(
        pd.DataFrame(
            [
                {
                    "Id": "86",
                    "Anio": 2026,
                    "Mes": "Junio",
                    "Cumplimiento_norm": 0.5,
                    "Categoria": "Peligro",
                }
            ]
        ),
        ["86"],
        anio=2026,
        mes="Junio",
    )
    assert h["86"][0]["cumplimiento_pct"] == 50.0
