"""Tests CMI por Procesos — builders y endpoints."""

import pandas as pd
import pytest

from app.domain.procesos_builders import (
    MESES_OPCIONES,
    apply_ui_filters,
    build_propuesta_accion,
    build_procesos_detalle,
    build_procesos_kpis,
    build_tipo_proceso_cards,
    filter_by_anio_mes,
    mes_nombre,
    mes_to_num,
    prepare_tracking,
)


def test_mes_to_num_enero():
    assert mes_to_num("Enero") == 1.0
    assert mes_to_num(6) == 6.0


def test_mes_nombre():
    assert mes_nombre(3) == "Marzo"


def test_prepare_tracking_merge_map():
    df = pd.DataFrame(
        {
            "Id": ["1"],
            "Proceso": ["Sub A"],
            "Subproceso": ["Sub A"],
            "Cumplimiento_norm": [0.95],
            "Anio": [2025],
            "Mes": ["Junio"],
        }
    )
    map_df = pd.DataFrame(
        {
            "Subproceso": ["Sub A"],
            "Proceso": ["PROC PADRE"],
            "Unidad": ["U1"],
            "Tipo de proceso": ["MISIONAL"],
        }
    )
    out = prepare_tracking(df, map_df)
    assert out.iloc[0]["Proceso_padre"] == "PROC PADRE"
    assert out.iloc[0]["Unidad"] == "U1"
    assert out.iloc[0]["cumplimiento_pct"] == pytest.approx(95.0)


def test_filter_by_anio_mes():
    df = pd.DataFrame({"Anio": [2024, 2025], "Mes": ["Mayo", "Junio"], "Id": ["1", "2"]})
    out = filter_by_anio_mes(df, anio=2025, mes=6)
    assert len(out) == 1
    assert out.iloc[0]["Id"] == "2"


def test_apply_ui_filters_proceso():
    df = pd.DataFrame(
        {
            "Proceso_padre": ["A", "B"],
            "Unidad": ["U1", "U2"],
            "cumplimiento_pct": [90, 80],
        }
    )
    out = apply_ui_filters(df, proceso="A")
    assert len(out) == 1


def test_build_comparativa_procesos_colors():
    from app.domain.procesos_builders import build_comparativa_procesos, cumplimiento_semaforo_color

    df = pd.DataFrame(
        {
            "Proceso_padre": ["P1", "P2"],
            "Tipo de proceso": ["MISIONAL", "APOYO"],
            "cumplimiento_pct": [95.0, 65.0],
            "Nivel de cumplimiento": ["Cumplimiento", "Peligro"],
        }
    )
    prev = pd.DataFrame({"Proceso_padre": ["P1", "P2"], "cumplimiento_pct": [90.0, 70.0]})
    out = build_comparativa_procesos(df, prev)
    assert len(out) == 2
    assert out[0]["color"] == cumplimiento_semaforo_color(95.0)
    assert out[1]["estado"] == "Crítico"


def test_build_vista_global_structure():
    from app.domain.procesos_builders import build_vista_global

    df = pd.DataFrame(
        {
            "Id": ["1"],
            "Indicador": ["Ind A"],
            "Proceso_padre": ["P1"],
            "Subproceso_final": ["S1"],
            "Unidad": ["U1"],
            "Tipo de proceso": ["MISIONAL"],
            "cumplimiento_pct": [88.0],
            "Nivel de cumplimiento": ["Alerta"],
            "Anio": [2025],
            "Mes": ["Junio"],
        }
    )
    vg = build_vista_global(df, pd.DataFrame(), pd.DataFrame(), anio=2025, mes_corte=6, base_year=2024, base_mes=12)
    assert vg["mes_corte"] == 6
    assert "kpis" in vg
    assert "comparativa_procesos" in vg
    assert "alertas_criticas" in vg


def test_build_procesos_kpis():
    df = pd.DataFrame(
        {
            "cumplimiento_pct": [100, 85],
            "Nivel de cumplimiento": ["Cumplimiento", "Alerta"],
            "Proceso_padre": ["P1", "P1"],
            "Subproceso_final": ["S1", "S2"],
            "Unidad": ["U1", "U1"],
        }
    )
    kpis = build_procesos_kpis(df)
    assert kpis["total"] == 2
    assert kpis["n_procesos"] == 1
    assert kpis["n_subprocesos"] == 2


def test_build_tipo_proceso_cards():
    df = pd.DataFrame(
        {
            "Tipo de proceso": ["MISIONAL", "MISIONAL"],
            "cumplimiento_pct": [100, 90],
            "Nivel de cumplimiento": ["Cumplimiento", "Alerta"],
        }
    )
    cards = build_tipo_proceso_cards(df)
    assert len(cards) == 1
    assert cards[0]["tipo"] == "MISIONAL"
    assert cards[0]["n_indicadores"] == 2


def test_build_procesos_detalle_subprocesos():
    df = pd.DataFrame(
        {
            "Proceso_padre": ["P1", "P1"],
            "Subproceso_final": ["S1", "S2"],
            "Unidad": ["U1", "U1"],
            "Tipo de proceso": ["APOYO", "APOYO"],
            "cumplimiento_pct": [100, 70],
            "Nivel de cumplimiento": ["Cumplimiento", "Peligro"],
        }
    )
    det = build_procesos_detalle(df)
    assert len(det) == 1
    assert len(det[0]["subprocesos"]) == 2


def test_meses_opciones_length():
    assert len(MESES_OPCIONES) == 12


def test_build_propuesta_accion():
    df = pd.DataFrame(
        {
            "Indicador": ["A", "B", "C"],
            "Proceso_padre": ["P1", "P1", "P1"],
            "cumplimiento_pct": [100.0, 75.0, 50.0],
        }
    )
    prop = build_propuesta_accion(df, proceso="P1")
    assert "B" in prop["plan_mejoramiento"] or "C" in prop["plan_mejoramiento"]
    assert len(prop["top_criticos"]) == 2


def test_generate_ficha_narrativa():
    from app.domain.procesos_builders import generate_ficha_narrativa_heuristica

    narr = generate_ficha_narrativa_heuristica(
        nombre="Ind 1",
        meta=100,
        ejecucion=50,
        nivel="Peligro",
        cumplimiento=50.0,
        proceso="DOCENCIA",
    )
    assert narr["fuente"] == "heuristica"
    assert "Diagnóstico" in narr["texto_html"]


def test_build_export_dataframe():
    from app.domain.procesos_builders import build_export_dataframe

    df = pd.DataFrame(
        {
            "Id": ["1"],
            "Indicador": ["Test"],
            "Proceso_padre": ["P1"],
            "cumplimiento_pct": [95.5],
            "Nivel de cumplimiento": ["Cumplimiento"],
        }
    )
    out = build_export_dataframe(df)
    assert "Código" in out.columns
    assert "Cumplimiento (%)" in out.columns
