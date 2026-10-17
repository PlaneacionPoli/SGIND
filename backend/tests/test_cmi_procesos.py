"""Tests CMI por Procesos — builders y endpoints."""

import pandas as pd
import pytest

from app.domain.procesos_builders import (
    MESES_OPCIONES,
    apply_ui_filters,
    build_procesos_detalle,
    build_procesos_kpis,
    build_propuesta_accion,
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
    # Vocabulario canónico desde Oleada 2 (categorizar_cumplimiento), antes
    # decía "Crítico" (vocabulario propio ya eliminado) — ver
    # docs/tecnico/05-reglas-de-negocio.md.
    assert out[1]["estado"] == "Peligro"


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
    vg = build_vista_global(
        df, pd.DataFrame(), pd.DataFrame(), anio=2025, mes_corte=6, base_year=2024, base_mes=12
    )
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


def test_jerarquia_por_id_prevalece_sobre_el_nombre():
    """El proceso/subproceso sale del catálogo por Id, no del nombre que trae el seguimiento."""
    df = pd.DataFrame(
        {
            "Id": ["10", "386.1", "99"],
            "Proceso": ["Nombre equivocado", "Otro nombre", "Sin catalogo"],
            "Subproceso": ["Nombre equivocado", "Otro nombre", "Sin catalogo"],
            "Cumplimiento_norm": [0.9, 1.0, 0.8],
            "Anio": [2025, 2025, 2025],
            "Mes": ["Junio"] * 3,
        }
    )
    map_df = pd.DataFrame(
        {
            "Subproceso": ["SUB A", "SUB B"],
            "Proceso": ["PROC A", "PROC B"],
            "Unidad": ["U1", "U2"],
            "Tipo de proceso": ["MISIONAL", "APOYO"],
        }
    )
    jer = pd.DataFrame(
        {
            "Id": ["10", "386"],
            "Proceso_cat": ["PROC A ", "PROC B"],
            "Subproceso_cat": ["SUB  A", "SUB B"],
            "TipoCalculo": ["Cierre", "Acumulado"],
            "Estado_cat": ["Activo", "Activo"],
        }
    )
    out = prepare_tracking(df, map_df, jer).set_index("Id")
    assert out.loc["10", "Proceso_padre"] == "PROC A"
    assert out.loc["10", "Subproceso_final"] == "SUB A"
    assert out.loc["10", "Unidad"] == "U1"
    # un subindicador hereda la jerarquía de su indicador padre
    assert out.loc["386.1", "Proceso_padre"] == "PROC B"
    assert out.loc["386.1", "Tipo de proceso"] == "APOYO"
    # un Id fuera del catálogo conserva la asignación previa
    assert out.loc["99", "Proceso_padre"] == "Sin catalogo"


def test_estado_cierre_fila_parcial_solo_en_el_año_en_curso():
    from app.domain.procesos_builders import estado_cierre_fila

    assert estado_cierre_fila("2025-12-31", 2026) == "Final"
    assert estado_cierre_fila("2022-06-30", 2026) == "Final"
    assert estado_cierre_fila("2026-07-31", 2026) == "Parcial"
    assert estado_cierre_fila(None, 2026) == ""


def test_build_mapa_procesos_agrega_por_id_y_calcula_variaciones():
    from app.domain.procesos_builders import build_mapa_procesos, ultimo_registro_anual

    def frame(valores):
        return pd.DataFrame(
            {
                "Id": ["1", "2"],
                "Indicador": ["Ind 1", "Ind 2"],
                "Proceso_padre": ["P"] * 2,
                "Subproceso_final": ["S"] * 2,
                "Unidad": ["U"] * 2,
                "Tipo de proceso": ["MISIONAL"] * 2,
                "cumplimiento_pct": valores,
                "Nivel de cumplimiento": ["Cumplimiento", "Peligro"],
                "Mes": ["Diciembre"] * 2,
                "Fecha": ["2024-12-31"] * 2,
                "Periodicidad": ["Mensual", "Semestral"],
            }
        )

    frames = {
        2024: ultimo_registro_anual(frame([100.0, 80.0]), mes_corte=12),
        2025: ultimo_registro_anual(frame([100.0, 90.0]), mes_corte=12),
        2026: ultimo_registro_anual(frame([100.0, 100.0]), mes_corte=12),
    }
    jer = pd.DataFrame({"Id": ["1"], "TipoCalculo": ["Promedio"]})
    m = build_mapa_procesos(
        frames, jer, anios=[2024, 2025, 2026], anio_parcial=2026
    )
    p = m["procesos"][0]
    assert p["anios"] == {"2024": 90.0, "2025": 95.0, "2026": 100.0}
    assert p["variaciones"] == {"2024-2025": 5.0, "2025-2026": 5.0}
    assert m["anio_parcial"] == 2026
    inds = {i["id"]: i for i in p["subprocesos"][0]["indicadores"]}
    assert inds["1"]["tipo_calculo"] == "Promedio"
    assert inds["1"]["periodicidad"] == "Mensual"
    assert inds["1"]["ultimo_reporte"] == "Dic 2024"
    assert inds["1"]["estado_cierre"] == "Final"
    assert inds["2"]["tipo_calculo"] is None
    assert m["sin_tipo_calculo"] == 1
